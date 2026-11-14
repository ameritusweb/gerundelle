"""The attention gate (trace_abstract_reach.log: no fill placement was ever attended, so Abstract never read one and nothing was told).
Understanding cues a concept's SOV (sov:<c> in the pool) when (a) it is the dominant phase's anchor; (b) an ownership instance winning the
top serves it (Territory.serve: the claims on the instance's region, and its region's own concepts, pushes excepted) and it has needed
slots; or (c) an instance of it won the top, it matters (with a territory: what the open slots serve, and what leads by a link funded 1+
to something that matters) and it has open slots; at most Params.sov_cues a tick. Replays seed 0 and, at each turn of the mind's in game
3's endgame, for each placement on a held point on offer: whether it won the top, whether it matters, whether it is served (and its pay),
which regions it is a claim on, its open and needed slots, and how many SOVs were cued that tick and on what.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_attention.py [from slice, to slice]"""
import collections
import sys

import run
from world import opportunity

sys.stdout.reconfigure(encoding="utf-8")
LO, HI = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (700, 768)
a, w = run.build(0, 0.7)
und, terr, mind = a.mind.understanding, a.mind.territory, a.mind
read = 0
tally = collections.Counter()
print(f"sov_cues {mind.p.sov_cues}")
for t in range(HI):
    a.mind.potentials = w.potentials()
    invs = w.invitations()
    before = {i for i in mind.pool if i.startswith("sov:")}
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    if t < LO or not invs:
        continue
    cued = sorted(i[4:] for i in mind.pool if i.startswith("sov:") and i not in before)
    winners = {i.split("|")[0] for i in rec["levels"][-1]["winners"]} if rec.get("levels") else set()
    served = terr.served or {}
    own_top = [i for i in (rec["levels"][-1]["winners"] if rec.get("levels") else []) if i.startswith("own:")]
    print(f"slice {t}: cued this tick {cued[:6]}; ownership instances at the top {own_top[:4]}; matters {len(und.matters)}, served {len(served)}")
    for inv in invs:
        if inv[0] != "place":
            continue
        c = w.target(inv)
        if terr.rows.get(opportunity(c), {}).get("holder") != "mine":
            continue
        iid = f"place_push:{inv[1]}_{inv[2]}"
        claims_on = sorted(r for r, row in terr.rows.items() if iid in row["claims"])
        won = iid in winners
        matters = iid in und.matters
        sv = served.get(iid)
        need = und.needed(iid)
        open_ = und.open_slots(iid)
        print(f"    held {c} {inv[2]}: won the top {won}; matters {matters}; served {sv and (round(sv[0], 2), sv[1])}; claim on {claims_on[:4]}; "
              f"open slots {sorted(open_)[:5]}; needed {need and sorted(need)[:5]}; sov in pool {('sov:' + iid) in mind.pool}")
        tally[(("won" if won else "lost the top"), ("matters" if matters else "doesn't matter"), ("served" if sv else "not served"),
               ("a claim" if claims_on else "a claim on nothing"))] += 1
print("\nheld placements on offer:", sorted(tally.items(), key=lambda x: -x[1]))
