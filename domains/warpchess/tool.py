"""The tool (PLAN.md, "Tool use"; the user, 2026-11-13: "it then uses tool use, which runs mcts with alpha beta pruning and tables and
heuristics to get an answer to a question"; its answer is told; it answers questions about plans and potential effects; its heuristics
stay inside it; "it just costs time of course").

A search over the real rules (WarpBoard, through plans.py's readings), outside the mind. It answers a question and returns what it
searched, nothing else: never a value or a recommendation (DRIFT.md rule 10).

Questions (so far):
  ("thwart", plan)   can the mind (White, to move) stop this plan of the opponent's (plans.py: a gain of a piece, square or outpost, one or
                     two of their moves away, read through the mind's reply)? -> the move that stops it, or None
  ("plan", plan)     is this a plan of theirs on this board at all? -> True / False

The search (my readings, for the user to change):
- "Can it be thwarted" has a yes/no answer, so the search is an AND-OR search: some move of mine such that no first move of theirs forces
  the gain through every reply of mine. Each branch stops as soon as its answer is known (alpha-beta's cut-off, for a yes/no value).
- Tables: positions searched are kept (a transposition table, by the engine's hash), across calls, so a position asked about again costs
  nothing; bounded, cleared when large.
- Heuristics, inside the tool only: moves touching the plan's square are tried first, so a refutation or a stop is found early.
- Time: what a call costs is the positions it searched (pushes made); SLICE_POSITIONS of them make one slice of the mind's waiting (my
  number). An answer from the table costs one slice (the asking).
"""
import math

import plans

WHITE, BLACK = True, False
SLICE_POSITIONS = 2000   # positions searched per slice the mind waits (my number)
TABLE_LIMIT = 400_000


class Tool:
    def __init__(self):
        self.table = {}   # the transposition table: plans.py's memo (positions, pressures, plans, single-gain checks) and the answers
        self.calls = []   # (question, answer, positions searched, slices)

    def _positions(self):
        return sum(1 for k in self.table if isinstance(k, tuple) and k and k[0] == "moves")

    def ask(self, question, board, me=WHITE):
        """-> (answer, slices it took)."""
        if len(self.table) > TABLE_LIMIT:
            self.table.clear()
        them = not me
        kind, plan = question
        key = ("answer", kind, plan, board.zobrist_hash(), me)
        if key in self.table:
            answer, slices = self.table[key], 1
            self.calls.append((question, answer, 0, slices))
            return answer, slices
        before = self._positions()
        if kind == "thwart":
            answer = plans.thwartable(plan, board, them, me, self.table)
        elif kind == "plan_lines":   # two-move ways to end the plan (plans.plan_lines)
            answer = plans.plan_lines(board, plan, them, me, self.table)
        elif kind == "line":   # (PLAN.md step 4) after my move `plan` (here a move): each reply of theirs, my moves ending their plans
            answer = plans.lines(board, plan, them, me, self.table)
        elif kind == "plan":
            answer = plans.still_plan(plan, plans.turned(board, them), them, me, self.table)
        else:
            raise ValueError(f"the tool doesn't answer {kind!r}")
        searched = self._positions() - before
        slices = max(1, math.ceil(searched / SLICE_POSITIONS))
        self.table[key] = answer
        self.calls.append((question, answer, searched, slices))
        return answer, slices


