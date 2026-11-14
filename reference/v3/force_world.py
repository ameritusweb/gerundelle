"""The physical world for the thought-molecule agent (THOUGHT_MOLECULES.md sec. 5k): the force
simulator of forces/poc.py, with potential forces (NEWTONIAN_WORLD_MODEL.md sec. 14).

A potential force is a configuration that invites a force (the user). Here: a node whose gerund
watches the push channel invites a push, read off the scene's structure, never off names. An
invitation's identity includes the object's current gerund, because the configuration is what
invites (a standing prop and a resting prop invite different pushes). Its magnitude is the work it
would do: the push times the change it produces in the forces of every object it reaches
(gerunds flipped) and in what is invited (invitations opened or closed), over a few slices, later
ones discounted. No positions or distances: displacement is change in force or potential force.

The agent: each invitation it perceives is a question molecule whose pull is its estimated work
times the gap, 1 minus how well that invitation's effect is understood; the one that wins the top
is tried (the agent's push lasts one slice); the diffs are written into its understanding as
intervened effects ("no change" is an effect too), and the observed work replaces the estimate.
"""
import copy
import os
import re
from itertools import combinations
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "forces"))
import poc  # noqa: E402
from molecules import Mind, Params, clause, concept_of  # noqa: E402

AMOUNTS = {"light": 1.0, "hard": 5.0}
NUMERIC = re.compile(r"^(.+_(?:level|pressed))_(-?\d+(?:\.\d+)?)$")   # a gauge's or a sensor's reading


def numbers(facts):
    """The perceived quantities among facts: quantity -> value ('tank_level_4.5' -> tank_level: 4.5)."""
    out = {}
    for x in facts:
        m = NUMERIC.match(x)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out
AGENT = "agent"
GUST = "gust"            # a push from outside the scene, on the world's schedule (a hidden driver)
HIDDEN = (None, AGENT, GUST)
BACKGROUND = "margin"   # how effects are explained away as background (see predict)
PHASE = 0   # the seed: every world built while it is set runs its gusts this many ticks later


class phase:
    """with phase(s): worlds built inside run their gusts s ticks later (a seed: the same world, its
    hidden drivers at other moments against the agent's pushes)."""

    def __init__(self, s):
        self.s = s

    def __enter__(self):
        global PHASE
        self.old, PHASE = PHASE, self.s

    def __exit__(self, *a):
        global PHASE
        PHASE = self.old


def node(objs, kind, doer, *kids):
    return poc.Node(kind, poc.watches_for(kind, objs[doer]) + list(kids), doer)


def walk(n):
    yield n
    for k in poc.doings(n):
        yield from walk(k)


