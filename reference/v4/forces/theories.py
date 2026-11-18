"""Theories as rules over the force AST, and a search over force skeletons with
step() as the gate (world-model POC steps 2 and 3; the code POC's steps 2-3 in
physics; NEWTONIAN_WORLD_MODEL.md sections 9, 13).

A theory is 3-6 rules over a force skeleton, three-valued as in poc2: a rule
answers True, False or None on a partly wired scene, and a False is final so
the search prunes on it. Two kinds of rule appear:
- structural: decided by the shape alone, before any slot is filled (a tower
  has no hanging member; a suspension has no supporting one). These prune
  whole skeletons before any wiring is tried.
- balance: a filled member's reserve against the load on it. The load from a
  part-filled subtree is a lower bound (weights are nonnegative), so a False
  is final: the prune the search leans on, as the spec was in poc3.

The gate is the simulator: a complete wiring is admitted if step() finds no
diff (every doing keeps its gerund). The rules are cheap and run on every
partial wiring; the gate is dear and runs only on their survivors - the same
cost order poc3 settled on. The rules are also NARROWER than the gate where
the theory says more than "it holds" (pb_tapering keeps one of two
gate-valid orders of the stone and the oak).

The held-out material test (section 10): no rule names a material. Suspension's
rules were written with rope and chain in hand; the oak beam, used only in the
compression scenes, must read as a suspension member because the rule asks for
tensile reserve, not for rope-ness. The same rope is invalid as a post and
valid as a hanger: which reserve the load reads is a fact about the gerund.
"""
from itertools import product

from poc import INF, Node, Obj, anchoring, doing, doings, label, show, slot, slots, step, wire


# ---- objects (internal forces; tensile now set per material) ----------------------

MATERIALS = {o.name: o for o in [
    Obj("ground", 0.0),
    Obj("thatch-roof", 5.0, capacity=20.0, cohesion=30.0, tensile=2.0),
    Obj("lantern", 3.0, capacity=1.0, cohesion=20.0, tensile=10.0),
    Obj("stone-post", 6.0, capacity=30.0, cohesion=40.0, tensile=1.0),
    Obj("oak-beam", 4.0, capacity=12.0, cohesion=30.0, tensile=18.0),
    Obj("plank", 1.0, capacity=3.0, cohesion=10.0, tensile=2.0),
    Obj("hemp-rope", 0.5, capacity=0.3, cohesion=6.0, tensile=25.0),
    Obj("steel-chain", 2.0, capacity=0.5, cohesion=60.0, tensile=50.0),
]}


# ---- judging: three-valued rules over partly wired scenes --------------------------

def named(label_, kind):
    def wrap(fn):
        fn.__name__ = label_
        fn.kind = kind
        return fn
    return wrap


def alldoings(n):
    yield n
    for k in doings(n):
        yield from alldoings(k)


def finished(scene):
    return all(n.doer is not None for n in alldoings(scene))


def lb_output(n, objs):
    """A lower bound on the force this doing hands to its bearer: unfilled
    doers weigh at least nothing, so the bound only grows as slots fill."""
    w = objs[n.doer].weight if n.doer is not None else 0.0
    return w + lb_external(n, objs)


def lb_external(n, objs):
    return sum(lb_output(k, objs) for k in doings(n))


def reserve(n, objs):
    """The internal reserve this doing's load reads: tensile when hanging,
    capacity when bearing. A fact about the gerund, not the object."""
    o = objs[n.doer]
    return o.tensile if n.kind == "hanging" else o.capacity


def judge(rules, scene, objs):
    return {r.__name__: r(scene, objs) for r in rules}


# ---- rules shared by both theories ------------------------------------------------

@named("grounded", "every")
def grounded(scene, objs):
    """The configuration stands on an anchor (structural: decided at the shape)."""
    return scene.kind == "anchoring"


