"""The operation language (PoC step 1, rebuilt): typed trees of operations, for search.

Every node is an operation named as a gerund, a verb for what it does (VOCABULARY.md):
indexing, appending, iterating over positions. Names, constants and function
references are leaf inputs. Operations nest by design, so a result feeds the
operation that uses it; an idiom such as s[:i] + t + s[i:] is a subtree
(concatenating over slicing before, t, slicing from), not a special node. Loop
headers are the one fold: range(len(s)) is plumbing inside iterating over positions.

The syntax-level grammar of poc/ (separate var, len, range, const nodes) was a drift
from this design (POC.md section 14b).

An unfinished part of a tree is a hole: "expr" (carrying the type it must produce),
"stmt", or "stmts" (the open end of a block: one more operation, or done).

visit() is the one traversal: every node with its path, the scope at that point and
what its parent expects, so holes(), check() and expansions() agree on scoping.
Scoping is stricter than Python's: a name bound inside a body is visible only there.
Function signatures and module state are given (a domain's skeleton).
"""
import re
from dataclasses import dataclass, field
from itertools import product


# ---- types -----------------------------------------------------------------

@dataclass(frozen=True)
class T:
    name: str
    args: tuple = ()

    def __repr__(self):
        return type_str(self)


INT, STR, BOOL, NONE = T("int"), T("str"), T("bool"), T("none")


def LIST(e):
    return T("list", (e,))


def DICT(k, v):
    return T("dict", (k, v))


def PAIR(a, b):
    return T("tuple", (a, b))


def FN(params, ret):
    """A function type. args is (ret, *params)."""
    return T("fn", (ret, *params))


def type_str(t):
    if t is None:
        return "?"
    if t == NONE:
        return "None"
    if t.name == "fn":
        ret, *params = t.args
        return f"Callable[[{', '.join(map(type_str, params))}], {type_str(ret)}]"
    if t.args:
        return f"{t.name}[{', '.join(map(type_str, t.args))}]"
    return t.name


def elem(t):
    """What iterating over t yields (a dict yields its keys)."""
    if t == STR:
        return STR
    if t is not None and t.name in ("list", "dict"):
        return t.args[0]
    return None


def is_seq(t):
    return t == STR or t.name == "list"


GROUPS = {
    "any": lambda t: True,
    "seq": is_seq,
    "list": lambda t: t.name == "list",
    "dict": lambda t: t.name == "dict",
    "sized": lambda t: is_seq(t) or t.name == "dict",
    "joinable": lambda t: is_seq(t),                    # concatenating
    "storable": lambda t: t.name in ("list", "dict"),   # storing
    "eq": lambda t: t.name not in ("fn", "none"),
    "fn": lambda t: t.name == "fn",
    "pair": lambda t: t.name == "tuple" and len(t.args) == 2,
}


def fits(t, expect):
    if t is None or expect is None:
        return False
    if isinstance(expect, T):
        return t == expect
    return GROUPS[expect](t)


# ---- nodes -----------------------------------------------------------------

@dataclass
class Node:
    kind: str
    kids: list = field(default_factory=list)
    value: object = None  # a name, a constant, an operator, or a hole's category
    type: T = None        # holes, creating_empty and functions carry their type


LEAVES = {"name", "constant", "function"}
READING = {"indexing", "slicing_before", "slicing_from", "slicing_between", "measuring", "looking_up"}
BUILDING = {"creating_empty", "pairing", "wrapping", "concatenating", "adding", "subtracting"}
TESTING = {"comparing", "testing_membership", "testing_emptiness", "combining", "negating"}
VALUE_OPS = READING | BUILDING | TESTING | {"calling", "popping"}
EXPR_KINDS = LEAVES | VALUE_OPS

ITERATING = {"iterating_over_items", "iterating_over_positions", "iterating_with_positions",
             "iterating_together", "iterating_over_keys", "iterating_over_keys_and_values"}
