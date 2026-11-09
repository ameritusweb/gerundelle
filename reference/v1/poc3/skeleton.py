"""Gerund skeletons with existential wiring (POC3 step 1).

A skeleton is a program of gerund operations whose inputs are unnamed slots. It's valid
if there EXISTS a wiring (each slot filled with a name in scope) that passes the rules
and the semantic gate (POC.md section 14c). Its valid wirings are its readings.

Built on poc2: a skeleton is a poc2 program whose input names are replaced by typed
holes that only accept names, so poc2's three-valued rules prune partial wirings.
Names being bound (binding targets, destructuring targets, loop names) stay fixed; which
reads become slots, and what may fill them, is the slot policy (strip).

strip(tree, policy)              -> the skeleton, and the number of slots
wirings_decomposed(skel, domain) -> every valid wiring (complete programs), with stats:
    sections wired alone and cached, then functions wired one at a time with the spec
    pruning each prefix (spec_rejects), then the full rules and the gate.
wirings(skel, domain)            -> the same by one depth-first search over all slots
    (step 1a; too slow beyond the color line, kept for comparison).
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "poc2"))
from dataflow import judge_complete  # noqa: E402
from grammar import LOOP_NAMES, Node, find, hole, holes, name, replace, visit  # noqa: E402
from rulesets import judge, ruleset  # noqa: E402
from specs import CASES, admit, run_case  # noqa: E402


def bound_positions(n):
    """Positions of n's parts that are names being bound (they stay fixed)."""
    if n.kind in LOOP_NAMES:
        return set(range(LOOP_NAMES[n.kind]))
    if n.kind in ("binding", "accumulating"):
        return {0}
    if n.kind == "destructuring":
        return {0, 1}
    return set()


SLOT_POLICIES = ("all", "origin", "external")  # default origin (decided 2026-10-20)


def externals(tree, fi):
    """Module state and the parameters of function fi: the names that reach it from outside."""
    f = tree.kids[1].kids[fi]
    return {s.kids[0].value for s in tree.kids[0].kids} | {p.value for p in f.kids[0].kids}


def strip(tree, policy="origin"):
    """The skeleton of a program: names used as inputs in function bodies become holes of
    their type that only a name may fill. Returns (skeleton, number of slots).
    policy decides which reads are slots and what may fill them (POC.md 14c, step 1c;
    "origin" is the decided default):
    - "all": every read is a slot, filled by any name in scope of its type (the design as
      stated; the most readings, but the wiring space is a product over every slot);
    - "origin": every read is a slot, but a read of an external name (state, parameter)
      is filled only by externals and a read of the function's own local only by locals,
      so the skeleton keeps whether an input comes from outside or from its own plumbing;
    - "external": only reads of externals are slots; reads of locals are fixed edges of
      the skeleton (fewest readings)."""
    assert policy in SLOT_POLICIES
    slots = []
    for v in visit(tree):
        if v.path and v.path[0] == 1 and v.node.kind == "name" and v.expect not in ("new", "target"):
            ext = v.node.value in externals(tree, v.path[1])
            if policy == "external" and not ext:
                continue
            tag = "slot" if policy == "all" else ("slot:external" if ext else "slot:local")
            slots.append((v.path, v.scope.vars.get(v.node.value), tag))
    for path, t, tag in slots:
        tree = replace(tree, path, Node("hole", value=tag, type=t))
    return tree, len(slots)


def may_fill(tree, v, nm):
    """Whether name nm may fill slot v under its tag."""
    if v.node.value == "slot":
        return True
    ext = nm in externals(tree, v.path[1])
    return ext if v.node.value == "slot:external" else not ext


def slot_holes(tree):
    return [v for v in visit(tree) if v.node.kind == "hole" and v.node.value.startswith("slot")]


def as_expr_holes(tree):
    """The same tree with slots shown to the rules as ordinary value holes."""
    def go(n):
        if n.kind == "hole" and n.value.startswith("slot"):
            return hole("expr", n.type)
        return Node(n.kind, [go(c) for c in n.kids], n.value, n.type)
    return go(tree)


SECTION_CACHE = {}


def section_paths(tree):
    """Paths of each function's top-level operations (its sections), grouped by function."""
    return [[(1, i, 1, j) for j in range(len(f.kids[1].kids))] for i, f in enumerate(tree.kids[1].kids)]


def node_at(tree, path):
    n = tree
    for i in path:
        n = n.kids[i]
    return n


def fill_slots(tree, slots, picks):
    for v, nm in zip(slots, picks):
        tree = replace(tree, v.path, name(nm))
    return tree


def section_key(tree, path):
    """A section's shape, scope and slot tags: identical keys have identical local wirings."""
    from printer import op
    first = slot_holes_under(tree, path)
    scope = tuple(sorted((k, str(t)) for k, t in (first[0].scope.vars.items() if first else ())))
    tags = tuple(v.node.value for v in first)
    lines = []
    op(node_at(tree, path), 0, lines)
    return "\n".join(lines), scope, tags


