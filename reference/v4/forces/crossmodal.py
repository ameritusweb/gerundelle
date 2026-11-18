"""Gap item 2, first standing point: render force diffs as sentences and check
them against the version-2 structural space and the determination system,
retraining nothing (NEWTONIAN_WORLD_MODEL.md sections 6, 12).

The printer renders each diff in the NATURAL form for each row of section 6's
table, because the determination system reads tense: a past-tense event verb
narrates, a copula describes, "because" explains, a number grounds. If a diff
were printed as a copula ("The beam is on the ground") the mapping failing
would be the printer's fault, not section 6's; the informative failure is a
natural form read wrong.

Checks, in order:
0. The null boundary. Every printed sentence must land clean-side of the
   version-2 threshold (cosine to its own skeleton minus cosine to the null
   point); a sentence near null is a printer problem to fix before the other
   checks mean anything. An undetermined sentence is a template gap, reported.
1. Check A: same-diff (different wording) versus same-scene-different-diff
   cosine in the text tower, reported the way 0.85 against 0.10 was for text.
   Same-scene negatives keep content words from carrying the signal. A third
   number is kept honestly: different diffs of the SAME type (the beam broke /
   the roof fell) share a skeleton, so a structural space SHOULD conflate
   them; that number high is a property, not a failure.
2. Check B: the row-by-row mapping. Four rows, one per diff type; a hit is a
   printed sentence with the predicted gerund at the root of some valid
   reading. Where the natural form still reads wrong is where section 6 is
   wrong, which is the information the next layer wants.
"""
import json
import os
import sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT = os.path.abspath(os.path.join(HERE, "..", "text"))
sys.path.insert(0, HERE)
sys.path.insert(0, TEXT)

import numpy as np
import torch

from poc import anchoring, doing, pressing, slot, step, wire
from reader import GROUND, OBJS, base, observe, read_diff

NOUN = {"ground": "ground", "thatch-roof": "roof", "heavy-roof": "roof", "stone-post": "post",
        "oak-beam": "beam", "snow": "snow", "mortared-wall": "wall", "brick": "brick",
        "hemp-rope": "rope", "steel-chain": "chain", "lantern": "lantern", "plank": "plank"}


def N(u):
    return NOUN[base(u)]


# ---- the scenes: trajectories from the simulator, read into events -------------------

def trajectory(t, objs):
    snaps = [observe(t, objs)]
    while True:
        t, ev = step(t, objs)
        if not ev:
            return snaps
        snaps.append(observe(t, objs))


def scenes():
    objs = OBJS
    out = {}
    pre = wire(anchoring(GROUND, slot("supporting", slot("supporting",
              doing("resting", "thatch-roof")))), ("stone-post", "oak-beam"), objs)
    t0 = wire(anchoring(GROUND, slot("supporting", slot("supporting",
             doing("resting", "thatch-roof", pressing("snow"))))), ("stone-post", "oak-beam"), objs)
    out["tower"] = [observe(pre, objs)] + trajectory(t0, objs)
    wall = wire(anchoring(GROUND, slot("supporting", doing("resting", "heavy-roof"))),
                ("mortared-wall",), objs)
    out["wall"] = trajectory(wall, objs)
    hung = wire(anchoring(GROUND, slot("hanging", doing("hanging", "thatch-roof"))),
                ("plank",), objs)
    out["hanger"] = trajectory(hung, objs)
    chain = wire(anchoring(GROUND, slot("hanging", slot("hanging",
                doing("hanging", "lantern")))), ("steel-chain", "hemp-rope"), objs)
    out["chain"] = trajectory(chain, objs)
    return out


# ---- the printer: the natural form for each row ---------------------------------------

def print_describing(snap):
    """A slice renders as stative clauses, one per contact; the copula and the
    stative verbs are the lever for the describing row."""
    out = []
    for a, b in sorted(snap.on):
        out.append((f"on:{a}", [f"The {N(a)} rests on the {N(b)}.",
                                f"The {N(a)} sits on the {N(b)}.",
                                f"The {N(a)} is on the {N(b)}."]))
    for a, b in sorted(snap.hangs):
        out.append((f"hangs:{a}", [f"The {N(a)} hangs from the {N(b)}.",
                                   f"The {N(a)} dangles from the {N(b)}.",
                                   f"The {N(a)} is suspended from the {N(b)}."]))
    return out


def print_narrating(e):
    o = N(e["obj"])
    return {"broke": [f"The {o} broke.", f"The {o} snapped.", f"The {o} gave way."],
            "fell": [f"The {o} fell.", f"The {o} dropped.", f"The {o} tumbled down."],
            "landed": [f"The {o} landed on the ground.", f"The {o} crashed onto the ground."],
            "came_apart": [f"The {o} crumbled.", f"The {o} fell apart."],
            "arrived": [f"The {o} settled on the {N(e.get('bearer', GROUND))}.",
                        f"The {o} piled onto the {N(e.get('bearer', GROUND))}."],
            "unburdened": [f"The {o} shed its load.", f"The {o} stood free."]}[e["kind"]]


def print_explaining(e):
    o = N(e["obj"])
    if e["kind"] == "broke":
        return [f"The {o} broke because the load on it grew too great.",
                f"The {o} snapped because it carried more than it could bear."]
    if e["kind"] == "fell":
        return [f"The {o} fell because the {N(e['bearer'])} broke.",
                f"The {o} dropped because the {N(e['bearer'])} gave way."]
    if e["kind"] == "came_apart":
        return [f"The {o} crumbled because the weight crushed it.",
                f"The {o} fell apart because the load broke its mortar."]
    return []