LOOPS = ITERATING | {"repeating_while"}
CHANGING = {"appending", "inserting", "removing", "popping", "storing", "deleting"}
NAMING = {"binding", "destructuring", "accumulating"}
CONTROLLING = {"branching", "returning", "breaking"}
STMT_KINDS = LOOPS | CHANGING | NAMING | CONTROLLING | {"calling"}  # calling and popping work either way
OPERATIONS = VALUE_OPS | STMT_KINDS

# How many names a loop binds before its other parts.
LOOP_NAMES = {"iterating_over_items": 1, "iterating_over_positions": 1, "iterating_with_positions": 2,
              "iterating_together": 2, "iterating_over_keys": 1, "iterating_over_keys_and_values": 2,
              "repeating_while": 0}
ARITY = {"indexing": 2, "slicing_before": 2, "slicing_from": 2, "slicing_between": 3, "measuring": 1,
         "looking_up": 2, "creating_empty": 0, "pairing": 2, "wrapping": 1, "adding": 2, "subtracting": 2,
         "comparing": 2, "testing_membership": 2, "testing_emptiness": 1, "combining": 2, "negating": 1,
         "iterating_over_items": 3, "iterating_over_positions": 3, "iterating_with_positions": 4,
         "iterating_together": 5, "iterating_over_keys": 3, "iterating_over_keys_and_values": 4,
         "repeating_while": 2, "appending": 2, "inserting": 3, "removing": 2, "storing": 3, "deleting": 2,
         "binding": 2, "destructuring": 3, "accumulating": 2, "breaking": 0}
COMPARES = {"==", "!=", "<", "<=", ">", ">="}


# Leaf inputs.
def name(n): return Node("name", value=n)
def constant(v): return Node("constant", value=v)
def function(f): return Node("function", value=f)
def hole(category, t=None): return Node("hole", value=category, type=t)


# Reading.
def indexing(s, i): return Node("indexing", [s, i])
def slicing_before(s, i): return Node("slicing_before", [s, i])
def slicing_from(s, i): return Node("slicing_from", [s, i])
def slicing_between(s, i, j): return Node("slicing_between", [s, i, j])
def measuring(s): return Node("measuring", [s])
def looking_up(d, k): return Node("looking_up", [d, k])


# Building.
def creating_empty(t): return Node("creating_empty", type=t)
def pairing(a, b): return Node("pairing", [a, b])
def wrapping(x): return Node("wrapping", [x])
def concatenating(*parts): return Node("concatenating", list(parts))
def adding(a, b): return Node("adding", [a, b])
def subtracting(a, b): return Node("subtracting", [a, b])


# Testing.
def comparing(op, a, b): return Node("comparing", [a, b], op)
def testing_membership(x, c): return Node("testing_membership", [x, c])
def testing_emptiness(s): return Node("testing_emptiness", [s])
def combining(op, a, b): return Node("combining", [a, b], op)
def negating(c): return Node("negating", [c])


# Calling, and changing a collection.
def calling(f, *args): return Node("calling", [f, *args])
def popping(lst, i=None): return Node("popping", [lst] if i is None else [lst, i])
def appending(lst, x): return Node("appending", [lst, x])
def inserting(lst, i, x): return Node("inserting", [lst, i, x])
def removing(lst, x): return Node("removing", [lst, x])
def storing(c, k, v): return Node("storing", [c, k, v])
def deleting(d, k): return Node("deleting", [d, k])


# Naming.
def binding(target, v): return Node("binding", [target, v])
def destructuring(a, b, v): return Node("destructuring", [a, b, v])
def accumulating(target, v): return Node("accumulating", [target, v])


# Iterating (names first, then sources, then the body).
def iterating_over_items(x, s, body): return Node("iterating_over_items", [x, s, body])
def iterating_over_positions(i, s, body): return Node("iterating_over_positions", [i, s, body])
def iterating_with_positions(i, x, s, body): return Node("iterating_with_positions", [i, x, s, body])
def iterating_together(a, b, s, t, body): return Node("iterating_together", [a, b, s, t, body])
def iterating_over_keys(k, d, body): return Node("iterating_over_keys", [k, d, body])
def iterating_over_keys_and_values(k, v, d, body): return Node("iterating_over_keys_and_values", [k, v, d, body])
def repeating_while(c, body): return Node("repeating_while", [c, body])


