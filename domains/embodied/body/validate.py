"""Validation on mugs nothing was tuned on: learn on all six tasks of the seed-7 scene, then take each of the six
tasks of a seed-11 scene (the same kinds of mug, different individuals: their own dimensions, ages, wear, stains,
turns). Every threshold and design choice was settled on seed 7; nothing is changed for seed 11. 20 tie orders.

    python -X utf8 body/validate.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grasp as G  # noqa: E402

LAYOUTS = (200, 201, 202, 203, 204, 205)
train = {L: G.task(L, 7) for L in LAYOUTS}
test = {L: G.task(L, 11) for L in LAYOUTS}
names = {200: "chipped mug", 201: "it turned", 202: "diner mug", 203: "new diner", 204: "stoneware", 205: "blue mug"}


def first_hold(kind, order):
    if kind == "relational":
        cons = []
        for L in LAYOUTS:
            w, p = train[L]
            G.episode(w, cons, "x", p, True, save=False, quiet=True, order=order)
        return {L: len(G.episode(test[L][0], list(cons), "x", test[L][1], True, save=False, quiet=True, order=order))
                for L in LAYOUTS}
    if kind == "vocabulary":
        h = []
        for L in LAYOUTS:
            G.episode_perceived(*train[L], h, "x", order)
        return {L: G.episode_perceived(*test[L], list(h), "x", order) for L in LAYOUTS}
    mode, ep = ("margin", G.episode_minted) if kind == "minted" else ("probe", G.episode_probing)
    h, v = [], G.Vocabulary(mode)
    for L in LAYOUTS:
        ep(*train[L], h, v, "x", order)
    out = {}
    for L in LAYOUTS:
        vv = G.Vocabulary(mode)
        vv.cuts = list(v.cuts)
        out[L] = ep(*test[L], list(h), vv, "x", order)
    return out


if __name__ == "__main__":
    kinds = {"relational": "hand-written, relational", "vocabulary": "perceived, hand-written vocabulary",
             "minted": "perceived, minted (widest margin)", "probe": "perceived, minted (near misses)"}
    print("attempts to the first hold on the seed-11 tasks, after learning on all six seed-7 tasks (20 orders)")
    print(f"  {'':38}" + "".join(f"{names[L]:>16}" for L in LAYOUTS) + f"{'all':>8}")
    for kind, label in kinds.items():
        res = {L: [] for L in LAYOUTS}
        for order in G.orders(20):
            for L, n in first_hold(kind, order).items():
                res[L].append(n)
        alls = [x for L in LAYOUTS for x in res[L]]
        print(f"  {label:38}" + "".join(f"{np.mean(res[L]):8.1f} (max {max(res[L]):2})" for L in LAYOUTS)
              + f"{np.mean(alls):8.2f}", flush=True)
