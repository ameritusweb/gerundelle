"""mate_oracle for the browser (site/chess): the native module's forced_mate(fen, colour), asked of Stockfish 19 lite (WASM) through the page
worker's synchronous bridge (sfMate: the bridge worker answers into a SharedArrayBuffer, this worker waits with Atomics.wait; the user,
2026-11-17: "are you sure there's no stockfish/leela tool clone that will work with wasm?"). Depth and caching as the native module."""
import chess
import js

DEPTH = 14
_cache = {}
invalid, crashed = [], []


def forced_mate(fen, colour=chess.WHITE):
    """`colour`'s forced mate from this position, in moves (X >= 1), or None."""
    if fen not in _cache:
        board = chess.Board(fen)
        score = None
        if not board.is_valid():
            invalid.append(fen)
        elif not board.is_game_over():
            m = js.sfMate(fen, DEPTH)   # mate in N from the side to move's view (negative: it is mated), or None
            if isinstance(m, (int, float)) and not isinstance(m, bool) and m != 0:   # (anything else, a jsnull, is no reading)
                score = (int(m), board.turn)
        _cache[fen] = score
    score = _cache[fen]
    if score is None:
        return None
    n, mover = score
    s = n if mover == colour else -n
    return s if s > 0 else None


def close():
    pass
