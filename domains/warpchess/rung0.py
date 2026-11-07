"""Rung 0 (LADDER.md): win the hanging piece on a Warp board. One want, the world pushing back, no reply.

Run: python -X utf8 rung0.py [--seeds 10] [--ticks 400]
"""
import argparse
import collections
import os
import random
import statistics
import sys

sys.path.insert(0, os.environ.get("GERUNDELLE", "E:/vscode/analogy/molecules"))
from sov_agent import SovAgent  # noqa: E402

from warpworld import RUNG0, WarpWorld  # noqa: E402

WANT = "material_up"


class Budgeted(SovAgent):
    budget = 60

    def plan_step(self, invs, budget=60, horizon=3):
        return super().plan_step(invs, self.budget, horizon)


def winners(seed=0):
    """The moves that win material here, read from the engine: for the baselines and the report, never shown to the mind."""
    out, w = {}, WarpWorld(RUNG0, seed=seed)
    for label, move in w.offers().items():
        v = WarpWorld(RUNG0, seed=seed)
        v.play(move)
        v.pass_black()
        out[label] = (move, v.read()["material"] == "up")
    return out


def is_flip(label, table):
    return table[label][0].flip_type != 0


def mind(seed, ticks, budget):
    Budgeted.budget = budget
    w = WarpWorld(RUNG0, seed=seed)
    a = Budgeted(w)
    a.goal = WANT
    first, tries = None, 0
    for _ in range(ticks):
        if a.goal is None:
            a.goal = WANT   # renewed when met, to see what it settles on
        a.tick()
        if first is None and a.reached:
            first = len(a.pushed)
    return a, w, first


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=400)
    args = ap.parse_args()
    table = winners()
    wins = {m.uci(): good for m, good in table.values()}
    print(f"moves on offer {len(table)}; winning {sum(wins.values())}: {sorted(u for u, g in wins.items() if g)}; flips on offer {sum(m.flip_type != 0 for m, _ in table.values())}")
    enum, rand = [], []
    for s in range(args.seeds):
        t = winners(s)
        labels = sorted(t)
        enum.append(1 + min(i for i, x in enumerate(labels) if t[x][1]))
        rng, n = random.Random(s), 0
        while True:
            n += 1
            if t[rng.choice(labels)][1]:
                break
        rand.append(n)
    med = statistics.median
    print(f"enumeration: tries median {med(enum)}, range {min(enum)}-{max(enum)}; random mover: median {med(rand)}, range {min(rand)}-{max(rand)}")
    for budget in (60, 500):
        rows = []
        for s in range(args.seeds):
            a, w, first = mind(s, args.ticks, budget)
            t = winners(s)
            tried = [x[1] for x in w.log if x[2]]
            half = tried[len(tried) // 2:]
            late = sum(t[x][1] for x in half) / max(1, len(half))
            rows.append(dict(first=first, pushes=len(tried), refused=sum(not x[2] for x in w.log), late=late, reached=len(a.reached),
                             flips=sum(is_flip(x, t) for x in set(tried)), distinct=len(set(tried)), splits=len(a.mind.meta.splits),
                             top=collections.Counter(t[x][0].uci() for x in half).most_common(2)))
            r = rows[-1]
            print(f"  budget {budget} seed {s}: first want at try {str(first):>4}, tries {r['pushes']:>3}, distinct moves {r['distinct']:>2}, flips tried {r['flips']:>2}, refused {r['refused']}, wants met {r['reached']:>3}, winning share late {late:.2f}, late moves {r['top']}")
        ok = [r["first"] for r in rows if r["first"]]
        print(f"budget {budget}: found in {len(ok)}/{len(rows)}, first want at try median {med(ok) if ok else '-'}, range {min(ok) if ok else '-'}-{max(ok) if ok else '-'}; winning share late median {med(r['late'] for r in rows):.2f}; flips tried median {med(r['flips'] for r in rows)}")


if __name__ == "__main__":
    main()
