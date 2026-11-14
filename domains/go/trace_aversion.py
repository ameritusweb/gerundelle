"""Why the fills go on with the anti-want held (trace_opp_games_causes.log: after "causes = threat" for "a region I hold, <doing>", the
user, 2026-11-12, held_bearing stays held through the endgames, and games 3 and 5 still fill to the last eye). Replays seed 0 and, at
each turn of the mind's in the endgame windows, for every placement on a held point on offer: whether the SOV links it ("causes", any
funding) to one of the anti-want's targets (threatened), the funding of that link, its bid at the top level, and the choice. Also the
anti-want's targets: how many, and whether the point being filled is among them.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_aversion.py"""
import collections
import sys

import run
from world import opportunity

sys.stdout.reconfigure(encoding="utf-8")
WINDOWS = [(700, 772), (1370, 1428)]
N = WINDOWS[-1][1]
a, w = run.build(0, 0.7)
und, terr, mind = a.mind.understanding, a.mind.territory, a.mind
read = 0
told = mind.p.credulity
summary = collections.Counter()
for t in range(N):
    a.mind.potentials = w.potentials()
    invs = w.invitations()
    targets = set(mind.__dict__.get("anti_targets") or ())   # what the support in this tick reads (set by the last anti_update)
    anti = a.__dict__.get("anti")
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    if not invs or not any(lo <= t <= hi for lo, hi in WINDOWS):
        continue
    lv = rec["levels"][-1] if rec.get("levels") else {"bids": {}, "winners": []}
    rows = []
    for inv in invs:
        if inv[0] != "place":
            continue
        c = w.target(inv)
        if terr.rows.get(opportunity(c), {}).get("holder") != "mine":
            continue
        iid = f"place_push:{inv[1]}_{inv[2]}"
        links = [(o, round(e[0] + e[2] + told * e[1], 2)) for (k, o), e in und.rel.get(iid, {}).items()
                 if k in ("causes", "prevents") and o in targets and e[0] + e[2] + told * e[1] > 0]
        bid = max((v for i, v in lv["bids"].items() if i.split("|")[0] == iid), default=None)
        won = any(i.split("|")[0] == iid for i in lv["winners"])
        own_target = f"{opportunity(c)}_bearing" in targets
        rows.append((c, inv[2], bool(links), links[:2], bid and round(bid, 2), won, own_target))
    if not rows:
        continue
    chosen = None if choice is None else (w.target(choice) if choice[0] == "place" else choice[0])
    pass_bid = max((v for i, v in lv["bids"].items() if i.startswith("pass_push")), default=None)
    print(f"slice {t}: anti {anti} ({len(targets)} targets); chose {chosen}; pass bid {pass_bid and round(pass_bid, 2)}")
    for r in rows:
        print(f"    held {r[0]} {r[1]}: threatened {r[2]} {r[3]} | bid {r[4]} won {r[5]} | its own point's bearing among the targets {r[6]}")
        summary[("threatened" if r[2] else "not threatened", "chosen" if chosen == r[0] else "not chosen")] += 1
print("held placements on offer in the windows:", dict(summary))
