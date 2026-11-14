"""The minimal (SOV, world) pair, and structural similarity between two of them (SOV_WORLD_PAIR.md).

A known concept is the minimal pair that describes or illustrates it. The world has a default behavior. Funded relations
in the SOV restrict it, and the concept shows in the dynamics when you act. An unfunded relation is still an unknown and
restricts nothing. The concepts inside a pair are strings; a pair doesn't recurse.

"Restriction" is used here because "constraint" already means something else in Gerundelle: constraints_from, runs_into and
notice narrow what the mind chooses, while these narrow what the world can do.
"""
import copy
import os
import sys
from dataclasses import dataclass
from itertools import chain, combinations, permutations

sys.path.insert(0, os.environ.get("GERUNDELLE", __import__("paths").GERUNDELLE))
from force_world import AGENT, AMOUNTS, effect_id, poc  # noqa: E402

CAUSES, CONDITIONED_BY, PREVENTS = "causes", "conditioned_by", "prevents"
TRIGGER = "agent"     # in conditioned_by: the agent's own push
QUIET = ("quiet",)    # in a trace: nothing flipped, and the agent may act
WEIGHT = {"seen": 1.0, "worked": 1.0, "told": 0.5, "imagined": 0.0}
OPEN_BELOW = 1.0      # a slot is open below this funding (Understanding.open_slots)
SLOT_WEIGHT = 0.5     # an unknown relation weighs what a told one does in S_sov
SIDEWAYS = AMOUNTS["hard"]
SLICES = 8            # slices watched after each push
CAP = 200_000         # prefixes before the dynamics are reported as too large


class TooLarge(Exception):
    pass


@dataclass(frozen=True)
class Receipt:
    how: str        # "seen", "told", "worked" or "imagined"
    world: str      # the world it came from
    source: tuple   # the trials behind it, or who told it


class Pair:
    def __init__(self, concept, relations, world):
        self.concept, self.world = concept, world
        self.relations = {r: list(receipts) for r, receipts in relations.items()}
        self.restrictions = set()
        self.license()

    def funding(self, relation):
        return sum(WEIGHT[x.how] for x in self.relations.get(relation, ()))

    def license(self):
        """Funding is checked when a restriction is made: any funding above zero restricts fully."""
        self.restrictions |= {r for r in self.relations if self.funding(r) > 0}

    def evict(self, relation):
        """Its evidence goes (Archaize). The restriction stays until retract: licensing, and the Lean's Law 5."""
        self.relations[relation] = []

    def retract(self, relation):
        self.restrictions.discard(relation)

    def unknowns(self):
        """Relations that restrict nothing."""
        return set(self.relations) - self.restrictions

    def open_slots(self):
        """Relations still pulling for evidence. A told relation is here and also restricts."""
        return {r for r in self.relations if self.funding(r) < OPEN_BELOW}

    def objects(self):
        return objects_of(self.world)

    def dynamics(self, **kw):
        return dynamics(self.world, self.restrictions, **kw)


class MainSOV:
    """The graph of knowns and unknowns. A known's single feasible resolution is its pair."""

    def __init__(self):
        self.nodes, self.relations, self.pairs = set(), set(), {}

    def relate(self, relation, a, b):
        self.nodes |= {a, b}
        self.relations.add((relation, a, b))

    def fill(self, node, pair):
        """Filling a slot narrows it to one pair. A pair with nothing funded is no understanding yet."""
        if not pair.restrictions:
            raise ValueError(f"{pair.concept}: nothing funded")
        self.nodes.add(node)
        self.pairs[node] = pair

    def unknowns(self):
        return self.nodes - set(self.pairs)

    def outer(self, node):
        """How a node sits in the main graph: all an unknown has."""
        return {r for r in self.relations if node in r[1:]}


# ---- the default world ------------------------------------------------------------------------
#
# The simulator's force only travels between parent and child, so the layer below holds the coupling between objects as
# potential forces. After any flip, the next slice may push any subset of the objects sideways. Relations remove branches.

def objects_of(world):
    return sorted(o for o in world.states(world.start) if o != world.start.doer)


def obj_of(fact):
    return fact.rsplit("_", 1)[0]


