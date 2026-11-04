"""Search helpers (PoC step 3, rebuilt): skeletons, limits, unsatisfiability, canonical
forms and rollouts, for seeded mutation search (mutate.py).

MCTS from empty bodies (poc/mcts.py) isn't carried over: it hit the stop trigger
(POC.md 3a) and seeded mutation search replaced it. What it contributed lives here:
- skeleton(): a domain's given signatures and state, with every body open.
- options(): the expansions of a hole that keep a program within the limits.
- feasible(): False when an undecided rule needs an operation kind that can no
  longer be added (unsatisfiability pruning).
- canonical(): the printed program with locals renamed in order of appearance.
- Filler.rollout(): fill every hole, depth-first with backtracking, trying options in
  weighted random order (fewer new holes, names not read yet, a returning while one is
  missing, and parts of what the edit removed are likelier), skipping any option a
  rule already rejects.
"""
import random
from collections import Counter

from grammar import EXPR_KINDS, LOOPS, Node, block, expansions, find, hole, holes, infer, replace, walk
from printer import to_python
from references import REFERENCES
from rules import reads_writes
from rulesets import judge, ruleset

MAX_STMTS = 4         # operations per block
MAX_BLOCK_DEPTH = 4   # a function body is depth 1 (raised from 3: publishing over keys and values needs 4)
MAX_EXPR_DEPTH = 4    # value holes may sit at most this many values deep (raised from 3: command undo)
MAX_NODES = 50        # per function body (raised from 30: run-length encoding needs 48)
RETURN_BOOST = 20     # rollout weight on returning while a function that must return has none
REUSE_BOOST = 5.0     # refill weight on a part of what the edit removed
REFILL_BUDGET = 300   # fills one refill may try, over all its attempts
BRANCH = 3            # options a refill attempt tries at each hole before backing up
MAX_ATTEMPTS = 20     # fresh attempts one refill may make
REWRITE_BUDGET = 600  # fills the rewrite enumeration may try


def skeleton(domain):
    """The domain's given signatures and state, with every function body open."""
    tree = REFERENCES[domain]()
    for i in range(len(tree.kids[1].kids)):
        tree = replace(tree, (1, i, 1), block(hole("stmts")))
    return tree


# ---- limits ------------------------------------------------------------------

def context(tree, path):
    """At path: value depth, block nesting, the enclosing block's length, and the
    enclosing function."""
    n, depth, blocks, block_len, fn = tree, 0, 0, 0, None
    for i in path:
        if n.kind == "block":
            blocks, block_len = blocks + 1, len(n.kids)
        n = n.kids[i]
        if n.kind == "func":
            fn = n
        depth += n.kind in EXPR_KINDS
    return depth, blocks, block_len, fn


def size(n):
    return sum(1 for _ in walk(n))


def options(tree, path, hole_node, max_nodes=MAX_NODES):
    """Expansions of the hole at path that keep the program within the limits."""
    depth, blocks, block_len, fn = context(tree, path)
    fsize = size(fn.kids[1])
    out = []
    for e in expansions(tree, path):
        if isinstance(e, list):  # "stmts": done, or one more operation
            if e and (block_len - 1 >= MAX_STMTS or fsize + 1 > max_nodes):
                continue
        elif fsize - 1 + size(e) > max_nodes:
            continue
        elif blocks >= MAX_BLOCK_DEPTH and any(x.kind == "block" for x in walk(e)):
            continue
        elif hole_node.value == "expr" and depth + 1 > MAX_EXPR_DEPTH and any(x.kind == "hole" for x in walk(e)):
            continue
        out.append(e)
    return out, fn


# ---- unsatisfiability ----------------------------------------------------------
# A rule that needs an operation kind which is missing can no longer become true when
# no open slot or not enough node budget is left. Costs are lower bounds (fewest nodes
# a new operation of that kind adds in place of an operation hole).

def all_rules():
    from rulesets import DOMAINS, ruleset
    return {r.__name__: r for d in DOMAINS for r in ruleset(d)}


