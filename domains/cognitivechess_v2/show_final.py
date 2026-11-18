"""The final position of a finished game, replayed from the world's move log in a checkpoint.
python -X utf8 show_final.py checkpoints/rung4p_full_s0_g10.pkl 10
(The log keeps every move played, both sides, across games; games[i][2] is game i's half-moves. The checkpoint is saved after the next
game's first move may already be played, so the moves after the last finished game are skipped.)"""
import sys

import chess

from rung4p import load_run
from warpworld import START

path, game = sys.argv[1], int(sys.argv[2])
agent, world, black, state = load_run(path)
moves = [x[1].split(" ", 1)[1] for x in world.log if x[2]]
lens = [g[2] for g in world.games]
print("games recorded:", len(lens), "| moves in the log:", len(moves), "| half-moves per game:", lens)
# the log may begin after some games (a resumed run); count back from the end of the finished games
end = len(moves) - world.moved            # the game in progress's moves come last
start = end - sum(lens[game - 1:])
stop = start + lens[game - 1]
b = chess.Board(START)
for u in moves[start:stop]:
    b.push_uci(u)
print("game", game, "result recorded:", world.games[game - 1])
print("moves:", " ".join(moves[start:stop]))
print("FEN:", b.fen())
print("checkmate:", b.is_checkmate(), "| stalemate:", b.is_stalemate(), "| outcome:", b.outcome())
print()
print(b.unicode(borders=True, empty_square="·"))
