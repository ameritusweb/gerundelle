"""The hand reaches for the full mug and grasps it: reaching by bond strengthening, grasping by constraint search.

    python -X utf8 body/grasp.py

Reaching (EMBODIED_COGNITION.md): the want to hold the mug is a molecule; the hand's moves are molecules that
bind to it. A move is tried; if the regions between hand and goal thinned, the outcome is good, if they
thickened, bad (Mind.learn: the Dirichlet record of the move with the want). The move that strengthens the
bond keeps winning; one that stops working loses to the others. No distance is measured by the mind, only
the count of coarse regions between, as the world reports it.

Grasping (CONSTRAINT_DISCOVERY.md): the hand's repertoire for a mug is small (a side to come from, a part
to take, a grip). Each failure reveals a constraint anchored on where it happened (what was touched, what
was knocked, on which side). A constraint is a molecule with a standing site; an attempt fills it if it
does not involve that anchor. The next attempt is the untried one most supported by the constraints found
(Mind.support, candidates: simultaneous binding). Success is noticed where they converge. A second episode
starts with the constraints the first found.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "gerundelle", "molecules"))
from world import HandWorld, DIRS, SIDES, PARTS, GRIPS, CELL, STEP, HOME  # noqa: E402
from perceive import scale_of  # noqa: E402
from molecules import Mind, Params, clause  # noqa: E402  (the copy in embodied/gerundelle)


# ---- reaching -----------------------------------------------------------------------------------------

AXIS = {"left": (0, -1), "right": (0, 1), "down": (1, -1), "up": (1, 1), "forward": (2, -1), "back": (2, 1)}


def invitations(world, goal):
    """The moves, as the hand sees them: each with how it lies to the wanted thing, seen as a direction
    (toward it, away from it; away too along a line already level with it). An invitation's identity includes
    the configuration that invites it (force_world.py: a standing prop and a resting prop invite different
    pushes); first the bare direction, and "left", good while the mug lay to the left, went on being tried
    past it and was undone only slowly by its record."""
    out = []
    gap = goal - world.hand
    span = np.abs(gap).sum() or 1.0
    for d, (ax, sgn) in AXIS.items():
        off = gap[ax]
        rel = "toward" if off * sgn > 0.5 * world_step() else "away"
        # how strongly it invites: a move toward the thing, by how much of the way lies along it (an invitation
        # has a strength, as a push has its amount in the force world); first all alike, and the hand, level with
        # the mug one way, rocked there on its good record and never tried the way still open
        act = 0.5 + 0.5 * abs(off) / span if rel == "toward" else 0.5
        out.append((clause(f"move:{rel}:{d}", tags=("move", rel), sites=("goal",)), act))
    return out


def world_step():
    from world import STEP
    return STEP


def reach(world, goal, max_steps=90):
    """The hand reaches toward goal by trial and the tournament's feedback. Returns (arrived, steps, event)."""
    mind = Mind(Params(sov=False, meta=False, closure=False))
    want = clause("want:hold", tags=("goal", "want"))
    before = world.between(goal)
    for step in range(max_steps):
        if before * CELL <= 0.75 * STEP:   # there: within a step of it (first only at no regions between at all,
            return True, step, None        # which 2 cm steps never land on, and the hand bobbed up and down there)
        invited = invitations(world, goal)
        moves = [m for m, _ in invited]
        offered = {m.id for m in moves}
        for i in [i for i in mind.pool if i.startswith("move:")]:
            if i in offered:   # still invited: perceived again, its site open again (first kept as it was, and
                mind.pool[i].sites = ("goal",)   # the want filled it on the first tick, no move bound to it after;
            else:              # then taken out and presented anew, and Gerundelle's re-entry boost kept the
                mind.remove(i)   # first winners winning); no longer invited: gone. Records persist
        for m, act in invited:   # each invitation at its strength (re-presented: present keeps the higher)
            if m.id in mind.pool:
                mind.pool[m.id].act = act
            else:
                mind.present(m, act)
        rec = mind.tick([want])
        # the move made is the one the want binds to: its pull flows through that bond (the argmax of the want's
        # force: the learned record with the move, novelty for an untried one, the fit). First the best-bidding
        # of the top winners; before that the first of them, broken by name: "back", every time
        b = rec["levels"][0]["res"].get("want:hold", ("none",))
        bids = rec["levels"][0]["bids"]
        chosen = b[1] if b[0] == "partner" and b[1].startswith("move:") else max(
            (i for i in bids if i.startswith("move:")), key=lambda i: (round(bids[i], 9), i))
        d = chosen.split(":")[-1]
        ev = world.move(d)
        if ev:
            return False, step + 1, ev
        now = world.between(goal)
        outcome = 1 if now < before else -1 if now > before else 0
        # the bond strengthened, or weakened: credited to the move that was made, bound to the want (first every
        # winning move bound to the want shared the outcome, the moves not made with the one made, and none
        # learned)
        made = dict(rec, pairs=[(L, p) for L, p in rec["pairs"] if chosen in p])
        mind.learn(made, outcome)
        before = now
    return False, max_steps, None


