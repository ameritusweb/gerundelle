"""(SOV, world) pairs and the aha on the Warp board (LADDER.md, rung 3). After ../structuralsimilarity/forward.py and aha.py; Gerundelle is unchanged.

A relation is read from the mind's own trials: in this reading, a move by A puts a force on B (B's reading becomes X) within this range of slices.
It's kept only if every trial in that reading shows it; otherwise it's still conflated and specifies nothing. A known node's pair is the relations
that specify it: for a move, what it does; for a reading, the moves that bring it about. The board is the pair's world.

Differences from the force rooms, my choices where the theory doesn't settle them:
- The force a relation carries is the reading it leaves on its target (`captured`, `hanging`, `pressing`...): Warp moves have no light or hard pushes.
- There's no physics to run between moves here, so no relation is implied by the others: a node's pair is all the relations that specify it.
- A structure is compared without its move's name: a move is carried as the piece that makes it. "A move of the king puts a force on the knight" is
  the structure; which square it goes to is the move's name, as the room's square names are the pieces'.
- Every object is named with its room, so two rooms' structures never share a node (analogize compares only structures sharing none).
- Pairs are re-read every UPDATE slices, not every slice, and compared only against the earlier room's (sealed) pairs.
"""
import collections
import sys
from pathlib import Path

import rung0  # noqa: E402,F401  (this domain's: puts Gerundelle on the path)
sys.path.append(str(Path(__file__).resolve().parent.parent / "structuralsimilarity"))   # after this domain, whose rung0 shares a name
from forward import holds, known_nodes, push_id, readings_of  # noqa: E402
from molecules import Params, clause  # noqa: E402
from offers import RemembersOffers  # noqa: E402
from potential import ForceMind, feel  # noqa: E402
from sov_agent import SovAgent  # noqa: E402

CHANNELS = ("_bearing", "_exerting", "_unique")
UPDATE = 20


def obj_of(fact):
    return fact.rsplit("_", 1)[0]


def entity(obj):
    """The piece (or file, or the material count) an object is a reading of."""
    for ch in CHANNELS:
        if obj.endswith(ch):
            return obj[: -len(ch)], ch
    return obj, ""


class PairMind(RemembersOffers, SovAgent):
    """The main mind of rung 1f (potential forces, offer memory, winner_acts), keeping the slice each effect arrived at, and its pairs."""

    def __init__(self, world, room, mind=None, budget=500, sealed=None, aha=True):
        super().__init__(world, mind or ForceMind(Params(inquiry=True, phases=True, winner_acts=True)))
        self.room, self.budget, self.sealed, self.aha_on = room, budget, dict(sealed or {}), aha
        self.timed, self.pairs, self.ahas = [], {}, {}

    def watch(self, diffs, rec):
        inv, facts, k, effects = self.watching
        done = k + 1 >= self.world.horizon
        super().watch(diffs, rec)
        if done:
            self.timed.append((inv, facts, dict(effects)))

    def plan_step(self, invs, budget=60, horizon=3):
        return super().plan_step(invs, self.budget, horizon)

    def tick(self, force=None):
        feel(self, self.world)
        out = super().tick(force)
        rec = out[1]
        for level, lv in enumerate(rec["levels"]):
            for i in lv["winners"]:
                if i in self.ahas:
                    x = self.ahas[i]
                    x["reach"] = max(x["reach"], level)
                    if level == len(rec["levels"]) - 1:
                        x["top"] += 1
        if self.mind.t % UPDATE == 0:
            self.update()
        return out

    def q(self, name):
        return f"{self.room}:{name}"

    def relations(self):
        """(move, its reading's conditions, target object, the reading it leaves, first slice, last slice), room-named."""
        meta, objects = self.mind.meta, set(self.world.objs)
        by_push = collections.defaultdict(list)
        for inv, facts, effects in self.timed:
            by_push[inv].append((facts, effects))
        out = set()
        for inv, rows in by_push.items():
            for _, conds in readings_of(meta, push_id(inv)):
                trials = [r for r in rows if holds(conds, r[0])]
                if not trials:
                    continue
                for target in objects:
                    got = []
                    for _, effects in trials:
                        hit = sorted((t, e) for e, t in effects.items() if obj_of(e) == target)
                        got.append(hit[0] if hit else None)
                    if None in got or len({e for _, e in got}) > 1:   # only sometimes, or not the same: still conflated
                        continue
                    reading = got[0][1].rsplit("_", 1)[1]
                    ticks = [t for t, _ in got]
                    out.add((push_id(inv), tuple((self.q(t), w) for t, w in conds), self.q(target), reading, min(ticks), max(ticks)))
        return out

    def pairs_now(self):
        rels = self.relations()
        by_move = collections.defaultdict(list)
        by_fact = collections.defaultdict(list)
        for r in rels:
            by_move[r[0]].append(r)
            by_fact[f"{r[2]}_{r[3]}"].append(r)
        out = {}
        for n in known_nodes(self):
            base, *tags = n.split("|")
            if "_push:" in base:
                want = {(self.q(t.split("=")[0]), t.split("=")[1] == "True") for t in tags}
                rs = [r for r in by_move.get(base, []) if want <= set(r[1])]
                mover = base.split("_push:")[1].rsplit("_", 1)[0]
                if rs and mover in self.world.where:
                    out[self.q(n)] = rs
            elif self.q(base) in by_fact and obj_of(base) in self.world.objs:
                out[self.q(n)] = by_fact[self.q(base)]
        return out

    def update(self):
        new = self.pairs_now()
        changed = {n for n, p in new.items() if self.pairs.get(n) != p}
        self.pairs = new
        if not self.aha_on:
            return
        for a in sorted(changed):
            for b, rb in self.sealed.items():
                s, phi = score(new[a], rb)
                if s > 0:
                    self.relate(a, b, s, phi, new[a], rb)

    def relate(self, a, b, s, phi, ra, rb):
        """The score is a relation in the SOV; its first writing triggers the thought (aha.py)."""
        und = self.mind.understanding
        for p, q in ((a, b), (b, a)):
            und.rel.setdefault(p, {})[("similar_to", q)] = [0.0, 0.0, s]
        mid = f"similar:{min(a, b)}~{max(a, b)}"
        capture = any(r[3] == "captured" for r in ra) and any(r[3] == "captured" for r in rb)
        if mid in self.ahas:
            x = self.ahas[mid]
            x.update(score=s, phi=phi)
            if capture and not x["capture"]:   # the structure came to hold a capture after its first writing
                x.update(capture=True, capture_t=self.mind.t, capture_score=s)
            return
        ents = {entity_of_rel(r) for r in ra} | {entity(r[2])[0] for r in ra}
        self.ahas[mid] = dict(t=self.mind.t, a=a, b=b, score=s, first_score=s, phi=phi, entities=len(ents), reach=-1, top=0,
                              capture=capture, capture_t=self.mind.t if capture else None, capture_score=s if capture else None)
        self.mind.present(clause(mid, tags=("similarity",)), act=s)


