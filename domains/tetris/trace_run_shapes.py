"""What each clear prediction's structure looked like: for row+k / run+k, how many of the falling piece's parts (p0-p3) were in the cleared
row or run, how many blocks of other pieces, and how many parts the piece had below the floor... read off the relative forces.
python -u -X utf8 trace_run_shapes.py checkpoints/clean5_28000.pkl"""
import collections
import sys

import checkpoint
import run  # noqa: F401

sys.stdout.reconfigure(encoding="utf-8")
a, w, t_end = checkpoint.load(sys.argv[1])
sovs = a.mind.understanding.__dict__.get("prediction_sovs", {})
out = collections.defaultdict(collections.Counter)
for pid, s in sovs.items():
    rel = s["effect"]
    if not rel.startswith(("row+", "run+")):
        continue
    k = rel.split("_")[0]
    across = [(x, y) for x, y in s["forces"] if (x.startswith(("row+", "run+")) or y.startswith(("row+", "run+")))]
    parts = {n for pair in across for n in pair if n.startswith("p")}
    others = {n for pair in across for n in pair if n.startswith(k + ":other")}
    shape = (len(parts), "other pieces' blocks" if others else "settled only")
    out[k][shape] += len(s["instances"])
for k in sorted(out):
    print(f"{k}: instances by (the piece's own parts in the cleared row or run, what else is in it): {dict(out[k])}")
print("well:", w.width, "x", w.height)
