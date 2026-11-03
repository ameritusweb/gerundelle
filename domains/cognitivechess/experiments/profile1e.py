"""Rung 1e: time per tick and progress over a short run, and the top of a profile."""
import cProfile
import os
import pstats
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1e  # noqa: E402

arm, ticks = sys.argv[1], int(sys.argv[2])
t0 = time.time()
pr = cProfile.Profile()
pr.enable()
per, done, noticed, m = rung1e.run(0, arm, 20, ticks)
pr.disable()
dt = time.time() - t0
print(f"{arm}: {ticks} ticks in {dt:.0f}s ({dt / ticks:.3f}s/tick); positions mated {done}; pushes {per}; noticed {noticed}; "
      f"pool {len(m.agent.mind.pool)}; known pushes {len(m.agent.known)}")
pstats.Stats(pr).sort_stats("cumulative").print_stats(14)
