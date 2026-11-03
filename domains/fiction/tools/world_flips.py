"""Every state and flip both minds meet in a world (to write its lexicon): python tools/world_flips.py WORLD WANT"""
import os
import sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import worlds  # noqa: E402
from lean import LeanMind  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

make, want = getattr(worlds, sys.argv[1]), sys.argv[2]
w = make()
print("states:", w.states())
print("invitations:", sorted(w.invitations()))
flips, pushes = Counter(), Counter()
lm = LeanMind("Mara", make(), want=want)
for _ in range(300):
    lm.tick()
    if lm.done:
        break
print("lean reached:", lm.want.closed is not None, "tries", len(lm.tries))
for b in lm.beats:
    if b.kind in ("change", "other"):
        flips[(b.obj, b.detail["from"], b.detail["to"])] += 1
    if b.kind == "try":
        pushes[(b.detail["strength"], b.obj)] += 1
g = GerundelleMind("Mara", make(), want=want)
g.run(300)
print("gerundelle reached:", bool(g.agent.reached), "tries", len(g.agent.tried))
for b in g.beats:
    if b.kind in ("change", "other"):
        flips[(b.obj, b.detail["from"], b.detail["to"])] += 1
    if b.kind == "try":
        pushes[(b.detail["strength"], b.obj)] += 1
print("flips:", sorted(flips))
print("pushes:", sorted(pushes))
