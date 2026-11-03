"""Rung 1 with converge, one seed: which path chose each push, by configuration, and the constraints at the end."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1  # noqa: E402
from chessworld import RUNG1, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402
from sov_agent import constraints_from  # noqa: E402

seed = int(sys.argv[1])
w = ChessWorld(RUNG1, order=seed, seed=seed, reply="recapture", moves=2, relations=tuple(sys.argv[2:]))
m = GerundelleMind("White", w, want=rung1.WANT, want_count=10 ** 6)
for k, v in rung1.ARMS["converge"].items():
    setattr(m.agent.mind.p, k, v)
a = m.agent
src = {}
op, on = a.plan_step, a.notice


def plan_step(invs, **kw):
    s = op(invs, **kw)
    if s is not None:
        src[a.mind.t] = "planner(sub)" if a.stack else "planner"
    return s


def notice(invs):
    s = on(invs)
    if s is not None:
        src[a.mind.t] = "noticed"
    return s


a.plan_step, a.notice = plan_step, notice
act, c = w.act, collections.Counter()


def logged(inv=None, hold=False):
    if inv is not None:
        c[(w.config, src.get(a.mind.t, "experiment" if a.queue or a.running else "other"))] += 1
    return act(inv, hold)


w.act = logged
for _ in range(800):
    m.step(len(a.tried))
print(sorted(c.items()))
print("contradicted:", sum(1 for _, x in a.noticed if isinstance(x, tuple) and x[0] == "contradicted"),
      "noticed:", sum(1 for _, x in a.noticed if not (isinstance(x, tuple) and x[0] == "contradicted")))
print("trial kinds:", collections.Counter(k[:40] for _, k in a.trials).most_common(6))
print("constraints:", {e[:30]: [" ".join(sorted(h)) for h in hs] for e, hs in constraints_from(a.trials).items()})