# ---- grasping: the constraints and the attempts --------------------------------------------------------

def involves(attempt, anchor, percept=None):
    """Whether an attempt (side, part, grip) involves what a constraint is anchored on: the mind's reading of
    its own action, which parts its hand would touch and which way it would come.

    Fixed anchors (first): a side as the body saw it then: "knocked-from-left", "handle-from-near",
    "chip-from-near". They hold for that mug where it stood, and say nothing about one turned another way.
    Relational anchors: what was perceived to do it, read again in each scene (body/perceive.py):
      in-the-way       reaching to a side with something lying between the hand and there (the field's
                       regions between; first "neighbour": something standing close on that side, and the
                       hand, sent to the far side, knocked a bottle standing on the right four times running)
      handle-edge-on   taking the handle from a side it does not face
      rim-mark         taking the rim on the side where its distinctive mark is
    and, as before, body, rim, handle-pinch, which are relational already."""
    side, part, grip = attempt
    if anchor == "body":
        return part == "body" or grip == "wrap"
    if anchor == "rim":
        return part == "rim"
    if anchor == "handle-pinch":
        return part == "handle" and grip == "pinch"
    if anchor == "in-the-way":
        return percept.in_the_way(HOME, percept.approach(side))
    if anchor == "handle-edge-on":
        return part == "handle" and percept.handle_side is not None and side != percept.handle_side
    if anchor == "rim-mark":
        return part == "rim" and side == percept.mark_side
    if anchor.startswith("chip-from-"):
        return part == "rim" and side == anchor[len("chip-from-"):]
    if anchor.startswith("handle-from-"):
        return part == "handle" and side == anchor[len("handle-from-"):]
    if anchor.startswith("knocked-from-"):
        return side == anchor[len("knocked-from-"):]
    return False


def taken(world):
    """The path the hand took on its way (the reach's steps), for what lay in its way."""
    return [p["at"] for p in world.path if p.get("gerund") == "extending"]


def attempt_id(a):
    return "attempt:" + ":".join(a)


def choose(constraints, tried, percept=None, order=None):
    """The untried attempt the constraints found so far support most: candidate attempts and constraint
    molecules in the tournament, support by simultaneous binding. None left: None."""
    options = [(s, p, g) for s in SIDES for p in PARTS for g in GRIPS if (s, p, g) not in tried]
    if not options:
        return None, {}
    mind = Mind(Params(support="candidates", sov=False, meta=False, closure=False))
    mols = [clause(attempt_id(a), tags=("attempt",) + tuple(
        f"clears:{c}" for c in constraints if not involves(a, c, percept))) for a in options]
    mols += [clause(f"constraint:{c}", tags=("constraint",), sites=(f"clears:{c}",)) for c in constraints]
    rec = mind.tick(mols)
    bids = rec["levels"][0]["bids"]
    # ties between equally supported attempts break by `order` (a rank per attempt: a style, for now arbitrary;
    # first by name only, and one order's luck was taken for a result)
    rank = order or {}
    best = max(options, key=lambda a: (round(bids.get(attempt_id(a), 0.0), 9), -rank.get(a, 0),
                                       [-ord(ch) for ch in attempt_id(a)]))
    support = {a: sum(not involves(a, c, percept) for c in constraints) for a in options}
    return best, support


