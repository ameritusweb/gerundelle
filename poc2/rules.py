"""Rules over operation trees (PoC step 2, rebuilt after the assumptions audit).

rule(tree) -> True, False or None. Rules are structural: they read the tree and never
run it. On a partial tree a rule may answer None (not decided yet). A False is final,
so a search can prune on it. Every rule declares its kind (`rule.kind`):
- "exists": some pattern appears. True as soon as it does (patterns match finished
  nodes only and only ask for things to be present, so a match stays a match); False
  only once the tree has no holes left.
- "never": a pattern must not appear. False as soon as it does.
- "every": a property of all matches, decided once its scope (the tree, or one
  function) has no holes left.
dataflow.judge_complete() uses the kind: an exists-rule passes if the program or its
inlined copy passes it; a never- or every-rule fails if either copy fails.

Three layers:
- BASE rules: what every program needs (hygiene from the audit rounds of poc/).
- THEORY facets: structural patterns with named roles (theory_facets()). Core facets
  are validity rules every program of the theory passes; all facets give labels: a
  concept's fingerprint is the set of (facet, role) pairs it occupies (fingerprint()).
  Roles are defined by the theory, not the domain, so they transfer across domains.
- MUSTS per domain: weak necessary conditions every correct program of the domain
  meets, kept only for early pruning. The behavior spec (specs.py) defines the domain;
  domain rules that tried to define it encoded one implementation's shape (POC.md).

Theory facets follow data flow: a value's origin is found through access chains,
temporaries bound once, aliases and loop names (resolve()), so routing a value through
a local doesn't hide a pattern.
"""
from itertools import combinations

from grammar import LOOP_NAMES, LOOPS, NONE, STR, infer, visit, walk

ACCESSING = {"indexing", "slicing_before", "slicing_from", "slicing_between"}
CHAINING = ACCESSING | {"looking_up"}
CHANGING_OPS = {"appending", "inserting", "removing", "storing", "deleting", "popping"}


def named(label, kind):
    def wrap(fn):
        fn.__name__ = label
        fn.kind = kind
        return fn
    return wrap


# ---- queries -----------------------------------------------------------------

def funcs(tree):
    return {f.value: f for f in tree.kids[1].kids}


def state(tree):
    return {s.kids[0].value for s in tree.kids[0].kids}


def params(f):
    return [p.value for p in f.kids[0].kids]


_FINISHED = {}  # id(node) -> (node, finished); cleared by rulesets.judge; the node is kept so an id can't be reused


def finished(n):
    hit = _FINISHED.get(id(n))
    if hit is not None and hit[0] is n:
        return hit[1]
    v = all(x.kind != "hole" for x in walk(n))
    _FINISHED[id(n)] = (n, v)
    return v


def root(n):
    """The name at the base of an access chain (v1 for v1[k][:i]), else None."""
    while n.kind in CHAINING:
        n = n.kids[0]
    return n.value if n.kind == "name" else None


def same(a, b):
    """Structurally identical and finished (a hole equals nothing)."""
    return (a.kind == b.kind != "hole" and a.value == b.value and a.type == b.type
            and len(a.kids) == len(b.kids) and all(same(x, y) for x, y in zip(a.kids, b.kids)))


def same_c(a, b):
    """same(), treating == / != comparisons, adding and combining as commutative."""
    if a.kind != b.kind or a.kind == "hole" or a.value != b.value or len(a.kids) != len(b.kids):
        return False
    if a.kind in ("adding", "combining") or (a.kind == "comparing" and a.value in ("==", "!=")):
        x, y = a.kids
        return (same_c(x, b.kids[0]) and same_c(y, b.kids[1])) or (same_c(x, b.kids[1]) and same_c(y, b.kids[0]))
    return a.type == b.type and all(same_c(x, y) for x, y in zip(a.kids, b.kids))


def loop_names(n):
    return [x.value for x in n.kids[:LOOP_NAMES[n.kind]]] if n.kind in LOOP_NAMES else []


def loop_sources(n):
    """What a loop iterates over (not a while loop's condition)."""
    return n.kids[LOOP_NAMES[n.kind]:-1] if n.kind in LOOP_NAMES and n.kind != "repeating_while" else []


def names_in(n):
    return {x.value for x in walk(n) if x.kind == "name"}


def standalone(f):
    """The operations of f that stand alone (directly in a block), in order."""
    return [s for b in walk(f.kids[1]) if b.kind == "block" for s in b.kids if s.kind != "hole"]


def exists(found, tree):
    return True if found else (False if finished(tree) else None)


def never(found, tree):
    return False if found else (True if finished(tree) else None)


def every(ok, tree):
    return ok if finished(tree) else None


def per_function(tree, check):
    """check(f) on each finished function: False if one fails, True once all pass."""
    fs = list(funcs(tree).values())
    done = [f for f in fs if finished(f)]
    if not all(check(f) for f in done):
        return False
    return True if len(done) == len(fs) else None


# ---- data flow: where values come from ------------------------------------------------

def writes(f):
    """How many operations bind or change each name in f."""
    out = {}
    for n in walk(f.kids[1]):
        names = []
        if n.kind in ("binding", "accumulating"):
            names = [n.kids[0].value]
        elif n.kind == "destructuring":
            names = [n.kids[0].value, n.kids[1].value]
        elif n.kind in LOOP_NAMES:
            names = loop_names(n)
        for nm in names:
            out[nm] = out.get(nm, 0) + 1
    return out