class MindTool:
    """The tool as a mind's agent sees it (Params.tool_use; SovAgent.tool): it can answer questions about the opponent's plans
    (plansworld's objects), and gives its answer as told relations. Asked about a plan concept (plan_<kind>_<square>_<doing>), it asks
    the Tool "can the mind thwart this plan?" on the board as it stands; a move that stops it is told as "<that move's push> causes
    <plan>_none" (the plan, no plan); when nothing stops it, nothing is told (my reading). The slices are the Tool's."""

    def __init__(self, world, tool=None):
        from plansworld import SQUARES
        from WarpOneChess.move import square_name
        self.world, self.tool = world, tool or Tool()
        self.predicted = []   # (the board's hash when asked, the prediction item)
        self.squares = {square_name(sq): sq for sq in SQUARES}

    def plan_of(self, concept):
        parts = concept.split("_")
        if len(parts) < 3 or parts[0] != "plan" or parts[1] not in ("piece", "square", "outpost") or parts[2] not in self.squares:
            return None
        return f"plan_{parts[1]}_{parts[2]}", (parts[1], self.squares[parts[2]])

    def can_answer(self, concept):
        """Only about a plan the world shows now (stoppable or unstoppable): first any plan concept, and the mind asked about plans that
        weren't plans (plan_outpost_Rc1_none), where any move trivially 'stops' one, and the told answers meant nothing. Or (PLAN.md
        step 4) about a move of the mind's on offer now: what follows it (lines)."""
        if self.move_of(concept) is not None:
            return True
        found = self.plan_of(concept)
        return found is not None and self.world.shown.get(found[0], "none") != "none"

    def move_of(self, concept):
        """The move a push on offer now names (its push id), or None."""
        w = self.world
        for inv in w.invitations():
            if concept == f"{inv[0]}_push:{inv[1]}_{inv[2]}":
                return w.offers().get(inv[0])
        return None

    def ask_line(self, concept, m1):
        """What follows a move (PLAN.md step 4; the user, 2026-11-13: the mind decides how far a line goes and what counts as forced):
        the Tool's lines after it, each standing as a two-move prediction, (m1's push, m2's push), whose effect is the plan ended, a
        slice after m2 (3 of the mind's slices from now: m1, then Black's answer seen and m2 made, then what m2 did). In its force
        structure, beside the plan's (plansworld.plan_effect, after m2 on the first reply it holds after): whether it holds after every
        reply Black has (`line`, `every` / `some`; my reading of the counts the mind decides on). Nothing is told beyond the predictions
        (force_predict tells m1's push it causes each). -> ([], slices)."""
        import plans as plans_
        from plansworld import plan_obj
        w = self.world
        (n, found), slices = self.tool.ask(("line", m1), w.board)
        b0 = plans_.turned(w.board, True)
        b1 = plans_._after(b0, m1)
        mover1 = w.ids_at(m1.from_square)
        land1 = m1.final_square
        memo = w._plan_memo
        for (m2, g), replies in sorted(found.items(), key=lambda kv: (kv[0][0].uci(), kv[0][1])):
            r = sorted(replies, key=lambda x: x.uci())[0]
            b2 = plans_._after(plans_.turned(b1, False), r)
            b3 = plans_._after(plans_.turned(b2, True), m2)
            mover2 = mover1 if m2.from_square == land1 else w.ids_at(m2.from_square)
            push2 = f"{w.label(m2)}_push:{mover2}_present"
            effect, _, forces, rel, _ = w.plan_effect(g, "none", m2.final_square, plans_.press(b3, True, memo),
                                                      plans_.press(b3, False, memo), push2)
            forces = frozenset(forces | {("line", "every" if len(replies) == n else "some")})
            self.predicted.append((w.board.zobrist_hash(), (effect, 3, forces, rel, (concept, push2))))
        return [], slices

    def stand_line(self, m1, push1, m2, g, replies, n):
        """A line (m1, a reply, m2 ends plan g) standing as a two-move prediction: (the plan, none; 3 of the mind's slices; the plan's force
        structure after m2 on the first reply it holds after, with `line`: `every` or `some` reply; the relative effect; (m1's push,
        m2's push)), for as long as the board is as it was asked on."""
        import plans as plans_
        w = self.world
        b1 = plans_._after(plans_.turned(w.board, True), m1)
        r = sorted(replies, key=lambda x: x.uci())[0]
        b2 = plans_._after(plans_.turned(b1, False), r)
        b3 = plans_._after(plans_.turned(b2, True), m2)
        mover1 = w.ids_at(m1.from_square)
        try:
            mover2 = mover1 if m2.from_square == m1.final_square else w.ids_at(m2.from_square)
        except StopIteration:
            return
        push2 = f"{w.label(m2)}_push:{mover2}_present"
        memo = w._plan_memo
        effect, _, forces, rel, _ = w.plan_effect(g, "none", m2.final_square, plans_.press(b3, True, memo), plans_.press(b3, False, memo), push2)
        forces = frozenset(forces | {("line", "every" if len(replies) == n else "some")})
        self.predicted.append((w.board.zobrist_hash(), (effect, 3, forces, rel, (push1, push2))))

    def ask(self, concept):
        m1 = self.move_of(concept)
        if m1 is not None:
            return self.ask_line(concept, m1)
        obj, plan = self.plan_of(concept)
        w = self.world
        # and the two-move ways to end it (the user, 2026-11-13: "why not have the tool answer the questions about the opponent's plans";
        # first only "can one move stop it", and the mind never asked about its moves, so no line was ever offered to commit to)
        found, slices2 = self.tool.ask(("plan_lines", plan), w.board)
        for m1_, (n, by_m2) in sorted(found.items(), key=lambda kv: kv[0].uci()):
            inv1 = next((i for i in w.invitations() if i[0] == w.label(m1_)), None)   # (m1 is on offer now: its push as offered)
            if inv1 is None:
                continue
            push1 = f"{inv1[0]}_push:{inv1[1]}_{inv1[2]}"
            for m2_, replies in sorted(by_m2.items(), key=lambda kv: kv[0].uci()):
                self.stand_line(m1_, push1, m2_, plan, replies, n)
        move, slices = self.tool.ask(("thwart", plan), w.board)
        slices += slices2
        if move is None:
            return [], slices
        mover = w.ids_at(move.from_square)
        push = f"{w.label(move)}_push:{mover}_{w.shown[mover]}"
        # and stood as a prediction (the user, 2026-11-13: "Stoppability as the tool's prediction"): the move ends the plan, a slice
        # after it, for as long as the board is as it was asked on (SovAgent.force_predict reads predictions())
        import plans as plans_
        b = plans_._after(plans_.turned(w.board, True), move)
        memo = w._plan_memo
        item = w.plan_effect(plan, "none", move.final_square, plans_.press(b, True, memo), plans_.press(b, False, memo), push)
        self.predicted.append((w.board.zobrist_hash(), item))
        return [(push, "causes", f"{obj}_none")], slices

    def predictions(self):
        """The tool's answers standing as predictions: those asked on the board as it stands now (each a potential effect, as
        world.push_predictions gives them)."""
        now = self.world.board.zobrist_hash()
        self.predicted = [(k, item) for k, item in self.predicted if k == now]
        return [item for _, item in self.predicted]