# Built from the rules' own `needs` attributes, so renaming a rule can't silently drop
# its unsatisfiability check (ASSUMPTIONS.md R13).
NEEDS = {nm: r.needs for nm, r in all_rules().items() if hasattr(r, "needs")}
COST = {"loop": 4, "branching": 3, "returning": 1}  # loop over x: op  /  if c: op  /  return v
HAS_BLOCK = {"loop", "branching"}


def category(n):
    return "loop" if n.kind in LOOPS else n.kind


def slots(tree, max_nodes):
    fs = tree.kids[1].kids
    open_ = {f.value: [] for f in fs}
    for v in holes(tree):
        if v.node.value in ("stmt", "stmts") and v.path[0] == 1:
            open_[fs[v.path[1]].value].append(context(tree, v.path)[1])
    return {f.value: (max_nodes - size(f.kids[1]), open_[f.value]) for f in fs}


def feasible(tree, results, max_nodes=MAX_NODES):
    """False if some undecided rule needs an operation that can no longer be added."""
    room = slots(tree, max_nodes)
    present = {category(n) for n in walk(tree.kids[1])}
    missing = set()
    for rule, needed in NEEDS.items():
        if rule in results and results[rule] is None:  # in this ruleset and undecided
            missing |= needed - present
    usable = {f: r for f, (r, open_) in room.items() if open_}
    for kind in missing:
        def nest_ok(open_):
            return kind not in HAS_BLOCK or any(d < MAX_BLOCK_DEPTH for d in open_)
        if not any(r >= COST[kind] and nest_ok(room[f][1]) for f, r in usable.items()):
            return False
    if sum(COST[k] for k in missing) > sum(usable.values()):
        return False
    if "returns_value" in results and results["returns_value"] is None:
        for f in tree.kids[1].kids:
            if f.type.args[0].name != "none" and not any(n.kind == "returning" for n in walk(f.kids[1])):
                r, open_ = room[f.value]
                if not open_ or r < COST["returning"]:
                    return False
    return True


# ---- canonical form ------------------------------------------------------------

def canonical(tree):
    """The printed program with locals renamed in order of appearance, per function."""
    state = {s.kids[0].value for s in tree.kids[0].kids}

    def rename(n, names):
        if n.kind == "name" and n.value in names:
            return Node("name", [], names[n.value], n.type)
        return Node(n.kind, [rename(c, names) for c in n.kids], n.value, n.type)

    funcs = []
    for f in tree.kids[1].kids:
        keep = state | {p.value for p in f.kids[0].kids}
        names = {}
        for n in walk(f.kids[1]):
            if n.kind == "name" and n.value not in keep and n.value not in names:
                names[n.value] = f"x{len(names) + 1}"
        funcs.append(rename(f, names))
    return to_python(Node("module", [tree.kids[0], Node("funcs", funcs)]))


# ---- rollouts ------------------------------------------------------------------

def copy(n):
    return Node(n.kind, [copy(c) for c in n.kids], n.value, n.type)