def print_grounding(e):
    # The number goes mid-sentence: determine.py's truncated() reads a sentence
    # ending in a bare 1-2 digit number as a cut-off citation (a corpus-hygiene
    # rule), so "broke under a load of 13." gets no reading at all. Found by
    # this check's first run; a printer fact, not a section 6 fact.
    o = N(e["obj"])
    if e["kind"] == "broke":
        return [f"Under a load of {e['load']:g}, the {o} broke.",
                f"At a load of {e['load']:g}, the {o} failed."]
    if e["kind"] == "came_apart":
        return [f"Under a weight of {e['load']:g}, the {o} crumbled.",
                f"At a weight of {e['load']:g}, the {o} came apart."]
    return []


def sentences():
    """Every printed sentence, with (scene, diff id, row). The diff id keys
    check A's pairs: same id and row = same diff, different wording."""
    rows = []
    for scene, snaps in scenes().items():
        for key, words in print_describing(snaps[0]):
            for w in words:
                rows.append({"scene": scene, "diff": f"slice:{key}", "row": "describing", "text": w})
        for i, (a, b) in enumerate(zip(snaps, snaps[1:])):
            for e in read_diff(a, b):
                eid = f"{i}:{e['kind']}:{e['obj']}"
                for row, words in (("narrating", print_narrating(e)),
                                   ("explaining", print_explaining(e)),
                                   ("grounding", print_grounding(e))):
                    for w in words:
                        rows.append({"scene": scene, "diff": eid, "row": row, "text": w})
    return rows


# ---- the checks ------------------------------------------------------------------------

def determine_all(rows):
    from determine import determine_many
    for r, (_, readings) in zip(rows, determine_many([r["text"] for r in rows])):
        r["roots"] = sorted({rd.kind for rd in readings})
        r["skels"] = sorted({_skel(str(rd)) for rd in readings})


def _skel(s):
    from structural import skeleton
    return skeleton(s)


def check_null(rows):
    from sentence_transformers import SentenceTransformer
    from structural2 import NullTreeTower
    model = SentenceTransformer(os.path.join(TEXT, "models", "structural2", "text"))
    ck = torch.load(os.path.join(TEXT, "models", "structural2", "tree.pt"), map_location="cpu")
    tree = NullTreeTower(set(ck["labels"]), set(ck["roles"]))
    tree.load_state_dict(ck["state"])
    tree.eval()
    threshold = json.load(open(os.path.join(TEXT, "models", "structural2", "threshold.json")))["threshold"]
    embs = torch.tensor(model.encode([r["text"] for r in rows], normalize_embeddings=True,
                                     show_progress_bar=False))
    null = tree.null_vec().detach()
    with torch.no_grad():
        for r, e in zip(rows, embs):
            r["emb"] = e
            if not r["skels"]:
                r["score"] = None  # a template gap: no reading, nothing to score against
                continue
            own = (tree(r["skels"]) @ e).max().item()
            r["score"] = own - float(null @ e)
    gaps = [r for r in rows if r["score"] is None]
    clean = [r for r in rows if r["score"] is not None and r["score"] >= threshold]
    low = [r for r in rows if r["score"] is not None and r["score"] < threshold]
    print(f"== Check 0: the null boundary (threshold {threshold:.3f}) ==\n")
    print(f"  {len(rows)} printed sentences: {len(clean)} clean-side, {len(low)} below, "
          f"{len(gaps)} template gaps (no reading).")
    for r in low:
        print(f"    below: {r['text']!r} score {r['score']:.3f}")
    for r in gaps:
        print(f"    gap:   {r['text']!r}")


def mean_cos(pairs):
    return float(np.mean([float(a["emb"] @ b["emb"]) for a, b in pairs])) if pairs else float("nan")


def check_a(rows):
    same, other_type, same_type = [], [], []
    for a, b in combinations(rows, 2):
        if a["scene"] != b["scene"]:
            continue
        if a["diff"] == b["diff"] and a["row"] == b["row"]:
            same.append((a, b))
        elif a["diff"] != b["diff"] and a["row"] != b["row"]:
            other_type.append((a, b))
        elif a["diff"] != b["diff"]:
            same_type.append((a, b))
    print("\n== Check A: closeness in the version-2 space (text tower cosines) ==\n")
    print(f"  same diff, different wording:            {mean_cos(same):.2f}   ({len(same)} pairs)")
    print(f"  same scene, different diff, other type:  {mean_cos(other_type):.2f}   ({len(other_type)} pairs)")
    print(f"  same scene, different diff, same type:   {mean_cos(same_type):.2f}   ({len(same_type)} pairs)")
    print("  (the third is high by design: a structural space conflates same-skeleton diffs)")


def check_b(rows):
    print("\n== Check B: section 6's mapping, row by row ==\n")
    print(f"  {'diff type':12} {'predicted':12} {'read as predicted':>18}")
    for row in ("describing", "narrating", "explaining", "grounding"):
        rs = [r for r in rows if r["row"] == row]
        hits = [r for r in rs if row in r["roots"]]
        print(f"  {row:12} {row:12} {f'{len(hits)}/{len(rs)}':>18}")
    misses = [r for r in rows if r["row"] not in r["roots"]]
    if misses:
        print("\n  natural form, read wrong (the information for the next layer):")
        for r in misses:
            print(f"    [{r['row']:10}] {r['text']!r} -> roots {r['roots'] or ['(no reading)']}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = sentences()
    determine_all(rows)
    check_null(rows)
    check_a(rows)
    check_b(rows)


if __name__ == "__main__":
    main()
