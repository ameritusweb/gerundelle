"""The Warp world with the opponent's plans as the mind's territory (PLAN.md step 2; the user, 2026-11-13: territory is "being able to
'thwart' the hypothetical plans of the opponent"; "a plan is a gain of a piece, a square, or an outpost").

The mind plays White; the opponent's plans are Black's (plans.py). Each plan has an object, by kind and square: plan_piece_<sq>,
plan_square_<sq>, plan_outpost_<sq>, 3 x 64 (chess; 3 x 112 in warpchess). A plan on the mind's king is the plan to checkmate it
(cognitivechess_v2/PLAN.md). Its doing, read each time the board changes (memoized by position):
  stoppable    a gain one of Black's moves would make now, and the mind has a move after which it is no longer there (one move: the
               two-move reading is the tool's, PLAN.md "Tool use", and too slow for every slice: check_plans.py)
  unstoppable  a gain one of Black's moves would make now that no move of the mind's stops
  none         no gain there for Black now
Territory (give), three levels (the user, 2026-11-13): no plan there, held; a plan the mind can stop, contested; one it can't, lost.
Held by reading only (read_held). Potential effects (push_predictions, PLAN.md step 3): what each move on offer would do to the plans. The pieces and files are no one's to claim (unclaimable), as Go's stones are once territory moved off them; `material` is left
claimable (a placed want, rung 1's, is about it).
"""
import plans
from rustboard import TOTAL_SQUARES, square_name, square_rank
from warpworld import WarpWorld

KINDS = ("piece", "square", "outpost")
WHITE, BLACK = True, False


SQUARES = list(range(TOTAL_SQUARES))   # (chess: all 64 squares; warpchess listed the 112 real squares of two 7-rank boards)


def plan_obj(kind, sq):
    return f"plan_{kind}_{square_name(sq)}"


# Stalemate, an opponent plan (cognitivechess_v2; the user, 2026-11-17: "stalemate is an opponent plan", "only stalemate"): a draw that
# turns the opponent's loss into their gain. The mind's own move makes it (leaving them no legal move while not in check), so its doing is
# read off the mind's moves: none (no move of mine stalemates them), stoppable (some do, some don't), unstoppable (every move does), made
# (the board is stalemate). Territory as the other plans: held at none, contested at stoppable, lost at unstoppable or made (give).
STALEMATE = "plan_stalemate"


def stalemates(after, them=BLACK):
    """Whether the board, them to move, is stalemate: no legal move, not in check (the mind's move left it so)."""
    return not after.legal_moves and not after.is_in_check(them)


def stalemate_doing(board, memo, me=WHITE):
    """plan_stalemate's doing on this board: made if it is stalemate with them to move; else read off my moves (me to move, as the
    opponent's plans are read off their turned board)."""
    them = not me
    if board.turn == them and stalemates(board, them):
        return "made"
    b, mine = plans.moves(board, me, memo)
    if not mine:
        return "none"
    n = sum(1 for x in mine if stalemates(plans._after(b, x), them))
    return "none" if n == 0 else ("unstoppable" if n == len(mine) else "stoppable")


# Coverage (cognitivechess_v2; the user, 2026-11-17: impossible_demands.md; "option A please"; piece plans only): plans of the opponent's that the mind can
# stop one at a time but not together, since it has one move. A plan is stoppable when some move of the mind's ends it; a set of
# stoppable plans is uncovered when no single move ends them all ("logical defeat precedes material defeat": one of them falls, the
# opponent's choice). Each smallest uncovered set is a region of its own, named by its member plans, cover_<plan>_and_<plan>[...]:
#   none       not all its members stand as stoppable plans now
#   covered    they all stand, and one move of the mind's ends them all
#   uncovered  they all stand, and no move of the mind's ends them all
# Territory as the plans': held at none, contested at covered, lost at uncovered (give). The members keep their own readings
# (each still stoppable, contested); the set's loss is what they can't say alone. My readings, for the user to change: sets of two
# and three plans (an uncovered four would need every three of it covered: not read); a set is named the first time it is uncovered
# on the game's board (not in a dream), and read from then on.
COVER = "cover_"


def cover_obj(members):
    return COVER + "_and_".join(sorted(plan_obj(*g) for g in members))


COVER_KINDS = ("piece",)   # (the user, 2026-11-17: "Piece plans only": the plans to win a piece, the king's included; square and
#   outpost plans keep their own readings. First all kinds: a small fork position had 21 square plans and hundreds of sets of them)


