"""A second theory for the harder transfer test: the mask. A test of one sequence at a position guards what is taken
from another sequence at the same position (select the characters of v2 where v1 has 'a').

    def f1(v1: str, v2: str) -> str:
        v3 = ''
        for v4 in range(len(v1)):
            if v1[v4] == 'a':
                v3 += <str>          # v2[v4]
        return v3

Its facet has roles of its own (test, selected, accumulator), none of lockstep's names. Written here, not in poc2's
rules.py (the world's physics there stays as it is); registered in rules.FACETS under its own theory name.
"""
import codeworld  # noqa: F401  (puts poc2 on the path)
import grammar as G  # noqa: E402
import rules  # noqa: E402
import specs  # noqa: E402
from grammar import STR, FN  # noqa: E402


def program():
    return G.module(state=[], funcs=[
        G.func("f1", ["v1", "v2"], FN([STR, STR], STR), G.block(
            G.binding(G.name("v3"), G.constant("")),
            G.iterating_over_positions(G.name("v4"), G.name("v1"), G.block(
                G.branching(G.comparing("==", G.indexing(G.name("v1"), G.name("v4")), G.constant("a")), G.block(
                    G.accumulating(G.name("v3"), G.indexing(G.name("v2"), G.name("v4"))),
                )),
            )),
            G.returning(G.name("v3")),
        )),
    ])


SLOT = (1, 0, 1, 1, 2, 0, 1, 0, 1)   # the accumulated value


def find_mask(tree):
    """A branching that tests one sequence at a loop's position, guarding an accumulation of a read of another
    sequence at the same position. Roles: test, selected, accumulator."""
    out = []
    for f in rules.funcs(tree).values():
        for loop in (n for n in rules.walk(f.kids[1]) if n.kind == "iterating_over_positions"):
            pos = loop.kids[0].value
            for b in (n for n in rules.walk(loop.kids[-1]) if n.kind == "branching"):
                test = b.kids[0]
                reads = [x for x in rules.walk(test) if x.kind == "indexing" and x.kids[1].kind == "name"
                         and x.kids[1].value == pos and x.kids[0].kind == "name"]
                for acc in (n for n in rules.walk(b.kids[1]) if n.kind == "accumulating"):
                    sel = acc.kids[1]
                    if (sel.kind == "indexing" and sel.kids[0].kind == "name" and sel.kids[1].kind == "name"
                            and sel.kids[1].value == pos and any(r.kids[0].value != sel.kids[0].value for r in reads)):
                        out.append({"test": test, "selected": sel, "accumulator": acc})
    return out


mask_select = rules.Facet("mask_select", ["test", "selected", "accumulator"], find_mask)
rules.FACETS["mask"] = [mask_select]


def cases():
    """f1(v1, v2) returns the characters of v2 at the positions where v1 has 'a'; v1 and v2 of equal length."""
    def case(a, b):
        def run(tree):
            got = specs.Machine(tree).call("f1", a, b)
            want = "".join(b[i] for i in range(len(a)) if a[i] == "a")
            return "" if got == want else f"f1({a!r}, {b!r}) returned {got!r}, not {want!r}"
        return run
    pairs = [(a, b) for a in specs.strings("ab", 3) for b in specs.strings("xy", 3) if len(a) == len(b)]
    pairs += [("ababa", "xyxyx"), ("aabba", "xyyxx"), ("abababa", "yyyxxxy")]
    return [case(a, b) for a, b in pairs]


specs.CASES["mask"] = cases()