def anchor_of(event, side, part, at, percept, relational):
    """What the mind takes a failure's constraint to be anchored on: what it perceived doing it."""
    if event.endswith("knocked tipping"):
        return "in-the-way" if relational else f"knocked-from-{side}"
    if event == "burning":
        return "body"
    if event == "spilling":
        return "rim"
    if event == "slipping":
        return "handle-pinch"
    if event == "edge-on":
        return "handle-edge-on" if relational else f"handle-from-{side}"
    if event == "cutting":   # the cut, where a distinctive mark lay under the fingers (the octree's chip mark)
        if relational:
            return "rim-mark" if percept.mark_under(at) else "rim"
        return f"chip-from-{side}"
    return None


def episode(world, constraints, label, percept=None, relational=False, max_attempts=36, save=True, quiet=False,
            order=None):
    tried, log = set(), []
    for n in range(1, max_attempts + 1):
        a, support = choose(constraints, tried, percept, order)
        if a is None:
            break
        tried.add(a)
        side, part, grip = a
        world.reset()
        arrived, steps, ev = reach(world, world.approach_point(side))
        at = world.hand.copy()
        if ev:   # knocked something on the way
            event = f"{ev.split(':', 1)[1]} knocked tipping"
        elif not arrived:
            event = "never got there"
        else:
            event, _ = world.grasp(side, part, grip)
            at = world.side_point(side, part)
        locus = None if event in ("held", "never got there") else anchor_of(event, side, part, at, percept, relational)
        new = locus is not None and locus not in constraints
        if new:
            constraints.append(locus)
        log.append(dict(n=n, attempt=a, steps=steps, event=event, locus=locus, new=new))
        if save:
            world.save_path(f"hand_{label}_{n:02d}")
        if not quiet:
            print(f"  {n:2}. {side:5} {part:6} {grip:5}  reach {steps:2} steps  ->  {event:28}"
                  + (f"  constraint found: {locus}" if new else ("  (known)" if locus else "")))
        if event == "held":
            break
    return log


TASKS = {200: "mug_b", 201: "mug_b", 202: "mug_c", 203: "mug_a", 204: "mug_d", 205: "mug_e"}


def task(layout, seed=7):
    from perceive import Percept
    world = HandWorld(f"seed{seed}_layout{layout}", TASKS[layout])
    return world, Percept(f"seed{seed}_layout{layout}", world.target.center)


# ---- constraints from perception (the user, 2026-10-28: from what the mind perceives, not hand-written rules) ----

def perceived(percept, attempt, event, at):
    """An attempt as the mind perceived it: what its fingers met (the octree's cells there), whether something
    lay in the way, how it came to what the mug shows, its grip. A reach stopped by a knock touched nothing."""
    side, part, grip = attempt
    tags = percept.way_tags(side) | percept.came_tags(side) | {f"grip:{grip}"}
    if not event.endswith("knocked tipping"):
        tags |= percept.touch_tags(at, grip)
    return frozenset(tags)


def distinguishing(tags, others):
    """The smallest combination of `tags` that no other attempt carried in full, releasing first the tags most
    common among the others; None if some other attempt carried all of them."""
    s = set(tags)
    if any(s <= o for o in others):
        return None
    common = {tag: sum(tag in o for o in others) for tag in s}
    for tag in sorted(s, key=lambda x: (-common[x], x)):   # (tried: the grip released first: worse, see mint)
        if len(s) > 1 and not any((s - {tag}) <= o for o in others):
            s.discard(tag)
    return frozenset(s)


