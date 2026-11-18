"""Finds the position that crashed Stockfish in a league game: replays the game's log and analyses every position (and, at each, both
colours' readings as mate_oracle asks them) with a fresh engine per crash. python -X utf8 trace_stockfish_crash.py <tag>"""
import re
import sys

import chess
import chess.engine

from mate_oracle import DEPTH, ENGINE

tag = sys.argv[1]
b = chess.Board()
fens = []
for line in open(f"league/logs/{tag}.log", encoding="utf-8"):
    if "game over" in line:
        break
    m = re.search(r"(?:White|Black)\s+[\d.]+s: .*?moved \d+ ([a-h][1-8][a-h][1-8][qrbn]?)", line)
    if m:
        b.push_uci(m.group(1))
        fens.append((len(b.move_stack), m.group(1), b.fen()))
print("positions", len(fens))
e = chess.engine.SimpleEngine.popen_uci(ENGINE)
e.configure({"Threads": 1, "Hash": 16})
for n, uci, fen in fens:
    try:
        board = chess.Board(fen)
        if not board.is_game_over():
            e.analyse(board, chess.engine.Limit(depth=DEPTH), game=n)
    except chess.engine.EngineTerminatedError as x:
        print(f"CRASH at half-move {n} after {uci}: {fen} ({x})")
        e = chess.engine.SimpleEngine.popen_uci(ENGINE)
        e.configure({"Threads": 1, "Hash": 16})
print("last position", fens[-1] if fens else None)
e.quit()
