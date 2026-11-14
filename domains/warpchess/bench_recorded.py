"""Whether the Model.split memo (sov_agent.py, 2026-11-13) is exact: the rung4p game from rung 1's room, seed 0, for N of the mind's
slices, recording every move made, every commit and every tool call, and the time. Run it on the code before and after and compare
the two JSON files. Run: PYTHONHASHSEED=0 python -u -X utf8 bench_recorded.py <out.json> [slices]"""
import json
import sys
import time

import rung0  # noqa: F401
import rung4p
from gameworld import RandomSide
from plansworld import give
from rung4 import TURN_STEPS
from warpworld import RUNG1_TWO

OUT = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40
w, a = rung4p.build(0, RUNG1_TWO)
black = RandomSide(w, 0)
slices, t0, per = 0, time.time(), []
while slices < N:
    if w.board.turn == 1 and not w.over():
        w.actor = "White"
        n = len([x for x in w.log if x[2]])
        for _ in range(TURN_STEPS):
            ts = time.time()
            a.tick()
            give(a, w)
            per.append(time.time() - ts)
            slices += 1
            if len([x for x in w.log if x[2]]) > n or slices >= N:
                break
    elif not w.over():
        black.tick()
        w.actor = "White"
        ts = time.time()
        a.tick()
        give(a, w)
        per.append(time.time() - ts)
        slices += 1
    else:
        w.actor = "White"
        a.tick()
        give(a, w)
        slices += 1
out = dict(moves=[list(x[:3]) for x in w.log], commits=[list(map(str, x)) for x in a.__dict__.get("commit_log", [])],
           tools=[[str(x[0]), str(x[1]), str(x[3])] for x in a.__dict__.get("tool_log", [])],
           wants=[list(x) for x in a.sub_log], seconds=time.time() - t0, per_slice=per)
json.dump(out, open(OUT, "w"))
print(f"{N} slices in {out['seconds']:.0f}s; moves {sum(1 for m in out['moves'] if m[2])}, commits {len(out['commits'])}, tool calls {len(out['tools'])}")
