"""The Go force world (go/README.md; the user, 2026-11-11: "let's try 7x7, create a new folder, let's build it, following the principles
that I have laid out as to not 'drift'").

No state machine: the board changes only when a quantity crosses a reserve (civilization/PHYSICS.md, principle 1), as in the tetris
force world (tetris/world.py), which this follows.
- placing: a stone is a PUSH onto a point. A free point has no reserve against it; a point that bears a stone holds (INF). A stone
  that could not hold where it lands (its own group's load would cross its reserve at once, and it would free nothing) isn't on offer.
- a group: stones of one colour side by side are bound (cohesion, as a tetris piece's blocks are), so they stand or leave together. The
  points around a group are its breath; its load is how many of them bear a stone of the other colour; its reserve is CAPACITY, just
  under the number of points around it (a tetris row's reserve is just under the well's width). When every point around it bears, the
  load crosses the reserve and the group comes apart: its stones leave the board, and the points they stood on are free again.
- the stone that lands presses: the loads read after it are those of the other colour's groups. What it frees by taking them is free
  before its own group is read (a stone may land where its only breath is what it takes).

Principle 0: in the slice a stone lands, only the point it lands on changes (and the stone itself comes into view). The sides of the
stones beside it, and a group's load crossing, are read a slice later; the stones of a group that came apart leave the slice after that.
The same holds for the other colour's stones.

What the mind perceives is doings, never state labels, the whole board (carried from tetris: the user, "the mind perceives the whole
well"):
- each point (point_<x>_<y>), the space: `bearing` (a stone rests on it); `free` (nothing on it, and a stone of either colour could
  land and hold there); with the other colour's potential force on the mind's groups there, where it has one (the user, 2026-11-11:
  the potential forces on a group, read where they would land, since a point has the same name every game and a group has none):
  `free_white_pressing`, `free_white_cutting`, `free_white_choking`, `free_white_taking` (a white stone there would take a breath from
  a black group, land between two a black stone would join, leave one a single breath, take one); or, free but with a reserve no stone
  of one colour can cross (the user, 2026-11-11, "do it now"; the eye read as
  a force: the same test that keeps a stone that couldn't hold off offer): `barring_white`, `barring_black` (with white's potential force too: `barring_black_white_taking`),
  `barring_both`. The words are mine. A point inside the mind's group bars white while the group has breath elsewhere; the moment it is the group's
  last breath it reads `barring_black_white_taking` instead (white could land there and take the group; black couldn't hold);
- each stone (black_<k>, white_<n>), by its group's breath (the group's gerund; the user, 2026-11-11: "adding gerunds generally
  helps too because it helps anchor the mind"; as tetris's `aligning`): `breathing` (two or more free points around its group),
  `straining` (one left, and its own colour places next: it can still be answered), `hanging` (one left, and the other colour places
  next: its reserve can be crossed now; Warp chess's free / pressed / hanging, with `straining` my word for the middle one, since
  `pressed` here is a stone's side), or `coming_apart` (its group's load crossed its reserve; it leaves next
  slice). Read on each stone, since groups join and have no lasting name. (First `resting` or `coming_apart` only: a group about to
  come apart could be read only by adding up its stones' sides.)
- each side of a stone (<stone>_up, _down, _left, _right; carried from tetris: the user, "a block reads each side"): `free` (a free
  point beside it: breath), `pressed` (a stone of the other colour, or the board's edge, against it), `binding` (bound to a stone of its
  own colour);
- the mind's hand (`hand`): `holding` (a stone in it: the mind's to place, the board at rest) or `resting`;
- each colour's breath (`black_breath`, `white_breath`; the user, 2026-11-11: "yes, build it, and give black_breath as territory"),
  one lasting object for all of a colour's groups, as tetris's `piece_alignment` is one object for every piece: `breathing` (none of
  its groups is down to one breath), `straining` or `hanging` (one is, as a stone reads it), `coming_apart` (one's load has crossed). A stone's own `hanging` comes before
  its loss, but on a stone named once; this is the same named thing every game, so what follows it can be learned. run.py gives
  `black_breath` as territory with the mind's stones.

Passing is a push (2026-11-11, after trace_seed.py: with every placement on offer threatened by an anti-want, threatened placements
still took the top level, since nothing else was on offer; the other session's reading of the user's ruling that something has to win:
doing nothing competes as a real move, and in Go passing is one). ("pass", "hand", "holding"): the hand lets its stone go unplaced and
the turn goes to the other. It reaches the hand and nothing on the board, so its potential force is QUIET. (First there was no pass
push, "a pass acts on nothing": it acts on the hand.) The hand as an object is my reading.

The mind plays Black and places first. The other colour (the user, 2026-11-11: random replies with a luck dial) places a random legal
stone when its turn comes; with chance `luck` it places the stone best for the mind instead (worth(), my reading), from its own random
source. Luck falls a step each game the mind keeps its stones better: it lost fewer to the other than in the game before (the user,
2026-11-11: "keeping its stones"; reset(), earn()). (First tetris's rule, a capture the mind made and predicted: every capture is
certain a slice ahead and the mind takes any group on offer from its first game, so luck fell from 0.7 to 0.16 in 1,200 slices while
it lost 49, 56 and 49 stones a game.)

Pushes on offer are only the legal ones (as Warp chess's and tetris's): ("place", point, what the stone would meet there) for each
free point a Black stone could hold on, when it is the mind's turn and the board is at rest. A placement is read by the potential
forces it holds on the groups it touches (the user, 2026-11-11: "stop the others; and build it"; a group has forces acting on it and
forces that could: pressing, connecting, cutting, capturing), not by its coordinates alone ("absolute is plain wrong"), the point
kept (the user: keep the point, add the situation): free_<own>_<theirs>_<after>.
- <own>, what it would do to the mind's groups: `alone` (it touches none), `extending` (it binds to one), `joining` (it binds two or
  more into one), `saving` (a group it binds to is down to one breath, and would breathe again);
- <theirs>, what it would do to the other's: `taking` (a group comes apart), `choking` (a group is left one breath), `cutting` (it
  lands between two groups a stone of theirs would have joined), `pressing` (it takes a breath, and the reserve holds), `quiet`;
- <after>, what the stone would be doing once landed, by its group's breath: `breathing` or `hanging`.
The words are mine. (First every placement at a point was one push; then the push carried a count of what was on its four sides,
free_b2_w1_e0, which said what surrounded it and nothing of what it would do.)
Each carries a potential force read from what it reaches
(potentials(), for warpchess's ForceMind; the scale carried from Warp chess, the maze and tetris): HANGING 3 if it would take a group
(no reserve left against it), PRESSED 2 if it presses, chokes or cuts the other colour's groups, QUIET 1 if it reaches none of them.
reaches() names what a placement's force reaches: the point, the stones beside it and their sides facing it.

The stones (the user, 2026-11-11: the mind's given territory is its stones and its captures, as Warp chess's pieces; run.py gives them).
Each stone is a new object from the slice it lands to the slice it leaves (black_<n>, white_<n>, never named again), as a tetris
block is. (First the mind's stones were named by the order placed in a game, the same names each game: "the eighth stone" landed
somewhere else every game, the mind noticed its sides changed since it last saw it, and wants formed on it, e.g. black_8_down_pressed.)
- a stone of the mind's that the other takes is out of view and gone: lost.
- a stone of the other's that the mind takes is the mind's for good: kept (out of view, not gone).
- when the board is set back, the stones on it leave with nothing having taken them: kept too.

My choices where nothing is decided (each can change; README.md lists them): Black for the mind, placing first; turns strictly
alternate; a stone's consequences are given REST slices to land before the next stone, so the other replies the third slice after the
mind's stone; the mind's turn also passes if it does nothing for PASS_AFTER slices on offer; a game ends
when both pass in a row or after CAP stones, and the board is set back empty; a placement that would put the board back as it stood
before the other's last stone isn't on offer (the game's rule against taking straight back; I see no force reading of it); no score
is reported to the mind (DRIFT.md rule 10), the games' counts are for the run's report only.
"""
import random

