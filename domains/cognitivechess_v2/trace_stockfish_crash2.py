"""The boards White's move predictions hand Stockfish from a position (plansworld.push_predictions: plans._after(plans.turned(board, me),
move)), each checked by python-chess and analysed. python -X utf8 trace_stockfish_crash2.py "<FEN>" """
import sys

import chess
import chess.engine

import plans
from mate_oracle import DEPTH, ENGINE
from rustboard import WarpBoard

fen = sys.argv[1]
board = WarpBoard.from_fen(fen)
me = board.turn
e = chess.engine.SimpleEngine.popen_uci(ENGINE)
e.configure({"Threads": 1, "Hash": 16})
for move in board.legal_moves:
    b = plans._after(plans.turned(board, me), move)
    f = b.to_fen()
    pb = chess.Board(f)
    status = pb.status()
    note = "" if status == chess.STATUS_VALID else f" INVALID {status!r}"
    try:
        if not pb.is_game_over():
            e.analyse(pb, chess.engine.Limit(depth=DEPTH))
        res = "ok"
    except chess.engine.EngineTerminatedError:
        res = "CRASH"
        e = chess.engine.SimpleEngine.popen_uci(ENGINE)
        e.configure({"Threads": 1, "Hash": 16})
    if res != "ok" or note:
        print(f"{move.uci()}: {f}{note} -> {res}")
print("done")
e.quit()
