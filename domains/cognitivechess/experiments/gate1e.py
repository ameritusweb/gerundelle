"""Rung 1e, converge: at each push, which path chose it (planner, noticed, sub-want, experiment step, experiment start),
and when notice was asked, why it returned nothing."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1e  # noqa: E402
from chessworld import ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402
import rung1d  # noqa: E402

fens = rung1d.positions(1000, 20)
w = ChessWorld(fens, order=0, reply="answer", moves=1, relations=("reply", "game"), sequence=True)
m = GerundelleMind("White", w, want=rung1e.WANT, want_count=10 ** 6)
for k, v in rung1e.ARMS["converge"].items():
    setattr(m.agent.mind.p, k, v)
a = m.agent
why = collections.Counter()
src = {}
op, on = a.plan_step, a.notice


def plan_step(invs, **kw):
    s = op(invs, **kw)
    if s is not None:
        src[a.mind.t] = "planner"
    return s


def notice(invs):
    s = on(invs)
    why["notice asked"] += 1
    if s is not None:
        src[a.mind.t] = "noticed"
    return s


a.plan_step, a.notice = plan_step, notice
act = w.act


def logged(inv=None, hold=False):
    if inv is not None:
        why[src.get(a.mind.t, "experiment step" if a.queue or a.running else "experiment start/other")] += 1
    return act(inv, hold)


w.act = logged
for _ in range(1200):
    m.step(len(a.tried))
print(dict(why), "positions mated", w.at)
