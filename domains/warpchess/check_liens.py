import sys
sys.argv = ["probe_carry.py", "900"]
import collections, runpy
g = runpy.run_path("probe_carry.py", run_name="__main__")
a = g["a"]
pairs = a._pairs
trials = collections.Counter(f"{i[0]}_push:{i[1]}_{i[2]}" for i, _, _ in a.timed)
srcs = collections.Counter(a.liens.values())
print("sources behind carried relations:", len(srcs))
for src, n in srcs.most_common(8):
    print(f"  {str(src)[:60]}: carried {n}, still a lived concept {src in pairs}, its move made {trials[src]} times")
und = a.mind.understanding
for src in srcs:
    keys = [k for k, s in a.liens.items() if s == src]
    funded = sum(1 for k in keys if (und.rel.get(k[0], {}).get(("causes", k[2])) or [0, 0, 0])[2] > 0)
    print(f"  {str(src)[:60]}: still funded {funded} of {len(keys)}")
