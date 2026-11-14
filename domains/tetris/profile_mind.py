"""Profile the tetris mind (run.py's setup, luck 0.7) with progress: every 50 slices the slice, the time, the slices per second over the
last 50, and the counts that grow (prediction SOVs, structures in the SOV, abstracts); every 200 slices the functions taking the most
time so far. Run: python -u -X utf8 profile_mind.py [slices]"""
import cProfile
import io
import pstats
import sys
import time

import run
from molecules import Params
from potential import ForceMind
from sov_agent import SovAgent
from world import TetrisWorld

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
w = TetrisWorld(seed=0, luck=0.7)
a = SovAgent(w, ForceMind(Params(**run.SWITCHES)))
a.mind.p.acceptance = 6
und = a.mind.understanding
pr = cProfile.Profile()
t0 = last = time.time()
for t in range(1, N + 1):
    pr.enable()
    a.mind.potentials = w.potentials()
    a.tick()
    pr.disable()
    if t % 50 == 0:
        now = time.time()
        print(f"slice {t}: {now - t0:.0f}s, {50 / (now - last):.2f} slices/s; games {len(w.games)}, rows {w.lines}; "
              f"prediction SOVs {len(und.__dict__.get('prediction_sovs', {}))}, concepts in the SOV {len(und.rel)}, "
              f"abstracts {len(und.abstracts)}, concept abstracts {len(und.__dict__.get('concept_abstracts', []))}, "
              f"shared searches cached {len(und.shared_cache)}", flush=True)
        last = now
    if t % 200 == 0:
        s = io.StringIO()
        pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(25)
        print("\n".join(l for l in s.getvalue().splitlines() if l.strip())[-1200:], flush=True)
pr.dump_stats("profile_mind.prof")
