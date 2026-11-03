"""The code world: the operation language (E:/vscode/analogy/poc2) as a world a lean SOV mind (fiction/lean.py)
acts in, with no change to the mind.

The world's interface is ForceWorld's, as the mind reads it:
    objs           the world's objects (here: the program's open slots, the pattern's roles, the spec)
    states()       object -> its current state, read as facts "<object>_<state>"
    invitations()  the pushes on offer: (strength, object, its state)
    act(inv)       apply a push (None: wait); returns the diffs, "<object>: <from> -> <to>"
    t, horizon, diffs, tree

The states (the user's design, 2026-10-26): each facet role of the pattern, filled or empty, and the spec, passing or
failing. A role filled is the code world's "latch_connecting"; a condition the mind learns is a role dependency, found by
the contrast learner as it found the wind.

My choices (named, to be revised by what the rungs find):
- A slot is an open value of the program; its state is the roles its value plays in the pattern ('pair-output.
  right-part+...'), 'none' when it plays none, 'empty' when unfilled. Not the value's text: an edit always changes the
  text, so every edit "took", every slot was held at once, and refilling one pulled only at the curiosity floor while
  running pulled at the want's control (rung 0, first run: 4 edits, then 396 runs). With roles, an edit that plays no
  role leaves its slot as it was: the latch did not give.
  The state also carries the slot's abstract values over the spec's cases, the set of what it came to ('=value',
  '=empty', '=fault', joined: '=value/fault'; '=unreached'): POC.md 3h's domain. The set, not "non-empty in any case":
  v5[v4] is non-empty at the first position and faults after, and read as 'value' it looked like v1[v4]. Roles tell whether a value fits the pattern; the
  value tells whether it does anything. Roles alone could not tell junk from the answer when a facet is satisfied by
  both (rung 3: v5[v4:v4], always '', plays the same roles as v5, because the facets resolve a loop's item to its
  sequence; the junk fill "took", every role read filled, and the mind ran a failing spec 600 times). Every case, not
  one probe input: a probe can read empty for a fill that is non-empty elsewhere.
- A push on a slot fills it with a complete value: one operation of the slot's type (grammar.expansions) with each of
  its inputs a leaf in scope (a name or a constant). Its strength is the value printed: each fill is its own push, as
  'light' and 'hard' are.
- Running the program is the push on the spec ('run'): the spec flips failing -> passing when every case passes
  (specs.CASES, run by the interpreter), and does not move otherwise. Editing is pushing the latch; running is pushing
  the lid.
- The pattern's roles are perceived after every push (structure is seen as it changes, as a latch is seen to part).

poc2 and fiction/ both have a grammar.py and a printer.py; poc2's come first on the path. The lean mind's imports
(beats, memory, ownership, worlds) are not among them.
"""
import itertools
import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
FICTION = os.path.join(os.path.dirname(HERE), "fiction")
ANALOGY = os.environ.get("ANALOGY", "E:/vscode/analogy")
sys.path.insert(0, FICTION)
sys.path.insert(0, os.path.join(ANALOGY, "poc2"))

import grammar as G  # noqa: E402  (poc2's)
import interp  # noqa: E402
import specs  # noqa: E402
from printer import to_python, value  # noqa: E402  (poc2's)
from rules import FACETS  # noqa: E402
from specs import CASES, run_case  # noqa: E402
import lean  # noqa: E402  (fiction's)

LEAVES = {"name", "constant", "function"}