def binders(f):
    """name -> the value it comes from, for locals bound exactly once: a binding's value,
    or a loop's source for the names that take its items, keys or values. A loop's
    position names (iterating over positions, the index of iterating with positions)
    come from no collection."""
    count, out = writes(f), {}
    for n in walk(f.kids[1]):
        if n.kind == "binding" and count.get(n.kids[0].value) == 1:
            out[n.kids[0].value] = n.kids[1]
        elif n.kind in LOOP_NAMES and n.kind != "repeating_while":
            names, src = loop_names(n), loop_sources(n)
            pairs = {"iterating_over_items": [(0, 0)], "iterating_with_positions": [(1, 0)],
                     "iterating_together": [(0, 0), (1, 1)], "iterating_over_keys": [(0, 0)],
                     "iterating_over_keys_and_values": [(0, 0), (1, 0)]}.get(n.kind, [])
            for ni, si in pairs:
                if count.get(names[ni]) == 1:
                    out[names[ni]] = src[si]
    return out


def resolve(n, f, st, seen=None):
    """The state or parameter name a value comes from (following access chains,
    temporaries bound once, aliases and loop names), else the local name it reaches,
    else None."""
    seen = seen or set()
    while n.kind in CHAINING:
        n = n.kids[0]
    if n.kind != "name":
        return None
    nm = n.value
    if nm in st or nm in params(f) or nm in seen:
        return nm
    src = binders(f).get(nm)
    return resolve(src, f, st, seen | {nm}) if src is not None else nm


def alias_root(nm, f):
    """The name a local is an alias of (bound once to just that name), followed to the end."""
    b, seen = binders(f), set()
    while nm in b and b[nm].kind == "name" and nm not in seen:
        seen.add(nm)
        nm = b[nm].value
    return nm


def updated(s):
    """Names an operation updates: binds, accumulates into, or changes a collection of."""
    k = s.kind
    if k in ("binding", "accumulating"):
        return {s.kids[0].value}
    if k == "destructuring":
        return {s.kids[0].value, s.kids[1].value}
    if k in CHANGING_OPS:
        return {root(s.kids[0])} - {None}
    return set()


def reads_writes(f):
    """Names a function body reads, and names it binds."""
    reads, bound = set(), set()

    def go(n):
        if n.kind == "binding":
            bound.add(n.kids[0].value)
            go(n.kids[1])
        elif n.kind == "destructuring":
            bound.update({n.kids[0].value, n.kids[1].value})
            go(n.kids[2])
        elif n.kind == "accumulating":
            bound.add(n.kids[0].value)
            reads.add(n.kids[0].value)
            go(n.kids[1])
        elif n.kind in LOOP_NAMES:
            bound.update(loop_names(n))
            for c in n.kids[LOOP_NAMES[n.kind]:]:
                go(c)
        elif n.kind == "name":
            reads.add(n.value)
        else:
            for c in n.kids:
                go(c)
    go(f.kids[1])
    return reads, bound


def locals_declared(f):
    return reads_writes(f)[1] - set(params(f))


def real_reads(f):
    """Names read somewhere other than in their own updates (x += x, x.append(x[0]) and
    x = x + [y] don't count as reads of x)."""
    out = set()

    def go(block):
        for s in block.kids:
            if s.kind in ("branching", "repeating_while"):
                out.update(names_in(s.kids[0]))
                for b in s.kids[1:]:
                    go(b)
            elif s.kind in LOOP_NAMES:
                for src in loop_sources(s):
                    out.update(names_in(src))
                go(s.kids[-1])
            elif s.kind != "hole":
                targets = {s.kids[0].value} if s.kind == "binding" else \
                    {s.kids[0].value, s.kids[1].value} if s.kind == "destructuring" else set()
                out.update(names_in(s) - targets - updated(s))
    go(f.kids[1])
    return out


def loop_bound(f):
    return {x for n in walk(f.kids[1]) for x in loop_names(n)}


# ---- base rules ----------------------------------------------------------------

@named("uses_params", "every")
def uses_params(tree):
    """Every function reads all its parameters."""
    return per_function(tree, lambda f: set(params(f)) <= reads_writes(f)[0])


@named("returns_value", "every")
def returns_value(tree):
    """A function with a return type has a returning operation."""
    return per_function(tree, lambda f: f.type.args[0] == NONE or any(n.kind == "returning" for n in walk(f.kids[1])))


@named("no_dead_locals", "every")
def no_dead_locals(tree):
    """Every local a function binds is read somewhere other than in its own updates; a
    local that's an alias of another (v6 = v3) counts as read when that one is."""
    def ok(f):
        reads = real_reads(f)
        return all(nm in reads or alias_root(nm, f) in reads for nm in locals_declared(f) - state(tree))
    return per_function(tree, ok)


@named("uses_state", "exists")
def uses_state(tree):
    """Every piece of module state is used by some function."""
    used = set().union(*(set().union(*reads_writes(f)) for f in funcs(tree).values()))
    return exists(state(tree) <= used, tree)


@named("no_self_assign", "never")
def no_self_assign(tree):
    """Nothing is bound to itself (x = x)."""
    return never(any(n.kind == "binding" and same(n.kids[0], n.kids[1]) for n in walk(tree)), tree)


def no_aliases(tree):
    """No local is bound to a bare name (y = x): an alias adds nothing a read of x doesn't
    (POC3 audit: the skeleton search bound a temporary to the result list inside the loop
    and appended through it). Module state may be bound to a name: that's storing a value
    (double buffering's `back = incoming`; ASSUMPTIONS.md W28)."""
    st = state(tree)
    return never(any(n.kind == "binding" and n.kids[1].kind == "name" and n.kids[0].value not in st
                     for n in walk(tree)), tree)


def unreachable(b):
    """A block has something after a returning or breaking (an open end doesn't count)."""
    ends = [i for i, s in enumerate(b.kids) if s.kind in ("returning", "breaking")]
    return bool(ends) and any(not (s.kind == "hole" and s.value == "stmts") for s in b.kids[ends[0] + 1:])


@named("no_unreachable", "never")
def no_unreachable(tree):
    """No operation follows a returning or breaking in the same block."""
    return never(any(n.kind == "block" and unreachable(n) for n in walk(tree)), tree)


