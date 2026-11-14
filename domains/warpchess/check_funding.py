import sys
sys.argv = ["probe_carry.py", "300"]
import runpy
g = runpy.run_path("probe_carry.py", run_name="__main__")
a = g["a"]
und = a.mind.understanding
kept = [(k, und.rel.get(k[0], {}).get(("causes", k[2]))) for k in sorted(a.carried)]
print("carried:", len(kept), "| still funded as worked out:", sum(1 for _, e in kept if e and e[2] > 0))
print("retractions logged for them:", sum(1 for t, what, pair in und.log if what == "retract:causes" and (pair[0], "causes", pair[1]) in a.carried))
for k, e in kept[:4]: print("  ", k[0][:30], k[2], e)
