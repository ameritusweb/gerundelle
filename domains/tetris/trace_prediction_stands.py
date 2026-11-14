"""How often each potential effect's prediction stood (an instance the world answers), per 2000 slices and by what stood it, and whether
any run+2 stood during the three long run+2 holds; plus the owned-prediction row potential_run+2_coming_apart's history.
python -u -X utf8 trace_prediction_stands.py checkpoints/clean5_28000.pkl"""
import collections
import sys

import checkpoint
import run  # noqa: F401

sys.stdout.reconfigure(encoding="utf-8")
a, w, t_end = checkpoint.load(sys.argv[1])
und = a.mind.understanding
sovs = und.__dict__.get("prediction_sovs", {})
inst = [(ins["made"], s["effect"], ins.get("outcome"), ins["by"]) for s in sovs.values() for ins in s["instances"]]
print(f"prediction SOVs {len(sovs)}, instances {len(inst)}")
by_rel = collections.Counter(r for _, r, _, _ in inst)
print("instances by effect:", by_rel.most_common())
print("\nper 2000 slices, instances of each clear effect (row+k / run+k):")
per = collections.defaultdict(collections.Counter)
for t, r, o, by in inst:
    if r.startswith(("row+", "run+")):
        per[t // 2000 * 2000][r] += 1
for b in sorted(per):
    print(f"  {b:6d}: {dict(per[b])}")
runs2 = sorted(t for t, r, o, by in inst if r == "run+2_coming_apart")
print(f"\nrun+2 instances: {len(runs2)} at slices {runs2}")
print("run+2 outcomes:", collections.Counter(o for t, r, o, by in inst if r == "run+2_coming_apart"),
      "| stood by:", collections.Counter(by for t, r, o, by in inst if r == "run+2_coming_apart").most_common(5))
for t0, t1 in ((3523, 8169), (8728, 14541), (24385, 25733)):
    inside = [t for t in runs2 if t0 <= t <= t1]
    print(f"  hold {t0}..{t1}: run+2 stood at {inside}")
row = a.mind.territory.rows.get("potential_run+2_coming_apart")
if row:
    print("\nrow potential_run+2_coming_apart: holder", row.get("holder"), "prediction", row.get("prediction"))
    print("  history:", row.get("history"))
anti = [x for x in a.__dict__.get("anti_log", [])][:0]
print("\nanswers for run+2 (prediction_answers by effect shown):")
ans = a.__dict__.get("prediction_answers", [])
print("  answered total", len(ans), "| run+2-shaped effects can't be told apart by name here; outcomes overall:", collections.Counter(x[2] for x in ans))
