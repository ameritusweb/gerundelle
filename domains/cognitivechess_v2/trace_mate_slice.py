"""One slice of a fresh mind on a position with a mate in one: the top level's bids for the mate want and for each move, what the mating
move's molecule carries (tags, sites), and what won. python -X utf8 trace_mate_slice.py "<fen>" <mating uci> [slices]"""
import sys

import rung4p
from gameworld import RandomSide
from plansworld import give

sys.stdout.reconfigure(encoding="utf-8")
fen, mate_uci = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
w, a = rung4p.build(0, fen, dreams=True, half_moves=10 ** 6)
a.mind.p.dream_when_stuck = False
a.__dict__.pop("dreamer", None)
a.mind.p.dreams = False
a.mind.p.dream_for_want = True
give(a, w)
for k in range(n):
    choice, rec = a.tick()
    give(a, w)
    top = rec["levels"][-1]
    bids = top.get("bids", {})
    mate_ids = [i for i in bids if mate_uci in i]
    want_ids = [i for i in bids if "mate+0" in i]
    print(f"slice {k + 1}: chose {choice}; goal {a.goal}; stack {a.stack}")
    print(f"   top level winners: {top['winners'][:6]}")
    ranked = sorted(bids.items(), key=lambda x: -x[1])
    print(f"   top bids: {[(i[:60], round(v, 2)) for i, v in ranked[:8]]}")
    print(f"   mate move molecules' bids: {[(i[:60], round(bids[i], 2)) for i in mate_ids]}")
    print(f"   mate want molecules' bids: {[(i[:60], round(bids[i], 2)) for i in want_ids]}")
    for i in mate_ids[:2]:
        m = a.mind.pool.get(i)
        if m is not None:
            print(f"   {i[:50]} tags {sorted(m.tags)[:8]} sites {m.sites}")
    commits = [i for i in a.mind.pool if i.startswith("commit_push:potential_mate+0")]
    print(f"   mate commits in the pool: {[(i[:70], round(a.mind.pool[i].act, 3)) for i in commits]}")
    for L, lv in enumerate(rec["levels"]):
        lb = lv.get("bids", {})
        mine = {i[:50]: round(v, 2) for i, v in lb.items() if i.startswith("commit_push:potential_mate+0") or "mate+0" in i}
        best = sorted(lb.items(), key=lambda x: -x[1])[:3]
        print(f"   level {L}: {len(lb)} bids; mate commit/want {mine}; best {[(i[:45], round(v, 2)) for i, v in best]}; "
              f"res of a mate commit {[lv.get('res', {}).get(i) for i in commits][:2]}")
    sit = a.__dict__.get("situational") or {}
    print(f"   situational for the mate move: {[v for c, v in sit.items() if mate_uci in c]}")
    print(f"   row potential_mate+0: {({k_: v for k_, v in a.mind.territory.rows.get('potential_mate+0', {}).items() if k_ in ('holder', 'prediction')})}")
    if choice is not None:
        break
