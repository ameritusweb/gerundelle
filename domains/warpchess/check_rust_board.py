"""Whether the Rust board (warp_board, built 2026-04-11 from WarpOneChess/rust_board) generates exactly the Python board's legal moves
(the user, 2026-11-13: "Build the Rust board"), before plans.py uses it. Positions from random play out of the ladder's rooms and out of
the full starting position (castling rights, flips, promotions); for each, the two engines' legal moves compared as (from, to, flip type,
flip from, flip to, promotion); and the time of each, Python's cache cleared first. The Python board carries the 2026-11-06 castling fix
(a king's 2-square move treated as castling regardless of rights); the Rust board was built before it.
Run: python -u -X utf8 check_rust_board.py [games per start] [plies per game]"""
import random
import sys
import time

import rung0  # noqa: F401
import warp_board as wb
from warpworld import RUNG1_TWO, RUNG2B, WarpBoard

GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 60
PLIES = int(sys.argv[2]) if len(sys.argv) > 2 else 60
rng = random.Random(1)


def key(m):
    return (m.from_square, m.to_square, int(m.flip_type), m.flip_from, m.flip_to, m.promotion or None)


starts = [WarpBoard.from_fen(RUNG1_TWO), WarpBoard.from_fen(RUNG2B), WarpBoard.starting_position()]
positions, differ, t_py, t_rs = 0, [], 0.0, 0.0
pushes, push_differ = 0, []
for start in starts:
    for g in range(GAMES):
        b = start.copy()
        for ply in range(PLIES):
            WarpBoard._legal_cache.clear()
            t0 = time.perf_counter()
            py = b.legal_moves
            t1 = time.perf_counter()
            rb = wb.PyWarpBoard.from_fen(b.to_fen())
            rs = rb.legal_moves
            t2 = time.perf_counter()
            t_py += t1 - t0
            t_rs += t2 - t1
            positions += 1
            a, c = {key(m) for m in py}, {key(m) for m in rs}
            if a != c:
                differ.append((b.to_fen(), sorted(a - c)[:3], sorted(c - a)[:3]))
            by_key = {key(m): m for m in rs}   # (2026-11-13, after the castling fix in push: each move made in both, the boards compared)
            for m in py:
                rm = by_key.get(key(m))
                if rm is None:
                    continue
                b2 = b.copy()
                b2.push(m)
                r2 = wb.PyWarpBoard.from_fen(b.to_fen())
                r2.push(rm)
                pushes += 1
                if r2.to_fen() != b2.to_fen():
                    push_differ.append((b.to_fen(), key(m), b2.to_fen(), r2.to_fen()))
            if not py or b.is_game_over():
                break
            b.push(rng.choice(py))
print(f"{positions} positions; moves differ in {len(differ)}; Python {t_py / positions * 1000:.3f} ms a position (uncached), "
      f"Rust (with the FEN round trip) {t_rs / positions * 1000:.3f} ms")
for fen, only_py, only_rs in differ[:6]:
    print(f"  {fen}\n     only Python: {only_py}\n     only Rust:   {only_rs}")
print(f"moves made in both: {pushes}; boards differ after {len(push_differ)}")
for fen, k, a_, b_ in push_differ[:6]:
    print(f"  {fen} {k}")
    print(f"     Python: {a_}")
    print(f"     Rust:   {b_}")
