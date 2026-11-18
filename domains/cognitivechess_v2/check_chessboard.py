"""Checks chess_board (the Rust board, PLAN.md step 1) against python-chess.
1. perft node counts on standard positions (start, Kiwipete, positions 3-5 of the chessprogramming wiki).
2. Random games (seeded): at every position, the legal moves, the board after each move made (placement, turn, castling, en passant,
   clocks), attacks on every square by both colours, check, checkmate, stalemate, result, and pressure (press_map) against the same
   reading done with python-chess wherever the turned position is a legal one.
3. A turned board (the side not to move in check): the king capture is among the moves, and nowhere else.
python -X utf8 check_chessboard.py [games]"""
import random
import sys
import time

import chess

import chess_board

PERFT = [   # (FEN, depth, nodes)
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 4, 197281),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 3, 97862),
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 4, 43238),
    ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 3, 9467),
    ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 3, 62379),
]


def perft(b, depth):
    if depth == 0:
        return 1
    n = 0
    for f, t, p, *_ in b.legal_move_tuples():
        c = b.copy()
        c.push_move(f, t, p)
        n += perft(c, depth - 1)
    return n


def uci_set(b):
    return {chess.Move(f, t, p or None).uci() for f, t, p, *_ in b.legal_move_tuples()}


def press_py(board, colour):
    """press_map read with python-chess: colour's legal moves with the turn set to it and no en passant square, by landing square; a
    pawn's push and castling press nothing. None if that turned position isn't a legal chess position."""
    t = board.copy(stack=False)
    t.turn = colour
    t.ep_square = None
    if not t.is_valid():
        return None
    out = {}
    for m in t.legal_moves:
        if t.piece_type_at(m.from_square) == chess.PAWN and chess.square_file(m.from_square) == chess.square_file(m.to_square):
            continue
        if t.is_castling(m):
            continue
        out.setdefault(m.to_square, set()).add(m.from_square)
    return out


def main(games):
    bad = 0
    t0 = time.time()
    for fen, depth, nodes in PERFT:
        got = perft(chess_board.ChessBoard.from_fen(fen), depth)
        ok = got == nodes
        bad += not ok
        print(f"perft {'ok ' if ok else 'BAD'} {got:>7} (expected {nodes}) depth {depth}: {fen}")
    print(f"  perft took {time.time() - t0:.1f}s")
    rng = random.Random(0)
    positions = press_checked = press_skipped = 0
    for g in range(games):
        ref = chess.Board()
        rb = chess_board.ChessBoard.starting_position()
        for ply in range(200):
            positions += 1
            if uci_set(rb) != {m.uci() for m in ref.legal_moves}:
                bad += 1
                print(f"MOVES differ, game {g} ply {ply}: {ref.fen()}\n  rust only {uci_set(rb) - {m.uci() for m in ref.legal_moves}}"
                      f"\n  python-chess only {{m.uci() for m in ref.legal_moves}} - uci_set(rb)")
                break
            for sq in chess.SQUARES:
                for col in (chess.WHITE, chess.BLACK):
                    if rb.is_attacked_by(sq, col) != ref.is_attacked_by(col, sq):
                        bad += 1
                        print(f"ATTACK differs at {chess.square_name(sq)} by {col}: {ref.fen()}")
            checks = [(rb.is_in_check(ref.turn), ref.is_check(), "check"), (rb.is_checkmate(), ref.is_checkmate(), "mate"),
                      (rb.is_stalemate(), ref.is_stalemate(), "stalemate")]
            for a, b, what in checks:
                if a != b:
                    bad += 1
                    print(f"{what} differs ({a} vs {b}): {ref.fen()}")
            for col in (chess.WHITE, chess.BLACK):
                want = press_py(ref, col)
                if want is None:
                    press_skipped += 1
                    continue
                press_checked += 1
                got = {k: set(v) for k, v in rb.press_map(col).items()}
                if got != want:
                    bad += 1
                    print(f"PRESS differs for {col}: {ref.fen()}")
            if ref.is_game_over(claim_draw=False) and (ref.is_checkmate() or ref.is_stalemate()):
                outcome = ref.outcome()
                want = outcome.result()
                if rb.result() != want:
                    bad += 1
                    print(f"RESULT differs ({rb.result()} vs {want}): {ref.fen()}")
                break
            moves = list(ref.legal_moves)
            if not moves:
                break
            m = rng.choice(moves)
            ref.push(m)
            rb.push_move(m.from_square, m.to_square, m.promotion or 0)
            a, b = rb.to_fen().split(), ref.fen(en_passant="fen").split()
            if a[:3] != b[:3] or a[4:] != b[4:] or (rb.en_passant if rb.en_passant >= 0 else None) != ref.ep_square:
                bad += 1
                print(f"BOARD differs after {m.uci()}:\n  rust   {rb.to_fen()}\n  python {ref.fen(en_passant='fen')} (ep {ref.ep_square})")
                break
    print(f"random games {games}: {positions} positions; pressure checked {press_checked}, skipped (turned position not legal) {press_skipped}")
    # 3. a turned board: Black has just given check (Qh4+ in the fool's mate line, before mate), White's turn handed to Black
    b = chess_board.ChessBoard.from_fen("rnb1kbnr/pppp1ppp/8/4p3/5PPq/8/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    t = b.copy()
    t.turn = False
    king_takes = [(f, t_) for f, t_, *_ in t.legal_move_tuples() if t_ == 4]
    print(f"turned board (checkmate position, Black to move): moves taking White's king on e1: {king_takes}; "
          f"White to move has {len(b.legal_move_tuples())} moves, checkmate {b.is_checkmate()}, result {b.result()}")
    bad += not king_takes or b.legal_move_tuples() or not b.is_checkmate()
    print("ALL OK" if not bad else f"{bad} DIFFERENCES", f"({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
