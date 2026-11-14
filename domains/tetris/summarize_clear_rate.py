"""From clean5_run.log: pieces cleared per 1000 slices (across game resets), and each game's length."""
import re

rows = []
for l in open("clean5_run.log", encoding="utf-8"):
    m = re.match(r"slice (\d+) .*games (\d+), rows (\d+), pieces cleared this game (\d+)", l)
    if m:
        rows.append(tuple(int(x) for x in m.groups()))
total, prev, per = 0, (0, 0, 0, 0), {}
for s, g, r, pc in rows:
    total += pc if g != prev[1] else pc - prev[3]
    if s % 1000 == 0:
        per[s] = total
    prev = (s, g, r, pc)
last = 0
print("pieces cleared per 1000 slices:")
for s in sorted(per):
    print(f"  {s - 1000:6d}-{s:6d}: {per[s] - last}")
    last = per[s]
