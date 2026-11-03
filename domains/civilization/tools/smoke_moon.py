"""Scripted pushes through MoonWorld: unmaking, forming, a failed hop (unlit), fusing, and the voyage home."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from moon_world import MoonWorld  # noqa: E402

w = MoonWorld()
seq = [("light", "flask", "empty"), ("hard", "husk", "resting"), None,
       ("light", "flask", "empty"), ("light", "flask", "charged"), ("light", "basin", "shaping"), None,
       ("hard", "skiff", "moored"), None, None,                                   # unlit, flask 7: hops, falls back
       ("light", "flask", "empty"), ("light", "flask", "charged"), ("hard", "lantern", "resting"), None,
       ("light", "flask", "charged"), ("hard", "skiff", "lit"), None, None, None, None, None]
for inv in seq:
    print(inv, w.act(inv))
print(w.states())
print(w.history[0]["total"], w.history[-1])
