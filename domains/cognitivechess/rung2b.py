"""Rung 2b (chess-sov-plan.md rung 2, "a book"): a world where being told pays.

Every position is new and is a mate in two whose first move is quiet: no move mates at once; one or two quiet first moves
(no check, no capture; Black, answering by this world's rule, then passes) let a move mate next. The first move brings
nothing, and there is nothing to contrast it against: alone, the mind can only stumble on the line among some forty by
forty pairs. A book knows the line (a full search under this world's own rules). Asked when the mind has no way to its
want, at the start of an episode, it tells two receipts, Gerundelle's told knowledge as it is: the quiet move causes the
facts it changes, and the mating move, as it will stand after the quiet one, causes the mate. With Params.told_effects
the planner chains them into the line; without it, only a told way to the want itself is read.

Coaches: none; the book; a wrong book (a quiet move at random told as the line's first step, and a move at random told
to mate): that the gain is the book's knowledge.

Run: python -X utf8 rung2b.py [--seeds 10] [--positions 12] [--ticks 2400] [--arms alone,book,book_no_effects,wrong]
"""
import argparse
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

import chess  # noqa: E402
import rung1e  # noqa: E402
from chessworld import ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402
from force_world import inv_id  # noqa: E402

FULL = dict(rung1e.ARMS["full"], bridge=True)


def after_pass(board, move):
    capture = board.is_capture(move)   # asked before the move (after it, the moved piece stands on the square)
    b = board.copy()
    b.push(move)
    if not b.is_check() and not capture:
        b.push(chess.Move.null())   # Black passes (this world's answer to a quiet move)
        return b
    return None


def lines(board):
    """The quiet first moves after which some move mates, and those mates: [(quiet, mate)]."""
    out = []
    for q in board.legal_moves:
        if board.is_capture(q) or board.gives_check(q):
            continue
        b = after_pass(board, q)
        if b is None:
            continue
        for m in b.legal_moves:
            c = b.copy()
            c.push(m)
            if c.is_checkmate():
                out.append((q, m))
    return out


def positions(seed, n, most=6):
    """n positions, each a mate in two whose first move is quiet: a mate in one (rung 1d's), hidden by a White bishop put
    on the mating line; the bishop stepping off it (quietly) is the first move. Kept if nothing mates at once and at most
    `most` quiet first moves lead to a mate. (First positions drawn at random: none in 400,000 tries.)"""
    import rung1d
    rng, out = random.Random(seed), []
    for fen in rung1d.positions(seed, 6 * n):
        b = chess.Board(fen)
        mate = rung1d.mates(b)[0]
        between = list(chess.SquareSet(chess.between(mate.from_square, mate.to_square)))
        rng.shuffle(between)
        for sq in between:
            if b.piece_at(sq) is not None:
                continue
            c = b.copy()
            c.set_piece_at(sq, chess.Piece(chess.BISHOP, chess.WHITE))
            if not c.is_valid() or c.is_check() or c.is_game_over():
                continue
            if any((lambda d: (d.push(m), d.is_checkmate())[1])(c.copy()) for m in c.legal_moves):
                continue
            qs = {q for q, _ in lines(c)}
            if 1 <= len(qs) <= most:
                out.append(c.fen())
                break
        if len(out) >= n:
            break
    return out


