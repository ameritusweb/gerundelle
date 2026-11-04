"""Behavior specs per domain (PoC step 3, the semantic gate and the search's guide).

Each spec states what the domain's program must do, as test cases checked by the
operation-language interpreter (interp.py). Specs describe the behavior, not one
implementation, so any correct program passes. Inputs are chosen systematically (every
small case), not by hand, so a search can't slip through a gap between picked examples.

A spec is a list of cases; each case is a function tree -> "" (passed) or the reason it
failed. That makes behavior gradable:
- behaves(domain, tree) -> (True, "") or (False, the first failure): every case passes.
- spec_score(domain, tree) -> the share of cases passed, used by the search to tell a
  half-built program on the way to a correct one from junk (ASSUMPTIONS.md X15).
- admit(domain, tree) -> behaves, and also False if some part doesn't matter.
"""
from grammar import STMT_KINDS, Node, replace, visit
from interp import Fault, Machine


def strings(alphabet, max_len):
    """Every string over alphabet up to max_len characters."""
    out, layer = [""], [""]
    for _ in range(max_len):
        layer = [s + a for s in layer for a in alphabet]
        out += layer
    return out


def color_line_cases():
    """f1(content, meta) returns one (character, color) pair per position, in order. One
    case per pair of equal-length strings over {a, b} up to length 3 (equal length is the
    theory's precondition)."""
    def case(content, meta):
        def run(tree):
            got = Machine(tree).call("f1", content, meta)
            want = [(content[i], meta[i]) for i in range(len(content))]
            return "" if got == want else f"f1({content!r}, {meta!r}) returned {got!r}, not {want!r}"
        return run
    short = [case(c, m) for c in strings("ab", 3) for m in strings("ab", 3) if len(m) == len(c)]
    # Longer than any constant a program may use (grammar.CONSTANTS stops at 3), so a
    # truncation like result[:3] can't hide (POC3 audit round 2, ASSUMPTIONS.md W9).
    long = [case(c, m) for c, m in [("ababa", "babab"), ("aabba", "abbaa"), ("abababa", "bbbaaab"), ("aaaaaa", "bbbbbb")]]
    return short + long


def styled_edit_cases():
    """f1(at, text, styles) inserts text and its styles at position at; f2(start, end)
    deletes positions start..end-1 from both. One case for a short script, then, from
    content "abc" / styles "123", one per insert position and one per delete range."""
    def case(steps):
        def run(tree):
            m = Machine(tree)
            for fn, args, content, styles in steps:
                m.call(fn, *args)
                got = (m.globals["v1"], m.globals["v2"])
                if got != (content, styles):
                    return f"after {fn}{args}: content and styles are {got!r}, not {(content, styles)!r}"
            return ""
        return run
    script = [("f1", (0, "helo", "!!  "), "helo", "!!  "), ("f1", (3, "l", "@"), "hello", "!! @ "),
              ("f1", (5, "!", "#"), "hello!", "!! @ #"), ("f2", (0, 2), "llo!", " @ #"), ("f2", (1, 3), "l!", " #")]
    base = ("f1", (0, "abc", "123"), "abc", "123")
    cases = [case(script)]
    for at in range(4):
        cases.append(case([base, ("f1", (at, "xy", "!@"), "abc"[:at] + "xy" + "abc"[at:], "123"[:at] + "!@" + "123"[at:])]))
    for start in range(4):
        for end in range(start, 4):
            cases.append(case([base, ("f2", (start, end), "abc"[:start] + "abc"[end:], "123"[:start] + "123"[end:])]))
    return cases


def pubsub_chat_cases():
    """f1(topic, handler) subscribes, f2(topic, handler) unsubscribes, f3(topic, message)
    calls every handler subscribed to the topic, once each, and nothing else. One case
    per pair of topics from {'', 'a', 'b', 'ab'}, checked against a small model: three
    handlers subscribe across the two topics, messages go to both and to a topic nobody
    subscribed to, one handler unsubscribes, and messages go out again. (The hand-picked
    script this replaced never subscribed to two topics; ASSUMPTIONS.md S3, X13.)"""
    def case(t1, t2):
        def run(tree):
            got = {h: [] for h in ("h1", "h2", "h3")}
            handler = {h: got[h].append for h in got}
            model, m, want = {}, Machine(tree), {h: [] for h in got}
            script = [("f3", t1, "m0"), ("f1", t1, "h1"), ("f1", t2, "h2"), ("f1", t1, "h3"),
                      ("f3", t1, "m1"), ("f3", t2, "m2"), ("f3", "zz", "m3"),
                      ("f2", t1, "h1"), ("f3", t1, "m4"), ("f3", t2, "m5")]
            for fn, topic, x in script:
                if fn == "f1":
                    m.call("f1", topic, handler[x])
                    model.setdefault(topic, []).append(x)
                elif fn == "f2":
                    m.call("f2", topic, handler[x])
                    model[topic].remove(x)
                else:
                    m.call("f3", topic, x)
                    for h in model.get(topic, []):
                        want[h].append(x)
                if got != want:
                    return f"topics {t1!r}, {t2!r}: after {fn}({topic!r}, {x!r}) handlers got {got!r}, not {want!r}"
            return ""
        return run
    # Topics longer than any constant a program may use (grammar.CONSTANTS stops at 3), so
    # a cut key like topic[:3] can't hide (POC3 audit round 3, ASSUMPTIONS.md W9).
    topics = ["", "a", "b", "ab", "abab", "abba"]

    def twice(topic):
        """The same handler subscribed twice is called twice, and one unsubscribe leaves one
        (ASSUMPTIONS.md W33: a corner the script above never exercised)."""
        def run(tree):
            got, m = [], Machine(tree)
            h = got.append
            m.call("f1", topic, h)
            m.call("f1", topic, h)
            m.call("f3", topic, "m1")
            m.call("f2", topic, h)
            m.call("f3", topic, "m2")
            want = ["m1", "m1", "m2"]
            return "" if got == want else f"topic {topic!r}, handler subscribed twice: got {got!r}, not {want!r}"
        return run
    return [case(a, b) for a in topics for b in topics] + [twice("a"), twice("abab")]


