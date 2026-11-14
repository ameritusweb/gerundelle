"""Pairs that run forward (LADDER.md, rung 4; SOV_WORLD_PAIR.md).

The SOV specifies the dynamics: a relation says this push reading on A puts a force of this strength on B within this range of ticks. The world runs forward from those
relations, and each object's reserve decides whether it flips. Nothing happens that isn't specified, and nothing is enumerated. All of it is read from what a mind experienced.
"""
import copy
from itertools import permutations

import pair  # noqa: F401  (puts Gerundelle on the path)
from force_world import AGENT, AMOUNTS, effect_id, poc
from sov_agent import SovAgent

SLICES = 8     # a run stops here if it hasn't gone quiet
ORDER = sorted(AMOUNTS, key=AMOUNTS.get)   # the mind's own scale of pushes, weakest first


class TimedAgent(SovAgent):
    """A SovAgent that keeps the tick each effect arrived at, which agent.pushed drops. It adds nothing to the mind."""

    def __init__(self, world, mind=None):
        super().__init__(world, mind)
        self.timed = []   # (invitation, facts at the push, {effect: tick})

    def watch(self, diffs, rec):
        inv, facts, k, effects = self.watching
        done = k + 1 >= self.world.horizon
        super().watch(diffs, rec)
        if done:
            self.timed.append((inv, facts, dict(effects)))


def obj_of(fact):
    return fact.rsplit("_", 1)[0]


def push_id(inv):
    return f"{inv[0]}_push:{inv[1]}_{inv[2]}"


def readings_of(meta, c, conds=()):
    """A push's readings as the mind's own splits make them: two situations with different outcomes are two concepts."""
    if c in meta.splits:
        sp = meta.splits[c]
        return readings_of(meta, sp["yes"], conds + ((sp["tag"], True),)) + readings_of(meta, sp["no"], conds + ((sp["tag"], False),))
    return [(c, conds)]


def holds(conds, facts):
    return all((t in facts) == want for t, want in conds)


def relations_of(agent, names):
    """What the mind's trials specify: (c, conds, target, strength, lo, hi) -> the trials behind it."""
    meta, objects = agent.mind.meta, set(names)
    by_push = {}
    for k, (inv, facts, effects) in enumerate(agent.timed):
        by_push.setdefault(inv, []).append((k, facts, effects))
    flips_own = {}   # object -> the strengths the mind has seen flip it directly
    for inv, rows in by_push.items():
        if any(obj_of(e) == inv[1] and t == 0 for _, _, effects in rows for e, t in effects.items()):
            flips_own.setdefault(inv[1], set()).add(inv[0])
    out = {}
    for inv, rows in by_push.items():
        c = push_id(inv)
        for reading, conds in readings_of(meta, c):
            trials = [r for r in rows if holds(conds, r[1])]
            if not trials:
                continue
            for target in sorted(objects - {inv[1]}):
                arrivals = []
                for _, _, effects in trials:
                    ticks = [t for e, t in effects.items() if obj_of(e) == target]
                    arrivals.append(min(ticks) if ticks else None)
                if None in arrivals:   # only sometimes: still conflated, so it specifies nothing yet
                    continue
                seen = flips_own.get(target)
                strength = next(s for s in ORDER if s in seen) if seen else inv[0]
                out[(c, conds, target, strength, min(arrivals), max(arrivals))] = tuple(k for k, _, _ in trials)
    return out


