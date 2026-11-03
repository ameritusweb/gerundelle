"""Seed 6 (rung 1, both): around each sub-want met, the moves made, the configuration, and what followed."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1  # noqa: E402
from chessworld import RUNG1, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

w = ChessWorld(RUNG1, order=6, seed=6, reply="recapture", moves=2)
m = GerundelleMind("White", w, want=rung1.WANT, want_count=10 ** 6)
for k, v in rung1.ARMS["both"].items():
    setattr(m.agent.mind.p, k, v)
a = m.agent
rows, act = [], w.act


def logged(inv=None, hold=False):
    t, ep, cfg, moved, goal, run = a.mind.t, len(w.episodes), w.config, w.moved, a.goal, a.running
    ev = act(inv, hold)
    if inv is not None or ev:
        rows.append((t, ep, cfg, moved, inv[0].split(" ", 1)[-1] if inv else "", goal, (run or "")[:28],
                     [e for e in ev if "material" in e or "a6" in e]))
    return ev


w.act = logged
m.run(800)
met = [t for t, g, k in a.sub_log if k == "met" and g == "white_bishop_a6_hanging"]
print("first sub-want sets/mets:", [(t, g, k) for t, g, k in a.sub_log][:6])
for t0 in met[:4]:
    print(f"--- met at t{t0}")
    for r in rows:
        if t0 - 6 <= r[0] <= t0 + 8:
            print(f"  t{r[0]} ep{r[1]} {'DEF' if r[2] == 0 else 'hng'} moved={r[3]} {r[4]:5} goal={r[5]} run={r[6]} {r[7]}")