def constraints_from(history):
    """Each kind of failure's constraints: what is distinctive of its failures among the attempts. Each failure
    is given its smallest combination of tags that no other attempt carried in full (a profile compressed:
    the tags most common elsewhere let go first); two are merged into what they share while that still tells
    them apart from every other attempt. A kind of failure can so carry more than one constraint: one label,
    two situations (the meta layer's conflation, split). First one combination per kind, the intersection of
    all its failures, and the burn (a hand wrapped round the handle; a hand on the body) had none that held.
    Before that tag by tag, and the burn was left as "the way is clear"."""
    out = {}
    for e in {ev for _, ev in history if ev not in ("held", "never got there")}:
        others = [t for t, ev in history if ev != e]
        conj = []
        for t in [t for t, ev in history if ev == e]:
            d = distinguishing(t, others)
            if d is not None and d not in conj:
                conj.append(d)
        merged = True
        while merged and len(conj) > 1:   # generalize: two that share a combination still telling them apart
            merged = False
            for i in range(len(conj)):
                for j in range(i + 1, len(conj)):
                    d = distinguishing(conj[i] & conj[j], others) if conj[i] & conj[j] else None
                    if d is not None:
                        conj = [c for k, c in enumerate(conj) if k not in (i, j)] + [d]
                        merged = True
                        break
                if merged:
                    break
        if conj:
            out[e] = conj
    return out


def choose_perceived(cons, tried, percept, order):
    options = [(s, p, g) for s in SIDES for p in PARTS for g in GRIPS if (s, p, g) not in tried]
    if not options:
        return None
    pred = {a: percept.predict(a) for a in options}
    mind = Mind(Params(support="candidates", sov=False, meta=False, closure=False))
    mols = [clause(attempt_id(a), tags=("attempt",) + tuple(
        f"clears:{e}" for e, hs in cons.items() if not any(h <= pred[a] for h in hs))) for a in options]
    mols += [clause(f"constraint:{e}", tags=("constraint",), sites=(f"clears:{e}",)) for e in cons]
    bids = mind.tick(mols)["levels"][0]["bids"]
    rank = order or {}
    return max(options, key=lambda a: (round(bids.get(attempt_id(a), 0.0), 9), -rank.get(a, 0),
                                       [-ord(ch) for ch in attempt_id(a)]))


def episode_perceived(world, percept, history, label, order=None, max_attempts=36, quiet=True, save=False):
    tried, n = set(), 0
    for n in range(1, max_attempts + 1):
        cons = constraints_from(history)
        a = choose_perceived(cons, tried, percept, order)
        if a is None:
            break
        tried.add(a)
        side, part, grip = a
        world.reset()
        arrived, steps, ev = reach(world, world.approach_point(side))
        at = world.hand.copy()
        if ev:
            event = f"{ev.split(':', 1)[1]} knocked tipping".replace(ev.split(':', 1)[1], "a thing")
        elif not arrived:
            event = "never got there"
        else:
            event, _ = world.grasp(side, part, grip)
            at = world.side_point(side, part)
        history.append((perceived(percept, a, event, at), event))
        if save:
            world.save_path(f"hand_{label}_{n:02d}")
        if not quiet:
            now = constraints_from(history)
            print(f"  {n:2}. {side:5} {part:6} {grip:5}  ->  {event:24}"
                  + (f"  its constraints so far: {' | '.join(' '.join(sorted(h)) for h in now[event])}"
                     if event in now else ""))
        if event == "held":
            break
    return n


# ---- tags minted by perception itself (the user, 2026-10-28: perception chooses its own tags) ----------------

