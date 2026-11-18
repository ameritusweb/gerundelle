"""A predicted loss of territory felt at once (the user, 2026-11-17: "loss of territory is always felt"; Params.defense_still read
through PlansWorld.effects_after). White to move after 1. e4 e5 2. c4 Bc5 (the play app's game, where a fresh mind played 3. b4 and
left the pawn hanging). Fresh minds, 10 seeds, the switch off and on. Expectations written before the run:
  D1 (on): at the first slice, b2b4's defense is negative (a held region lost by it: the b-pawn's bearing), with nothing lived.
  D2: moves that leave one of its own pieces hanging are chosen less often with the switch on than off.
python -X utf8 check_felt_loss.py [seeds]"""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
import chess

import mate_oracle
import rung4p
from chessduel import configure
from plansworld import give, read_mate_passed
from rung4 import TURN_STEPS

seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 10
b0 = chess.Board()
for san in ("e4", "e5", "c4", "Bc5"):
    b0.push_san(san)
FEN = b0.fen()
hanging_moves = None
chosen = {False: Counter(), True: Counter()}
d1 = []
for on in (False, True):
    for seed in range(seeds):
        w, a = rung4p.build(seed, FEN, dreams=True, half_moves=4)
        configure(a)
        a.mind.p.defense_still = on
        w.shown = w.read()
        give(a, w)
        if hanging_moves is None:
            hanging_moves = sorted({p[4][0].split("_push")[0].split(" ", 1)[1] for p in w.push_predictions() if p[0].endswith("_bearing_hanging")})
            print("moves that leave a piece of its own hanging:", hanging_moves)
        move = None
        for t in range(TURN_STEPS * 4):
            n0 = w.moved
            choice, _ = a.tick()
            read_mate_passed(a, choice)
            give(a, w)
            if on and t == 0:
                d = a.mind.__dict__.get("anti_defense") or {}
                d1.append(next((v for c, v in d.items() if "b2b4" in c), None))
            if w.moved > n0:
                move = next(x[1] for x in reversed(w.log) if x[2]).split(" ", 1)[1]
                break
        chosen[on][move] += 1
for on in (False, True):
    n = sum(chosen[on][m] for m in hanging_moves)
    print(f"defense_still {'on ' if on else 'off'}: moves {dict(chosen[on])}; leaving a piece hanging {n}/{seeds}")
print(f"D1: b2b4's defense at the first slice, per seed: {d1} -> {'met' if d1 and all(v is not None and v < 0 for v in d1) else 'NOT met'}")
off_n, on_n = (sum(chosen[x][m] for m in hanging_moves) for x in (False, True))
print(f"D2: {'met' if on_n < off_n else 'NOT met'} ({off_n} off, {on_n} on)")
mate_oracle.close()
