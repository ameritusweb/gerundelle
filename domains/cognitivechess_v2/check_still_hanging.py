"""A piece that stays hanging (the play app: 1. c3 d5 2. Qb3 e6 3. e3 Bd6 4. d4 Bd7 5. g4 f5 6. h3 Nf6 7. Qxb7 Bc6, White to move, the
queen on b7 attacked by the bishop; the mind played 8. Be2). Expectations written before the run:
  Q1: waiting carries the losses resting on the queen (effects_after(None) non-empty); the moves saving the queen read a better felt
      loss than Be2.
  Q2: 10 fresh minds (the league's configure, accepting_patient): every one saves the queen (after its move the queen is not hanging).
python -X utf8 check_still_hanging.py [seeds]"""
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
for san in ("c3", "d5", "Qb3", "e6", "e3", "Bd6", "d4", "Bd7", "g4", "f5", "h3", "Nf6", "Qxb7", "Bc6"):
    b0.push_san(san)
FEN = b0.fen()
w, a = rung4p.build(0, FEN, dreams=True, half_moves=4)
configure(a, PROFILES["accepting_patient"])
w.shown = w.read()
give(a, w)
print("the queen's bearing:", w.shown.get("white_queen_d1_bearing"))
wait = w.effects_after(None)
invs = {f"{i[0]}_push:{i[1]}_{i[2]}": i for i in w.invitations()}
a.defense_now(invs)
d = a.mind.anti_defense or {}
saving = []
for c, i in invs.items():
    m = chess.Move.from_uci(i[0].split(" ", 1)[1])
    after = b0.copy()
    after.push(m)
    q = next((sq for sq in chess.SQUARES if after.piece_at(sq) == chess.Piece(chess.QUEEN, chess.WHITE)), None)
    safe = q is None or not after.is_attacked_by(chess.BLACK, q) or after.is_attacked_by(chess.WHITE, q)
    if safe:
        saving.append(i[0].split(" ", 1)[1])
be2 = next((v for c, v in d.items() if "f1e2" in c), None)
best_saving = max((v for c, v in d.items() if any(s in c for s in saving)), default=None)
print(f"waiting's losses: {len(wait)}; Be2 felt loss {be2}; best queen-saving move's {best_saving}; queen-saving moves {saving}")
chosen = Counter()
saved = 0
for seed in range(seeds):
    w, a = rung4p.build(seed, FEN, dreams=True, half_moves=4)
    configure(a, PROFILES["accepting_patient"])
    w.shown = w.read()
    give(a, w)
    move = None
    for t in range(TURN_STEPS * 6):
        n0 = w.moved
        choice, _ = a.tick()
        read_mate_passed(a, choice)
        give(a, w)
        if w.moved > n0:
            move = next(x[1] for x in reversed(w.log) if x[2]).split(" ", 1)[1]
            break
    chosen[move] += 1
    saved += move in saving
print("chosen:", dict(chosen))
print(f"Q1: {'met' if wait and be2 is not None and best_saving is not None and best_saving > be2 else 'NOT met'}; "
      f"Q2: {'met' if saved == seeds else 'NOT met'} ({saved} of {seeds} saved the queen)")
mate_oracle.close()
