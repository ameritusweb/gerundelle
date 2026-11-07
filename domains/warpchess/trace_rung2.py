"""Trace rung 2: where does White's material go? Every move that changes material: who moved, what was lost, whose it was. Run: python -X utf8 trace_rung2.py [--seed 1] [--rounds 600]"""
import argparse
import collections
import sys

import rung2
from duel import WarpDuel

events = []


class Traced(WarpDuel):
    def play(self, move):
        side = "White" if self.board.turn else "Black"
        before = self.material()
        alive = {o for o, sq in self.where.items() if sq is not None}
        label = self.label(move)
        mover = super().play(move)
        gone = sorted(alive - {o for o, sq in self.where.items() if sq is not None})
        if self.material() != before or gone:
            events.append(dict(ep=len(self.episodes), side=side, mover=mover, move=label, delta=self.material() - before, gone=gone))
        return mover


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--rounds", type=int, default=600)
    args = ap.parse_args()
    rung2.WarpDuel = Traced
    r = rung2.play(args.seed, args.rounds, True)
    print(r)
    n = r["episodes"]
    kinds = collections.Counter()
    for e in events:
        own = [g for g in e["gone"] if g.startswith(e["side"].lower())]
        theirs = [g for g in e["gone"] if g not in own]
        kinds[(e["side"], "took " + ",".join(theirs) if theirs else "", "lost own " + ",".join(own) if own else "", "early" if e["ep"] < n // 2 else "late")] += 1
    for k, c in kinds.most_common(25):
        print(c, k)
    print("first 15 events:")
    for e in events[:15]:
        print(e)


if __name__ == "__main__":
    main()
