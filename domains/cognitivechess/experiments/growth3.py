"""Stress-test trace: what makes full games slower as the minds' records grow. Per game: ms per tick by component, next to
the sizes each reads (both minds summed). --no-speedup switches off the concept_of cache and the funding index.

Run: PYTHONHASHSEED=0 python -X utf8 experiments/growth3.py [--seed 1] [--games 20] [--no-speedup]
"""
import argparse, os, sys, time
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "fiction"))
import chess  # noqa: E402
from rung3 import make, TURN_STEPS  # noqa: E402
import molecules  # noqa: E402

T = Counter(); N = Counter()


def timed(cls, name, label=None):
    f = getattr(cls, name); label = label or name; active = {"d": 0}

    def w(*a, **k):
        if active["d"]:   # count only the outermost call of a recursive or re-entrant one
            return f(*a, **k)
        active["d"] = 1; t = time.perf_counter()
        try:
            return f(*a, **k)
        finally:
            T[label] += time.perf_counter() - t; N[label] += 1; active["d"] = 0
    setattr(cls, name, w)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--games", type=int, default=20)
    ap.add_argument("--no-speedup", action="store_true")
    ap.add_argument("--stuck-earns", action="store_true")
    a = ap.parse_args()
    if a.no_speedup:
        molecules.concept_of = molecules.concept_of.__wrapped__
        molecules.Understanding.funding_index = lambda self: None
    U, M, Y, I = molecules.Understanding, molecules.Mind, molecules.Territory, molecules.Inquiry
    for cls, name in ((M, "think"), (U, "observe"), (U, "analogize"), (U, "core"), (U, "edges"), (U, "refine"),
                      (U, "shared"), (M, "resolve"), (M, "novelty"), (Y, "relation_of"), (Y, "observe"), (I, "observe"),
                      (molecules.Phases, "observe"), (molecules.Meta, "observe")):
        timed(cls, name, f"{cls.__name__}.{name}")
    w, minds = make(a.seed, "mind", "base", "keeper", given=True, fen=chess.STARTING_FEN, half_moves=120)
    for m in minds:
        p = m.agent.mind.p
        p.winner_acts = p.imagined_lane = p.news_in_structure = True
        p.stuck_earns = a.stuck_earns
    st = dict(done=0, t=time.time(), half=0); reset, act = w.reset, w.act

    def report():
        ticks = N["Mind.think"] or 1
        ms = lambda k: round(1000 * T[k] / ticks, 1)
        size = Counter()
        for m in minds:
            mi = m.agent.mind; u = mi.understanding
            size["pool"] += len(mi.pool); size["pool pushes"] += sum("invitation" in x.tags for x in mi.pool.values())
            size["pool stuck"] += sum(i.startswith("meta:stuck") for i in mi.pool)
            size["concepts"] += len(u.rel); size["relations"] += sum(len(r) for r in u.rel.values())
            size["edges"] += len(U.edges(u)); size["abstracts"] += len(u.abstracts)
            size["readings"] += len(mi.meta.modes); size["splits"] += len(mi.meta.splits)
            size["plans"] += len(mi.inquiry.plans); size["boxes"] += len(mi.boxes)
            size["questions"] += len(u.questions); size["other_moves"] += sum(len(r.get("other_moves", ())) for r in mi.territory.rows.values())
        print(f"game {st['done']}: {time.time() - st['t']:.0f}s, {ticks} ticks, {1000 * (time.time() - st['t']) / ticks:.0f} ms/tick | "
              + " ".join(f"{k.split('.')[0][0]}.{k.split('.')[1]}={ms(k)}" for k, _ in T.most_common(14)) + " | " + str(dict(size)), flush=True)
        T.clear(); N.clear()

    def counted():
        st["done"] += 1
        report()
        st["t"] = time.time()
        reset()
    w.reset = counted
    by = {m.name: m for m in minds}; seen = {"White": 0, "Black": 0}

    def step(n):
        w.actor = n
        seen[n] = by[n].step(seen[n])
    while st["done"] < a.games:
        mover = "White" if w.board.turn == chess.WHITE else "Black"
        other = "Black" if mover == "White" else "White"
        before = (w.moved, len(w.episodes))
        for _ in range(TURN_STEPS):
            step(mover)
            if (w.moved, len(w.episodes)) != before:
                break
        step(other)


if __name__ == "__main__":
    main()
