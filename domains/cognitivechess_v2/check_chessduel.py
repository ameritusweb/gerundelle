"""Checks the two-mind duel (chessduel.py): two fresh minds, short games (a 20 half-move cap); the seats stay one game after every move
(play_game raises if not), both seats record the same results, both start the next game together, and Black's seat reads Black's own
plans, outcome and standing. python -u -X utf8 check_chessduel.py [games]"""
import sys

from chessduel import BLACK, WHITE, ChessDuel, new_mind

sys.stdout.reconfigure(encoding="utf-8")
games = int(sys.argv[1]) if len(sys.argv) > 1 else 2
aw, ww = new_mind(WHITE, half_moves=20, seed=0)
ab, wb = new_mind(BLACK, half_moves=20, seed=1)
d = ChessDuel({WHITE: aw, BLACK: ab}, {WHITE: ww, BLACK: wb})
bad = 0
for g in range(games):
    r = d.play_game()
    rw, rb = ww.games[-1], wb.games[-1]
    ok = rw[0] == rb[0] and rw[2] == rb[2]
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} game {g + 1}: White's seat {rw}; Black's seat {rb}")
print("seats:", ww.me_name, ww.outcome_obj, "|", wb.me_name, wb.outcome_obj)
print("Black's seat objects of its own:", sorted(o for o in wb.shown if o in ("outcome_black", "standing_black", "plan_stalemate")))
print("Black's mind's territory rows (kinds):", sorted({r.split('_')[0] + '_' + r.split('_')[1] for r in ab.mind.territory.rows if '_' in r})[:12])
print("ALL OK" if not bad else f"{bad} BAD")
import mate_oracle   # (Stockfish closed, so the process exits)
mate_oracle.close()
