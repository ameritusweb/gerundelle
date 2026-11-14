"""The dream planner (LADDER.md, rung 4; the user, 2026-11-07). Between games, the mind dreams over the positions the game went through,
manipulating the force structure one force at a time, and checks itself: where what follows is not what it expected, it has found the
edge of its understanding.

- Forces, not pieces (the user: "the reason why you use forces, is because it's more generalizable than pieces"). A manipulation adds
  or takes away one potential force onto the square the mind's move went to. A force has a kind: diagonal, line, jump, forward
  (a pawn's diagonal take). A carrier is placed only because the world needs one: the piece whose own force is that kind (a bishop
  carries a diagonal, a rook a line, a knight a jump, a pawn a forward take).
- The world as teacher: only configurations the world says are valid (both kings on the board; the side not to move not in check).
- What follows: the mind's move, then the opponent's reply as the mind would make it in their shoes (shoes.py), read as forces.
- How well it understands the dreamed situation is read from its own tournament (the user): what came is presented to it as imagined
  percepts, and where questions, SOV pulls, experiments or meta molecules about those concepts win, it is at the edge; there the
  dream manipulates one force further. (First a comparison beside the mind, my own, then the watch's per-change test: neither read
  the thought molecules, as the user had said.)
- Kept as force structure (a dream pair: the start, what changed on every piece's readings when the move was made, and the rest,
  what the reply did to the pieces and the shared objects), so a dream fits any situation with the same force structure
  (carry.py's fit): on waking, a move whose start fits a dream pair gets that dream as imagined experience (SovAgent.dreamed),
  which the planner and the sub-wants read where nothing was lived. It funds nothing (the firewall).
- Dreams shape wants (the user: "our dreams shape our wants ... this becomes a want even if it is just an imagined future"): a state
  a dream showed on one of the mind's regions is offered to that region's ownership slot as a candidate want (own_candidates reads
  the region's dreamed states with its perceived ones).
- At most DREAM_TRIALS trials a dream (a compute budget, stated to the user, not a rule about what to try).
"""
from carry import SHARED, start_of
from pairs3 import entity
from warpworld import BLACK, NAMES, TOTAL_SQUARES, WHITE, rehash, square_side

DREAM_TRIALS = 200
FORCES = {"diagonal": 3, "line": 4, "jump": 2, "forward": 1}   # a kind of force -> the piece whose own force it is (its carrier)


class Remembers:
    """A mixin for the game world: the positions where White moved this game (board, where, the move's label, its mover)."""

    def play(self, move):
        if self.board.turn == WHITE and not self.__dict__.get("dreaming"):
            self.__dict__.setdefault("game_positions", []).append((self.board.copy(), dict(self.where), self.label(move), self.ids_at(move.from_square)))
        return super().play(move)

    def reset(self):
        self.__dict__["last_game"] = self.__dict__.get("game_positions", [])
        self.__dict__["game_positions"] = []
        super().reset()


def bears_on(world, sq, target):
    """Whether the piece on sq puts a force on the square target (it could take there, as the world's pressure reads it)."""
    return sq in world.pressure(world.board.colors[sq]).get(target, set())


def valid(board):
    """The world as teacher: both kings on the board, and the side not to move not in check."""
    return board._king_sq[WHITE] >= 0 and board._king_sq[BLACK] >= 0 and not board.is_in_check(not board.turn)


def understanding_of(agent, inv, names):
    """How the mind's own tournament reads a dreamed situation (the user: "see how well you understand that position after
    manipulation, by looking at your thought molecules and SOV"): what came (each change) and the move are presented to it as imagined
    percepts, its tournament runs (Mind.imagined_winners: think()'s own levels; nothing kept, the firewall), and what wins is read.
    -> the top-level winners that are open structure about these concepts (a question, an SOV still pulling, an experiment, a meta
    molecule about them): the edge. Empty: only knowns won, the situation is understood."""
    from molecules import clause
    mind = agent.mind
    move = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
    concepts = set(names) | {move}
    pool = {i: m for i, m in mind.pool.items() if "invitation" not in m.tags}
    for c in concepts:
        pool[c] = mind.pool[c] if c in mind.pool else clause(c, tags=(("invitation", inv[1]) if c == move else ()))
    won = mind.imagined_winners(pool, set(concepts))
    about = lambda w: any(c in w for c in concepts)
    return [w for w in won if w.startswith(("q:", "sov:", "exp:", "meta:")) and about(w)]