def entity_of_rel(r):
    """The piece whose move a relation is about, room-named."""
    room = r[2].split(":", 1)[0]
    return f"{room}:{r[0].split('_push:')[1].rsplit('_', 1)[0]}"


def parts(r, phi):
    """A relation carried under a mapping of entities, as its parts (the user's choice, 2026-11-06): its core, a move by the piece that makes it
    leaving this reading on its target within these slices, and each condition it holds under, tied to that core. A split relation and an unsplit
    one then share their core and differ in their conditions."""
    def m(obj):
        e, ch = entity(obj)
        return phi.get(e, "?" + e) + ch
    core = (phi.get(entity_of_rel(r), "?" + entity_of_rel(r)), m(r[2]), r[3], r[4], r[5])
    return {core} | {("when", core, m(obj_of(t)) + "_" + t.rsplit("_", 1)[1], w) for t, w in r[1]}


def bare_parts(r):
    """A relation's parts with every name dropped: what any mapping must keep."""
    core = (entity(r[2])[1], r[3], r[4], r[5])
    return [core] + [("when", core, entity(obj_of(t))[1], t.rsplit("_", 1)[1], w) for t, w in r[1]]


def all_parts(rs, phi):
    return set().union(*(parts(r, phi) for r in rs))


def score(a, b, limit=4000):
    """Parts shared under the best one-to-one mapping of a's entities onto b's, both ways: (score, mapping)."""
    if not a or not b:
        return 0.0, None
    ca = collections.Counter(x for r in a for x in bare_parts(r))
    cb = collections.Counter(x for r in b for x in bare_parts(r))
    bound = sum((ca & cb).values())
    if bound == 0:
        return 0.0, None
    ents_a = sorted({entity_of_rel(r) for r in a} | {entity(r[2])[0] for r in a} | {entity(obj_of(t))[0] for r in a for t, _ in r[1]})
    ents_b = sorted({entity_of_rel(r) for r in b} | {entity(r[2])[0] for r in b} | {entity(obj_of(t))[0] for r in b for t, _ in r[1]})
    ident = {e: e for e in ents_b}
    target = all_parts(b, ident)
    n = sum(ca.values()) + sum(cb.values())
    best, seen = (0.0, None), [0]

    def roles(rs, e):
        out = {bare_parts(r)[0] for r in rs if entity(r[2])[0] == e} | {("moves",) for r in rs if entity_of_rel(r) == e}
        return out | {("cond", entity(obj_of(t))[1], t.rsplit("_", 1)[1], w) for r in rs for t, w in r[1] if entity(obj_of(t))[0] == e}
    cand = {e: [x for x in ents_b if roles(a, e) & roles(b, x)] or [None] for e in ents_a}
    order = sorted(ents_a, key=lambda e: len(cand[e]))

    def go(i, phi, used):
        nonlocal best
        if seen[0] >= limit:
            return
        if i == len(order):
            seen[0] += 1
            s = 2 * len(all_parts(a, phi) & target) / n
            if s > best[0]:
                best = (s, dict(phi))
            return
        e = order[i]
        for x in cand[e]:
            if x is not None and x in used:
                continue
            if x is not None:
                phi[e] = x
            go(i + 1, phi, used | ({x} if x else set()))
            phi.pop(e, None)
            if best[0] >= 2 * bound / n:
                return
    go(0, {}, set())
    return best
