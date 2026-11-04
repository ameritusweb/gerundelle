"""Data flow (PoC step 3, rebuilt): what reaches a program's outputs.

Load-bearing pressure on the rules and the search (POC.md 3g):
- relevant(): a backward slice from each function's outputs (returning, writes to
  module state, calling, breaking), by liveness over the structured tree. An
  operation is load-bearing if it can affect an output; no_dead_code requires every
  operation to be load-bearing.
- inline_temps(): a copy with single-binding temporaries replaced by their values,
  so rules judge what a value is rather than the route it took. judge_complete()
  applies the rules to both on finished programs (inlining a partial program isn't
  monotone, so pruning uses judge() alone).
- signature(): the load-bearing data flow as a set of edges (how a value is bound ->
  how it's used), with names abstracted away. The search's novelty bonus and the
  variety count use it.
"""
from grammar import LOOP_NAMES, STMT_KINDS, Node, walk
from rules import (CHANGING_OPS, alias_root, finished, funcs, loop_names, loop_sources, named, names_in, params,
                   per_function, standalone, state, updated)


def is_op(n):
    return n.kind in STMT_KINDS


# ---- the slice ------------------------------------------------------------------

def uses(s):
    """Names an operation reads (a collection it changes counts as read)."""
    if s.kind == "binding":
        return names_in(s.kids[1])
    if s.kind == "destructuring":
        return names_in(s.kids[2])
    return names_in(s)


def defs(s, f=None):
    """Names an operation writes, and the ones it overwrites completely (kills). Changing
    a collection through an alias (v6 = v3; v6.append(x)) also writes the name it's an
    alias of, so the slice sees the change (ASSUMPTIONS.md D4)."""
    if s.kind == "binding":
        return {s.kids[0].value}, {s.kids[0].value}
    if s.kind == "destructuring":
        written = {s.kids[0].value, s.kids[1].value}
        return written, written
    written = updated(s)
    if f is not None and (s.kind in CHANGING_OPS or s.kind == "accumulating"):
        written = written | {alias_root(nm, f) for nm in written}
    return written, set()


def is_output(s, st):
    return (s.kind in ("returning", "breaking") or bool(defs(s)[0] & st)
            or any(x.kind == "calling" for x in walk(s)))


def relevant(f, st):
    """ids of the operations of function f that can affect its outputs."""
    rel = set()

    def through(block, live):
        for s in reversed(block.kids):
            live = step(s, live)
        return live

    def body_relevant(blocks):
        return any(id(x) in rel for b in blocks for x in walk(b))

    def step(s, live):
        k = s.kind
        if k == "hole":
            return live
        if k == "branching":
            bodies = s.kids[1:]
            outs = [through(b, live) for b in bodies] + ([] if len(bodies) == 2 else [live])
            merged = set().union(*outs)
            if body_relevant(bodies):
                rel.add(id(s))
                return merged | names_in(s.kids[0])
            return merged
        if k == "repeating_while" or k in LOOP_NAMES:
            body = s.kids[-1]
            head = names_in(s.kids[0]) if k == "repeating_while" else set().union(*map(names_in, loop_sources(s)))
            bound = set(loop_names(s))
            loop_live = set(live)
            while True:  # the body may run any number of times
                new = live | (through(body, loop_live) - bound)
                if new == loop_live:
                    break
                loop_live = new
            if body_relevant([body]):
                rel.add(id(s))
                return loop_live | head
            return loop_live
        written, killed = defs(s, f)
        if is_output(s, st) or written & live:
            rel.add(id(s))
            return (live - killed) | uses(s)
        return live

    through(f.kids[1], set())
    return rel


@named("no_dead_code", "every")
def no_dead_code(tree):
    """Every operation that stands alone can affect an output (returning, writing module
    state, calling). A popping used as a value inside another operation isn't checked on
    its own (ASSUMPTIONS.md R7). Decided per finished function."""
    st = state(tree)

    def ok(f):
        rel = relevant(f, st)
        return all(id(s) in rel for s in standalone(f))
    return per_function(tree, ok)


# ---- inlining temporaries ----------------------------------------------------------

def copy(n):
    return Node(n.kind, [copy(c) for c in n.kids], n.value, n.type)


def binds_at(n):
    """Positions of an operation's parts that are names being bound (they stay names)."""
    if n.kind in LOOP_NAMES:
        return set(range(LOOP_NAMES[n.kind]))
    if n.kind in ("binding", "accumulating"):
        return {0}
    if n.kind == "destructuring":
        return {0, 1}
    return set()