@named("no_empty_blocks", "never")
def no_empty_blocks(tree):
    """Every body has at least one operation."""
    return never(any(n.kind == "block" and not n.kids for n in walk(tree)), tree)


LITERALS = {"creating_empty", "wrapping", "pairing", "constant"}
OPERAND_SLOTS = {"indexing": [0], "slicing_before": [0], "slicing_from": [0], "slicing_between": [0],
                 "measuring": [0], "looking_up": [0], "popping": [0], "appending": [0], "inserting": [0],
                 "removing": [0], "storing": [0], "deleting": [0], "testing_membership": [1],
                 "testing_emptiness": [0]}


@named("no_literal_access", "never")
def no_literal_access(tree):
    """A literal is never the thing read, measured, changed or iterated over: no [][0],
    len(''), iterating over []. (A while loop's condition isn't something it iterates over.)"""
    def literal_operand(n):
        if n.kind in LOOP_NAMES:
            return any(s.kind in LITERALS for s in loop_sources(n))
        return n.kind in OPERAND_SLOTS and any(n.kids[i].kind in LITERALS for i in OPERAND_SLOTS[n.kind])
    return never(any(literal_operand(n) for n in walk(tree)), tree)


def is_const(x, v=None):
    return x.kind == "constant" and type(x.value) is not bool and (v is None or x.value == v)


@named("no_trivial_ops", "never")
def no_trivial_ops(tree):
    """No operation that does nothing or is constant: concatenating '' or [], adding 0,
    accumulating '' or [] or 0, an operation on constants only, comparing or combining
    a thing with itself (in either order) or combining with a constant, negating a
    constant, x in x, s[0:], s[:len(s)], s[:i][:i]."""
    def trivial(n):
        k, c = n.kind, n.kids
        if k == "concatenating":
            return any(x.kind == "creating_empty" or is_const(x, "") for x in c) or all(x.kind == "constant" for x in c)
        if k in ("adding", "subtracting"):
            return any(is_const(x, 0) for x in c[(0 if k == "adding" else 1):]) or all(x.kind == "constant" for x in c)
        if k == "accumulating":
            return c[1].kind == "creating_empty" or is_const(c[1], "") or is_const(c[1], 0)
        if k == "comparing":
            return same_c(c[0], c[1]) or c[0].kind == c[1].kind == "constant"
        if k == "combining":
            return same_c(c[0], c[1]) or any(x.kind == "constant" for x in c)
        if k == "negating":
            return c[0].kind == "constant"
        if k == "testing_membership":
            return same(c[0], c[1])
        if k == "slicing_from":
            return is_const(c[1], 0)
        if k == "slicing_before":
            return (c[1].kind == "measuring" and same(c[1].kids[0], c[0])) or \
                (c[0].kind == "slicing_before" and same(c[0].kids[1], c[1]))  # s[:i][:i]
        if k == "slicing_between":
            return is_const(c[1], 0) and c[2].kind == "measuring" and same(c[2].kids[0], c[0])
        return False
    return never(any(trivial(n) for n in walk(tree)), tree)


@named("no_recursion", "never")
def no_recursion(tree):
    """A function doesn't call itself."""
    return never(any(c.kind == "calling" and c.kids[0].kind == "function" and c.kids[0].value == f.value
                     for f in funcs(tree).values() for c in walk(f.kids[1])), tree)


@named("no_param_writes", "never")
def bound_names(n):
    """The names an operation rebinds: a binding's or accumulating's target, both targets
    of a destructuring."""
    if n.kind in ("binding", "accumulating"):
        return [n.kids[0].value]
    if n.kind == "destructuring":
        return [n.kids[0].value, n.kids[1].value]
    return []


def no_param_writes(tree):
    """Parameters are never rebound (changing a collection they hold is fine), not by a
    binding, an accumulating or a destructuring (POC3 audit round 5)."""
    return never(any(set(bound_names(n)) & set(params(f))
                     for f in funcs(tree).values() for n in walk(f.kids[1])), tree)


def exits(body):
    """A loop body contains a returning, or a breaking that isn't inside a nested loop."""
    def go(n, nested):
        if n.kind == "returning" or (n.kind == "breaking" and not nested):
            return True
        return any(go(c, nested or n.kind in LOOPS) for c in n.kids)
    return any(go(s, False) for s in body.kids)


@named("no_constant_conditions", "never")
def no_constant_conditions(tree):
    """A branching or repeating condition reads some name, except `while True` with a
    way out (a returning, or a breaking that isn't inside a nested loop): the event-loop
    idiom."""
    def bad(n):
        if n.kind not in ("branching", "repeating_while") or not finished(n.kids[0]) or names_in(n.kids[0]):
            return False
        if n.kind == "repeating_while" and n.kids[0].kind == "constant" and n.kids[0].value is True:
            return finished(n) and not exits(n.kids[1])
        return True
    return never(any(bad(n) for n in walk(tree)), tree)


@named("no_temp_edits", "never")
def no_temp_edits(tree):
    """Only named collections are changed: no v[i:].append(x), which changes a copy."""
    def temporary(n):
        while n.kind in ("indexing", "looking_up"):
            n = n.kids[0]
        return n.kind not in ("name", "hole")
    return never(any(n.kind in CHANGING_OPS and temporary(n.kids[0]) for n in walk(tree)), tree)


@named("no_loop_var_writes", "never")
def no_loop_var_writes(tree):
    """A loop's names aren't rebound inside the loop, not by a binding, an accumulating or
    a destructuring (POC3 audit round 5)."""
    def writes_own(loop):
        bound = set(loop_names(loop))
        return any(set(bound_names(n)) & bound for n in walk(loop.kids[-1]))
    return never(any(n.kind in LOOP_NAMES and writes_own(n) for n in walk(tree)), tree)