# Controlling.
def branching(c, then, otherwise=None): return Node("branching", [c, then] + ([otherwise] if otherwise else []))
def returning(v=None): return Node("returning", [] if v is None else [v])
def breaking(): return Node("breaking")


# Structure.
def block(*ops): return Node("block", list(ops))


def func(fname, params, t, body):
    return Node("func", [Node("params", [name(p) for p in params]), body], fname, t)


def module(state, funcs):
    return Node("module", [Node("state", list(state)), Node("funcs", list(funcs))])


# ---- types of values -----------------------------------------------------------

@dataclass
class Scope:
    vars: dict
    funcs: dict
    ret: T = None
    in_loop: bool = False

    def add(self, new):
        return Scope({**self.vars, **new}, self.funcs, self.ret, self.in_loop) if new else self

    def looping(self):
        return Scope(self.vars, self.funcs, self.ret, True)


def infer(n, sc):
    """The type of value n in scope sc, or None if it has none."""
    k, c = n.kind, n.kids
    if k == "hole":
        return n.type
    if k == "name":
        return sc.vars.get(n.value)
    if k == "constant":
        return {bool: BOOL, int: INT, str: STR, type(None): NONE}[type(n.value)]
    if k == "function":
        return sc.funcs.get(n.value)
    if k == "creating_empty":
        return n.type
    if k in TESTING:
        return BOOL
    if k == "measuring":
        return INT
    ts = [infer(x, sc) for x in c]
    if None in ts:
        return None
    if k in ("slicing_before", "slicing_from", "slicing_between", "concatenating", "adding", "subtracting"):
        return ts[0]
    if k == "indexing":
        return STR if ts[0] == STR else ts[0].args[0] if ts[0].name == "list" else None
    if k == "looking_up":
        return ts[0].args[1] if ts[0].name == "dict" else None
    if k == "pairing":
        return PAIR(ts[0], ts[1])
    if k == "wrapping":
        return LIST(ts[0])
    if k == "popping":
        return ts[0].args[0] if ts[0].name == "list" else None
    if k == "calling":
        return ts[0].args[0] if ts[0].name == "fn" else None
    return None


def loop_binds(n, sc):
    """Names a loop binds for its body, with their types."""
    k, c = n.kind, n.kids
    src = [infer(x, sc) for x in c[LOOP_NAMES[k]:-1]]
    if None in src:
        return {x.value: None for x in c[:LOOP_NAMES[k]]}
    if k == "iterating_over_items":
        types = [elem(src[0])]
    elif k == "iterating_over_positions":
        types = [INT]
    elif k == "iterating_with_positions":
        types = [INT, elem(src[0])]
    elif k == "iterating_together":
        types = [elem(src[0]), elem(src[1])]
    elif k == "iterating_over_keys":
        types = [src[0].args[0] if src[0].name == "dict" else None]
    elif k == "iterating_over_keys_and_values":
        types = list(src[0].args) if src[0].name == "dict" else [None, None]
    else:
        types = []
    return {x.value: t for x, t in zip(c[:LOOP_NAMES[k]], types)}


def declares(target, sc):
    return target.kind == "name" and target.value not in sc.vars


def block_binds(b, sc):
    """Names a block definitely binds by its end, with their types."""
    out, inner = {}, sc
    for s in b.kids:
        new = declared(s, inner)
        out.update(new)
        inner = inner.add(new)
    return out


def declared(s, sc):
    """Names an operation definitely adds to the rest of its block (definite assignment).

    A branching with both arms binds the names both arms bind, at the same type; a
    branching without an else, or a loop (which may run zero times), binds nothing for
    the code after it."""
    if s.kind == "binding" and declares(s.kids[0], sc):
        return {s.kids[0].value: infer(s.kids[1], sc)}
    if s.kind == "destructuring":
        t = infer(s.kids[2], sc)
        parts = t.args if t is not None and t.name == "tuple" else (None, None)
        return {x.value: p for x, p in zip(s.kids[:2], parts) if x.value not in sc.vars}
    if s.kind == "branching" and len(s.kids) == 3:
        a, b = block_binds(s.kids[1], sc), block_binds(s.kids[2], sc)
        return {n: t for n, t in a.items() if n in b and b[n] == t and t is not None}
    return {}


