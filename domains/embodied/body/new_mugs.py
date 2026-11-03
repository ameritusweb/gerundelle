"""Generalizing to mugs no method has learned on: learn on the three first tasks in turn (the chipped mug, it turned,
the diner mug), then take each of three new mugs: the new diner mug with its handle toward the near side, the
stoneware mug (wider, thicker, uneven) with its handle toward the far side, the blue mug with its handle toward
the right; the bottle beside each on the side away from its handle. 20 tie orders.

    python -X utf8 body/new_mugs.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grasp as G  # noqa: E402

LEARN, TESTS = (200, 201, 202), (203, 204, 205)
tasks = {L: G.task(L) for L in LEARN + TESTS}
names = {203: "new diner mug", 204: "stoneware mug", 205: "blue mug"}


def learned(kind, order):
    """What a method carries out of learning on the three first tasks."""
    if kind == "relational":
        cons = []
        for L in LEARN:
            w, p = tasks[L]
            G.episode(w, cons, "x", p, True, save=False, quiet=True, order=order)
        return cons
    if kind == "vocabulary":
        h = []
        for L in LEARN:
            G.episode_perceived(*tasks[L], h, "x", order)
        return h
    mode, ep = ("margin", G.episode_minted) if kind == "minted" else ("probe", G.episode_probing)
    h, v = [], G.Vocabulary(mode)
    for L in LEARN:
        ep(*tasks[L], h, v, "x", order)
    return h, v


def take(kind, carried, test, order):
    w, p = tasks[test]
    if kind == "relational":
        return len(G.episode(w, list(carried), "x", p, True, save=False, quiet=True, order=order))
    if kind == "vocabulary":
        return G.episode_perceived(w, p, list(carried), "x", order)
    h, v = carried
    mode, ep = ("margin", G.episode_minted) if kind == "minted" else ("probe", G.episode_probing)
    vv = G.Vocabulary(mode)
    vv.cuts = list(v.cuts)
    return ep(w, p, list(h), vv, "x", order)


if __name__ == "__main__":
    kinds = {"relational": "hand-written, relational", "vocabulary": "perceived, hand-written vocabulary",
             "minted": "perceived, minted (widest margin)", "probe": "perceived, minted (near misses)"}
    print("attempts to the first hold on each new mug, after learning on the three first tasks (20 orders: mean, worst)")
    print(f"  {'':38}" + "".join(f"{names[t]:>22}" for t in TESTS) + f"{'all':>8}")
    for kind, label in kinds.items():
        res = {t: [] for t in TESTS}
        for order in G.orders(20):
            carried = learned(kind, order)
            for t in TESTS:
                res[t].append(take(kind, carried, t, order))
        alls = [x for t in TESTS for x in res[t]]
        print(f"  {label:38}" + "".join(f"{np.mean(res[t]):12.1f} (max {max(res[t]):2})" for t in TESTS)
              + f"{np.mean(alls):8.2f}", flush=True)
