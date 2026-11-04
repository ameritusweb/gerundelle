"""The measures a scene is judged by, whichever arm produced it.

- round-trip: the determination system reads each printed sentence back; the sentence passes if a
  reading has the gerund shape its construction intended, and that reading is its label (the corpus's
  labels are the reader's, checked against the plan's, never only asserted);
- judge: the structural judge (../judge.py, tower v2) on the passage: matched share, theory coverage,
  variety;
- history: how much of the scene depends on what came before (plans whose beats cite earlier beats),
  and the longest chain of such dependence.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from printer import alternatives, shape_of  # noqa: E402
from probe import skeletons  # noqa: E402
from theories import gerunds_of, theory_coverage  # noqa: E402

NAN = float("nan")   # a judge score that wasn't measured: never a real 0
_JUDGE = None
_WARNED = False


def judge():
    """The structural judge, or None where it isn't available: it needs torch and trained models that aren't in the repo.
    Everything else here runs without it, and its scores read nan."""
    global _JUDGE, _WARNED
    if _JUDGE is None:
        try:
            from judge import Judge
            _JUDGE = Judge(backend="tower")
        except (ImportError, OSError) as e:
            if not _WARNED:
                print(f"(the structural judge isn't available, so its scores read nan: {e})", file=sys.stderr)
                _WARNED = True
    return _JUDGE


def round_trip(sentences):
    """sentences: [(plan index, text, intended shape)] -> rows with the reader's verdict."""
    rows = []
    for (i, text, shape), (_, skels, why) in zip(sentences, skeletons([t for _, t, _ in sentences])):
        want = alternatives(shape)
        hit = next((s for s in skels if shape_of(s) in want), "")
        rows.append({"plan": i, "text": text, "shape": shape, "reading": hit, "ok": bool(hit),
                     "readings": skels, "why": why})
    return rows


def history(scene):
    """Share of plans that depend on an earlier one, and the longest dependence chain (in plans)."""
    depth = {}
    for i, p in enumerate(scene.plans):
        depth[i] = 1 + max((depth[r] for r in p.refs), default=0)
    n = len(scene.plans)
    # reach: how far back the furthest dependence goes, in plans (a memory reopened after time has passed
    # cites the loss it came from: history kept, and used)
    reach = max((i - min(p.refs) for i, p in enumerate(scene.plans) if p.refs), default=0)
    return {"dependent": sum(1 for p in scene.plans if p.refs) / max(1, n), "chain": max(depth.values(), default=0),
            "reach": reach}


def evaluate(scene, sentences):
    rows = round_trip(sentences)
    tower = judge()
    j = tower.judge(" ".join(r["text"] for r in rows), sentences=[r["text"] for r in rows]) if tower else dict(
        sentences=[], matched_share=NAN, best_theory=None, theories={}, variety=NAN)
    # theory coverage from the exact labels (the tower's own coverage takes the gerunds of the five
    # nearest skeletons per sentence, which saturates: every theory reads 1.0 on any passage)
    exact = theory_coverage([set(gerunds_of(r["reading"])) for r in rows])
    best = max(exact.items(), key=lambda kv: (kv[1], -len(kv[0])))
    return {"round_trip": sum(r["ok"] for r in rows) / max(1, len(rows)), "rows": rows,
            "exact_theory": best[0], "exact_coverage": best[1],
            "exact_theories": {k: round(v, 2) for k, v in sorted(exact.items(), key=lambda kv: -kv[1])[:5]},
            "unmatched": [r["text"] for r in j["sentences"] if not r["matched"]],
            "matched_share": j["matched_share"], "best_theory": j["best_theory"],
            "best_coverage": j.get("best_coverage", 0.0),
            "theories": {k: v for k, v in sorted(j["theories"].items(), key=lambda kv: -kv[1])[:4]},
            "variety": j["variety"], "judge_rows": j["sentences"], "history": history(scene),
            "irony": irony(scene, rows), "reader": reader(scene, rows)}


HALF = 8.0   # the reader's memory: a planted detail's warmth halves every HALF sentences
SALIENCE = {"try": 0.25, "change": 0.25, "learn": 0.6, "summary": 0.0}


def reader(scene, rows):
    """The reader as a mind (rung 6): each sentence that shows a detail later paid off plants a key, with a
    memorability by how it was shown (a passing action, a stated lesson); keys cool by HALF sentences. At the
    payoff (a recall), satisfaction = relevance x (1 - the key's warmth then): the time-hotel formula (an
    element that solves the problem and that the reader had forgotten). Relevance: how stuck the character was
    (failed pushes on the wanted object in the scene before the payoff). A payoff with nothing planted is
    unearned (deus ex machina); a plant never paid off is Chekhov's debt."""
    sent_of = [r["plan"] for r in rows]
    payoff = next((i for i, p in enumerate(scene.plans) if p.kind == "recall"), None)
    plants = [i for i, p in enumerate(scene.plans) if p.fill.get("plant")]
    if payoff is None:
        return {"satisfaction": 0.0, "memorability": 0.0, "relevance": 0.0, "deus": False, "debt": bool(plants)}
    at = sent_of.index(payoff)
    warmth = 0.0
    for i in plants:
        s = sent_of.index(i) if i in sent_of else at
        warmth += SALIENCE.get(scene.plans[i].kind, 0.25) * 0.5 ** ((at - s) / HALF)
    warmth = min(1.0, warmth)
    brk = max((i for i, p in enumerate(scene.plans) if p.kind == "scene" and i < payoff), default=0)
    fails = sum(1 for p in scene.plans[brk:payoff] if p.kind == "nothing" or
                (p.kind == "attempt" and p.fill["outcome"] == "nothing")) +         sum(p.fill["count"] for p in scene.plans[brk:payoff] if p.kind == "explore")   # however a failure is told
    relevance = min(1.0, 0.5 + 0.25 * fails)
    planted = bool(plants)
    return {"satisfaction": round(relevance * (1 - warmth), 3) if planted else 0.0, "memorability": round(warmth, 3),
            "relevance": relevance, "deus": not planted, "debt": False}


def irony(scene, rows):
    """Dramatic irony: sentences during which the reader holds a truth the character does not, from the
    reveal (the narrator says what a liar holds) to the character's own realization (0 if never revealed)."""
    reveal = next((i for i, p in enumerate(scene.plans) if p.kind == "reveal"), None)
    if reveal is None:
        return 0
    found = next((i for i, p in enumerate(scene.plans) if i > reveal and p.kind == "learn"), len(scene.plans))
    return sum(1 for r in rows if reveal < r["plan"] < found)
