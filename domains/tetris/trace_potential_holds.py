"""Every potential:* want over the whole run (the slice-28000 checkpoint's sub_log): how long each was held and how it ended, and for the
long holds, the sub-wants set beneath it. Also when the owned-prediction rows those wants come from were last held.
python -u -X utf8 trace_potential_holds.py checkpoints/clean5_28000.pkl"""
import collections
import sys

import checkpoint
import run  # noqa: F401

sys.stdout.reconfigure(encoding="utf-8")
a, w, t_end = checkpoint.load(sys.argv[1])
log = a.sub_log
held = []
open_ = {}
for i, (t, g, k) in enumerate(log):
    if g.startswith("potential:"):
        if k == "set":
            open_[g] = (t, i)
        elif g in open_:
            t0, i0 = open_.pop(g)
            held.append((g, t0, t, k, i0, i))
for g, (t0, i0) in open_.items():
    held.append((g, t0, None, "still held", i0, len(log)))
dur = lambda h: (h[2] if h[2] is not None else t_end) - h[1]
print(f"potential wants set: {len(held)}; held 0 slices: {sum(1 for h in held if dur(h) == 0)}; 1-50: {sum(1 for h in held if 0 < dur(h) <= 50)}; "
      f"over 50: {sum(1 for h in held if dur(h) > 50)}")
print("ending kinds:", collections.Counter(h[3] for h in held))
print("\nheld over 50 slices:")
for h in sorted(held, key=lambda h: h[1]):
    if dur(h) <= 50:
        continue
    g, t0, t1, k, i0, i1 = h
    under = collections.Counter((gg, kk) for tt, gg, kk in log[i0 + 1:i1] if not gg.startswith("potential:"))
    print(f"  {g}: set {t0}, {k} {t1} (held {dur(h)} slices)")
    print(f"      beneath it: {sum(c for (gg, kk), c in under.items() if kk == 'set')} wants set, "
          f"{sum(c for (gg, kk), c in under.items() if kk == 'dropped')} dropped; most set: "
          f"{collections.Counter({gg: c for (gg, kk), c in under.items() if kk == 'set'}).most_common(4)}")
print("\nholds per 2000 slices (slices a potential want was the root or on the stack):")
per = collections.Counter()
for h in held:
    t1 = h[2] if h[2] is not None else t_end
    for b in range(h[1] // 2000 * 2000, t1 + 1, 2000):
        per[b] += max(0, min(t1, b + 2000) - max(h[1], b))
for b in sorted(per):
    print(f"  {b:6d}: {per[b]}")
print("\ngoal now:", a.goal, "stack:", a.stack)
