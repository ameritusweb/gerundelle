"""The mystery maze (README.md, the user's design), on forces (the user, 2026-11-08: "Each position is an object with a potential force
to walk onto it"; first I built it as a state machine with one walk of the body, a shortcut).

Objects: each position (pos_x_y), each wall (wall_<type>_<x1>_<y1>_<x2>_<y2>, its kind in its identity as a Warp chess piece's), the
body, the controller (its readings: controller_heading, set by the buttons, and controller_distance, the distance gerund), the voice
(the words' doer), the cheese. What the mind perceives is a forces reading (as warpworld's
read_forces), every reading what a thing is doing (the user, 2026-11-08: "STATES ARE SABOTAGE"): the position underfoot "bearing" the
body; in front, a wall "blocking" the way (or "yielding" once a word made it give way), the position beyond an open way "free" (nothing
on it) or "bearing" (the cheese on it), or a border position "blocking"; a position a walk lands on "pressed"; the controller and the
voice "resting", the heading "pointing_<direction>", the distance gerund "decreasing", "increasing" or "holding"; the cheese "resting"
where it lies and "borne" once the body is on it. Each push on offer carries the force it would exert (potentials(), read by warpchess's ForceMind, as potential.py's). Potential forces: walk onto the position in front; the controller's four buttons; the voice's 26 words (each reaching the wall in front). Only what is legal is on offer
(as Warp chess): a walk onto a position a wall seals, or past the edge, isn't; after LOCK slices without a step the buttons and the words
aren't (the user's lock); a word reaches the wall in front and opens it if it is that wall's word. PHYSICS.md Principle 0: in a push's slice only the thing pushed changes; what follows lands next.

The interface a Gerundelle mind reads (as warpchess/warpworld.py's): objs, states(), invitations(), act(inv) -> the changes, diffs,
renew(); still, gamma, horizon; kept (positions out of view aren't gone) and seen_only (objects that only came into or left view).

My choices where the README's questions are open (each can change):
- A word that matches a wall's type opens that wall for good (until the maze is set back); every other word does nothing to it.
- Three wall types, each opened by one word of the 26.
- The maze: a 5x5 perfect maze from the seed; three passages on the way to the cheese are made walls (so a word is needed to get there),
  and every wall inside the maze has a type. The maze is set back only when the cheese is reached.

(The first build, 2026-11-07, was a state machine with no forces: a perceived `ahead`, the walk as a push of a `body`, the position not
perceived, episodes cut at 150 slices. Replaced; the old files are the maze.py.before_* backups.)
"""
import math
import random

WORDS = ["alfa", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india", "juliett", "kilo", "lima", "mike",
         "november", "oscar", "papa", "quebec", "romeo", "sierra", "tango", "uniform", "victor", "whiskey", "xray", "yankee", "zulu"]
HEADINGS = {"north": (0, -1), "east": (1, 0), "south": (0, 1), "west": (-1, 0)}
TYPES = ("a", "b", "c")
SIZE = 5
LOCK = 10        # slices without a step, after which the buttons and the words do nothing (the user)



CELLS = [(x, y) for x in range(SIZE) for y in range(SIZE)]
OUTSIDE = [(x, y) for x in range(-1, SIZE + 1) for y in range(-1, SIZE + 1) if (x, y) not in CELLS and (x in (-1, SIZE)) != (y in (-1, SIZE))]
# the border's positions: perceived as "edge" when in front, never walked onto (first the edge had no position, so facing it nothing was
# perceived in front, and the mind faced the edge for 205 of 225 choices)


def pos(c):
    return f"pos_{c[0]}_{c[1]}"


def wall_id(e, kind):
    a, b = sorted(e)
    return f"wall_{kind}_{a[0]}_{a[1]}_{b[0]}_{b[1]}"


HANGING, PRESSED, QUIET = 3.0, 2.0, 1.0   # potential forces, warpchess/potential.py's scale: onto something with no reserve against it,
                                          # onto something whose reserve holds, or onto nothing


