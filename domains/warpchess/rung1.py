"""Rung 1 (LADDER.md): a want only a flip can meet. Nothing about flipping is written into the mind.

Run: python -X utf8 rung1.py [--seeds 10] [--ticks 1000]
"""
import argparse
import collections
import random
import statistics
import sys

from rung0 import Budgeted, WANT
from warpworld import RUNG1_ONE, RUNG1_TWO, WarpWorld


def first_labels(fen, seed):
    w = WarpWorld(fen, seed=seed)
    out = {}
    for label, m in w.offers().items():
        v = WarpWorld(fen, seed=seed)
        v.play(m)
        v.pass_black()
        out[label] = (m, v.read()["material"] == "up")
    return out


FORCES = False


def run(fen, moves, seed, ticks):
    Budgeted.budget = 500
    w = WarpWorld(fen, seed=seed, moves=moves, forces=FORCES)
    a = Budgeted(w)
    first = None
    for _ in range(ticks):
        if a.goal is None:
            a.goal = WANT
        a.tick()
        if first is None and a.reached:
            first = len(a.pushed)
    return a, w, first


def uci(label):
    return label.split(" ", 1)[1]


def report(name, fen, moves, seeds, ticks):
    rows = []
    for s in range(seeds):
        a, w, first = run(fen, moves, s, ticks)
        made = [x for x in w.log if x[2]]
        half = made[len(made) // 2:]
        wins = sum(x[3] == "up" for x in half)
        top = collections.Counter(uci(x[1]) for x in half).most_common(3)
        rows.append(dict(first=first, tries=len(made), late=wins / max(1, len(half)), met=len(a.reached), distinct=len({x[1] for x in made}),
                         flips=len({x[1] for x in made if ">" in x[1] or "=" in x[1]}), refused=sum(not x[2] for x in w.log), splits=len(a.mind.meta.splits), top=top))
        r = rows[-1]
        print(f"  {name} seed {s}: first want at try {str(first):>4}, tries {r['tries']:>3}, distinct {r['distinct']:>2}, flips tried {r['flips']:>2}, refused {r['refused']:>2}, wants met {r['met']:>3}, winning share late {r['late']:.2f}, splits {r['splits']}, late {top}")
    ok = [r["first"] for r in rows if r["first"]]
    med = statistics.median
    print(f"{name}: found in {len(ok)}/{len(rows)}; first want at try median {med(ok) if ok else '-'}, range {min(ok) if ok else '-'}-{max(ok) if ok else '-'}; winning share late median {med(r['late'] for r in rows):.2f}; wants met median {med(r['met'] for r in rows)}\n")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=1000)
    ap.add_argument("--which", default="both")
    args = ap.parse_args()
    t = first_labels(RUNG1_ONE, 0)
    print(f"one move: {len(t)} on offer, {sum(m.flip_type != 0 for m, _ in t.values())} flips, winning {[m.uci() for m, g in t.values() if g]}")
    t2 = first_labels(RUNG1_TWO, 0)
    print(f"two moves: {len(t2)} on offer at the start, {sum(m.flip_type != 0 for m, _ in t2.values())} flips, winning at once {[m.uci() for m, g in t2.values() if g]}, rook flips at once {[m.uci() for m, _ in t2.values() if m.flip_type and m.uci().startswith('Ld3')]}")
    enum, rand = [], []
    for s in range(args.seeds):
        t = first_labels(RUNG1_ONE, s)
        labels = sorted(t)
        enum.append(1 + next(i for i, x in enumerate(labels) if t[x][1]))
        rng, n = random.Random(s), 0
        while True:
            n += 1
            if t[rng.choice(labels)][1]:
                break
        rand.append(n)
    med = statistics.median
    print(f"one move, enumeration: median {med(enum)}, range {min(enum)}-{max(enum)}; random mover: median {med(rand)}, range {min(rand)}-{max(rand)}\n")
    if args.which in ("one", "both"):
        report("one move", RUNG1_ONE, 1, args.seeds, args.ticks)
    if args.which in ("two", "both"):
        report("two moves", RUNG1_TWO, 2, args.seeds, args.ticks)


if __name__ == "__main__":
    main()
