"""The clean code force world (PLAN.md, CONTROL_FLOW.md; the user, 2026-11-14: "the force structure and gerunds make up the code
structure"): a program in the clean code language (graph.py) behind the interface a Gerundelle mind reads, as go/world.py and
tetris/world.py put their boards. The mind turns wheels; nothing else moves (a still world).

A push: one connection's wheel turned one step, forward or back (the user: "You can exert a force to change the operation to either the
one in front directly, or behind directly"). Every connection's two pushes are on offer whenever a problem is open: ("turning_forward" |
"turning_back", conn_<c>, the operation it does now).

Resting is a push too (go/world.py's pass, the ruling there that something has to win, so doing nothing competes as a real move):
("resting", "hands", "holding"). It turns no wheel and reaches only the mind's hands, so its potential force is QUIET. Found on rung 0
(trace_settle.py, seed 0): with only the two turns on offer, a mind that had lived "turning back from halving causes the tests to fail"
three times, with its anti-want threatening both turns, still turned, since one of them always won. The hands as an object are mine.

Time territory (the user, 2026-11-14: "'time territory'. Where you gain territory each tick that you are correct or 'winning'"; correct
is everything held, tests, compile errors, lint and clean, and a tick gained is kept for good, both confirmed by the user): each slice
in which no wheel turns and every territory gerund holds, a new object comes into view, tick_<n> `gained`; the slice after, it leaves
view, kept (not gone), as Go's taken stones are. run.give holds each for good. Resting while everything holds is predicted to gain the
next tick (push_predictions, a slice on), a turn after which everything holds to gain one two slices on (the turn, then the read), and
with nothing pushed the forces predict it too (potential_effects): the relative effect `time+0_gained`, the force structure
p0 -> `time+0:tick`. Found on rung 0 (trace_settle.py, seed 0): with no gain in staying correct, a turn that broke every test was the
strongest force on offer (HANGING), and the mind turned away from a solved wheel again and again.

Principle 0 (civilization/PHYSICS.md): in the slice a wheel turns, only that connection changes (conn_<c>, its operation); what the new
operation does to the values, and so to every gerund, is read a slice later. The world never says what a change is worth (DRIFT.md rule
10): it reads the program's gerunds (graph.read), and run.py gives the territory gerunds as the mind's (PLAN.md, Territory).

What the mind perceives: every object graph.read names, each with its doing:
- conn_<c>: the operation (`adding_2`, `passing`, `taking_max`, ...);
- test_<problem>_<k>: `passing` or `failing`; output_<problem>_<k>: what a failing test gave (`giving_7`, `giving_nothing`), `passing` while it passes (the
  user: "pass/fail per test, plus the output value on failure only"); wanted_<k>: what the test wants (`wanting_9`; my reading);
- the compile errors, one gerund each (the user): sign_<c> (`keeping_sign`, `going_negative`), divisor_<c> on a join (`holding`,
  `dividing_by_zero`), range_<k> (`passing`, `failing`: its range hidden), overflow_<n> on a loop (`contained`, `overflowing`);
- lint_cancel_<c>, lint_dominated_<c>_first / _second, lint_deadloop_<n>, lint_deadpath_<n>_<side>: `quiet` or `firing`;
- clean_<c> on a single path: `empty` (passing), `needed`, `spare` (graph.clean, my reading);
- cond_<n> (`resisting_<units>`), path_<n>_over / _hold (`flowing`, `blocked`): a loop's or a branch's condition and paths.

Potential forces (ForceMind, warpchess/potential.py; the scale carried from Warp chess, the maze, tetris and Go): a push is HANGING if it
would flip some territory gerund (a reserve crossed), PRESSED if it would change some test's output but flip none, QUIET if it would
change no output. Read from the program run, never from what the change is worth.

Predictions (push_predictions; the user's prediction SOVs, tetris's and Go's): for each push on offer, every territory gerund the forces
say would flip, as the world will show it two slices on (the turn, then the read). The force structure is relative to the connection
turned (the user: "absolute is plain wrong"): p0 the connection; `<kind>+<d>:<place>` the gerund's place, d nodes downstream of it (`x`
when not downstream). Losses as well as gains: which is which is the territory register's to say (Go's ruling).

My choices where nothing is decided (each can change): a problem is open until everything the mind could own holds (every territory
gerund, clean included) and SETTLE slices pass with no wheel turned, or CAP slices pass; then the next problem of the room comes. Losses
when a problem is closed aren't losses (run.give, as Go's board set back).
"""
import random

import graph as g