@named("no_disguised_constants", "every")
def no_disguised_constants(tree):
    """A condition doesn't read only locals that are only ever set to constants."""
    def ok(f):
        sets = {}
        for n in walk(f.kids[1]):
            if n.kind in ("binding", "accumulating"):
                sets.setdefault(n.kids[0].value, []).append(n.kids[1])
        bound = loop_bound(f) | set(params(f)) | state(tree)
        consts = {nm for nm, vals in sets.items() if nm not in bound and all(not names_in(v) for v in vals)}
        return not any(n.kind in ("branching", "repeating_while") and names_in(n.kids[0])
                       and names_in(n.kids[0]) <= consts for n in walk(f.kids[1]))
    return per_function(tree, ok)


@named("no_churn", "never")
def no_churn(tree):
    """No update that feeds a collection from itself or undoes itself: appending x.pop(),
    accumulating x into x, x = [x.pop()], or appending followed at once by popping."""
    def feeds_itself(n):
        if n.kind in ("appending", "inserting", "accumulating"):
            r = root(n.kids[0])
            return r is not None and r in names_in(n.kids[-1])
        if n.kind == "binding":
            r = n.kids[0].value
            return any(x.kind == "popping" and root(x.kids[0]) == r for x in walk(n.kids[1]))
        return False

    def undoes(b):
        return any(s.kind == "appending" and t.kind == "popping" and len(t.kids) == 1
                   and root(s.kids[0]) is not None and root(s.kids[0]) == root(t.kids[0])
                   for s, t in zip(b.kids, b.kids[1:]))
    return never(any(feeds_itself(n) or (n.kind == "block" and undoes(n)) for n in walk(tree)), tree)


@named("no_char_index", "never")
def no_char_index(tree):
    """No indexing or slicing of a single character: s[i][j], or c[j] where c takes the
    characters of a string."""
    chars, nodes = set(), []
    for v in visit(tree):
        n = v.node
        if len(v.path) < 2 or v.path[0] != 1:
            continue
        fname = tree.kids[1].kids[v.path[1]].value
        if n.kind in LOOP_NAMES and n.kind != "repeating_while":
            src = [infer(s, v.scope) for s in loop_sources(n)]
            names = loop_names(n)
            if n.kind == "iterating_over_items" and src[0] == STR:
                chars.add((fname, names[0]))
            elif n.kind == "iterating_with_positions" and src[0] == STR:
                chars.add((fname, names[1]))
            elif n.kind == "iterating_together":
                chars |= {(fname, nm) for nm, t in zip(names, src) if t == STR}
        if n.kind in ACCESSING:
            nodes.append((fname, n, v.scope))
    found = any((b.kind == "name" and (fname, b.value) in chars) or (b.kind == "indexing" and infer(b.kids[0], sc) == STR)
                for fname, n, sc in nodes for b in [n.kids[0]])
    return never(found, tree)


@named("no_overwritten_stores", "never")
def no_overwritten_stores(tree):
    """No binding overwritten before anything reads it (x = []; x = [])."""
    def overwritten(b):
        for i, s in enumerate(b.kids):
            if not (s.kind == "binding" and finished(s)):
                continue
            nm = s.kids[0].value
            for t in b.kids[i + 1:]:
                if not finished(t):
                    break
                if t.kind == "binding" and t.kids[0].value == nm:
                    if nm not in names_in(t.kids[1]):
                        return True
                    break
                if nm in names_in(t):
                    break
        return False
    return never(any(n.kind == "block" and overwritten(n) for n in walk(tree)), tree)


@named("no_len_index", "never")
def no_len_index(tree):
    """No s[len(...)]: indexing at a length is out of range whenever that length is at
    least the length of s."""
    return never(any(n.kind == "indexing" and n.kids[1].kind == "measuring" for n in walk(tree)), tree)


# ---- POC3 audit round 2 (skelsearch.py on the color line, 2026-10-21) ------------------
# The skeleton search admitted slices that are empty by construction, slices of slices,
# a list concatenated with itself, lengths of built values and reads into concatenations,
# all hidden behind a spec whose cases were too short to notice (ASSUMPTIONS.md W9).

BUILT = {"concatenating", "wrapping", "pairing", "creating_empty"}
SLICING = {"slicing_before", "slicing_from", "slicing_between"}


def const_int(n):
    return n.kind == "constant" and isinstance(n.value, int) and not isinstance(n.value, bool)


@named("no_empty_slices", "never")
def no_empty_slices(tree):
    """No slice that is empty whatever the data: s[:0], s[i:0], s[2:2], s[3:2], s[len(s):],
    s[len(s):k]."""
    def empty(n):
        k, c = n.kind, n.kids
        if k == "slicing_before":
            return const_int(c[1]) and c[1].value == 0
        if k == "slicing_from":
            return c[1].kind == "measuring" and same(c[1].kids[0], c[0])
        if k == "slicing_between":
            lo, hi = c[1], c[2]
            if const_int(hi) and hi.value == 0:
                return True
            if const_int(lo) and const_int(hi) and lo.value >= hi.value:
                return True
            if same_c(lo, hi):
                return True
            return lo.kind == "measuring" and same(lo.kids[0], c[0])
        return False
    return never(any(empty(n) for n in walk(tree)), tree)


@named("no_slice_of_slice", "never")
def no_slice_of_slice(tree):
    """No slicing or indexing of a slice (s[1:][:2], s[2:][0]): one access with the right
    bounds says the same."""
    return never(any(n.kind in ACCESSING and n.kids[0].kind in SLICING for n in walk(tree)), tree)


@named("no_self_concat", "never")
def no_self_concat(tree):
    """No sequence concatenated with itself (x + x)."""
    def doubled(n):
        return n.kind == "concatenating" and any(same(a, b) for a, b in zip(n.kids, n.kids[1:]))
    return never(any(doubled(n) for n in walk(tree)), tree)