INF = float("inf")
PUSH = 1.0          # the force of a stone placed
REST = 2            # slices a stone's consequences take to land: its load read, then what came apart leaving
PASS_AFTER = 6      # slices on offer with no stone placed before the mind's turn passes (my number)
LUCK_STEP = 0.02    # how much luck falls for a game the mind lost fewer stones in than the game before (tetris's step)
HANGING, PRESSED, QUIET = 3.0, 2.0, 1.0   # potential forces (warpchess/potential.py's scale)
BLACK, WHITE = "black", "white"
SIDES = (("up", (0, -1)), ("down", (0, 1)), ("left", (-1, 0)), ("right", (1, 0)))


def point(c):
    return f"point_{c[0]}_{c[1]}"


def other(colour):
    return WHITE if colour == BLACK else BLACK


def opportunity(c):
    """White's opportunity force at a point (go/go-design.md, the user, 2026-11-12: the primary objects are the opponent's opportunity
    forces; the mind's territory is where they are dead)."""
    return f"opportunity_{c[0]}_{c[1]}"


NO_KO = {}   # (landing's `before` for a stone imagined with no stone before it to take straight back: the rule is about timing, not
             # whether a stone could live there)
WAITING = object()   # reply(): the other hasn't chosen yet (only a seat in a duel ever says so: goduel.py)
DEAD = ("failing", "hanging")   # an opportunity force's doings that the user ruled dead (2026-11-12: "can't hold or would hang")