def dream(agent, rng=None):
    """Dream over the last game's positions; returns (trials, trials at the edge). Starting from the game's own configurations one force
    away, a configuration the mind's tournament reads as at the edge is manipulated one force further; an understood one isn't."""
    world = agent.world
    positions = world.__dict__.get("last_game", [])
    if not positions:
        return 0, 0
    pairs = agent.__dict__.setdefault("dream_pairs", [])
    terr = agent.mind.territory
    saved = (world.board, dict(world.where), dict(getattr(world, "captured_by", {})), world.__dict__.get("_imagined"))
    trials = edges = 0
    world.__dict__["dreaming"] = True
    try:
        frontier = [(cfg, label, mover) for board, where, label, mover in positions for cfg in manipulations(world, board, where, label)]
        while frontier and trials < DREAM_TRIALS:
            (board, where), label, mover = frontier.pop(0)
            world.board, world.where = board.copy(), dict(where)
            rehash(world.board)
            world.__dict__.pop("_imagined", None)
            move = next((m for m in world.board.legal_moves if world.label(m) == label), None)
            if move is None or where.get(mover) != move.from_square:
                continue
            before = world.read()
            facts = frozenset(f"{o}_{st}" for o, st in before.items())
            inv = (label, mover, "present")
            world.play(move)
            mid = world.read()
            reply = world.in_their_shoes(world) if getattr(world, "in_their_shoes", None) else None
            if reply is not None:
                world.play(reply)
            after = world.read()
            names = frozenset(f"{o}_{st}" for o, st in after.items() if st != before.get(o))
            agent.dreamed.append((inv, facts, names))
            trials += 1
            edge = understanding_of(agent, inv, names)
            agent.__dict__.setdefault("dream_edges", []).append((inv, facts, names, edge))
            if edge:   # at the edge of its understanding: manipulate further there (the user: "keep improving your understanding if it
                edges += 1   # is lacking"); understood: leave it
                frontier[:0] = [(cfg, label, mover) for cfg in manipulations(world, board, where, label)]   # followed first (depth first)
            first = start_of({f"{o}_{st}" for o, st in mid.items() if st != before.get(o)}, mover)
            rest = frozenset((o, st) for o, st in after.items() if st != mid.get(o) and (o in SHARED or not o.startswith("file_")))
            if first and rest:
                pairs.append((("dream", label, len(pairs)), mover, first, rest))
            for o, st in after.items():   # dreams shape wants: a state dreamed on one of the mind's regions is offered to its slot
                if st != before.get(o) and o in terr.rows:
                    terr.rows[o].setdefault("dreamed_states", set()).add(f"{o}_{st}")
    finally:
        world.__dict__["dreaming"] = False
        world.board, world.where = saved[0], saved[1]
        if hasattr(world, "captured_by"):
            world.captured_by = saved[2]
        world.__dict__["_imagined"] = saved[3] or {}
    return trials, edges


def manipulations(world, board, where, label):
    """The valid configurations one potential force away on the square the move went to: (board, where) pairs. Taken away: a piece
    whose force bears on it (not a king). Added: for each kind of force and each side, a carrier on an empty square of that board from
    which it bears on it."""
    keep = (world.board, world.where)
    out = []
    try:
        world.board, world.where = board.copy(), dict(where)
        rehash(world.board)
        move = next((m for m in world.board.legal_moves if world.label(m) == label), None)
        if move is None:
            return out
        target = move.final_square
        for o, sq in where.items():
            if sq is None or sq == move.from_square or NAMES.get(board.pieces[sq]) == "king":
                continue
            if bears_on(world, sq, target):
                b = board.copy()
                b.pieces[sq], b.colors[sq] = 0, None
                rehash(b)
                if valid(b):
                    w2 = dict(where)
                    w2[o] = None
                    out.append((b, w2))
        side = square_side(target)
        for sq in range(TOTAL_SQUARES):
            if board.pieces[sq] or square_side(sq) != side:
                continue
            for colour in (WHITE, BLACK):
                for force, carrier in FORCES.items():
                    b = board.copy()
                    b.set_piece_at(sq, carrier, colour)
                    rehash(b)
                    world.board = b
                    if valid(b) and bears_on(world, sq, target):
                        w2 = dict(where)
                        w2[f"{'white' if colour else 'black'}_{force}_dream{sq}"] = sq
                        out.append((b, w2))
                    world.board = board.copy()
    finally:
        world.board, world.where = keep
    return out


def wake(agent, invs):
    """On waking: a move on offer the mind has never made, whose imagined start fits a dream pair (carry.py's fit), gets that dream's
    rest, under the fit's mapping, as imagined experience in this situation (SovAgent.dreamed). Nothing is written to the SOV."""
    from carry import fit, inv_id_of
    pairs = agent.__dict__.get("dream_pairs", [])
    if not pairs or not hasattr(agent.world, "imagine"):
        return 0
    tried = {inv_id_of(i) for i, _, _ in agent.pushed}
    now = agent.facts_now()
    n = 0
    for c, inv in invs.items():
        if c in tried:
            continue
        got = agent.world.imagine([inv[0]])
        if not got:
            continue
        start = start_of(got[1], inv[1])
        if not start:
            continue
        for src, mover, first, rest in pairs:
            phi = fit(first, start, mover, inv[1])
            if phi is None:
                continue
            names = set()
            for obj, st in rest:
                e, ch = entity(obj)
                if obj in SHARED:
                    names.add(f"{obj}_{st}")
                elif e in phi:
                    names.add(f"{phi[e]}{ch}_{st}")
            if names:
                agent.dreamed.append((inv, now, frozenset(names)))
                n += 1
    return n