class Filler:
    """Fills holes at random for a domain (the refill step of mutation search)."""

    def __init__(self, domain, seed=0):
        self.rules = ruleset(domain)
        self.rng = random.Random(seed)
        self.stats = Counter()

    def viable(self, program, path, opts):
        """Drop "finish this block" when finishing fails a rule at once."""
        return [e for e in opts if not (isinstance(e, list) and not e
                                        and False in judge(self.rules, replace(program, path, e)).values())]

    def weights(self, opts, fn):
        """Fewer new holes, names not read yet, and a returning while one is missing, are
        likelier. 1/(1 + holes): the squared form of poc/ (meant to stop programs growing
        without bound from empty bodies) made nested values like [(x, y)] too rare."""
        unread = {p.value for p in fn.kids[0].kids} - reads_writes(fn)[0]
        needs_return = fn.type.args[0].name != "none" and not any(n.kind == "returning" for n in walk(fn.kids[1]))
        out = []
        for e in opts:
            if isinstance(e, list):
                out.append(1.0)
                continue
            w = 1.0 / (1 + sum(x.kind == "hole" for x in walk(e)))
            if any(x.kind == "name" and x.value in unread for x in walk(e)):
                w *= 3
            if needs_return and e.kind == "returning":
                w *= RETURN_BOOST
            out.append(w)
        return out

    def reusable(self, program, path, hole_node, reuse):
        """Parts of what an edit removed that fit this value hole: the right type, with
        every name they read in scope here."""
        sc = find(program, path).scope
        return [copy(r) for r in reuse if infer(r, sc) == hole_node.type]

    def rollout(self, program, reuse=(), budget=REFILL_BUDGET):
        """The program with every hole filled, or None if none was found within `budget`
        fills. Each attempt is depth-first: at every hole it tries the top BRANCH options
        of a weighted random order, skipping any a rule rejects (False is final), and backs
        up from dead ends. A failed attempt restarts with a fresh order.

        Plain greedy picks led into corners nothing completes (ASSUMPTIONS.md X1); full
        backtracking spent its whole budget inside the first wide sub-tree it tried, so
        each hole now gets at most BRANCH tries per attempt. `reuse` holds parts of what
        the edit removed; they're offered first wherever they fit (X5, X8)."""
        self.fills = 0
        for _ in range(MAX_ATTEMPTS):
            before = self.fills
            done = self._fill(program, list(reuse), budget, BRANCH)
            if done is not None:
                return done
            if self.fills == before or self.fills >= budget:
                break  # nothing left to try (an attempt that fills nothing would repeat forever)
        self.stats["dead_end"] += 1
        return None

    def candidates(self, program, path, h, reuse, reuse_only):
        """(options, weights) for the hole at path. With reuse_only, a value hole may only
        take a part of what was removed, or wrap or pair such parts."""
        opts, fn = options(program, path, h)
        if h.value == "stmts":
            opts = self.viable(program, path, opts)
        if h.value == "expr" and reuse_only:
            again = self.reusable(program, path, h, reuse)
            builders = [e for e in opts if e.kind in ("wrapping", "pairing")]
            return again + builders, [REUSE_BOOST] * len(again) + [1.0] * len(builders)
        weights = self.weights(opts, fn)
        if h.value == "expr" and reuse:
            again = self.reusable(program, path, h, reuse)
            opts, weights = again + opts, [REUSE_BOOST] * len(again) + weights
        return opts, weights

    def _fill(self, program, reuse, budget, branch, reuse_only=False):
        hs = holes(program)
        if not hs:
            return program
        path, h = hs[0].path, hs[0].node
        opts, weights = self.candidates(program, path, h, reuse, reuse_only)
        # Weighted random order without replacement (Efraimidis-Spirakis keys).
        order = sorted(range(len(opts)), key=lambda i: self.rng.random() ** (1.0 / weights[i]), reverse=True)
        tried = 0
        for i in order:
            if self.fills >= budget or tried >= branch:
                return None
            self.fills += 1
            filled = replace(program, path, opts[i])
            res = judge(self.rules, filled)
            if False in res.values() or (h.value in ("stmt", "stmts") and not feasible(filled, res)):
                self.stats["pruned_pick"] += 1
                continue
            tried += 1
            done = self._fill(filled, reuse, budget, branch, reuse_only)
            if done is not None:
                return done
        return None

    def rewrites(self, program, path, reuse, budget=REWRITE_BUDGET):
        """Every way to replace the operation hole at path using only the removed parts
        (and wrapping or pairing them): the same inputs, a different operation, e.g.
        appending(x, p) -> accumulating(x, [p]) -> inserting(x, i, p). Enumerated, not
        sampled, so a rewrite one step away is always found (ASSUMPTIONS.md X8)."""
        self.fills, out = 0, []
        h = hole("stmt")
        for e in self.candidates(program, path, h, reuse, False)[0]:
            if self.fills >= budget:
                break
            names = {x.value for x in walk(e) if x.kind == "name"}
            if not names <= {x.value for r in reuse for x in walk(r) if x.kind == "name"}:
                continue  # an operation that names something the removed one didn't
            filled = replace(program, path, e)
            if False in judge(self.rules, filled).values():
                continue
            done = self._fill(filled, reuse, budget, 99, reuse_only=True)
            if done is not None:
                out.append(done)
        return out
