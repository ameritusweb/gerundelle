"""Trace rung 1c's JustOne configuration in one seed: each episode's moves and what followed."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1c  # noqa: E402

w, m, log = rung1c.run(int(sys.argv[1]), "baseline", 800)
shown = 0
for ep, cfg, mv, ev in log:
    if cfg == rung1c.ONE and (mv or ev) and shown < 30:
        shown += 1
        print(f"ep{ep:3} {mv or '':6} {ev}")
