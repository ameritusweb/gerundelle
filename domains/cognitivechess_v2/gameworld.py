"""Full games of Warp 1 Chess (LADDER.md, rung 4). After duel.py: the mind plays White from the rulebook's starting position (WarpBoard.starting_position); Black is another player.

- A game ends when a king is taken, the side to move has no move (mate or stalemate), the engine's fifty-move rule, or after HALF_MOVES half-moves (my cap).
- Each game's result is kept: White's material balance at its end and the engine's result where the game ended by its rules.
"""
import random

from duel import WarpDuel
from warpworld import BLACK, WHITE, WarpBoard  # noqa: F401

HALF_MOVES = 80


class GameWorld(WarpDuel):
    me = WHITE   # the seat: the colour of the mind this world is read for (cognitivechess_v2's league, 2026-11-17: "Mind vs mind"); a class
    #              default, so worlds pickled before seats load as White's

    def __init__(self, seed=0, half_moves=HALF_MOVES, fen=None, me=WHITE):
        self.me = me
        super().__init__(fen or WarpBoard.starting_position().to_fen(), seed=seed, half_moves=half_moves)   # the rulebook's start (chevron pawns); move.py's STARTING_FEN isn't it
        self.objs[self.outcome_obj] = None   # the game, from the seat's view: playing, won, lost or drawn (read from the engine's result)
        self.games = []   # (result, White's material balance, half-moves played)

    @property
    def me_name(self):
        return "White" if self.me == WHITE else "Black"

    @property
    def them_name(self):
        return "Black" if self.me == WHITE else "White"

    @property
    def outcome_obj(self):
        return f"outcome_{self.me_name.lower()}"

    RESIGN_AFTER_NEW_MATES = 7   # the seat's opponent resigns after this many new forced mates for the seat in a game (the user,
    #                              2026-11-17: "after the 7th 'new' forced mate, have black resign the game so white wins"; in the league,
    #                              "Either side resigns"); 0: never

    def over(self):
        return bool(self.__dict__.get("resigned")) or super().over() or self.draw_reason() is not None

    def result_now(self):
        """The game's result: a resignation, else the engine's."""
        r = self.__dict__.get("resigned")
        return "1-0" if r == "Black" else "0-1" if r == "White" else self.board.result()

    def conclude(self):
        """If the game is over and the seat hasn't been told: the outcome from the seat's view, shown to its mind in its next slice."""
        if not self.over() or self.outcome != "playing":
            return
        r = self.result_now()
        mine, theirs = ("1-0", "0-1") if self.me == WHITE else ("0-1", "1-0")
        new = "won" if r == mine else "lost" if r == theirs else "drawn"
        if self.me_name in self.has_moved:
            self.pend[self.me_name][self.outcome_obj] = ("playing", new)
        self.outcome = new

    def draw_reason(self):
        """A draw by the rules besides stalemate (cognitivechess_v2, the user, 2026-11-17: "Go till checkmate or there are too few pieces
        for checkmate. No other stopping condition other than ones in the rules like stalemate, draw"). Applied as they arise, not claimed
        (my reading: no player here claims): the fifty-move rule, threefold repetition, and insufficient material (python-chess's
        reading). None if none holds."""
        if self.board.halfmove_clock >= 100:
            return "fifty-move rule"
        if self.__dict__.get("_reps", {}).get(self._rep_key(), 0) >= 3:
            return "threefold repetition"
        key = self.board.zobrist_hash()
        memo = self.__dict__.setdefault("_insufficient", {})
        if key not in memo:
            import chess
            memo[key] = chess.Board(self.board.to_fen()).is_insufficient_material()
        return "insufficient material" if memo[key] else None

    def _rep_key(self, board=None):
        """The position as repetition reads it: placement, side to move, castling rights, and an en passant square only if a capture
        there is legal. Also the identity of a distinct forced-mate position (read_mate)."""
        board = self.board if board is None else board
        f = board.to_fen().split()
        ep = f[3]
        if ep != "-":
            sq = (int(ep[1]) - 1) * 8 + (ord(ep[0]) - ord("a"))
            if not any(m.to_square == sq and board.pieces[m.from_square] == 1 for m in board.legal_moves):
                ep = "-"
        return (f[0], f[1], f[2], ep)

    mates_read = True   # (cognitivechess_v2, the user, 2026-11-17: a Stockfish mate-in-X situation is territory, never given back)

    @staticmethod
    def qualifies(before, move, after):
        """Whether Stockfish is asked about the position a move leaves (the user, 2026-11-17: "it would only get called on a capture or a
        check or a promotion")."""
        capture = bool(before.pieces[move.to_square]) or (before.pieces[move.from_square] == 1 and move.to_square == before.en_passant
                                                         and (move.from_square & 7) != (move.to_square & 7))
        return capture or bool(move.promotion) or after.is_in_check(after.turn)

    def read_mate(self, board):
        """-> ("new" | "known", key, X) if the seat's colour has a forced mate from this position (Stockfish, mate_oracle), else None.
        New: a distinct position this world hasn't reached with a forced mate before (forced_mate_seen, over the world's whole lifetime)."""
        import mate_oracle
        x = mate_oracle.forced_mate(board.to_fen(), self.me)
        if not x:
            return None
        key = self._rep_key(board)
        return ("known" if key in self.__dict__.get("forced_mate_seen", set()) else "new", key, x)

    def play(self, move):
        before = self.board.copy()
        out = super().play(move)
        if not self.__dict__.get("dreaming") and not self.__dict__.get("imagining"):   # (only the game's own moves repeat)
            reps = self.__dict__.setdefault("_reps", {})
            k = self._rep_key()
            reps[k] = reps.get(k, 0) + 1
            if self.mates_read:   # a forced mate for White, reached by the game's own move: each distinct one recorded once (the world's
                state = "none"    # record of what happened, as tetris's cleared_log; whose territory it is, the register's: plansworld.give)
                if self.qualifies(before, move, self.board):
                    found = self.read_mate(self.board)
                    if found:
                        state, key, x = found
                        self.__dict__.setdefault("forced_mate_reads", []).append(   # (each reading, for the run's log)
                            (state, x, "White" if before.turn else "Black", move.uci()))
                        if state == "new":
                            self.__dict__.setdefault("forced_mate_seen", set()).add(key)
                            self.__dict__.setdefault("forced_mate_log", []).append((key, x))
                            self.new_mates_game = self.__dict__.get("new_mates_game", 0) + 1
                            if self.RESIGN_AFTER_NEW_MATES and self.new_mates_game >= self.RESIGN_AFTER_NEW_MATES:
                                self.resigned = self.them_name   # (the game is over: over(), and conclude shows the seat it won)
                self.forced_mate_state = state
        return out

    def reset(self):
        if hasattr(self, "standing") and getattr(self, "moved", 0):
            ended = self.over()
            r = "unfinished"
            if not ended and self.moved >= self.moves:   # the half-move cap, a draw (the user, 2026-11-17: "end it at 300 half-moves as a draw")
                r = f"1/2-1/2 (the {self.moves} half-move cap)"
            if ended and self.__dict__.get("resigned"):
                r = f"{self.result_now()} ({self.resigned} resigned after {self.RESIGN_AFTER_NEW_MATES} new forced mates)"
            elif ended:
                r = self.board.result()
                why = self.draw_reason()
                if r == "*" and why:
                    r = f"1/2-1/2 ({why})"
                elif r == "1/2-1/2":
                    r = "1/2-1/2 (stalemate)"
            self.games.append((r, self.material() - self.start_material, self.moved))
        super().reset()
        self.outcome = "playing"
        self._reps = {self._rep_key(): 1}
        self.forced_mate_state = "none"
        self.new_mates_game, self.resigned = 0, None

    owned = False   # rung 4 with Params.own_wants (the user: White's pieces are given territory, like the body)

    def states(self, tree=None):
        out = super().states(tree)
        out[self.outcome_obj] = self.outcome
        if self.owned:   # a captured White piece leaves view, so a mind whose pieces are given reads its capture as a loss (as
            # chessworld's `owned`); a Black piece White has taken stays in view, captured: White's for good (the user)
            for o in [o for o, g in out.items() if o.startswith("white_") and g == "captured"]:
                del out[o]
        return out

    def white_pieces(self):
        return {o for o in self.ids.values() if o.startswith("white_")}

    def act(self, inv=None, hold=False):
        diffs = super().act(inv, hold)
        if inv is not None:
            self.conclude()
        return diffs


def opening_rooms(root=__import__("paths").MINI_GAMES):
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
