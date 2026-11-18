"""For the problems a run settled: was the setting it settled on the cleanest (fewest non-identity operations among every setting that
satisfies everything, searched over all of them), and how many settings satisfied the problem? Problems are made again from the run's
seed (world.py draws them from random.Random(f"problems:{seed}") in order). Run: python -X utf8 clean_check.py <rung> <log> <seed>"""
import itertools
import random
import re
import sys

import graph as g
import rooms

rung, log, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
rng = random.Random(f"problems:{seed}")
rows = [l for l in open(log, encoding="utf-8") if re.match(r"\s+problem \d+ \(", l)]
for line in rows:
    p = rooms.ROOMS[rung](rng)
    end = [int(x) for x in re.search(r"end \[([^\]]*)\]", line).group(1).split(",")]
    settled = "not settled" not in line and "in 300 slices" not in line
    sat = [pos for pos in itertools.product(*[range(len(g.wheel(k))) for k in p.shape.kinds])
           if g.satisfied(p, list(pos)) and all(h for o, h in g.territory(p.reading(list(pos))).items())]
    cost = lambda pos: sum(1 for c, (x, k) in enumerate(zip(pos, p.shape.kinds)) if k == "single" and x % len(g.SINGLE) != g.IDENTITY)
    best = min(map(cost, sat)) if sat else None
    endc = [x % len(g.wheel(k)) for x, k in zip(end, p.shape.kinds)]
    if settled:
        print(f"{line.split(':')[0].strip()}: settled on {[p.shape.doing(c, x) for c, x in enumerate(endc)]} ({cost(endc)} working); "
              f"cleanest possible {best}; {len(sat)} settings satisfy it")
