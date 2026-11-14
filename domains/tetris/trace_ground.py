"""Does holding ground pieces give the mind a reason to place pieces on the ground (the user, 2026-11-12: "It IS a reason because of
the prediction SOV")? From a checkpoint, with the ground rule on or off: each piece as it settles, whether it touches the floor, how
high it came to rest, and whether it cleared; and the wants the mind set in those slices.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_ground.py <checkpoint> <slices> [--no-ground] [--commit]"""
import collections
import sys

import run
import checkpoint

sys.stdout.reconfigure(encoding="utf-8")
args = [x for x in sys.argv[1:] if not x.startswith("--")]
a, w, start = checkpoint.load(args[0])
N = int(args[1])
ground = "--no-ground" not in sys.argv
a.mind.p.commit = "--commit" in sys.argv
floor = w.height - 1
pieces, n_sub = [], len(a.sub_log)
cleared0 = w.__dict__.get("pieces_cleared", 0)
games0 = len(w.games)
for k in range(N):
    placed = w.placed
    a.mind.potentials = w.potentials()
    a.tick()
    run.after_tick(a, w, ground=ground)
    if w.placed > placed:
        cells = w.__dict__.get("settling_cells", [])
        if cells:
            pieces.append((any(y == floor for _, y in cells), floor - max(y for _, y in cells)))
print(f"from {args[0]}, {N} slices, ground pieces {'held' if ground else 'not held'}, commit {'on' if a.mind.p.commit else 'off'}:")
print(f"    pieces settled {len(pieces)}; touching the floor {sum(1 for t, _ in pieces if t)}; rows above the floor its lowest block rested, by count: "
      f"{sorted(collections.Counter(h for _, h in pieces).items())}")
print(f"    pieces cleared {w.__dict__.get('pieces_cleared', 0) - cleared0}; games ended {len(w.games) - games0}; ground blocks held {len(a.__dict__.get('ground_held', ()))}")
print("    wants set:", collections.Counter(g.split("_")[0].split(":")[0] + ("" if not g.startswith("block") else " (a block)") for _, g, kk in a.sub_log[n_sub:] if kk == "set").most_common(6))
sovs = a.mind.understanding.__dict__.get("prediction_sovs", {})
with_floor = [p for p, s in sovs.items() if any("floor" in (x, y) for x, y in s["forces"])]
print(f"    prediction SOVs {len(sovs)}; with a part pressing on the floor in their forces {len(with_floor)}; what those predict: "
      f"{collections.Counter(sovs[p]['effect'] for p in with_floor).most_common(4)}")