class Vocabulary:
    """The mind's own tags, minted from raw perception when it needs them: each a quantity and a cut-off
    ("out_from_axis_max > 1.31": the fingers met cells standing out beyond 1.31 of the body's radius). It starts
    with none; the grip is the body's own action, known, not a perception."""

    def __init__(self, mode="margin"):
        self.cuts = []
        self.mode = mode   # how a cut is chosen: "margin" (the default), "nearmiss", or "probe" (deliberate near
                           # misses: the cut is minted against the probe made for the failure)
        self.probe_of = {}   # history index of a probe -> history index of the failure it was made for

    def tags(self, raw, grip):
        """Each minted cut tags the side it was minted for. (Tried: one cut, both sides tagged on every attempt,
        to end the "idle" opposite cuts: worse, 3.88 attempts across held-out mugs against 2.27. The opposite side
        is minted only when a failure needs it; tagging it always gave the constraints coincidences to compress
        onto, "not much in the way" among them.)"""
        out = {f"grip:{grip}"}
        for f, op, th in self.cuts:
            v = raw.get(f, np.nan)
            if not np.isnan(v) and ((v > th) if op == ">" else (v < th)):
                out.add(f"{f}{op}{th:.3g}")
        return frozenset(out)

    def mint(self, history):
        """Escalation on collision: while some failure cannot be told apart from an attempt that did not fail
        that way (all its tags carried by the other too), find in raw perception the one quantity and cut-off
        that separates it (margin_cut or nearmiss_cut), and mint it. Resolution only where two collide."""
        for _ in range(40):
            tagged = [(self.tags(r, g), ev) for r, g, ev in history]
            hit = None
            for i, (t, ev) in enumerate(tagged):
                if ev in ("held", "never got there"):
                    continue
                # colliding in every tag, the grip included. (Tried: colliding in what was perceived alone, the grip
                # set aside, so a perceived cut is minted for every failure: worse, 7.0 and 8.4 attempts to transfer.
                # In this world a wrap burns wherever it grips: the grip is part of the cause, and forced to find a
                # perceived one the mind minted a coincidence, "a highly distinctive cell under the fingers")
                coll = [j for j, (tt, e2) in enumerate(tagged) if e2 != ev and t <= tt]
                if coll:
                    hit = (i, coll)
                    break
            if hit is None:
                return
            i, coll = hit
            ri, ev = history[i][0], history[i][2]
            if self.mode == "margin":
                best = self.margin_cut(history, ri, ev, coll)
            elif self.mode == "nearmiss":
                best = self.nearmiss_cut(history, ri, coll)
            else:   # probe: the near miss made for this failure narrows the cause to the quantities that changed
                # between them; the widest margin over every attempt chooses among those (first the near miss
                # alone, the quantity that changed most: one change of side moves several quantities together,
                # and "came straight at a mark" was minted for a knock)
                made = [j for j, f in self.probe_of.items() if f == i and j in coll]
                best = None
                if made:
                    rj = history[made[0]][0]
                    moved = {f for f, vi in ri.items() if not np.isnan(vi) and not np.isnan(rj.get(f, np.nan))
                             and abs(vi - rj[f]) > 1e-9}
                    moved |= {f for f, vi in ri.items() if not np.isnan(vi) and np.isnan(rj.get(f, np.nan))}
                    best = self.margin_cut(history, {f: v for f, v in ri.items() if f in moved}, ev, coll)
                if best is None:
                    best = self.margin_cut(history, ri, ev, coll)
            if best is None or best[0][0] == 0 or best[1] in self.cuts:
                return
            self.cuts.append(best[1])


    @staticmethod
    def margin_cut(history, ri, ev, coll):
        """The cut separating the failure from the most of those it collides with, keeping the most failures of its
        kind with it, with the widest margin for that quantity (first the narrowest: the cut between the two
        closest values, and coincidences were minted: "came straight at a mark" for a knock). The margin is
        measured on the quantity's own scale, what that measurement can range over (perceive.SCALE), not the
        spread a few attempts happened to show (first that spread: every mug learned on had straight diner walls,
        their cells faced out between 0.98 and 1.0, and a cut at 0.985 looked wide; the flared blue mug fell
        under it, and the hand burned on it again and again)."""
        same = [r for r, g, e in history if e == ev]
        best = None
        for f, vi in ri.items():
            if np.isnan(vi):
                continue
            vals = np.array([v for v in (r.get(f, np.nan) for r, g, e in history) if not np.isnan(v)])
            span = scale_of(f)
            if len(vals) < 2 or vals.max() == vals.min():
                continue
            u = np.unique(vals)
            for th in (u[:-1] + u[1:]) / 2:
                for op in (">", "<"):
                    def holds(r, f=f, op=op, th=th):
                        v = r.get(f, np.nan)
                        return (not np.isnan(v)) and ((v > th) if op == ">" else (v < th))
                    if not holds(ri):
                        continue
                    margin = float(np.abs(vals - th).min()) / span
                    score = (sum(not holds(history[k][0]) for k in coll), sum(holds(r) for r in same), margin)
                    if best is None or score > best[0]:
                        best = (score, (f, op, round(float(th), 3)))
        return best

    @staticmethod
    def nearmiss_cut(history, ri, coll):
        """The cut separating the failure from its nearest miss: of the attempts it collides with, the one most
        like it in everything perceived (each quantity as a share of how much it varies); the quantity is the one
        on which the two differ most, the cut half way between them. Tried (the user's near miss, Winston's): it
        did worse, 5.0 and 6.7 attempts to transfer against 3.4 and 3.8, because the attempts the mind chooses
        change side, part and grip at once, so the nearest miss is not near, and where it differs most is
        arbitrary. A near miss has to be made: an attempt changing one thing after a failure."""
        feats = sorted({f for r, g, e in history for f in r})
        span = {}
        for f in feats:
            v = np.array([r.get(f, np.nan) for r, g, e in history], dtype=float)
            v = v[~np.isnan(v)]
            span[f] = float(v.max() - v.min()) if len(v) > 1 else 0.0

        def gap(f, x, y):
            vx, vy = x.get(f, np.nan), y.get(f, np.nan)
            if np.isnan(vx) and np.isnan(vy):
                return 0.0
            if np.isnan(vx) or np.isnan(vy) or span[f] <= 0:
                return 1.0 if (np.isnan(vx) != np.isnan(vy)) else 0.0
            return abs(vx - vy) / span[f]
        j = min(coll, key=lambda k: (np.mean([gap(f, ri, history[k][0]) for f in feats]), k))
        rj = history[j][0]
        best = None
        for f in feats:
            vi, vj = ri.get(f, np.nan), rj.get(f, np.nan)
            if np.isnan(vi) or np.isnan(vj) or vi == vj or span[f] <= 0:
                continue
            op, th = (">" if vi > vj else "<"), (vi + vj) / 2

            def holds(r, f=f, op=op, th=th):
                v = r.get(f, np.nan)
                return (not np.isnan(v)) and ((v > th) if op == ">" else (v < th))
            score = (gap(f, ri, rj), sum(not holds(history[k][0]) for k in coll))
            if best is None or score > best[0]:
                best = (score, (f, op, round(float(th), 3)))
        return best


