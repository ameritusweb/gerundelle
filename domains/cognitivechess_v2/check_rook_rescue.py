"""Params.defense_gains: a lost region brought back is felt (the play app: 1. g4 b6 2. g5 Bb7, the rook on h1 attacked down the long
diagonal; the mind played 3. d4). Fresh minds (the league's configure, accepting_patient) play 1. g4 and 2. g5 against Black's b6 and
Bb7, so the rook's bearing was held before it went hanging; then White's third move. 10 seeds, defense_gains off and on. Expectations
written before the run:
  K1 (on): the moves saving the rook carry a positive felt defense.
  K2: the rook saved more often with it on than off.
python -X utf8 check_rook_rescue.py [seeds]"""
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


def black_plays(w, uci):
    move = next(m for m in w.board.legal_moves if m.uci() == uci)
    w.actor = "Black"
    w.pend["Black"] = {}
    w.act((w.label(move), w.ids_at(move.from_square), "present"))
    w.pend["Black"] = {}
    w.actor = "White"


def white_turn(w, a, force=None):
    for t in range(TURN_STEPS * 6):
        n0 = w.moved
        choice, _ = a.tick() if force is None else a.tick(force=next(i for i in w.invitations() if i[0].endswith(force)))
        read_mate_passed(a, choice)
        give(a, w)
        if w.moved > n0:
            return next(x[1] for x in reversed(w.log) if x[2]).split(" ", 1)[1]
    return None


for on in (False, True):
    saved, moves, k1 = 0, Counter(), []
    for seed in range(seeds):
        w, a = rung4p.build(seed, None, dreams=True, half_moves=20)
        configure(a, PROFILES["accepting_patient"])
        a.mind.p.defense_gains = on
        w.shown = w.read()
        give(a, w)
        white_turn(w, a, force="g2g4")
        black_plays(w, "b7b6")
        white_turn(w, a, force="g4g5")
        black_plays(w, "c8b7")
        move = white_turn(w, a)
        moves[move] += 1
        b = chess.Board(w.board.to_fen())
        rook = chess.H1 if move is None or not move.startswith("h1") else chess.parse_square(move[2:4])
        safe = not (b.is_attacked_by(chess.BLACK, rook) and not b.is_attacked_by(chess.WHITE, rook))
        saved += safe
    print(f"defense_gains {'on ' if on else 'off'}: rook saved {saved}/{seeds}; moves {dict(moves)}")
mate_oracle.close()
