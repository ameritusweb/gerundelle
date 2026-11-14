"""The dream planner (LADDER.md, rung 4; the user, 2026-11-07). Between games, the mind dreams over the positions the game went through,
manipulating the force structure one force at a time, and checks itself: where what follows is not what it expected, it has found the
edge of its understanding.

- Forces, not pieces (the user: "the reason why you use forces, is because it's more generalizable than pieces"). A manipulation adds
  or takes away one potential force onto the square the mind's move went to. A force has a kind: diagonal, line, jump, forward
  (a pawn's diagonal take). A carrier is placed only because the world needs one: the piece whose own force is that kind (a bishop
  carries a diagonal, a rook a line, a knight a jump, a pawn a forward take).
- The world as teacher: only configurations the world says are valid (both kings on the board; the side not to move not in check).
- What follows: the mind's move, then the opponent's reply as the mind would make it in their shoes (shoes.py), read as forces.
- How well it understands the dreamed situation: a copy of the mind takes a real tick with the dream as its percepts (perceive,
  think), and the concepts it attends to whose structure is still open are the edge; there the dream manipulates one force further.
  What the dream shows stays in the mind's SOV as imagined structure (Understanding.add_imagined), funding nothing (the firewall: it
  says imagined evidence doesn't fund, not that a dream leaves no structure); the copy's own tick is thrown away. (Before: a comparison beside the mind, then the watch's per-change test, then a
  pool I built by hand with winners filtered by my own prefixes: shortcuts, each; the user had said to look at the thought molecules
  and the SOV.)
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
        if self.board.turn == WHITE and not self.__dict__.get("dreaming") and not self.__dict__.get("imagining"):   # (an imagined move,
            # Imagines, is no position of the game: first imagining every untried move recorded each as one, 2026-11-13)
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


def dreaming_mind(mind):
    """A copy of the mind, to read its attention to a dream: a real tick would take the dream's percepts as lived (the firewall). The
    copy's own tick is thrown away; what the dream shows is kept in the mind itself as imagined structure (dream()). The register
    holds two small functions pickle can't carry; they are set aside and put back, as worldbuilding/play/match.py's freeze does."""
    import pickle
    und = mind.understanding
    names = [k for k in ("kind", "owner", "lien_holds") if k in und.__dict__]   # the functions the register holds (carry.py adds lien_holds)
    held = {k: und.__dict__[k] for k in names}
    snap = mind.__dict__.get("_dream_snapshot")   # (an exact speed-up, 2026-11-13: the mind pickled once per dream, not once per trial;
    if snap is None:                              # a dream changes nothing a tick reads but the imagined register, given to each copy as it
        for k in names:                           # stands. py-spy: pickling and unpickling the mind for each trial was 44% of a dream)
            und.__dict__[k] = None
        try:
            snap = pickle.dumps(mind, protocol=4)
        finally:
            und.__dict__.update(held)
    copy = pickle.loads(snap)
    copy.understanding.__dict__.update(held)
    if "imagined" in und.__dict__:
        copy.understanding.__dict__["imagined"] = {c: dict(v) for c, v in und.imagined.items()}
    return copy


def snapshot(mind):
    """The mind pickled once, for a dream's copies (dreaming_mind); its imagined register is given to each copy as it stands."""
    import pickle
    und = mind.understanding
    names = [k for k in ("kind", "owner", "lien_holds") if k in und.__dict__]
    held = {k: und.__dict__[k] for k in names}
    for k in names:
        und.__dict__[k] = None
    try:
        return pickle.dumps(mind, protocol=4)
    finally:
        und.__dict__.update(held)


def understanding_of(agent, inv, names, states):
    """How well the mind understands a dreamed situation (the user: "see how well you understand that position after manipulation, by
    looking at your thought molecules and SOV"). A copy of the mind takes a real tick with the dream as its percepts: the facts
    register is the dreamed board, the news is each change that came, and the move is offered (as SovAgent.perceive presents them);
    it perceives and thinks as the mind does. -> the concepts the copy attended to (its top level) whose structure in the mind's SOV is
    still open, counting what dreams have given it as structure (Understanding.open_structure): the edge. Empty: understood. (First the
    SOV's funded level, which a dream can never raise: the dream stuck on one move for all its trials.)"""
    from molecules import clause
    copy = dreaming_mind(agent.mind)
    move = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
    copy.facts = {o: clause(f"{o}_{st.replace(' ', '_')}") for o, st in states.items()}
    news = [clause(e) for e in sorted(names)]
    offers = [clause(move, tags=("invitation", inv[1]))]
    rec = copy.tick(news + offers)
    concepts = set(names) | {move}
    attended = {c for c in concepts for w in rec["levels"][-1]["winners"] if c in w}
    und = agent.mind.understanding   # the mind's own SOV, with what its dreams have given it as structure
    return sorted(c for c in attended if und.open_structure(c))


