"""F0-2 and F0-3 on the force world (LADDER.md, the force world, rung 0): one seed run in-process, then the mind's understanding read:
  F0-2: splits (meta.splits) whose condition is a count (load_ / pulse_ / want_), and conditions links on counts;
  F0-3: funded links from a turn to a pulse ("turning ... causes pulse_..._rising_<n>").
Also the count wants (load_/pulse_ set as sub-wants) traced: which path set them.
python -X utf8 probe_force_world.py [rung] [seed] [slices]"""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
import run

rung = sys.argv[1] if len(sys.argv) > 1 else "0"
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
slices = int(sys.argv[3]) if len(sys.argv) > 3 else 600
a, w = run.build(rung, seed, 6, True, 2.0)
for t in range(slices):
    a.mind.potentials = w.potentials()
    a.tick()
    run.give(a, w)
und, meta = a.mind.understanding, a.mind.meta
count = lambda x: x.startswith(("load_", "pulse_", "want_"))
splits = [(c, sp["tag"]) for c, sp in meta.splits.items() if sp.get("tag") and count(sp["tag"])]
print(f"problems {len(w.solved)}, settled before the cap {sum(1 for s in w.solved if s['settled'] and s['slices'] < 300)}")
print(f"F0-2: splits {len(meta.splits)}, on a count {len(splits)}:", [t for _, t in splits][:6])
cond = [(c, o) for c, rels in und.rel.items() for (r, o), e in rels.items() if r in ("conditioned_by", "enables") and count(o)
        and e[0] + e[2] > 0]
print(f"     lived conditions on a count: {len(cond)}:", cond[:4])
pulse = [(c, o) for c, rels in und.rel.items() if "_push:" in c for (r, o), e in rels.items() if r == "causes"
         and o.startswith("pulse_") and e[0] > 0]
print(f"F0-3: lived 'turn causes pulse' links: {len(pulse)}; kinds", Counter(o.rsplit("_", 1)[0].split("_", 3)[-1] for _, o in pulse).most_common(4),
      "| sample", pulse[:3])
cw = [(t, g, k) for t, g, k in a.sub_log if g.startswith(("load_", "pulse_"))]
print("count wants:", Counter((g, k) for t, g, k in cw).most_common(6))
