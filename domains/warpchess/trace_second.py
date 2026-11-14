"""Rung 1b, two moves: what happens once the rook can cross? Run: python -X utf8 trace_second.py"""
import collections
import sys

from rung0 import Budgeted, WANT
from warpworld import RUNG1_TWO, WarpWorld


class Traced(Budgeted):
    def __init__(self, world):
        super().__init__(world)
        self.sources = collections.Counter()
        self.seen = collections.Counter()

    def foreseen(self, steps, invs):
        out = super().foreseen(steps, invs)
        self.seen["reported, not made" if out is not None else "goes on"] += 1
        return out

    def planned(self, invs):
        step = super().planned(invs)
        self.planned_step = step
        return step


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for seed in (0, 3, 6, 2):
        Budgeted.budget = 500
        w = WarpWorld(RUNG1_TWO, seed=seed, moves=2, forces=True)
        a = Traced(w)
        chances = []   # a second move made with the winning capture on offer
        how = collections.Counter()
        missed_ticks = 0
        for t in range(1000):
            if a.goal is None:
                a.goal = WANT
            target = w.where["black_knight_Rd4"]
            on_offer = [m for m in w.offers().values() if m.final_square == target] if w.moved == 1 and target is not None else []
            a.planned_step = None
            n = len(w.log)
            choice, rec = a.tick()
            if len(w.log) > n and w.log[-1][2]:
                source = "plan" if a.planned_step == choice else "experiment" if rec["experiments"] or a.running else "other"
                how[source] += 1
                if on_offer:
                    chances.append((w.log[-1][1].split(" ")[1], source))
            elif on_offer and not a.watching:
                missed_ticks += 1
        wins = sum(x[3] == "up" for x in w.log if x[2])
        print(f"\n===== seed {seed}: pushes {len(a.pushed)}, material up {wins}, sources {dict(how)}, foreseen {dict(a.seen)}")
        print(f"  second moves made with a crossing capture on offer: {len(chances)}; winning: {sum(c[0].endswith('Rd4') for c in chances)}; made by {dict(collections.Counter(c[1] for c in chances))}; ticks it sat there with no move: {missed_ticks}")
        print(f"  those moves: {collections.Counter(c[0] for c in chances).most_common(6)}")
        known = {i[0].split(" ")[1] for i in a.known.values()}
        print(f"  knows the winning move exists: {[u for u in ('Ld6>Rd6Rd4', 'Ld7>Rd7Rd4') if u in known]}; pushes known {len(a.known)}")
        goal = a.mind.understanding.rel.get(WANT, {})
        print(f"  rook to d6's first move made {sum(1 for x in w.log if x[2] and x[1].endswith('Ld3Ld6'))} times; episodes ended by idling {sum(1 for x in w.log if not x[2])}")
        print(f"  what the mind saw knight_hanging do: causes {[o for (r, o) in a.mind.understanding.rel.get('black_knight_Rd4_bearing_hanging', {}) if r == 'causes'][:4]}")
        print(f"  splits {len(a.mind.meta.splits)}; questions {collections.Counter(r for _, r in a.mind.understanding.questions.values())}")


if __name__ == "__main__":
    main()