def episode_minted(world, percept, history, vocab, label, order=None, max_attempts=36, quiet=True, save=False):
    tried, n = set(), 0
    for n in range(1, max_attempts + 1):
        vocab.mint(history)
        cons = constraints_from([(vocab.tags(r, g), ev) for r, g, ev in history])
        options = [(s_, p_, g_) for s_ in SIDES for p_ in PARTS for g_ in GRIPS if (s_, p_, g_) not in tried]
        if not options:
            break
        pred = {a: vocab.tags(percept.predict_raw(a), a[2]) for a in options}
        mind = Mind(Params(support="candidates", sov=False, meta=False, closure=False))
        mols = [clause(attempt_id(a), tags=("attempt",) + tuple(
            f"clears:{e}" for e, hs in cons.items() if not any(h <= pred[a] for h in hs))) for a in options]
        for e in cons:   # a constraint weighs by its receipts: the failures it accounts for (1 - 1/2^n: a single
            # coincidence half as much as a cause seen again and again; first all alike, and a coincidence that
            # forbade the answer was never tested)
            mind.present(clause(f"constraint:{e}", tags=("constraint",), sites=(f"clears:{e}",)),
                         1 - 0.5 ** sum(1 for _, _, ev in history if ev == e))
        bids = mind.tick(mols)["levels"][0]["bids"]
        rank = order or {}
        a = max(options, key=lambda a: (round(bids.get(attempt_id(a), 0.0), 9), -rank.get(a, 0),
                                        [-ord(ch) for ch in attempt_id(a)]))
        tried.add(a)
        side, part, grip = a
        world.reset()
        arrived, steps, ev = reach(world, world.approach_point(side))
        if ev:
            event, raw = "a thing knocked tipping", percept.raw(side, None, grip, touched=False, path=taken(world))
        elif not arrived:
            event, raw = "never got there", percept.raw(side, None, grip, touched=False, path=taken(world))
        else:
            event, _ = world.grasp(side, part, grip)
            raw = percept.raw(side, world.side_point(side, part), grip, path=taken(world))
        history.append((raw, grip, event))
        if save:
            world.save_path(f"hand_{label}_{n:02d}")
        if not quiet:
            print(f"  {n:2}. {side:5} {part:6} {grip:5}  ->  {event:24}  tags minted so far: {len(vocab.cuts)}")
        if event == "held":
            break
    return n


