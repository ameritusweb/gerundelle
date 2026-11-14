"""Full games of Warp chess with the opponent's plans as the mind's territory (PLAN.md step 4; the user, 2026-11-13: "Plans on the game
world"). GameWorld (rung 4: the rulebook's start, Black a second player, turns, the other side's news) with PlansWorld's plan objects,
three-level territory, plan predictions and read-held plans (plansworld.py). The mind plays White.

Timing (as duel.py): the mind's move lands in its own slice (only the piece moved changes); Black answers between the mind's slices; what
both moves did reaches the mind in its next slice. A plan prediction made for a move is due a slice after it (plansworld: 2), which is the
slice in which the mind sees Black's answer too, so Black's reply can change what was predicted: that is the other side moving
(world.others), where a commitment can dissolve.
"""
from gameworld import GameWorld, HALF_MOVES
from plansworld import KINDS, SQUARES, PlansWorld, plan_obj

WHITE, BLACK = True, False


class PlansGame(PlansWorld, GameWorld):
    """PlansWorld's readings on GameWorld's game (MRO: PlansGame, PlansWorld, GameWorld, WarpDuel, WarpWorld)."""

    def __init__(self, seed=0, half_moves=HALF_MOVES, fen=None):
        self._plan_memo = {}
        self._plan_read = {}
        GameWorld.__init__(self, seed=seed, half_moves=half_moves, fen=fen)
        self.objs.update({plan_obj(k, sq): None for k in KINDS for sq in SQUARES})
        self.shown = self.read()

    def over(self):
        """The game's own end, or ended early by the run (rung4p --stop-at-dream: the mind tried to dream on its second slice in this game;
        the user, 2026-11-14)."""
        return bool(self.__dict__.get("ended_early")) or super().over()

    def reset(self):
        why = self.__dict__.pop("ended_early", None)
        n = len(getattr(self, "games", []))
        super().reset()
        if why and len(self.games) > n:   # recorded as stopped, with why, in place of the engine's result
            self.games[-1] = (why,) + tuple(self.games[-1][1:])

    def renew(self):
        """A game is set back only when it is over or reaches the half-move cap: the mind keeps its turn however long it thinks or waits
        on the tool (the user, 2026-11-13, "Nothing: no idle limit"; first the puzzle rooms' rule, IDLE slices with no move end an
        episode, set the first game back after 6 half-moves while the mind asked the tool)."""
        if (self.moved >= self.moves or self.over()) and not any(self.pend.values()):
            self.reset()
            self.diffs = []

    def push_predictions(self):
        if self.actor != "White":   # (only the mind's moves are predicted; Black's are its own)
            return []
        return PlansWorld.push_predictions(self)
