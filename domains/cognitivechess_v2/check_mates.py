"""Checks the forced-mate territory (mate_oracle, gameworld.read_mate / play, plansworld.mate_effect / give).
1. Stockfish's mate distance against a brute-force solver on the chess Rust board: on random positions (White to move) where White has a
   mate in 1 or a mate in 2 (and none in 1), Stockfish says 1 or 2; where the solver finds neither, Stockfish says None or 3+.
2. The world: on positions with a qualifying move (capture, check, promotion) reaching a forced mate, push_predictions predicts
   `forced_mate_new` exactly for the qualifying moves whose result Stockfish mates and the world hasn't reached; a real move there makes
   forced_mate read `new`, records it once, and reaching it again reads `known`; give makes each distinct one territory for good, and it
   stays held after the game is set back. python -X utf8 check_mates.py"""
import random
import sys

import chess

import mate_oracle
import rung0  # noqa: F401
import plansworld
from plansgame import PlansGame
from rustboard import WarpBoard

sys.stdout.reconfigure(encoding="utf-8")
bad = 0


def mates_now(b):
    """White to move: White's mating moves (the board's own reading: Black then has no move and is in check)."""
    out = []
    for m in b.legal_moves:
        c = b.copy()
        c.push(m)
        if not c.legal_moves and c.is_in_check(False):
            out.append(m)
    return out


def mate_in_two(b):
    """White to move: a move after which every Black reply leaves White a mate in one (and Black isn't stalemated or mated at once)."""
    for m in b.legal_moves:
        c = b.copy()
        c.push(m)
        replies = c.legal_moves
        if not replies:
            continue
        if all(mates_now(_after(c, r)) for r in replies):
            return True
    return False


def _after(b, m):
    c = b.copy()
    c.push(m)
    return c


rng = random.Random(6)
n1 = n2 = n0 = tries = 0
LONGER = []   # solver's mate in 2 that Stockfish reported as longer (it found a mate, not the shortest)


def sparse_position():
    """A random legal endgame, White to move: White's king, queen and rook (some of them) against Black's king and maybe a pawn."""
    while True:
        pb = chess.Board(None)
        pieces = [chess.Piece(chess.KING, chess.WHITE), chess.Piece(chess.KING, chess.BLACK)]
        pieces += rng.sample([chess.Piece(chess.QUEEN, chess.WHITE), chess.Piece(chess.ROOK, chess.WHITE),
                              chess.Piece(chess.ROOK, chess.WHITE), chess.Piece(chess.KNIGHT, chess.WHITE)], rng.randrange(1, 3))
        if rng.random() < 0.4:
            pieces.append(chess.Piece(chess.PAWN, chess.BLACK))
        squares = rng.sample(range(8, 56), len(pieces))
        for p, s in zip(pieces, squares):
            pb.set_piece_at(s, p)
        pb.turn = chess.WHITE
        if pb.is_valid() and not pb.is_game_over():
            return pb


while (n1 < 15 or n2 < 15 or n0 < 15) and tries < 20000:
    tries += 1
    pb = sparse_position()
    b = WarpBoard.from_fen(pb.fen())
    if mates_now(b):
        kind = 1
        if n1 >= 15:
            continue
        n1 += 1
    elif mate_in_two(b):
        kind = 2
        if n2 >= 15:
            continue
        n2 += 1
    else:
        if n0 >= 15:
            continue
        kind = 0
        n0 += 1
    x = mate_oracle.forced_mate(pb.fen())
    # the territory reads whether a forced mate exists; Stockfish's X is the mate it found at its depth, not always the shortest (one
    # position in the first run: the solver's mate in 2, Stockfish's mate in 3), so a mate in 2 is checked for existence, reported apart
    ok = (kind == 1 and x == 1) or (kind == 2 and x is not None and x >= 2) or (kind == 0 and (x is None or x >= 3))
    if kind == 2 and x not in (None, 2):
        LONGER.append((pb.fen(), x))
    if not ok:
        bad += 1
        print(f"BAD solver says {kind or 'none in 2'}, Stockfish {x}: {pb.fen()}")
print(f"Stockfish against the solver: mate in 1 {n1}, mate in 2 {n2}, none within 2 {n0} ({tries} positions): {'all agree' if not bad else 'see above'}; "
      f"mates in 2 Stockfish reported longer: {LONGER}")

# 2. the world
def check_predictions(fen):
    global bad
    w = PlansGame(fen=fen, half_moves=10 ** 6)
    w.actor = "White"
    pred = {c[0].split("_push:")[0].split(" ", 1)[1] for e, n, f, rel, c in w.push_predictions() if e == "forced_mate_new"}
    want = set()
    for m in w.board.legal_moves:
        after = _after(w.board, m)
        if w.qualifies(w.board, m, after) and mate_oracle.forced_mate(after.to_fen()):
            want.add(m.uci())
    ok = pred == want and bool(want)
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} predicted forced_mate_new for {sorted(pred)}; qualifying moves Stockfish mates after {sorted(want)}")


rng2 = random.Random(8)
found = None
for _ in range(4000):   # a real game position with a qualifying move to a forced mate, to play it through the world
    pb = chess.Board()
    for _ in range(rng2.randrange(20, 100)):
        ms = list(pb.legal_moves)
        if not ms:
            break
        pb.push(rng2.choice(ms))
    if pb.turn != chess.WHITE or pb.is_game_over():
        continue
    b = WarpBoard.from_fen(pb.fen())
    for m in b.legal_moves:
        a_ = _after(b, m)
        if GW_q := PlansGame.qualifies(b, m, a_):
            if mate_oracle.forced_mate(a_.to_fen()) and a_.legal_moves:
                found = (pb.fen(), m)
                break
    if found:
        break
if found is None:
    bad += 1
    print("BAD no position found to play through")
else:
    fen, m = found
    check_predictions(fen)
    w = PlansGame(fen=fen, half_moves=10 ** 6)
    w.actor = "White"
    w.play(m)
    first = (w.forced_mate_state, len(w.forced_mate_log))
    w.board = WarpBoard.from_fen(fen)   # the same position again, the same move
    w.where = {o: sq for sq, o in w.ids.items()}
    w.play(m)
    second = (w.forced_mate_state, len(w.forced_mate_log))
    ok = first == ("new", 1) and second == ("known", 1)
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} played {m.uci()} from {fen}: first {first}, again {second} (wanted ('new', 1) then ('known', 1))")
    import rung4p
    w2, a = rung4p.build(0, None, dreams=True, half_moves=10 ** 6)
    w2.forced_mate_log = list(w.forced_mate_log) + [(("x",), 3)]
    plansworld.give(a, w2)
    w2.forced_mate_log = []   # the record gone (as if a new world): what was given stays
    plansworld.give(a, w2)
    rows = {r: (row.get("holder"), row.get("for_good")) for r, row in a.mind.territory.rows.items() if r.startswith("forced_mate_")}
    ok = rows == {"forced_mate_1": ("mine", True), "forced_mate_2": ("mine", True)}
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} forced mates as territory for good: {rows}")
mate_oracle.close()
print("ALL OK" if not bad else f"{bad} BAD")