def holds(fact, states):
    obj, gerund = fact.rsplit("_", 1)
    return states.get(obj) == gerund


def allowed(restrictions, before, fired, flips):
    """Whether a slice survives: `fired` is what flipped in the slice before, `flips` is what flipped in this one."""
    for relation, a, b in restrictions:
        if relation == CAUSES and a in fired and b not in flips:
            return False
        if relation == CONDITIONED_BY and a in flips and b not in fired:   # conditioned_by(a, b): a only if b just fired
            return False
        if relation == PREVENTS and b in flips and holds(a, before):
            return False
    return True


def state_of(world, tree):
    root = world.start.doer
    return tuple(sorted((o, g) for o, g in world.states(tree).items() if o != root))


def dynamics(world, restrictions, slices=SLICES, cap=CAP):
    """The runs from every quiet state the pair can reach, as a set of prefixes. A run is a push, carrying the state it was
    made in, then what flipped in each slice, then quiet unless the slice limit came first. A branch that can't reach quiet
    or the limit doesn't exist. Each run counts once, however many times it could be repeated. Raises TooLarge past cap."""
    objs = objects_of(world)
    subsets = list(chain.from_iterable(combinations(objs, k) for k in range(len(objs) + 1)))
    prefixes, memo, frontier, seen = set(), {}, [copy.deepcopy(world.start)], set()

    def step(tree, pushes):
        key = (state_of(world, tree), pushes)
        if key not in memo:
            t = tree
            for doer, amount in pushes:
                t = world._apply(t, doer, amount, AGENT)
            t, events = poc.step(copy.deepcopy(t), world.objs)
            memo[key] = (world._unpush(t), frozenset(effect_id(e) for e in events))
        return memo[key]

    def keep(prefix):
        prefixes.add(prefix)
        if len(prefixes) > cap:
            raise TooLarge

    def after(tree, fired, prefix, left):
        if not fired:   # the world went quiet: part of the run, so "must go on" differs from "may stop"
            keep(prefix + (QUIET,))
            frontier.append(tree)
            return True
        if left == 0:
            keep(prefix)
            return True
        before, alive, tried = world.states(tree), False, set()
        for targets in subsets:
            nxt, flips = step(tree, tuple((o, SIDEWAYS) for o in targets))
            outcome = (flips, state_of(world, nxt))
            if outcome in tried or not allowed(restrictions, before, fired, flips):
                continue
            tried.add(outcome)
            alive |= after(nxt, flips, prefix + (tuple(sorted(flips)),) if flips else prefix, left - 1)
        if alive:
            keep(prefix)
        return alive

    while frontier:
        tree = frontier.pop()
        state = state_of(world, tree)
        if state in seen:
            continue
        seen.add(state)
        before = world.states(tree)
        for inv in world.invitations(tree):
            nxt, flips = step(tree, ((inv[1], AMOUNTS[inv[0]]),))
            if not flips or not allowed(restrictions, before, frozenset({TRIGGER}), flips):
                continue
            acted = (("push", inv[0], inv[1], state),)
            if after(nxt, flips, acted + (tuple(sorted(flips)),), slices):
                keep(acted)
    return prefixes


def spare_relations(pair, **kw):
    """Restrictions whose removal leaves the dynamics unchanged."""
    full = pair.dynamics(**kw)
    out = []
    for r in sorted(pair.restrictions):
        try:
            if dynamics(pair.world, pair.restrictions - {r}, **kw) == full:
                out.append(r)
        except TooLarge:
            pass   # it let in more than the cap: it was doing work
    return out


def spare_objects(pair):
    """Objects no restriction mentions. An unmentioned object isn't inert: under the default it can push the others, so it
    changes the dynamics by adding what the SOV doesn't understand, not by doing work for the concept."""
    mentioned = {obj_of(x) for r in pair.restrictions for x in r[1:] if x != TRIGGER}
    return [o for o in pair.objects() if o not in mentioned]