class Maze:
    still = False
    gamma = 0.7
    horizon = 2     # the push's slice, and the slice what follows from it lands in

    def __init__(self, seed=0):
        self.seed, self.rng = seed, random.Random(seed)
        self.opens = dict(zip(TYPES, self.rng.sample(WORDS, len(TYPES))))   # wall type -> the word that opens it
        self.build()
        self.objs = {"controller_heading": None, "controller_distance": None, "cheese": None, "controller": None, "voice": None}
        # the heading and the distance gerund are the controller's readings (the user's design: the buttons set the heading, the distance
        # gerund is on the controller), as a Warp chess piece's _bearing and _exerting are the piece's
        self.objs.update({pos(c): None for c in CELLS + OUTSIDE})
        self.objs.update({wall_id(e, k): None for e, k in self.walls.items()})
        self.kept = {pos(c) for c in CELLS + OUTSIDE} | {wall_id(e, k) for e, k in self.walls.items()}   # out of view isn't gone
        self.t, self.log, self.diffs, self.episodes = 0, [], [], []
        self.reset()

    def build(self):
        """A perfect maze (a passage between every pair of cells a depth-first walk joined), the cheese at the far corner, three passages
        on the way there made walls, and every wall inside the maze given a type."""
        rng = random.Random(self.seed + 1)
        cells = [(x, y) for x in range(SIZE) for y in range(SIZE)]
        passages, seen, stack = set(), {(0, 0)}, [(0, 0)]
        while stack:
            x, y = stack[-1]
            nxt = [(x + dx, y + dy) for dx, dy in HEADINGS.values() if (x + dx, y + dy) in cells and (x + dx, y + dy) not in seen]
            if not nxt:
                stack.pop()
                continue
            c = rng.choice(nxt)
            passages.add(frozenset(((x, y), c)))
            seen.add(c)
            stack.append(c)
        self.start, self.cheese_at = (0, 0), (SIZE - 1, SIZE - 1)
        path = self.route(passages)
        for edge in rng.sample(path, 3):   # made walls on the way: a word is needed to get through
            passages.discard(edge)
        self.passages0 = passages
        self.walls = {}
        for a in cells:
            for dx, dy in HEADINGS.values():
                b = (a[0] + dx, a[1] + dy)
                e = frozenset((a, b))
                if b in cells and e not in passages and e not in self.walls:
                    self.walls[e] = rng.choice(TYPES)

    def route(self, passages):
        """The passages from the start to the cheese (the perfect maze's one way)."""
        prev, todo = {self.start: None}, [self.start]
        while todo:
            c = todo.pop(0)
            for dx, dy in HEADINGS.values():
                n = (c[0] + dx, c[1] + dy)
                if n not in prev and frozenset((c, n)) in passages:
                    prev[n] = c
                    todo.append(n)
        out, c = [], self.cheese_at
        while prev.get(c) is not None:
            out.append(frozenset((c, prev[c])))
            c = prev[c]
        return out

    def reset(self):
        if getattr(self, "slices", 0):
            self.episodes.append((self.got, self.slices))
        self.pos, self.heading, self.got, self.slices = self.start, "east", False, 0
        self.open_now = set(self.passages0)
        self.dist = self.distance(self.pos)
        self.shown = {"controller_heading": f"pointing_{self.heading}", "controller_distance": "holding", "cheese": "resting", "controller": "resting", "voice": "resting"}
        self.shown.update(self.view())
        self.pending = {}
        self.since_walk = 0
        self.idle = 0

    def distance(self, p):
        return math.dist(p, self.cheese_at)

    def front(self):
        dx, dy = HEADINGS[self.heading]
        return (self.pos[0] + dx, self.pos[1] + dy)   # inside, or a position of the border (OUTSIDE)

    def can_step(self, c):
        """The way onto c is open: inside the maze, and no wall between or the wall between open."""
        return c in CELLS and frozenset((self.pos, c)) in self.open_now

    def wall_in_front(self):
        f = self.front()
        e = frozenset((self.pos, f))
        return e if f in CELLS and e in self.walls else None

    def state_of(self, c):
        """What is in front, as one word (for traces): edge, blocking (a closed wall), the cheese, or open."""
        if c not in CELLS:
            return "blocking"
        if not self.can_step(c):
            return "blocking"
        return "bearing" if c == self.cheese_at and not self.got else "free"

    def view(self):
        """The forces reading of what is perceived: underfoot, and in front (a wall, the position beyond an open way, or
        the edge)."""
        f = self.front()
        out = {pos(self.pos): "bearing"}   # (first also a "body" reading, pressing or free: a label of mine, no force; removed)
        e = self.wall_in_front()
        if f not in CELLS:
            out[pos(f)] = "blocking"
        elif e is not None:
            out[wall_id(e, self.walls[e])] = "yielding" if e in self.open_now else "blocking"
        if self.can_step(f):
            out[pos(f)] = "bearing" if f == self.cheese_at and not self.got else "free"
        return out

    def potentials(self):
        """push id -> the force it would exert now (warpchess/potential.py's reading, from what the push reaches): a word onto the closed
        wall in front that has no reserve against it, the wall's own word (hanging, 3); onto a closed wall whose reserve holds against it
        (pressed, 2); a word with nothing to reach, a walk or a button (quiet, 1). The wall's type is perceived this way, through the
        force each word would exert on it (the user, 2026-11-08: "it's perceived through potential force"; first every word read 2 at
        any closed wall, blind to its type)."""
        e = self.wall_in_front()
        closed = e is not None and e not in self.open_now
        out = {}
        for i in self.invitations():
            f = QUIET
            if closed and i[0].startswith("say_"):
                f = HANGING if self.opens[self.walls[e]] == i[0][len("say_"):] else PRESSED
            out[f"{i[0]}_push:{i[1]}_{i[2]}"] = f
        return out

    def reaches(self, inv):
        """The objects a push's force reaches now (what its potential force is read from): a word, the wall in front; a walk, the
        position underfoot it pushes off from and the position in front it lands on; a button, the controller."""
        if inv[0].startswith("say_"):
            e = self.wall_in_front()
            return {wall_id(e, self.walls[e])} if e is not None else set()
        if inv[0] == "walk":   # it pushes off from the position underfoot and lands on the one in front
            return {pos(self.pos), inv[1]}
        return {inv[1]}

    def states(self, tree=None):
        return dict(self.shown)

    def invitations(self, tree=None):
        """What is legal now (as Warp chess offers only legal moves): walk onto the position in front if the way is open; the four
        buttons on the controller; the 26 words, the voice's (the voice is their doer, as a piece is its move's), only with a closed wall
        in front for them to reach (what a word reaches is read in its potential force, potentials()). Buttons and words only while not locked (the user: the lock
        is the move not being offered)."""
        out = []
        f = self.front()
        can_step = self.can_step(f)
        if can_step:
            out.append(("walk", pos(f), self.shown.get(pos(f), self.state_of(f))))
        if self.since_walk < LOCK or not can_step:   # the lock holds only where a step is on offer (the user: then the walk is the
            # only thing on offer, and wins its track); facing a wall or the edge, nothing is locked (first locked there too, and with
            # nothing on offer the episode ended)
            out += [(f"press_{h}", "controller", self.shown["controller"]) for h in HEADINGS]
            e = self.wall_in_front()
            if e is not None and e not in self.open_now:   # a word is on offer only with a closed wall in front for it to reach (as a
                # walk only onto an open position: a potential force acts on something; first offered facing the edge or an open way,
                # and experiments on words took 117 of 300 pushes facing the edge, where they reach nothing; trace_slices_fix.py)
                out += [(f"say_{w}", "voice", self.shown["voice"]) for w in WORDS]
        return out

    def renew(self):
        if self.shown["cheese"] == "borne" and not self.pending and not any(d.startswith("cheese:") for d in self.diffs):
            # (and not while the news of it is still to be perceived: first the reset came at the start of the next tick, before the
            # mind perceived anything, and the cheese never arrived in its records; trace_distance4.py)   # set back only when the cheese is reached (first also after
            # MAX_SLICES slices and after IDLE slices with no move, my imports from the Warp chess worlds' episodes: they cut off what
            # the mind was in the middle of, a chain of sub-wants among it)
            self.reset()
            self.diffs = []

    def later(self):
        """What follows a change of view: next slice, positions leave view or come into it as they now stand."""
        now = self.view()
        for o in list(self.shown):
            if o.startswith(("pos_", "wall_")) and o not in now:
                self.pending[o] = None
        for o, st in now.items():
            if self.shown.get(o) != st:
                self.pending[o] = st

    def act(self, inv=None, hold=False):
        diffs, self.seen_only = [], set()   # objects that only came into or left view this slice (SovAgent.watch: not claimed)
        for o, to in sorted(self.pending.items(), key=lambda x: x[0]):   # what followed the last slice's push lands now
            frm = self.shown.get(o, "unseen")
            if to is None or frm == "unseen":
                self.seen_only.add(o)
            if to is None:
                self.shown.pop(o, None)
                diffs.append(f"{o}: {frm} -> unseen")
            else:
                self.shown[o] = to
                diffs.append(f"{o}: {frm} -> {to}")
        self.pending = {}
        self.slices += 1
        self.since_walk += 1
        legal = inv is not None and inv in self.invitations()
        if inv is not None:
            self.log.append((self.t, inv[0], legal))
        self.idle = 0 if legal else self.idle + 1   # a push not on offer does nothing: the world pushes back
        f = self.front()
        if legal and inv[0] == "walk":   # the step: the position walked onto changes now, the rest next slice
            self.since_walk = 0
            diffs.append(f"{inv[1]}: {self.shown.get(inv[1])} -> pressed")
            self.shown[inv[1]] = "pressed"
            before = self.dist
            self.pos, self.dist = f, self.distance(f)
            if f == self.cheese_at and not self.got:
                self.got = True
                self.pending["cheese"] = "borne"
            d = "decreasing" if self.dist < before else ("increasing" if self.dist > before else "holding")
            self.pending["controller_distance"] = d   # read out every step, changed or the same (the user's design: "every step it
            # either changes or stays the same"); first only a change was read out, so on the last steps to the cheese, all
            # decreasing, nothing about the distance arrived before the cheese
            self.later()
        elif legal and inv[0].startswith("press_"):
            h = inv[0][len("press_"):]
            if h != self.heading:
                diffs.append(f"controller_heading: pointing_{self.heading} -> pointing_{h}")
                self.heading = h
                self.shown["controller_heading"] = f"pointing_{h}"
                self.later()
        elif legal and inv[0].startswith("say_"):
            w = inv[0][len("say_"):]
            e = frozenset((self.pos, f)) if f in CELLS else None
            if e in self.walls and e not in self.open_now and self.opens[self.walls[e]] == w:
                self.open_now.add(e)
                self.later()   # next slice: the wall open, the way beyond it in view
        self.diffs = diffs
        self.t += 1
        return diffs