def inline_temps(tree):
    """A copy with each local that's bound exactly once, never changed, from a value
    without calling or popping, replaced by that value where it's read (and its
    binding removed)."""
    st = state(tree)
    new_funcs = []
    for f in funcs(tree).values():
        body = f.kids[1]
        writes = {}
        for s in walk(body):
            if is_op(s):  # changes through an alias count as writes to the aliased name too
                for nm in set(defs(s, f)[0]) | set(loop_names(s)):
                    writes[nm] = writes.get(nm, 0) + 1
        temps = {s.kids[0].value: s.kids[1] for s in walk(body)
                 if s.kind == "binding" and writes.get(s.kids[0].value) == 1
                 and s.kids[0].value not in st | set(params(f))
                 and not any(x.kind in ("calling", "popping", "hole") for x in walk(s.kids[1]))
                 and s.kids[0].value not in names_in(s.kids[1])}

        def sub(n, depth=0):
            if n.kind == "name" and n.value in temps and depth < 4:
                return sub(copy(temps[n.value]), depth + 1)
            return Node(n.kind, [sub(c, depth) for c in n.kids], n.value, n.type)

        def rewrite(n):
            if n.kind == "block":
                return Node("block", [rewrite(k) for k in n.kids
                                      if not (k.kind == "binding" and k.kids[0].value in temps)])
            if is_op(n):
                bound = binds_at(n)
                kids = [rewrite(c) if c.kind == "block" else c if i in bound else sub(c)
                        for i, c in enumerate(n.kids)]
                return Node(n.kind, kids, n.value, n.type)
            return Node(n.kind, [rewrite(c) for c in n.kids], n.value, n.type)
        new_funcs.append(Node("func", [f.kids[0], rewrite(body)], f.value, f.type))
    return Node("module", [tree.kids[0], Node("funcs", new_funcs)])


def judge(rules, tree):
    return {r.__name__: r(tree) for r in rules}


def judge_complete(rules, tree):
    """judge(), and on a finished program also the rules on its inlined copy, combined by
    each rule's kind (ASSUMPTIONS.md R3): an exists-rule passes if either copy passes (the
    inlined copy can reveal a legitimate pattern hidden behind a temporary); a never- or
    every-rule fails if either copy fails (it can reveal junk hidden behind one)."""
    res = judge(rules, tree)
    if not finished(tree):
        return res
    inlined = judge(rules, inline_temps(tree))
    kinds = {r.__name__: getattr(r, "kind", "never") for r in rules}
    out = {}
    for k, v in res.items():
        if kinds[k] == "exists":
            out[k] = True if (v is True or inlined[k] is True) else v
        else:
            out[k] = False if inlined[k] is False else v
    return out


# ---- the load-bearing data-flow signature -------------------------------------------

def def_label(s, nm):
    """How an operation binds a name."""
    if s.kind in LOOP_NAMES:
        names = loop_names(s)
        return f"{s.kind}.{names.index(nm)}" if len(names) > 1 else s.kind
    if s.kind == "binding":
        return f"binding:{s.kids[1].kind}"
    return s.kind


def signature(tree):
    """The load-bearing data flow: (definition label, use label) for every read of a name
    in an operation that can affect an output, with names abstracted away."""
    st, edges = state(tree), set()
    for f in funcs(tree).values():
        rel = relevant(f, st)
        defined = {p: {"param"} for p in params(f)}
        defined.update({s: {"state"} for s in st})
        ops = [s for s in walk(f.kids[1]) if is_op(s) and id(s) in rel]
        for s in ops:
            for nm in set(loop_names(s)) | (defs(s)[0] if s.kind not in LOOP_NAMES else set()):
                defined.setdefault(nm, set()).add(def_label(s, nm))
        for s in ops:
            if s.kind in LOOP_NAMES:
                parts = loop_sources(s)
            elif s.kind in ("branching", "repeating_while"):
                parts = s.kids[:1]
            else:
                parts = [s]
            for part in parts:
                stack = [(part, s.kind)]
                if part.kind == "name":
                    edges |= {(d, f"{s.kind}/source") for d in defined.get(part.value, {"?"})}
                while stack:
                    n, _ = stack.pop()
                    for i, c in enumerate(n.kids):
                        if c.kind == "name":
                            edges |= {(d, f"{s.kind}/{n.kind}.{i}") for d in defined.get(c.value, {"?"})}
                        elif c.kind != "block":
                            stack.append((c, n.kind))
            if s.kind == "returning" and s.kids:
                edges.add(("out", f"returning:{s.kids[0].kind}"))
        # Order: which load-bearing operation follows which in a block. Without it, a wrong
        # order (appending before the list exists) had a correct program's signature
        # (ASSUMPTIONS.md T8).
        for b in (n for n in walk(f.kids[1]) if n.kind == "block"):
            kept = [s for s in b.kids if id(s) in rel]
            edges |= {("then", a.kind, c.kind) for a, c in zip(kept, kept[1:])}
    return frozenset(edges)


def distance(a, b):
    """Jaccard distance between two signatures."""
    return 1 - len(a & b) / len(a | b) if a | b else 0.0
