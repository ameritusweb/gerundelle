"""Whether the waking speed-up (imagine.py's single-move starts, cached; imagined moves not recorded as game positions; 2026-11-13) is
exact: rung 4p's room game with dreams, seed 0, N of the mind's slices, recording moves, commits, tool calls, wants, dreams (what about,
trials, edges), what waking gave each slice, and the time. Run on the code before and after and compare.
Run: PYTHONHASHSEED=0 python -u -X utf8 bench_dreams.py <out.json> [slices]"""
import json
import sys
import time

import rung0  # noqa: F401
import rung4p
from gameworld import RandomSide
from plansworld import give
from rung4 import TURN_STEPS
from warpworld import RUNG1_TWO

def main():
    global slices
    OUT = sys.argv[1]
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    w, a = rung4p.build(0, RUNG1_TWO, dreams=True)
    import os
    a.dream_workers = int(os.environ.get("DREAM_WORKERS", "0"))   # (dream.py's waves: 0 = one trial at a time)
    black = RandomSide(w, 0)
    slices, t0, woken, per = 0, time.time(), [], []


    def step():
        global slices
        ts = time.time()
        a.tick()
        give(a, w)
        per.append(round(time.time() - ts, 1))
        woken.append(getattr(a, "woken", 0) or 0)
        slices += 1


    while slices < N:
        if w.board.turn == 1 and not w.over():
            w.actor = "White"
            n = len([x for x in w.log if x[2]])
            for _ in range(TURN_STEPS):
                step()
                if len([x for x in w.log if x[2]]) > n or slices >= N:
                    break
        elif not w.over():
            black.tick()
            w.actor = "White"
            step()
        else:
            w.actor = "White"
            step()
    out = dict(moves=[list(x[:3]) for x in w.log], commits=[list(map(str, x)) for x in a.__dict__.get("commit_log", [])],
               tools=[[str(x[0]), str(x[1]), str(x[3])] for x in a.__dict__.get("tool_log", [])], wants=[list(x) for x in a.sub_log],
               dreams=[[x[0], x[1], x[2], x[3], x[4]] for x in a.__dict__.get("dreams_done", [])], woken=woken,
               dreamed=len(a.dreamed), timing=a.__dict__.get("dream_timing", []), edges=[[str(x[0]), sorted(x[3])] for x in a.__dict__.get("dream_edges", [])], seconds=time.time() - t0, per_slice=per)
    json.dump(out, open(OUT, "w"))
    print(f"{N} slices in {out['seconds']:.0f}s; per slice {per}")


if __name__ == "__main__":   # (worker processes re-import this module: dream.py's waves, spawned on Windows)
    main()
