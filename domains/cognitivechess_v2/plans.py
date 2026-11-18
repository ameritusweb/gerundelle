"""The opponent's plans, and which the mind can thwart (PLAN.md step 2; the user, 2026-11-13: territory is "being able to 'thwart' the
hypothetical plans of the opponent"; "a plan is a gain of a piece, a square, or an outpost").

Read by the board's own physics, the Warp world's pressure (warpworld.WarpWorld.pressure: the squares a side's legal moves would press,
flips included). `me` is the mind's colour, `them` the opponent's. A gain, named by kind and square:
  ("piece", t)    one of my pieces, on t, taken
  ("square", s)   a safe landing on s (one of theirs lands there and I couldn't take it at once), or more pressure than mine on s, newly
                  (the user: "a safe landing or more pressure than the opponent has on it")
  ("outpost", s)  a safe landing on s that is also defended by another of theirs, or that no move of mine could press (the user: both)
Plans (the user: "one or two"; and "read it", the mind's reply between):
  one-move   a gain one of their moves makes now
  two-move   a gain they can make in two moves whatever I reply between: some first move of theirs such that after every reply of mine,
             some second move of theirs makes it (and not already a one-move plan)
Thwartable: I have a move now after which it is no longer a plan of either kind. The mind holds the thwartable plans (the user).

Relevance (the user: "two-move plans shouldn't be that costly if it uses only relevant moves"): a single gain is checked directly
(`there`: only their moves that land on its square, or for a lead, the pressure on it); replies are searched until one refutes it; my
moves until one thwarts it, moves touching its square first. What my pieces could press after one move is read once per position for
every square. Positions are memoized by the engine's hash. A two-move plan's candidates are what their second move would gain if I
passed; a gain my every move would create for them and a pass wouldn't isn't seen (my reading; check_plans.py measures it).
(First version, plans.py.v1: every reply recomputed every gain, and the check never finished its first position.)
"""
from rustboard import KING, WarpMove, flip_square, square_file, square_rank  # noqa: F401
from warpworld import rehash

BLACK, WHITE = False, True


def legal(b):
    """b's legal moves (the Rust board's, rustboard.py; check_rust_board.py: the same moves as the Python board's, in another order:
    every reading here is a set or a search for any one, so which move is named first can differ)."""
    return list(b.legal_moves)


def turned(board, colour):
    """The board with `colour` to move. The en passant square goes only when the turn changes (it belongs to the side to move; first it
    always went, and a move read off the real board's legal moves, an en passant capture, was played on the turned board as a plain
    pawn move with the captured pawn left standing: cognitivechess_v2's league, exf6 e.p. read in White's move predictions, the board
    handed to Stockfish illegal, Black's f5 pawn checking White's king with Black to move, and Stockfish crashed;
    trace_stockfish_crash2.py, 2026-11-17)."""
    b = board.copy()
    changed = False
    if b.turn != colour:
        b.turn = colour
        changed = True
        if b.en_passant != -1:
            b.en_passant = -1
    if changed:
        rehash(b)
    return b


def _after(board, move):
    c = board.copy()
    c.push(move)
    return c


def moves(board, colour, memo):
    """(the board with colour to move, its legal moves), memoized."""
    key = ("moves", board.zobrist_hash(), board.turn, colour)
    if key not in memo:
        b = turned(board, colour)
        kings = {board.colors[sq] for sq in range(len(board.pieces)) if board.pieces[sq] == KING}   # (read off the pieces: the Python
        if len(kings) < 2:        # board's own _king_sq can be stale after a king is taken; one search saw White's at 82 with none there)
            memo[key] = (b, [])   # a king taken: the game is over, so a line stops there (the user, 2026-11-13, "Stop at a king capture");
            return memo[key]      # the capture is read as a gain, nothing after it. First the search went on, and the Python board read a
            # kingless side's legality off wrapped-around squares
        memo[key] = (b, legal(b))
    return memo[key]


def press(board, colour, memo):
    """square -> the squares a colour's pieces press it from (warpworld.WarpWorld.pressure, on any board). Read by the Rust board
    (press_map, 2026-11-14: press_py's reading, which took most of a slice's time; check_rustboard.py checks they agree)."""
    key = ("press", board.zobrist_hash(), colour)
    if key not in memo:
        memo[key] = board.press_map(colour)
    return memo[key]


def press_py(board, colour, memo):
    """press, read in Python (as before the Rust board's press_map)."""
    key = ("press_py", board.zobrist_hash(), colour)
    if key in memo:
        return memo[key]
    b, ms = moves(board, colour, memo)
    out = {}
    for m in ms:
        kind = b.pieces[m.from_square]
        d_file, d_rank = abs(square_file(m.from_square) - square_file(m.to_square)), abs(square_rank(m.from_square) - square_rank(m.to_square))
        if kind == 1 and d_file == 0:
            continue
        if kind in (6, 7) and (d_file == 2 or d_rank == 2) and (d_file == 0 or d_rank == 0):
            continue
        out.setdefault(m.final_square, set()).add(m.from_square)
    memo[key] = out
    return out