@named("no_measuring_built", "never")
def no_measuring_built(tree):
    """No length of a value built or cut on the spot (len(a + b), len([x]), len(s[1:])):
    arithmetic on lengths says the same without building anything."""
    return never(any(n.kind == "measuring" and n.kids[0].kind in BUILT | ACCESSING for n in walk(tree)), tree)


@named("no_built_access", "never")
def no_built_access(tree):
    """No read into a concatenation ((a + b)[i], (a + b)[1:]): read the parts."""
    return never(any(n.kind in ACCESSING | {"measuring"} and n.kids[0].kind == "concatenating" for n in walk(tree)), tree)


@named("no_literal_destructuring", "never")
def no_literal_destructuring(tree):
    """No destructuring of a pair built on the spot (x, y = (a, b)): that's two bindings
    in disguise, and with the targets among the parts a self-assignment. The one
    exception is a swap (x, y = y, x). POC3 audit round 3 (pub/sub): v2, v1 = (v2, v1)."""
    def literal(n):
        if n.kind != "destructuring" or n.kids[2].kind != "pairing":
            return False
        a, b, (x, y) = n.kids[0], n.kids[1], n.kids[2].kids
        swap = x.kind == "name" and y.kind == "name" and x.value == b.value and y.value == a.value and a.value != b.value
        return not swap
    return never(any(literal(n) for n in walk(tree)), tree)


@named("no_double_constants", "never")
def no_double_constants(tree):
    """No sum or difference with two constants in it (3 + i + 3): fold them. POC3 audit
    round 4 (color line): x = 3 + i + 3 as an insert position, which Python clamps to an
    append."""
    def constants_in(n):
        if n.kind in ("adding", "subtracting"):
            return sum(constants_in(c) for c in n.kids)
        return 1 if n.kind == "constant" else 0
    return never(any(n.kind in ("adding", "subtracting") and constants_in(n) >= 2 for n in walk(tree)), tree)


@named("no_unread_loop_names", "never")
def no_unread_loop_names(tree):
    """Every name a loop binds is read in its body: no `for i, c in enumerate(s)` that
    never looks at c. (Loop names can't be rebound, so any occurrence in the body is a
    read.) Decided once the body is finished. POC3 audit round 5 (color line)."""
    def unread(loop):
        body = loop.kids[-1]
        return finished(body) and any(nm not in names_in(body) for nm in loop_names(loop))
    return never(any(n.kind in LOOP_NAMES and unread(n) for n in walk(tree)), tree)


@named("no_built_comparisons", "never")
def no_built_comparisons(tree):
    """No comparison or membership test on a value built on the spot ([i] + [1] == [i],
    x in [a, b]): compare the parts. POC3 audit round 5 (color line, gate rejects)."""
    return never(any(n.kind in ("comparing", "testing_membership", "testing_emptiness") and any(c.kind in BUILT for c in n.kids)
                     for n in walk(tree)), tree)


@named("no_insert_at_length", "never")
def no_insert_at_length(tree):
    """No inserting at a length (x.insert(len(y), v)): at the end that's appending, beyond
    it Python clamps to appending. POC3 audit round 6 (color line)."""
    return never(any(n.kind == "inserting" and n.kids[1].kind == "measuring" for n in walk(tree)), tree)


@named("no_edit_while_iterating", "never")
def no_edit_while_iterating(tree):
    """A loop doesn't change a collection it iterates over."""
    def edits(loop):
        roots = {root(s) for s in loop_sources(loop)} - {None}
        return bool(roots) and any(roots & updated(s) for s in walk(loop.kids[-1]))
    return never(any(n.kind in LOOP_NAMES and edits(n) for n in walk(tree)), tree)


@named("no_single_pass_loops", "never")
def no_single_pass_loops(tree):
    """A loop body doesn't return or break unconditionally (as its own operation): such
    a loop never runs a second time, so it's a branching in disguise."""
    return never(any(n.kind in LOOPS and any(s.kind in ("returning", "breaking") for s in n.kids[-1].kids)
                     for n in walk(tree)), tree)


@named("no_trailing_return", "never")
def no_trailing_return(tree):
    """A function that returns nothing doesn't end with a bare returning (it does nothing)."""
    return never(any(f.type.args[0] == NONE and f.kids[1].kids and f.kids[1].kids[-1].kind == "returning"
                     and not f.kids[1].kids[-1].kids for f in funcs(tree).values()), tree)


# ---- theory facets ------------------------------------------------------------------
# A facet is a structural pattern with named roles. facet.matches(tree) gives a list of
# {role: node} dicts; core facets are also validity rules (callable on a tree).

class Facet:
    def __init__(self, label, roles, find, kind="exists", core=False, check=None):
        self.__name__, self.roles, self.find, self.kind, self.core = label, roles, find, kind, core
        self.check = check  # for every-kind facets: tree -> bool, the property itself

    def matches(self, tree):
        return self.find(tree)

    def __call__(self, tree):
        if self.kind == "every":
            return every(self.check(tree), tree)
        return exists(bool(self.find(tree)), tree)


# -- parallel strings -------------------------------------------------------------------

class Access:
    """A position access: the sequence it reads (resolved), the node doing it, and its
    position (a kind: index, before, from, between; and the position's node(s))."""

    def __init__(self, seq, node, kind, pos):
        self.seq, self.node, self.kind, self.pos = seq, node, kind, pos

    def same_position(self, other):
        return self.kind == other.kind and len(self.pos) == len(other.pos) and all(
            (a is b) or same(a, b) for a, b in zip(self.pos, other.pos))


