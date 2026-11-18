"""What rests on a piece (the user, 2026-11-17, "yes, exactly": a piece left hanging loses every region it alone holds up;
PlansWorld.resting_on, read into effects_after). The play app's game: 1. g3 e5 2. e3 d5 3. Qh5 Nc6, White to move, where a fresh mind
played 4. Qg4 and left its queen hanging (its felt loss 8: 7 plans given and the queen's bearing, against 7 plans ended). Expectations
written before the run:
  R1: Qg4's felt loss larger than 8, the queen having regions resting on it.
  R2: a move leaving a pawn hanging, if any, weighs about 1 for the pawn (its resting set small).
  R3: across 10 fresh minds (the league's configure, accepting_patient), no move leaving the queen hanging is chosen.
python -X utf8 check_resting.py [seeds]"""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
import chess

import mate_oracle
import rung4p
from chessduel import configure
from league import PROFILES
from plansworld import give, read_mate_passed
from rung4 import TURN_STEPS

seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 10
b0 = chess.Board()
for san in ("g3", "e5", "e3", "d5", "Qh5", "Nc6"):
    b0.push_san(san)
FEN = b0.fen()
w, a = rung4p.build(0, FEN, dreams=True, half_moves=4)
configure(a, PROFILES["accepting_patient"])
w.shown = w.read()
give(a, w)
invs = {f"{i[0]}_push:{i[1]}_{i[2]}": i for i in w.invitations()}
a.defense_now(invs)
d = a.mind.anti_defense or {}
queen_hangs, pawn_hangs = [], []
for c, i in invs.items():
    eff = w.effects_after(i)
    hanging = [e for e in eff if e.endswith("_bearing_hanging")]
    if any("queen" in e for e in hanging):
        queen_hangs.append(i[0].split(" ", 1)[1])
    elif any("pawn" in e for e in hanging):
        pawn_hangs.append((i[0].split(" ", 1)[1], d.get(c)))
    if i[0].endswith("h5g4"):
        rest = [e for e in eff if e.endswith("_stoppable") and e.startswith("plan_")]
        print(f"Qg4: felt loss {d.get(c)}; effects {len(eff)}; plan regions it loses {len(rest)}")
        q_loss = d.get(c)
print("moves leaving the queen hanging:", queen_hangs)
print("moves leaving a pawn hanging (felt loss):", pawn_hangs[:6])
chosen = Counter()
for seed in range(seeds):
    w, a = rung4p.build(seed, FEN, dreams=True, half_moves=4)
    configure(a, PROFILES["accepting_patient"])
    w.shown = w.read()
    give(a, w)
    move = None
    for t in range(TURN_STEPS * 4):
        n0 = w.moved
        choice, _ = a.tick()
        read_mate_passed(a, choice)
        give(a, w)
        if w.moved > n0:
            move = next(x[1] for x in reversed(w.log) if x[2]).split(" ", 1)[1]
            break
    chosen[move] += 1
print("chosen:", dict(chosen))
print(f"R1: {'met' if q_loss is not None and q_loss < -8 else 'NOT met'} ({q_loss}); "
      f"R3: {'met' if not any(chosen[m] for m in queen_hangs) else 'NOT met'} ({sum(chosen[m] for m in queen_hangs)} of {seeds})")
mate_oracle.close()