def slot_holes_under(tree, path):
    return [v for v in slot_holes(tree) if v.path[:len(path)] == path]


def section_wirings(tree, path, rules, stats, limit):
    """Every wiring of one section's slots that no rule rejects (with the rest of the
    program still unwired), as lists of names in slot order. Cached by section_key.
    The slots' paths are fixed (a name replaces a hole in place), so they're collected
    once. The rules don't judge here: they can't tell names apart within one section
    (ASSUMPTIONS.md W6) and cost most of the search's time; the function stage judges
    the survivors of the spec instead."""
    key = section_key(tree, path)
    if key in SECTION_CACHE:
        stats["cache_hits"] += 1
        return SECTION_CACHE[key]
    out = []
    hs = slot_holes_under(tree, path)
    options = [[nm for nm, ty in sorted(v.scope.vars.items()) if ty == v.node.type and may_fill(tree, v, nm)]
               for v in hs]

    from itertools import product
    for picks in product(*options):
        if stats["tried"] >= limit:
            break
        stats["tried"] += 1
        out.append(list(picks))
    SECTION_CACHE[key] = out
    return out


def slot_product(tree):
    """How many wirings each function has at most: the product of its slots' options."""
    out = []
    for i, f in enumerate(tree.kids[1].kids):
        n = 1
        for v in slot_holes(tree):
            if v.path[:2] == (1, i):
                n *= sum(1 for nm, ty in v.scope.vars.items() if ty == v.node.type and may_fill(tree, v, nm))
        out.append(n)
    return out


def wire_sections(tree, paths, choices, slot_paths=None):
    """tree with each section's slots filled from its chosen list of names. slot_paths maps
    a section path to its slots' paths (fixed: a name replaces a hole in place), so the
    tree needn't be rescanned per wiring."""
    for path, picks in zip(paths, choices):
        if not picks:
            continue
        sps = slot_paths[path] if slot_paths else [v.path for v in slot_holes_under(tree, path)]
        for sp, nm in zip(sps, picks):
            tree = replace(tree, sp, name(nm))
    return tree


COMMUTATIVE = {"adding", "combining"}


def fold_commutative(n):
    """A copy with the operands of commutative operations (adding, combining, == and !=
    comparisons) in a fixed order, so `a == b` and `b == a` are one reading (W8)."""
    kids = [fold_commutative(c) for c in n.kids]
    if n.kind in COMMUTATIVE or (n.kind == "comparing" and n.value in ("==", "!=")):
        kids = sorted(kids, key=repr)
    return Node(n.kind, kids, n.value, n.type)


def reading_key(tree):
    """Two wirings are the same reading if their commutative-folded canonical texts match."""
    from search import canonical
    return canonical(fold_commutative(tree))


def spec_outcome(domain, tree):
    """(rejected, share) for a partly wired program. rejected: some spec case fails without
    ever evaluating a hole. Code that never ran can't change a case's result, so no
    completion of the wiring can pass either: a sound prune. A case that reaches a hole is
    undecided. share: the cases passed outright over all cases, the graded signal a search
    uses to tell a half-wired program on the way to a correct one from junk. Stops at the
    first decided failure (most wrong wirings fail the first case), so the share is then a
    lower bound."""
    passed, cases = 0, CASES[domain]
    for case in cases:
        failed = run_case(case, tree)
        if not failed:
            passed += 1
        elif "unfilled hole" not in failed:
            return True, passed / len(cases)
    return False, passed / len(cases)


def spec_rejects(domain, tree):
    return spec_outcome(domain, tree)[0]


def node_key(n):
    """A hashable structural key of a tree (names, constants, holes and types included)."""
    return (n.kind, n.value, repr(n.type), tuple(node_key(c) for c in n.kids))


PREFIX_CACHE = {}  # (domain, k, node_key of the program with functions < k wired) -> survivors


