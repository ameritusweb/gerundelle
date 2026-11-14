"""Rung 1, two moves: where do the experiments go? Counts what becomes of each, and what the mind can see change. Run: python -X utf8 trace_foreseen.py"""
import collections
import sys

from rung0 import Budgeted, WANT
from warpworld import RUNG1_TWO, WarpWorld


class Counting(Budgeted):
    def __init__(self, world):
        super().__init__(world)
        self.seen = collections.Counter()

    def foreseen(self, steps, invs):
        out = super().foreseen(steps, invs)
        self.seen["foreseen: reported, not made" if out is not None else "foreseen: not known, goes on"] += 1
        return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for seed in (1, 2, 0):
        Budgeted.budget = 500
        w = WarpWorld(RUNG1_TWO, seed=seed, moves=2)
        a = Counting(w)
        for t in range(1000):
            if a.goal is None:
                a.goal = WANT
            a.tick()
        print(f"\n===== seed {seed}: pushes {len(a.pushed)}, wants met {len(a.reached)}, experiments done {sum(a.mind.inquiry.done.values())}")
        print(f"  {dict(a.seen)}")
        facts = collections.Counter(f for _, f, _ in a.pushed)
        print(f"  distinct situations it met a push in: {len(facts)} in {len(a.pushed)} pushes; the commonest held {facts.most_common(1)[0][1]}")
        outcome = collections.Counter(tuple(sorted(m)) for _, _, m in a.pushed)
        print(f"  outcomes: {[(k[:3], n) for k, n in outcome.most_common(5)]}")
        rook = [(i[0].split(' ')[1], sorted(m)[:2]) for i, _, m in a.pushed if i[0].split(" ")[1].startswith("Ld3")][:5]
        print(f"  the rook's pushes and what the mind saw them do: {rook}")
        first = a.pushed[0][1]
        print(f"  the situation it perceives (a sample of {len(first)} facts): {sorted(first)[:6]}")
        moved = WarpWorld(RUNG1_TWO, seed=seed, moves=2)
        before = moved.states()
        label = next(l for l, m in moved.offers().items() if m.uci() == "Ld3Ld6")
        inv = next(i for i in moved.invitations() if i[0] == label)
        moved.act(inv)
        moved.act(None)
        print(f"  after the rook goes d3 to d6, what changes in what it perceives: {[(k, before[k], v) for k, v in moved.states().items() if before.get(k) != v] or 'nothing'}")
        print(f"  moves on offer: before {len(WarpWorld(RUNG1_TWO, seed=seed, moves=2).invitations())}, after {len(moved.invitations())}; winning move on offer after: {any(m.uci() == 'Ld6>Rd6Rd4' for m in moved.offers().values())}")


if __name__ == "__main__":
    main()