def reach(board, me, memo):
    """Every square some move of mine (me to move) would leave pressed by me: what 'could press' reads, once per position. Read by
    the Rust board (reach, 2026-11-14; reach_py is the Python reading, check_rustboard.py checks they agree)."""
    key = ("reach", board.zobrist_hash(), me)
    if key not in memo:
        memo[key] = board.reach(me)
    return memo[key]


def reach_py(board, me, memo):
    """reach, read in Python (as before the Rust board's reach)."""
    key = ("reach_py", board.zobrist_hash(), me)
    if key not in memo:
        b, ms = moves(board, me, memo)
        out = set()
        for x in ms:
            out |= set(press_py(_after(b, x), me, memo))
        memo[key] = out
    return memo[key]


def pieces_of(board, colour):
    return {sq for sq in range(len(board.pieces)) if board.pieces[sq] and board.colors[sq] == colour}


def landed(before, after, colour):
    return {sq for sq in range(len(after.pieces)) if after.pieces[sq] and after.colors[sq] == colour
            and (before.pieces[sq], before.colors[sq]) != (after.pieces[sq], after.colors[sq])}


def leads(board, them, me, sq, memo):
    pt, pm = press(board, them, memo), press(board, me, memo)
    return len(pt.get(sq, ())) > len(pm.get(sq, ()))


def gains(before, after, them, me, memo):
    """What their move from `before` to `after` gained."""
    out = set()
    for t in pieces_of(before, me) - pieces_of(after, me):
        out.add(("piece", t))
    pm, pt = press(after, me, memo), press(after, them, memo)
    for s in landed(before, after, them):
        if s not in pm:
            out.add(("square", s))
            if s in pt or s not in reach(after, me, memo):
                out.add(("outpost", s))
    for s in pt:
        if len(pt[s]) > len(pm.get(s, ())) and not leads(before, them, me, s, memo):
            out.add(("square", s))
    return out


def one_move(board, them, me, memo):
    """{gain: [their moves that make it]} with them to move: every gain, memoized."""
    b, ms = moves(board, them, memo)
    key = ("one", b.zobrist_hash(), them)
    if key in memo:
        return memo[key]
    out = {}
    for m in ms:
        for g in gains(b, _after(b, m), them, me, memo):
            out.setdefault(g, []).append(m)
    memo[key] = out
    return out


def there(g, board, them, me, memo):
    """Whether gain g is there for them to make in one move (them to move): only the moves that could make it."""
    key = ("there", g, board.zobrist_hash(), them)
    if key in memo:
        return memo[key]
    kind, s = g
    b, ms = moves(board, them, memo)
    found = False
    if kind == "piece":
        if s in pieces_of(b, me):
            found = any(s in pieces_of(b, me) - pieces_of(_after(b, m), me) for m in ms if m.final_square in (s, flip_square(s))
                        or s in press(b, them, memo))
    else:
        for m in ms:
            if m.final_square not in (s, flip_square(s)):
                continue
            c = _after(b, m)
            if s in landed(b, c, them) and s not in press(c, me, memo):
                if kind == "square" or s in press(c, them, memo) or s not in reach(c, me, memo):
                    found = True
                    break
        if not found and kind == "square" and not leads(b, them, me, s, memo):
            for m in ms:   # (a lead on s: only a move that changes the pressure on s can make one; read after each, memoized)
                if leads(_after(b, m), them, me, s, memo):
                    found = True
                    break
    memo[key] = found
    return found


def touches(x, squares):
    return int(x.from_square in squares or x.final_square in squares or flip_square(x.final_square) in squares)


def no_reply(r_board, replies, me):
    """Chess (cognitivechess_v2/PLAN.md): with no legal reply of mine the game is over. Mated: their only gain is my king (the plan to
    checkmate, read as the king's capture, as a turned board allows). Stalemated: a draw, nothing gained. -> None while I have replies,
    else the gains still standing: {("piece", my king's square)} or set(). (In warpchess an empty reply list meant a king already taken.)"""
    if replies:
        return None
    king = next((sq for sq in range(len(r_board.pieces)) if r_board.pieces[sq] == KING and r_board.colors[sq] == me), None)
    if king is None or not r_board.is_in_check(me):
        return set()
    return {("piece", king)}


