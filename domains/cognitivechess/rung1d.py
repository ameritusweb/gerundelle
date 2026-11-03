"""Rung 1d: constraints that converge on a move never tried (embodied/CONSTRAINT_DISCOVERY.md; JustOne).

Rung 1c found that the mind learns each move's own conditions from that move's failures. Here the constraints have to
carry: every position is new, so the move that mates has never been tried there, and nothing has been learned about it
as a move. Several other moves fail, each for its own reason; the constraints those failures reveal converge on the one
that mates, and the mind notices it through Gerundelle's tournament with candidate support (Params.support, ported from
embodied/gerundelle), as the hand noticed the grasp through the handle from the right (embodied/body/grasp.py).

- **Positions** (`positions`): generated, a black king on its back rank behind pawns (sometimes with luft), White's
  rooks and queen, Black's knights, bishops and rooks placed at random; kept if exactly one move mates in one and at
  least two checks fail, for at least two different reasons. Guards, flights and interposers come from different
  pieces in different places, so relations vary independently of pieces.
- **An attempt is perceived before it is made** (`tags`), its relations read off the board as the move would meet them
  (the hand predicted an untried grasp's tags from the mug as it saw it): whether it checks; whether where it lands is
  guarded; whether the king would have a flight; whether Black could interpose; and what is not a cause: the piece's
  kind, whether it captures, whether it lands on the back rank.
- **A failure is an event** (`event`), what the world's reply did (`ChessWorld.answer`'s rule): no check; the checking
  piece taken; the king stepped out; interposed. A mate is the want.
- **A failure's constraint** (`constraints_from`, grasp.py's): what is distinctive of its failures among the attempts,
  the smallest combination of their tags that no attempt not failing that way carried in full.
- **Noticing** (`choose`): each untried move a molecule tagged with the constraints it clears; each constraint a
  molecule tagged "constraint" whose open site is clearing it; Gerundelle's Mind ticks once; the move made is the top
  bid, ties broken by a seeded order. Support off, the bids tie: a scan in that order.

Measured: attempts to the mate in each position, constraints carried from one position to the next; the share of
positions mated at the first attempt; against support off.

Run: python -X utf8 rung1d.py [--seeds 10] [--positions 20] [--modes none,candidates,resolved] [--no-relations] [--fine] [--receipts]
"""
import argparse
import os
import random
import statistics
import sys
import time

import chess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))
import gerundelle_arm  # noqa: E402,F401  (puts Gerundelle on the path)
from molecules import Mind, Params, clause  # noqa: E402

NAME = {chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop", chess.ROOK: "rook", chess.QUEEN: "queen",
        chess.KING: "king"}
VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


# ---- the world: positions, what a move meets, what the reply does --------------------------------------------------

def mates(board):
    out = []
    for m in board.legal_moves:
        b = board.copy()
        b.push(m)
        if b.is_checkmate():
            out.append(m)
    return out


def event(board, move):
    """What the world's reply makes of a move (ChessWorld.answer's rule): mated; no check (Black then recaptures or
    passes); the checking piece taken (by the least valuable piece that can); else the king stepped out; else
    interposed."""
    b = board.copy()
    b.push(move)
    if b.is_checkmate():
        return "mated"
    if not b.is_check():
        return "no check"
    legal = list(b.legal_moves)
    if any(m.to_square == move.to_square for m in legal):
        return "checker taken"
    if any(b.piece_at(m.from_square).piece_type == chess.KING for m in legal):
        return "king stepped out"
    return "interposed"


RELATIONAL = ("check:", "landing:", "flight:", "interpose:", "guard:", "backed:")
FINE = False           # --fine: who guards the landing square, and whether White backs it
USE_RECEIPTS = False
RECEIPTS = None        # --receipts: the history, so each combination weighs by the failures it accounts for
NO_RELATIONS = False   # the ablation (--no-relations): the attempt perceived without its relations


def tags(board, move):
    out = perceived(board, move)
    return frozenset(t for t in out if not t.startswith(RELATIONAL)) if NO_RELATIONS else out


