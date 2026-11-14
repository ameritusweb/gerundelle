"""Bench a speed fix from a checkpoint, as bench_from.py, with a signature that reads the mind's state exactly (every activation,
surprise, precision and SOV weight at full precision, the territory's holders, the meta layer's log), so a fix that changes anything
the mind holds shows. Run before and after from the same checkpoint with the same PYTHONHASHSEED:
PYTHONHASHSEED=0 python -u -X utf8 bench_speed.py <checkpoint> [slices] [--profile [file.prof]]
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
N = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 80
profile = "--profile" in sys.argv
prof_file = sys.argv[sys.argv.index("--profile") + 1] if profile and len(sys.argv) > sys.argv.index("--profile") + 1 else "bench_speed.prof"


def signature(a, w):
    m = a.mind
    und, terr = m.understanding, m.territory
    parts = (
        sorted(w.shown.items()), w.luck, a.goal, tuple(a.stack), len(a.pushed), repr(a.pushed[-1:]),
        sorted((i, x.act, x.c, x.last_level, sorted(x.tags), x.sites) for i, x in m.pool.items()),
        sorted(m.S.items()), sorted(m.pi.items()), sorted(m.top_wins.items()), len(m.boxes),
        sorted((c, sorted((repr(k), repr(v)) for k, v in r.items())) for c, r in und.rel.items()),
        sorted((r, row.get("holder")) for r, row in terr.rows.items()),
        len(m.meta.log), repr(m.meta.log[-3:]), sorted(m.meta.splits),
        len(a.sub_log), repr(a.sub_log[-3:]), len(a.__dict__.get("prediction_answers", [])),
    )
    return hashlib.md5(repr(parts).encode()).hexdigest()[:10]


a, w, start = checkpoint.load(path)
print(f"loaded {path} at slice {start}; running {N} slices", flush=True)
pr = cProfile.Profile() if profile else None
sigs, t0 = [], time.time()
for t in range(N):
    if pr:
        pr.enable()
    a.mind.potentials = w.potentials()
    a.tick()
    run.earn_luck(a, w)
    if pr:
        pr.disable()
    sigs.append(signature(a, w))
    if (t + 1) % 20 == 0:
        print(f"  {t + 1} slices, {time.time() - t0:.1f}s", flush=True)
dt = time.time() - t0
print(f"{N} slices in {dt:.1f}s, {N / dt:.2f} slices/s{' (profiled: slower than without)' if pr else ''}")
print("signature, last 5 slices:", sigs[-5:])
print("signature, all slices:", hashlib.md5("".join(sigs).encode()).hexdigest()[:12])
if pr:
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(40)
    print("\n".join(l[:200] for l in s.getvalue().splitlines() if l.strip() and (l.lstrip()[:1].isdigit() or "ncalls" in l)))
    pr.dump_stats(prof_file)