class GoWorld:
    still = False   # the other colour places whether or not the mind does
    read_held = ("opportunity_",)   # held by reading only (Territory.update; the user, 2026-11-13, "Held by reading only"): an opportunity is
    # the mind's while dead (run.give), never by a placement's claim on it (Params.reach_claims makes placements claims on it, for attention)
    unclaimable = ("point_", "black_", "white_")   # no one's to claim (SovAgent.perceive), as tetris's cells and blocks: the points, the
    # stones and their sides, each colour's breath. The mind's territory is where White's opportunity forces are dead (opportunity_<x>_<y>,
    # run.give; the user, 2026-11-12: "You don't build territory by placing stones"); first the stones were given, and after that was
    # replaced, the mind's pushes still claimed the stones and points they reached (9 stones, 80 sides, 26 points "mine" in 1,500 slices)
    returns = frozenset()   # objects out of view that come back (SovAgent.can_be): none here; a stone or block that has left never returns,
                            # though one kept isn't lost (the user, 2026-11-11). The maze's positions do come back (no `returns`: its kept)
    gamma = 0.7
    horizon = 6     # the mind's watch spans the other's answer and what it takes (Warp chess's duel: "a mind's watch spans the other
                    # side's answer"): its stone's slice, the loads read, what came apart leaving, then the same three for the reply.
                    # First 3, the mind's own stone only: it filled the breath inside its own group stone by stone, the other took all
                    # 48 stones with its reply, and that fell outside the watch of the stone that had left the group one breath
                    # (trace_boards.py, game 2), so nothing the mind did was followed by the loss

    def __init__(self, seed=0, size=7, luck=0.0, me=BLACK):
        self.seed, self.size = seed, size
        self.me, self.them = me, other(me)   # the mind's colour, and the other's (the two-mind duel seats a mind as either: goduel.py;
                                             # alone, the mind is Black, as before)
        self.rng = random.Random(f"white:{seed}")       # the other's replies
        self.luck, self.luck_rng = luck, random.Random(f"luck:{seed}")   # (its own source, as tetris's)
        self.lucky = 0                       # replies made lucky
        self.earned, self.luck_log = 0, []   # games the mind lost fewer stones in than the one before, and luck after each
        self.cap = 2 * size * size           # stones placed before a game is called (my cap)
        self.objs = {point((x, y)): None for x in range(size) for y in range(size)}
        self.objs["hand"] = None
        self.objs.update({f"{BLACK}_breath": None, f"{WHITE}_breath": None})
        self.objs.update({opportunity((x, y)): None for x in range(size) for y in range(size)})   # the other's opportunity forces
        self.t, self.log, self.diffs, self.games = 0, [], [], []
        self.kept = set()        # stones out of view that aren't gone, with their sides: taken by the mind (its for good), or on the
                                 # board when it was set back
        self.taken = set()       # the other's stones the mind took
        self.next = {BLACK: 0, WHITE: 0}   # each colour's next stone (names never used again)
        self.captures = {BLACK: 0, WHITE: 0}   # stones each colour has taken, over the run
        self.others = set()      # objects in this slice's changes that the other colour's stone changed (the world says who placed)
        self.reset()

    # ---- the board -----------------------------------------------------------------------------------------------------------

    def stone_objs(self, s):
        return [s] + [f"{s}_{side}" for side, _ in SIDES]

    def reset(self):
        if getattr(self, "placed", 0):
            area = self.area()
            self.games.append(dict(stones=self.placed, black_took=self.took[BLACK], white_took=self.took[WHITE],
                                   black_area=area[BLACK], white_area=area[WHITE], slices=self.t - self.game_start))
            if len(self.games) > 1 and self.games[-1][f"{self.them}_took"] < self.games[-2][f"{self.them}_took"]:
                self.earn()   # it kept its stones better than in the game before
            self.games[-1]["luck"] = self.luck
        was = dict(self.__dict__.get("shown", {}))
        for s in list(self.__dict__.get("at", {}).values()):   # the board set back: the stones on it leave, nothing having taken
            self.leave(s, keep=True)                            # them (kept: out of view, not gone)
        self.at = {}              # point (x, y) -> the stone on it
        self.colour = {}          # stone -> its colour (the stones on the board)
        self.coming_apart = set() # stones whose group's load crossed its reserve, leaving next slice
        self.unread = False       # a stone landed last slice: the loads it changed aren't read yet
        self.turn = BLACK
        self.last = None          # the colour of the last stone placed
        self.since_stone = 1      # slices since a stone landed (a slice passes before the first stone: the board set back is perceived)
        self.waited = 0           # slices the mind has been on offer without placing
        self.passes = 0
        self.placed, self.black_placed = 0, 0
        self.took = {BLACK: 0, WHITE: 0}
        self.before_last = None   # the board as it stood before the last stone (for the rule against taking straight back)
        self.lucky_reply = False  # whether the other's last stone was a lucky one
        self.game_start = self.t
        self.full = False
        self.shown = self.read()
        self.set_back = {o for o, st in self.shown.items() if was.get(o) != st} | {o for o in was if o not in self.shown}

    def inside(self, c):
        return 0 <= c[0] < self.size and 0 <= c[1] < self.size

    def beside(self, c):
        return [(c[0] + dx, c[1] + dy) for _, (dx, dy) in SIDES if self.inside((c[0] + dx, c[1] + dy))]

    def reserve(self, c, board=None):
        """The reserve a point has against a stone landing on it: none if it is free; a stone on it holds (INF)."""
        board = self.board() if board is None else board
        return INF if c in board else 0.0

    def board(self):
        return {c: self.colour[s] for c, s in self.at.items()}

    @staticmethod
    def group_of(board, c, beside):
        """The stones bound to the one at c (cohesion: one colour, side by side), and the points around them."""
        col, group, around, todo = board[c], set(), set(), [c]
        while todo:
            x = todo.pop()
            if x in group:
                continue
            group.add(x)
            for n in beside(x):
                if board.get(n) == col:
                    todo.append(n)
                else:
                    around.add(n)
        return group, around

    def crossed(self, board, colour):
        """The groups of a colour whose load crosses their reserve: every point around them bears a stone of the other colour."""
        out, seen = [], set()
        for c, col in board.items():
            if col != colour or c in seen:
                continue
            group, around = self.group_of(board, c, self.beside)
            seen |= group
            load = sum(1 for n in around if n in board)   # (a point around a group that bears, bears the other colour)
            capacity = len(around) - 0.5
            if load > capacity:
                out.append(group)
        return out

    def landing(self, c, colour, board=None, before=None):
        """What follows a stone of `colour` landing on point c: (the board after, the points of the other colour's stones it takes), or
        None if it couldn't land (the point holds), couldn't hold there (its own group's load would cross with nothing freed), or
        would put the board back as it stood before the other's last stone (`before`: that board, when the stone is imagined after
        a reply not yet made; else the world's own record)."""
        if before is None:
            before = self.before_last if self.last == other(colour) else None
        board = dict(self.board() if board is None else board)
        if not PUSH > self.reserve(c, board):
            return None
        board[c] = colour
        taken = set().union(*self.crossed(board, other(colour))) if board else set()
        for x in taken:
            del board[x]
        if any(c in g for g in self.crossed(board, colour)):
            return None
        if before is not None and board == before:
            return None
        return board, taken

    def legal(self, colour):
        """point -> (the board after, the points taken), for every point a stone of this colour could land and hold on."""
        out = {}
        for x in range(self.size):
            for y in range(self.size):
                r = self.landing((x, y), colour)
                if r is not None:
                    out[(x, y)] = r
        return out

    def settled(self):
        """Nothing a stone set going is still to land."""
        return self.since_stone >= REST and not self.coming_apart and not self.unread

    def over(self):
        return self.passes >= 2 or self.placed >= self.cap

    def at_rest(self):
        return self.settled() and not self.over()

    def area(self):
        """Each colour's stones and the free points only its stones surround (for the run's report: never shown to the mind)."""
        board = self.board()
        out = {BLACK: sum(1 for v in board.values() if v == BLACK), WHITE: sum(1 for v in board.values() if v == WHITE)}
        seen = set()
        for x in range(self.size):
            for y in range(self.size):
                c = (x, y)
                if c in board or c in seen:
                    continue
                region, edge, todo = set(), set(), [c]
                while todo:
                    p = todo.pop()
                    if p in region:
                        continue
                    region.add(p)
                    for n in self.beside(p):
                        if n in board:
                            edge.add(board[n])
                        else:
                            todo.append(n)
                seen |= region
                if len(edge) == 1:
                    out[next(iter(edge))] += len(region)
        return out

    # ---- luck (the user: the other's replies lucky for the mind, on a dial) ---------------------------------------------------------

    def worth(self, after, taken, now):
        """How good for the mind the board is after a reply of the other's (my reading of "best for the mind", by liberties): the other's
        stones the mind could take with its next stone less the mind's stones the reply takes, then the breath the mind's groups are
        left with. (First what it could take came before what it lost, and a reply that took the mind's stones while offering its own
        counted as lucky: with random stones for the mind, the other took 2,997 at luck 0.7 against 2,248 at luck 0.)"""
        could = 0
        seen = set()
        for c, col in after.items():
            if col != self.them or c in seen:
                continue
            group, around = self.group_of(after, c, self.beside)
            seen |= group
            free = [n for n in around if n not in after]
            if len(free) == 1 and self.landing(free[0], self.me, after, before=now) is not None:
                could += len(group)
        breath, seen = 0, set()
        for c, col in after.items():
            if col != self.me or c in seen:
                continue
            group, around = self.group_of(after, c, self.beside)
            seen |= group
            breath += sum(1 for n in around if n not in after)
        return (could - len(taken), breath)

    def reply(self):
        """The other's stone: a random legal point; with chance `luck`, the point best for the mind (ties by the luck source). None if
        it has nowhere to place (it passes)."""
        options = self.legal(self.them)
        self.lucky_reply = False
        if not options:
            return None
        choice = self.rng.choice(sorted(options))   # (drawn whether or not luck takes over: the plain replies' source isn't luck's)
        if self.luck and self.luck_rng.random() < self.luck:
            now = self.board()
            scored = {c: self.worth(*options[c], now) for c in sorted(options)}
            top = max(scored.values())
            choice = self.luck_rng.choice([c for c in sorted(options) if scored[c] == top])
            self.lucky += 1
            self.lucky_reply = True
        return choice

    def earn(self):
        """A game the mind lost fewer stones in than the one before: luck falls a step."""
        if self.luck > 0:
            self.earned += 1
            self.luck = max(0.0, round(self.luck - LUCK_STEP, 4))
            self.luck_log.append((self.t, self.luck))

    # ---- what the mind perceives --------------------------------------------------------------------------------------------

    def read_stone(self, s, c):
        out = {}
        col = self.colour[s]
        for side, (dx, dy) in SIDES:
            n = (c[0] + dx, c[1] + dy)
            if not self.inside(n):
                out[f"{s}_{side}"] = "pressed"   # the board's edge
            elif n not in self.at:
                out[f"{s}_{side}"] = "free"
            else:
                out[f"{s}_{side}"] = "binding" if self.colour[self.at[n]] == col else "pressed"
        out[s] = "coming_apart" if s in self.coming_apart else self.doing(self.board(), c)
        return out

    def doing(self, board, c, turn=None):
        """What the stone on point c is doing, by its group's breath: `breathing`; with one free point or none left around its group
        (none only in the slice before what its own stone takes has left), `hanging` if the other colour places next, `straining` if
        its own does. `turn`: who places next (the world's own turn if not given)."""
        _, around = self.group_of(board, c, self.beside)
        if sum(1 for n in around if n not in board) >= 2:
            return "breathing"
        return "hanging" if (self.turn if turn is None else turn) == other(board[c]) else "straining"

    def read(self):
        """The forces reading: every point and every stone on the board with its sides, each by what it is doing."""
        board = self.board()
        out = {point((x, y)): ("bearing" if (x, y) in self.at else self.point_doing((x, y), board))
               for x in range(self.size) for y in range(self.size)}
        out["hand"] = "holding" if self.turn == self.me and self.at_rest() else "resting"
        breath = {BLACK: "breathing", WHITE: "breathing"}
        worse = ("breathing", "straining", "hanging", "coming_apart")
        for c, s in self.at.items():
            out.update(self.read_stone(s, c))
            col = self.colour[s]
            if worse.index(out[s]) > worse.index(breath[col]):
                breath[col] = out[s]   # the colour's breath: its worst-off group's
        out[f"{BLACK}_breath"], out[f"{WHITE}_breath"] = breath[BLACK], breath[WHITE]
        out.update(self.opportunities(board))
        return out

    def opportunity_doing(self, board, c):
        """What White's opportunity force at point c is doing (go/go-design.md; the user, 2026-11-12): read by the physics one reply
        forward, a white stone landing there and Black placing next. `bearing`: a stone is on the point, there is no opportunity;
        `failing`: a white stone couldn't hold there; `hanging`: it would hold with one breath, and a black stone there next would take
        it; `breathing`: it would hold, and Black couldn't take it at once. Dead (DEAD, the user's ruling): failing or hanging. Whether a
        breathing one can truly live is for the mind's SOV to learn, not for the world to say. The words are mine."""
        if c in board:
            return "bearing"
        w = self.landing(c, self.them, board, NO_KO)
        if w is None:
            return "failing"
        after, _ = w
        _, around = self.group_of(after, c, self.beside)
        free = [n for n in around if n not in after]
        if len(free) == 1 and self.landing(free[0], self.me, after, before=board) is not None:
            return "hanging"
        return "breathing"

    def points(self):
        return [(x, y) for x in range(self.size) for y in range(self.size)]

    def opportunities(self, board):
        return {opportunity(c): self.opportunity_doing(board, c) for c in self.points()}

    def states(self, tree=None):
        return dict(self.shown)

    # ---- what the mind can do -----------------------------------------------------------------------------------------------

    def invitations(self, tree=None):
        """The legal placements and the pass, when it is the mind's turn and the board is at rest."""
        if self.turn != self.me or not self.at_rest():
            return []
        board = self.board()
        return [("place", point(c), self.placing(c, board, after, taken))
                for c, (after, taken) in sorted(self.legal(self.me).items())] + [("pass", "hand", "holding")]

    def groups_beside(self, board, c, colour):
        """The groups of a colour with a stone beside point c: [(the group's points, its breath)]."""
        out, seen = [], set()
        for n in self.beside(c):
            if board.get(n) == colour and n not in seen:
                group, around = self.group_of(board, n, self.beside)
                seen |= group
                out.append((group, sum(1 for x in around if x not in board)))
        return out

    def force_on(self, board, c, colour, after, taken):
        """What a stone of `colour` landing on c would do to the other colour's groups: `taking`, `choking` (one left a single
        breath), `cutting` (it lands between two that a stone of theirs would have joined), `pressing`, or `quiet`."""
        if taken:
            return "taking"
        if any(breath == 1 for _, breath in self.groups_beside(after, c, other(colour))):
            return "choking"
        beside = self.groups_beside(board, c, other(colour))
        return "cutting" if len(beside) >= 2 else "pressing" if beside else "quiet"

    def placing(self, c, board, after, taken):
        """A placement of the mind's as the potential forces it holds: free_<what it would do to the mind's own groups>_<what it would do
        to the other's>_<what the stone would be doing once landed>."""
        own = self.groups_beside(board, c, self.me)
        if not own:
            mine = "alone"
        elif any(breath <= 1 for _, breath in own) and self.doing(after, c, self.them) == "breathing":
            mine = "saving"
        else:
            mine = "joining" if len(own) >= 2 else "extending"
        return f"free_{mine}_{self.force_on(board, c, self.me, after, taken)}_{self.doing(after, c, self.them)}"

    def point_doing(self, c, board, before=None):
        """How a free point reads: which colour's stone could land and hold there, and the potential force a white stone there would
        hold on black's groups. `before`: as landing's (the dream passes a board no stone could put back)."""
        b = self.landing(c, self.me, board, before)
        w = self.landing(c, self.them, board, before)
        if w is None:   # (colours by name, the stone's own: the other's, the mind's; alone, the mind is Black, as before)
            return "barring_both" if b is None else f"barring_{self.them}"
        base = "free" if b is not None else f"barring_{self.me}"
        force = self.force_on(board, c, self.them, *w)
        return base if force == "quiet" else f"{base}_{self.them}_{force}"

    def target(self, inv):
        _, x, y = inv[1].split("_")
        return (int(x), int(y))

    def reaches(self, inv):
        """The objects a placement's force reaches: the point, White's opportunity there, the stones beside it and their sides facing it."""
        if inv[0] == "pass":
            return {"hand"}
        if inv[0] != "place":
            return set()
        c = self.target(inv)
        out = {inv[1], opportunity(c)}   # (and White's opportunity at the point: the stone's force takes it, the user, 2026-11-12, "Reach as
        for side, (dx, dy) in SIDES:     # a relation"; Params.reach_relations)
            n = (c[0] + dx, c[1] + dy)
            if n in self.at:
                facing = {"up": "down", "down": "up", "left": "right", "right": "left"}[side]
                out |= {self.at[n], f"{self.at[n]}_{facing}"}
        return out

    def potentials(self):
        """push id -> the force it would exert, read from what it reaches: it would take a group (HANGING), press a stone of the
        other colour whose reserve holds (PRESSED), or reach none (QUIET)."""
        out = {}
        if self.turn != self.me or not self.at_rest():
            return out
        board = self.board()
        for c, (after, taken) in self.legal(self.me).items():
            f = HANGING if taken else PRESSED if any(board.get(n) == self.them for n in self.beside(c)) else QUIET
            out[f"place_push:{point(c)}_{self.placing(c, board, after, taken)}"] = f
        out["pass_push:hand_holding"] = QUIET
        return out

    def potential_effects(self):
        """What the force structure predicts with certainty if nothing more is placed (tetris's potential_effects; the user, 2026-11-10):
        a stone has landed and the loads aren't read yet, so each group of the other colour whose load now crosses its reserve comes apart
        next slice. The structure is read relative to the stone that landed (the user: "absolute is plain wrong"), folded as tetris
        folds a row: p0 the stone that landed, `presser` the other stones of its colour around the group, `group+0:stone` the group's
        stones, `wall_edge` the board's edge where the group touches it. -> [(the effect as the world will show it, slices from now,
        every (a, b) "a has a force on b", the effect relative: a group of which colour)]. (First the effect said whose group, "mine"
        or "theirs": whose a stone is is the territory register's to say, not the world's; its colour is the stone's own.)"""
        if not self.unread or self.last is None:
            return []
        board, out = self.board(), []
        landed = self.last_point
        for group in self.crossed(board, other(self.last)):
            _, around = self.group_of(board, next(iter(group)), self.beside)
            forces = {("p0", "group+0:stone")} if landed in around else set()
            if around - {landed}:
                forces.add(("presser", "group+0:stone"))
            if any(len(self.beside(c)) < 4 for c in group):
                forces.add(("group+0:stone", "wall_edge"))
            whose = other(self.last)
            first = sorted(self.at[c] for c in group)[0]
            out.append((f"{first}_coming_apart", 1, frozenset(forces), f"group+{whose}_coming_apart"))
        return out

    def push_predictions(self):
        """What the forces predict after each placement on offer: White's opportunity forces it would kill (the user, 2026-11-12: the
        mind's territory is where the opponent's opportunity forces are dead, go/go-design.md; a potential effect is a gain in ownership,
        as tetris's clear and ground piece). The physics followed forward as the world will show it: the stone lands (only its point
        changes), the loads are read (the opportunities read with any group it takes still standing), what came apart leaves (read
        again). The other's reply comes after, so it isn't followed: what it does is where a commitment can dissolve.
        The force structure is relative to the stone (the user: "absolute is plain wrong"): p0 the stone placed; `opportunity+0:point`
        the point whose opportunity dies; `presser` the mind's other stones beside that point; `group+white:stone` a white group the
        stone takes, when the point is one of its points; `wall_edge` the board's edge beside the point. The effect relative: how far
        the point is from the stone (steps along the board) and how it dies. The names are mine.
        Also each dead opportunity that would come to life again, or be borne by the stone (opportunity+0_bearing: a placement on a point
        whose opportunity is dead), the same way (the user, 2026-11-12, "Yes, as a loss"): where the mind holds that point its register
        reads a loss (SovAgent.stand_prediction, Params.predicted_losses); the world says only what changes.
        -> [(effect as the world will show it, slices from now, relative force structure, relative effect, (the placement's id,))]."""
        offered = self.invitations()
        if not offered:
            return []
        board = self.board()
        memo = self.__dict__.setdefault("_pp_memo", {})
        key = frozenset(board.items())
        if memo.get("key") != key:
            memo.clear()
            memo["key"] = key
        if "out" in memo:
            return memo["out"]
        out = []
        legal = self.legal(self.me)
        for inv in offered:
            if inv[0] != "place":
                continue
            c = self.target(inv)
            after, taken = legal[c]
            landed = dict(board)
            landed[c] = self.me
            dies = []   # each slice an opportunity reads dead where the slice before it read alive (one can live again while a
            prev = {q: self.shown.get(opportunity(q)) for q in self.points()}   # group it takes still stands, and die again as it leaves)
            for n, b in [(2, landed)] + ([(3, after)] if taken else []):   # (with nothing taken, the third slice reads as the second)
                for q in self.points():
                    doing = self.opportunity_doing(b, q)
                    if doing in DEAD and prev[q] not in DEAD:
                        dies.append((q, n, doing, b))
                    elif prev[q] in DEAD and doing not in DEAD:   # a dead opportunity living again, or borne by the stone itself (the
                        dies.append((q, n, doing, b))              # user, 2026-11-12, "Yes, as a loss": the mind's register reads it as a
                    prev[q] = doing                                # loss where it holds the point; the world only reports the change)
            for q, n, doing, b in dies:
                forces = set()
                near = self.beside(q)
                if c in near or q == c:   # (q == c: the stone lands on the point itself)
                    forces.add(("p0", "opportunity+0:point"))
                if any(b.get(m) == self.me and m != c for m in near):
                    forces.add(("presser", "opportunity+0:point"))
                if q in taken:
                    forces.add(("p0", "group+white:stone"))
                if len(near) < 4:
                    forces.add(("opportunity+0:point", "wall_edge"))
                d = abs(q[0] - c[0]) + abs(q[1] - c[1])
                out.append((f"{opportunity(q)}_{doing}", n, frozenset(forces), f"opportunity+{d}_{doing}",
                            (f"{inv[0]}_push:{inv[1]}_{inv[2]}",)))   # (the placement's whole id, force_world.inv_id: placements share a name)
        memo["out"] = out
        return out

    @staticmethod
    def role_of(node):
        """A node of a force structure (potential_effects): its role kind, and whether it is on the effect's side (the group that
        comes apart, and the edge it is pressed against), as tetris's world says for its own (SovAgent.force_predict reads it)."""
        if node == "wall_edge":
            return "wall", True
        if node.startswith("opportunity+"):   # the point whose opportunity force dies: the effect's side
            return node.split(":", 1)[-1], True
        if node.startswith("group+"):
            return node.split(":", 1)[-1], True
        return ("part" if node == "p0" else node), False

    # ---- a slice ------------------------------------------------------------------------------------------------------------

    def forget(self, s):
        for o in self.stone_objs(s):
            self.objs.pop(o, None)

    def leave(self, s, keep):
        """A stone leaves the board: no longer an object in view. Kept (out of view, not gone) or not."""
        c = next(k for k, v in self.at.items() if v == s)
        del self.at[c]
        del self.colour[s]
        self.forget(s)
        if keep:
            self.kept.update(self.stone_objs(s))
        else:
            self.kept.difference_update(self.stone_objs(s))

    def land(self, c, colour):
        """A stone of this colour lands on point c (its force crosses the point's reserve): only the point changes, and the stone
        comes into view."""
        self.before_last = self.board()
        if self.__dict__.get("dreaming"):   # a dreamed stone: named by its colour and point, never a stone of a real game (dream_go.py)
            s = f"{colour}_at_{c[0]}_{c[1]}"
        else:
            s = f"{colour}_{self.next[colour]}"
            self.next[colour] += 1
        self.black_placed += colour == self.me   # (the mind's stones placed, whatever its colour; the name kept for the reports)
        self.at[c], self.colour[s] = s, colour
        for o in self.stone_objs(s):
            self.objs[o] = None
        self.placed += 1
        self.last, self.last_point, self.since_stone, self.unread = colour, c, 0, True
        self.turn, self.passes, self.waited = other(colour), 0, 0
        return s

    def renew(self):
        if self.full:   # the game is over: the board is set back empty
            self.reset()
            self.diffs = []

    def act(self, inv=None, hold=False):
        """One slice: what followed from the last slice lands first (the loads a landed stone changed are read, and a group whose load
        crossed comes apart; the stones of a group that came apart leave); then a stone lands, the mind's if it placed one and it is
        legal, else the other's when its turn has come and the board is at rest. Every change is a force crossing a reserve."""
        before = dict(self.shown)
        legal = inv is not None and inv in self.invitations()
        theirs = (self.last == self.them and not legal) or bool(self.set_back)   # what changes in this slice follows the other's stone (or
        # the board set back); a slice the mind's stone lands in changes only its point
        landed, passed = None, False
        if self.coming_apart:   # a group whose load crossed its reserve: its stones leave, and the points are free again
            taker = self.last
            for s in sorted(self.coming_apart):
                mine = self.colour[s] == self.me
                self.leave(s, keep=not mine)   # the other's stone the mind took: the mind's for good, out of view and not gone;
                if not mine:                   # the mind's stone the other took: gone
                    self.taken.add(s)
                self.took[taker] += 1
                self.captures[taker] += 1
            self.coming_apart = set()
        elif self.unread:   # the stone that landed presses: the other colour's loads are read
            for group in self.crossed(self.board(), other(self.last)):
                self.coming_apart |= {self.at[c] for c in group}
            self.unread = False
        if inv is not None:
            self.log.append((self.t, inv[1], legal))
        if legal and inv[0] == "pass":   # the mind's pass: the hand lets its stone go unplaced (only the hand changes)
            self.passes += 1
            self.turn, self.waited = self.them, 0
            passed = True
        elif legal:   # the mind's stone
            landed = self.land(self.target(inv), self.me)
        elif self.at_rest() and self.turn == self.them:   # the other's stone, or its pass
            c = self.reply()
            if c is WAITING:   # the other hasn't chosen yet (a mind's turn, in a duel: goduel.py): nothing lands
                pass
            elif c is None:
                self.passes += 1
                self.turn = self.me
            else:
                landed = self.land(c, self.them)
                theirs = True
        elif self.at_rest() and self.turn == self.me:   # on offer and nothing placed: after PASS_AFTER slices the mind has passed
            self.waited += 1
            if self.waited >= PASS_AFTER or not self.legal(self.me):
                self.passes += 1
                self.turn, self.waited = self.them, 0
        if landed is None:
            self.since_stone += 1
        if self.over() and self.settled():   # the game is over once what the last stone set going has landed
            self.full = True
        if landed is not None:   # principle 0: only the point changes, and the stone comes into view; the rest is read next slice
            c = self.last_point
            self.shown = dict(before)
            self.shown[point(c)] = "bearing"
            self.shown.update(self.read_stone(landed, c))
        else:
            self.shown = self.read()
        if passed:
            theirs = False
        self.diffs = [f"{o}: {before.get(o)} -> {st}" for o, st in sorted(self.shown.items()) if before.get(o) != st]
        changed = {o for o, st in self.shown.items() if before.get(o) != st} | self.set_back
        self.others = changed if theirs else set()
        self.set_back = set()
        self.t += 1
        return self.diffs
