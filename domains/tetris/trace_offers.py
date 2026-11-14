"""Trace how often a push is on offer to the tetris mind and how often it takes one (run.py's setup, luck 0.7, earned luck). Each slice is
put in one place: no falling piece (forming, resting, settling, blocks falling, clearing), the piece optimal (nothing on offer), or pushes
on offer, and then: the mind still watching its last push (a push's watch is the world's horizon), it pushed, or it didn't (and what it
was doing instead: an experiment's wait, or nothing won). Run: python -u -X utf8 trace_offers.py [slices]"""
import collections
import sys
import time

import run
from molecules import Params
from potential import ForceMind
from sov_agent import SovAgent
from world import TetrisWorld

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
w = TetrisWorld(seed=0, luck=0.7)
a = SovAgent(w, ForceMind(Params(**run.SWITCHES)))
a.mind.p.acceptance = 6
where, t0, top = collections.Counter(), time.time(), collections.Counter()
for t in range(N):
    a.mind.potentials = w.potentials()
    offered = w.invitations()
    falling = w.piece is not None and w.doing == "falling"
    watching = bool(a.watching)
    choice, rec = a.tick()
    run.earn_luck(a, w)
    if not falling:
        k = "no falling piece"
    elif not offered:
        k = "piece optimal: nothing on offer"
    elif watching:
        k = "offered: watching its last push"
    elif choice is not None:
        k = "offered: pushed"
    else:
        k = "offered: no push"
        won = [i for i in rec["levels"][-1]["winners"] if "_push:" in i]
        top["a push won the top level" if won else "no push won the top level"] += 1
        if rec.get("experiments"):
            top["an experiment won"] += 1
    where[k] += 1
    if (t + 1) % 200 == 0:
        print(f"slice {t + 1} ({time.time() - t0:.0f}s): {dict(where)}", flush=True)
print("slices:", dict(where))
print("offered but no push:", dict(top))
print("luck", w.luck, "earned", w.earned, "| pieces cleared", w.pieces_cleared, "rows", w.lines)