def perceived(board, move):
    """The relations a move would meet, read off the board by the rules before it is made (perception, not its
    outcome): its piece's kind, whether it captures, whether it lands on Black's back rank (not causes); whether it
    checks, whether where it lands is guarded by Black, whether the black king would have a flight, whether Black
    could interpose."""
    piece = board.piece_at(move.from_square)
    out = {f"piece:{NAME[piece.piece_type]}", f"captures:{'yes' if board.is_capture(move) else 'no'}",
           f"lands:{'back-rank' if chess.square_rank(move.to_square) == 7 else 'elsewhere'}"}
    b = board.copy()
    b.push(move)
    check = b.is_check()
    out.add(f"check:{'yes' if check else 'no'}")
    guards = b.attackers(chess.BLACK, move.to_square)
    out.add(f"landing:{'guarded' if guards else 'open'}")
    if FINE:   # who guards it, and whether White backs it (first only guarded or open: a queen's mate next to the
        # king, guarded by the king alone and backed, read as a check that is taken, and was passed over 36 times)
        kind = "none" if not guards else ("king-only" if all(b.piece_at(sq).piece_type == chess.KING for sq in guards)
                                          else "piece")
        out.add(f"guard:{kind}")
        out.add(f"backed:{'yes' if b.attackers(chess.WHITE, move.to_square) else 'no'}")
    k = b.king(chess.BLACK)
    flight = any(b.piece_at(m.from_square).piece_type == chess.KING and m.to_square != move.to_square
                 for m in b.legal_moves) if check else any(
        not b.attackers(chess.WHITE, sq) and (b.piece_at(sq) is None or b.piece_at(sq).color == chess.WHITE)
        for sq in chess.SquareSet(chess.BB_KING_ATTACKS[k]))
    out.add(f"flight:{'open' if flight else 'none'}")
    between = chess.SquareSet(chess.between(move.to_square, k))
    block = check and any(m.to_square in between and b.piece_at(m.from_square).piece_type != chess.KING
                          for m in b.legal_moves)
    out.add(f"interpose:{'possible' if block else 'none'}")
    return frozenset(out)


def positions(seed, n):
    """n positions with exactly one mate in one and at least two checks that fail, for two different reasons."""
    rng, out, tries = random.Random(seed), [], 0
    while len(out) < n and tries < 200000:
        tries += 1
        b = chess.Board(None)
        kf = rng.randrange(1, 7)
        b.set_piece_at(chess.square(kf, 7), chess.Piece(chess.KING, chess.BLACK))
        for f in (kf - 1, kf, kf + 1):
            rank = 5 if rng.random() < 0.2 else 6
            b.set_piece_at(chess.square(f, rank), chess.Piece(chess.PAWN, chess.BLACK))
        wk = chess.square(rng.choice([0, 1, 6, 7]), 0)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(chess.square(wk % 8 + (1 if wk % 8 < 4 else -1), 1), chess.Piece(chess.PAWN, chess.WHITE))
        for kind in rng.sample([chess.ROOK, chess.ROOK, chess.QUEEN], rng.randrange(1, 4)):
            sq = chess.square(rng.randrange(8), rng.randrange(0, 4))
            if b.piece_at(sq) is None:
                b.set_piece_at(sq, chess.Piece(kind, chess.WHITE))
        for kind in rng.sample([chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.KNIGHT], rng.randrange(0, 4)):
            sq = chess.square(rng.randrange(8), rng.randrange(3, 8))
            if b.piece_at(sq) is None:
                b.set_piece_at(sq, chess.Piece(kind, chess.BLACK))
        b.turn = chess.WHITE
        if not b.is_valid() or b.is_check() or b.is_game_over():
            continue
        if len(mates(b)) != 1:
            continue
        fails = {event(b, m) for m in b.legal_moves if b.gives_check(m)} - {"mated"}
        if len(fails) < 2:
            continue
        out.append(b.fen())
    return out


# ---- the mind: constraints from failures, noticing by support ------------------------------------------------------

def distinguishing(tg, others):
    """The smallest combination of `tg` that no other attempt carried in full, the tags commonest among the others let
    go first; None if some other attempt carried all of them (grasp.py's)."""
    s = set(tg)
    if any(s <= o for o in others):
        return None
    common = {t: sum(t in o for o in others) for t in s}
    for t in sorted(s, key=lambda x: (-common[x], x)):
        if len(s) > 1 and not any((s - {t}) <= o for o in others):
            s.discard(t)
    return frozenset(s)


def constraints_from(history):
    """Each kind of failure's constraints: what is distinctive of its failures among the attempts, merged into what two
    share while that still tells them apart (grasp.py's)."""
    out = {}
    for e in {ev for _, ev in history if ev != "mated"}:
        others = [t for t, ev in history if ev != e]
        conj = []
        for t in [t for t, ev in history if ev == e]:
            d = distinguishing(t, others)
            if d is not None and d not in conj:
                conj.append(d)
        merged = True
        while merged and len(conj) > 1:
            merged = False
            for i in range(len(conj)):
                for j in range(i + 1, len(conj)):
                    d = distinguishing(conj[i] & conj[j], others) if conj[i] & conj[j] else None
                    if d is not None:
                        conj = [c for k, c in enumerate(conj) if k not in (i, j)] + [d]
                        merged = True
                        break
                if merged:
                    break
        if conj:
            out[e] = conj
    return out


