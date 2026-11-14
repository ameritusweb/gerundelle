"""The tetris force world (tetris/README.md; the user, 2026-11-09: "build the 'tetris force world' part, keeping with the no finite state
machine rule").

No state machine: the world changes only when a quantity crosses a reserve (civilization/PHYSICS.md, principle 1), never because a
label is switched. Each slice the forces are read and compared with the reserves they meet:
- gravity: the piece's WEIGHT pushes down on the cells under it. A free cell has no reserve against it, so the weight crosses and the
  piece falls a row; a settled block or the floor has a reserve the weight can't cross, so the piece is borne and comes to rest.
- the mind's pushes (shift left, shift right, rotate, drop): a PUSH on the piece. The piece moves only if every cell it would enter
  has no reserve against it (free and inside the well); the walls, the floor and settled blocks hold.
- rows: a row's load is the number of its cells that bear a block; its reserve is CAPACITY, just under the well's width. A full row's
  load crosses it and the row comes apart; every row above loses what bore it and falls a row, as a whole.
- a piece at rest settles into the well (its cells bear); a new piece forms at the top. If the cells it would form in already bear, it
  can't: the well is full (topping out) and the game ends.

Principle 0: in the slice of the mind's push, only the piece (the thing pushed) moves; what follows from it (resting, settling, a row
coming apart, rows falling, a new piece forming) lands in later slices.

Blocks (the user, 2026-11-09: each piece is individual blocks with a force holding them together, so a full row can be perceived;
the cells stay as the space; a block reads each side, and `spanning` when both are pressed). A piece is four blocks bound by cohesion
(`binding`): a push or gravity carries all four through their bonds, or none if any one meets a reserve. When a row comes apart its
blocks leave the well and every bond reaching into it tears (the piece that straddled it parts); the rows above fall a row.

What the mind perceives is doings, never state labels (the user, 2026-11-08: "STATES ARE SABOTAGE"), the whole well (the user):
- each cell (cell_<x>_<y>), the space: `free` (nothing in it), `bearing` (a settled block in it), `carrying` (the falling piece passes
  through it), `pressed` (the piece at rest weighs on it);
- each block (block_<n>): `falling` (in the falling piece), `resting` (settled), `spanning` (settled, pressed on both sides); its sides
  (block_<n>_left, block_<n>_right): `pressed` (a settled block or the wall against it) or `free`; its bond (block_<n>_bond): `binding` (held to
  a block of its piece) or `parted` (every bond torn);
- the piece: `falling`, `resting`, or `forming` (a new piece entering);
- each row (row_<y>): `free` (no cell bears), `holding` (some do), `coming_apart` (its load crossed its reserve).

Pushes on offer are only the legal ones (as Warp chess's), each a potential force read from what it reaches (potentials(), for
warpchess's ForceMind): HANGING 3 if the piece would come to rest there and complete a row (no reserve left in it), PRESSED 2 if it
would come to rest there, QUIET 1 otherwise. reaches() names the cells a push's force reaches (the cells the piece would enter).

The mind's own memory is its own: the world returns a list of changes (diffs) as the other worlds do, but a mind with
Params.self_noticed reads only what it perceives.

My choices where the README's questions are open (each can change): a 10 x 20 well by default; the seven tetromino shapes, in an order
from the seed; a new piece forms at the top centre; the next piece isn't shown; gravity acts every GRAVITY_EVERY slices, in slices
without a push of the mind's (the pushed piece moves by the push in that slice, principle 0); topping out ends the game and the well is
set back (empty).
"""
import random

INF = float("inf")
WEIGHT = 1.0     # the piece's weight: gravity's push down each time it acts
PUSH = 1.0       # the force of each of the mind's pushes on the piece
GRAVITY_EVERY = 2
LUCK_STEP = 0.02   # how much each clear the mind made itself lowers luck (my number: from 0.7, 35 earned clears to none)
RUN_RESERVE = 3.5   # a run's reserve: crossed when at least 4 blocks press side by side (the user's "a row of at least 4")
HANGING, PRESSED, QUIET = 3.0, 2.0, 1.0   # potential forces (warpchess/potential.py's scale)

