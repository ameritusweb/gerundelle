"""The repair's yardstick (DRIFT.md): the SOV-driven agent against the earlier one, per library
world, scored on the held answer keys over seeds."""
import sys

import curriculum_worlds as C
from force_world import ForceAgent, phase
from sov_agent import SovAgent

sys.stdout.reconfigure(encoding="utf-8")
TICKS = int(sys.argv[1]) if len(sys.argv) > 1 else 150
tot = {"old": 0.0, "new": 0.0}
for name in C.library():
    row = {}
    for kind, cls in (("old", ForceAgent), ("new", SovAgent)):
        vals = []
        for s in range(3):
            with phase(s):
                w = C.library()[name]
                a = cls(w)
                for _ in range(TICKS):
                    a.tick()
                vals.append(C.right_all(C.readout(a, w, C.PROBES[name])[0]))
        row[kind] = sum(vals) / len(vals)
        tot[kind] += row[kind] / len(C.library())
    print(f"{name:10s} old {row['old']:.2f}  new {row['new']:.2f}", flush=True)
print(f"mean       old {tot['old']:.3f}  new {tot['new']:.3f}")