@named("raised", "every")
def raised(scene, objs):
    """The load does not lie on the anchor itself: everything the anchor bears
    bears something in turn (the task is to hold the load up)."""
    return all(doings(k) for k in doings(scene))


@named("members_hold", "every")
def members_hold(scene, objs):
    """Every filled member's reserve covers the load on it, on the lower bound:
    a part-filled violation is already final."""
    for n in alldoings(scene):
        if n.doer is None or n.kind == "anchoring":
            continue
        if lb_external(n, objs) > reserve(n, objs):
            return False
    return True if finished(scene) else None


@named("members_cohere", "every")
def members_cohere(scene, objs):
    """Every filled member's cohesion covers the load through it, on the lower
    bound. Added after the gate caught what members_hold missed (the rope over
    the oak holds its load but comes apart): a gap found by the gate gets a
    rule, as in the poc3 audits."""
    for n in alldoings(scene):
        if n.doer is None or n.kind == "anchoring":
            continue
        if lb_output(n, objs) > objs[n.doer].cohesion:
            return False
    return True if finished(scene) else None


# ---- post-and-beam: a compression chain -------------------------------------------

@named("pb_compression_only", "never")
def pb_compression_only(scene, objs):
    """No member hangs: every force in the chain is borne (structural)."""
    return not any(n.kind == "hanging" for n in alldoings(scene))


@named("pb_tapering", "every")
def pb_tapering(scene, objs):
    """A tower tapers: a bearer is at least as strong as the bearer it carries.
    Both orders of the stone and the oak pass the gate; the theory keeps one.
    Decided pairwise as slots fill."""
    for n in alldoings(scene):
        if n.kind != "supporting" or n.doer is None:
            continue
        for k in doings(n):
            if k.kind == "supporting" and k.doer is not None \
                    and objs[n.doer].capacity < objs[k.doer].capacity:
                return False
    return True if finished(scene) else None


# ---- suspension: a tension chain ---------------------------------------------------

@named("susp_tension_only", "never")
def susp_tension_only(scene, objs):
    """Below the anchor, every doing hangs: the load reaches the anchor through
    tension alone (structural)."""
    return not any(n.kind in ("supporting", "resting") for n in alldoings(scene) if n.kind != "anchoring")


THEORIES = {
    "post_and_beam": [grounded, raised, pb_compression_only, pb_tapering, members_hold, members_cohere],
    "suspension": [grounded, raised, susp_tension_only, members_hold, members_cohere],
}


# ---- the gate: the simulator -------------------------------------------------------

def admit(scene, objs):
    """A configuration is admitted if stepping it changes nothing: every doing
    keeps its gerund. The gate's question is existence of equilibrium, asked by
    running the world, not by reading the tree."""
    _, events = step(scene, objs)
    return not events, events


# ---- search over force skeletons (step 3): shapes, then wirings, rules before gate --

def shapes(load, max_links=2):
    """Every chain skeleton holding the load through 1..max_links slotted
    members on the ground anchor. Each link bears (supporting) or hangs
    (hanging); the load's own gerund follows its holder."""
    out = []
    for n in range(1, max_links + 1):
        for kinds in product(("supporting", "hanging"), repeat=n):
            node = doing("resting" if kinds[-1] == "supporting" else "hanging", load)
            for k in reversed(kinds):
                node = slot(k, node)
            out.append(anchoring("ground", node))
    return out


def fill(skel, picks):
    """The skeleton with its first len(picks) doer slots filled, in tree order.
    No thresholds: the rules read reserves from the objects; wire() builds the
    phase-change nodes for the gate."""
    it = iter(picks)

    def go(n):
        doer = n.doer if n.doer is not None else next(it, None)
        return Node(n.kind, [go(k) for k in doings(n)], doer)
    return go(skel)


