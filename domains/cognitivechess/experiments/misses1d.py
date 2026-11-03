"""Rung 1d, candidate support: the second-half positions not mated at the first attempt; what was tried first, the
constraint that kept the mate down, and the mate's own tags."""
import collections
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chess  # noqa: E402
import rung1d as R  # noqa: E402

R.FINE = "--fine" in sys.argv

why = collections.Counter()
for k in range(10):
    fens, history = R.positions(1000 + k, 20), []
    for i, fen in enumerate(fens):
        board = chess.Board(fen)
        cons = R.constraints_from(history)
        mate = R.mates(board)[0]
        mt = R.tags(board, mate)
        blocking = [(e, " ".join(sorted(h))) for e, hs in cons.items() for h in hs if h <= mt]
        n, _ = R.position_run(fen, history, "candidates", k)
        if i >= 10 and n > 1:
            why[tuple(blocking) or ("(none: tied)",)] += 1
            print(f"seed {k} pos {i}: {n} attempts; mate {board.san(mate)} tags {' '.join(sorted(mt))}; runs into {blocking}")
print(why.most_common())