def ps_accesses(tree, f):
    """Every position access in f. A loop over two sequences at once also accesses them
    at its position: iterating together over s and t reads s and t at a position shared
    by that loop only; iterating with positions (i, x) over s reads s at i."""
    st, out = state(tree), []
    kinds = {"indexing": "index", "slicing_before": "before", "slicing_from": "from", "slicing_between": "between"}
    for n in walk(f.kids[1]):
        if n.kind in kinds:
            seq = resolve(n.kids[0], f, st)
            if seq:
                out.append(Access((f.value, seq) if seq not in st else seq, n, kinds[n.kind], n.kids[1:]))
        elif n.kind == "iterating_together":
            for s in n.kids[2:4]:
                seq = resolve(s, f, st)
                if seq:
                    out.append(Access((f.value, seq) if seq not in st else seq, n, "index", [n]))
        elif n.kind == "iterating_with_positions":
            seq = resolve(n.kids[2], f, st)
            if seq:
                out.append(Access((f.value, seq) if seq not in st else seq, n, "index", [n.kids[0]]))
        elif n.kind == "iterating_over_items":
            # A counter kept by hand is the loop's position too: bound to 0 before the
            # loop, increased by 1 once per item (ASSUMPTIONS.md R1).
            seq = resolve(n.kids[1], f, st)
            for c in counters(f, n):
                if seq:
                    out.append(Access((f.value, seq) if seq not in st else seq, n, "index", [c]))
    return out


def counters(f, loop):
    """Name nodes standing for a counter that follows loop's items: a local bound only to
    0 and increased only by `+= 1`, once, as its own operation in the loop body."""
    from grammar import name as name_node
    out = []
    for s in loop.kids[-1].kids:
        if s.kind == "accumulating" and s.kids[1].kind == "constant" and s.kids[1].value == 1:
            c = s.kids[0].value
            binds = [n for n in walk(f.kids[1]) if n.kind == "binding" and n.kids[0].value == c]
            incs = [n for n in walk(f.kids[1]) if n.kind == "accumulating" and n.kids[0].value == c]
            if len(binds) == 1 and binds[0].kids[1].kind == "constant" and binds[0].kids[1].value == 0 and len(incs) == 1:
                out.append(name_node(c))
    return out


def lockstep(tree):
    """(function, access a, access b) for two different sequences accessed at the same position."""
    out = []
    for f in funcs(tree).values():
        for a, b in combinations(ps_accesses(tree, f), 2):
            if a.seq != b.seq and a.same_position(b):
                out.append((f, a, b))
    return out


def ps_pairs(tree):
    return {frozenset((a.seq, b.seq)) for _, a, b in lockstep(tree)}


def find_lockstep(tree):
    return [{"left_read": a.node, "right_read": b.node, "position": a.pos[0]} for _, a, b in lockstep(tree)]


def paired_reads(tree):
    """(access, partner access or None) for every access of a paired sequence."""
    pairs, out = ps_pairs(tree), []
    for f in funcs(tree).values():
        acc = ps_accesses(tree, f)
        for a in acc:
            for pair in pairs:
                if a.seq in pair:
                    other = next(iter(pair - {a.seq}))
                    out.append((a, next((b for b in acc if b.seq == other and a.same_position(b)), None)))
    return out


def paired_writes(tree):
    """(function, write op, partner write op or None) for writes to a paired sequence."""
    pairs, st, out = ps_pairs(tree), state(tree), []
    for f in funcs(tree).values():
        ws = [(s, resolve_target(s, f, st)) for s in standalone(f) if updated(s)]
        for s, seq in ws:
            for pair in pairs:
                if seq in pair:
                    other = next(iter(pair - {seq}))
                    out.append((f, s, next((t for t, q in ws if q == other), None)))
    return out


def resolve_target(s, f, st):
    """The (resolved) sequence an operation writes, keyed like ps_accesses."""
    if s.kind in ("binding", "accumulating"):
        nm = s.kids[0].value
    elif s.kind in CHANGING_OPS:
        nm = resolve(s.kids[0], f, st)
    else:
        return None
    if nm is None:
        return None
    nm = alias_root(nm, f) if nm not in st else nm
    return nm if nm in st else (f.value, nm)


def loop_position_names(f):
    """Names that are a loop's position: iterating over positions' name, iterating with
    positions' index."""
    return {n.kids[0].value: n for n in walk(f.kids[1])
            if n.kind in ("iterating_over_positions", "iterating_with_positions")}


def find_position_from_loop(tree):
    out = []
    for f, a, b in lockstep(tree):
        pos = a.pos[0]
        if pos.kind in ("iterating_together",):
            out.append({"position_loop": pos, "position_use": a.node})
        elif pos.kind == "name" and pos.value in loop_position_names(f):
            out.append({"position_loop": loop_position_names(f)[pos.value], "position_use": pos})
    return out


def find_position_from_param(tree):
    return [{"position_param": a.pos[0]} for f, a, b in lockstep(tree)
            if a.pos[0].kind == "name" and a.pos[0].value in params(f)]


def find_full_coverage(tree):
    pairs, st, out = ps_pairs(tree), state(tree), []
    paired = set().union(*pairs) if pairs else set()
    for f in funcs(tree).values():
        for n in walk(f.kids[1]):
            for s in loop_sources(n):
                seq = resolve(s, f, st)
                if seq and ((f.value, seq) if seq not in st else seq) in paired:
                    out.append({"covering_loop": n, "covered": s})
    return out


def find_splice(tree):
    """A state sequence rebuilt from a slice before and a slice from a position (with
    something between for an insert). A slice may reach the rebuild through a temporary
    bound once (v6 = v1[:v3]; v1 = v6 + v4 + v7): the cut is then the temporary's value,
    so the temporary's binding carries the role (POC step 5)."""
    st, out = state(tree), []
    for f in funcs(tree).values():
        b = binders(f)

        def cut_of(x):
            if x.kind in ("slicing_before", "slicing_from"):
                return x
            if x.kind == "name" and b.get(x.value) is not None and b[x.value].kind in ("slicing_before", "slicing_from"):
                return b[x.value]
            return None
        for n in walk(f.kids[1]):
            if n.kind == "binding" and n.kids[0].value in st:
                r = n.kids[0].value
                cuts, seen = [], set()
                for x in walk(n.kids[1]):
                    c = cut_of(x)
                    if c is not None and id(c) not in seen and resolve(c.kids[0], f, st) == r:
                        seen.add(id(c))
                        cuts.append(c)
                for sb in (c for c in cuts if c.kind == "slicing_before"):
                    for sf in (c for c in cuts if c.kind == "slicing_from"):
                        m = {"rebuild": n, "before": sb, "after": sf}
                        # What goes between the two slices: present for an insert, not a delete.
                        if n.kids[1].kind == "concatenating":
                            middle = [x for x in n.kids[1].kids if cut_of(x) is not sb and cut_of(x) is not sf]
                            if middle:
                                m["inserted"] = middle[0]
                        out.append(m)
    return out