def wirings_decomposed(skeleton, domain, limit=200_000):
    """Every valid wiring, found by decomposition (POC3 step 1b):
    1. sections: each top-level operation's slots are wired alone, pruned by the rules,
       cached by shape and scope;
    2. functions: the product of a function's section candidates;
    3. module: the functions are wired one at a time, in order. After each, the spec runs
       on the partly wired program; a case that fails before reaching a hole rejects the
       prefix (spec_outcome), and the never- and per-function rules then judge what the
       spec let through (the rules are the dear check, the spec the cheap one, so the
       spec goes first). The survivors of each prefix are cached (PREFIX_CACHE), so a
       skeleton that differs from a judged one in its last function only redoes that
       function. Complete wirings are then checked by every rule and the gate.
    A sum of small searches instead of one product over all slots. Without stage 3's
    pruning the editor's two functions left about 605,000 module combinations
    (2,702 x 224): the base rules can't tell which string goes where; the spec can.
    stats["best_graded"] is the best graded score seen (half the share of rules passed
    plus half the share of spec cases passed, on complete wirings; half the share of spec
    cases passed outright, on prefixes): a search's direction when there is no reading."""
    from itertools import product
    from specs import spec_score
    rules = ruleset(domain)
    stats = {"tried": 0, "pruned": 0, "cache_hits": 0, "prefix_hits": 0, "function_combos": 0, "module_combos": 0,
             "spec_pruned": 0, "fail_rules": 0, "fail_gate": 0, "best_graded": 0.0, "graded_runs": 0}
    # Only rules that can say False before the whole program is wired: never-rules and
    # per-function rules. Theory facets and other exists-rules can't fail until the end,
    # and computing them for every combination was where the time went.
    from rules import Facet
    early = [r for r in rules if not isinstance(r, Facet) and getattr(r, "kind", "never") != "exists"]
    stats["per_function_candidates"] = stats["slot_product"] = slot_product(skeleton)
    if max(stats["slot_product"], default=0) > limit:  # beyond the budget before any work: unjudged
        stats["capped"] = True
        return [], stats
    slot_paths = {}
    for paths in section_paths(skeleton):
        for p in paths:
            slot_paths[p] = [v.path for v in slot_holes_under(skeleton, p)]
    per_function = []
    for paths in section_paths(skeleton):
        cands = [section_wirings(skeleton, p, rules, stats, limit) for p in paths]
        kept = []
        for choice in product(*cands):
            stats["function_combos"] += 1
            if stats["function_combos"] > limit:
                break
            kept.append((paths, choice))
        per_function.append(kept)
    out = []

    def go(t, k):
        if stats["module_combos"] > limit:
            return
        if k == len(per_function):
            stats["module_combos"] += 1
            res = judge_complete(rules, t)
            rules_share = sum(v is True for v in res.values()) / len(res)
            if rules_share < 1.0:
                stats["fail_rules"] += 1
                if stats["graded_runs"] < 3:  # the spec on a failing wiring is dear; a few give the direction
                    stats["graded_runs"] += 1
                    stats["best_graded"] = max(stats["best_graded"], 0.5 * rules_share + 0.5 * spec_score(domain, t))
            elif admit(domain, t)[0]:
                out.append(t)
                stats["best_graded"] = 1.0
            else:
                stats["fail_gate"] += 1
                stats["best_graded"] = max(stats["best_graded"], 0.5 * rules_share + 0.5 * spec_score(domain, t))
            return
        key = (domain, k, node_key(t))
        if key in PREFIX_CACHE:
            stats["prefix_hits"] += 1
            survivors, best = PREFIX_CACHE[key]
        else:
            survivors, best = [], 0.0
            for paths, choice in per_function[k]:
                wired = wire_sections(t, paths, choice, slot_paths)
                rejected, share = spec_outcome(domain, wired)  # cheap: most wrong wirings fail the first case
                best = max(best, share)
                if rejected:
                    stats["spec_pruned"] += 1
                    continue
                if False in judge(early, as_expr_holes(wired)).values():  # dear: only on the spec's survivors
                    stats["pruned"] += 1
                    continue
                survivors.append(wired)
            PREFIX_CACHE[key] = (survivors, best)
        stats["best_graded"] = max(stats["best_graded"], 0.5 * best)
        for wired in survivors:
            go(wired, k + 1)
    go(skeleton, 0)
    stats["per_function_candidates"] = [len(k) for k in per_function]
    stats["capped"] = stats["tried"] >= limit or stats["function_combos"] > limit or stats["module_combos"] > limit
    return out, stats


def wirings(skeleton, domain, limit=100_000):
    """Every valid wiring of the skeleton (complete programs passing every rule and the
    gate), depth-first, filling the first slot with each name in scope of its type and
    pruning a partial wiring as soon as a rule says False. Returns (valid programs, stats)."""
    rules = ruleset(domain)
    stats = {"tried": 0, "pruned": 0, "complete": 0, "fail_rules": 0, "fail_gate": 0}
    out = []

    def go(tree):
        if stats["tried"] >= limit:
            return
        hs = slot_holes(tree)
        if not hs:
            stats["complete"] += 1
            res = judge_complete(rules, tree)
            if not all(x is True for x in res.values()):
                stats["fail_rules"] += 1
            elif admit(domain, tree)[0]:
                out.append(tree)
            else:
                stats["fail_gate"] += 1
            return
        v = hs[0]
        for nm, t in sorted(v.scope.vars.items()):
            if t != v.node.type or not may_fill(tree, v, nm):
                continue
            stats["tried"] += 1
            filled = replace(tree, v.path, name(nm))
            if slot_holes(filled) and False in judge(rules, as_expr_holes(filled)).values():
                stats["pruned"] += 1
                continue
            go(filled)
    go(skeleton)
    stats["capped"] = stats["tried"] >= limit
    return out, stats