# ---- the traversal -----------------------------------------------------------

@dataclass
class Visit:
    path: tuple
    node: Node
    scope: Scope
    expect: object  # a T, a GROUPS name, or a position: "stmt", "stmts", "new", "target", "block", ...


def expect_kid(n, i, sc):
    """What operation n expects of its i-th part."""
    k, c = n.kind, n.kids
    t0 = infer(c[0], sc) if i > 0 else None
    if k == "binding":
        new = declares(c[0], sc)
        if i == 0:
            return "new" if new else "target"
        return "any" if new else infer(c[0], sc)
    if k == "accumulating":
        return "target" if i == 0 else t0
    if k == "destructuring":
        if i < 2:  # a new name, or an existing one (a swap: a, b = b, a); types are checked in check()
            return "new" if declares(c[i], sc) else "target"
        return "pair"
    if k == "returning":
        return sc.ret
    if k == "branching":
        return BOOL if i == 0 else "block"
    if k == "repeating_while":
        return BOOL if i == 0 else "block"
    if k in LOOP_NAMES:
        names = LOOP_NAMES[k]
        if i < names:
            return "new"
        if i == len(c) - 1:
            return "block"
        if k in ("iterating_over_keys", "iterating_over_keys_and_values"):
            return "dict"
        if k == "iterating_over_items":
            return "seq"
        return "seq"
    if k in ("appending", "inserting", "removing"):
        if i == 0:
            return "list"
        return INT if k == "inserting" and i == 1 else elem(t0)
    if k == "popping":
        return "list" if i == 0 else INT
    if k == "storing":
        if i == 0:
            return "storable"
        if t0 is None:
            return None
        if t0.name == "list":
            return INT if i == 1 else t0.args[0]
        return t0.args[i - 1]
    if k == "deleting":
        return "dict" if i == 0 else elem(t0)
    if k == "indexing":
        return "seq" if i == 0 else INT
    if k in ("slicing_before", "slicing_from", "slicing_between"):
        return "seq" if i == 0 else INT
    if k == "measuring":
        return "sized"
    if k == "looking_up":
        return "dict" if i == 0 else elem(t0)
    if k == "pairing":
        return "any"
    if k == "wrapping":
        return "any"
    if k == "concatenating":
        return "joinable" if i == 0 else t0
    if k in ("adding", "subtracting"):
        return INT
    if k == "comparing":
        if n.value in ("==", "!="):
            return "eq" if i == 0 else t0
        return INT
    if k == "testing_membership":
        return elem(infer(c[1], sc)) if i == 0 else "sized"
    if k == "testing_emptiness":
        return "sized"
    if k in ("combining", "negating"):
        return BOOL
    if k == "calling":
        if i == 0:
            return "fn"
        return t0.args[i] if t0 is not None and t0.name == "fn" and i < len(t0.args) else None
    return None


def visit(n, path=(), scope=None, expect="module"):
    """Every node of the tree under n, in order, with its path, scope and expectation."""
    yield Visit(path, n, scope, expect)
    k = n.kind
    if k == "module":
        state, funcs = n.kids
        sc = Scope({}, {f.value: f.type for f in funcs.kids})
        yield Visit(path + (0,), state, sc, "state")
        for i, s in enumerate(state.kids):
            yield from visit(s, path + (0, i), sc, "stmt")
            sc = sc.add(declared(s, sc))
        yield Visit(path + (1,), funcs, sc, "funcs")
        for i, f in enumerate(funcs.kids):
            yield from visit(f, path + (1, i), sc, "func")
    elif k == "func":
        params, body = n.kids
        ret, *ptypes = n.type.args
        sc = Scope({**scope.vars, **{p.value: t for p, t in zip(params.kids, ptypes)}}, scope.funcs, ret)
        yield Visit(path + (0,), params, sc, "params")
        for i, p in enumerate(params.kids):
            yield Visit(path + (0, i), p, sc, "new")
        yield from visit(body, path + (1,), sc, "block")
    elif k == "block":
        sc = scope
        for i, s in enumerate(n.kids):
            at_end = s.kind == "hole" and s.value == "stmts"
            yield from visit(s, path + (i,), sc, "stmts" if at_end else "stmt")
            sc = sc.add(declared(s, sc))
    elif k in LOOP_NAMES:
        names = LOOP_NAMES[k]
        for i, c in enumerate(n.kids[:-1]):
            yield from visit(c, path + (i,), scope, expect_kid(n, i, scope))
        body_sc = scope.add(loop_binds(n, scope)).looping() if names else scope.looping()
        yield from visit(n.kids[-1], path + (len(n.kids) - 1,), body_sc, "block")
    elif k == "branching":
        yield from visit(n.kids[0], path + (0,), scope, BOOL)
        for i, b in enumerate(n.kids[1:], 1):
            yield from visit(b, path + (i,), scope, "block")
    elif k != "hole":
        for i, c in enumerate(n.kids):
            yield from visit(c, path + (i,), scope, expect_kid(n, i, scope))


