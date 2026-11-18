"""Stockfish as the world's reader of forced mates (cognitivechess_v2; the user, 2026-11-17: "Why not have a Stockfish mate-in-X situation
be territory; that is never given back"; "every distinct; it forces diverse understanding"; "it would only get called on a capture or a
check or a promotion"). Like plans.py's search, it is the world reading its own physics; the mind never sees Stockfish's moves.

forced_mate(fen) -> X >= 1: White has a forced mate in X of its moves from this position (whichever side is to move), or None.
My readings, for the user to change:
- DEPTH: a fixed search depth, so "mate in X" is a mate Stockfish finds at that depth; one thread, and its hash cleared before every
  search (a new game id each call), so a run is the same every time.
- The engine is held by this module, never by the world, so checkpoints don't try to pickle it; answers are cached by FEN (exact).
"""
import itertools

import chess
import chess.engine

ENGINE = __import__("paths").STOCKFISH
DEPTH = 14
_engine = None
_cache = {}
_ids = itertools.count()
_registered = []
invalid, crashed = [], []   # positions refused as impossible, and positions the engine died on (then read again)


def engine():
    global _engine
    if _engine is None:
        _engine = chess.engine.SimpleEngine.popen_uci(ENGINE)
        _engine.configure({"Threads": 1, "Hash": 16})
        if not _registered:   # closed as the program ends, before Python waits on threads: the engine's thread kept every script
            import threading  # that read a mate from exiting (check_win.py waited at its end; the league's workers, 2026-11-17).
            threading._register_atexit(close)   # (atexit runs after that wait, too late)
            _registered.append(True)
    return _engine


def forced_mate(fen, colour=chess.WHITE):
    """`colour`'s forced mate from this position, in moves (X >= 1), or None (White's by default; a seat's own colour in the league).
    A position already checkmated (no move left) is None: the win condition reads that one (plansworld.win_effect)."""
    if fen not in _cache:
        board = chess.Board(fen)
        score = None
        if not board.is_valid():   # (an impossible position is no chess position: no reading; Stockfish crashes on some, 2026-11-17's
            invalid.append(fen)    #  league, exf6 e.p. read with the captured pawn standing, plans.turned. Recorded, for a trace)
        elif not board.is_game_over():
            try:
                score = engine().analyse(board, chess.engine.Limit(depth=DEPTH), game=next(_ids))["score"]
            except chess.engine.EngineTerminatedError:   # (the engine died: restarted, and the position read again once)
                global _engine
                _engine = None
                crashed.append(fen)
                score = engine().analyse(board, chess.engine.Limit(depth=DEPTH), game=next(_ids))["score"]
        _cache[fen] = score
    score = _cache[fen]
    if score is None:
        return None
    s = score.pov(colour)
    return s.mate() if s.is_mate() and s.mate() > 0 else None


def close():
    global _engine
    if _engine is not None:
        _engine.quit()
        _engine = None
