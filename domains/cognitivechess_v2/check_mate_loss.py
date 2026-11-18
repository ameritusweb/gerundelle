"""Checks that a mate passed up is a loss of territory (plansworld.read_mate_passed): a fresh mind on a position with a mate in one, a
few slices with random Black; the owned prediction potential_mate+0 before and after, the mates passed, and the anti-want.
python -X utf8 check_mate_loss.py [fen]"""
import sys

import plansworld
import rung4p
from gameworld import RandomSide

sys.stdout.reconfigure(encoding="utf-8")
fen = sys.argv[1] if len(sys.argv) > 1 else "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
w, a = rung4p.build(0, fen, dreams=True, half_moves=10 ** 6)
a.mind.p.dream_when_stuck = False
a.__dict__.pop("dreamer", None)
a.mind.p.dreams = False
a.mind.p.dream_for_want = True
black = RandomSide(w, 0)
plansworld.give(a, w)


def row():
    r = a.mind.territory.rows.get("potential_mate+0", {})
    return r.get("holder"), r.get("prediction")


print("before:", row())
for k in range(8):
    choice, _ = a.tick()
    plansworld.read_mate_passed(a, choice)
    plansworld.give(a, w)
    if w.board.turn is False and not w.over():
        black.tick()
    passed = a.__dict__.get("mates_passed", [])
    print(f"slice {k + 1}: chose {choice[0] if choice else None}; mate row {row()}; anti-want {a.__dict__.get('anti')}; "
          f"mates passed {len(passed)} {passed[-1][:2] if passed else ''}")
