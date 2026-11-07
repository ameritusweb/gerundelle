"""Rung 1c (LADDER.md): one mind carried up the ladder, rung 0, then one move, then two. Run: python -X utf8 rung1c.py [--seeds 10]"""
import argparse
import statistics
import sys

from rung0 import Budgeted, WANT
from warpworld import RUNG0, RUNG1_ONE, RUNG1_TWO, WarpWorld

STAGES = (("rung 0", RUNG0, 1, 400), ("one move", RUNG1_ONE, 1, 1000), ("two moves", RUNG1_TWO, 2, 1000))


def stage(mind, fen, moves, ticks, seed):
    Budgeted.budget = 500
    w = WarpWorld(fen, seed=seed, moves=moves, forces=True)
    a = Budgeted(w, mind)
    first = None
    for _ in range(ticks):
        if a.goal is None:
            a.goal = WANT
        a.tick()
        if first is None and a.reached:
            first = len(a.pushed)
    made = [x for x in w.log if x[2]]
    half = made[len(made) // 2:]
    late = sum(x[3] == "up" for x in half) / max(1, len(half))
    return a, dict(first=first, tries=len(made), late=late, met=len(a.reached), recalled=len(a.recalled), splits=len(a.mind.meta.splits))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    args = ap.parse_args()
    rows = {name: [] for name, *_ in STAGES}
    for s in range(args.seeds):
        mind, line = None, []
        for name, fen, moves, ticks in STAGES:
            a, r = stage(mind, fen, moves, ticks, s)
            mind = a.mind
            rows[name].append(r)
            line.append(f"{name}: first {r['first']}, tries {r['tries']}, late {r['late']:.2f}, recalled {r['recalled']}")
        print(f"seed {s}: " + " | ".join(line), flush=True)
    med = statistics.median
    for name, *_ in STAGES:
        ok = [r["first"] for r in rows[name] if r["first"]]
        print(f"{name}: found in {len(ok)}/{len(rows[name])}; first want at try median {med(ok) if ok else '-'}, range {min(ok) if ok else '-'}-{max(ok) if ok else '-'}; "
              f"winning share late median {med(r['late'] for r in rows[name]):.2f}; recalled in {sum(r['recalled'] > 0 for r in rows[name])} seeds")


if __name__ == "__main__":
    main()
