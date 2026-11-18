"""Rung 2's unsettled problems, measured against the whole setting space (2026-11-15): rebuild each
problem from its seed, find every setting where everything holds (clean included), and walk the full
log's per-slice wheels to ask the one question that splits the failure: was the mind ever ONE TURN
from a fully-held setting and did not take it (a valuation failure), or did it never get that close
(a search failure)? Also: the slices spent at each distance, and what the mind did the slice after
standing at distance 1.

Run: python -X utf8 trace_distance.py rung2/s0_full.log 0 [rung2/s1_full.log 1 ...]
"""
import itertools
import random
import re
import sys

import graph as g
import rooms

SIZES = {"single": len(g.SINGLE), "join": len(g.JOIN)}


def held_settings(p):
    out = []
    sizes = [SIZES[k] for k in p.shape.kinds]
    for pos in itertools.product(*(range(n) for n in sizes)):
        if all(g.territory(p.reading(list(pos))).values()):
            out.append(pos)
    return out


def dist(pos, target, sizes):
    return sum(min((a - b) % n, (b - a) % n) for a, b, n in zip(pos, target, sizes))


def main():
    args = sys.argv[1:]
    for log, seed in zip(args[::2], args[1::2]):
        rng = random.Random(f"problems:{seed}")
        lines = open(log, encoding="utf-8").read().splitlines()
        heads = [l for l in lines if re.match(r"\s+problem \d+ \(", l)]
        problems = [rooms.rung2(rng) for _ in range(len(heads) + 1)]
        print(f"== {log}")
        cur, k = [], 0
        for l in lines + ["  problem end ("]:
            m = re.match(r"\s+s\d+ .*wheels \[(.*)\]", l)
            if m:
                cur.append([x.strip().strip("'") for x in m.group(1).split(",")])
                continue
            m = re.match(r"\s+problem \d+ \((\w+)\): (settled|not settled).*correct \[(.*)\]", l)
            if not (m or l.startswith("  problem end")) or k >= len(problems) or not cur:
                continue
            p = problems[k]
            k += 1
            if m and list(map(int, m.group(3).split(","))) != p.correct:
                print(f"  problem {k}: rebuilt problem does not match the log (correct differs); skipped")
                cur = []
                continue
            sizes = [SIZES[kk] for kk in p.shape.kinds]
            wheels = {("single" if kk == "single" else "join"): None for kk in p.shape.kinds}
            idx = [[(g.SINGLE if kk == "single" else g.JOIN).index(op) for kk, op in zip(p.shape.kinds, ops)]
                   for ops in cur]
            held = held_settings(p)
            ds = [min(dist(pos, h, sizes) for h in held) for pos in idx]
            at1 = [i for i, d in enumerate(ds) if d == 1]
            closed = sum(1 for i in at1 if i + 1 < len(ds) and ds[i + 1] == 0)
            away = sum(1 for i in at1 if i + 1 < len(ds) and ds[i + 1] > 1)
            stay = sum(1 for i in at1 if i + 1 < len(ds) and ds[i + 1] == 1)
            tag = m.group(2) if m else "?"
            print(f"  problem {k} ({tag}): {len(held)} fully-held settings; min distance {min(ds)}, "
                  f"slices at d0/d1 {ds.count(0)}/{len(at1)}; from d1: closed {closed}, stayed {stay}, moved away {away}")
            cur = []


if __name__ == "__main__":
    main()