class Forward:
    """A room's objects, run forward from a set of relations. Steps are remembered, so reduction stays cheap."""

    def __init__(self, room):
        self.room = copy.deepcopy(room)
        self.room.episode = None
        self.memo = {}
        self.starts, self.real = self.explore()

    def state(self, tree):
        return tuple(sorted((o, g) for o, g in self.room.states(tree).items() if o != self.room.start.doer))

    def explore(self):
        """What the room really does, from each quiet state it can reach: its own physics, not the mind's."""
        starts, real, frontier, seen = {}, {}, [self.room], set()
        while frontier:
            w = frontier.pop()
            st = self.state(w.tree)
            if st in seen:
                continue
            seen.add(st)
            starts[st] = w.tree
            for inv in w.invitations():
                v = copy.deepcopy(w)
                v.reset = None   # never set back
                trail = [frozenset(effect_id(e) for e in v.act(inv))]
                while trail[-1] and len(trail) < SLICES:
                    trail.append(frozenset(effect_id(e) for e in v.act(None)))
                real[(st, inv)] = tuple(s for s in trail if s)
                if not trail[-1]:
                    v.reset = type(self.room).reset.__get__(v)
                    frontier.append(v)
        return starts, real

    def step(self, tree, pushes):
        key = (self.state(tree), pushes)
        if key not in self.memo:
            t = tree
            for doer, amount in pushes:
                t = self.room._apply(t, doer, amount, AGENT)
            t, events = poc.step(copy.deepcopy(t), self.room.objs)
            self.memo[key] = (self.room._unpush(t), frozenset(effect_id(e) for e in events))
        return self.memo[key]

    def run(self, st, inv, relations):
        """A push, then what the relations specify. A force landing on an object fires the relations of that push reading."""
        tree, pending, trail, t = self.starts[st], {0: [(inv[1], inv[0])]}, [], 0
        by_c = {}
        for r in relations:
            by_c.setdefault(r[0], []).append(r)
        while t < SLICES:
            forces = pending.pop(t, [])
            facts = {f"{o}_{g}" for o, g in self.state(tree)}
            gerunds = dict(self.state(tree))
            for doer, strength in forces:
                c = f"{strength}_push:{doer}_{gerunds.get(doer)}"
                for _, conds, target, s, lo, _ in by_c.get(c, ()):
                    if holds(conds, facts) and lo > 0:
                        pending.setdefault(t + lo, []).append((target, s))
            pushes = tuple(sorted({(d, AMOUNTS[s]) for d, s in forces}))
            tree, flips = self.step(tree, pushes)
            if flips:
                trail.append(flips)
            elif not pending:
                break
            t += 1
        return tuple(trail)

    def dynamics(self, relations):
        return {key: self.run(key[0], key[1], relations) for key in self.real}


def involved(node, key, trail):
    st, inv = key
    base, *tags = node.split("|")
    facts = {f"{o}_{g}" for o, g in st}
    if "_push:" in base:
        if push_id(inv) != base:
            return False
        for tag in tags:
            t, want = tag.split("=")
            if (t in facts) != (want == "True"):
                return False
        return True
    return any(base in s for s in trail)


def reduced_pair(node, relations, fw, reverse=False):
    """The fewest of the mind's relations that leave what happens to this node unchanged."""
    full = fw.dynamics(relations)
    scope = [k for k, trail in full.items() if involved(node, k, trail)]
    kept = sorted(relations, key=str, reverse=reverse)
    for r in list(kept):
        trial = [x for x in kept if x != r]
        if all(fw.run(k[0], k[1], trial) == full[k] for k in scope):
            kept = trial
    return kept


def known_nodes(agent):
    """If a node isn't unknown, it's known: any funding of its own. A push the mind split is two nodes."""
    und, meta, out = agent.mind.understanding, agent.mind.meta, set()
    for c, rels in und.rel.items():
        if c.startswith(("not:", "[", "sov:", "q:", "similar:")) or "|" in c:
            continue
        if not any(sum(e) > 0 for k, e in rels.items() if k[0] != "similar_to"):
            continue
        if c in meta.splits:
            out |= {c + "".join(f"|{t}={w}" for t, w in conds) for _, conds in readings_of(meta, c)}
        else:
            out.add(c)
    return out


def objects_in(node, relations):
    base = node.split("|")[0]
    own = base.split(":", 1)[1] if ":" in base else base
    out = {obj_of(own)}
    for c, conds, target, *_ in relations:
        out |= {obj_of(c.split(":", 1)[1]), target} | {obj_of(t) for t, _ in conds}
    return out


def carry_concept(s, phi):
    prefix, rest = s.split(":", 1) if ":" in s else (None, s)
    obj, gerund = rest.rsplit("_", 1)
    mapped = f"{phi.get(obj, '?' + obj)}_{gerund}"
    return f"{prefix}:{mapped}" if prefix else mapped


def carry(r, phi):
    c, conds, target, s, lo, hi = r
    return (carry_concept(c, phi), tuple(sorted((carry_concept(t, phi), w) for t, w in conds)), phi.get(target, "?" + target), s, lo, hi)


def score(a, b, oa, ob):
    """Relations shared under the best mapping of objects, both ways: (score, mapping)."""
    if not a or not b:
        return 0.0, None
    oa, ob = sorted(oa), sorted(ob)
    maps = (dict(zip(oa, p)) for p in permutations(ob, len(oa))) if len(oa) <= len(ob) else (dict(zip(p, ob)) for p in permutations(oa, len(ob)))
    best = (0.0, None)
    for phi in maps:
        carried = {carry(r, phi) for r in a}
        s = 2 * len(carried & set(b)) / (len(a) + len(b))
        if s > best[0]:
            best = (s, phi)
    return best