def coverage(board, memo, me, them):
    """-> (the opponent's stoppable one-move piece plans, {my move: the plans it ends}) on a board (whoever is to move: read as
    read_plans reads, the plans theirs as if they moved, the stops mine as if I did)."""
    one = [g for g in plans.one_move(board, them, me, memo) if g[0] in COVER_KINDS]
    if len(one) < 2:
        return frozenset(one), {}
    b, mine = plans.moves(board, me, memo)
    stops = {x: frozenset(g for g in one if not plans.there(g, plans._after(b, x), them, me, memo)) for x in mine}
    stoppable = frozenset(g for g in one if any(g in s for s in stops.values()))
    return stoppable, stops


def uncovered_sets(stoppable, stops):
    """The smallest sets (two or three plans) of stoppable plans no single move ends together."""
    from itertools import combinations
    ends = list(stops.values())

    def covered(t):
        return any(t <= s for s in ends)

    s = sorted(stoppable)
    pairs = [frozenset(p) for p in combinations(s, 2) if not covered(frozenset(p))]
    triples = [frozenset(t) for t in combinations(s, 3)
               if not covered(frozenset(t)) and all(covered(frozenset(p)) for p in combinations(t, 2))]
    return pairs + triples


def cover_doing(members, stoppable, stops):
    if not members <= stoppable:
        return "none"
    return "covered" if any(members <= s for s in stops.values()) else "uncovered"


def seat(world):
    """(me, them): the seat's colours (GameWorld.me; White for a world with no seat)."""
    me = getattr(world, "me", WHITE)
    return me, not me


