"""The Warp world with the opponent's plans as the mind's territory (PLAN.md step 2; the user, 2026-11-13: territory is "being able to
'thwart' the hypothetical plans of the opponent"; "a plan is a gain of a piece, a square, or an outpost").

The mind plays White; the opponent's plans are Black's (plans.py). Each plan has an object, by kind and square: plan_piece_<sq>,
plan_square_<sq>, plan_outpost_<sq>, 3 x 112. Its doing, read each time the board changes (memoized by position):
  stoppable    a gain one of Black's moves would make now, and the mind has a move after which it is no longer there (one move: the
               two-move reading is the tool's, PLAN.md "Tool use", and too slow for every slice: check_plans.py)
  unstoppable  a gain one of Black's moves would make now that no move of the mind's stops
  none         no gain there for Black now
Territory (give), three levels (the user, 2026-11-13): no plan there, held; a plan the mind can stop, contested; one it can't, lost.
Held by reading only (read_held). Potential effects (push_predictions, PLAN.md step 3): what each move on offer would do to the plans. The pieces and files are no one's to claim (unclaimable), as Go's stones are once territory moved off them; `material` is left
claimable (a placed want, rung 1's, is about it).
"""
import plans
from WarpOneChess.move import TOTAL_SQUARES, square_name, square_rank
from warpworld import WarpWorld

KINDS = ("piece", "square", "outpost")
WHITE, BLACK = True, False


SQUARES = [sq for sq in range(TOTAL_SQUARES) if square_rank(sq) < 7]   # (the 112 real squares: a side is indexed by 64, a Warp board has 7 ranks)


def plan_obj(kind, sq):
    return f"plan_{kind}_{square_name(sq)}"


class PlansWorld(WarpWorld):
    unclaimable = ("white_", "black_", "file_")
    read_held = ("plan_",)

    def __init__(self, fen, **kw):
        self._plan_memo = {}
        self._plan_read = {}
        kw["forces"] = True
        super().__init__(fen, **kw)
        self.objs.update({plan_obj(k, sq): None for k in KINDS for sq in SQUARES})

    def read_plans(self):
        """plan object -> its doing, for the board as it stands (memoized by position)."""
        key = self.board.zobrist_hash()
        if key in self._plan_read:
            return self._plan_read[key]
        if len(self._plan_memo) > 200_000:   # (a bound on memory: the memo is a cache, cleared when large)
            self._plan_memo.clear()
        memo = self._plan_memo
        one = plans.one_move(self.board, BLACK, WHITE, memo)
        out = {}
        if one:
            b, mine_moves = plans.moves(self.board, WHITE, memo)
            for g in one:
                squares = {g[1]}
                stop = any(not plans.there(g, plans._after(b, x), BLACK, WHITE, memo)
                           for x in sorted(mine_moves, key=lambda x: -plans.touches(x, squares)))
                out[plan_obj(*g)] = "stoppable" if stop else "unstoppable"
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
        from WarpOneChess.move import square_file, square_rank, square_side
        invs = self.invitations()
        if not invs:
            return []
        memo = self._plan_memo
        now = self.read_plans()   # plan object -> stoppable / unstoppable
        current = {g: now[plan_obj(*g)] for g in ((k, sq) for k in KINDS for sq in SQUARES) if plan_obj(*g) in now}
        out = []
        for inv in invs:
            move = self.offers().get(inv[0])
            if move is None:
                continue
            b = plans._after(plans.turned(self.board, WHITE), move)
            one_after = plans.one_move(b, BLACK, WHITE, memo)
            touched = {move.from_square, move.final_square}
            land = move.final_square
            pm, pt = plans.press(b, WHITE, memo), plans.press(b, BLACK, memo)
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
        return out

    @staticmethod
    def plan_effect(g, new, land, pm, pt, push):
        """A plan's change as a potential effect: (as the world will show it, 2 slices, the force structure relative to the move, the
        relative effect, (the push,))."""
        from WarpOneChess.move import square_file, square_rank, square_side
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
        b, mine_moves = plans.moves(board_black_to_move, WHITE, memo)
        stop = any(not plans.there(g, plans._after(b, x), BLACK, WHITE, memo)
                   for x in sorted(mine_moves, key=lambda x: -plans.touches(x, {g[1]})))
        return "stoppable" if stop else "unstoppable"

    @staticmethod
    def role_of(node):
        """A node of a plan effect's force structure: its role kind, and whether it is on the effect's side (the plan's square)."""
        if node.startswith("plan+"):
            return node.split(":", 1)[-1], True
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
        return out


def give(agent, world):
    """The mind's territory, after each tick, in three levels (the user, 2026-11-13: "Yes, three levels"): a square where the opponent
    has no plan is held; a plan the mind can stop is contested (a threat it can still answer); one it can't stop is lost. Every plan
    region is tracked from the start (SovAgent.track_region, by reading). (First, the user's "Thwartable ones": only stoppable plans
    held, a plan ending let go; then "ending a plan is a gain" and a new plan for them a loss, which needs no plan to be held.)"""
    for o, doing in world.shown.items():
        if o.startswith("plan_"):
            agent.track_region(o, doing != "unstoppable", contested=(doing == "stoppable"))