CASES = {"color_line": color_line_cases(), "styled_edit": styled_edit_cases(), "pubsub_chat": pubsub_chat_cases()}


def run_case(case, tree):
    try:
        return case(tree)
    except Fault as e:
        return f"runtime fault: {e}"


def behaves(domain, tree):
    """(True, "") if every case passes, else (False, the first failure)."""
    for case in CASES[domain]:
        failed = run_case(case, tree)
        if failed:
            return False, failed
    return True, ""


def spec_score(domain, tree):
    """The share of the domain's cases the program passes (0 to 1)."""
    cases = CASES[domain]
    return sum(not run_case(case, tree) for case in cases) / len(cases)


def operations(tree):
    """Paths of every operation that stands alone (a statement) in the function bodies."""
    out = []

    def go(n, path):
        if n.kind in STMT_KINDS:
            out.append(path)
        for i, c in enumerate(n.kids):
            if c.kind == "block" or n.kind in ("block", "funcs", "func"):
                go(c, path + (i,))
    go(tree.kids[1], (1,))
    return out


def node_at(tree, path):
    n = tree
    for i in path:
        n = n.kids[i]
    return n


def admit(domain, tree):
    """The semantic gate: the program behaves as its spec says, and everything matters.
    Load-bearing pressure on behavior, as dataflow.py applies it to data flow. Each of
    these must break the spec; if the program still passes, the part was decoration:
    - removing any one operation that stands alone (with everything inside it): a call
      that does nothing, a redundant guard, a trailing returning;
    - keeping a branching's body but dropping its condition (and its else): an
      always-true guard around needed code (ASSUMPTIONS.md S5);
    - removing two operations of the same block together: a pair that cancels out, such
      as adding text and cutting it off again (S6)."""
    ok, why = behaves(domain, tree)
    if not ok:
        return False, why
    paths = operations(tree)
    for path in paths:
        if behaves(domain, replace(tree, path, []))[0]:
            return False, f"{node_at(tree, path).kind} at {path} doesn't matter: the spec passes without it"
    for path in paths:
        n = node_at(tree, path)
        if n.kind == "branching" and behaves(domain, replace(tree, path, list(n.kids[1].kids)))[0]:
            return False, f"the condition of the branching at {path} doesn't matter: the spec passes with its body alone"
    for a in paths:
        for b in paths:
            if a < b and a[:-1] == b[:-1]:  # same block; remove the later one first so the earlier path holds
                if behaves(domain, replace(replace(tree, b, []), a, []))[0]:
                    return False, f"operations at {a} and {b} cancel out: the spec passes without both"
    # - a slice that could be its operand: result[:len(content)] on a result that is already
    #   that long, x[:n] where n is always the length (POC3 audit round 7). The same pressure
    #   as above, one level down: every cut must change something the spec sees.
    for v in visit(tree):
        if v.path and v.path[0] == 1 and v.node.kind in ("slicing_before", "slicing_from", "slicing_between"):
            if behaves(domain, replace(tree, v.path, v.node.kids[0]))[0]:
                return False, f"the slice at {v.path} doesn't matter: the spec passes with its operand alone"
    # - a part of a concatenation that could be left out (a + '' in disguise): the same
    #   pressure for the other value kind the search builds (ASSUMPTIONS.md W15).
    for v in visit(tree):
        if v.path and v.path[0] == 1 and v.node.kind == "concatenating" and len(v.node.kids) > 2:
            for i in range(len(v.node.kids)):
                rest = [k for j, k in enumerate(v.node.kids) if j != i]
                if behaves(domain, replace(tree, v.path, Node("concatenating", rest)))[0]:
                    return False, f"part {i} of the concatenation at {v.path} doesn't matter: the spec passes without it"
        if v.path and v.path[0] == 1 and v.node.kind == "concatenating" and len(v.node.kids) == 2:
            for i in range(2):
                if behaves(domain, replace(tree, v.path, v.node.kids[1 - i]))[0]:
                    return False, f"part {i} of the concatenation at {v.path} doesn't matter: the spec passes without it"
    return True, ""
