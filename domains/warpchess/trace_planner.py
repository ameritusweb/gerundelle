"""Trace (rung 4, own_wants + subwants + sub_yield, placed goal): why the planner (imagined_lines) almost never finds a way to a sub-want.
For each plan made while a sub-want is held: the roots (moves on offer that won the top level), each root's recorded outcome in this situation
and its reward, how many moves the imagined tournament admits at the next step, the best line's worth; and whether any move the mind has
made ever brought the sub-want's state."""
import collections
import sys

import gameworld
import rung4
import sov_agent
from sov_agent import inv_id

sys.stdout.reconfigure(encoding="utf-8")
from imagine import Imagines
IMAGINE = "imagine" in sys.argv


class ImaginingGame(Imagines, gameworld.GameWorld):
    pass


mind = rung4.learned(1, 1000, True)
w = (ImaginingGame if IMAGINE else gameworld.GameWorld)(seed=1)
w.owned = True
w.actor = "White"
a = rung4.Player(w, "game", mind=mind)
rung4.switch(a.mind, True)
for k in ("own_wants", "subwants", "sub_yield"):
    setattr(a.mind.p, k, True)
a.mind.p.imagine = IMAGINE
terr = a.mind.territory
terr.given = w.white_pieces()
for r in terr.given:
    terr.row(r)
terr.update(terr.given)
black = gameworld.RandomSide(w, 1)
rows = []
real = sov_agent.imagined_lines
def traced(model, s, roots, horizon=3, gamma=1.0):
    out = real(model, s, roots, horizon, gamma)
    if a.stack:   # a sub-want held
        info = []
        for root in roots[:6]:
            inv = a.known.get(root)
            pred = a.predict(inv, frozenset(x for x in s if not x.startswith(("made:", "line:")))) if inv else None
            nxt, r, _ = model.step(s, root)
            info.append((root[:30], "known here" if pred is not None else "never tried here", round(r, 2), len(model.actions(nxt))))
        ever = any(a.goal in names for _, _, names in a.pushed)
        rows.append(dict(t=a.mind.t, want=a.goal, roots=len(roots), info=info, worth=round(out[1], 2), ever=ever))
    return out
sov_agent.imagined_lines = traced
import offers
offers.imagined_lines = traced
for r in range(400):
    if w.board.turn == 1:
        w.actor = "White"
        for _ in range(rung4.TURN_STEPS):
            if a.goal is None:
                a.goal = rung4.GOAL
            n = len([x for x in w.log if x[2]])
            a.tick()
            if len([x for x in w.log if x[2]]) > n:
                break
    else:
        black.tick()
        w.actor = "White"
        a.tick()
print("imagine:", IMAGINE, "| imagined lines:", len(getattr(w, "_imagined", {})))
print("plans made while a sub-want was held:", len(rows))
print("roots per plan:", collections.Counter(r["roots"] for r in rows).most_common(6))
print("worth > 0:", sum(r["worth"] > 0 for r in rows))
print("sub-want states some move of the mind's had ever brought:", collections.Counter((r["want"], r["ever"]) for r in rows).most_common(8))
roots = [i for r in rows for i in r["info"]]
print("roots: recorded here / never tried here:", collections.Counter(i[1] for i in roots), "; reward > 0:", sum(i[2] > 0 for i in roots))
print("moves admitted at the next imagined step:", collections.Counter(i[3] for i in roots).most_common(6))
for r in rows[:5]:
    print(r)