def episode_probing(world, percept, history, vocab, label, order=None, max_attempts=36, quiet=True, save=False):
    """Deliberate near misses (the user, 2026-10-28; Gerundelle's Inquiry: change one thing first). After a failure
    the mind did not see coming (the first of its kind, or one its constraints said the attempt would clear), its
    next attempt is a probe: the failed attempt with one thing changed (the side, or the part, or the grip), the one
    of those its constraints support most. A probe that fails the same way says the thing changed was not the
    cause: the next probe changes another thing in the original failure, each at most once. A probe that does not
    fail the same way is a near miss, and the cut is minted against it, on the quantity the one change isolates.
    Otherwise attempts are chosen by support."""
    tried, n, done = set(), 0, []
    probing = None   # (the failed attempt, its history index, its event, the dimensions not yet changed)
    for n in range(1, max_attempts + 1):
        vocab.mint(history)
        cons = constraints_from([(vocab.tags(r, g), ev) for r, g, ev in history])
        options = [(s_, p_, g_) for s_ in SIDES for p_ in PARTS for g_ in GRIPS if (s_, p_, g_) not in tried]
        if not options:
            break
        pred = {a: vocab.tags(percept.predict_raw(a), a[2]) for a in options}
        probe_for = None
        if done:   # (first every probe changed whatever its support favoured, and after a knock from the left the
            # hand changed its grip three times running, knocking each time: a probe failing the same way says the
            # thing changed was not the cause, so the next changes another)
            last, last_ev, foreseen = done[-1]
            if probing is not None and (last_ev != probing[2] or not probing[3]):
                probing = None   # a near miss found (it did not fail that way), or nothing left to change
            if probing is None and last_ev not in ("held", "never got there") and not foreseen:
                probing = (last, len(history) - 1, last_ev, [0, 1, 2])   # change the side, the part, the grip
        if probing is not None:
            orig, at_i, _, dims = probing
            # only variants not already expected to fail some other known way: a probe the mind expects to burn
            # teaches nothing (first any variant, and in a new task every variant left was a wrap it expected to
            # burn, and it burned)
            expected = lambda a: any(any(h <= pred[a] for h in hs) for e, hs in cons.items() if e != probing[2])
            variants = [a for a in options if sum(x != y for x, y in zip(a, orig)) == 1
                        and [x != y for x, y in zip(a, orig)].index(True) in dims and not expected(a)]
            if variants:
                options, probe_for = variants, at_i
            else:
                probing = None
        mind = Mind(Params(support="candidates", sov=False, meta=False, closure=False))
        mols = [clause(attempt_id(a), tags=("attempt",) + tuple(
            f"clears:{e}" for e, hs in cons.items() if not any(h <= pred[a] for h in hs))) for a in options]
        for e in cons:   # a constraint weighs by its receipts: the failures it accounts for (1 - 1/2^n: a single
            # coincidence half as much as a cause seen again and again; first all alike, and a coincidence that
            # forbade the answer was never tested)
            mind.present(clause(f"constraint:{e}", tags=("constraint",), sites=(f"clears:{e}",)),
                         1 - 0.5 ** sum(1 for _, _, ev in history if ev == e))
        bids = mind.tick(mols)["levels"][0]["bids"]
        rank = order or {}
        a = max(options, key=lambda a: (round(bids.get(attempt_id(a), 0.0), 9), -rank.get(a, 0),
                                        [-ord(ch) for ch in attempt_id(a)]))
        tried.add(a)
        side, part, grip = a
        world.reset()
        arrived, steps, ev = reach(world, world.approach_point(side))
        if ev:
            event, raw = "a thing knocked tipping", percept.raw(side, None, grip, touched=False, path=taken(world))
        elif not arrived:
            event, raw = "never got there", percept.raw(side, None, grip, touched=False, path=taken(world))
        else:
            event, _ = world.grasp(side, part, grip)
            raw = percept.raw(side, world.side_point(side, part), grip, path=taken(world))
        # was it foreseen? a failure of a kind already met, whose constraints said this attempt would meet it
        foreseen = event in cons and any(h <= pred[a] for h in cons[event])
        if probe_for is not None:
            vocab.probe_of[len(history)] = probe_for
            changed = [x != y for x, y in zip(a, probing[0])].index(True)
            probing = (probing[0], probing[1], probing[2], [d for d in probing[3] if d != changed])
        history.append((raw, grip, event))
        done.append((a, event, foreseen))
        if save:
            world.save_path(f"hand_{label}_{n:02d}")
        if not quiet:
            print(f"  {n:2}. {side:5} {part:6} {grip:5}  ->  {event:24}" + ("  (a probe)" if probe_for is not None else "")
                  + (f"   minted so far: {len(vocab.cuts)}"))
        if event == "held":
            break
    return n


