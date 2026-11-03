"""Rung 1c, seed 8: where does each Rd8 in the JustOne configuration come from (plan, sub-want try, experiment)?"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1c  # noqa: E402
from chessworld import RUNG1C, RUNG1C_RELATIONS, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

w = ChessWorld(RUNG1C, order=8, seed=8, reply="answer", moves=2, relations=RUNG1C_RELATIONS)
m = GerundelleMind("White", w, want=rung1c.WANT, want_count=10 ** 6)
for k, v in rung1c.ARMS["baseline"].items():
    setattr(m.agent.mind.p, k, v)
a = m.agent
src, op = {}, a.planned


def planned(invs):
    step = op(invs)
    src[a.mind.t] = ("plan" if step is not None else "none", a.goal, (a.running or "")[:40], list(a.sub_log[-1:]))
    return step


a.planned = planned
act, out = w.act, collections.Counter()


def logged(inv=None, hold=False):
    if inv is not None and w.config == rung1c.ONE and "Rd8" in inv[0]:
        s = src.get(a.mind.t, ("?",))
        out[(s[0], s[1], s[2][:24])] += 1
    return act(inv, hold)


w.act = logged
m.run(800)
print("Rd8 in the JustOne configuration, by source:", out.most_common(6))
print("sub_log:", collections.Counter((g, k) for _, g, k in a.sub_log).most_common(5))