def search(rules, shape_list, inventory, objs):
    """Every reading of every shape: distinct objects fill the slots depth-first,
    a partial wiring is pruned as soon as a rule says False, and the gate runs
    only on complete wirings the rules let through. Returns (readings, stats);
    a reading is (shape, picks, wired scene)."""
    stats = {"shapes": 0, "shape_pruned": 0, "tried": 0, "rule_pruned": 0,
             "gate_runs": 0, "gate_rejects": 0}
    readings = []
    for shape in shape_list:
        stats["shapes"] += 1
        if False in judge(rules, fill(shape, ()), objs).values():
            stats["shape_pruned"] += 1
            continue
        k = slots(shape)

        def go(picks):
            for nm in inventory:
                if nm in picks:
                    continue
                ps = picks + (nm,)
                stats["tried"] += 1
                res = judge(rules, fill(shape, ps), objs)
                if False in res.values():
                    stats["rule_pruned"] += 1
                    continue
                if len(ps) < k:
                    go(ps)
                    continue
                stats["gate_runs"] += 1
                wired = wire(shape, ps, objs)
                if admit(wired, objs)[0] and all(v is True for v in res.values()):
                    readings.append((shape, ps, wired))
                else:
                    stats["gate_rejects"] += 1
        go(())
    return readings, stats


# ---- demo --------------------------------------------------------------------------

def chain_str(scene):
    """A one-line reading: the chain from the anchor down to the load."""
    parts, n = [], scene
    while True:
        parts.append(label(n))
        ds = doings(n)
        if not ds:
            return " <- ".join(parts)
        n = ds[0]


def print_rules(name, rules):
    print(f"  {name}:")
    for r in rules:
        print(f"    {r.__name__} ({r.kind}): {r.__doc__.splitlines()[0]}")


def run_task(title, rules, load, inventory, objs, max_links=2):
    print(f"\n== {title} ==\n")
    readings, stats = search(rules, shapes(load, max_links), inventory, objs)
    print(f"  shapes {stats['shapes']} (pruned at the shape, before any wiring:"
          f" {stats['shape_pruned']}); wirings tried {stats['tried']},"
          f" rule-pruned {stats['rule_pruned']};")
    print(f"  gate ran {stats['gate_runs']} times, rejected {stats['gate_rejects']}."
          f" Readings: {len(readings)}.\n")
    for _, picks, wired in readings:
        print(f"    {chain_str(wired)}")
    return readings


def main():
    objs = MATERIALS
    print("== Theories as rules over the force AST ==\n")
    for name, rules in THEORIES.items():
        print_rules(name, rules)

    inventory = ("stone-post", "oak-beam", "plank", "hemp-rope", "steel-chain")
    run_task("Task 1: hold the thatch-roof up (post_and_beam)",
             THEORIES["post_and_beam"], "thatch-roof", inventory, objs)

    print("\n  Narrower than the gate: the swapped order is an equilibrium, but not a tower.")
    tower = anchoring("ground", slot("supporting", slot("supporting", doing("resting", "thatch-roof"))))
    swapped = wire(tower, ("oak-beam", "stone-post"), objs)
    ok, _ = admit(swapped, objs)
    verdict = judge(THEORIES["post_and_beam"], fill(tower, ("oak-beam", "stone-post")), objs)
    print(f"    {chain_str(swapped)}")
    print(f"    gate: {'admits (no diff when stepped)' if ok else 'rejects'};"
          f" pb_tapering: {verdict['pb_tapering']}")

    run_task("Task 2: hang the lantern (suspension)",
             THEORIES["suspension"], "lantern", inventory, objs)

    print("\n  The held-out material: suspension's rules were written with rope and chain")
    print("  in hand, and no rule names a material. The oak beam, used only in the")
    print("  compression scenes, reads as a suspension member (tensile 18 covers the")
    print("  lantern); the same rope that reads here is invalid as a post in task 1")
    print("  (capacity 0.3): which reserve the load consults is a fact about the gerund.")


if __name__ == "__main__":
    main()