class PlansWorld(WarpWorld):
    unclaimable = ("white_", "black_", "file_", "standing_", "outcome_")   # (cognitivechess_v2: standing_ and outcome_ are held only by
    #   reading, forever once reached: give, HELD_FOREVER)
    read_held = ("plan_", COVER)
    covers_read = False   # (coverage: off unless a world turns it on, so the league running on this code is unchanged)

    def read_covers(self):
        """cover object -> its doing on the board as it stands: every set named so far, and any uncovered set found now (named here,
        on the game's board only: a dream's or imagining's board names none)."""
        me, them = seat(self)
        key = ("covers", self.board.zobrist_hash())
        memo = self._plan_memo
        if key not in memo:
            memo[key] = coverage(self.board, memo, me, them)
        stoppable, stops = memo[key]
        named = self.__dict__.setdefault("_cover_sets", {})
        if not self.__dict__.get("dreaming") and not self.__dict__.get("imagining"):
            for t in uncovered_sets(stoppable, stops):
                named.setdefault(cover_obj(t), t)
            if self.board.turn == me:   # the sets a move on offer would uncover, named as the board is read, so they are shown and held
                b, mine = plans.moves(self.board, me, memo)   # before the mind's slice (first named only by the predictions, inside
                for x in mine:                                 # the slice: a walk-in wasn't a loss the slice it was first seen, and a
                    after = plans._after(b, x)                 # mind that moved then never read it as one; check_cover_room.py)
                    k = ("covers", after.zobrist_hash())
                    if k not in memo:
                        memo[k] = coverage(after, memo, me, them)
                    for t in uncovered_sets(*memo[k]):
                        named.setdefault(cover_obj(t), t)
        return {o: cover_doing(t, stoppable, stops) for o, t in named.items()}

    def cover_effects(self, b, move, land, push, now, stoppable_now, stops_now):
        """What a move would do to coverage, as the world will show it a slice after (the plan effects' timing, 2): sets named now that
        it changes, and uncovered sets it would make. Force structure, relative to the move: each member plan converging on the set
        (member+<kind>@<distance from where the piece lands>, the members' identities), and p0 if the piece moved answered a member
        before the move (a defender drawn off) or answers one after it."""
        from rustboard import square_file, square_rank, square_side
        me, them = seat(self)
        memo = self._plan_memo
        key = ("covers", b.zobrist_hash())
        if key not in memo:
            memo[key] = coverage(b, memo, me, them)
        stoppable, stops = memo[key]
        named = self.__dict__.setdefault("_cover_sets", {})
        after = {o: cover_doing(t, stoppable, stops) for o, t in named.items()}
        for t in uncovered_sets(stoppable, stops):
            after.setdefault(cover_obj(t), "uncovered")
        sets = dict(named)
        sets.update({cover_obj(t): t for t in uncovered_sets(stoppable, stops)})
        if not self.__dict__.get("dreaming") and not self.__dict__.get("imagining"):
            # a set a move on offer would uncover is named now, held while none (give), as every plan region is from the start: else
            # walking into a new fork predicted the loss of a region not yet the mind's, which is no loss
            for o, t in sets.items():
                named.setdefault(o, t)
        out = []
        for o, new in after.items():
            if now.get(o, "none") == new:
                continue
            members = sets[o]
            forces = set()
            for kind, sq in members:
                d = (max(abs(square_file(sq) - square_file(land)), abs(square_rank(sq) - square_rank(land)))
                     if square_side(sq) == square_side(land) else "x")
                forces.add((f"member+{kind}@{d}", "cover"))
            answered_before = any(x.from_square == move.from_square and (s & members) for x, s in stops_now.items())
            answers_after = any(x.from_square == land and (s & members) for x, s in stops.items())
            if answered_before or answers_after:
                forces.add(("p0", "cover"))
            out.append((f"{o}_{new}", 2, frozenset(forces), f"cover+{len(members)}_{new}", (push,)))
        return out

    def __init__(self, fen, **kw):
        self._plan_memo = {}
        self._plan_read = {}
        kw["forces"] = True
        super().__init__(fen, **kw)
        self.objs.update({plan_obj(k, sq): None for k in KINDS for sq in SQUARES})
        self.objs[STALEMATE] = None

    def read_plans(self):
        """plan object -> its doing, for the board as it stands (memoized by position)."""
        key = self.board.zobrist_hash()
        if key in self._plan_read:
            return self._plan_read[key]
        if len(self._plan_memo) > 200_000:   # (a bound on memory: the memo is a cache, cleared when large)
            self._plan_memo.clear()
        memo = self._plan_memo
        me, them = seat(self)
        one = plans.one_move(self.board, them, me, memo)
        out = {}
        if one:
            b, mine_moves = plans.moves(self.board, me, memo)
            for g in one:
                squares = {g[1]}
                stop = any(not plans.there(g, plans._after(b, x), them, me, memo)
                           for x in sorted(mine_moves, key=lambda x: -plans.touches(x, squares)))
                out[plan_obj(*g)] = "stoppable" if stop else "unstoppable"
        st = stalemate_doing(self.board, memo, me)
        if st != "none":
            out[STALEMATE] = st
        self._plan_read[key] = out
        return out

    def push_predictions(self):
        """What each move on offer would do to the opponent's plans (PLAN.md step 3; the user, 2026-11-13: ending a plan or stopping one
        is a gain, a new plan or one made unstoppable a loss; which is which the mind's register reads). For each move: the plans it
        ends (no longer a one-move plan after it) and the plans it creates (stoppable or not, read afresh); each as the world will show
        it a slice after the move (the move's slice changes only the
        piece moved: principle 0). Read relative to the move: the plan's kind, how far its square is from where the piece lands (steps
        on the same board, "x" across), and what presses the square after the move (`p0` the piece moved, `mine` the mind's others,
        `theirs` the opponent's). Whether a plan already there becomes stoppable is not predicted here: it is the tool's (tool.MindTool
        stands its answers as predictions). Checked by check_plans_effects.py. -> [(effect, 2, force structure, relative effect, (the move's push id,))]."""
        from rustboard import square_file, square_rank, square_side
        invs = self.invitations()
        if not invs:
            return []
        memo = self._plan_memo
        me, them = seat(self)
        now = self.read_plans()   # plan object -> stoppable / unstoppable
        current = {g: now[plan_obj(*g)] for g in ((k, sq) for k in KINDS for sq in SQUARES) if plan_obj(*g) in now}
        out = []
        if self.covers_read:   # (coverage now: the sets named and their doings, and which of my moves end which plans)
            covers_now = self.read_covers()
            stoppable_now, stops_now = memo[("covers", self.board.zobrist_hash())]
        for inv in invs:
            move = self.offers().get(inv[0])
            if move is None:
                continue
            b = plans._after(plans.turned(self.board, me), move)
            one_after = plans.one_move(b, them, me, memo)
            touched = {move.from_square, move.final_square}
            land = move.final_square
            pm, pt = plans.press(b, me, memo), plans.press(b, them, memo)
            changes = {}
            for g, doing in current.items():   # the plans it ends
                if g not in one_after:
                    changes[g] = "none"
            for g in set(one_after) - set(current):   # the plans it creates, each read afresh: stoppable or not
                changes[g] = self._stop_doing(g, b, memo)
            # (whether a plan already there becomes stoppable or not is the tool's to answer: the user, 2026-11-13, "Stoppability as
            # the tool's prediction"; first re-read for the plans the move touched, 12 s a slice and 60 changes missed in 16 moves,
            # check_plans_effects.py: a rook flipped across makes plans far from its squares stoppable)
            push = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
            for g, new in changes.items():
                if current.get(g, "none") != new:
                    out.append(self.plan_effect(g, new, land, pm, pt, push))
            if self.wins_read:   # the win condition (cognitivechess_v2): a move after which the opponent has no reply while in check
                _, replies = plans.moves(b, them, memo)
                if not replies and b.is_in_check(them):
                    out.append(self.win_effect(b, land, pm, push, them, getattr(self, "outcome_obj", "outcome_white")))
            if self.stalemate_read and stalemates(b, them):   # the opponent's stalemate plan, made by this move (cognitivechess_v2)
                out.append(self.stalemate_effect(b, land, pm, push, them))
            if getattr(self, "mates_read", False) and self.qualifies(self.board, move, b):   # a new forced mate this move would reach
                found = self.read_mate(b)
                if found and found[0] == "new":
                    out.append(self.mate_effect(b, land, pm, push, them))
            if self.covers_read:   # coverage: the sets this move would uncover or cover again
                out.extend(self.cover_effects(b, move, land, push, covers_now, stoppable_now, stops_now))
            if self.bearings_read:   # its own pieces' bearings: the move leaving one hanging, or one no longer hanging
                out.extend(self.bearing_effects(b, move, land, push, pm, pt))
        return out

    bearings_read = True   # (the user, 2026-11-17: "the gerund changing to 'hanging' should be a loss of territory")

    def region_weight(self, r):
        """What a region weighs where the register sums what a push loses or brings back (Params.region_weights; the user, 2026-11-17,
        "include what it can reach"): a piece's bearing weighs 1 and what the piece can reach, the squares its force reaches from where
        it stands on an open board (rook moves for a rook, a knight's jumps; a pawn's captures and its step), so what it could do once
        the lines open counts, not only what it holds up now; every other region 1."""
        if not r.endswith("_bearing"):
            return 1
        piece = r[:-len("_bearing")]
        sq = self.where.get(piece)
        if sq is None:
            return 1
        memo = self.__dict__.setdefault("_reach_memo", {})
        kind = self.board.pieces[sq]
        colour = bool(self.board.colors[sq])
        key = (kind, colour, sq)
        if key not in memo:
            import chess
            open_board = chess.BaseBoard.empty()
            open_board.set_piece_at(sq, chess.Piece(kind, colour))
            n = len(open_board.attacks(sq))
            if kind == chess.PAWN:
                n += 1   # (its step forward, besides its captures)
            memo[key] = n
        return 1 + memo[key]

    def resting_on(self, b, sq):
        """What rests on the piece standing on `sq` (b: the board after a move, them to move): the opponent's plans (one-move gains)
        that stand only without it, read by taking it off the board and reading their gains again (the plans it alone prevents; the
        register's liens, read off the board). Its own square excluded (that is the piece's own loss). -> set of gains, memoized."""
        me, them = seat(self)
        memo = self._plan_memo
        key = ("resting", b.zobrist_hash(), sq)
        if key not in memo:
            without = b.copy()
            without.set_piece_at(sq, 0, False)
            plans.rehash(without)
            had = set(plans.one_move(b, them, me, memo))
            memo[key] = {g for g in plans.one_move(without, them, me, memo) if g not in had and g[1] != sq}
        return memo[key]

    def effects_after(self, inv):
        """What a push would do to the regions that are territory here (the opponent's plans, coverage, its own pieces' bearings), as
        the forces predict it (push_predictions; read by SovAgent.anti_update with Params.defense_still: the register presses for
        everything it holds, so a predicted loss of territory is felt at once; the user, 2026-11-17: "loss of territory is always
        felt"). Waiting (None) changes nothing on the board. -> set of effects (`<region>_<doing>`), memoized by position."""
        me_, them_ = seat(self)
        if inv is None:   # waiting: every piece of its own hanging now stays hanging, and what rests on it is still to be lost (the
            # play app: 7... Bc6 attacked the queen on b7; waiting, and every move leaving it there, read as costing nothing, and the
            # queen's escape, giving them a few square plans, read worse than leaving it: a hanging piece only counted when a move
            # made it hang)
            out = set()
            if self.bearings_read and self.board.turn == me_:
                b_them = plans.turned(self.board, them_)
                for o, sq in self.where.items():
                    if sq is not None and self.board.colors[sq] == me_ and self.shown.get(f"{o}_bearing") == "hanging":
                        out.update(f"{plan_obj(*g)}_stoppable" for g in self.resting_on(b_them, sq))
            return out
        key = (self.board.zobrist_hash(), len(self.__dict__.get("_cover_sets", {})),   # (and the bearings as shown: a reading
               tuple(sorted((o, s) for o, s in self.shown.items() if o.endswith("_bearing"))))   # reaches the mind a slice after the
        #   board changes, and the memo kept by position alone held answers read before: a rook just attacked read free, its
        #   rescues no gain, waiting no loss; check_rook_rescue.py)
        memo = self.__dict__.get("_effects_after")
        if memo is None or memo[0] != key:
            by = {}
            offers = None
            for effect, n, forces, rel, chain in self.push_predictions():
                if effect.startswith(("plan_", COVER)) or "_bearing_" in effect:
                    by.setdefault(chain[0], set()).add(effect)
                if effect.endswith("_bearing_hanging"):   # a piece left hanging: what rests on it goes with it (the user, 2026-11-17,
                    if offers is None:                       # "yes, exactly": a piece's loss is the loss of every region it alone holds
                        offers = self.offers()               # up, so a queen weighs what it does on the board, not a value table)
                    move = offers.get(chain[0].split("_push")[0])
                    if move is not None:
                        piece = effect[:-len("_bearing_hanging")]
                        me_, _ = seat(self)
                        b = plans._after(plans.turned(self.board, me_), move)
                        at = move.final_square if self.ids_at(move.from_square) == piece else self.where.get(piece)
                        if at is not None:
                            by[chain[0]].update(f"{plan_obj(*g)}_stoppable" for g in self.resting_on(b, at))
            if self.bearings_read:   # and a piece that stays hanging after the move: what rests on it is still to be lost (as waiting)
                if offers is None:
                    offers = self.offers()
                me_, them_ = seat(self)
                hanging_now = [(o, sq) for o, sq in self.where.items() if sq is not None and self.board.colors[sq] == me_
                               and self.shown.get(f"{o}_bearing") == "hanging"]
                if hanging_now:
                    for label, move in offers.items():
                        b = plans._after(plans.turned(self.board, me_), move)
                        pt = plans.press(b, them_, self._plan_memo)
                        c_ = f"{label}_push:{self.ids_at(move.from_square)}_present"
                        for o, sq in hanging_now:
                            at = move.final_square if sq == move.from_square else sq
                            if b.pieces[at] == 0 or b.colors[at] != me_:
                                continue
                            if at in pt and not b.is_attacked_by(at, me_):   # still hanging after this move
                                by.setdefault(c_, set()).update(f"{plan_obj(*g)}_stoppable" for g in self.resting_on(b, at))
            memo = self._effects_after = (key, by)
        c = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
        if c not in memo[1]:   # a commitment (commit_push:<potential>_<push>): what the push it commits to would do (first nothing,
            import re          # so a commitment to a move leaving a knight hanging carried no felt loss: trace_defense.py)
            m = re.search(r"(\d+ [^_]+_push:.*)$", c)
            c = m.group(1) if m else c
        return set(memo[1].get(c, ()))

    def bearing_effects(self, b, move, land, push, pm, pt):
        """Its own pieces' bearings after a move (them to move: b), as the world reads a bearing (WarpWorld.read_forces): hanging when
        their pieces press the square and none of its own guard it, pressed when guarded, free when unpressed. A change into or out of
        hanging is a potential effect: `<piece>_bearing_<doing>`, as the world will show it a slice after (2), relative
        `bearing+<distance from where the piece lands>_<doing>`. Forces: theirs pressing the square, p0 if the piece moved guards it
        (or is it), mine if others do."""
        from rustboard import square_file, square_rank
        me, them = seat(self)
        out = []
        for o, sq in self.where.items():
            if sq is None or self.board.colors[sq] != me:
                continue
            now = self.shown.get(f"{o}_bearing")
            at = land if sq == move.from_square else sq
            if b.pieces[at] == 0 or b.colors[at] != me:
                continue   # (a piece that isn't there after the move: castling's rook is read where it stood)
            attacked = at in pt
            guarded = b.is_attacked_by(at, me)
            new = "free" if not attacked else "pressed" if guarded else "hanging"
            if (now == "hanging") == (new == "hanging"):
                continue
            node = "bearing+piece:square"
            forces = set()
            if attacked:
                forces.add(("theirs", node))
            if at == land or land in pm.get(at, ()):
                forces.add(("p0", node))
            if set(pm.get(at, ())) - {land}:
                forces.add(("mine", node))
            d = max(abs(square_file(at) - square_file(land)), abs(square_rank(at) - square_rank(land)))
            out.append((f"{o}_bearing_{new}", 2, frozenset(forces), f"bearing+{d}_{new}", (push,)))
        return out

    @staticmethod
    def mate_effect(b, land, pm, push, them=BLACK):
        """A move reaching a forced-mate position for White not reached before (Stockfish; cognitivechess_v2, the user, 2026-11-17: a
        mate-in-X situation is territory, never given back, every distinct one): the world shows forced_mate: new in the mind's next
        slice (the plan effects' timing, 2). Force structure as the win effect's: p0 and/or mine pressing their_king. -> (effect, 2,
        forces, "forced_mate+0_new", (push,))."""
        king = b._king_sq[them]
        src = set(pm.get(king, ()))
        forces = set()
        if land in src:
            forces.add(("p0", "their_king"))
        if src - {land}:
            forces.add(("mine", "their_king"))
        return ("forced_mate_new", 2, frozenset(forces), "forced_mate+0_new", (push,))

    stalemate_read = True   # (cognitivechess_v2, the user, 2026-11-17: "stalemate is an opponent plan")

    @staticmethod
    def stalemate_effect(b, land, pm, push, them=BLACK):
        """A move that stalemates them: their stalemate plan made, as the world shows it in the mind's next slice (plan_stalemate:
        made; the plan effects' timing, 2). Its force structure, relative: the piece moved (p0) presses a square their king could step
        to, and/or the mind's other pieces do. -> (effect, 2, forces, "plan_stalemate+0_made", (push,))."""
        from rustboard import square_file, square_rank
        king = b._king_sq[them]
        around = {sq for sq in range(64) if sq != king and max(abs(square_file(sq) - square_file(king)),
                                                               abs(square_rank(sq) - square_rank(king))) == 1}
        src = set().union(*(pm.get(sq, ()) for sq in around)) if around else set()
        forces = set()
        if land in src:
            forces.add(("p0", "their_king_box"))
        if src - {land}:
            forces.add(("mine", "their_king_box"))
        return (f"{STALEMATE}_made", 2, frozenset(forces), "plan_stalemate+0_made", (push,))

    wins_read = True   # (cognitivechess_v2, the user, 2026-11-17: "the rules conditions should ALWAYS be territory")

    @staticmethod
    def win_effect(b, land, pm, push, them=BLACK, outcome="outcome_white"):
        """The win condition as a potential effect (the user, 2026-11-17: the rules' conditions are always territory; checkmating the
        opponent is the rules' win). A move that mates: the game's outcome for White becomes won, as the world shows it in the mind's
        next slice (GameWorld.act; the plan effects' timing, 2). Its force structure, relative: the piece moved (p0) presses the
        opponent's king, and/or the mind's other pieces do (a discovered or double check). -> (effect, 2, forces, "mate+0", (push,))."""
        king = b._king_sq[them]
        src = set(pm.get(king, ()))
        forces = set()
        if land in src:
            forces.add(("p0", "their_king"))
        if src - {land}:
            forces.add(("mine", "their_king"))
        return (f"{outcome}_won", 2, frozenset(forces), "mate+0", (push,))

    @staticmethod
    def plan_effect(g, new, land, pm, pt, push):
        """A plan's change as a potential effect: (as the world will show it, 2 slices, the force structure relative to the move, the
        relative effect, (the push,))."""
        from rustboard import square_file, square_rank, square_side
        kind, sq = g
        d = (max(abs(square_file(sq) - square_file(land)), abs(square_rank(sq) - square_rank(land)))
             if square_side(sq) == square_side(land) else "x")
        node = f"plan+{kind}:square"
        forces = set()
        if land in pm.get(sq, ()):
            forces.add(("p0", node))
        if set(pm.get(sq, ())) - {land}:
            forces.add(("mine", node))
        if pt.get(sq):
            forces.add(("theirs", node))
        return (f"{plan_obj(*g)}_{new}", 2, frozenset(forces), f"plan_{kind}+{d}_{new}", (push,))

    def potential_effects(self, pushes=()):
        """No-push predictions: none (the board is still between the mind's moves); defined so the mind reads push_predictions
        (SovAgent.force_predict runs where a world has potential_effects)."""
        return []

    def _stop_doing(self, g, board_black_to_move, memo):
        """A plan's doing on a board where the opponent is to move: stoppable if some move of the mind's then ends it."""
        me, them = seat(self)
        b, mine_moves = plans.moves(board_black_to_move, me, memo)
        stop = any(not plans.there(g, plans._after(b, x), them, me, memo)
                   for x in sorted(mine_moves, key=lambda x: -plans.touches(x, {g[1]})))
        return "stoppable" if stop else "unstoppable"

    @staticmethod
    def role_of(node):
        """A node of a plan effect's force structure: its role kind, and whether it is on the effect's side (the plan's square)."""
        if node.startswith("plan+"):
            return node.split(":", 1)[-1], True
        if node == "their_king":   # (the win effect's side: the opponent's king, cognitivechess_v2)
            return "king", True
        if node == "their_king_box":   # (the stalemate effect's side: the squares their king could step to)
            return "king_box", True
        if node == "cover":   # (a coverage effect's side: the set of plans one move can't end together)
            return "cover", True
        if node.startswith("bearing+"):   # (a bearing effect's side: the square its piece stands on)
            return "bearing", True
        if node.startswith("member+"):   # (a member plan converging on the set: its kind)
            return "plan_" + node.split("+", 1)[1].split("@", 1)[0], False
        return ("part" if node == "p0" else node), False

    def read_forces(self):
        out = super().read_forces()
        if self.__dict__.get("no_plans"):   # (a reading that never looks at the plans: imagine.Imagines.imagined_start, whose start keeps a
            return out                      # piece's own readings and the files' pressure only, carry.start_of; 2026-11-13, exact)
        readings = self.read_plans()
        for k in KINDS:
            for sq in SQUARES:
                o = plan_obj(k, sq)
                out[o] = readings.get(o, "none")
        out[STALEMATE] = readings.get(STALEMATE, "none")
        if self.covers_read:
            out.update(self.read_covers())
        if getattr(self, "mates_read", False):
            out["forced_mate"] = self.__dict__.get("forced_mate_state", "none")
        return out