def choose(board, cons, tried, mode, rank):
    """The untried move the constraints support most: Gerundelle's tournament, one tick, the top bid; ties by a seeded
    order. Each move clears a constraint unless it would carry all of one of its combinations."""
    options = [m for m in board.legal_moves if m not in tried]
    if not options:
        return None, {}
    pred = {m: tags(board, m) for m in options}
    mind = Mind(Params(support=mode, sov=False, meta=False, closure=False))
    if RECEIPTS is None:
        mols = [clause(f"move:{m.uci()}", tags=("attempt",) + tuple(
            f"clears:{e}" for e, hs in cons.items() if not any(h <= pred[m] for h in hs))) for m in options]
        mols += [clause(f"constraint:{e}", tags=("constraint",), sites=(f"clears:{e}",)) for e in cons]
    else:
        # each combination its own constraint, weighing by its receipts: the failures of its kind that carried it
        # (1 - 1/2^n, grasp.py's rule, there per kind). First each kind one constraint at full weight, and a
        # combination seen once that forbade the mate ("taken when only the king guards", every such check met so far
        # unbacked) passed it over 36 times
        combos = [(f"{e}|{i}", h, sum(1 for t, ev in RECEIPTS if ev == e and h <= t))
                  for e, hs in cons.items() for i, h in enumerate(hs)]
        mols = [clause(f"move:{m.uci()}", tags=("attempt",) + tuple(
            f"clears:{c}" for c, h, _ in combos if not h <= pred[m])) for m in options]
        for c, h, n in combos:
            mind.present(clause(f"constraint:{c}", tags=("constraint",), sites=(f"clears:{c}",)), 1 - 0.5 ** n)
    bids = mind.tick(mols)["levels"][0]["bids"]
    best = max(options, key=lambda m: (round(bids.get(f"move:{m.uci()}", 0.0), 9), -rank(m)))
    return best, pred


def position_run(fen, history, mode, order_seed):
    """Attempts in one position until the mate (each from the position as given). Returns the attempts."""
    board = chess.Board(fen)
    rank = lambda m: random.Random(f"{order_seed}:{fen}:{m.uci()}").random()
    tried, n = set(), 0
    while True:
        cons = constraints_from(history)
        global RECEIPTS
        RECEIPTS = history if USE_RECEIPTS else None
        m, pred = choose(board, cons, tried, mode, rank)
        if m is None:
            return n, False
        n += 1
        tried.add(m)
        ev = event(board, m)
        history.append((pred[m], ev))
        if ev == "mated":
            return n, True


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--positions", type=int, default=20)
    ap.add_argument("--modes", default="none,candidates,resolved")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--no-relations", action="store_true", help="the ablation: no relational tags")
    ap.add_argument("--fine", action="store_true", help="who guards the landing square, and whether White backs it")
    ap.add_argument("--receipts", action="store_true", help="each combination weighs by the failures it accounts for")
    args = ap.parse_args()
    global NO_RELATIONS, FINE, USE_RECEIPTS
    NO_RELATIONS, FINE, USE_RECEIPTS = args.no_relations, args.fine, args.receipts
    t0 = time.time()
    sets = {k: positions(1000 + k, args.positions) for k in range(args.seeds)}
    legal = [len(list(chess.Board(f).legal_moves)) for s in sets.values() for f in s]
    print(f"{args.seeds} sequences of {args.positions} positions; legal moves median {statistics.median(legal)}; "
          f"a scan in a random order takes (n+1)/2 on average  ({time.time() - t0:.0f}s to generate)")
    half = args.positions // 2
    for mode in args.modes.split(","):
        t1, first, later, firsts, cons_seen = time.time(), [], [], 0, None
        for k, fens in sets.items():
            history, row = [], []
            for i, fen in enumerate(fens):
                n, ok = position_run(fen, history, None if mode == "none" else mode, k)
                row.append(n)
                (first if i < half else later).append(n)
                if i >= half and n == 1:
                    firsts += 1
            cons_seen = constraints_from(history)
            if args.verbose:
                print(f"  {mode} seed {k}: attempts per position {row}", flush=True)
        print(f"{mode:10} attempts per position: first half mean {statistics.mean(first):.2f}, second half mean "
              f"{statistics.mean(later):.2f} (median {statistics.median(later)}); second-half positions mated at the "
              f"first attempt {firsts}/{len(later)}  {time.time() - t1:.0f}s")
        print(f"           constraints at the end of the last sequence: "
              f"{ {e: [' '.join(sorted(h)) for h in hs] for e, hs in cons_seen.items()} }")


if __name__ == "__main__":
    main()
