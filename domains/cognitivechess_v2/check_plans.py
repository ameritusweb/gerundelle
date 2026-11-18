"""Checks plans.py on the chess board, with no mind (PLAN.md step 4): warpchess's check_plans.py, on chess positions.
1. Named positions, for the plan to checkmate:
   - in check now (Black's queen next to White's king): a one-move plan on White's king, thwartable (the king takes the queen);
   - a mating move threatened (1.f3 e5 2.g4 d6: Qh4 would mate): a two-move plan on White's king, thwartable (e.g. e3 opens e2);
   - the start: no plan on the king.
2. Random positions from the start (seeded): plans as read against a full search (every first move, every reply, gains intersected;
   with no reply, mate leaves only the king and stalemate nothing, as plans.no_reply reads it); every one-move plan made by its move; a
   named thwarting move leaves the plan no plan, and where none is named, no move of the mind's does.
python -u -X utf8 check_plans.py [random positions]"""
import random
import sys
import time

import chess

import plans
from rustboard import WarpBoard, square_name

N = int(sys.argv[1]) if __name__ == "__main__" and len(sys.argv) > 1 else 24
WHITE, BLACK = True, False
rng = random.Random(5)


def fen_after(*sans):
    b = chess.Board()
    for s in sans:
        b.push_san(s)
    return b.fen()


def full_two(board, them, me, memo):
    one = plans.one_move(board, them, me, memo)
    b, firsts = plans.moves(board, them, memo)
    out = set()
    for m1 in firsts:
        b1 = plans._after(b, m1)
        r_board, replies = plans.moves(b1, me, memo)
        cands = set(plans.one_move(b1, them, me, memo))
        if not replies:
            ended = plans.no_reply(r_board, replies, me)
            inter = cands & ended
        else:
            inter = None
            for r in replies:
                g = set(plans.one_move(plans._after(r_board, r), them, me, memo))
                inter = g if inter is None else inter & g
        out |= (inter or set()) - set(one)
    return out


READING = []   # differences that are warpchess's documented reading, not bugs


def full_two_from(board, m1, memo):
    """The gains one first move of theirs forces, as full_two reads them."""
    b, _ = plans.moves(board, BLACK, memo)
    b1 = plans._after(b, m1)
    r_board, replies = plans.moves(b1, WHITE, memo)
    if not replies:
        return set(plans.one_move(b1, BLACK, WHITE, memo)) & plans.no_reply(r_board, replies, WHITE)
    inter = None
    for r in replies:
        g = set(plans.one_move(plans._after(r_board, r), BLACK, WHITE, memo))
        inter = g if inter is None else inter & g
    return inter or set()


def name(g):
    return f"{g[0]} {square_name(g[1])}"


def check(b, label, bad):
    memo, fmemo = {}, {}
    t0 = time.perf_counter()
    read = plans.plans(b, BLACK, WHITE, memo)
    t1 = time.perf_counter()
    full = full_two(b, BLACK, WHITE, fmemo) | set(plans.one_move(b, BLACK, WHITE, fmemo))
    t2 = time.perf_counter()
    if set(read) != full:
        # warpchess's documented reading (plans.py's docstring): a two-move plan's candidates are what their second move would gain if I
        # passed, so a gain my every reply would create for them, and a pass wouldn't, isn't read. A difference of that kind is the
        # reading, kept to match warpchess; any other is a bug.
        bt, firsts = plans.moves(b, BLACK, fmemo)
        for g in sorted(set(read) ^ full):
            reading = g not in read and all(g not in plans.one_move(plans._after(bt, m1), BLACK, WHITE, fmemo) for m1 in firsts
                                            if g in full_two_from(b, m1, fmemo))
            (READING if reading else bad).append((label, "plans differ", name(g), "full only" if g not in read else "read only"))
    one = plans.one_move(b, BLACK, WHITE, memo)
    bb, _ = plans.moves(b, BLACK, memo)
    for g, ms in one.items():
        if g not in plans.gains(bb, plans._after(bb, ms[0]), BLACK, WHITE, memo):
            bad.append((label, "one-move plan not made by its move", name(g)))
    h = plans.held(b, BLACK, WHITE, memo)
    wb, wmoves = plans.moves(b, WHITE, memo)
    for g, (depth, x) in h.items():
        if x is not None:
            if plans.still_plan(g, plans._after(wb, x), BLACK, WHITE, fmemo):
                bad.append((label, "named thwart doesn't thwart", name(g)))
        elif any(not plans.still_plan(g, plans._after(wb, y), BLACK, WHITE, fmemo) for y in wmoves):
            bad.append((label, "a thwart exists but none was named", name(g)))
    t3 = time.perf_counter()
    return read, h, (t1 - t0, t2 - t1, t3 - t2)


def king_plan(h, b):
    k = b._king_sq[WHITE]
    return h.get(("piece", k))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    bad = []
    named = [
        ("in check now: Black's queen beside White's king", "4k3/8/8/8/8/8/4q3/4K3 w - - 0 1", (1, "thwart")),
        ("mate threatened: 1.f3 e5 2.g4 d6 (Qh4 mates)", fen_after("f3", "e5", "g4", "d6"), (2, "thwart")),
        ("no threat: the start", chess.STARTING_FEN, "absent"),
    ]
    for label, fen, want in named:
        b = WarpBoard.from_fen(fen)
        read, h, t = check(b, label, bad)
        kp = king_plan(h, b)
        got = None if kp is None else (kp[0], "thwart" if kp[1] is not None else "unstoppable")
        thw = kp[1].uci() if kp and kp[1] is not None else None
        ok = (want == "absent" and kp is None) or (want is None) or (kp is not None and got == want)
        if not ok:
            bad.append((label, "king plan", got, "wanted", want))
        print(f"{'ok ' if ok else 'BAD'} {label}: king plan {got} (thwart {thw}); {len(read)} plans; read {t[0]:.2f}s full {t[1]:.2f}s held {t[2]:.2f}s")
    positions = []
    for _ in range(N):
        c = chess.Board()
        for _ in range(rng.randrange(4, 40)):
            ms = list(c.legal_moves)
            if not ms:
                break
            c.push(rng.choice(ms))
        if c.turn == chess.BLACK and list(c.legal_moves):
            c.push(rng.choice(list(c.legal_moves)))
        if c.turn == chess.WHITE and not c.is_game_over():
            positions.append(c.fen())
    tt = [0.0, 0.0, 0.0]
    kinds = {}
    for k, fen in enumerate(positions):
        read, h, t = check(WarpBoard.from_fen(fen), f"random {k}", bad)
        for i in range(3):
            tt[i] += t[i]
        for g, (depth, x) in h.items():
            key = (g[0], depth, "held" if x is not None else "unstoppable")
            kinds[key] = kinds.get(key, 0) + 1
    print(f"random positions {len(positions)}: read {tt[0]:.1f}s, full search {tt[1]:.1f}s, held {tt[2]:.1f}s; plans by kind {dict(sorted(kinds.items()))}")
    print(f"differences that are warpchess's documented reading (a gain my every reply creates, not there if I passed): {len(READING)}: {READING[:8]}")
    print("problems:", bad[:12] if bad else "none")
