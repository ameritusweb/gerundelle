"""Bench a speed fix from a checkpoint (the user, 2026-11-11: test speed fixes with the checkpoints). Loads a checkpoint (checkpoint.py),
runs the given number of slices, and prints the time, slices per second, the functions taking the most time on their own, and a signature
of the state after each slice (its last few, and one over all of them). Run it before and after a fix from the same checkpoint: the same
signatures mean the fix changed only speed. Run: PYTHONHASHSEED=0 python -u -X utf8 bench_from.py <checkpoint> [slices] [--no-profile]
"""
import cProfile
import hashlib
import io
import pstats
import sys
import time

import checkpoint
import run

sys.stdout.reconfigure(encoding="utf-8")
path = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 200
profile = "--no-profile" not in sys.argv


def signature(a, w):
    """The state after a slice: what the world shows, the mind's goal and stack, its pushes, its pool, its register's size, luck."""
    und = a.mind.understanding
    return hashlib.md5(repr((sorted(w.shown.items()), a.goal, tuple(a.stack), len(a.pushed), sorted(a.mind.pool),
                             sum(len(r) for r in und.rel.values()), w.luck)).encode()).hexdigest()[:10]


a, w, start = checkpoint.load(path)
if "--dormancy" in sys.argv:   # (a checkpoint saved before Params.dormancy has it off)
    a.mind.p.dormancy = True
print(f"loaded {path} at slice {start}; running {N} slices", flush=True)
pr = cProfile.Profile() if profile else None
sigs, t0 = [], time.time()
for t in range(N):
    if pr:
        pr.enable()
    a.mind.potentials = w.potentials()
    a.tick()
    run.earn_luck(a, w)
    run.own_open_rows(a, w)
    if pr:
        pr.disable()
    sigs.append(signature(a, w))
dt = time.time() - t0
print(f"{N} slices in {dt:.1f}s, {N / dt:.2f} slices/s{' (profiled: slower than without)' if pr else ''}")
print("signature, last 5 slices:", sigs[-5:])
print("signature, all slices:", hashlib.md5("".join(sigs).encode()).hexdigest()[:12])
if pr:
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(15)
    print("\n".join(l for l in s.getvalue().splitlines() if l.strip() and (l.lstrip()[:1].isdigit() or "ncalls" in l)))
if pr:
    pr.dump_stats("bench.prof")