class Book:
    """Tells the line: the quiet move and what it changes, then the mate. `wrong`: a quiet move and a mate at random."""

    def __init__(self, kind, seed=0):
        self.kind, self.name, self.rng = kind, f"book ({kind})", random.Random(seed)

    def tell(self, world, und, known, log):
        board = chess.Board(world.board.fen())
        ls = lines(board)
        if self.kind == "wrong":
            quiet = [m for m in board.legal_moves if not board.is_capture(m) and not board.gives_check(m)]
            if not quiet:
                return
            q = self.rng.choice(quiet)
            b = after_pass(board, q)
            if b is None or not list(b.legal_moves):
                return
            line = (q, self.rng.choice(list(b.legal_moves)))
        elif ls:
            line = sorted(ls, key=lambda x: (x[0].uci(), x[1].uci()))[0]
        else:
            return
        q, m = line
        # the receipts, in the mind's own terms: the quiet move as the world offers it, and what it changes; then the
        # mating move as it will stand after the quiet one (its label and piece read off the world after the quiet move)
        saved = (world.board.copy(), dict(world.where), dict(world.shown), getattr(world, "last_capture", False))
        try:
            before = world.read()
            q_inv = next(i for i in world.invitations() if i[0].split(" ", 1)[-1] == world.board.san(q).rstrip("+#"))
            world.play(q)
            world.board.push(chess.Move.null())
            now = world.read()
            effects = {f"{o}_{st}" for o, st in now.items() if st != before[o] and o not in world.events}
            world.shown = now
            m_san = world.board.san(m).rstrip("+#")
            m_inv = next((i for i in world.invitations() if i[0].split(" ", 1)[-1] == m_san), None)
        finally:
            world.board, world.where, world.shown, world.last_capture = saved
        cq = inv_id(q_inv)
        for e in effects:
            und.add(cq, "causes", e, "told", 1.0)
            und.tellers[(cq, "causes", e)] = self.name
        known.setdefault(cq, q_inv)
        if m_inv is not None:
            cm = inv_id(m_inv)
            und.add(cm, "causes", "game_mate", "told", 1.0)
            und.tellers[(cm, "causes", "game_mate")] = self.name
            und.add(cm, "after", cq, "told", 1.0)   # it mates after the quiet move (Params.told_effects reads it)
            known.setdefault(cm, m_inv)
        log.append((q_inv[0], m_inv[0] if m_inv else None, sorted(effects)))


def run(seed, arm, n, ticks):
    fens = positions(2000 + seed, n)
    # three of White's moves an episode: the line's two and room for one more (first two: the mind's first move went to
    # an experiment under way, the book's quiet move came second, and the mate it prepared never came; then the quiet
    # move's own record, "nothing happened", rightly came before the book's word)
    w = ChessWorld(fens, order=seed, reply="answer", moves=3, relations=("reply", "game"), sequence=True)
    m = GerundelleMind("White", w, want="game_mate", want_count=10 ** 6)
    for k, v in dict(FULL, told_effects=(arm in ("book", "wrong"))).items():
        setattr(m.agent.mind.p, k, v)
    a, told, asked = m.agent, [], set()
    book = Book("wrong" if arm == "wrong" else "right", seed) if arm in ("book", "book_no_effects", "wrong") else None
    orig = a.planned

    def planned(invs):
        if book is not None and w.moved == 0 and a.goal is not None and not a.stack and not a.queue and not a.running:
            key = w.at
            if key not in asked and a.plan_step(invs) is None:
                asked.add(key)
                book.tell(w, a.mind.understanding, a.known, told)
        return orig(invs)
    a.planned = planned
    per, act = [0] * n, w.act

    def logged(inv=None, hold=False):
        if inv is not None and w.at < n:
            per[w.at] += 1
        return act(inv, hold)
    w.act = logged
    for _ in range(ticks):
        m.step(len(a.tried))
        if w.at >= n - 1 and w.mated:
            break
    done = w.at + (1 if w.mated else 0)
    und = a.mind.understanding
    return dict(done=done, per=per[:done + 1], told=len(told), refuted=len(und.belied), first=told[:2])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--seed-from", type=int, default=0, help="the first seed (to run seeds in parallel)")
    ap.add_argument("--positions", type=int, default=12)
    ap.add_argument("--ticks", type=int, default=2400)
    ap.add_argument("--arms", default="alone,book,book_no_effects,wrong")
    args = ap.parse_args()
    for arm in args.arms.split(","):
        t0, rows = time.time(), []
        for k in range(args.seed_from, args.seed_from + args.seeds):
            r = run(k, arm, args.positions, args.ticks)
            rows.append(r)
            print(f"  {arm} seed {k}: positions mated {r['done']}/{args.positions}; pushes per position {r['per']}; told "
                  f"{r['told']}, refuted {r['refuted']}; first told {r['first'][:1]}", flush=True)
        print(f"{arm:16} positions mated {sum(r['done'] for r in rows)}/{args.seeds * args.positions}; told "
              f"{sum(r['told'] for r in rows)}, refuted {sum(r['refuted'] for r in rows)}  {time.time() - t0:.0f}s",
              flush=True)


if __name__ == "__main__":
    main()
