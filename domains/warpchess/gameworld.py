"""Full games of Warp 1 Chess (LADDER.md, rung 4). After duel.py: the mind plays White from the rulebook's starting position (WarpBoard.starting_position); Black is another player.

- A game ends when a king is taken, the side to move has no move (mate or stalemate), the engine's fifty-move rule, or after HALF_MOVES half-moves (my cap).
- Each game's result is kept: White's material balance at its end and the engine's result where the game ended by its rules.
"""
import random

from duel import WarpDuel
from warpworld import BLACK, WHITE, WarpBoard  # noqa: F401

HALF_MOVES = 80


class GameWorld(WarpDuel):
    def __init__(self, seed=0, half_moves=HALF_MOVES, fen=None):
        super().__init__(fen or WarpBoard.starting_position().to_fen(), seed=seed, half_moves=half_moves)   # the rulebook's start (chevron pawns); move.py's STARTING_FEN isn't it
        self.objs["outcome_white"] = None   # the game, from White's view: playing, won, lost or drawn (read from the engine's result)
        self.games = []   # (result, White's material balance, half-moves played)

    def over(self):
        return super().over() or self.board.halfmove_clock >= 100

    def reset(self):
        if hasattr(self, "standing") and getattr(self, "moved", 0):
            ended = self.over()
            self.games.append((self.board.result() if ended else "unfinished", self.material() - self.start_material, self.moved))
        super().reset()
        self.outcome = "playing"

    owned = False   # rung 4 with Params.own_wants (the user: White's pieces are given territory, like the body)

    def states(self, tree=None):
        out = super().states(tree)
        out["outcome_white"] = self.outcome
        if self.owned:   # a captured White piece leaves view, so a mind whose pieces are given reads its capture as a loss (as
            # chessworld's `owned`); a Black piece White has taken stays in view, captured: White's for good (the user)
            for o in [o for o, g in out.items() if o.startswith("white_") and g == "captured"]:
                del out[o]
        return out

    def white_pieces(self):
        return {o for o in self.ids.values() if o.startswith("white_")}

    def act(self, inv=None, hold=False):
        diffs = super().act(inv, hold)
        if inv is not None and self.over() and self.outcome == "playing":
            r = self.board.result()
            new = "won" if r == "1-0" else "lost" if r == "0-1" else "drawn"
            if "White" in self.has_moved:
                self.pend["White"]["outcome_white"] = ("playing", new)
            self.outcome = new
        return diffs


def opening_rooms(root="E:/vscode/warponechess/mini_games"):
    """The user's self-play openings (warp_self_play.py): each iteration's game starts from one opening and the engine's best move after it, and
    every mini game of that iteration is a proven line from that one position. -> [(iteration, the start's FEN)], in iteration order."""
    import glob
    import os
    out = []
    for d in sorted(glob.glob(f"{root}/iter_*")):
        f = sorted(glob.glob(f"{d}/line_A/*.txt"))[0]
        out.append((os.path.basename(d), open(f, encoding="utf-8").read().splitlines()[1][len("Start: "):].strip()))
    return out


class RandomSide:
    """Black, playing a uniformly random legal move when it's its turn."""

    def __init__(self, world, seed=0):
        self.world, self.rng = world, random.Random(9000 + seed)
        self.reached = []

    def tick(self):
        w = self.world
        w.actor = "Black"
        w.pend["Black"] = {}   # a random player reads nothing: what its moves came to isn't kept for it (else the game never resets)
        offers = w.offers()
        if not offers:
            return
        label = self.rng.choice(sorted(offers))
        w.act((label, w.ids_at(offers[label].from_square), "present"))
        w.pend["Black"] = {}
