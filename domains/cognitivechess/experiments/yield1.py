"""Rung 1 (reply perceived), converge + sub_yield, one seed: at each yield, the sub-want left, the configuration, the
root step taken, and what the episode's moves then were."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1  # noqa: E402
from chessworld import RUNG1, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

seed = int(sys.argv[1])
w = ChessWorld(RUNG1, order=seed, seed=seed, reply="recapture", moves=2, relations=("reply",))
m = GerundelleMind("White", w, want=rung1.WANT, want_count=10 ** 6)
for k, v in rung1.ARMS["c_yield"].items():
    setattr(m.agent.mind.p, k, v)
a = m.agent
eps, act = collections.defaultdict(list), w.act


def logged(inv=None, hold=False):
    ep, cfg = len(w.episodes), w.config
    ev = act(inv, hold)
    if inv is not None:
        eps[ep].append((cfg, inv[0].split(" ", 1)[-1], a.mind.t, [e for e in ev if "material" in e]))
    elif any("material" in e for e in ev):
        eps[ep].append((cfg, "", a.mind.t, [e for e in ev if "material" in e]))
    return ev


w.act = logged
m.run(800)
yields = [(t, g) for t, g, k in a.sub_log if k == "yielded"]
summary = collections.Counter()
for t, g in yields:
    ep = next((e for e, rows in eps.items() if any(r[2] >= t for r in rows)), None)
    rows = eps.get(ep, [])
    moves = [r[1] for r in rows if r[1]]
    won = any("-> up" in x for r in rows for x in r[3])
    cfg = rows[0][0] if rows else None
    summary[(g, "defended" if cfg == 0 else "hanging", " ".join(moves), "won" if won else "not")] += 1
for k, v in summary.most_common(10):
    print(v, k)