class ForceWorld:
    """A scene of forces the agent can push. `gusts` is a schedule of outside pushes: (period,
    offset, [(object, amount)]), applied for one slice at ticks where tick % period == offset; the
    gust itself is not perceived, only what it does (a common driver). `episode`: the scene is
    set back to its start every this many ticks (a release or a fall cannot be undone otherwise).
    `gauges`: containers whose contents the agent perceives (a display), part of the sensor
    interface; other containers show only their gerund. `sensors`: objects whose pressing (the
    pushes on them from every side, summed in size) the agent perceives, as a fact and, when it
    changes, as an event: a push that is balanced and moves nothing still acted."""

    def __init__(self, scene, objs, horizon=3, gamma=0.7, gusts=(), episode=None, gauges=(),
                 sensors=(), name="world"):
        objs = {**objs, **{w: objs.get(w, poc.Obj(w, 0.0)) for w in (AGENT, GUST)}}   # pushers
        self.start, self.objs, self.horizon, self.gamma = scene, objs, horizon, gamma
        self.gusts, self.episode, self.gauges, self.name = list(gusts), episode, set(gauges), name
        self.phase = PHASE
        self.sensors = set(sensors)   # objects whose pressing the agent perceives (Stage 4: a force can
        # act and be balanced, nothing moving; without a sensor the agent sees only gerunds flip)
        self.t = self.began = 0
        self.reset()

    def reset(self):
        self.tree = copy.deepcopy(self.start)
        self.diffs = []
        self.acted = None

    # ---- reading the configuration ----------------------------------------------------------

    def states(self, tree=None):
        """Each object's current gerund (the agent's push is not part of the scene)."""
        out = {}
        for n in walk(tree or self.tree):
            if n.doer in HIDDEN or n.kind in poc.STUFF:
                continue
            out[n.doer] = n.kind
            if n.kind in poc.CONTAINERS and n.doer in self.gauges:   # contents: its internal load
                out[f"{n.doer}_level"] = f"{poc.contents(n, self.objs):g}"
            if n.doer in self.sensors:
                out[f"{n.doer}_pressed"] = f"{self.pressing(n):g}"
        return out

    def pressing(self, n):
        """How hard a node is pressed: the pushes on it from its kids, summed in size."""
        return sum(abs(poc.outputs(k, self.objs).get("push", 0.0)) for k in poc.doings(n))

    def sense(self, before, after):
        """Sensor events between two slices: a sensed object pressed harder or less."""
        if not self.sensors:
            return []
        p = lambda t: {n.doer: (n.kind, self.pressing(n)) for n in walk(t) if n.doer in self.sensors}
        a, b = p(before), p(after)
        return [f"{o}: {b[o][0]}, pressed ({b[o][1] - a[o][1]:+g}, holds {b[o][1]:g})"
                for o in sorted(b) if o in a and b[o][1] != a[o][1]]

    def invitations(self, tree=None):
        """Open force slots: (strength, object, its gerund) for every node whose gerund watches the
        push channel against a reserve its object actually has (a finite one: a push could cross
        it), read off the structure (first: any push watch, so a support with an infinite tearing
        reserve invited a push it could never answer)."""
        out = []
        for n in walk(tree or self.tree):
            if n.doer in HIDDEN:
                continue
            obj = self.objs[n.doer]
            if any(q == "push" and getattr(obj, r, poc.INF) < poc.INF
                   for q, r, *_ in poc.GERUNDS.get(n.kind, poc.G("")).watches):
                out += [(s, n.doer, n.kind) for s in AMOUNTS]
        return sorted(out)

    # ---- acting -----------------------------------------------------------------------------

    def _apply(self, tree, doer, amount, who=AGENT):
        t = copy.deepcopy(tree)
        for n in walk(t):
            if n.doer == doer:
                n.kids.append(poc.Node("pushing", [], who, amount=amount))
                break
        return t

    @staticmethod
    def _unpush(tree):
        for n in walk(tree):
            n.kids = [k for k in n.kids if k.doer not in (AGENT, GUST)]
        return tree

    def renew(self):
        """At an episode's end, set the scene back (its diffs are not news)."""
        if self.episode and self.t - self.began >= self.episode:
            self.reset()
            self.began = self.t

    def gusting(self, t=None):
        t = self.t if t is None else t
        return [p for period, off, pushes in self.gusts if (t + self.phase) % period == off for p in pushes]

    def act(self, inv=None, hold=False):
        """Apply an invited push for one slice (None: wait) and this tick's gusts, step, and return
        the diffs. At an episode's end the scene is set back (its diffs are not news), unless held:
        the agent is still watching a push (first: a reset cut a chain's watch short, and the cut
        outcomes read as conditions)."""
        if not hold:
            self.renew()
        t = self.tree if inv is None else self._apply(self.tree, inv[1], AMOUNTS[inv[0]])
        for doer, amount in self.gusting():
            t = self._apply(t, doer, amount, GUST)
        sensed = self.sense(self.acted or self.tree, t)   # the pushes on the sensed objects now,
        self.acted = t                                     # against the last slice as it was acted on
        t, ev = poc.step(t, self.objs)
        ev = sensed + ev
        self.tree, self.diffs = self._unpush(t), ev
        self.t += 1
        return ev

    def truth(self, tree=None, horizon=None):
        """What each invited push really does from this configuration, against the same slices
        without it and without gusts: invitation -> {slice: effects}. The designer's answer key,
        computed by the simulator, never shown to the agent."""
        tree, out = tree or self.start, {}
        for inv in self.invitations(tree):
            a, b, got = self._apply(tree, inv[1], AMOUNTS[inv[0]]), copy.deepcopy(tree), {}
            pa, pb = tree, tree
            base = horizon or self.horizon
            # past the horizon, the key runs on while the push still makes a difference, up to four
            # times it, as the agent's watch does (first: a fixed horizon, so a toy's landing after its
            # flight, seen by a watch that ran on, counted against the agent)
            for k in range(4 * base):   # every world (DRIFT.md: the key is the world's truth, whatever
                                        # an agent can watch; first only in worlds with gauges or sensors)
                sa, sb = self.sense(pa, a), self.sense(pb, b)
                pa, pb = a, b
                a, ev_a = poc.step(a, self.objs)
                b, ev_b = poc.step(b, self.objs)
                ev_a, ev_b = sa + ev_a, sb + ev_b
                if k == 0:
                    a = self._unpush(a)
                diff = {effect_id(e) for e in ev_a} - {effect_id(e) for e in ev_b}
                if diff:
                    got[k] = diff
                elif k >= base - 1:
                    break
            out[inv] = got
        return out

    def work(self, inv, tree=None):
        """The work an invited push would do: its amount times the change it makes (gerunds
        flipped, invitations opened or closed) over `horizon` slices, later ones discounted. The
        change is counted against the same slices without the push, so what would have happened
        anyway is not the push's work (first: everything that changed counted, and a push into a
        wall did work because the scene settled meanwhile). Computed in imagination."""
        tree = tree or self.tree
        a, b, total = self._apply(tree, inv[1], AMOUNTS[inv[0]]), copy.deepcopy(tree), 0.0
        for k in range(self.horizon):
            a, ev_a = poc.step(a, self.objs)
            b, ev_b = poc.step(b, self.objs)
            if k == 0:
                a = self._unpush(a)
            flips = set(ev_a) ^ set(ev_b)
            invited = set(self.invitations(a)) ^ set(self.invitations(b))
            total += self.gamma ** k * (len(flips) + len(invited))
        return AMOUNTS[inv[0]] * total


def inv_id(inv):
    return f"{inv[0]}_push:{inv[1]}_{inv[2]}"


def effect_id(event):
    """'prop: standing -> tipping (...)' -> 'prop_tipping'."""
    doer, rest = event.split(": ", 1)
    if " -> " in rest:   # a gerund flipped
        to = rest.split(" -> ")[1].split(" (")[0].split(",")[0]
    else:                # a doing's own work this slice: 'register: filling (+2, holds 5)' ->
        to = rest.split(" (")[0].split(",")[-1].strip()   # 'register_filling_+2' (its size kept)
        delta = rest.split(" (")[1].split(",")[0].split(")")[0] if " (" in rest else ""
        if delta[:1] in "+-" and delta:
            to += f"_{delta}"
    return f"{doer}_{to.replace(' ', '_')}"


