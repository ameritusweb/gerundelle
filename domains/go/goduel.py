"""Two minds on one Go board (the user, 2026-11-13: "build the two-mind world", for a league of temperament profiles ranked by Elo).

Each mind has its own seat: a GoWorld seen from its colour (`me`), with the other colour's opportunity forces as its objects
(opportunity_<x>_<y>: the opponent's chance at each point), its own placements and pass on offer, its own predictions (kills and
losses), its own reach, and its own territory read by run.give (where the opponent's opportunity is dead). Stones keep their own colour's
names in both seats (black_<n>, white_<n>; the user, 2026-11-11: whose a stone is is the register's to say, not the world's).

The two seats are one game: they are kept in lockstep. Each slice both seats act once, the side to move first. A seat's "other colour's
stone" (GoWorld.reply) is the stone the other mind placed in its own seat that same slice, or its pass; WAITING while the other hasn't
chosen. So the physics is GoWorld's, run once per seat on the same board, and the seats are checked identical every slice
(Duel.check). A pass is the mind's pass push or its turn passing after PASS_AFTER slices on offer, as alone.

The game ends as alone: both pass in a row, or the cap; both seats set back together (Duel.renew, before either mind's tick: a seat
must not wait on a mind that is watching or committed, or the seats would part). No luck: the other is a mind.

The result (for the league's Elo, never shown to a mind: DRIFT.md rule 10): area, each colour's stones and the free points only its
stones surround (GoWorld.area); equal area is a draw (the user, 2026-11-13: "Area, alternate colours", no komi).
"""
from world import BLACK, WAITING, WHITE, GoWorld, other


class GoSeat(GoWorld):
    """A mind's seat in a duel: the board seen from its colour, the other colour's stones the other mind's."""

    def __init__(self, duel, me, seed=0, size=7):
        self.duel = duel   # the game it is in now (a lifelong mind's seat is linked to a new duel for each game: league.py)
        super().__init__(seed=seed, size=size, luck=0.0, me=me)

    def reply(self):
        """The other mind's stone this slice, its pass (None), or WAITING."""
        return self.duel.moves.get((self.duel.clock, self.them), WAITING)

    def act(self, inv=None, hold=False):
        turn, placed = self.turn, self.placed
        diffs = super().act(inv, hold)
        if turn == self.me and self.turn == self.them:   # the mind's turn went: its stone, or its pass, for the other seat this slice
            self.duel.moves[(self.duel.clock, self.me)] = self.last_point if self.placed > placed else None
        return diffs

    def renew(self):
        """A seat is set back only by the duel (Duel.renew), both together."""
        return None

    def begin_again(self):
        GoWorld.renew(self)


class Duel:
    """Two seats, one game. Drive it with step(agents): agents = {colour: SovAgent on that colour's seat}."""

    def __init__(self, seed=0, size=7, seats=None):
        self.moves = {}   # (the duel's slice, colour) -> the point it placed on, or None for its pass
        self.clock = 0    # the duel's own slices (each seat keeps its own count: a lifelong mind's seat goes on across games)
        if seats is None:
            seats = (GoSeat(self, BLACK, seed, size), GoSeat(self, WHITE, seed, size))
        self.seats = {BLACK: seats[0], WHITE: seats[1]}
        for seat in seats:
            seat.duel = self
        assert seats[0].me == BLACK and seats[1].me == WHITE and not seats[0].board() and not seats[1].board()
        self.results = []   # each game: black area, white area, stones placed, slices, and who won ("black", "white", "draw")

    def renew(self):
        if self.seats[BLACK].full:
            g_before = len(self.seats[BLACK].games)
            for seat in self.seats.values():
                seat.begin_again()
            if len(self.seats[BLACK].games) == g_before:   # both passed before any stone: the world records no game (GoWorld.reset
                g = dict(stones=0, black_took=0, white_took=0, black_area=0, white_area=0, slices=0, empty=True)   # only records a game
            else:                                                                                                  # with stones), a draw
                g = self.seats[BLACK].games[g_before]
            winner = "draw" if g["black_area"] == g["white_area"] else (BLACK if g["black_area"] > g["white_area"] else WHITE)
            self.results.append(dict(g, winner=winner))

    def order(self):
        """The side to move acts first in a slice, so the other seat sees its stone the same slice."""
        first = self.seats[BLACK].turn
        return [first, other(first)]

    def check(self):
        """The two seats are one game."""
        b, w = self.seats[BLACK], self.seats[WHITE]
        assert b.board() == w.board(), (self.clock, b.board(), w.board())
        assert (b.turn, b.passes, b.placed, b.unread, b.since_stone) == (w.turn, w.passes, w.placed, w.unread, w.since_stone), self.clock
        # (by point: a lifelong mind's seat names stones with its own counters, so the same stone has a different name in each seat)
        assert {c for c in b.at if b.at[c] in b.coming_apart} == {c for c in w.at if w.at[c] in w.coming_apart}, self.clock

    def end_slice(self):
        """Both seats have acted: they are checked one game, and the duel's slice moves on."""
        self.check()
        for k in [k for k in self.moves if k[0] < self.clock - 2]:   # (moves long answered)
            del self.moves[k]
        self.clock += 1

    def step(self, agents, after=None):
        """One slice: the game set back if it is over, then each mind's tick, the side to move first. after(colour, agent, seat): what
        the run does after a mind's tick (its territory: run.give)."""
        self.renew()
        for colour in self.order():
            agent, seat = agents[colour], self.seats[colour]
            agent.mind.potentials = seat.potentials()
            agent.tick()
            if after is not None:
                after(colour, agent, seat)
        self.end_slice()