def walk(n):
    """Every node under n, without scopes."""
    yield n
    for c in n.kids:
        yield from walk(c)


def holes(tree):
    return [v for v in visit(tree) if v.node.kind == "hole"]


def find(tree, path):
    return next(v for v in visit(tree) if v.path == path)


def replace(tree, path, new):
    """A copy of tree with the node at path replaced. A list is spliced into the parent."""
    if not path:
        return new
    i, rest = path[0], path[1:]
    kids = list(tree.kids)
    if rest:
        kids[i] = replace(kids[i], rest, new)
    elif isinstance(new, list):
        kids[i:i + 1] = new
    else:
        kids[i] = new
    return Node(tree.kind, kids, tree.value, tree.type)


# ---- checking ----------------------------------------------------------------

def check(tree, holes_ok=False):
    """Problems with a tree, as (path, message). Empty means well-formed and well-typed."""
    errors = []
    for v in visit(tree):
        n, e, sc = v.node, v.expect, v.scope
        k = n.kind

        def err(msg):
            errors.append((v.path, f"{k}: {msg}"))

        if k in ARITY and len(n.kids) != ARITY[k]:
            err(f"{len(n.kids)} parts, needs {ARITY[k]}")
            continue
        if k == "hole":
            if not holes_ok:
                err("unfilled hole")
            ok = n.value == e if e in ("stmt", "stmts") else n.value == "expr" and fits(n.type, e)
            if not ok:
                err(f"{n.value} hole of type {type_str(n.type)} where {e} expected")
        elif e in ("stmt", "stmts"):
            if k not in STMT_KINDS and k != "popping":
                err("not an operation that can stand alone")
            elif k == "returning" and (sc.ret == NONE) != (not n.kids):
                err("return value doesn't match the signature")
            elif k == "breaking" and not sc.in_loop:
                err("breaking outside a loop")
            elif k == "accumulating" and not fits(infer(n.kids[0], sc), "joinable") and infer(n.kids[0], sc) != INT:
                err(f"accumulating into {type_str(infer(n.kids[0], sc))}")
            elif k == "branching" and len(n.kids) not in (2, 3):
                err("bad shape")
            elif k == "destructuring":
                t = infer(n.kids[2], sc)
                if t is not None and t.name == "tuple":
                    for x, part in zip(n.kids[:2], t.args):
                        if x.value in sc.vars and sc.vars[x.value] != part:
                            err(f"{x.value} is {type_str(sc.vars[x.value])}, the pair gives {type_str(part)}")
            elif k == "calling" and len(n.kids) - 1 != len((infer(n.kids[0], sc) or T("fn", (None,))).args) - 1:
                err("wrong number of arguments")
        elif e == "new":
            if k != "name":
                err("only a name can be bound")
        elif e == "target":
            if k != "name" or infer(n, sc) is None:
                err("not a bound name")
        elif e == "block":
            if k != "block":
                err("not a block")
        elif e in ("module", "state", "funcs", "func", "params"):
            pass
        elif k not in EXPR_KINDS:
            err(f"not a value (where {e} expected)")
        else:
            t = infer(n, sc)
            if t is None:
                err("has no type (unbound name or wrong input)")
            elif not fits(t, e):
                err(f"{type_str(t)} where {type_str(e) if isinstance(e, T) else e} expected")
            elif k == "calling" and len(n.kids) - 1 != len(infer(n.kids[0], sc).args) - 1:
                err("wrong number of arguments")
            elif k == "comparing" and n.value not in COMPARES or k == "combining" and n.value not in ("and", "or"):
                err(f"unknown operator {n.value}")
            elif k == "concatenating" and len(n.kids) < 2:
                err("concatenating needs at least two parts")
            elif k == "popping" and len(n.kids) not in (1, 2):
                err("bad shape")
    return errors