# the seven shapes, each a list of rotations, each rotation the cells (dx, dy) of its four parts (y grows downward)
SHAPES = {
    "I": [[(0, 1), (1, 1), (2, 1), (3, 1)], [(2, 0), (2, 1), (2, 2), (2, 3)]],
    "O": [[(1, 0), (2, 0), (1, 1), (2, 1)]],
    "T": [[(1, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (2, 1), (1, 2)], [(0, 1), (1, 1), (2, 1), (1, 2)], [(1, 0), (0, 1), (1, 1), (1, 2)]],
    "S": [[(1, 0), (2, 0), (0, 1), (1, 1)], [(1, 0), (1, 1), (2, 1), (2, 2)]],
    "Z": [[(0, 0), (1, 0), (1, 1), (2, 1)], [(2, 0), (1, 1), (2, 1), (1, 2)]],
    "J": [[(0, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (1, 2)], [(0, 1), (1, 1), (2, 1), (2, 2)], [(1, 0), (1, 1), (0, 2), (1, 2)]],
    "L": [[(2, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (1, 2), (2, 2)], [(0, 1), (1, 1), (2, 1), (0, 2)], [(0, 0), (1, 0), (1, 1), (1, 2)]],
}
PUSHES = {"shift_left": (-1, 0, 0), "shift_right": (1, 0, 0), "rotate": (0, 0, 1), "drop": (0, 1, 0)}


def cell(c):
    return f"cell_{c[0]}_{c[1]}"


class TetrisWorld:
    still = False   # gravity acts whether or not the mind pushes
    unclaimable = ("cell_", "block_")   # no one's to claim (SovAgent.perceive): a cell is the open space, filling it is losing space, and
    # a block is what fills it; the mind's territory is the open rows (run.own_open_rows). The user, 2026-11-11: first every cell a push
    # moved the piece into was claimed, and the mind took the tower for its territory and stacked
    returns = frozenset()   # objects out of view that come back (SovAgent.can_be): none here; a stone or block that has left never returns,
                            # though one kept isn't lost (the user, 2026-11-11). The maze's positions do come back (no `returns`: its kept)
    gamma = 0.7
    horizon = 4     # the push's slice and what follows from it: a push that brings the piece to rest where it completes a row is
                    # followed by gravity finding it borne at slice 1 or 2 (gravity acts only in slices without a push), the piece
                    # settling and the row coming apart the slice after, at slice 2 or 3. First 2 slices (the maze's), and that row
                    # came apart outside the push's watch, so no push could be seen to cause it (the user, 2026-11-09)

    def __init__(self, seed=0, width=10, height=20, gravity_every=GRAVITY_EVERY, luck=0.0):
        self.seed, self.rng = seed, random.Random(seed)
        self.luck, self.luck_rng = luck, random.Random(f"luck:{seed}")   # (its own source: the shapes' order is the same at any luck)
        self.lucky = 0   # pieces formed lucky
        self.earned, self.luck_log = 0, []   # clears the mind made itself, and luck after each (the user: luck falls in-game as it earns)
        self.width, self.height, self.gravity_every = width, height, gravity_every
        self.capacity = width - 0.5   # a row's reserve: crossed only when every one of its cells bears
        self.objs = {cell((x, y)): None for x in range(width) for y in range(height)}
        self.objs.update({f"row_{y}": None for y in range(height)})
        self.objs["piece"] = None
        self.objs["piece_alignment"] = None   # the piece's alignment gerund (the user, 2026-11-09), as the maze's distance gerund
        self.t, self.log, self.diffs, self.games = 0, [], [], []
        self.lines = 0
        self.kept = set()   # blocks that left by a clear, with their sides and bond: out of view isn't gone (the user: a clear is the
        # mind's for good, "just like we did in warpchess with capturing pieces"; first their leaving read as a loss, and every clear set
        # anti-wants against the mind's own blocks). A block lost when the well fills is gone
        self.reset()

    # ---- the well -----------------------------------------------------------------------------------------------------------

    def forget(self, b):
        """A block that left the well is no longer an object of this world (nor its sides and bond)."""
        for o in (b, f"{b}_left", f"{b}_right", f"{b}_bond"):
            self.objs.pop(o, None)

    def reset(self):
        if getattr(self, "placed", 0):
            self.games.append((self.placed, self.lines_this_game))
        for b in set(self.__dict__.get("block_at", {}).values()) | set(self.__dict__.get("piece_blocks", [])):
            self.forget(b)   # the well set back empty: its blocks are gone
            if hasattr(self, "kept"):   # and not a loss: what was lost was the open space, row by row (the user, 2026-11-11); first each
                self.kept |= {b, f"{b}_left", f"{b}_right", f"{b}_bond"}   # block read as lost, and anti-wants landed on "resting"
        self.settled = set()           # cells that bear a block
        self.block_at = {}             # settled cell -> the block in it
        self.piece_blocks = []         # the falling piece's blocks, in the order of its parts
        self.bonds = {}                # block -> the blocks it is bound to (cohesion)
        self.piece = None              # (shape, rotation, x, y) or None
        self.doing = "forming"         # what the piece is doing (read off the forces each slice)
        self.coming_apart = set()      # rows whose load crossed their reserve, clearing next slice
        self.piece_of = {}             # block -> the piece it formed in (the user: a run clears whole pieces)
        self.clearing = set()          # pieces a run's load came apart in, clearing next slice
        self.loose = set()             # settled blocks with nothing to hold them, falling on gravity's schedule
        self.cleared_at = {}           # block -> the cell it left when its piece cleared (the space it leaves: the mind's, run.py)
        self.placed, self.lines_this_game = 0, 0
        self.pieces_cleared = 0
        self.since_gravity = 0
        self.shown = {}
        self.form()
        self.alignment = self.align_next = self.aligning()   # read at once when the well is set back (nothing was pushed)
        self.shown = self.read()

    def parts(self, piece=None):
        return set(self.part_list(piece))

    def part_list(self, piece=None):
        """The piece's parts in order (each the cell of one of its blocks)."""
        piece = piece or self.piece
        if piece is None:
            return []
        shape, rot, x, y = piece
        return [(x + dx, y + dy) for dx, dy in SHAPES[shape][rot % len(SHAPES[shape])]]

    def reserve(self, c):
        """The reserve a cell has against the piece entering it: none if it is inside the well and free; the walls, the floor and a
        settled block hold (INF)."""
        x, y = c
        if not (0 <= x < self.width) or y >= self.height or c in self.settled:
            return INF
        return 0.0

    def crosses(self, force, cells):
        """Whether a force on the piece crosses every reserve of the cells it would enter."""
        return all(force > self.reserve(c) for c in cells)

    def moved(self, piece, dx, dy, dr):
        shape, rot, x, y = piece
        return (shape, (rot + dr) % len(SHAPES[shape]), x + dx, y + dy)

    def borne(self, piece=None):
        """Whether the piece is borne: gravity's weight can't cross what lies under it."""
        piece = piece or self.piece
        below = self.parts(self.moved(piece, 0, 1, 0))
        return not self.crosses(WEIGHT, below)

    def worth(self, p):
        """How good the place is where piece p comes to rest falling straight down (the user, 2026-11-11: "the optimal placement is NEXT to a
        piece, not on top of one"): the rows and runs it completes, then how many of its blocks' sides would press against another piece's
        settled blocks (left or right; the walls don't count). First my reading, the free cells it would leave covered and then how full the
        rows it lands in are, and a flat tower top covered nothing: with luck gone, pieces falling on the middle stack were optimal, offered
        nothing, and the mind stacked a tower."""
        cells = self.parts(self.landing(p))
        clears = self.completes(cells)
        beside = sum(1 for (cx, cy) in cells for dx in (-1, 1) if (cx + dx, cy) in self.settled and (cx + dx, cy) not in cells)
        return (clears, beside)

    def places(self, shape, y):
        """Every column and rotation the piece fits in at height y: [(worth, piece)]."""
        out = []
        for rot in range(len(SHAPES[shape])):
            for x in range(-3, self.width):
                p = (shape, rot, x, y)
                if self.crosses(PUSH, self.parts(p)):
                    out.append((self.worth(p), p))
        return out

    def best_place(self, shape):
        """Luck's place for a new piece: the column and rotation, at the top, from which falling straight down lands it best; ties by
        the luck source. None if the piece fits nowhere at the top."""
        options = self.places(shape, 0)
        if not options:
            return None
        top = max(k for k, _ in options)
        return self.luck_rng.choice([p for k, p in options if k == top])

    def optimal(self):
        """Whether the falling piece is in an optimal position: its straight-down landing is as good as any the piece could have from the
        height it is at (the user, 2026-11-09: such a piece has no potential force, whether the mind put it there or luck did)."""
        if self.piece is None:
            return False
        key = (self.piece, frozenset(self.settled))
        if self.__dict__.get("_optimal_key") != key:
            options = self.places(self.piece[0], self.piece[3])
            best = max(k for k, _ in options) if options else None
            self._optimal_key, self._optimal = key, best is not None and self.worth(self.piece) >= best
        return self._optimal

    def landing(self, piece=None):
        """Where the piece would come to rest falling straight down from where it is (its column and rotation as they are)."""
        p = piece or self.piece
        while p is not None and not self.borne(p):
            p = self.moved(p, 0, 1, 0)
        return p

    def aligning(self):
        """The alignment gerund (the user, 2026-11-09: "a gerund for 'aligning' that flips when a piece would eventually clear a row;
        like we had for decreasing in the mysterymaze"): `aligning` if the piece, falling straight down from where it is, would come
        to rest completing a row; `straying` otherwise (my word for the other state). With no piece, as it last read."""
        if self.piece is None:
            return self.__dict__.get("alignment", "straying")
        return "aligning" if self.completes(self.parts(self.landing())) else "straying"   # (a row, or a run that clears pieces)

    def forces_now(self):
        """The force configuration now, as "a has a force on b" (the user, 2026-11-10: the forces are the ground truth): each block of
        the piece on the blocks bonded to it and on the square it is in, its weight on the square under it (or the floor); a settled
        block's weight on the square under it; along a row, each block on the block its side presses against, and the walls."""
        out = set()
        where = dict(self.block_at)
        for b, c in zip(self.piece_blocks, self.part_list()):
            where[c] = b
            out.add((b, cell(c)))
            for o in self.bonds.get(b, ()):
                out.add((b, o))
        for c, b in where.items():
            below = (c[0], c[1] + 1)
            out.add((b, "floor" if below[1] >= self.height else cell(below)))
            for side, dx in (("left", -1), ("right", 1)):
                n = (c[0] + dx, c[1])
                if not (0 <= n[0] < self.width):
                    out.add((b, f"wall_{side}"))
                elif n in self.block_at and c in self.block_at:
                    out.add((b, self.block_at[n]))
        return out

    def simulation(self):
        """A copy of the world's own state to follow its forces forward (potential_effects, effects_after): nothing of the mind in it."""
        import copy
        sim = object.__new__(type(self))
        own = ("settled", "block_at", "piece_blocks", "bonds", "piece", "doing", "coming_apart", "placed", "lines_this_game", "lines",
               "since_gravity", "shown", "alignment", "align_next", "next_block", "width", "height", "gravity_every", "capacity",
               "rng", "luck_rng", "lucky", "seed", "t", "full", "piece_of", "clearing", "loose", "pieces_cleared", "cleared_at",
               "lucky_piece", "pushed_piece", "earned", "luck_log", "free_clear", "made_clears")
        sim.__dict__.update({k: copy.deepcopy(self.__dict__[k]) for k in own if k in self.__dict__})
        sim.objs, sim.log, sim.games, sim.diffs, sim.kept = dict(self.objs), [], [], [], set()
        sim.luck = 0.0
        return sim

    def effects_after(self, inv=None, limit=60):
        """What the forces bring about if this push is made now (None: no push) and then nothing more is pushed, until the piece has come
        to rest and settled (and what that clears has cleared): the facts that end up different from now, as the world will show them.
        Ground truth, as potential_effects is (the user, 2026-11-11: waiting carries the loss the forces predict)."""
        if self.piece is None:
            return frozenset()
        before = dict(self.shown)
        sim = self.simulation()
        blocks = list(self.piece_blocks)
        TetrisWorld.act(sim, inv if inv is not None and inv in self.invitations() else None)
        for _ in range(limit):
            if sim.piece is not None and sim.piece_blocks != blocks and not sim.coming_apart and not sim.clearing and not sim.loose:
                break
            TetrisWorld.act(sim, None)
        return frozenset(f"{o}_{st}" for o, st in sim.shown.items() if before.get(o) != st)

    def potential_effects(self, pushes=(), limit=60):
        """The potential effects the force structure predicts with certainty if nothing pushes (the user, 2026-11-10): the world's own
        physics followed forward from now, with no push, until the piece has come to rest and settled. The force structure is read
        relative to the piece (the user: "absolute is plain wrong"), so the same structure anywhere in the well is the same structure:
        the piece's blocks are p0-p3 (its parts); each part has a force on the part bonded to it, and on what is under it as it falls
        and when it rests, by kind (below_free, below_own, below_settled, floor); the row it completes is row+<k>, k rows up from the
        piece's lowest part, and that row's blocks press on one another out to the walls, each named as the part it is or as a
        settled block of that row (row+<k>:settled; how many, like how far the piece fell, isn't part of the structure). -> [(the effect as the world shows it, slices from now, the relative
        force structure: every (a, b) "a has a force on b", the effect relative to the piece)].
        pushes: a sequence of pushes made first, one a watch (horizon) apart, gravity acting between, as the mind makes them (the user,
        2026-11-12: you use a force to rotate it, then predict the new force configuration); one not legal when it comes predicts nothing."""
        if self.piece is None:
            return []
        sim = self.simulation()   # the world's own state only (first everything in its __dict__, and that held the agent noticing it)
        blocks = list(self.piece_blocks)
        pending = list(pushes)
        part = {b: f"p{k}" for k, b in enumerate(blocks)}
        structure, out, landed = set(), [], None
        grounded = False
        for n in range(1, limit + 1):
            if sim.piece is not None and sim.piece_blocks == blocks:   # the piece's forces: on the parts bonded to it, and under it
                cells = sim.part_list()
                for b, c in zip(blocks, cells):
                    for o in sim.bonds.get(b, ()):
                        structure.add((part[b], part[o]))
                    below = (c[0], c[1] + 1)
                    kind = ("floor" if below[1] >= sim.height else "below_own" if below in cells else
                            "below_settled" if below in sim.settled else "below_free")
                    structure.add((part[b], kind))
                landed = cells
            if pending and (n - 1) % self.horizon == 0:   # the next push of the sequence, a watch after the last
                inv = (pending.pop(0), "piece", sim.shown.get("piece", sim.doing))
                if inv not in sim.invitations():
                    return []
                TetrisWorld.act(sim, inv)
            else:
                TetrisWorld.act(sim, None)
            for y in sorted(sim.coming_apart):   # the row it completes: each block on the next, wall to wall
                if landed is None:
                    continue
                k = max(c[1] for c in landed) - y
                name = lambda x: part.get(sim.block_at.get((x, y)), f"row+{k}:settled")   # (a chain folded, as the fall is: first each
                # block by its column relative to the piece, and how far the row reached each wall made every structure different)
                across = {(name(0), "wall_left"), (name(sim.width - 1), "wall_right")}
                for x in range(sim.width - 1):
                    across |= {(name(x), name(x + 1)), (name(x + 1), name(x))} - {(name(x), name(x))}
                out.append((f"row_{y}_coming_apart", n, frozenset(structure | across), f"row+{k}_coming_apart"))
            if sim.clearing and landed is not None:
                for y, x0, x1, pieces in sim.runs():   # a run that clears pieces: each block on the next along it (the user, 2026-11-10)
                    if not pieces & sim.clearing:
                        continue
                    k = max(c[1] for c in landed) - y
                    run = [sim.block_at[(x, y)] for x in range(x0, x1 + 1)]
                    name = lambda b: part.get(b, f"run+{k}:other" if sim.piece_of.get(b) in pieces else f"run+{k}:settled")
                    across = set()
                    for a_, b_ in zip(run, run[1:]):
                        across |= {(name(a_), name(b_)), (name(b_), name(a_))} - {(name(a_), name(a_))}
                    shows = sorted((b for b in run if sim.piece_of.get(b) in pieces), key=lambda b: (b not in part, b))
                    if shows:   # the effect as the world will show it: a block of a piece coming apart (the piece's own if it is one)
                        effect = (f"{shows[0]}_coming_apart", n, frozenset(structure | across), f"run+{k}_coming_apart")
                        if effect[0] not in {e[0] for e in out}:
                            out.append(effect)
            if not grounded and landed is not None and (sim.piece is None or sim.piece_blocks != blocks):
                # the piece has settled. If it rests on the well's floor, that is a potential effect too: a gain in ownership, as a
                # clear is (the user, 2026-11-12: "a prediction SOV is for a 'potential effect' like a gain in ownership, which includes
                # a clear AND a ground piece"; a piece that touches ground level is the mind's territory, run.own_ground). As the world
                # will show it: the floor cell under its first part there, bearing. (First only clears were potential effects, and the
                # mind had no reason to bring a piece to the ground unless it cleared on the way.)
                grounded = True
                on_floor = sorted(c for c in landed if c[1] == sim.height - 1)
                if on_floor:
                    out.append((f"{cell(on_floor[0])}_bearing", n, frozenset(structure), "ground_bearing"))
            if sim.piece is not None and sim.piece_blocks != blocks:   # a new piece formed: what this one does is done
                break
        return out

    def push_predictions(self):
        """What the forces predict after each sequence of pushes that can bring the falling piece to a place it would gain ownership from:
        a clear, or coming to rest on the floor (the user, 2026-11-12: a potential effect is a gain in ownership, a clear and a ground
        piece alike). First: to a place it would clear from (the user,
        2026-11-12: the prediction SOV, not a gerund, says which push leads toward a clear): every count of rotations, then every shift
        left or right, that the piece can make from where it is; for those whose landing would complete a row or a run, the forces followed
        forward after them (potential_effects). -> [(effect, slices from now, relative force structure, relative effect, the pushes)]."""
        if self.piece is None or self.doing != "falling":
            return []
        memo = self.__dict__.setdefault("_pp_memo", {})
        key0 = frozenset(self.settled)
        if memo.get("key") != key0:
            memo.clear()
            memo["key"] = key0
        shape = self.piece[0]
        out, seen = [], set()
        for r in range(len(SHAPES[shape])):
            for dx in range(-self.width, self.width + 1):
                chain = ["rotate"] * r + (["shift_left"] * -dx if dx < 0 else ["shift_right"] * dx)
                if not chain:
                    continue
                p, ok = self.piece, True
                for name in chain:   # (each step must be one the piece can make)
                    q = self.moved(p, *PUSHES[name])
                    if not self.crosses(PUSH, self.parts(q)):
                        ok = False
                        break
                    p = q
                if not ok:
                    continue
                land = (p[0], p[1] % len(SHAPES[shape]), p[2])
                if land not in memo:   # (where it lands depends only on the column and rotation while the well stands): a landing that
                    rest = self.parts(self.landing(p))   # clears, or that rests on the floor (a ground piece: the mind's territory)
                    memo[land] = self.completes(rest) > 0 or any(c[1] == self.height - 1 for c in rest)
                if not memo[land] or land in seen:
                    continue
                seen.add(land)
                for effect, n, forces, rel in self.potential_effects(chain):
                    out.append((effect, n, forces, rel, tuple(chain)))
        return out

    # ---- runs that clear pieces (the user, 2026-11-10) -----------------------------------------------------------------------------

    def runs(self, block_at=None, piece_of=None):
        """Runs that clear pieces (the user, 2026-11-10: "If there is a row of at least 4, with at least two blocks of one tetrimino and
        two blocks of another tetrimino, then that 'clears' both pieces"). A run is blocks side by side in a row, each pressing the next;
        its load (how many) crosses its reserve (RUN_RESERVE, just under 4) when it holds at least 4. Its pieces with at least two blocks
        in it come apart if there are at least two such pieces. -> [(row, first column, last column, the pieces it clears)]."""
        block_at = self.block_at if block_at is None else block_at
        piece_of = self.piece_of if piece_of is None else piece_of
        out = []
        for y in range(self.height):
            x = 0
            while x < self.width:
                if (x, y) not in block_at:
                    x += 1
                    continue
                x0 = x
                while x < self.width and (x, y) in block_at:
                    x += 1
                if x - x0 > RUN_RESERVE:
                    count = {}
                    for cx in range(x0, x):
                        p = piece_of.get(block_at[(cx, y)])
                        count[p] = count.get(p, 0) + 1
                    pieces = {p for p, n in count.items() if p is not None and n >= 2}
                    if len(pieces) >= 2:
                        out.append((y, x0, x - 1, pieces))
        return out

    def completes(self, cells):
        """What the piece completes resting on these cells: the rows it fills, plus the runs that would clear its piece (each counted)."""
        after = self.settled | set(cells)
        rows = sum(1 for y in {c[1] for c in cells} if self.row_load(y, after) > self.capacity)
        block_at = dict(self.block_at)
        piece_of = dict(self.piece_of)
        for k, c in enumerate(cells):
            block_at[c] = f"new_{k}"
            piece_of[f"new_{k}"] = "new"
        return rows + sum(1 for _, _, _, pieces in self.runs(block_at, piece_of) if "new" in pieces)

    def unsupported(self):
        """The settled blocks with nothing to hold them: groups bound by cohesion (bonds) none of whose blocks rests on the floor or on a
        block that is held. Read up from the floor: held is what rests on the floor or on what is held."""
        cell_of = {b: c for c, b in self.block_at.items()}
        groups, seen = [], set()
        for b in self.block_at.values():
            if b in seen:
                continue
            group, todo = set(), [b]
            while todo:
                x = todo.pop()
                if x in group or x not in cell_of:
                    continue
                group.add(x)
                todo += [o for o in self.bonds.get(x, ()) if o in cell_of]
            seen |= group
            groups.append(group)
        held = set()
        changed = True
        while changed:
            changed = False
            for g in groups:
                if g <= held:
                    continue
                for x in g:
                    cx, cy = cell_of[x]
                    under = self.block_at.get((cx, cy + 1))
                    if cy + 1 >= self.height or (under is not None and under not in g and under in held):
                        held |= g
                        changed = True
                        break
        return {b for g in groups for b in g} - held

    @staticmethod
    def role_of(node):
        """A node of a force structure (potential_effects): its role kind, and whether it is on the effect's side (the row or run that
        comes apart, and the walls it presses). The kinds are the ones Gerundelle first worked out from these names itself (the parts alike,
        a row's settled blocks alike, the two walls alike, what is under a part by what it is); kept exactly, so a run is the same run.
        (One quirk kept with them: a run's blocks keep their row offset in their kind, run+0:other, where a row's don't.)"""
        if node[:1] == "p" and node[1:].isdigit():
            return "part", False
        side = node.startswith(("row+", "run+", "wall_"))
        if node.startswith("row+"):
            return node.split(":", 1)[-1], side
        return ("wall" if node.startswith("wall_") else node), side

    def row_load(self, y, settled=None):
        settled = self.settled if settled is None else settled
        return sum(1 for x in range(self.width) if (x, y) in settled)

    def form(self):
        """A new piece forms at the top centre, if the cells it would form in hold nothing (else the well is full)."""
        shape = self.rng.choice(sorted(SHAPES))
        piece = (shape, 0, self.width // 2 - 2, 0)
        self.lucky_piece, self.pushed_piece = False, False
        if self.luck and self.luck_rng.random() < self.luck:   # luck (the user, 2026-11-09: "randomly initially placing a tetrimino in
            best = self.best_place(shape)                       # the optimal place like 'luck', on a dial until it starts learning")
            if best is not None:
                piece = best
                self.lucky += 1
                self.lucky_piece = True
        if self.crosses(PUSH, self.parts(piece)):
            self.piece, self.doing = piece, "falling"
            self.free_clear = self.completes(self.parts(self.landing(piece))) > 0   # would it clear with no push at all?
            n0 = self.__dict__.get("next_block", 0)
            ids = [f"block_{n0 + k}" for k in range(4)]
            self.next_block = n0 + 4
            for b in ids:
                self.piece_of[b] = n0 // 4
            cells = self.part_list(piece)
            for k, b in enumerate(ids):   # bound to each block of the piece it touches (cohesion)
                self.bonds[b] = {ids[j] for j, c in enumerate(cells) if j != k and abs(c[0] - cells[k][0]) + abs(c[1] - cells[k][1]) == 1}
                for o in (b, f"{b}_left", f"{b}_right", f"{b}_bond"):
                    self.objs[o] = None
            self.piece_blocks = ids
            return True
        self.piece, self.doing = None, "forming"
        return False

    # ---- what the mind perceives --------------------------------------------------------------------------------------------

    def read(self):
        """The forces reading: every cell, every row and the piece, each by what it is doing."""
        out = {}
        mine = self.parts()
        for y in range(self.height):
            for x in range(self.width):
                c = (x, y)
                if c in self.settled:
                    out[cell(c)] = "bearing"
                elif c in mine:
                    out[cell(c)] = "pressed" if self.doing == "resting" else "carrying"
                else:
                    out[cell(c)] = "free"
            load = self.row_load(y)
            out[f"row_{y}"] = "coming_apart" if y in self.coming_apart else ("holding" if load else "free")
        out["piece"] = self.doing
        out["piece_alignment"] = self.alignment
        where = dict(self.block_at)
        for b, c in zip(self.piece_blocks, self.part_list()):
            where[c] = b
        for c, b in where.items():   # each block: what it does, each side, its bond
            falling = b in self.piece_blocks
            sides = {}
            for side, dx in (("left", -1), ("right", 1)):
                n = (c[0] + dx, c[1])
                sides[side] = "pressed" if not (0 <= n[0] < self.width) or n in self.block_at else "free"   # a settled block or the wall
                # (first any block, and a falling block passing by made a row read as spanning before the piece came to rest)
                out[f"{b}_{side}"] = sides[side]
            out[b] = ("coming_apart" if self.piece_of.get(b) in self.clearing else
                      "falling" if (falling and self.doing == "falling") or b in self.loose else
                      "spanning" if sides["left"] == sides["right"] == "pressed" else "resting")
            out[f"{b}_bond"] = "binding" if self.bonds.get(b) else "parted"
        return out

    def states(self, tree=None):
        return dict(self.shown)

    # ---- what the mind can do -----------------------------------------------------------------------------------------------

    def target(self, name):
        dx, dy, dr = PUSHES[name]
        return self.moved(self.piece, dx, dy, dr)

    def invitations(self, tree=None):
        """The legal pushes on the falling piece: those whose force crosses the reserves of every cell the piece would enter."""
        if self.piece is None or self.doing != "falling":
            return []
        if self.luck > 0 and self.optimal():   # a piece in an optimal position has no potential force (the user): gravity carries it in;
            return []                          # with luck gone, pushes are always on offer (the user, 2026-11-11: "always have pushes on
                                               # offer at luck of 0"; first a piece with nothing to be next to was optimal anywhere)
        return [(name, "piece", self.shown.get("piece", self.doing)) for name in PUSHES
                if self.crosses(PUSH, self.parts(self.target(name)))]

    def reaches(self, inv):
        """The objects a push's force reaches: the cells the piece would enter."""
        if self.piece is None or inv[0] not in PUSHES:
            return set()
        return {cell(c) for c in self.parts(self.target(inv[0])) if c[1] >= 0}

    def potentials(self):
        """push id -> the force it would exert, read from what it reaches: if the piece would come to rest there and complete a row
        (HANGING), come to rest there (PRESSED), or neither (QUIET)."""
        out = {}
        for inv in self.invitations():
            p = self.target(inv[0])
            f = QUIET
            if self.borne(p):
                f = HANGING if self.completes(self.parts(p)) else PRESSED   # (a row, or a run that clears pieces)
            out[f"{inv[0]}_push:{inv[1]}_{inv[2]}"] = f
        return out

    # ---- a slice ------------------------------------------------------------------------------------------------------------

    def earn(self):
        """A clear the mind made and predicted (run.py reads both): luck falls a step (the user: in-game, as the mind gets better)."""
        if self.luck > 0:
            self.earned += 1
            self.luck = max(0.0, round(self.luck - LUCK_STEP, 4))
            self.luck_log.append((self.t, self.luck))

    def next_clear(self):
        """All held again: rows and runs whose load crosses their reserve come apart (a cascade), or else a new piece forms."""
        self.coming_apart = {y for y in range(self.height) if self.row_load(y) > self.capacity}
        self.clearing = {p for _, _, _, pieces in self.runs() for p in pieces}
        if not self.coming_apart and not self.clearing and self.piece is None:
            if not self.form():
                self.full = True

    def renew(self):
        if self.__dict__.get("full"):   # the well filled: the game is over, the well is set back
            self.full = False
            self.reset()
            self.diffs = []

    def act(self, inv=None, hold=False):
        """One slice: what followed from the last slice lands first (a row coming apart clears and the rows above fall; a piece at rest
        settles; a new piece forms); then the mind's push on the piece, if it is legal (only the piece moves); else gravity, on its
        schedule. Every change is a force crossing a reserve."""
        before = dict(self.shown)
        self.alignment = self.__dict__.get("align_next", self.alignment)   # the alignment as the last slice left the piece (Principle 0:
        # in a push's slice only the piece moves; the gerund follows in the next slice, as the maze's distance gerund does)
        if self.coming_apart or self.clearing:   # rows whose load crossed their reserve: they clear, every row above falls one row
            cleared = self.__dict__.setdefault("cleared_log", [])   # (slice, rows cleared, blocks cleared): the mind's for good (run.own_clears)
            cleared.append((self.t, frozenset(f"row_{y}" for y in self.coming_apart),
                            frozenset(b for (cx, cy), b in self.block_at.items() if cy in self.coming_apart or self.piece_of.get(b) in self.clearing)))
            for y in sorted(self.coming_apart):
                gone = {b for (cx, cy), b in self.block_at.items() if cy == y}
                for b in gone:   # its blocks leave the well; every bond reaching into the row tears
                    for o in self.bonds.pop(b, set()):
                        self.bonds.get(o, set()).discard(b)
                    self.kept |= {b, f"{b}_left", f"{b}_right", f"{b}_bond"}
                    self.forget(b)   # and they are no longer objects of this world (first they stayed in objs for good)
                self.settled = {(cx, cy + 1) if cy < y else (cx, cy) for (cx, cy) in self.settled if cy != y}
                self.block_at = {((cx, cy + 1) if cy < y else (cx, cy)): b for (cx, cy), b in self.block_at.items() if cy != y}
            n = len(self.coming_apart)
            self.lines += n
            self.lines_this_game += n
            self.coming_apart = set()
            gone = {b for b in self.block_at.values() if self.piece_of.get(b) in self.clearing}   # pieces a run came apart in leave whole
            for c, b in list(self.block_at.items()):
                if b in gone:
                    self.cleared_at[b] = c
                    del self.block_at[c]
                    self.settled.discard(c)
            for b in gone:
                for o in self.bonds.pop(b, set()):
                    self.bonds.get(o, set()).discard(b)
                self.forget(b)
                self.kept |= {b, f"{b}_left", f"{b}_right", f"{b}_bond"}
            self.pieces_cleared += len(self.clearing)
            self.clearing = set()
            self.loose = self.unsupported()   # what nothing holds now falls (the user: blocks above fall)
            if not self.loose:
                self.next_clear()
        elif self.loose:   # loose blocks fall a row each time gravity acts, each bound group as a whole, until all are held
            self.since_gravity += 1
            if self.since_gravity >= self.gravity_every:
                self.since_gravity = 0
                moved = {b: (c[0], c[1] + 1) for c, b in self.block_at.items() if b in self.loose}
                self.block_at = {c: b for c, b in self.block_at.items() if b not in self.loose}
                self.block_at.update({c: b for b, c in moved.items()})
                self.settled = set(self.block_at)
                self.loose = self.unsupported()
                if not self.loose:
                    self.next_clear()
        elif self.doing == "resting":   # the piece at rest settles into the well; rows whose load crosses their reserve come apart
            self.settling_cells = self.part_list()
            self.settling_piece = self.piece_of.get(self.piece_blocks[0]) if self.piece_blocks else None
            self.settled |= self.parts()
            for b, c in zip(self.piece_blocks, self.part_list()):
                self.block_at[c] = b
            self.piece_blocks = []
            self.placed += 1
            self.piece = None
            self.coming_apart = {y for y in range(self.height) if self.row_load(y) > self.capacity}
            self.clearing = {p for _, _, _, pieces in self.runs() for p in pieces}   # runs whose load crossed their reserve
            settled_piece = self.__dict__.get("settling_piece")
            made = any(c[1] in self.coming_apart for c in self.__dict__.get("settling_cells", ())) or settled_piece in self.clearing
            if made and self.__dict__.get("pushed_piece") and not self.__dict__.get("free_clear"):
                # a clear the mind's pushes made: the piece falling straight down from where it formed would not have cleared. Recorded as
                # the facts that will show it; luck falls only when the mind also predicted it (earn(); the user, 2026-11-11: "clears it
                # predicted"; first every such clear lowered luck, and random pushes made 35 in 20,000 slices)
                facts = {f"row_{y}_coming_apart" for y in self.coming_apart}
                facts |= {f"{b}_coming_apart" for b, pc in self.piece_of.items() if pc in self.clearing and b in self.block_at.values()}
                self.__dict__.setdefault("made_clears", set()).update(facts)
                self.__dict__.setdefault("made_events", []).append(frozenset(facts))   # each made clear once (run.earn_luck: one step per clear)
                self.__dict__.setdefault("made_log", []).append(self.t)   # (made; luck_log holds only what was earned: first both there)
            self.doing = "forming"
        elif self.piece is None:   # a new piece forms, if it can
            if not self.form():
                self.full = True
        legal = inv is not None and inv in self.invitations()
        if inv is not None:
            self.log.append((self.t, inv[0], legal))
        if legal:   # the mind's push: its force crosses the reserves of the cells the piece enters
            self.piece = self.target(inv[0])
            self.pushed_piece = True
        elif self.piece is not None and self.doing == "falling":
            self.since_gravity += 1
            if self.since_gravity >= self.gravity_every:   # gravity acts
                self.since_gravity = 0
                if self.borne():          # the weight can't cross what lies under: the piece comes to rest
                    self.doing = "resting"
                else:                     # nothing holds under it: it falls a row
                    self.piece = self.moved(self.piece, 0, 1, 0)
        self.shown = self.read()
        self.align_next = self.aligning()   # read next slice
        self.diffs = [f"{o}: {before.get(o)} -> {st}" for o, st in sorted(self.shown.items()) if before.get(o) != st]
        self.t += 1
        return self.diffs