HANGING, PRESSED, QUIET = 3.0, 2.0, 1.0   # potential forces (warpchess/potential.py's scale)
SETTLE = 3     # slices with everything held and no wheel turned before a problem is done (my number)
CAP = 300      # slices a problem stays open at most (my number)
TURNS = (("turning_forward", 1), ("turning_back", -1))
REST = ("resting", "hands", "holding")


def place_of(p, o):
    """The node a gerund is read at (for its distance from a connection turned)."""
    s = p.shape
    kind, rest = o.split("_", 1)
    if kind in ("test", "gap", "want"):
        return len(s.nodes) - 1
    if kind in ("load", "pulse"):   # (the force world: load_<place>_<test>, pulse_<place>_<test>)
        return int(rest.split("_")[0])
    if kind == "range":
        return sorted(s.checks)[int(rest)]
    if kind in ("sign", "divisor", "clean"):
        return s.where[int(rest)]
    if kind == "overflow":
        return int(rest)
    if kind == "lint":
        rule, tail = rest.split("_", 1)
        n = int(tail.split("_")[0])
        return s.where[n] if rule in ("cancel", "dominated") else n
    return None


def downstream(s, a, b):
    """Nodes from node a to node b along the graph (b reads a's value, through any number of nodes), or None."""
    reads = {i: [nd[1]] if nd[0] in ("op", "loop", "branch") else [nd[1], nd[2]] if nd[0] == "join" else []
             for i, nd in enumerate(s.nodes)}
    dist = {a: 0}
    for i in range(a + 1, len(s.nodes)):
        ds = [dist[j] + 1 for j in reads[i] if j in dist]
        if ds:
            dist[i] = min(ds)
    return dist.get(b)