class CodeWorld:
    still = True   # nothing changes between the mind's pushes unless it acts (no wind): waiting brings nothing
    gamma = 0.7    # how a push's later effects are discounted (ForceWorld's; Gerundelle reads it)

    def renew(self):
        """ForceWorld sets a scene back at an episode's end; a code world has no episodes (Gerundelle calls it)."""

    def __init__(self, program, slots, domain, theory, facets, name="code", order=None, last=None, spec="spec",
                 first=None):
        """program: a poc2 module tree; slots: {slot name: path of an open value}; domain: the spec's cases;
        theory, facets: the pattern whose roles are perceived (facet names of rules.FACETS[theory]).
        order: a seed. The mind breaks ties among equal pushes by the push itself (alphabetically), so a fill's text
        decides which untried fill comes first; with a seed each fill's strength is prefixed by its place in a
        shuffled order ('042 v2[v4]'), so the order is fair. last: a fill (by its text) put last in that order (the
        fair test of fiction's rung 6: the answer cannot come first by its name). spec: the spec's object name (a
        second scene names its own, so nothing carries over by identity: fiction rung 6, the chest's lid)."""
        self.spec = spec
        self.program, self.domain, self.name = program, domain, name
        self.slots = dict(slots)
        self.facets = [f for f in FACETS[theory] if f.__name__ in facets]
        self.roles = [f"{f.__name__.replace('ps_', '').replace('pub_', '')}.{r}" for f in self.facets for r in f.roles]
        for s, p in self.slots.items():   # the slots start open
            node = G.find(self.program, p).node
            if node.kind != "hole":
                self.program = G.replace(self.program, p, G.hole("expr", self._type(p)))
        self.passing = False
        self._cache = {}   # (spec, program text) -> (passes, {slot: abstract value})
        self.version = 0   # the program's changes, counted (the key of the read state)
        self.objs = {o: None for o in list(self.slots) + self.roles + [self.spec]}
        self.t, self.horizon, self.diffs = 0, 1, []
        self.tree = SimpleNamespace(doer=None, kids=[])   # no force tree: nothing is carried (worlds.carried)
        self._fills = {s: self._complete_fills(p) for s, p in self.slots.items()}
        if order is not None:
            import random
            for s, fills in self._fills.items():
                labels = sorted(fills)
                random.Random(order).shuffle(labels)
                if last in labels:
                    labels.remove(last)
                    labels.append(last)   # ties go to the largest strength: the end of the list gets rank 000
                if first in labels:   # the largest rank: tried first by the lean mind's tie-break, last by an agent
                    labels.remove(first)   # that takes the smallest first (Gerundelle's preparations are sorted)
                    labels.insert(0, first)
                self._fills[s] = {f"{len(labels) - 1 - k:03d} {lab}": fills[lab] for k, lab in enumerate(labels)}
        for fills in self._fills.values():   # each fill is its own push strength, of size 1 (lean.AMOUNTS)
            for label in fills:
                lean.AMOUNTS.setdefault(label, 1.0)
        lean.AMOUNTS.setdefault("run", 1.0)

    # ---- reading the configuration ----------------------------------------------------------------

    def _type(self, path):
        v = G.find(self.program, path)
        return v.node.type if v.node.kind == "hole" else G.infer(v.node, v.scope)

    def _complete_fills(self, path):
        """Every complete value for the slot: an operation of its type with leaf inputs, or a leaf. label -> node."""
        out = {}
        base = G.replace(self.program, path, G.hole("expr", self._type(path)))
        for opt in G.expansions(base, path):
            tree = G.replace(base, path, opt)
            subs = [v.path for v in G.holes(tree) if v.path[:len(path)] == path and v.path != path]
            choices = [[o for o in G.expansions(tree, sp) if o.kind in LEAVES] for sp in subs]
            for pick in itertools.product(*choices):
                t2 = tree
                for sp, leaf in zip(subs, pick):
                    t2 = G.replace(t2, sp, leaf)
                node = G.find(t2, path).node
                if any(n.kind == "hole" for n in G.walk(node)):
                    continue
                if any(p[:len(path)] == path for p, _ in G.check(t2, holes_ok=True)):
                    continue   # ill-typed in place
                out.setdefault(value(node), node)
        return out

    def role_nodes(self):
        """role -> the ids of the nodes filling it, over every match of the pattern's facets."""
        out = {r: set() for r in self.roles}
        for f in self.facets:
            try:
                ms = f.matches(self.program)
            except Exception:   # a partly built program a matcher cannot read: nothing matched
                ms = []
            key = f.__name__.replace("ps_", "").replace("pub_", "")
            for m in ms:
                for r, n in m.items():
                    if n is not None:
                        out[f"{key}.{r}"].add(id(n))
        return out

    def states(self, tree=None):
        """Read once per configuration: the mind reads the world many times a tick (every push's value reads the
        facts), and matching the facets and printing the program each time made the sweeps hours long."""
        key = (self.version, self.passing)   # bumped by every change to the program
        if getattr(self, "_states", (None,))[0] != key:
            self._states = (key, self._read())
        return dict(self._states[1])

    def _read(self):
        out, roles = {}, self.role_nodes()
        for s, p in self.slots.items():
            n = G.find(self.program, p).node
            inside = {id(x) for x in G.walk(n)}
            plays = sorted(r.replace("_", "-") for r, ids in roles.items() if ids & inside)
            out[s] = "empty" if n.kind == "hole" else ("+".join(plays) or "none") + "=" + self.evaluate()[1][s]
        out.update({r: "filled" if ids else "empty" for r, ids in roles.items()})
        out[self.spec] = "passing" if self.passing else "failing"
        return out

    def invitations(self, tree=None):
        # what invites a fill is the slot being there, not what fills it now: the slot's state stays in the facts.
        # (First the slot's state, as a force world's gerund: a fill into a slot holding junk and the same fill into
        # an empty one were two actions, every change of state made every fill untried again, and Gerundelle
        # re-tried the same fills under each new state; the lean code mind met it at rung 7, patched in its own
        # choose.)
        out = [(label, s, "slot") for s, fills in self._fills.items() for label in fills]
        return sorted(out) + [("run", self.spec, "passing" if self.passing else "failing")]

    # ---- acting -----------------------------------------------------------------------------------

    def evaluate(self):
        """Every case of the spec, by the interpreter, watching what each slot's value comes to: (all passed,
        {slot: 'value' | 'empty' | 'fault' | 'unreached'}). Cached by the program's text."""
        key = (self.domain, to_python(self.program))   # the spec too: it can change (rung 4)
        if key in self._cache:
            return self._cache[key]
        ids = {id(G.find(self.program, p).node): s for s, p in self.slots.items()}
        seen = {s: set() for s in self.slots}

        class Watching(interp.Machine):
            def value(m, n, env):
                s = ids.get(id(n))
                if s is None:
                    return interp.Machine.value(m, n, env)
                try:
                    v = interp.Machine.value(m, n, env)
                except interp.Fault:
                    seen[s].add("fault")
                    raise
                seen[s].add("empty" if isinstance(v, (str, list, dict, tuple)) and not v else "value")
                return v
        old, specs.Machine = specs.Machine, Watching
        try:
            passed = all([not run_case(c, self.program) for c in CASES[self.domain]])
        finally:
            specs.Machine = old
        out = (passed, {s: "/".join(k for k in ("value", "empty", "fault") if k in v) or "unreached"
                        for s, v in seen.items()})
        self._cache[key] = out
        return out

    def run(self):
        """Every case of the spec, by the interpreter: True if all pass."""
        return self.evaluate()[0]

    def act(self, inv=None, hold=False):
        before = self.states()
        if inv is not None and inv[1] == self.spec:
            self.passing = self.run()
        elif inv is not None:
            self.program = G.replace(self.program, self.slots[inv[1]], self._fills[inv[1]][inv[0]])
            self.version += 1
            self.passing = False   # an edit: nothing has run since
        after = self.states()
        filled = inv is not None and inv[1] != self.spec
        # a fill sets the configuration it governs, the slots and the roles read off them, whatever was there: it
        # reports all of it, re-made or not, so a fill has one outcome (first only what differed, and a fill that
        # re-made the slot's state read as doing nothing: the same fill did something or nothing by what was there
        # before, and Gerundelle studied the fills' "conditions" instead of running the spec)
        governed = set(self.slots) | set(self.roles) if filled else set()
        self.diffs = [f"{o}: {before[o]} -> {after[o]}" for o in after if (after[o] != before[o] or o in governed)
                      and not (o == self.spec and filled)]   # an edit is not a run
        self.t += 1
        return self.diffs

    def shape(self, slot, node):
        """A value's shape without its names: each name read as where it comes from (ext: a parameter or module
        state; loc: the function's own), as POC3's skeletons keep it (skeleton.strip, policy origin); constants
        kept. indexing(v2, v4) -> 'indexing(ext, loc)'."""
        fi = self.slots[slot][1]
        f = self.program.kids[1].kids[fi]
        ext = {s.kids[0].value for s in self.program.kids[0].kids} | {p.value for p in f.kids[0].kids}

        def go(n):
            if n.kind == "name":
                return "ext" if n.value in ext else "loc"
            if n.kind == "constant":
                return repr(n.value)
            return f"{n.kind}({', '.join(go(k) for k in n.kids)})" if n.kids else n.kind
        return go(node)

    def python(self):
        return to_python(self.program)
