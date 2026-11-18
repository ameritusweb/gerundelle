"""The clean code language (PLAN.md, CONTROL_FLOW.md): a feed-forward graph of operations on wheels. No mind here: the language, how a
program runs on its test inputs, every gerund it reads as, and how problems are made. world.py puts it behind the interface a mind reads.

A program (the user, 2026-11-14): N inputs on the left; paths go left to right, generally, and can come together; they always end at one
output. Each connection is an operation on a wheel: a single path's wheel or a join's wheel. A problem fixes the shape; only the wheels
turn (one step forward or back: a move). Values are integers; a negative value is a compile error.

Nodes, in order (each reads only nodes before it, so the graph is feed-forward):
  ("input", i)                                   the i-th input
  ("op", src, c)                                 the value at src through connection c (a single path's wheel)
  ("join", a, b, c)                              the values at a (first) and b (second) through connection c (a join's wheel)
  ("loop", src, body, units, limit)              CONTROL_FLOW.md: the value at src goes round through the body's connections (single
                                                 paths, in order) while its force does not outnumber the condition's `units`; past
                                                 `limit` rounds the loop overflows
  ("branch", src, units, over, hold)             the value at src goes down `over` (connections in order) if its force outnumbers the
                                                 condition's `units`, else down `hold`; the branch's value is the end of the path taken
The output is the last node.

My readings, where nothing is decided (each stated where it is used, for the user to change):
- A value's force against a condition is the value itself, in units: it outnumbers the condition when value > units (CONTROL_FLOW.md,
  "numbers are stacked unit potential forces on zero").
- A loop's condition is read before each round (so a loop can go round zero times: a dead loop is one that does on every test).
- After a `mod` by zero, or a loop stopped by its limit, the value is gone: nothing flows on (None), and every node after it has none;
  a test whose output is none fails, giving nothing.
- A negative value flows on (the compile error is its gerund's; what is computed after it is still computed).
"""
import random

SINGLE = ("multiplying_3", "multiplying_2", "adding_2", "adding_1", "passing", "subtracting_1", "subtracting_2", "negating", "halving")
JOIN = ("taking_max", "adding", "multiplying", "subtracting", "taking_min", "taking_mod")
IDENTITY = SINGLE.index("passing")   # (the user's "identity": a connection that passes its value on unchanged)
CANCEL = {("adding_1", "subtracting_1"), ("subtracting_1", "adding_1"), ("adding_2", "subtracting_2"), ("subtracting_2", "adding_2")}


def wheel(kind):
    return SINGLE if kind == "single" else JOIN


