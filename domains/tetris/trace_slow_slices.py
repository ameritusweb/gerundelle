"""Which slices are slow, and what they spend it on (the user, 2026-11-12: most slices are fast, some take 16-20 seconds): run from a
checkpoint as watch_mind does, time each slice, and for any over SLOW seconds print what took the time (cProfile of that slice alone).
Run: python -u -X utf8 trace_slow_slices.py [checkpoint] [slices]"""
import cProfile
import io
import pstats
import sys
import time

PATH = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/clean_8000.pkl"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 300
SLOW = 5.0
sys.argv = sys.argv[:1]
sys.path.insert(0, ".")
import checkpoint  # noqa: E402
import run  # noqa: E402
import watch_mind as wm  # noqa: E402

a, w, t = checkpoint.load(PATH)
wm.amnesia(a, w)
times, shown = [], 0
for k in range(N):
    pr = cProfile.Profile()
    t0 = time.time()
    pr.enable()
    a.mind.potentials = w.potentials()
    a.tick()
    run.earn_luck(a, w)
    run.own_clears(a, w)
    run.own_open_rows(a, w)
    pr.disable()
    dt = time.time() - t0
    times.append(dt)
    t += 1
    if dt > SLOW and shown < 4:
        shown += 1
        s = io.StringIO()
        pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(16)
        print(f"slice {t}: {dt:.1f}s", flush=True)
        print("\n".join(l for l in s.getvalue().splitlines() if l.strip().startswith(tuple("0123456789")))[:2600], flush=True)
slow = [(i, round(d, 1)) for i, d in enumerate(times) if d > SLOW]
print(f"{N} slices: median {sorted(times)[N // 2]:.2f}s, slow ones (over {SLOW}s): {len(slow)} at offsets {slow[:12]}")
