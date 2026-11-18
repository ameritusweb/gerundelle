"""Checks ChessDuel.align on the league's saved minds (sub-round 2's pairings, which began apart): the seats begin as one game and the
first four half-moves are played in both. Nothing is saved. python -u -X utf8 check_align.py"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
import league
import mate_oracle
import rung4p
from chessduel import BLACK, WHITE, ChessDuel
from rung4 import TURN_STEPS

bad = 0
for w_name, b_name in (("impatient", "restless"), ("steady", "patient")):
    agents, worlds = {}, {}
    for side, name, colour in ((WHITE, w_name, "white"), (BLACK, b_name, "black")):
        agents[side], worlds[side], _, _ = rung4p.load_run(league.path(name, colour))
        print(f"{name} {colour}: saved {worlds[side].moved} half-moves into its game, {worlds[side].board.to_fen()}")
    d = ChessDuel(agents, worlds)
    d.align()
    print("aligned:", worlds[WHITE].board.to_fen(), "|", worlds[BLACK].board.to_fen())
    for _ in range(4):   # (play_game's turn loop, four half-moves)
        mover = worlds[WHITE].board.turn
        n = d.moved_count(mover)
        for _ in range(TURN_STEPS * 20):
            d.step(mover)
            if d.moved_count(mover) > n:
                d.mirror(mover)
                break
    same = worlds[WHITE].board.to_fen().split()[:4] == worlds[BLACK].board.to_fen().split()[:4]
    print(f"after: White's seat {worlds[WHITE].moved}, Black's seat {worlds[BLACK].moved} half-moves; one game {same}\n")
    bad += not (same and worlds[WHITE].moved >= 4)
print("ALL OK" if not bad else f"{bad} BAD")
mate_oracle.close()