def dream(agent, rng=None, focus=None, budget=None):
    """Dream over the last game's positions; returns (trials, trials at the edge). Starting from the game's own configurations one force
    away, a configuration the mind's tournament reads as at the edge is manipulated one force further; an understood one isn't.
    focus: [(board, where, the move's label, its mover)] to dream from instead (the user, 2026-11-13: when the mind is stuck on something
    not on offer it dreams at once, the game waiting: the position where that move was on offer, with that move).
    In waves (agent.dream_workers set; the user, 2026-11-13: "why not just do all trials in parallel?", "Yes, waves"): as many trials as
    there are workers are made in order (the move, the reply, what it came to, its imagined structure), then their understanding is read
    at once in worker processes (dream_worker.py: each copy given the imagined register as it stood after its own trial's writes), then
    applied in order: what is at the edge is manipulated further. With no workers a wave is one trial: the dream as before.
    budget: trials at most (default DREAM_TRIALS; the user, 2026-11-13: 50 for a dream in the middle of a game)."""
    budget = DREAM_TRIALS if budget is None else budget
    world = agent.world
    positions = focus if focus is not None else world.__dict__.get("last_game", [])
    if not positions:
        return 0, 0
    pairs = agent.__dict__.setdefault("dream_pairs", [])
    terr = agent.mind.territory
    saved = (world.board, dict(world.where), dict(getattr(world, "captured_by", {})), world.__dict__.get("_imagined"))
    trials = edges = 0
    world.__dict__["dreaming"] = True
    snap = snapshot(agent.mind)
    agent.mind.__dict__["_dream_snapshot"] = snap
    workers = agent.__dict__.get("dream_workers") or 0
    pool = None
    timing = agent.__dict__.setdefault("dream_timing", [])   # (for traces: the pool's start, and each wave's preparing and reading, s)
    import time as time_
    t_pool = time_.perf_counter()
    if workers:
        import multiprocessing
        import dream_worker
        pool = multiprocessing.get_context("spawn").Pool(workers, initializer=dream_worker.init,
                                                         initargs=(snap, getattr(world, "role_of", None)))
    timing.append(dict(pool=round(time_.perf_counter() - t_pool, 2), snapshot_mb=round(len(snap) / 1e6, 1), waves=[]))
    und = agent.mind.understanding   # the dream's structure stays in the mind, marked imagined, funding nothing (the firewall)
    frontier = []
    writes = []   # (with workers) the imagined writes since the dream began, in order: replayed on the snapshot's register, they give
    #               each worker's copy the register as it stood at its trial (first the whole register was copied for every trial and
    #               sent with it: 66-114 s of a dream's preparing, against 11 s for reading all its trials' understanding in parallel)

    def imagine(c, rel, other):
        und.add_imagined(c, rel, other)
        if pool is not None:
            writes.append((c, rel, other))

    def prepare(item):
        """One trial up to its understanding: the move, the reply in their shoes, what it came to, the imagined structure, the force
        structure kept and the dreamed states. -> what applying its understanding needs, or None if the move isn't there."""
        (board, where, force), label, mover, base = item
        world.board, world.where = board.copy(), dict(where)
        rehash(world.board)
        world.__dict__.pop("_imagined", None)
        move = next((m for m in world.board.legal_moves if world.label(m) == label), None)
        if move is None or where.get(mover) != move.from_square:
            return None
        tm = timing[-1].setdefault("prep", {"read": 0.0, "shoes": 0.0, "misses": 0, "manip": 0.0})   # (for traces)
        misses0 = len(getattr(world, "_plan_read", {}))
        t_ = time_.perf_counter()
        before = world.read()
        facts = frozenset(f"{o}_{st}" for o, st in before.items())
        inv = (label, mover, "present")
        world.play(move)
        mid = world.read()
        tm["read"] += time_.perf_counter() - t_
        t_ = time_.perf_counter()
        reply = world.in_their_shoes(world) if getattr(world, "in_their_shoes", None) else None
        tm["shoes"] += time_.perf_counter() - t_
        if reply is not None:
            world.play(reply)
        t_ = time_.perf_counter()
        after = world.read()
        tm["read"] += time_.perf_counter() - t_
        tm["misses"] += len(getattr(world, "_plan_read", {})) - misses0
        names = frozenset(f"{o}_{st}" for o, st in after.items() if st != before.get(o))
        agent.dreamed.append((inv, facts, names))
        move_id = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
        for e in names:
            imagine(move_id, "causes", e)
            imagine(e, "caused_by", move_id)
        for e in {f"{o}_{st}" for o, st in mid.items() if st != before.get(o)}:   # in the move's own slice
            imagine(move_id, "co_occurs", e)
        if force is not None and base is not None and names != base:   # one force changed what follows: it conditions the move
            imagine(force, "conditions", move_id)
            imagine(move_id, "conditioned_by", force)
        if force is None:   # the baseline: the position one force away is what the dream tries next
            t_ = time_.perf_counter()
            frontier[:0] = [((b, w2, f), label, mover, names) for b, w2, f in manipulations(world, board, where, label)]
            tm["manip"] += time_.perf_counter() - t_
        first = start_of({f"{o}_{st}" for o, st in mid.items() if st != before.get(o)}, mover)
        rest = frozenset((o, st) for o, st in after.items() if st != mid.get(o) and (o in SHARED or not o.startswith("file_")))
        counts = agent.__dict__.setdefault("dream_counts", {})   # why a trial kept no force structure, for traces
        for k, v in (("no reply", reply is None), ("no start", not first), ("no rest", not rest), ("kept", bool(first and rest))):
            if v:
                counts[k] = counts.get(k, 0) + 1
        if first and rest:
            pairs.append((("dream", label, len(pairs)), mover, first, rest))
        for o, st in after.items():   # dreams shape wants: a state dreamed on one of the mind's regions is offered to its slot
            if st != before.get(o) and o in terr.rows:
                terr.rows[o].setdefault("dreamed_states", set()).add(f"{o}_{st}")
        imagined = len(writes) if pool is not None else None   # (how many of the writes this trial's copy has seen)
        return dict(board=board, where=where, force=force, label=label, mover=mover, base=base, inv=inv, facts=facts, names=names,
                    after=after, imagined=imagined)

    try:
        for board, where, label, mover in positions:   # each position as it was first (the baseline), then one force away
            frontier.append(((board, where, None), label, mover, None))
        while frontier and trials < budget:
            wave = []
            t_w = time_.perf_counter()
            while frontier and len(wave) < max(1, workers) and trials < budget:
                rec = prepare(frontier.pop(0))
                if rec is None:
                    continue
                trials += 1
                wave.append(rec)
                if pool is None:
                    break   # (one at a time: its understanding is read before the next trial's imagined writes, as before)
            if not wave:
                continue
            t_p = time_.perf_counter()
            if pool is not None:
                import dream_worker
                found = pool.map(dream_worker.understanding, [(writes[:r["imagined"]], r["inv"], r["names"], r["after"]) for r in wave])
            else:
                found = [understanding_of(agent, r["inv"], r["names"], r["after"]) for r in wave]
            timing[-1]["waves"].append((len(wave), round(t_p - t_w, 2), round(time_.perf_counter() - t_p, 2)))
            for r, edge in zip(wave, found):   # applied in order
                agent.__dict__.setdefault("dream_edges", []).append((r["inv"], r["facts"], r["names"], edge))
                if edge:   # at the edge of its understanding: manipulate further there (the user: "keep improving your understanding
                    edges += 1   # if it is lacking"); understood: leave it
                    if r["force"] is not None:
                        frontier[:0] = [((b, w2, f), r["label"], r["mover"], r["base"])
                                        for b, w2, f in manipulations(world, r["board"], r["where"], r["label"])]   # followed first
    finally:
        if pool is not None:
            pool.close()
            pool.join()
        agent.mind.__dict__.pop("_dream_snapshot", None)
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
                    out.append((b, w2, f"force:{o}@{target}:taken"))
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
                        base_name = f"{'white' if colour else 'black'}_{force}_dream"   # named by the force it carries, not its square,
                        name = base_name                                               # so what one dream learns of it carries to the next
                        while name in w2:
                            name = f"{base_name}{sum(1 for k in w2 if k.startswith(base_name)) + 1}"
                        w2[name] = sq
                        out.append((b, w2, f"force:{'white' if colour else 'black'}_{force}@{target}:added"))
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
        got = agent.world.imagined_start([inv[0]])
        if not got:
            continue
        start = start_of(got, inv[1])   # the move's own changes, before the reply, as a dream pair's start is read
        if not start:
            continue
        counts = agent.__dict__.setdefault("wake_counts", {})   # what waking found, for traces
        for src, mover, first, rest in pairs:
            phi = fit(first, start, mover, inv[1])
            if phi is None:
                continue
            counts["fitted"] = counts.get("fitted", 0) + 1
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
                und = agent.mind.understanding   # and its structure in the SOV, marked imagined (as the dream's own), funding nothing:
                pattern = f"dream:{src[1]}#{src[2]}"   # Abstract then Constrain: the pattern it fitted conditions it, and it causes
                und.add_imagined(c, "conditioned_by", pattern)   # what followed in the dream, carried under the mapping (first only
                und.add_imagined(pattern, "conditions", c)       # the register had it, an omission: the planner sent the move to the
                for e in names:                                  # board as if nothing were known of it)
                    und.add_imagined(c, "causes", e)
                    und.add_imagined(e, "caused_by", c)
            else:
                counts["fitted, nothing carried"] = counts.get("fitted, nothing carried", 0) + 1
                ex = counts.setdefault("examples", [])
                if len(ex) < 4:
                    ex.append((sorted(phi), sorted(o for o, _ in rest)[:6]))
    return n
