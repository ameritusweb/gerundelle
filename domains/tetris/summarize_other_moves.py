"""From trace_aligning_<slice>.log: piece_alignment's moves by something else per 1000 slices (all of them, other_times) against the
contested openings, and how many came outside a watch (other: those raise other_since)."""
import collections
import sys

text = open(sys.argv[1], encoding="utf-8").read().splitlines()
row = next(l for l in text if l.startswith("territory row piece_alignment:"))
d = eval(row[len("territory row piece_alignment:"):].strip(), {"frozenset": frozenset, "set": set, "inf": float("inf"), "nan": float("nan")})
times = d.get("other_times", [])
moves = d.get("other_moves", [])
print(f"other (outside a watch) {d['other']}, other_since {d['other_since']}, other_to {d.get('other_to')}, records {len(times)}")
by = collections.defaultdict(collections.Counter)
for t, (g, _) in zip(times, moves):
    by[t // 1000 * 1000][g] += 1
cont = collections.Counter(t // 1000 * 1000 for t, h in d["history"] if h == "contested")
print("per 1000 slices: moves by something else (to aligning / straying) | contested openings")
for b in sorted(set(by) | set(cont)):
    print(f"  {b:6d}: aligning {by[b]['aligning']:3d}  straying {by[b]['straying']:3d} | contested {cont[b]}")
