"""Scripted pushes through LockWorld: a keeper shuts its lid, another is locked out, the keeper opens it."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lock_world import LockWorld  # noqa: E402

w = LockWorld(2)
steps = [("A", ("light", "jar1", "empty")), ("A", ("light", "lid1", "open")), ("B", ("hard", "jar1", "charged")),
         ("B", ("light", "lid1", "shut")), ("A", ("light", "jar1", "charged")), ("A", ("light", "lid1", "shut")),
         ("A", ("light", "jar1", "charged"))]
for actor, inv in steps:
    w.actor = actor
    print(actor, inv, w.act(inv))
print(w.states(), w.blocked, w.history[0]["total"], w.history[-1]["total"])
