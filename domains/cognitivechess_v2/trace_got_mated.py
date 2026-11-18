"""How White got mated (a game whose result is 0-1): from the game's checkpoint (nothing run), White's last position, the move it played,
Black's mating replies after it, Black's plans on White's king before and after White's move (plans.held), and the register's reading of
that king plan region then. python -X utf8 trace_got_mated.py checkpoints/rung4p_full_s0_g<n>.pkl"""
import sys

import chess

import plans
import rung4p
from plansworld import plan_obj
from rustboard import square_name

sys.stdout.reconfigure(encoding="utf-8")
a, w, b, s = rung4p.load_run(sys.argv[1])
board, where, label, mover = w.__dict__["last_game"][-1]
uci = label.split(" ", 1)[1]
cb = chess.Board(board.to_fen())
print(f"White's last position: {board.to_fen()}\n  played {label} ({cb.san(chess.Move.from_uci(uci))})")
king = board._king_sq[True]
WHITE, BLACK = True, False


def king_plan(bd):
    h = plans.held(bd, BLACK, WHITE, {})
    k = bd._king_sq[WHITE]
    g = ("piece", k)
    return h.get(g), plan_obj(*g)


before = king_plan(board)
print(f"  Black's plan on White's king before the move: {before[1]} -> {before[0]}  (depth, a thwarting move)")
after = board.copy()
after.push(next(m for m in board.legal_moves if m.uci() == uci))
mates = []
for r in after.legal_moves:
    c = after.copy()
    c.push(r)
    if not c.legal_moves and c.is_in_check(WHITE):
        mates.append(r.uci())
print(f"  after it, Black's mating replies: {mates} of {len(after.legal_moves)} legal replies")
cb.push(chess.Move.from_uci(uci))
print(f"  python-chess agrees: {[m.uci() for m in cb.legal_moves if (cb.push(m) or True) and (cb.is_checkmate() if True else False) | (cb.pop() and False)]}")
safe = []
for m in board.legal_moves:
    c = board.copy()
    c.push(m)
    if not any((lambda d: (d.push(r) or True) and not d.legal_moves and d.is_in_check(WHITE))(c.copy()) for r in c.legal_moves):
        safe.append(m.uci())
print(f"  White moves that leave Black no mate in one: {len(safe)} of {len(board.legal_moves)}; the move played safe: {uci in safe}")
pred = [x for x in a.__dict__.get("prediction_answers", []) if "king" in str(x[1]) or square_name(king) in str(x[1])][-5:]
print(f"  last predictions answered about the king's square: {pred}")
row = a.mind.territory.rows.get(before[1], {})
print(f"  register's row {before[1]}: holder {row.get('holder')}, last history {row.get('history', [])[-4:]}")