def single(doing, v):
    if v is None:
        return None
    return {"multiplying_3": v * 3, "multiplying_2": v * 2, "adding_2": v + 2, "adding_1": v + 1, "passing": v,
            "subtracting_1": v - 1, "subtracting_2": v - 2, "negating": -v, "halving": v // 2}[doing]   # (halving rounds down: PLAN.md)


def join(doing, a, b):
    """-> (value, divided by zero)."""
    if a is None or b is None:
        return None, False
    if doing == "taking_mod":
        return (None, True) if b == 0 else (a % b, False)
    return {"taking_max": max(a, b), "adding": a + b, "multiplying": a * b, "subtracting": a - b, "taking_min": min(a, b)}[doing], False


class Shape:
    """A problem's fixed shape: its nodes, its connections (each a wheel kind), its range checks (node -> (lo, hi), hidden from the mind),
    and its tests' inputs."""

    def __init__(self, n_inputs, nodes, kinds, checks=None):
        self.n_inputs, self.nodes, self.kinds = n_inputs, list(nodes), list(kinds)   # kinds[c]: "single" or "join"
        self.checks = dict(checks or {})
        self.where = {}   # connection -> the node it belongs to
        for i, nd in enumerate(self.nodes):
            for c in conns_of(nd):
                self.where[c] = i

    def doing(self, c, pos):
        return wheel(self.kinds[c])[pos % len(wheel(self.kinds[c]))]

    def run(self, pos, inputs):
        """The program with the wheels at `pos` on one test's inputs -> a Run."""
        r = Run()
        vals = []
        for i, nd in enumerate(self.nodes):
            k = nd[0]
            if k == "input":
                v = inputs[nd[1]]
            elif k == "op":
                v = self._through(r, nd[2], vals[nd[1]], pos)
            elif k == "join":
                v, zero = join(self.doing(nd[3], pos[nd[3]]), vals[nd[1]], vals[nd[2]])
                r.after[nd[3]] = v
                if zero:
                    r.zero.add(nd[3])
                if v is not None and v < 0:
                    r.negative.add(nd[3])
            elif k == "loop":
                v, rounds = vals[nd[1]], 0
                while v is not None and not v > nd[3]:   # the condition holds: round again (read before each round)
                    if rounds >= nd[4]:                  # past the limit: overflowing, and the value is gone
                        r.overflow.add(i)
                        v = None
                        break
                    for c in nd[2]:
                        v = self._through(r, c, v, pos)
                    rounds += 1
                r.rounds[i] = rounds
            elif k == "branch":
                v = vals[nd[1]]
                if v is None:
                    r.taken[i] = None
                else:
                    side = "over" if v > nd[2] else "hold"
                    r.taken[i] = side
                    for c in (nd[3] if side == "over" else nd[4]):
                        v = self._through(r, c, v, pos)
            else:
                raise ValueError(k)
            vals.append(v)
        r.values, r.output = vals, vals[-1]
        return r

    def _through(self, r, c, v, pos):
        v = single(self.doing(c, pos[c]), v)
        r.after[c] = v
        if v is not None and v < 0:
            r.negative.add(c)
        return v


def conns_of(nd):
    k = nd[0]
    if k == "op":
        return [nd[2]]
    if k == "join":
        return [nd[3]]
    if k == "loop":
        return list(nd[2])
    if k == "branch":
        return list(nd[3]) + list(nd[4])
    return []


class Run:
    def __init__(self):
        self.after = {}       # connection -> the value after it (its last, in a loop)
        self.negative = set() # connections a negative value came out of
        self.zero = set()     # joins that took a mod by zero
        self.overflow = set() # loops past their limit
        self.rounds = {}      # loop node -> rounds gone
        self.taken = {}       # branch node -> "over", "hold", or None
        self.values, self.output = [], None


class Problem:
    """A problem: a shape, its tests [(inputs, wanted)], the correct wheels (one setting that satisfies everything: the user, "there has
    to be 'something' that satisfies it"), and where its wheels start (scrambled)."""

    def __init__(self, shape, tests, correct, start, name="problem"):
        self.shape, self.tests, self.correct, self.start, self.name = shape, list(tests), list(correct), list(start), name

    def runs(self, pos):
        return [self.shape.run(pos, inp) for inp, _ in self.tests]

    def reading(self, pos):
        """Every gerund the program reads as, with the wheels at pos: object -> doing (world.py names the objects)."""
        return read(self, pos, self.runs(pos))


# ---- the gerunds --------------------------------------------------------------------------------------------------------------------

def held_in(doing):
    """Whether a territory gerund's doing is the one the mind owns (PLAN.md, Territory)."""
    return doing in ("passing", "keeping_sign", "holding", "contained", "quiet", "empty", "needed", "flowing")


def units(v):
    """A value as a stack of unit forces, read as a count (the force world, PLAN.md): bearing_<n>; a negative value owes its units
    (owing_<n>: a compile error already, sign_<c>); a value that never came, nothing."""
    if v is None:
        return "bearing_nothing"
    return f"bearing_{v}" if v >= 0 else f"owing_{-v}"


def read(p, pos, runs):
    """The program's gerunds: object -> doing. Territory (PLAN.md): test_<k>, range_<k>, sign_<c>, divisor_<c>, overflow_<n>, lint_*,
    clean_<c>. Shown, not territory: conn_<c> (its operation), load_<place>_<k> and want_<k> (the force world's counts), gap_<k>,
    cond_<n>, path_<n>_over / _hold."""
    s = p.shape
    out = {}
    for c in range(len(s.kinds)):
        out[f"conn_{c}"] = s.doing(c, pos[c])
        out[f"sign_{c}"] = "going_negative" if any(c in r.negative for r in runs) else "keeping_sign"   # (one gerund per compile error)
        if s.kinds[c] == "join":
            out[f"divisor_{c}"] = "dividing_by_zero" if any(c in r.zero for r in runs) else "holding"
    for k, ((inp, wanted), r) in enumerate(zip(p.tests, runs)):
        ok = r.output == wanted
        out[f"test_{k}"] = "passing" if ok else "failing"
        # the force world (PLAN.md, decided 2026-11-17): a value is a stack of unit forces, perceived as an identity-free count at
        # every place on the graph, for every test ("Every place, every test"), as balance perceives a load; the wanted the same
        # stack on the test's other side. First the output was a name on failure only (`giving_7`) and the wanted a name
        # (`wanting_9`), and the places between never perceived: no terms for the SOV to build the program's equation from
        for i, v in enumerate(r.values):
            out[f"load_{i}_{k}"] = units(v)
        out[f"want_{k}"] = units(wanted)
        # the gap as a force balance (PLAN.md, the user: a failure and the actual output tell it the gap, "a force the mind
        # can feel"; the balance principle, 2026-11-15: the wanted is a stack of units, the output presses against it, and
        # the reading is which side outnumbers — a fact, not a worth: pass or fail already says which is good). The wheels
        # are ordered, so what a turn does to a gap holds in EVERY problem: the one problem-invariant relation the tests
        # afford, and so the one knowledge that can transfer (my choice, to revise; found 2026-11-15, the amnesia control:
        # with the gap unperceived, carrying 20% equalled amnesia 19% — nothing the tests taught could leave its problem)
        # counted gaps were tried and taken out (2026-11-15, three wirings, each traced in LADDER.md: as raw force the
        # biggest swing outplunged every closer; saturated, a whisper nothing read; as territory, EVERY counted state
        # became ownable and the register wanted its old wounds back — potential:gap+0_overshooting_40 set as a want. A
        # number is not a territory; the crossing is. How counts enter without becoming spurious claims is the balance
        # domain's rung 0 question, settled there first)
        out[f"gap_{k}"] = ("closed" if ok else "severed" if r.output is None else
                           "falling_short" if r.output < wanted else "overshooting")
    for k, (node, (lo, hi)) in enumerate(sorted(s.checks.items())):   # range validity: every test's value in range (hidden range)
        ok = all(r.values[node] is not None and lo <= r.values[node] <= hi for r in runs)
        out[f"range_{k}"] = "passing" if ok else "failing"
    for i, nd in enumerate(s.nodes):
        if nd[0] == "loop":
            out[f"overflow_{i}"] = "overflowing" if any(i in r.overflow for r in runs) else "contained"
            out[f"cond_{i}"] = f"resisting_{nd[3]}"
            out[f"lint_deadloop_{i}"] = "firing" if all(r.rounds.get(i, 0) == 0 for r in runs) else "quiet"
        if nd[0] == "branch":
            out[f"cond_{i}"] = f"resisting_{nd[2]}"
            for side in ("over", "hold"):
                took = any(r.taken.get(i) == side for r in runs)
                out[f"path_{i}_{side}"] = "flowing" if took else "blocked"
                if nd[3 if side == "over" else 4]:   # (a path with no connection on it isn't code: nothing to be dead)
                    out[f"lint_deadpath_{i}_{side}"] = "quiet" if took else "firing"
    out.update(lint_cancel(p, pos))
    out.update(lint_dominated(p, pos, runs))
    out.update(clean(p, pos, out))
    return out


def chains(s):
    """Pairs of single-path connections one straight after the other: (first, second)."""
    out = []
    for nd in s.nodes:
        if nd[0] == "op" and s.nodes[nd[1]][0] == "op":
            out.append((s.nodes[nd[1]][2], nd[2]))
        for seq in ([nd[2]] if nd[0] == "loop" else [nd[3], nd[4]] if nd[0] == "branch" else []):
            out += list(zip(seq, seq[1:]))
    return out


def lint_cancel(p, pos):
    """The user's lint: add N followed by subtract N on a path (lint_cancel_<second>)."""
    s = p.shape
    return {f"lint_cancel_{b}": "firing" if (s.doing(a, pos[a]), s.doing(b, pos[b])) in CANCEL else "quiet" for a, b in chains(s)}


def lint_dominated(p, pos, runs):
    """The user's lint, a join input "always dominated by the other path" (picked: read by the world from the test inputs): an input is
    dominated when, on every test, the join's result is the same with that input one more or one less (my reading of "never changes the
    join's result"). lint_dominated_<join>_first / _second."""
    s = p.shape
    out = {}
    for nd in s.nodes:
        if nd[0] != "join":
            continue
        c, doing = nd[3], s.doing(nd[3], pos[nd[3]])
        for side, idx in (("first", 1), ("second", 2)):
            dom = True
            for r in runs:
                a, b = r.values[nd[1]], r.values[nd[2]]
                if a is None or b is None:
                    continue
                base = join(doing, a, b)[0]
                for d in (1, -1):
                    a2, b2 = (a + d, b) if idx == 1 else (a, b + d)
                    if join(doing, a2, b2)[0] != base:
                        dom = False
                if not dom:
                    break
            out[f"lint_dominated_{c}_{side}"] = "firing" if dom else "quiet"
    return out


TERRITORY = ("test_", "range_", "sign_", "divisor_", "overflow_", "lint_", "clean_")   # gap_ was territory for an
# afternoon (2026-11-15) and is not: every counted state became an ownable claim and the register wanted its old wounds
# back (LADDER.md; "a number is not a territory; the crossing is")


def territory(reading):
    """The territory gerunds of a reading (PLAN.md, Territory): region -> held."""
    return {o: held_in(d) for o, d in reading.items() if o.startswith(TERRITORY)}


def clean(p, pos, now):
    """Clean code (PLAN.md: the fewest non-identity operations): once every other territory gerund holds, each single-path connection
    reads `empty` (passing), `needed` (passing there would lose something now held), or `spare` (passing there would lose nothing now
    held); before that, `unsettled`. My reading of the user's whole-program
    "simplest setting" one connection at a time, read by the world as lint is."""
    s = p.shape
    terr = territory(now)
    held = {o for o, h in terr.items() if h and not o.startswith("clean_")}
    settled = all(h for o, h in terr.items() if not o.startswith("clean_"))
    out = {}
    for c, kind in enumerate(s.kinds):
        if kind != "single":
            continue
        if not settled:   # (clean is the simplest among the settings that satisfy everything: until everything else holds, nothing here
            out[f"clean_{c}"] = "unsettled"   # is clean or not. First `empty` read as held with every test failing, and the mind
            continue                          # turned a solved wheel round to `passing`: rung 0, seed 0, 2026-11-14)
        if pos[c] % len(SINGLE) == IDENTITY:
            out[f"clean_{c}"] = "empty"
            continue
        trial = list(pos)
        trial[c] = IDENTITY
        r2 = read_core(p, trial)
        lost = any(o in held and not h for o, h in territory(r2).items() if not o.startswith("clean_"))
        out[f"clean_{c}"] = "needed" if lost else "spare"
    return out


def read_core(p, pos):
    """read() without the clean readings (which read this for each connection)."""
    runs = p.runs(pos)
    s = p.shape
    out = {}
    for c in range(len(s.kinds)):
        out[f"sign_{c}"] = "going_negative" if any(c in r.negative for r in runs) else "keeping_sign"
        if s.kinds[c] == "join":
            out[f"divisor_{c}"] = "dividing_by_zero" if any(c in r.zero for r in runs) else "holding"
    for k, ((inp, wanted), r) in enumerate(zip(p.tests, runs)):
        out[f"test_{k}"] = "passing" if r.output == wanted else "failing"
    for k, (node, (lo, hi)) in enumerate(sorted(s.checks.items())):
        out[f"range_{k}"] = "passing" if all(r.values[node] is not None and lo <= r.values[node] <= hi for r in runs) else "failing"
    for i, nd in enumerate(s.nodes):
        if nd[0] == "loop":
            out[f"overflow_{i}"] = "overflowing" if any(i in r.overflow for r in runs) else "contained"
            out[f"lint_deadloop_{i}"] = "firing" if all(r.rounds.get(i, 0) == 0 for r in runs) else "quiet"
        if nd[0] == "branch":
            for side in ("over", "hold"):
                if nd[3 if side == "over" else 4]:
                    out[f"lint_deadpath_{i}_{side}"] = "quiet" if any(r.taken.get(i) == side for r in runs) else "firing"
    out.update(lint_cancel(p, pos))
    out.update(lint_dominated(p, pos, runs))
    return out


def satisfied(p, pos):
    """Everything held but clean: tests, compile errors, lint (PLAN.md: "something" always satisfies a problem)."""
    return all(h for o, h in territory(read_core(p, pos)).items())


# ---- making problems ----------------------------------------------------------------------------------------------------------------

def make(shape, rng, n_tests=3, inputs=(0, 6), scramble=2, name="problem", tries=500):
    """A problem on a fixed shape: a correct setting drawn at random that keeps every value non-negative, divides by nothing, keeps every
    loop in its limit and fires no lint on the test inputs; the tests are its outputs; each range check's hidden range holds the correct
    values with room either side; the wheels start scrambled, each turned up to `scramble` steps from correct (luck: the user, "it's
    random how 'off' the operations are"), not all of them correct. My choices: the inputs, the number of tests, the room either side."""
    for _ in range(tries):
        correct = [rng.randrange(len(wheel(k))) for k in shape.kinds]
        tests_in = [tuple(rng.randint(*inputs) for _ in range(shape.n_inputs)) for _ in range(n_tests)]
        runs = [shape.run(correct, t) for t in tests_in]
        if any(r.output is None or r.negative or r.zero or r.overflow for r in runs):
            continue
        if len({r.output for r in runs}) < min(2, n_tests):   # (tests that all want the same thing say little: my choice)
            continue
        checks = {}
        for node, _ in shape.checks.items():
            vals = [r.values[node] for r in runs]
            room = rng.randint(1, 4)
            checks[node] = (max(0, min(vals) - room), max(vals) + room)
        s2 = Shape(shape.n_inputs, shape.nodes, shape.kinds, checks)
        p = Problem(s2, [(t, r.output) for t, r in zip(tests_in, runs)], correct, correct, name)
        if not satisfied(p, correct):   # (no lint fires on the correct setting either: something satisfies everything)
            continue
        for _ in range(100):
            start = [(c + rng.randint(-scramble, scramble)) % len(wheel(k)) for c, k in zip(correct, shape.kinds)]
            if start != correct:
                p.start = start
                return p
    raise ValueError("no problem found on this shape")


def loop_shape():
    """One input through a connection, then a loop whose body is one connection, then a connection (CONTROL_FLOW.md)."""
    nodes = [("input", 0), ("op", 0, 0), ("loop", 1, (1,), 6, 8), ("op", 2, 2)]
    return Shape(1, nodes, ["single"] * 3)


def branch_shape():
    """One input through a connection, then a branch with one connection on each path, then a connection (CONTROL_FLOW.md)."""
    nodes = [("input", 0), ("op", 0, 0), ("branch", 1, 3, (1,), (2,)), ("op", 2, 3)]
    return Shape(1, nodes, ["single"] * 4)


def chain_shape(n):
    """One input through n single-path connections."""
    nodes = [("input", 0)] + [("op", i, i) for i in range(n)]
    return Shape(1, nodes, ["single"] * n)


def join_shape():
    """Two inputs, each through one connection, joined (rung 1's room)."""
    nodes = [("input", 0), ("input", 1), ("op", 0, 0), ("op", 1, 1), ("join", 2, 3, 2)]
    return Shape(2, nodes, ["single", "single", "join"])


if __name__ == "__main__":
    rng = random.Random(0)
    p = make(chain_shape(2), rng)
    print(p.tests, p.correct, p.start)
    for o, d in sorted(p.reading(p.start).items()):
        print(" ", o, d)
