"""Why the mind turns away from a wheel where everything holds (rung 0, seed 0, 2026-11-14: halving held every test at slice 2 and again
at 34, 38, 58, ...; each time the next turn lost them). At each slice where every territory gerund holds, for each turn on offer: the
anti-want held and its targets; whether the mind's understanding links the turn (causes / prevents, any funding) to a target; its
lived and told links to any test failing; its bid at the top level, and whether it won; and what was chosen.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_settle.py [slices]"""
import sys

import graph as g
import run

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 90
FROM = int(sys.argv[2]) if len(sys.argv) > 2 else 0
RUNG = next((x.split("=")[1] for x in sys.argv if x.startswith("--rung=")), "0")
SEED = int(next((x.split("=")[1] for x in sys.argv if x.startswith("--seed=")), "0"))
a, w = run.build(RUNG, SEED, dream="--dream" in sys.argv)
und, mind = a.mind.understanding, a.mind
told = mind.p.credulity
for t in range(N):
    a.mind.potentials = w.potentials()
    invs = w.invitations()
    all_held = all(g.territory(w.shown).values()) and not w.unread
    targets = set(mind.__dict__.get("anti_targets") or ())
    anti = a.__dict__.get("anti")
    choice, rec = a.tick()
    run.give(a, w)
    if not all_held or t + 1 < FROM:
        continue
    lv = rec["levels"][-1] if rec.get("levels") else {"bids": {}, "winners": []}
    print(f"slice {t + 1}: everything held at {[w.p.shape.doing(c, x) for c, x in enumerate(w.pos)]} (after the choice); anti {anti} "
          f"({len(targets)} targets: {sorted(targets)[:4]}); chose {choice[0] if choice else None}; top winners {lv['winners'][:4]}")
    for inv in invs:
        iid = w.push_id(inv)
        rel = und.rel.get(iid, {})
        threat = [(k, o, round(e[0] + e[2] + told * e[1], 2)) for (k, o), e in rel.items()
                  if k in ("causes", "prevents") and o in targets and e[0] + e[2] + told * e[1] > 0]
        fails = [(k, o, tuple(round(x, 2) for x in e[:3])) for (k, o), e in rel.items() if "failing" in o]
        bid = max((v for i, v in lv["bids"].items() if i.split("|")[0] == iid), default=None)
        won = any(i.split("|")[0] == iid for i in lv["winners"])
        pot = a.mind.potentials.get(iid)
        print(f"    {inv[0]} (potential {pot}): threatens {threat[:3]} | links to failing (seen, told, worked) {fails[:3]} | bid {bid and round(bid, 2)} won {won}")