def orders(n, seed=1):
    """n tie orders: each a random rank over the attempts (stand-ins for n styles)."""
    rng = np.random.default_rng(seed)
    allA = [(s, p, g) for s in SIDES for p in PARTS for g in GRIPS]
    return [dict(zip(allA, rng.permutation(len(allA)))) for _ in range(n)]


if __name__ == "__main__":
    tasks = {L: task(L) for L in (200, 201, 202)}
    runs = 20
    table = {}
    for order in orders(runs):
        for mode, run_ep in (("margin", episode_minted), ("nearmiss", episode_minted), ("probe", episode_probing)):
            history, vocab = [], Vocabulary(mode)
            row = [run_ep(*tasks[200], history, vocab, f"{mode}_learn", order)]
            for L in (201, 202):
                v = Vocabulary(mode)
                v.cuts = list(vocab.cuts)
                row.append(run_ep(*tasks[L], list(history), v, f"{mode}_t{L}", order))
            row.append(len(vocab.cuts))
            table.setdefault(mode, []).append(row)
    print(f"tags minted by perception: attempts to the first hold, over {runs} tie orders (mean, and the worst)")
    print(f"  {'':40} {'learning, task 200':>20} {'the same mug turned':>22} {'another mug':>16}")
    names = {"margin": "the widest margin", "nearmiss": "the nearest miss (among attempts made)",
             "probe": "deliberate near misses (probes)"}
    for mode, rows in table.items():
        a = np.array(rows)
        print(f"  {names[mode]:40} {a[:, 0].mean():12.1f} (max {a[:, 0].max():2}) {a[:, 1].mean():14.1f} "
              f"(max {a[:, 1].max():2}) {a[:, 2].mean():8.1f} (max {a[:, 2].max():2})   tags: {a[:, 3].mean():.1f}")
    print("")
    print("one run with probes, in full (the first tie order):")
    order = orders(1)[0]
    history, vocab = [], Vocabulary("probe")
    print("  learning, task 200:")
    episode_probing(*tasks[200], history, vocab, "probe_learn", order, quiet=False, save=True)
    for L in (201, 202):
        print(f"  task {L}:")
        v = Vocabulary("probe")
        v.cuts = list(vocab.cuts)
        episode_probing(*tasks[L], list(history), v, f"probe_t{L}", order, quiet=False, save=True)
    print("")
    print("  the tags it minted:")
    for f, op, th in vocab.cuts:
        print(f"    {f} {op} {th}")
    print("  the constraints, in its own tags:")
    for e, hs in sorted(constraints_from([(vocab.tags(r, g), ev) for r, g, ev in history]).items()):
        print(f"    {e:24} {'   or   '.join(' '.join(sorted(h)) for h in hs)}")