def two_move(board, them, me, memo, one):
    """{gain: a first move of theirs that forces it}: gains they make in two moves whatever I reply, not one-move plans."""
    b, firsts = moves(board, them, memo)
    out = {}
    for m1 in firsts:
        b1 = _after(b, m1)
        candidates = set(one_move(b1, them, me, memo)) - set(one) - set(out)   # what their second move would gain if I passed
        if not candidates:
            continue
        r_board, replies = moves(b1, me, memo)
        ended = no_reply(r_board, replies, me)
        if ended is not None:   # (chess: their first move ends the game; mate leaves only my king as their gain)
            candidates &= ended
        squares = {s for _, s in candidates}
        for r in sorted(replies, key=lambda x: -touches(x, squares)):
            if not candidates:
                break
            b2 = _after(r_board, r)
            candidates = {g for g in candidates if there(g, b2, them, me, memo)}
        for g in candidates:
            out[g] = m1
    return out


def plans(board, them, me, memo=None):
    """{gain: 1 or 2}: the opponent's plans now, one or two moves."""
    memo = {} if memo is None else memo
    one = one_move(board, them, me, memo)
    out = {g: 1 for g in one}
    for g in two_move(board, them, me, memo, one):
        out.setdefault(g, 2)
    return out


def still_plan(g, board, them, me, memo):
    """Whether g is a plan of theirs (one or two moves) on this board."""
    if there(g, board, them, me, memo):
        return True
    b, firsts = moves(board, them, memo)
    s = {g[1]}
    for m1 in firsts:
        b1 = _after(b, m1)
        if not there(g, b1, them, me, memo):
            continue
        r_board, replies = moves(b1, me, memo)
        ended = no_reply(r_board, replies, me)
        if ended is not None:   # (chess: mate stands only as the king's plan; stalemate ends it)
            if g in ended:
                return True
            continue
        if all(there(g, _after(r_board, r), them, me, memo) for r in sorted(replies, key=lambda x: -touches(x, s))):
            return True
    return False


def thwartable(g, board, them, me, memo):
    """A move of mine now (me to move) after which g is no plan of theirs; None if there's none."""
    b, mine_moves = moves(board, me, memo)
    for x in sorted(mine_moves, key=lambda x: -touches(x, {g[1]})):
        if not still_plan(g, _after(b, x), them, me, memo):
            return x
    return None


def held(board, them, me, memo=None):
    """{plan: (depth, a thwarting move or None)}: the opponent's plans and whether the mind can thwart each (held: it can)."""
    memo = {} if memo is None else memo
    return {g: (depth, thwartable(g, board, them, me, memo)) for g, depth in plans(board, them, me, memo).items()}


def lines(board, m1, them, me, memo):
    """A line from the board now (me to move), for the tool (PLAN.md step 4; the user, 2026-11-13: "have the mind make the decision" how
    far a line goes and what is forced; tool.py): after my move m1, for each reply of theirs, the moves of mine that would end one of
    their plans standing now. -> (their replies, {(m2, g): the replies after which m2 ends g}).
    The tool's heuristic, inside it (my reading): only plans standing now, and for each, only my second moves that touch its square
    (the order `thwartable` tries first); a line it doesn't find isn't told, and what it tells, play settles."""
    b0, _ = moves(board, me, memo)
    b1 = _after(b0, m1)
    now = set(one_move(board, them, me, memo))
    bt, replies = moves(b1, them, memo)
    out = {}
    for r in replies:
        b2 = _after(bt, r)
        bw, mine = moves(b2, me, memo)
        if not mine:
            continue
        for g in now:
            if not there(g, turned(b2, them), them, me, memo):
                continue   # (not standing after the reply)
            for m2 in mine:
                if touches(m2, {g[1]}) and not there(g, _after(bw, m2), them, me, memo):
                    out.setdefault((m2, g), set()).add(r)
    return len(replies), out


def plan_lines(board, g, them, me, memo):
    """Two-move ways to end one plan of theirs (the user, 2026-11-13: the tool answers the questions about the opponent's plans with
    lines): my move m1, each reply of theirs, my move m2 after which g is no plan. -> {m1: (their replies, {m2: the replies after which m2
    ends g})}. The tool's heuristic, inside it (my reading): first moves and second moves that touch g's square only; what it doesn't
    find isn't told."""
    b0, mine = moves(board, me, memo)
    out = {}
    for m1 in mine:
        if not touches(m1, {g[1]}):
            continue
        b1 = _after(b0, m1)
        bt, replies = moves(b1, them, memo)
        found = {}
        for r in replies:
            b2 = _after(bt, r)
            if not there(g, turned(b2, them), them, me, memo):
                continue   # (gone after the reply: nothing for m2 to end)
            bw, mine2 = moves(b2, me, memo)
            for m2 in mine2:
                if touches(m2, {g[1]}) and not there(g, _after(bw, m2), them, me, memo):
                    found.setdefault(m2, set()).add(r)
        if found:
            out[m1] = (len(replies), found)
    return out