# ---- expansions: what may fill a hole ------------------------------------------

CONSTANTS = {INT: (0, 1, 2, 3), STR: ("",), BOOL: (True, False)}  # plus the skeleton's characters (constants())

# Local collection types offered even when no signature mentions them (a set of seen
# characters, a counter per key, a list of positions). Kept few: each adds options to
# every hole of its kind.
LOCAL_TYPES = [LIST(INT), LIST(STR), DICT(STR, INT), DICT(STR, BOOL)]


def constants(tree):
    """The constants a value hole may take: a tiny fixed universe (small integers, '',
    True, False) plus the single characters of the skeleton's string constants. Constants
    a domain gives meaning to belong in its skeleton as named state, not here."""
    chars = {ch for n in walk(tree.kids[0]) if n.kind == "constant" and isinstance(n.value, str) for ch in n.value}
    return {INT: CONSTANTS[INT], BOOL: CONSTANTS[BOOL], STR: CONSTANTS[STR] + tuple(sorted(chars))}


def universe(tree):
    """Types a hole may take: those in the signatures and state, their parts, a few local
    collection types (LOCAL_TYPES), and the basics."""
    state, funcs = tree.kids
    stack, seen, sc = [INT, STR, BOOL] + LOCAL_TYPES, set(), Scope({}, {})
    for s in state.kids:
        new = declared(s, sc)
        stack += list(new.values())
        sc = sc.add(new)
    for f in funcs.kids:
        stack += list(f.type.args)
    while stack:
        t = stack.pop()
        if t is not None and t not in seen:
            seen.add(t)
            stack += list(t.args)
    return seen


def fresh_names(tree, k):
    used = [int(m.group(1)) for n in walk(tree) if n.kind == "name" and (m := re.fullmatch(r"v(\d+)", n.value))]
    top = max(used, default=0)
    return [f"v{top + i + 1}" for i in range(k)]


def H(t):
    return hole("expr", t)


def open_block():
    return block(hole("stmts"))


def expansions(tree, path):
    """Everything that may fill the hole at path: one operation (or leaf), with typed
    holes for its inputs. For a "stmts" hole, each option is a list spliced into the block."""
    v = find(tree, path)
    h, sc = v.node, v.scope
    if h.value == "stmts":
        return [[], [hole("stmt"), hole("stmts")]]
    types = sorted((t for t in universe(tree) if t != NONE), key=type_str)
    if h.value == "stmt":
        return stmt_options(sc, types, fresh_names(tree, 2))
    return value_options(h.type, sc, types, constants(tree))


def call_options(sc, types, ret):
    """Calls returning ret: through a function-typed hole, or to a named function."""
    out = [calling(H(ft), *map(H, ft.args[1:])) for ft in types if ft.name == "fn" and ft.args[0] == ret]
    out += [calling(function(f), *map(H, ft.args[1:])) for f, ft in sorted(sc.funcs.items()) if ft.args[0] == ret]
    return out