class ForceAgent:
    """The thought-molecule agent in a force world. Each tick: perceive (each object's gerund as a
    fact, the last diffs as news), refresh a question molecule per invitation with pull =
    estimated work x gap, think, try the invitation whose question won the top (or wait), and
    write what happened into understanding.

    A push is watched for `world.horizon` slices (the push slice and the ones after it, while the
    agent does not push again): what changes meanwhile is the push's outcome (first: only the push
    slice, so a lamp lit a slice later, or a chain's end, was never the push's). Whatever else
    happens in that window counts too: a gust that coincides is attributed to the push, the trap
    the worlds set.

    Chains: in understanding, the push causes what changed in its own slice; a change in a later
    slice is caused by the change just before it in the same object, or, if that object did not
    change, by the changes of the slice before (first: every change in the window was written as
    the push's, so the understanding of a release was a star, push -> everything, and an analogy
    between two releases could not tell the release from the launch).

    Conditions: when an invitation's tries disagree, the sets of facts an effect turns on (an AND
    within a set, an OR across sets; see conditions()) are written as `conditions`, and the gap is
    then counted among the tries in the same reading (per-reading counts: a press with the cable
    seated and a press with it parted are two questions, each closable).

    Transfer: an untried push is predicted from a tried one in the same configuration (the same
    strength on an object in the same gerund), its effects carried over by a mapping of the objects
    that keeps their gerunds (objects alone in their gerund map to each other; one object left
    over on each side maps by elimination; effects of objects that do not map are dropped).
    `experience`: another agent whose tries this one remembers (a mind carried to a new world).
    Goals (Stage 3): with `goal` set to an effect, each tick the agent plans with its own model
    (plan(): what each push did in the reading, and the states it left) and makes the plan's first
    push; with no plan it explores as before (curiosity).
    `analogy=False`: no transfer; `necessity=False`: no refutation by intervention; `novelty=False`:
    a push is not re-opened by states the agent has since set (the ablations)."""

    def __init__(self, world, mind=None, prior=1.0, experience=None, analogy=True, necessity=True,
                 novelty=True, watch_len=None, extend=None, experiments=True):
        self.world = world
        self.experiments_on = experiments
        # base watch (None: the world's horizon); extend: watches run on while the push's gauged or
        # sensed quantities still change (None: where the world has gauges or sensors, opt-in elsewhere;
        # on everywhere it lengthened watches in worlds without them, and coincidences reshuffled)
        self.watch_len = watch_len
        self.extend = extend if extend is not None else bool(world.gauges or world.sensors)
        self.necessity_on, self.novelty_on = necessity, novelty   # ablation switches
        self.mind = mind or Mind(Params())
        self.prior = prior
        self.analogy = analogy
        self.estimate = {}   # invitation -> last observed work
        self.tried = []      # (tick, invitation, effects)
        self.seen = {}       # invitation -> [(facts at the try, frozenset of effects)]
        self.scenes = {}     # invitation -> [object -> gerund at the try], parallel to seen
        self.edoer = {}      # effect id -> the object that changed
        self.conds = {}      # invitation -> facts its outcome turns on
        self.watching = None  # (invitation, facts, slices watched, effects so far, invitations before, states)
        self.history = []    # per tick: (facts, what arrived)
        self.after = {}      # invitation -> [object -> gerund at the watch's end], parallel to seen
        self.known = set()   # every invitation the agent has perceived
        self.goal = None     # an effect the agent wants (Stage 3); None: curiosity only
        self.first = None    # object -> gerund when first perceived
        self.observed = set()  # (cause, effect) links held as observed only (no push produces the cause)
        self.slices = {}     # invitation -> [effect -> slice in the watch], parallel to seen
        self.rest = 0        # ticks to wait before the next push
        self.last_diffs = []
        self.detail = {}     # invitation -> [(condition, effect, tries covered)]
        self.plan_now = []   # the plan last made, for readouts
        self.bids = {}       # the question molecules' last bids at the top
        self.toggled = set()  # lasting states the agent's own pushes have left (facts)
        self.mind.understanding.kind = lambda c: "act" if "_push:" in c else "change"

        if experience is not None:
            self.seen = {k: list(v) for k, v in experience.seen.items()}
            self.scenes = {k: list(v) for k, v in experience.scenes.items()}
            self.edoer = dict(experience.edoer)
            self.conds = dict(experience.conds)

    # ---- what is understood ---------------------------------------------------------------------

    def conditions(self, inv):
        """What an effect turns on: for an effect that came after some tries and not others, the
        sets of facts (each at most three) that held together at tries it came after and never all
        together at a try it did not; chosen greedily, the set covering the most of those tries
        first, the smaller set on a tie, until every such try is covered. One set is a single
        condition or an AND (two plugs seated); several sets are alternatives, an OR (the register
        spills from level 4 or level 5). First: single facts present at every try with the effect
        and at none without, so no AND and no OR could be read, and the calculator's spill never
        was."""
        obs = [(self.expand(inv, fs), es) for fs, es in self.seen.get(inv, [])]
        out, detail = [], []   # detail: (condition, the effect it is for, tries it covers)
        self.detail[inv] = detail
        # no condition is sought for background: an effect on an object that changes after the agent's
        # other pushes too, unless it is the pushed object's own (first: sought for every effect, and a
        # gust's flag swing, coinciding with a guard state, gave the file's light push a condition)
        restless = self.restless(inv) - {inv[1]}
        for e in sorted(set().union(*(es for _, es in obs))) if obs else ():
            if self.edoer.get(e) in restless:
                continue
            hit = [fs for fs, es in obs if e in es]
            miss = [fs for fs, es in obs if e not in es]
            if not hit or not miss:
                continue
            # a condition on a state the world set (a flag swinging, a bell) needs two tries behind it;
            # one on a state the agent set, or a gauge's threshold, may rest on one (first: any, and
            # one try's incidental facts split the readings into slivers, each too thin to read). The
            # floor applies within the search (first after it, and a gust's flag, alone splitting the
            # one try with both plugs seated, was found first, then dropped, and the AND never sought)
            set_by_me = lambda x: x in self.toggled or "=" in x or NUMERIC.match(x)
            fair = lambda c: all(set_by_me(x) for x in c) or sum(set(c) <= fs for fs in hit) >= 2
            cands = set()
            for fs in hit:
                fl = sorted(fs)
                for k in (1, 2, 3):
                    found = [c for c in combinations(fl, k) if not any(set(c) <= m for m in miss) and fair(c)]
                    if found:
                        cands.update(found)
                        break
            left = list(hit)
            while left and cands:
                best = max(sorted(cands), key=lambda c: (sum(set(c) <= fs for fs in left), -len(c)))
                covered = [fs for fs in left if set(best) <= fs]
                if not covered:
                    break
                if best not in out:
                    out.append(best)
                detail.append((best, e, len(covered)))
                left = [fs for fs in left if fs not in covered]
                cands.discard(best)
        return tuple(sorted(out))

    def polarity(self, f):
        """A condition's polarity, against the scene as the agent first found it: a fact about an
        object holding there enables (the cable seated; the push works as found), and if the condition
        is the object's other state, its first state prevents (the latch seated; the lid would not
        open as found). (relation, fact) or None for a reading that is no object's state (a level
        threshold). First: one relation, conditions, for both, and an analogy matched the latch that
        prevents with the cable that enables."""
        for o, g in (self.first or {}).items():
            if f.startswith(o + "_") and NUMERIC.match(f) is None and "=" not in f:
                gerund = f[len(o) + 1:]
                if gerund == g.replace(" ", "_"):
                    return ("enables", f)
                return ("prevents", f"{o}_{g.replace(' ', '_')}")
        return None

    def owner(self, f):
        return next((o for o in (self.first or {}) if f.startswith(o + "_")), None)

    def reading(self, inv, facts):
        conds = self.conds.get(inv, ())
        if not conds:
            return ()
        facts = self.expand(inv, facts)
        return tuple(set(c) <= facts for c in conds)

    def cuts(self, inv):
        """The values each perceived quantity had at this push's tries: the cut points of its
        threshold facts."""
        out = {}
        for fs, _ in self.seen.get(inv, []):
            for q, v in numbers(fs).items():
                out.setdefault(q, set()).add(v)
        return out

    def expand(self, inv, facts):
        """Facts with threshold facts added: for each perceived quantity and each value it had at a try
        of this push, whether it is at or above it, at or below it ('tank_level>=4'). A condition can
        then be a threshold, which an untried value falls on one side of (first: only exact readings,
        so the calculator's spill was "level 4 or level 6", and a level never tried had no reading)."""
        nums = numbers(facts)
        if not nums:
            return facts
        extra = set()
        for q, vs in self.cuts(inv).items():
            if q in nums:
                v = nums[q]
                for t in vs:
                    if v >= t:
                        extra.add(f"{q}>={t:g}")
                    if v <= t:
                        extra.add(f"{q}<={t:g}")
        return frozenset(facts) | extra

    def outcomes(self, inv, facts=None):
        """The tries of this push in the current reading: [frozenset of effects]."""
        facts = self.facts_now() if facts is None else facts
        r = self.reading(inv, facts)
        return [e for fs, e in self.seen.get(inv, []) if self.reading(inv, fs) == r]

    def gap(self, inv, facts=None):
        """How much of what this force does here is not yet understood: per effect ever seen after
        it (in this reading), the uncertainty of its rate, 4 p (1 - p) / n with p = (k + 1/2) /
        (n + 1) after k of n tries; the gap is the largest. One try leaves it 0.75, two agreeing
        0.28, three 0.15; an effect that comes only sometimes (a coincidence) stays uncertain, but
        less with every try (first: 1 - (tries agreeing with the commonest outcome - the rest) / 2,
        so a push whose effect came with a gust's now and then stayed fully open forever, and the
        agent pushed a flag sixteen times in twenty)."""
        obs = self.outcomes(inv, facts)
        if not obs:
            return 1.0
        n = len(obs)
        worst = 0.0
        for e in set().union(*obs):
            p = (sum(e in o for o in obs) + 0.5) / (n + 1)
            worst = max(worst, 4 * p * (1 - p) / n)
        return min(1.0, worst)

    @staticmethod
    def majority(obs):
        got = frozenset(e for e in set().union(*obs) if 2 * sum(e in o for o in obs) > len(obs))
        return got or frozenset({"no_change"})

    def predict(self, inv, facts=None, tree=None):
        """The effects the agent expects from this push here: those that came after more than half
        its tries in the same reading; untried here, carried over from the same configuration
        elsewhere (transfer); None: nothing to go on."""
        facts = self.facts_now(tree) if facts is None else facts
        obs = self.outcomes(inv, facts)
        if obs:
            got = self.majority(obs)
            # explained away as background: an effect that comes after the agent's other pushes about
            # as often (a gust's, by the watch's length; first, with watches that run on, a gust's
            # flag fell in most of a few tries and was predicted from the lid)
            others = [es for j, o in self.seen.items() if j != inv and j[1] != inv[1] for _, es in o]
            if others and BACKGROUND != "none":
                # explaining away background (a gust's effects reach every push alike). Variants, chosen
                # by their pass rates over seeds (THOUGHT_MOLECULES.md sec. 5q): "margin", this push's
                # rate at least 0.1 over the pooled rate after pushes on other objects; "pooled", a
                # binomial test (under 10%) against that pooled rate; "min", against the lowest rate
                # among the other pushes of 2 tries or more
                groups = [[es for _, es in o] for j, o in self.seen.items() if j[1] != inv[1] and len(o) >= 2]
                pooled = lambda e: sum(e in es for es in others) / len(others)
                lowest = lambda e: min((sum(e in es for es in g) / len(g) for g in groups), default=0.0)
                k = lambda e: sum(e in o for o in obs)
                keep = {"margin": lambda e: k(e) / len(obs) - pooled(e) >= 0.1,
                        "pooled": lambda e: tail(k(e), len(obs), pooled(e)) < 0.1,
                        "min": lambda e: tail(k(e), len(obs), lowest(e)) < 0.1}[BACKGROUND]
                got = frozenset(e for e in got if e == "no_change" or keep(e))
            return got or frozenset({"no_change"})
        if not self.analogy:
            return None
        return self.transfer(inv, self.world.states(tree))

    @staticmethod
    def correspond(src, dst, anchor):
        """A mapping of the objects of one scene onto another's that keeps their gerunds: the pushed
        objects map; an object alone in its gerund on both sides maps; one left over on each side
        maps by elimination. src, dst: object -> gerund."""
        src = {o: g for o, g in src.items() if not o.endswith("_level")}
        dst = {o: g for o, g in dst.items() if not o.endswith("_level")}
        m = {anchor[0]: anchor[1]}
        for g in set(src.values()):
            a = [o for o, h in src.items() if h == g and o not in m]
            b = [o for o, h in dst.items() if h == g and o not in m.values()]
            if len(a) == 1 and len(b) == 1:
                m[a[0]] = b[0]
        a = [o for o in src if o not in m]
        b = [o for o in dst if o not in m.values()]
        if len(a) == 1 and len(b) == 1:
            m[a[0]] = b[0]
        return m

    def transfer(self, inv, states):
        """Predict an untried push from the most-tried push in the same configuration (same strength,
        same gerund of the pushed object), mapping each try's effects through the correspondence of
        its scene with this one."""
        same = [i for i in self.seen if i != inv and i[0] == inv[0] and i[2] == inv[2] and self.scenes.get(i)]
        if not same:
            return None
        # by role: pushes here already tried claim the source whose effects they share in kind (what
        # changed in which gerund, by how much); the untried push takes a source left unclaimed, by
        # elimination (first: the most-tried source, so three keys alike in gerund all mapped to one)
        here = [i for i in same if i[1] in states and self.seen.get(i)]
        sources = [i for i in same if i[1] not in states]
        kind = lambda r: {re.sub(r"_[-+][\d.]+$", "", x) for x in r}   # the change without its size
        sim = lambda a, b: ((len(a & b) + 0.5 * len(kind(a) & kind(b))) / (len(a | b) + 0.5 * len(kind(a) | kind(b)))
                            if a and b else 0.0)
        claimed = set()
        for h in here:   # each claims the source most like it (first: equal roles only, and a gust's
            rh = self.role(h) or frozenset()   # flag or the register's gerund at the moment broke it)
            best = max(sources, key=lambda s: (sim(rh, self.role(s) or frozenset()), s), default=None)
            if best is not None and sim(rh, self.role(best) or frozenset()) > 0:
                claimed.add(best)
        left = [s for s in sources if s not in claimed]
        if here and len(left) == 1:
            src = left[0]
        else:
            src = max(sources or same, key=lambda i: (len(self.seen[i]), i))
        mapped = []
        for (_, es), scene in zip(self.seen[src], self.scenes[src]):
            m = self.correspond(scene, states, (src[1], inv[1]))
            out = set()
            for e in es:
                if e == "no_change":
                    out.add(e)
                    continue
                d = self.edoer.get(e)
                if d in m:
                    out.add(m[d] + e[len(d):])
            mapped.append(frozenset(out))
        return self.majority(mapped)

    def role(self, inv):
        """What a push does to the rest of its scene, in kind: (gerund of the changed object, the
        change) for each effect on another object in most of its tries ('register_containing_+1' ->
        ('containing', 'containing_+1'))."""
        obs = [es for _, es in self.seen.get(inv, [])]
        if not obs:
            return None
        restless = self.restless(inv)
        out = set()
        # every change seen after two of its tries or more, in any reading (first: the majority, and a
        # reset tried mostly at an empty register had no role at all)
        for e in set().union(*obs):
            d = self.edoer.get(e)
            if d and d != inv[1] and d not in restless and (sum(e in o for o in obs) >= 2 or len(obs) == 1):
                out.add(e[len(d) + 1:])   # the change, by kind and size, on what it moves
        return frozenset(out)

    def pull(self, inv):
        """Estimated work x gap. An untried push's work is estimated as its size times the changes a
        push has produced on average so far (`prior` before any): the work it would do, guessed
        from the work pushes do (first: a flat prior of 1, so once one hard push had been seen to
        do work 20, no untried push ever won again)."""
        per = [v / world_amount(i) for i, v in self.estimate.items()]
        # never under the prior: where every push's last try did nothing, the guess was 0 (first: a
        # lever whose two tries disagreed stayed at pull 0, the scene's other pushes all inert)
        guess = world_amount(inv) * max(sum(per) / len(per) if per else self.prior, self.prior)
        if inv not in self.estimate:
            return guess * self.gap(inv)
        if self.novelty_on and self.novel(inv):   # tried, but never with the states it has since set
            return max(self.estimate[inv], guess) * max(self.gap(inv), 0.5)
        g = self.gap(inv)
        if g >= 0.5:   # its tries disagree: worth at least an average push (first: the last try's work
            return max(self.estimate[inv], guess) * g   # only; an inert try after the stone had
        return self.estimate[inv] * g                    # landed left the lever at 0, never retried)

    def novel(self, inv, facts=None):
        """Whether the states the agent itself has set (self.toggled) stand now in a combination no
        try of this push was made under: "would it still do nothing, now that I changed that?"
        (first: a push that did nothing kept a work estimate of 0 and was never tried again, so a
        lid tried once with its latch seated was never tried with the latch off)."""
        facts = self.facts_now() if facts is None else facts
        mine = frozenset(f for f in facts if f in self.toggled)
        if all(frozenset(f for f in fs if f in self.toggled) != mine for fs, _ in self.seen.get(inv, [])):
            return True
        # or a perceived quantity stands at a value no try of this push was made at (the world set it:
        # a tank's level; first, only states the agent set counted, and the regulator's drain was
        # never tried with the tank at the top of its band)
        cuts = self.cuts(inv)
        return any(q in cuts and v not in cuts[q] for q, v in numbers(facts).items())

    def facts_now(self, tree=None):
        return frozenset(f"{d}_{g.replace(' ', '_')}" for d, g in self.world.states(tree).items())

    def restless(self, inv):
        """Objects that change after the agent's pushes on other objects in a quarter of their tries or
        more: things that move on their own, or by others' doing."""
        # counted only from pushes that do not themselves set the object going (first: from all, and a
        # register that key 1 fills counted as moving on its own for key 2, so key 2's spill by level
        # was never read)
        if not hasattr(self, "_chains") or self._chains[0] != len(self.tried):
            self._chains = (len(self.tried), {j: self.chain(j) for j in self.seen})
        chains = self._chains[1]
        others = [(j, es) for j, o in self.seen.items() if j[1] != inv[1] for _, es in o]
        if not others:
            return set()
        count, total = {}, {}
        for j, es in others:
            for d in {self.edoer.get(e) for e in es} | set():
                if d not in chains.get(j, set()):
                    count[d] = count.get(d, 0) + 1
        n = len(others)
        return {d for d, c in count.items() if c / n >= 0.25}

    def chain(self, inv):
        """The objects this push has set going: those whose changes came after its tries at least 0.25
        more often than after the agent's pushes on other objects."""
        obs = [es for _, es in self.seen.get(inv, [])]
        if not obs:
            return set()
        others = [es for j, o in self.seen.items() if j[1] != inv[1] for _, es in o]
        rate = lambda e, group: sum(e in es for es in group) / len(group) if group else 0.0
        return {self.edoer.get(e) for e in set().union(*obs) if e in self.edoer and rate(e, obs) - rate(e, others) >= 0.25}

    def controllable(self):
        """The changes some push of the agent's produces: that come after its tries at least 0.5 more
        often than after the agent's other pushes (first: in most tries of a push; with watches that
        run on, a timer's changes fell inside most watches and counted as the agent's own)."""
        here = {i: [es for _, es in obs] for i, obs in self.seen.items() if i in self.known}
        groups = {}   # per push, its tries by reading: a press with the cable seated is its own group
        for i in here:
            for fs, es in self.seen[i]:
                groups.setdefault(i, {}).setdefault(self.reading(i, fs), []).append(es)
        everything = set().union(*[es for obs in here.values() for es in obs]) if here else set()
        out = set()
        for x in everything:
            for inv, by in groups.items():
                others = [es for j, o in here.items() if j != inv for es in o]
                p_out = sum(x in es for es in others) / len(others) if others else 0.0
                # a reading of fewer than 3 tries is too thin to tell (one or two tries show anything
                # at 100%: first, a timer's tick inside two watches counted as the agent's own)
                # (then 3 tries or more, and three coincidences in a row still happened in some reading
                # of many; now a test: k of n that unlikely, under 1%, at the other pushes' rate)
                if any(sum(x in es for es in g) / len(g) - p_out >= 0.5
                       and tail(sum(x in es for es in g), len(g), p_out) < 0.01 for g in by.values()):
                    out.add(x)
                    break
        return out

    def observed_only(self):
        """A link "X causes Y" between two changes where X is a change no push of the agent's produces
        is held as observed, not intervened on: written as co-occurrence (its funding moved there),
        and written so from then on; if a push comes to produce X, new links from X are causes again.
        (First: such links stood as causes, though the agent could not test them: the tick's valve
        before the door's.)"""
        und = self.mind.understanding
        mine = self.controllable()
        for (c, rel, o) in [k for k in und.recast if k[0] in mine or k[2] in mine]:
            del und.recast[(c, rel, o)]
        here = set(self.world.objs)
        for x, rels in list(und.rel.items()):
            # only this world's changes: a mind carried here holds other worlds' links too, which no
            # push here could produce (first: the weight world's agent recast the spring's release)
            if "_push:" in x or x in mine or self.edoer.get(x) not in here:
                continue
            for (r, y), e in list(rels.items()):
                if r != "causes" or "_push:" in y or sum(e) == 0:
                    continue
                und.recast[(x, "causes", y)] = "co_occurs"
                und.recast[(y, "caused_by", x)] = "co_occurs"
                for a, b in ((x, y), (y, x)):
                    key = ("causes" if a == x else "caused_by", b)
                    moved = und.rel.get(a, {}).get(key)
                    if moved and sum(moved):
                        tgt = und.rel[a].setdefault(("co_occurs", b), [0.0, 0.0, 0.0])
                        for i in range(3):
                            tgt[i] += moved[i]
                        und.rel[a][key] = [0.0, 0.0, 0.0]
                self.observed.add((x, y))

    def common_cause(self):
        """A link "X causes Y" between two objects' changes where, in most watches of some push holding
        both, Y's object was already set going by that push no later than X came: X was not needed for
        Y, the push did both. Recast as co-occurrence, as observed_only() does (first: a lever that
        launched two stones taught "stone A's flight causes stone B's fall")."""
        und = self.mind.understanding
        for inv, tries in self.slices.items():
            both = {}
            for sl in tries:
                firsts = {}
                for e, s in sl.items():
                    d = self.edoer.get(e)
                    firsts[d] = min(firsts.get(d, s), s)
                for x, sx in sl.items():
                    for y in sl:
                        dx, dy = self.edoer.get(x), self.edoer.get(y)
                        if dx and dy and dx != dy:
                            both.setdefault((x, y), []).append(firsts[dy] <= sx)
            for (x, y), v in both.items():
                if len(v) >= 2 and 2 * sum(v) > len(v) and (x, "causes", y) not in und.recast:
                    e = und.rel.get(x, {}).get(("causes", y))
                    e2 = und.rel.get(y, {}).get(("caused_by", x))   # either side (the register writes
                    if (e and sum(e)) or (e2 and sum(e2)):           # the effect's side on its own too)
                        und.recast[(x, "causes", y)] = "co_occurs"
                        und.recast[(y, "caused_by", x)] = "co_occurs"
                        for a, b, r in ((x, y, "causes"), (y, x, "caused_by")):
                            moved = und.rel.get(a, {}).get((r, b))
                            if moved and sum(moved):
                                tgt = und.rel[a].setdefault(("co_occurs", b), [0.0, 0.0, 0.0])
                                for i in range(3):
                                    tgt[i] += moved[i]
                                und.rel[a][(r, b)] = [0.0, 0.0, 0.0]

    def necessity(self, least=2, keep=0.8):
        """Refutation by intervention: a link X causes Y between two changes is withdrawn when, in a
        state the agent itself set (a fact about an object its pushes have changed), X never came
        while it did come otherwise, and Y came at least `least` times and at no less than `keep`
        of its rate otherwise (the state: one a push of the agent's left on the object it pushed, and
        that lasted; first, any fact about an object that changed while it watched, and a valve a
        gust had opened counted as set by the agent): X was blocked and Y did not miss it. Written back as refuted, so
        neither the agent's chain credit nor the register's own working-out writes it again
        (first: lamp B lit a slice after lamp A every time, a hidden driver lit both, and unseating
        A's plug left B lighting on time, yet "A causes B" stood: nothing read the intervention)."""
        und, hist = self.mind.understanding, self.history
        if len(hist) < 4 or not self.toggled:
            return
        facts = self.toggled
        for x, rels in list(und.rel.items()):
            if "_push:" in x:
                continue
            for (r, y), e in list(rels.items()):
                if r != "causes" or "_push:" in y or y == "no_change" or (x, "causes", y) in und.refuted:
                    continue
                for f in facts:
                    under = [a for fs, a in hist if f in fs]
                    other = [a for fs, a in hist if f not in fs]
                    if len(under) < 4 or not other:
                        continue
                    x_in, x_out = sum(x in a for a in under), sum(x in a for a in other)
                    y_in, y_out = sum(y in a for a in under), sum(y in a for a in other)
                    if x_in == 0 and x_out > 0 and y_in >= least and \
                            y_in / len(under) >= keep * (y_out / len(other) if y_out else 0.0):
                        for c, rel, o in ((x, "causes", y), (y, "caused_by", x)):
                            und.refuted.add((c, rel, o))
                            if (rel, o) in und.rel.get(c, {}):
                                und.rel[c][(rel, o)] = [0.0, 0.0, 0.0]
                        und.log.append((self.mind.t, "refuted", (x, y, f)))
                        break

    # ---- acting for a goal (Stage 3) -------------------------------------------------------------

    def model(self, inv, state):
        """The agent's own forward model of one push: from a state (object -> gerund), the effects it
        expects (predict) and the state it expects to leave: each object's gerund at the watch's end,
        where most tries in the same reading changed it. None when it has nothing to go on."""
        facts = frozenset(f"{d}_{g.replace(' ', '_')}" for d, g in state.items())
        effects = self.predict(inv, facts) if self.outcomes(inv, facts) else None
        if effects is None:
            return None
        r = self.reading(inv, facts)
        tries = [(s, a) for (fs, _), s, a in zip(self.seen.get(inv, []), self.scenes.get(inv, []), self.after.get(inv, []))
                 if self.reading(inv, fs) == r]
        nxt = dict(state)
        for o in {o for s, a in tries for o in a}:
            moved = [a[o] for s, a in tries if o in a and a[o] != s.get(o)]   # (a burst tank has no level)
            if 2 * len(moved) > len(tries):
                nxt[o] = max(set(moved), key=lambda g: (moved.count(g), g))
        return effects, nxt

    def questionable(self):
        """Pushes worth an experiment: those whose outcome turns on conditions (an untried
        combination may split them further), and those the register expects to have a condition it
        has not found (an analogy's expectation, Abstract then Constrain)."""
        und = self.mind.understanding
        out = {i for i, c in self.conds.items() if c}
        out |= {i for i in self.seen if not self.conds.get(i) and (inv_id(i), "conditioned_by") in und.expect}
        return out

    def experiment(self, state=None, depth=3):
        """The shortest sequence of pushes that brings a questionable push to a combination of the
        states the agent sets that it was never tried under, ending with that push: "which experiment
        would split this?" Found by the same search as plan(), over the agent's own model. [] if none
        (first: the agent made such a combination only by chance, and reading alone it took the AND
        of two plugs for one plug)."""
        state = dict(self.world.states() if state is None else state)
        targets = sorted(self.questionable())
        if not targets:
            return []
        # a condition expected and not found: the pushes on other objects not yet tried are where it
        # may be; try one (hard first), and the push again after
        und = self.mind.understanding
        expected = [t for t in targets if not self.conds.get(t) and (inv_id(t), "conditioned_by") in und.expect]
        untried = sorted((i for i in self.world.invitations() if not self.seen.get(i)
                          and all(i[1] != t[1] for t in expected)), key=lambda i: (i[0] != "hard", i))
        if expected and untried:
            return [untried[0], expected[0]]
        toggles = sorted(i for i in self.known if self.seen.get(i))
        tried = {i: {frozenset(f for f in fs if f in self.toggled) for fs, _ in self.seen.get(i, [])} for i in targets}
        facts = lambda s: frozenset(f"{d}_{g.replace(' ', '_')}" for d, g in s.items())
        frontier, seen = [(state, [])], {tuple(sorted(state.items()))}
        for _ in range(depth + 1):
            for s, path in frontier:
                mine = frozenset(f for f in facts(s) if f in self.toggled)
                for t in targets:
                    if s.get(t[1]) == t[2] and mine not in tried[t]:
                        return path + [t]
            nxt = []
            for s, path in frontier:
                for inv in toggles:
                    if s.get(inv[1]) != inv[2]:
                        continue
                    m = self.model(inv, s)
                    if m is None:
                        continue
                    key = tuple(sorted(m[1].items()))
                    if key not in seen:
                        seen.add(key)
                        nxt.append((m[1], path + [inv]))
            frontier = nxt
        return []

    def plan(self, goal, state=None, depth=3):
        """The shortest sequence of pushes the agent's own model says reaches the goal effect, found by
        search over the pushes it knows, at most `depth` long; pushes tried in the order of the
        question molecules' last bids (the top's winners guide the search). With the model
        deterministic, MCTS's rollouts reduce to this search. [] if the goal is reached by no
        sequence it can predict (it has no model, or nothing it knows does it)."""
        state = dict(self.world.states() if state is None else state)
        order = sorted(self.known, key=lambda i: (-self.bids.get(f"q:invite:{inv_id(i)}", 0.0), i))
        frontier, seen = [(state, [])], {tuple(sorted(state.items()))}
        for _ in range(depth):
            nxt_frontier = []
            for s, path in frontier:
                for inv in order:
                    if s.get(inv[1]) != inv[2]:   # the push is invited only in that configuration
                        continue
                    m = self.model(inv, s)
                    if m is None:
                        continue
                    effects, s2 = m
                    if goal in effects:
                        return path + [inv]
                    key = tuple(sorted(s2.items()))
                    if key not in seen:
                        seen.add(key)
                        nxt_frontier.append((s2, path + [inv]))
            frontier = nxt_frontier
        return []

    # ---- a tick -----------------------------------------------------------------------------------

    def tick(self, force=None):
        """force: an invitation to push this tick whatever won (a scripted intervention, for
        tests); ignored while watching."""
        mind, world = self.mind, self.world
        if not self.watching:   # a due reset happens before the scene is read (first: inside the
            world.renew()       # push's act, so the push was read off one scene and acted on another)
        mind.facts = {d: clause(f"{d}_{g.replace(' ', '_')}", tags=(d, g)) for d, g in world.states().items()}
        news = [clause(effect_id(e)) for e in world.diffs]
        self.known |= set(world.invitations())
        if self.first is None:   # the scene as the agent first found it (polarity's reference)
            self.first = {d: g for d, g in world.states().items() if not NUMERIC.match(f"{d}_{g}")}
        self.history.append((self.facts_now(), frozenset(effect_id(e) for e in world.diffs)))
        if not self.watching and self.necessity_on:
            self.necessity()
            self.observed_only()
            self.common_cause()
        live = set()
        for inv in world.invitations():
            q, p = f"q:invite:{inv_id(inv)}", self.pull(inv)
            if p > 0.05:
                mind.pool[q] = clause(q, tags=("question", "invitation"), sites=(f"causes?{inv_id(inv)}",))
                mind.pool[q].act = p
                live.add(q)
        for q in [i for i in mind.pool if i.startswith("q:invite:") and i not in live]:
            del mind.pool[q]
        rec = mind.tick(news)
        if self.watching:   # still watching the last push: no new push
            world.act(None, hold=True)
            self.watch(world.diffs)
            return None, rec
        if self.rest and force is None:   # varying when it pushes: a periodic driver cannot keep step
            self.rest -= 1   # (first: a steady rhythm, and a gust of period 8 fell in four of five tries
            world.act(None)  # of one push, which then read as that push's doing)
            return None, rec
        top = rec["levels"][-1]["winners"]
        self.bids = dict(rec["levels"][-1]["bids"])
        asks = [i for i in top if i.startswith("q:invite:")]
        choice = force
        if choice is None and self.goal is not None:   # a want: act on a plan, if there is one
            self.plan_now = self.plan(self.goal)
            live_now = set(world.invitations())
            if self.plan_now and self.plan_now[0] in live_now:
                choice = self.plan_now[0]
        if asks and choice is None:
            best = max(asks, key=lambda i: (rec["levels"][-1]["bids"].get(i, 0.0), i))
            choice = next(inv for inv in world.invitations() if f"q:invite:{inv_id(inv)}" == best)
        if self.experiments_on and force is None and self.goal is None:
            # an experiment, when it is worth more than the question that won: its push, half open
            # in an untried combination, at its estimated work
            exp = self.experiment()
            if exp and exp[0] in set(world.invitations()):
                target = exp[-1]
                per = [v / world_amount(i) for i, v in self.estimate.items()]
                worth = 0.5 * max(self.estimate.get(target, 0.0), world_amount(target) * (sum(per) / len(per) if per else self.prior))
                if choice is None or worth > self.pull(choice):
                    choice, self.plan_now = exp[0], exp
        if choice is None:
            world.act(None)
            return None, rec
        chain = self.chain(choice)   # the objects this push is known to set going
        background = {e.split(": ", 1)[0] for e in world.diffs}   # what was changing before the push
        self.last_diffs = []
        self.watching = (choice, self.facts_now(), 0, {}, set(world.invitations()), world.states(), (chain, background))
        self.watch(world.act(choice))
        return choice, rec

    def watch(self, diffs):
        """One slice of watching a push: collect its diffs; at the window's end, write them."""
        inv, facts, k, effects, before, states, (chain, background) = self.watching
        # changed in its own slice, and what it is known to set going; before that is known (a first
        # try), what changed in this watch that was not already changing and is not known to change
        # after the agent's other pushes too (a gust's flag is; first, without that exclusion, the
        # gusts' coincidences came back, and without the fallback a first try's watch could not run on)
        own = {self.edoer.get(x) for x, s in effects.items() if s == 0} | chain
        if not chain:
            own |= {self.edoer.get(x) for x in effects} - background - self.restless(inv)
        # going on: a gauged or sensed quantity of the push's own objects still changing (its "holds"
        # events; a plain flip, a gust's flag or a timer's lamp, never runs a watch on)
        going = any(e.split(": ", 1)[0] in own and "holds" in e for e in diffs)
        going = going or any(e.split(": ", 1)[0] in own and "holds" in e for e in self.last_diffs)  # a quiet slice
        self.last_diffs = list(diffs)   # (a pump's one-slice lag left one, and the runaway's watch ended there)
        for e in diffs:
            eid = effect_id(e)
            if eid not in effects:
                effects[eid] = k
                self.edoer[eid] = e.split(": ", 1)[0]
                self.mind.understanding.owners[eid] = self.edoer[eid]
        k += 1
        base = self.watch_len or self.world.horizon
        # past the base window, the watch goes on while what the push set going is still changing (an
        # object it changed in its own slice, or one its tries have shown it sets going), up to four
        # times the base (first: a fixed window, so a runaway's burst or a cascade's break later than
        # it was never the push's; then any object changed in the watch, and a gust's flag, swung
        # inside it, kept watches going and fell in most of a few tries)
        if k < base or (self.extend and going and k < 4 * base):
            self.watching = (inv, facts, k, effects, before, states, (chain, background))
            return
        self.watching = None
        und = self.mind.understanding
        names = sorted(effects) or ["no_change"]
        # a push that changed nothing is kept in the tries (seen), not in understanding: "no change"
        # is not a change, and as one node it joined every world's structure into one (found: no
        # analogy between worlds formed while every inert push "caused" the same no_change)
        by_slice = {}
        for e, s in effects.items():
            by_slice.setdefault(s, []).append(e)
        for e, s in sorted(effects.items(), key=lambda x: (x[1], x[0])):
            earlier = [t for t in by_slice if t < s]
            if not earlier:   # the push's own slice (or the first change after it)
                parents = [inv_id(inv)]
            else:
                prev = by_slice[max(earlier)]
                parents = [p for p in prev if self.edoer[p] == self.edoer[e]] or prev
            for p in parents:   # both ways: p causes e, and e is caused by p
                und.add(p, "causes", e, "seen", 1.0 / len(parents))
                und.add(e, "caused_by", p, "seen", 1.0 / len(parents))
        self.seen.setdefault(inv, []).append((facts, frozenset(names)))
        self.scenes.setdefault(inv, []).append(states)
        self.after.setdefault(inv, []).append(self.world.states())
        self.slices.setdefault(inv, []).append(dict(effects))   # when each change came in the watch
        now = self.world.states().get(inv[1])
        fact = f"{inv[1]}_{now.replace(' ', '_')}" if now else None
        if now != states.get(inv[1]) and effects.get(fact) == 0:   # its push made it, in its own
            self.toggled.add(fact)                                  # slice, and it lasted the watch
        new = self.conditions(inv)
        for c in new:   # each try that still splits on a condition funds it again (first: only when
            for f in c:   # found, so a condition stood at 1 against links funded by every try)
                und.add(f, "conditions", inv_id(inv), "seen", 1.0 / len(c))
        # polarity per object, the one most tries stand behind (first: per condition, and a gust's
        # coincidence with the latch seated wrote "enables" beside "prevents")
        votes = {}
        mine = self.chain(inv) | {inv[1]}   # only effects this push sets going vote (first: any, and a
        for c, e, n in self.detail.get(inv, []):   # gust's press of the button gave the flag push a cable)
            if self.edoer.get(e) not in mine:
                continue
            for f in c:
                pol = self.polarity(f)
                if pol:
                    votes.setdefault(self.owner(f), {}).setdefault(pol, 0)
                    votes[self.owner(f)][pol] += n
        for o, v in votes.items():
            rel, fact = max(v, key=lambda p: (v[p], p))
            other = "prevents" if rel == "enables" else "enables"
            for c, rels in und.rel.items():   # the losing polarity for this object and push goes
                if c.startswith(o + "_") and (other, inv_id(inv)) in rels:
                    rels[(other, inv_id(inv))] = [0.0, 0.0, 0.0]
            und.add(fact, rel, inv_id(inv), "seen", 1.0)
        self.conds[inv] = new
        # what the agent saw: the push times the changes that followed it (gerunds flipped,
        # invitations opened or closed), including any it wrongly attributes. Not world.work(),
        # the counterfactual against the no-push scene, which the agent cannot know (first the
        # estimate was set from it, so a confounded push was never retried).
        self.estimate[inv] = world_amount(inv) * (len(effects) + len(before ^ set(self.world.invitations())))
        self.tried.append((self.mind.t, inv, names))
        self.rest = len(self.seen[inv]) % 2   # a tick's rest after every other try of a push


def tail(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    from math import comb
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def world_amount(inv):
    return AMOUNTS[inv[0]]
