"""The tetris mind's decision paths (Params.decision_paths): each decision traced back to the winning thought, its bonds and the SOV
relations behind them, counted; printed as the most-used of each. A checkpoint is saved every 1000 slices (checkpoints/, checkpoint.py);
to go on from one: python -u -X utf8 trace_decisions.py [slices] [checkpoint file]. Run: python -u -X utf8 trace_decisions.py [slices] [--prefix name: checkpoints/<name>_<slice>.pkl, default decisions]"""
import sys
import time

import checkpoint
import run
from molecules import Params
from potential import ForceMind
from sov_agent import SovAgent
from world import TetrisWorld

sys.stdout.reconfigure(encoding="utf-8")
PREFIX = sys.argv[sys.argv.index("--prefix") + 1] if "--prefix" in sys.argv else "decisions"   # checkpoints/<prefix>_<slice>.pkl
NO_CKPT = "--no-checkpoints" in sys.argv
pos = [x for k, x in enumerate(sys.argv[1:], 1) if not x.startswith("--") and not (k > 1 and sys.argv[k - 1] == "--prefix")]
N = int(pos[0]) if pos else 1000
if len(pos) > 1:   # go on from a checkpoint
    a, w, start = checkpoint.load(pos[1])
    for k, v in run.SWITCHES.items():   # the switch set as it is now (a checkpoint carries the one it was saved with)
        setattr(a.mind.p, k, v)
    print(f"resumed from {pos[1]} at slice {start}, with the current switches", flush=True)
else:
    w = TetrisWorld(seed=0, luck=0.7)
    a = SovAgent(w, ForceMind(Params(**run.SWITCHES)))
    a.mind.p.acceptance = 6
    start = 0
t0 = time.time()
for t in range(start, N):
    a.mind.potentials = w.potentials()
    a.tick()
    run.after_tick(a, w)
    if (t + 1) % 200 == 0:
        terr = a.mind.territory
        held = sum(1 for r, row in terr.rows.items() if row.get("holder") == "mine" and r.startswith(("row_", "block_")))
        cleared = sum(1 for row in terr.rows.values() if row.get("cleared"))
        print(f"slice {t + 1} ({time.time() - t0:.0f}s): decisions {a.__dict__.get('decision_tree', {}).get('decisions', 0)}, luck {w.luck} "
              f"({w.earned} earned); games {len(w.games)}, rows {w.lines}, pieces cleared this game {w.pieces_cleared}; rows and blocks held "
              f"{held} ({cleared} cleared, for good); anti-want {a.__dict__.get('anti')}", flush=True)
    if (t + 1) % 1000 == 0 and not NO_CKPT:
        checkpoint.save(a, w, t + 1, f"checkpoints/{PREFIX}_{t + 1}.pkl")
    if (t + 1) % 1000 == 0:   # the view so far: what the decisions rest on, and how much of it is prediction, potential effect, row or run
        tree = a.__dict__.get("decision_tree", {"nodes": {}, "steps": {}})
        fore = sum(c for (k, n), c in tree["nodes"].items() if k in ("bond", "sov") and any(x in n for x in ("prediction:", "potential", "row_", "run+", "row+")))
        allb = sum(c for (k, n), c in tree["nodes"].items() if k in ("bond", "sov"))
        print(f"  VIEW at slice {t + 1}: bonds and SOV links resting on predictions, potential effects, rows or runs: {fore} of {allb}", flush=True)
        mlog = a.mind.meta.log
        rel = [x for x in mlog if "relevant" in str(x[2])]
        print(f"    relevant: formed {sum(1 for x in rel if x[1] == 'formed')}, targeted {sum(1 for x in rel if x[1] == 'op:targeted')}, "
              f"confirmed {sum(1 for x in rel if x[1] == 'confirmed')}, refuted {sum(1 for x in rel if x[1] == 'refuted')}; standing on "
              f"{sorted(k[len('meta:relevant:'):] for k in a.mind.meta.watch if k.startswith('meta:relevant:'))[:6]}", flush=True)
        v = a.decision_view(5)
        for kind in ("decision", "thought", "bond", "sov"):
            print(f"    {kind}s: " + "; ".join(f"{n[:60]} x{c}" for n, c in v[kind]), flush=True)
view = a.decision_view(14)
print("decisions:", view["decisions"])
for kind in ("decision", "thought", "bond", "sov"):
    print(f"most used {kind}s:")
    for n, c in view[kind]:
        print(f"  {c:5d}  {n[:140]}")