class CodeWorld:
    still = True
    gamma = 0.7
    horizon = 2     # the turn's slice, and the slice its consequences land in
    read_held = g.TERRITORY + ("tick_",)   # held by reading only: the territory gerunds are the mind's while they hold (run.give), never by a claim
    unclaimable = ("conn_", "load_", "want_", "pulse_", "cond_", "path_", "hands", "gap_")   # no one's to claim: the wheels and what
    #   is only shown (the force world's counts and pulses among it: a number is not a territory, balance's ruling)
    returns = frozenset()

    def __init__(self, room, seed=0):
        """room(rng) -> a Problem: the next problem of the rung (a fixed shape with fresh tests and scramble, or a corpus)."""
        self.room, self.seed = room, seed
        self.rng = random.Random(f"problems:{seed}")
        self.t, self.log, self.diffs, self.solved = 0, [], [], []
        self.others = set()   # (nothing but the mind moves anything)
        self.problems = 0
        self.gained = 0          # ticks gained over the run (time territory)
        self.kept = set()        # ticks out of view: kept, not gone
        self.objs = {}
        self.open_problem()

    # ---- a problem ----------------------------------------------------------------------------------------------------------------

    def open_problem(self):
        was = dict(self.__dict__.get("shown", {}))
        self.p = self.room(self.rng)
        self.problems += 1
        self.pos = list(self.p.start)
        self.unread = False
        self.idle, self.opened, self.turned = 0, self.t, 0
        self.full = self.closing = False
        self.shown = self.read(self.pos)
        self.shown["hands"] = "holding"
        self._outs_shown = [r.output for r in self.p.runs(self.pos)]   # the outputs behind the shown gaps (gap_moves)
        self._gap_motion = {}
        self.objs = {o: None for o in self.shown}
        self.set_back = {o for o, st in self.shown.items() if was.get(o) != st} | {o for o in was if o not in self.shown}

    def renew(self):
        if self.full:
            self.open_problem()
            self.diffs = []

    PER_PROBLEM = ()   # nothing named per problem (the user, 2026-11-15: "stop naming after one specific problem then"). It was
    # everything read from the tests' values (2026-11-14, after rung 0's trace_dream.py: one problem's lived links drowned the next
    # problem's dream), and on rung 2 a turn's SOV never closed: what it did was new in every problem, so its inquiry kept the mind
    # flipping one wheel for whole problems (seed 1, problem 3: sov:turning_back_push:conn_2_adding bid 85)

    def read(self, pos):
        """The program's gerunds (graph.read), with what belongs to this problem alone named afresh for it: its tests, their outputs and
        what they want, its hidden range checks (test_<problem>_<k>, ...). The user, 2026-11-14 ("yes, do it"), after rung 0's trace
        (trace_dream.py): named test_<k> in every problem, the mind's lived "turning back at subtracting_2 gives output_1 giving 3" from
        one problem's tests drowned the dream's way in the next, whose tests differ (dreams are read only where nothing was lived). As Go
        names its stones afresh (the "eighth stone" that was a different stone every game). The wheels, their pushes and the gerunds
        on connections keep their names: a wheel's physics is the same in every problem."""
        out = {}
        for o, d in self.p.reading(pos).items():
            pre = next((x for x in self.PER_PROBLEM if o.startswith(x)), None)
            if pre:
                o = f"{pre}{self.problems}_{o[len(pre):]}"
            out[o] = d
            if o.startswith("load_"):   # each count's pulse: quiet while nothing lands (the force world; act sets it)
                out["pulse_" + o[len("load_"):]] = "quiet"
        return out

    @staticmethod
    def pulses(before, after):
        """The force world's pulses (PLAN.md, decided 2026-11-17; balance's third cut: the change as its own transient object beside the
        standing count, neither hiding the other): for each place and test whose count changed, rising_<n> or falling_<n>."""
        def n(d):
            if d is None or d == "bearing_nothing":
                return None
            return -int(d[len("owing_"):]) if d.startswith("owing_") else int(d[len("bearing_"):])
        out = {}
        for o, d in after.items():
            if not o.startswith("load_"):
                continue
            a, b = n(before.get(o)), n(d)
            if a is not None and b is not None and a != b:
                out["pulse_" + o[len("load_"):]] = f"{'rising' if b > a else 'falling'}_{abs(b - a)}"
        return out

    def held_all(self):
        return all(g.territory(self.shown).values())

    def states(self, tree=None):
        return dict(self.shown)

    # ---- what the mind can do ---------------------------------------------------------------------------------------------------

    def invitations(self, tree=None):
        if self.full or self.closing:
            return []
        return [(label, f"conn_{c}", self.shown[f"conn_{c}"]) for c in range(len(self.pos)) for label, _ in TURNS] + [REST]

    @staticmethod
    def push_id(inv):
        return f"{inv[0]}_push:{inv[1]}_{inv[2]}"

    def turned_pos(self, inv):
        pos = list(self.pos)
        if inv[0] in dict(TURNS):
            pos[int(inv[1].split("_")[1])] += dict(TURNS)[inv[0]]
        return pos

    def reaches(self, inv):
        return {inv[1]}   # the push's force reaches its connection's wheel

    def _after(self, inv):
        memo = self.__dict__.setdefault("_after_memo", {})
        key = (tuple(self.pos), self.problems, inv)
        if memo.get("key") != (tuple(self.pos), self.problems):
            memo.clear()
            memo["key"] = (tuple(self.pos), self.problems)
        if inv not in memo:
            pos = self.turned_pos(inv)
            memo[inv] = (self.read(pos), [r.output for r in self.p.runs(pos)])
        return memo[inv]

    def potentials(self):
        out = {}
        if self.full or self.closing:
            return out
        now_out = [r.output for r in self.p.runs(self.pos)]
        now = g.territory(self.read(self.pos))
        for inv in self.invitations():
            reading, outputs = self._after(inv)
            flips = sum(1 for o, h in g.territory(reading).items() if h != now.get(o))
            if inv == REST and all(now.values()):   # resting while everything holds gains a tick (time territory)
                flips = max(flips, 1)
            # a push's force counts the gerunds it reaches, as stacked unit potential forces (the user, 2026-11-15, the
            # balance domain's principle applied here). A unit term for the gaps' movement was tried three ways and taken
            # out (2026-11-15, LADDER.md: raw, it made the biggest swing the strongest force; saturated, a whisper; with
            # gaps as territory, every counted state became an ownable claim). How counts enter a mind without becoming
            # spurious salience or spurious territory is the balance domain's rung 0 question, settled there first
            out[self.push_id(inv)] = HANGING + (flips - 1) if flips else PRESSED if outputs != now_out else QUIET
        return out

    def effects_after(self, inv):
        """The facts a push's force structure says change (SovAgent.anti_update's defense counting, Params.defense_still: the
        anti side counts as the potentials do). Waiting (None) changes nothing: a still world."""
        if inv is None or self.full or self.closing:
            return set()
        reading, _ = self._after(inv)
        return {f"{o}_{h}" for o, h in reading.items() if self.shown.get(o) != h}

    TIME = (frozenset({("p0", "time+0:tick")}), "time+0_gained")

    def tick_name(self):
        return f"tick_{self.gained}"

    def relative(self, c, o, doing):
        """A gerund's flip relative to connection c: (force structure, relative effect)."""
        s = self.p.shape
        kind = o.split("_", 1)[0]
        at = place_of(self.p, o)
        d = downstream(s, s.where[c], at) if at is not None else None
        d = "x" if d is None else d
        node = f"{kind}+{d}:{'here' if d == 0 else 'downstream' if d != 'x' else 'elsewhere'}"
        return frozenset({("p0", node)}), f"{kind}+{d}_{doing}"

    def gap_units(self, outputs):
        """Each test's gap as a stack of units (None where the output is severed: no count to a missing force)."""
        return [abs(o - w) if o is not None else None for o, (_, w) in zip(outputs, self.p.tests)]

    def gap_moves(self, c, before_outs, after_outs):
        """The counted CHANGES a turn of connection c makes to the gaps — "adding_2 stacks two" (the user, 2026-11-15:
        the count is a doing, what the push does, never a standing state to own): [(absolute effect, forces, rel)]. A
        gap that shrinks by two is `closing_2`, one that grows is `widening_n`; the standing readings stay uncounted."""
        out = []
        for k, (a, b) in enumerate(zip(self.gap_units(before_outs), self.gap_units(after_outs))):
            if a is None or b is None or a == b:
                continue
            doing = f"{'closing' if b < a else 'widening'}_{abs(b - a)}"
            forces, rel = self.relative(c, f"gap_{k}", doing)
            out.append((f"gap_{k}_{doing}", forces, rel))
        return out

    def potential_effects(self):
        """A wheel just turned and its consequences not read: every territory gerund that flips next slice (certain: the forces say it)."""
        if self.closing or self.full:
            return []
        if not self.unread:
            return [(f"{self.tick_name()}_gained", 1, *self.TIME)] if self.held_all() else []
        reading = self.read(self.pos)
        out = []
        for o, h in g.territory(reading).items():  # (the hands aren't territory)
            if self.shown.get(o) != reading[o]:
                forces, rel = self.relative(self.last_conn, o, reading[o])
                out.append((f"{o}_{reading[o]}", 1, forces, rel))
        before_outs = self.__dict__.get("_outs_shown")
        if before_outs is not None:   # the counted changes the turn makes to the gaps, as effects (the user: make it so)
            after_outs = [r.output for r in self.p.runs(self.pos)]
            out += [(eff, 1, forces, rel) for eff, forces, rel in self.gap_moves(self.last_conn, before_outs, after_outs)]
        if all(g.territory(reading).values()):   # nothing more turned, and everything holds once read: a tick gained
            out.append((f"{self.tick_name()}_gained", 1, *self.TIME))
        return out

    def push_predictions(self):
        out = []
        if self.full or self.closing or self.unread:
            return out
        now_outs = [r.output for r in self.p.runs(self.pos)]
        now_terr = g.territory(self.read(self.pos))
        one_step = {}   # push id -> the gerunds it alone makes held (lines must earn more than their first step)
        for inv in self.invitations():
            if inv == REST:
                if self.held_all():
                    out.append((f"{self.tick_name()}_gained", 1, *self.TIME, (self.push_id(inv),)))
                continue
            reading, outputs = self._after(inv)
            c = int(inv[1].split("_")[1])
            one_step[self.push_id(inv)] = {o for o, h in g.territory(reading).items() if h and not now_terr.get(o)}
            for o, h in g.territory(reading).items():
                if self.shown.get(o) != reading[o]:
                    forces, rel = self.relative(c, o, reading[o])
                    out.append((f"{o}_{reading[o]}", 2, forces, rel, (self.push_id(inv),)))
            for eff, forces, rel in self.gap_moves(c, now_outs, outputs):   # what this push would stack or take away
                out.append((eff, 2, forces, rel, (self.push_id(inv),)))
            if all(g.territory(reading).values()):
                out.append((f"{self.tick_name()}_gained", 2, *self.TIME, (self.push_id(inv),)))
        # lines to the crossing (the user's other session, 2026-11-16: magnitudes never pull — they decide WHEN the
        # crossing comes, inside the world's own prediction; warp chess's tool lines, tetris's commit): depth-2 turn
        # sequences whose END newly holds a territory gerund neither single step does — the units worked forward to the
        # crossing. The sequence's other flips are emitted too: a line that crosses one test while breaking another
        # predicts its loss, and the register reads losses. Nothing numeric is owned or wanted: crossings only
        if not (self.full or self.closing):
            turns = [inv for inv in self.invitations() if inv != REST]
            for inv1 in turns:
                pos1 = self.turned_pos(inv1)
                for inv2 in turns:
                    pos2 = list(pos1)
                    c2 = int(inv2[1].split("_")[1])
                    pos2[c2] += dict(TURNS)[inv2[0]]
                    reading2 = self.read(pos2)
                    terr2 = g.territory(reading2)
                    steps = (self.push_id(inv1),
                             f"{inv2[0]}_push:{inv2[1]}_{self.p.shape.doing(c2, pos1[c2])}")
                    gained = {o for o, h in terr2.items() if h and not now_terr.get(o)}
                    if not gained or gained <= one_step.get(steps[0], set()):
                        continue   # the line must earn a crossing its first step alone does not
                    for o, h in terr2.items():
                        if self.shown.get(o) != reading2[o]:
                            forces, rel = self.relative(c2, o, reading2[o])
                            out.append((f"{o}_{reading2[o]}", 4, forces, rel, steps))
                    if all(terr2.values()):
                        out.append((f"{self.tick_name()}_gained", 4, *self.TIME, steps))
        return out

    @staticmethod
    def role_of(node):
        if node == "p0":
            return "part", False
        return node.split(":", 1)[-1], True

    # ---- a slice ------------------------------------------------------------------------------------------------------------------

    def act(self, inv=None, hold=False):
        """One slice: what the last turn set going is read first (every value and gerund); then the mind's turn of a wheel, if it made
        one on offer: only that connection changes this slice."""
        before = dict(self.shown)
        if self.closing:   # the problem closes a slice after it is done: its last tick stays in view a slice, perceived (first it
            self.full, self.closing = True, False   # closed in the slice the tick came, the next problem opened before the mind saw
            # it, the tick it had predicted never came, and its last push, a rest, was told it prevents time gained: probe, 2026-11-14)
        legal = inv is not None and inv in self.invitations()
        for o in [o for o in self.shown if o.startswith("tick_")]:   # last slice's tick leaves view, kept
            del self.shown[o]
            self.objs.pop(o, None)
            self.kept.add(o)
        for o, standing in self.__dict__.pop("_gap_motion", {}).items():   # last slice's counted motion rests: the gap's
            if o in self.shown:                                             # standing reading is uncounted (a doing, not a state)
                self.shown[o] = standing
        for o in [o for o, d in self.shown.items() if o.startswith("pulse_") and d != "quiet"]:   # last slice's pulses rest
            self.shown[o] = "quiet"
        if self.unread:
            fresh = self.read(self.pos)
            after_outs = [r.output for r in self.p.runs(self.pos)]
            motion = {}
            before_outs = self.__dict__.get("_outs_shown")
            if before_outs is not None:   # the counted change is SEEN the slice it lands — "adding_2 stacks two", perceived
                for eff, _, _ in self.gap_moves(self.last_conn, before_outs, after_outs):
                    o, doing = eff.split("_", 2)[0] + "_" + eff.split("_", 2)[1], eff.split("_", 2)[2]
                    motion[o] = fresh[o]
                    fresh[o] = doing
            self._gap_motion = motion
            self._outs_shown = after_outs
            fresh.update(self.pulses(self.shown, fresh))   # the counts that changed pulse this slice; read() set the rest quiet
            self.shown = {**fresh, "hands": "holding"}
            self.unread = False
        if inv is not None:
            self.log.append((self.t, inv[0], inv[1], legal))
        if legal and inv != REST:
            c = int(inv[1].split("_")[1])
            self.pos[c] += dict(TURNS)[inv[0]]
            self.shown = dict(self.shown)
            self.shown[inv[1]] = self.p.shape.doing(c, self.pos[c])
            self.unread, self.last_conn, self.idle = True, c, 0
            self.turned += 1
        else:
            self.idle += 1
        if not self.unread and not self.full and not self.closing and self.held_all():   # time territory: a tick gained (only this object changes)
            tick = self.tick_name()
            self.gained += 1
            self.shown[tick] = "gained"
            self.objs[tick] = None
        if not self.unread and self.held_all() and self.idle >= SETTLE or self.t - self.opened >= CAP:
            if not self.full and not self.closing:
                self.solved.append(dict(name=self.p.name, slices=self.t - self.opened, turns=self.turned,
                                        settled=self.held_all(), start=list(self.p.start), end=list(self.pos), correct=list(self.p.correct)))
                self.closing = True
        self.diffs = [f"{o}: {before.get(o)} -> {st}" for o, st in sorted(self.shown.items()) if before.get(o) != st]
        self.set_back = set()
        self.t += 1
        return self.diffs