STANDING = "standing_white"
HELD_FOREVER = ((STANDING, "up"), ("outcome_white", "won"))   # (region, the state that, once reached, is the mind's forever; give
#   reads them for the seat's colour: standing_<colour>, outcome_<colour>)
OWNED_FROM_START = ("potential:mate+0", "potential:forced_mate+0_new")   # (the rules' win, owned before it is ever reached)


MATE = "potential:mate+0"


def read_mate_passed(agent, choice):
    """A mate passed up is a loss of territory (the user, 2026-11-17: "did you fix it so a loss of mate is a loss of territory??"; the
    owned prediction's own law, SovAgent.own_prediction: "if you lose the prediction by intervening, you've lost what you own"). Called
    after each of the mind's ticks with what it chose. If a move on offer this slice led to mate (SovAgent.situational, from the
    forces' predictions) and the mind made a push that wasn't one of them, the mate is lost; whenever a move on offer leads to mate and
    the mind hasn't passed it, the mate is held (held again when one stands again)."""
    from sov_agent import inv_id
    situational = agent.__dict__.get("situational") or {}
    mating = {c for c, effects in situational.items() if MATE in effects}
    if not mating:
        return
    made_push = choice is not None and choice[0] not in ("commit", "ask")
    if made_push and inv_id(choice) not in mating:
        agent.own_prediction(MATE, False)
        agent.__dict__.setdefault("mates_passed", []).append((agent.mind.t, inv_id(choice), sorted(mating)))
    else:
        agent.own_prediction(MATE, True)


