"""Replay one rung-7 story: python tools/rung7_path.py MR LR round:move ..."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung7  # noqa: E402

mr, lr = float(sys.argv[1]), float(sys.argv[2])
plan = {int(a.split(":")[0]): a.split(":")[1] for a in sys.argv[3:]}
s = rung7.State(mr, lr)
while not s.over():
    m = plan.get(s.round, "on")
    if m != "on":
        assert m in s.available(), (s.round, m, s.available())
    s.apply(m)
    s.advance()
for i, b in enumerate(s.beats):
    d = {k: v for k, v in b.detail.items() if k not in ("unexpected",)}
    print(i, b.t, b.actor, b.kind, b.obj, d)
print("ending", s.ending(), "moves", s.moves)