def find_paired_rebuild(tree):
    st, out = state(tree), []
    for pair in ps_pairs(tree):
        if not all(p in st for p in pair):
            continue
        a, b = sorted(pair)
        for f in funcs(tree).values():
            ra = [s for s in standalone(f) if s.kind == "binding" and s.kids[0].value == a]
            rb = [s for s in standalone(f) if s.kind == "binding" and s.kids[0].value == b]
            out += [{"left_rebuild": x, "right_rebuild": y} for x in ra for y in rb]
    return out


def find_pair_output(tree):
    """Pairing whose two parts come from the two sequences of a pair."""
    pairs, st, out = ps_pairs(tree), state(tree), []
    for f in funcs(tree).values():
        for n in walk(f.kids[1]):
            if n.kind == "pairing":
                srcs = [resolve(x, f, st) for x in n.kids]
                keys = [(f.value, s) if s and s not in st else s for s in srcs]
                if keys[0] != keys[1] and frozenset(keys) in pairs:
                    out.append({"pairing": n, "left_part": n.kids[0], "right_part": n.kids[1]})
    return out


def find_collect(tree):
    """A pairing of the two sequences added to a collection inside a loop; with where the
    collection starts (its binding) and where it goes out (its returning), when present."""
    pair_nodes = {id(m["pairing"]) for m in find_pair_output(tree)}
    out = []
    for f in funcs(tree).values():
        b = binders(f)

        def holds_pair(v):
            """The value, or a temporary bound once that it reads, contains a pairing of the two sequences."""
            for x in walk(v):
                if id(x) in pair_nodes:
                    return True
                if x.kind == "name" and b.get(x.value) is not None and any(id(y) in pair_nodes for y in walk(b[x.value])):
                    return True
            return False
        for loop in (n for n in walk(f.kids[1]) if n.kind in LOOPS):
            for op in walk(loop.kids[-1]):
                if op.kind in ("appending", "inserting", "accumulating") and holds_pair(op.kids[-1]):
                    m = {"collector": op, "collected": op.kids[-1]}
                    target = alias_root(root(op.kids[0]) or "", f)
                    start = [s for s in standalone(f) if s.kind == "binding" and s.kids[0].value == target]
                    out_ = [s for s in standalone(f) if s.kind == "returning" and s.kids
                            and alias_root(root(s.kids[0]) or "", f) == target]
                    if start:
                        m["collection_start"] = start[0]
                    if out_:
                        m["collection_out"] = out_[0]
                    out.append(m)
    return out


ps_lockstep = Facet("ps_lockstep", ["left_read", "right_read", "position"], find_lockstep, core=True)
ps_paired_reads = Facet(
    "ps_paired_reads", ["read", "partner_read"],
    lambda t: [{"read": a.node, "partner_read": b.node} for a, b in paired_reads(t) if b is not None],
    kind="every", core=True, check=lambda t: all(b is not None for _, b in paired_reads(t)))
ps_paired_writes = Facet(
    "ps_paired_writes", ["write", "partner_write"],
    lambda t: [{"write": s, "partner_write": p} for _, s, p in paired_writes(t) if p is not None],
    kind="every", core=True, check=lambda t: all(p is not None for _, _, p in paired_writes(t)))
PS_FACETS = [ps_lockstep, ps_paired_reads, ps_paired_writes,
             Facet("ps_position_from_loop", ["position_loop", "position_use"], find_position_from_loop),
             Facet("ps_position_from_param", ["position_param"], find_position_from_param),
             Facet("ps_full_coverage", ["covering_loop", "covered"], find_full_coverage),
             Facet("ps_splice", ["rebuild", "before", "after", "inserted"], find_splice),
             Facet("ps_paired_rebuild", ["left_rebuild", "right_rebuild"], find_paired_rebuild),
             Facet("ps_pair_output", ["pairing", "left_part", "right_part"], find_pair_output),
             Facet("ps_collect", ["collector", "collected", "collection_start", "collection_out"], find_collect)]


# -- pub/sub ----------------------------------------------------------------------------

def fn_typed(tree):
    """ids of value nodes whose type is a function, from one traversal."""
    return {id(v.node) for v in visit(tree)
            if v.node.kind not in ("block", "func", "module") and (t := _safe_infer(v)) is not None and t.name == "fn"}


def _safe_infer(v):
    try:
        return infer(v.node, v.scope) if v.scope is not None else None
    except Exception:
        return None


def registrations(tree):
    """(function, op, registry, registered value): a function value appended or inserted
    into a collection reached from module state, or stored there wrapped in a new list."""
    st, fns, out = state(tree), fn_typed(tree), []
    for f in funcs(tree).values():
        for n in walk(f.kids[1]):
            reg = resolve(n.kids[0], f, st) if n.kind in ("appending", "inserting", "storing") else None
            if reg not in st:
                continue
            val = n.kids[-1]
            if n.kind == "storing" and val.kind == "wrapping":
                val = val.kids[0]
            if id(val) in fns:
                out.append((f, n, reg, val))
    return out


