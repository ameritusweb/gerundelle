"""Scripted pushes through SealWorld: a jar filled, sealed by another, the owner blocked, a launch through the seal."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lock_world import SealWorld  # noqa: E402

w = SealWorld(2)
steps = [("A", ("light", "jar1", "empty")), ("A", ("light", "jar1", "charged")), ("B", ("seal", "jar1", "brimming")),
         ("A", ("hard", "jar1", "brimming sealed by B")), ("A", ("seal", "jar1", "brimming sealed by B")),
         ("A", ("light", "hollow1", "shaping")), ("A", None), ("A", ("hard", "skiff1", "resting")), ("A", None),
         ("A", None), ("A", None), ("A", None), ("B", ("seal", "jar1", "empty sealed by B"))]
for actor, inv in steps:
    w.actor = actor
    print(actor, inv, w.act(inv))
print(w.states(), w.blocked, w.history[0]["total"], w.history[-1]["total"])
