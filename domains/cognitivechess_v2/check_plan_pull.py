"""Params.plan_as_pull (the user, 2026-11-17, "do it"). The play app's game: 1. c4 e5 2. e4 Bc5 3. g4 d6, White to move, where a fresh
mind's planner played 4. g5 for its want "potential:plan_outpost+2_none" and left the pawn hanging. Fresh minds (the league's
configure, accepting_patient: the felt loss on), handed that want, 10 seeds, plan_as_pull off and on. Expectations written before:
  G1 (on): the planned step's pull is in the tournament (plan_pulls recorded), and g5 is chosen less often than off.
  G2 (on): no move that leaves a piece of its own hanging is chosen more often than off.
python -X utf8 check_plan_pull.py [seeds]"""
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

WANT = "potential:plan_outpost+2_none"
seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 10
b0 = chess.Board()
for san in ("c4", "e5", "e4", "Bc5", "g4", "d6"):
    b0.push_san(san)
FEN = b0.fen()
hanging = None
for on in (False, True):
    moves, pulls = Counter(), 0
    for seed in range(seeds):
        w, a = rung4p.build(seed, FEN, dreams=True, half_moves=4)
        configure(a, PROFILES["accepting_patient"])
        a.mind.p.plan_as_pull = on
        w.shown = w.read()
        give(a, w)
        if hanging is None:
            hanging = sorted({p[4][0].split("_push")[0].split(" ", 1)[1] for p in w.push_predictions() if p[0].endswith("_bearing_hanging")})
            print("moves leaving a piece of its own hanging:", hanging)
        a.goal, a.stack, a.sub_since = WANT, [], a.mind.t
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
        pulls += len(a.__dict__.get("plan_pulls", []))
    hung = sum(moves[m] for m in hanging)
    print(f"plan_as_pull {'on ' if on else 'off'}: moves {dict(moves)}; g5 {moves['g4g5']}; leaving a piece hanging {hung}; pulls {pulls}")
mate_oracle.close()