def value_options(t, sc, types, consts=CONSTANTS):
    dicts = [u for u in types if u.name == "dict"]
    out = [name(n) for n, vt in sorted(sc.vars.items()) if vt == t]
    out += [constant(c) for c in consts.get(t, ())]
    out += [function(f) for f, ft in sorted(sc.funcs.items()) if ft == t]
    # Reading.
    if LIST(t) in types:
        out += [indexing(H(LIST(t)), H(INT)), popping(H(LIST(t))), popping(H(LIST(t)), H(INT))]
    if t == STR:
        out.append(indexing(H(STR), H(INT)))
    out += [looking_up(H(d), H(d.args[0])) for d in dicts if d.args[1] == t]
    if is_seq(t):
        out += [slicing_before(H(t), H(INT)), slicing_from(H(t), H(INT)), slicing_between(H(t), H(INT), H(INT))]
    if t == INT:
        out += [measuring(H(u)) for u in types if GROUPS["sized"](u)]
        out += [adding(H(INT), H(INT)), subtracting(H(INT), H(INT))]
    # Building.
    if is_seq(t):
        out += [concatenating(H(t), H(t)), concatenating(H(t), H(t), H(t))]
    if t.name in ("list", "dict") or t == STR:
        out.append(creating_empty(t))
    if t.name == "list":
        out.append(wrapping(H(t.args[0])))
    if t.name == "tuple" and len(t.args) == 2:
        out.append(pairing(H(t.args[0]), H(t.args[1])))
    # Testing.
    if t == BOOL:
        out += [comparing(op, H(u), H(u)) for u in types if GROUPS["eq"](u) for op in ("==", "!=")]
        out += [comparing(op, H(INT), H(INT)) for op in ("<", "<=", ">", ">=")]
        out += [testing_membership(H(elem(u)), H(u)) for u in types if GROUPS["sized"](u)]
        out += [testing_emptiness(H(u)) for u in types if GROUPS["sized"](u)]
        out += [combining("and", H(BOOL), H(BOOL)), combining("or", H(BOOL), H(BOOL)), negating(H(BOOL))]
    out += call_options(sc, types, t)
    return out


def stmt_options(sc, types, fresh):
    a, b = fresh
    lists = [u for u in types if u.name == "list"]
    dicts = [u for u in types if u.name == "dict"]
    seqs = [STR] + lists
    out = [binding(name(a), H(t)) for t in types]
    for n, vt in sorted(sc.vars.items()):
        if vt is None:
            continue
        out.append(binding(name(n), H(vt)))
        if fits(vt, "joinable") or vt == INT:
            out.append(accumulating(name(n), H(vt)))
    out += [destructuring(name(a), name(b), H(t)) for t in types if t.name == "tuple" and len(t.args) == 2]
    # Destructuring into existing names, e.g. a swap: v1, v2 = v2, v1.
    known = sorted((n, vt) for n, vt in sc.vars.items() if vt is not None)
    out += [destructuring(name(x), name(y), H(PAIR(tx, ty))) for (x, tx), (y, ty) in product(known, known)
            if x != y and tx.name != "fn" and ty.name != "fn"]
    for lt in lists:
        e = lt.args[0]
        out += [appending(H(lt), H(e)), inserting(H(lt), H(INT), H(e)), removing(H(lt), H(e)),
                popping(H(lt)), storing(H(lt), H(INT), H(e))]
    for d in dicts:
        out += [storing(H(d), H(d.args[0]), H(d.args[1])), deleting(H(d), H(d.args[0]))]
    out += [c for ret in sorted({ft.args[0] for ft in [*types, *sc.funcs.values()] if ft.name == "fn"}, key=type_str)
            for c in call_options(sc, types, ret)]
    out.append(returning() if sc.ret == NONE else returning(H(sc.ret)))
    if sc.in_loop:
        out.append(breaking())
    out += [branching(H(BOOL), open_block()), branching(H(BOOL), open_block(), open_block()),
            repeating_while(H(BOOL), open_block())]
    out += [iterating_over_items(name(a), H(s), open_block()) for s in seqs]
    out += [iterating_over_positions(name(a), H(s), open_block()) for s in seqs]
    out += [iterating_with_positions(name(a), name(b), H(s), open_block()) for s in seqs]
    out += [iterating_together(name(a), name(b), H(s), H(t), open_block()) for s, t in product(seqs, seqs)]
    out += [iterating_over_keys(name(a), H(d), open_block()) for d in dicts]
    out += [iterating_over_keys_and_values(name(a), name(b), H(d), open_block()) for d in dicts]
    return out
