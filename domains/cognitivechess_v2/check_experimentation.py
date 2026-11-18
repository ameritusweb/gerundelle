"""Params.experimentation (the user, 2026-11-17). The play app's game: 1. h4 e5 2. c4 Bc5 3. g4 b6 4. a3 Bb7, White to move, the rook
on h1 hanging (the bishop on b7 down the long diagonal); there a fresh mind played b4 and Ra2 as experiment steps. Fresh minds (the
league's configure, accepting_patient), 10 seeds, experimentation unset (as before) and 0. Expectations written before the run:
  X1: the stakes read +1 (or more) for the moves that stop the rook hanging (Rh2, Rh3, Bg2, f3), 0 or less for b4 and Ra2.
  X2 (0): experiment steps yield (experiment_yields recorded) wherever a move on offer stakes more than the experiment's step.
  X3: the rook stops hanging with White's move more often with experimentation 0 than unset.
python -X utf8 check_experimentation.py [seeds]"""
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
for san in ("h4", "e5", "c4", "Bc5", "g4", "b6", "a3", "Bb7"):
    b0.push_san(san)
FEN = b0.fen()
results = {}
x1 = None
for label, value in (("unset", None), ("0", 0)):
    rescued, yields_, moves = 0, 0, Counter()
    for seed in range(seeds):
        w, a = rung4p.build(seed, FEN, dreams=True, half_moves=4)
        configure(a, PROFILES["accepting_patient"])
        a.mind.p.experimentation = value
        w.shown = w.read()
        give(a, w)
        if x1 is None:
            invs = {f"{i[0]}_push:{i[1]}_{i[2]}": i for i in w.invitations()}
            st = a.stakes(invs)
            x1 = {i[0].split(" ", 1)[1]: st[c] for c, i in invs.items() if i[0].split(" ", 1)[1] in ("h1h2", "h1h3", "f1g2", "f2f3", "b2b4", "a1a2")}
            print("X1 stakes:", x1)
        move = None
        for t in range(TURN_STEPS * 4):
            n0 = w.moved
            choice, _ = a.tick()
            read_mate_passed(a, choice)
            give(a, w)
            if w.moved > n0:
                move = next(x[1] for x in reversed(w.log) if x[2]).split(" ", 1)[1]
                break
        moves[move] += 1
        yields_ += len(a.__dict__.get("experiment_yields", []))
        rescued += w.read().get("white_rook_h1_bearing") != "hanging"
    results[label] = (rescued, yields_, moves)
    print(f"experimentation {label}: rook no longer hanging after White's move {rescued}/{seeds}; experiment yields {yields_}; moves {dict(moves)}")
ok1 = x1 and all(x1.get(m, 0) >= 1 for m in ("h1h2", "h1h3", "f1g2", "f2f3") if m in x1) and all(x1.get(m, 0) <= 0 for m in ("b2b4", "a1a2") if m in x1)
print(f"X1: {'met' if ok1 else 'NOT met'}; X2: yields with 0: {results['0'][1]}; X3: {'met' if results['0'][0] > results['unset'][0] else 'NOT met'}")
mate_oracle.close()