def give(agent, world):
    """The mind's territory, after each tick, in three levels (the user, 2026-11-13: "Yes, three levels"): a square where the opponent
    has no plan is held; a plan the mind can stop is contested (a threat it can still answer); one it can't stop is lost. Every plan
    region is tracked from the start (SovAgent.track_region, by reading). (First, the user's "Thwartable ones": only stoppable plans
    held, a plan ending let go; then "ending a plan is a gain" and a new plan for them a loss, which needs no plan to be held.)"""
    mine_ = ("white_" if seat(world)[0] == WHITE else "black_")
    for o, doing in world.shown.items():
        if o.startswith("plan_"):   # (made: the stalemate plan achieved, lost as an unstoppable plan is)
            agent.track_region(o, doing not in ("unstoppable", "made"), contested=(doing == "stoppable"))
        elif o.startswith(COVER):   # coverage (impossible_demands.md): held at none, contested at covered, lost at uncovered
            agent.track_region(o, doing != "uncovered", contested=(doing == "covered"))
        elif getattr(world, "bearings_read", False) and o.startswith(mine_) and o.endswith("_bearing"):
            # its own piece's bearing (the user, 2026-11-17: "the gerund changing to 'hanging' should be a loss of territory"): held
            # while free or pressed, lost when hanging
            agent.track_region(o, doing != "hanging")
    for o in world.__dict__.get("_cover_sets", {}):   # a set named but not yet shown (named by a prediction): none on the board, held
        if o not in world.shown:
            agent.track_region(o, True)
    # the win condition, for good (cognitivechess_v2; the user, 2026-11-17: the rules' conditions are always territory): each game the
    # mind won, by checkmate, is its territory for good, as tetris's cleared rows are (run.own_clears)
    me, them = seat(world)
    name = "white" if me == WHITE else "black"
    games = getattr(world, "games", [])
    seen = agent.__dict__.get("_wins_read", 0)
    for k in range(seen, len(games)):
        if str(games[k][0]).startswith("1-0" if me == WHITE else "0-1"):
            agent.track_region(f"won_game_{k + 1}", True)
            agent.mind.territory.rows[f"won_game_{k + 1}"]["for_good"] = True
    agent._wins_read = len(games)
    # White being up in material: once it is, the mind holds it forever (the user, 2026-11-17: "just like territory that is kept for
    # all-time"; "up can still be a want, because it's held"; "once it gets that territory of being up, it holds it forever"). Held while
    # White is up; held but contested while it isn't (never lost), so its contested slot offers back the one state held, up, as a want;
    # down and even are never held, never wanted. Before White is first up the region is no one's to claim (unclaimable "standing_"):
    # first it was held by claims, went lost when the mind's moves stopped changing it, and its lost slot offered standing_white_up and
    # then standing_white_down as wants (trace_standing_want.py)
    # The same for the game's outcome: once White has won, won is the mind's forever (the user, 2026-11-17: "why not make it permanent
    # territory like the standing??"; first the register claimed outcome_white as the mind's, drawn, at the end of the full run's game 1)
    # The win's potential effects are owned from the start (the user, 2026-11-17: "the rules conditions should ALWAYS be territory";
    # "FIX ALL THIS"): a potential effect becomes a want only through an owned prediction, and a prediction is owned only once one has
    # stood, so a mind that had never mated could never want mate. Traced on the full run's game 1 (trace_missed_mate.py): with h7h8q
    # and h7h8r mating (both told "causes potential:mate+0"), the mind played c5d7, which stalemated, for its held want
    # potential:plan_square+1_none; the mate+0 prediction had never stood, so nothing wanted it. Owned, held for good: whenever a move
    # on offer leads to one, own_candidates offers it as a want
    for p in OWNED_FROM_START:   # (owned from the start; held or lost after that by read_mate_passed)
        if p.replace(":", "_", 1) not in agent.mind.territory.rows:
            agent.own_prediction(p, True)
    terr = agent.mind.territory
    for region, state in ((f"standing_{name}", "up"), (f"outcome_{name}", "won")):   # (HELD_FOREVER, for the seat's colour)
        now = world.shown.get(region) == state
        row = terr.rows.get(region)
        if now or (row is not None and row.get("for_good")):
            agent.track_region(region, True, contested=not now)
            row = terr.rows[region]
            row["for_good"] = True
            row["held_states"] = {f"{region}_{state}"}
    # each distinct forced-mate position the game reached, territory for good, never given back (the user, 2026-11-17: "every
    # distinct; it forces diverse understanding"): read from the world's record of them, once each
    log = world.__dict__.get("forced_mate_log", [])
    seen = agent.__dict__.get("_mates_read", 0)
    for k in range(seen, len(log)):
        agent.track_region(f"forced_mate_{k + 1}", True)
        agent.mind.territory.rows[f"forced_mate_{k + 1}"]["for_good"] = True
    agent._mates_read = len(log)
