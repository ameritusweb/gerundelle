"""An interpreter for the operation language (PoC step 3): the semantic gate.

Programs are never run as Python. This evaluates operation trees directly, with a
step limit, so a finished program can be checked against its domain's behavior spec
(specs.py) before it enters the corpus (POC.md 3h). Search, pruning and fingerprints
stay structural; only corpus admission uses this.

Semantics follow the Python each operation stands for (VOCABULARY.md). Any runtime
error, an unfilled hole or running past the step limit raises Fault.
"""
from grammar import LOOP_NAMES


class Fault(Exception):
    pass


class Return(Exception):
    def __init__(self, value):
        self.value = value


class Break(Exception):
    pass


MAX_STEPS = 10_000
MAX_SIZE = 10_000  # longest sequence a program may build: a loop that doubles a value exhausts memory before the step limit (POC3 audit)
COMPARES = {"==": lambda a, b: a == b, "!=": lambda a, b: a != b, "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b}
EMPTY = {"list": list, "dict": dict, "str": str}


class Machine:
    """One program's module state, kept across calls (as a module's would be)."""

    def __init__(self, tree, max_steps=MAX_STEPS):
        self.funcs = {f.value: f for f in tree.kids[1].kids}
        self.steps, self.max_steps = 0, max_steps
        self.globals = {}
        for s in tree.kids[0].kids:
            self.globals[s.kids[0].value] = self.guard(self.value, s.kids[1], {})

    def guard(self, fn, *args):
        try:
            return fn(*args)
        except (Fault, Return):
            raise
        except Break:
            raise Fault("breaking outside a loop")
        except (IndexError, KeyError, TypeError, ValueError, ZeroDivisionError, AttributeError, RecursionError) as e:
            raise Fault(f"{type(e).__name__}: {e}")

    def call(self, fname, *args):
        """Call function `fname` of the program."""
        return self.guard(self._call, fname, args)

    def _call(self, fname, args):
        f = self.funcs[fname]
        env = {p.value: a for p, a in zip(f.kids[0].kids, args)}
        try:
            self.block(f.kids[1], env)
        except Return as r:
            return r.value
        return None

    def tick(self):
        self.steps += 1
        if self.steps > self.max_steps:
            raise Fault("step limit")

    def sized(self, v):
        if isinstance(v, (str, list)) and len(v) > MAX_SIZE:
            raise Fault("value too large")
        return v

    def position(self, i, seq=None, end_ok=True):
        """A position in the operation language is a non-negative place within a sequence.
        Python's negative indices and clamped out-of-range inserts are not part of it:
        both let junk pass the specs (POC3 audit round 6)."""
        if isinstance(i, bool) or not isinstance(i, int) or i < 0:
            raise Fault(f"not a position: {i!r}")
        if seq is not None and (i > len(seq) if end_ok else i >= len(seq)):
            raise Fault(f"position {i} beyond the sequence")
        return i

    # -- values --------------------------------------------------------------------
    def value(self, n, env):
        self.tick()
        k, c = n.kind, n.kids
        if k == "hole":
            raise Fault("unfilled hole")
        if k == "name":
            return env[n.value] if n.value in env else self.globals[n.value]
        if k == "constant":
            return n.value
        if k == "function":
            return lambda *args: self._call(n.value, args)
        if k == "creating_empty":
            return EMPTY[n.type.name]()
        if k == "combining":
            a = self.value(c[0], env)
            return (a and self.value(c[1], env)) if n.value == "and" else (a or self.value(c[1], env))
        v = [self.value(x, env) for x in c]
        if k in ("indexing", "looking_up"):
            return v[0][self.position(v[1], v[0], end_ok=False)] if isinstance(v[0], (str, list)) else v[0][v[1]]
        if k == "slicing_before":
            return v[0][:self.position(v[1])]
        if k == "slicing_from":
            return v[0][self.position(v[1]):]
        if k == "slicing_between":
            return v[0][self.position(v[1]):self.position(v[2])]
        if k == "measuring":
            return len(v[0])
        if k == "pairing":
            return (v[0], v[1])
        if k == "wrapping":
            return [v[0]]
        if k == "concatenating":
            out = v[0]
            for x in v[1:]:
                out = self.sized(out + x)
            return out
        if k == "adding":
            return v[0] + v[1]
        if k == "subtracting":
            return v[0] - v[1]
        if k == "comparing":
            return COMPARES[n.value](v[0], v[1])
        if k == "testing_membership":
            return v[0] in v[1]
        if k == "testing_emptiness":
            return len(v[0]) == 0
        if k == "negating":
            return not v[0]
        if k == "calling":
            return v[0](*v[1:])
        if k == "popping":
            return v[0].pop(*v[1:])
        raise Fault(f"not a value: {k}")

    # -- operations ------------------------------------------------------------------
    def bind(self, target, v, env):
        if target.value in self.globals and target.value not in env:
            self.globals[target.value] = v
        else:
            env[target.value] = v

    def block(self, b, env):
        for s in b.kids:
            self.op(s, env)

    def loop_items(self, n, env):
        """What a loop iterates over: one tuple of values per pass, for its names."""
        k, c = n.kind, n.kids
        src = [self.value(x, env) for x in c[LOOP_NAMES[k]:-1]]
        if k == "iterating_over_items":
            return [(x,) for x in src[0]]
        if k == "iterating_over_positions":
            return [(i,) for i in range(len(src[0]))]
        if k == "iterating_with_positions":
            return list(enumerate(src[0]))
        if k == "iterating_together":
            return list(zip(src[0], src[1]))
        if k == "iterating_over_keys":
            return [(x,) for x in list(src[0])]
        return list(src[0].items())  # iterating_over_keys_and_values

    def op(self, s, env):
        self.tick()
        k, c = s.kind, s.kids
        if k == "hole":
            raise Fault("unfilled hole")
        if k == "binding":
            self.bind(c[0], self.value(c[1], env), env)
        elif k == "destructuring":
            a, b = self.value(c[2], env)
            self.bind(c[0], a, env)
            self.bind(c[1], b, env)
        elif k == "accumulating":
            cur, add = self.value(c[0], env), self.value(c[1], env)
            if isinstance(cur, list):
                cur.extend(add)  # list += changes the list in place, as in Python
                self.sized(cur)
            else:
                self.bind(c[0], self.sized(cur + add), env)
        elif k in ("calling", "popping"):
            self.value(s, env)
        elif k == "appending":
            self.sized(self.value(c[0], env)).append(self.value(c[1], env))
        elif k == "inserting":
            lst = self.sized(self.value(c[0], env))
            lst.insert(self.position(self.value(c[1], env), lst), self.value(c[2], env))
        elif k == "removing":
            self.value(c[0], env).remove(self.value(c[1], env))
        elif k == "storing":
            self.value(c[0], env)[self.value(c[1], env)] = self.value(c[2], env)
        elif k == "deleting":
            del self.value(c[0], env)[self.value(c[1], env)]
        elif k == "returning":
            raise Return(self.value(c[0], env) if c else None)
        elif k == "breaking":
            raise Break()
        elif k == "branching":
            if self.value(c[0], env):
                self.block(c[1], env)
            elif len(c) > 2:
                self.block(c[2], env)
        elif k == "repeating_while":
            try:
                while self.value(c[0], env):
                    self.block(c[1], env)
            except Break:
                pass
        elif k in LOOP_NAMES:
            try:
                for item in self.loop_items(s, env):
                    self.tick()
                    for target, x in zip(c[:LOOP_NAMES[k]], item):
                        env[target.value] = x
                    self.block(c[-1], env)
            except Break:
                pass
        else:
            raise Fault(f"not an operation: {k}")