def reduced(pair, reverse=False, **kw):
    """The pair with spare relations removed one at a time until none is left. Removing one can make another necessary, so
    the result can depend on the order; reverse tries the other order."""
    kept = set(pair.restrictions)
    changed = True
    while changed:
        changed = False
        full = dynamics(pair.world, kept, **kw)
        for r in sorted(kept, reverse=reverse):
            try:
                if dynamics(pair.world, kept - {r}, **kw) == full:
                    kept.discard(r)
                    changed = True
                    break
            except TooLarge:
                pass
    return Pair(pair.concept, {r: pair.relations[r] for r in kept}, pair.world)


# ---- structural similarity -------------------------------------------------------------------

def map_fact(s, phi):
    if s == TRIGGER:
        return s
    obj, gerund = s.rsplit("_", 1)
    return f"{phi.get(obj, '?' + obj)}_{gerund}"


def map_relation(r, phi):
    return (r[0], map_fact(r[1], phi), map_fact(r[2], phi))


def map_prefix(prefix, phi):
    out = []
    for part in prefix:
        if part == QUIET:
            out.append(part)
        elif part[0] == "push":
            state = tuple(sorted((phi.get(o, "?" + o), g) for o, g in part[3]))
            out.append(("push", part[1], phi.get(part[2], "?" + part[2]), state))
        else:
            out.append(tuple(sorted(map_fact(f, phi) for f in part)))
    return tuple(out)


def dice(a, b):
    return 2 * len(a & b) / (len(a) + len(b)) if a or b else 0.0


def s_sov(a, b, phi):
    """Funding-weighted relations preserved under phi, both ways. Restrictions match restrictions, unknowns match unknowns."""
    def weights(p, f):
        out = {("restricts", f(r)): p.funding(r) or SLOT_WEIGHT for r in p.restrictions}
        out.update({("unknown", f(r)): SLOT_WEIGHT for r in p.unknowns()})
        return out
    wa, wb = weights(a, lambda r: map_relation(r, phi)), weights(b, lambda r: r)
    total = sum(wa.values()) + sum(wb.values())
    return 2 * sum(min(v, wb[k]) for k, v in wa.items() if k in wb) / total if total else 0.0


def mappings(a, b):
    oa, ob = a.objects(), b.objects()
    if len(oa) <= len(ob):
        for image in permutations(ob, len(oa)):
            yield dict(zip(oa, image))
    else:
        for image in permutations(oa, len(ob)):
            yield dict(zip(image, ob))


def s_world(a, b, da, db, phi, **kw):
    """Each pair's relations in the other's world through phi, against its own dynamics, averaged both ways. None if too
    large to compute."""
    inverse = {v: k for k, v in phi.items()}
    try:
        there = dynamics(b.world, {map_relation(r, phi) for r in a.restrictions}, **kw)
        here = dynamics(a.world, {map_relation(r, inverse) for r in b.restrictions}, **kw)
    except TooLarge:
        return None
    return (dice({map_prefix(p, phi) for p in da}, there) + dice({map_prefix(p, inverse) for p in db}, here)) / 2


def first_divergence(da, db):
    """The longest prefix the two dynamics share, and how each goes on from it."""
    shared = da & db
    if not shared:
        return None
    base = max(shared, key=lambda p: (len(p), p))
    nexts = lambda d: sorted({p[len(base)] for p in d if len(p) > len(base) and p[:len(base)] == base}, key=str)
    return base, nexts(da), nexts(db)


def similarity(a, b, **kw):
    """The three scores under one mapping, the one maximizing S_sov + S_dyn. S_world is read under it."""
    da, db = a.dynamics(**kw), b.dynamics(**kw)
    best, best_key, ties = None, None, 0
    for phi in mappings(a, b):
        sv = s_sov(a, b, phi)
        dy = dice({map_prefix(p, phi) for p in da}, db)
        key = (round(sv + dy, 9),)
        if best_key is None or key > best_key:
            best, best_key, ties = dict(sov=sv, dyn=dy, phi=phi), key, 1
        elif key == best_key:
            ties += 1
    phi = best["phi"]
    return dict(best, world=s_world(a, b, da, db, phi, **kw), ties=ties, sizes=(len(da), len(db)),
                diverge=first_divergence({map_prefix(p, phi) for p in da}, db))
