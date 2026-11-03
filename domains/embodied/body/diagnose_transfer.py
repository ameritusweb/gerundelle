"""Where transfer loses attempts: in each new task, every failure is either of a kind never met before (unavoidable
by what was learned) or of a kind already learned that the constraints did not foresee in the new scene (a
transfer failure). Counted for the hand-written vocabulary and for tags minted with deliberate near misses.

    python -X utf8 body/diagnose_transfer.py
"""
import collections
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grasp as G  # noqa: E402

tasks = {L: G.task(L) for L in (200, 201, 202)}
count = {m: collections.Counter() for m in ("vocabulary", "minted")}
missed = {m: collections.Counter() for m in ("vocabulary", "minted")}
for order in G.orders(20):
    # hand-written vocabulary of tags
    h = []
    G.episode_perceived(*tasks[200], h, "x", order)
    known = {ev for _, ev in h}
    for L in (201, 202):
        hh = list(h)
        n0 = len(hh)
        G.episode_perceived(*tasks[L], hh, "x", order)
        for t, ev in hh[n0:]:
            if ev == "held":
                continue
            kind = "learned kind, not foreseen" if ev in known else "new kind"
            count["vocabulary"][kind] += 1
            if ev in known:
                missed["vocabulary"][ev] += 1
    # minted with deliberate near misses
    h, v = [], G.Vocabulary("probe")
    G.episode_probing(*tasks[200], h, v, "x", order)
    known = {ev for _, _, ev in h}
    for L in (201, 202):
        hh, vv = list(h), G.Vocabulary("probe")
        vv.cuts = list(v.cuts)
        n0 = len(hh)
        G.episode_probing(*tasks[L], hh, vv, "x", order)
        for r, g, ev in hh[n0:]:
            if ev == "held":
                continue
            kind = "learned kind, not foreseen" if ev in known else "new kind"
            count["minted"][kind] += 1
            if ev in known:
                missed["minted"][ev] += 1
print("failures in the new tasks, over 20 tie orders, both new tasks together:")
for m in count:
    print(f"  {m:11} {dict(count[m])}   learned kinds missed: {dict(missed[m])}")
