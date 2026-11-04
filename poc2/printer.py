"""Print an operation tree as Python (PoC step 1, rebuilt).

Each operation prints as the Python it stands for (VOCABULARY.md). Holes print as
⟨int⟩, ⟨stmt⟩ and ⟨...⟩, so partial programs are readable too. A function that
rebinds module state gets a `global` line, as Python requires.
"""
from grammar import LOOP_NAMES, Scope, declared, infer, type_str, walk

# Python precedence of what an operation prints as (higher binds tighter).
PREC = {"combining:or": 1, "combining:and": 2, "negating": 3, "comparing": 4, "testing_membership": 4,
        "testing_emptiness": 4, "concatenating": 5, "adding": 5, "subtracting": 5}
ATOM = 9


def prec(n):
    if n.kind == "combining":
        return PREC[f"combining:{n.value}"]
    return PREC.get(n.kind, ATOM)


def wrap(n, least):
    s = value(n)
    return f"({s})" if prec(n) < least else s


def value(n):
    k, c = n.kind, n.kids
    if k == "hole":
        return f"⟨{type_str(n.type)}⟩"
    if k in ("name", "function"):
        return n.value
    if k == "constant":
        return repr(n.value)
    if k == "indexing":
        return f"{wrap(c[0], ATOM)}[{value(c[1])}]"
    if k == "slicing_before":
        return f"{wrap(c[0], ATOM)}[:{value(c[1])}]"
    if k == "slicing_from":
        return f"{wrap(c[0], ATOM)}[{value(c[1])}:]"
    if k == "slicing_between":
        return f"{wrap(c[0], ATOM)}[{value(c[1])}:{value(c[2])}]"
    if k == "measuring":
        return f"len({value(c[0])})"
    if k == "looking_up":
        return f"{wrap(c[0], ATOM)}[{value(c[1])}]"
    if k == "creating_empty":
        return {"list": "[]", "dict": "{}", "str": "''"}[n.type.name]
    if k == "pairing":
        return f"({value(c[0])}, {value(c[1])})"
    if k == "wrapping":
        return f"[{value(c[0])}]"
    if k == "concatenating":
        return " + ".join([wrap(c[0], 5)] + [wrap(x, 6) for x in c[1:]])
    if k in ("adding", "subtracting"):
        return f"{wrap(c[0], 5)} {'+' if k == 'adding' else '-'} {wrap(c[1], 6)}"
    if k == "comparing":
        return f"{wrap(c[0], 5)} {n.value} {wrap(c[1], 5)}"
    if k == "testing_membership":
        return f"{wrap(c[0], 5)} in {wrap(c[1], 5)}"
    if k == "testing_emptiness":
        return f"len({value(c[0])}) == 0"
    if k == "combining":
        p = prec(n)
        return f"{wrap(c[0], p)} {n.value} {wrap(c[1], p + 1)}"
    if k == "negating":
        if c[0].kind == "testing_membership":
            x, y = c[0].kids
            return f"{wrap(x, 5)} not in {wrap(y, 5)}"
        return f"not {wrap(c[0], 3)}"
    if k == "calling":
        return f"{wrap(c[0], ATOM)}({', '.join(map(value, c[1:]))})"
    if k == "popping":
        return f"{wrap(c[0], ATOM)}.pop({value(c[1]) if len(c) > 1 else ''})"
    raise ValueError(f"not a value: {k}")


METHODS = {"appending": "append", "inserting": "insert", "removing": "remove"}

LOOP_HEADERS = {
    "iterating_over_items": lambda c: f"for {c[0].value} in {value(c[1])}:",
    "iterating_over_positions": lambda c: f"for {c[0].value} in range(len({value(c[1])})):",
    "iterating_with_positions": lambda c: f"for {c[0].value}, {c[1].value} in enumerate({value(c[2])}):",
    "iterating_together": lambda c: f"for {c[0].value}, {c[1].value} in zip({value(c[2])}, {value(c[3])}):",
    "iterating_over_keys": lambda c: f"for {c[0].value} in {value(c[1])}:",
    "iterating_over_keys_and_values": lambda c: f"for {c[0].value}, {c[1].value} in {wrap(c[2], ATOM)}.items():",
    "repeating_while": lambda c: f"while {value(c[0])}:",
}


def op(s, depth, out):
    pad = "    " * depth
    k, c = s.kind, s.kids
    if k == "hole":
        out.append(pad + ("⟨stmt⟩" if s.value == "stmt" else "⟨...⟩"))
    elif k == "binding":
        out.append(f"{pad}{value(c[0])} = {value(c[1])}")
    elif k == "destructuring":
        out.append(f"{pad}{c[0].value}, {c[1].value} = {value(c[2])}")
    elif k == "accumulating":
        out.append(f"{pad}{value(c[0])} += {value(c[1])}")
    elif k in ("calling", "popping"):
        out.append(pad + value(s))
    elif k in METHODS:
        out.append(f"{pad}{wrap(c[0], ATOM)}.{METHODS[k]}({', '.join(map(value, c[1:]))})")
    elif k == "storing":
        out.append(f"{pad}{wrap(c[0], ATOM)}[{value(c[1])}] = {value(c[2])}")
    elif k == "deleting":
        out.append(f"{pad}del {wrap(c[0], ATOM)}[{value(c[1])}]")
    elif k == "returning":
        out.append(pad + ("return " + value(c[0]) if c else "return"))
    elif k == "breaking":
        out.append(pad + "break")
    elif k == "branching":
        out.append(f"{pad}if {value(c[0])}:")
        body(c[1], depth + 1, out)
        if len(c) > 2:
            out.append(f"{pad}else:")
            body(c[2], depth + 1, out)
    elif k in LOOP_HEADERS:
        out.append(pad + LOOP_HEADERS[k](c))
        body(c[-1], depth + 1, out)
    else:
        raise ValueError(f"not an operation that can stand alone: {k}")


def body(block, depth, out):
    if not block.kids:
        out.append("    " * depth + "pass")
    for s in block.kids:
        op(s, depth, out)


def rebound(n):
    """Names a function body rebinds (binding, destructuring, accumulating, loop names)."""
    found = set()
    for x in walk(n):
        if x.kind in ("binding", "accumulating"):
            found.add(x.kids[0].value)
        elif x.kind == "destructuring":
            found |= {x.kids[0].value, x.kids[1].value}
        elif x.kind in LOOP_NAMES:
            found |= {y.value for y in x.kids[:LOOP_NAMES[x.kind]]}
    return found


def to_python(tree):
    state, funcs = tree.kids
    out, sc = [], Scope({}, {})
    for s in state.kids:
        target, v = s.kids
        out.append(f"{target.value}: {type_str(infer(v, sc))} = {value(v)}")
        sc = sc.add(declared(s, sc))
    for f in funcs.kids:
        if out:
            out += ["", ""]
        params, block = f.kids
        ret, *ptypes = f.type.args
        sig = ", ".join(f"{p.value}: {type_str(t)}" for p, t in zip(params.kids, ptypes))
        out.append(f"def {f.value}({sig}) -> {type_str(ret)}:")
        shared = sorted((rebound(block) & set(sc.vars)) - {p.value for p in params.kids})
        if shared:
            out.append(f"    global {', '.join(shared)}")
        body(block, 1, out)
    text = "\n".join(out) + "\n"
    return "from typing import Callable\n\n\n" + text if "Callable[" in text else text
