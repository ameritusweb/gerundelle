"""Rung 1's unsettled problems, from the full logs (run.py without --quiet): for each, whether everything was ever held, how many
slices it was, how many times the mind turned away from a fully held program, the most held otherwise, and the turns made.
Run: python -X utf8 classify_unsettled.py rung1/s0_full.log ..."""
import re
import sys

for log in sys.argv[1:]:
    lines = open(log, encoding="utf-8").read().splitlines()
    cur, out = [], []
    for l in lines:
        m = re.match(r"\s+s\d+ .*?: (.*?); held (\d+)/(\d+); wheels (.*)", l)
        if m:
            cur.append((m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)))
        elif re.match(r"\s+problem \d+ \(", l):
            out.append((l.strip(), cur))
            cur = []
    print("==", log)
    for head, sl in out:
        if "not settled" not in head and "in 300 slices" not in head:
            continue
        full = [i for i, (_, h, n, _) in enumerate(sl) if h == n]
        left = sum(1 for i in full if i + 1 < len(sl) and sl[i + 1][0].startswith("turning"))
        most = max((h for _, h, n, _ in sl if h < n), default=0)
        n = sl[0][2] if sl else 0
        kind = "solved, left" if full else "never solved"
        print(f"  {head.split(':')[0]}: {kind}: all held in {len(full)} slices, turned away from it {left} times; "
              f"most held otherwise {most}/{n}; {head.split(';')[0].split(',')[-1].strip()}")
