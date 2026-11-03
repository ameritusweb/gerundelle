"""Learning across more than one mug: learn on all but one of the grasp tasks in turn (what was learned on each
carried into the next), then take the one held out. Each task held out once; 20 tie orders.

    python -X utf8 body/leave_one_out.py [tasks]      (default 200 201 202; all six: 200 201 202 203 204 205)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grasp as G  # noqa: E402

ALL = tuple(int(a) for a in sys.argv[1:]) or (200, 201, 202)
tasks = {L: G.task(L) for L in ALL}
names = {200: "chipped mug", 201: "it turned", 202: "diner mug", 203: "new diner", 204: "stoneware", 205: "blue mug"}


def run(kind, learn, test, order):
    if kind == "relational":
        cons = []
        for L in learn:
            w, p = tasks[L]
            G.episode(w, cons, "x", p, True, save=False, quiet=True, order=order)
        w, p = tasks[test]
        return len(G.episode(w, list(cons), "x", p, True, save=False, quiet=True, order=order))
    if kind == "vocabulary":
        h = []
        for L in learn:
            G.episode_perceived(*tasks[L], h, "x", order)
        return G.episode_perceived(*tasks[test], list(h), "x", order)
    mode, ep = ("margin", G.episode_minted) if kind == "minted" else ("probe", G.episode_probing)
    h, v = [], G.Vocabulary(mode)
    for L in learn:
        ep(*tasks[L], h, v, "x", order)
    vv = G.Vocabulary(mode)
    vv.cuts = list(v.cuts)
    return ep(*tasks[test], list(h), vv, "x", order)


kinds = {"relational": "hand-written, relational", "vocabulary": "perceived, hand-written vocabulary",
         "minted": "perceived, minted (widest margin)", "probe": "perceived, minted (deliberate near misses)"}
print("attempts to the first hold on the held-out task, after learning on all the others (20 tie orders: mean, worst)")
print(f"  {'':44}" + "".join(f"{names[t]:>18}" for t in ALL) + f"{'all':>8}")
for kind, label in kinds.items():
    cells, alls = [], []
    for test in ALL:
        learn = [L for L in ALL if L != test]
        xs = [run(kind, learn, test, order) for order in G.orders(20)]
        alls += xs
        cells.append(f"{np.mean(xs):9.1f} (max {max(xs):2})")
    print(f"  {label:44}" + "".join(f"{c:>18}" for c in cells) + f"{np.mean(alls):8.2f}", flush=True)