def notify_loops(tree):
    """(function, loop, registry, call): a loop over items of a collection reached from
    module state that calls its item."""
    st, out = state(tree), []
    for f in funcs(tree).values():
        for x in walk(f.kids[1]):
            if x.kind == "iterating_over_items":
                reg = resolve(x.kids[1], f, st)
                item = x.kids[0].value
                calls = [c for c in walk(x.kids[-1]) if c.kind == "calling" and c.kids[0].kind == "name"
                         and c.kids[0].value == item]
                if reg in st and calls:
                    out.append((f, x, reg, calls[0]))
    return out


def find_register(tree):
    return [{"register_op": n, "registry": n.kids[0], "registered": v} for _, n, _, v in registrations(tree)]


def find_notify(tree):
    return [{"notify_loop": x, "notified_call": c, "registry_read": x.kids[1]} for _, x, _, c in notify_loops(tree)]


def find_linked(tree):
    return [{"register_op": n, "notify_loop": x} for fa, n, ra, _ in registrations(tree)
            for fb, x, rb, _ in notify_loops(tree) if fa is not fb and ra == rb]


def find_unregister(tree):
    st, registries = state(tree), {r for _, _, r, _ in registrations(tree)}
    return [{"unregister_op": n} for f in funcs(tree).values() for n in walk(f.kids[1])
            if n.kind in ("removing", "deleting", "popping") and resolve(n.kids[0], f, st) in registries]


def find_keyed(tree):
    st, out = state(tree), []
    for f in funcs(tree).values():
        ps = set(params(f))
        for n in walk(f.kids[1]):
            if n.kind in ("looking_up", "storing", "deleting") and resolve(n.kids[0], f, st) in st \
                    and n.kids[1].kind == "name" and n.kids[1].value in ps:
                out.append({"keyed_access": n, "key": n.kids[1]})
            elif n.kind == "testing_membership" and resolve(n.kids[1], f, st) in st \
                    and n.kids[0].kind == "name" and n.kids[0].value in ps:
                out.append({"keyed_access": n, "key": n.kids[0]})
            elif n.kind == "comparing" and n.value == "==":
                a, b = n.kids
                for k, p in ((a, b), (b, a)):
                    if k.kind == "name" and p.kind == "name" and p.value in ps and \
                            any(loop.kind in ("iterating_over_keys", "iterating_over_keys_and_values")
                                and loop.kids[0].value == k.value for loop in walk(f.kids[1])):
                        out.append({"keyed_access": n, "key": p})
    return out


def find_on_demand(tree):
    st = state(tree)
    return [{"creation": n} for f in funcs(tree).values() for n in walk(f.kids[1])
            if n.kind == "storing" and resolve(n.kids[0], f, st) in st and n.kids[2].kind in ("creating_empty", "wrapping")]


def find_guarded_notify(tree):
    loops = {id(x) for _, x, _, _ in notify_loops(tree)}
    return [{"guard": b} for f in funcs(tree).values() for b in walk(f.kids[1])
            if b.kind == "branching" and any(id(x) in loops for blk in b.kids[1:] for x in walk(blk))]


def find_message(tree):
    out = []
    for f, x, _, c in notify_loops(tree):
        out += [{"message": a} for a in c.kids[1:] if a.kind == "name" and a.value in params(f)]
    return out


def find_handler_param(tree):
    return [{"handler": v} for f, _, _, v in registrations(tree) if v.kind == "name" and v.value in params(f)]


pub_register = Facet("pub_register", ["register_op", "registry", "registered"], find_register, core=True)
pub_notify = Facet("pub_notify", ["notify_loop", "notified_call", "registry_read"], find_notify, core=True)
pub_notify.needs = {"loop"}
pub_linked = Facet("pub_linked", ["register_op", "notify_loop"], find_linked, core=True)
pub_unregister = Facet("pub_unregister", ["unregister_op"], find_unregister, core=True)
PUB_FACETS = [pub_register, pub_notify, pub_linked, pub_unregister,
              Facet("pub_keyed", ["keyed_access", "key"], find_keyed),
              Facet("pub_on_demand", ["creation"], find_on_demand),
              Facet("pub_guarded_notify", ["guard"], find_guarded_notify),
              Facet("pub_message", ["message"], find_message),
              Facet("pub_handler_param", ["handler"], find_handler_param)]

FACETS = {"parallel_strings": PS_FACETS, "pubsub": PUB_FACETS}


def fingerprint(tree, node, theory):
    """The (facet, role) pairs a concept (the subtree at node) occupies in the theory's
    facet matches on tree."""
    inside = {id(x) for x in walk(node)}
    return frozenset((fc.__name__, role) for fc in FACETS[theory] for m in fc.matches(tree)
                     for role, n in m.items() if id(n) in inside)


# ---- domain must-haves (necessary conditions, for pruning only) ---------------------------

@named("must_loop", "exists")
def must_loop(tree):
    """Some loop exists (no correct color line can do without one in this language)."""
    return exists(any(n.kind in LOOPS for n in walk(tree.kids[1])), tree)


must_loop.needs = {"loop"}  # read by search.feasible() (unsatisfiability pruning)


@named("must_write_all_state", "every")
def must_write_all_state(tree):
    """Every function writes every piece of module state (an editor operation changes
    both the content and the styles)."""
    st = state(tree)
    return per_function(tree, lambda f: st <= {resolve_target(n, f, st) for n in walk(f.kids[1]) if updated(n)})


def writes_state_in(fname):
    @named(f"must_{fname}_writes_state", "exists")
    def rule(tree):
        st, f = state(tree), funcs(tree)[fname]
        return exists(any(resolve_target(n, f, st) in st for n in walk(f.kids[1]) if updated(n)), tree)
    return rule


def calls_in(fname):
    @named(f"must_{fname}_calls", "exists")
    def rule(tree):
        return exists(any(n.kind == "calling" for n in walk(funcs(tree)[fname].kids[1])), tree)
    return rule
