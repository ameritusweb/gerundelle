"""Thought molecules POC. Design: ../THOUGHT_MOLECULES.md.

Molecules are thought clauses. Each holds all its candidate bindings at once and resolves to the
argmax under the current state at each level. Observation is winning a limited working-memory
slot; each level's winners compete for the next level, under that level's own experience record.
Action is MCTS with rules, guided by the top-level winners. No sampling anywhere.
"""
from dataclasses import dataclass, replace
import math
import random


def digamma(x):
    r = 0.0
    while x < 6:
        r -= 1 / x
        x += 1
    f = 1 / (x * x)
    return r + math.log(x) - 0.5 / x - f * (1 / 12 - f * (1 / 120 - f / 252))


PRIOR = (1.0, 1.0, 1.0)   # Dirichlet prior over outcomes (good, neutral, bad)


_IG = {}


def info_gain(a):
    """Expected information gain about a Dirichlet's parameters from one more observation.

    Memoized on the counts: most pairs share a handful of count vectors (never-formed pairs all
    sit at the prior), so this is nearly free after the first few calls."""
    key = tuple(a)
    r = _IG.get(key)
    if r is None:
        r = _IG[key] = _info_gain(a)
    return r


def _info_gain(a):
    a0 = sum(a)
    p = [x / a0 for x in a]
    h_pred = -sum(q * math.log(q) for q in p)
    h_exp = sum(q * (digamma(a0 + 1) - digamma(x + 1)) for q, x in zip(p, a))
    return h_pred - h_exp


IG0 = info_gain(PRIOR)


@dataclass
class Params:
    slots: tuple = (7, 5, 4)   # working-memory slots per level; the last level is conscious (7/4/2 until 2026-10-22: room for the goals and one experience)
    T: float = 1.0             # open-site tension, and the pull between an open site and a filler
    n: float = 0.3             # novelty (expected surprise) at a never-formed pair
    w_edge: float = 0.5        # pull a bond acting as an edge puts between its two ends
    h0: float = 3.0            # base half-life in ticks
    floor: float = 0.05        # activation below which a molecule is gone
    kappa: float = 2.0         # shrinkage of a molecule's percept prediction toward the base rate
    w_pred: float = 0.5        # weight of expected surprise reduction going forward in the bid
    ema: float = 0.3           # running-average rate for precision
    # the five modulators of half-life: four extend it, closure lets a thought finish
    a_success: float = 0.5     # prior top-level wins
    a_surprise: float = 1.0    # surprise of its arrival or of what it generated
    a_novelty: float = 1.0     # structural uniqueness
    a_blocked: float = 1.0     # blocked momentum
    closure: bool = True       # resolved openings crystallize into boxes
    resonance: float = 0.5     # share of a box's keys among the winners that re-opens it
    s_keep: float = 0.7        # surprise remembered per tick
    reentry: float = 0.2       # success: shorter path back (activation on re-entry)
    # storage (the two-phase thread)
    h_site: float = 20.0       # half-life of a parked site: ticks without being filled
    cold: float = 0.1          # warmth below which a site is no longer checked
    rationalize: float = 0.6   # binding score at which an open thought closes on a non-fitting partner (None: off)
    park_after: int = None     # ticks blocked with >= park_holes open sites before parking (None: off)
    park_holes: int = 2
    self_feed: bool = True     # top-winning composites and re-opened parked boxes come back as percepts
    A: int = 8                 # partner search: history, site fit, bond, plus the A most active (None: everyone)
    dwell: int = 3             # a holeless thought that has won this many ticks running with flat surprise closes (None: off)
    flat: float = 0.05         # flat surprise: its precision moved less than this at its last update
    # the meta layer (Meta): processing states as molecules that compete, earn, and gate operations
    meta: bool = True          # on by default (the user, 2026-10-22)
    meta_slots: tuple = (3, 2, 2)  # meta molecules compete only with each other for their own slots per level (the user, 2026-10-22); None: shared
    mute_meta: bool = False    # ablation: meta molecules enter the pool but never bid (silent absence)
    meta_horizon: int = 5      # ticks a meta molecule's prediction has to come true
    meta_depth: int = 2        # deepest meta-about-meta (a safety bound; funding is the real one)
    meta_funding: bool = True  # ablation: predictions are scored but neither refresh nor drop anything
    meta_off: tuple = ()       # knockout: kinds of meta molecule that never form (ABI's knockout design)
    # SOV molecules and the understanding register (THOUGHT_MOLECULES.md sec. 5g)
    sov: bool = True           # on by default (the user, 2026-10-22, after the three decisions)
    sov_m0: float = 2.0        # funding at which one relation type of a concept counts as understood
    sov_cues: int = 2          # SOV molecules cued per tick at most
    sov_slots: tuple = (3, 2, 2)   # SOV molecules and questions compete only with each other (the user, 2026-10-22)
    # emotional phases (THOUGHT_MOLECULES.md sec. 5h)
    phases: bool = False       # off by default until the user decides
    phase_slots: tuple = (2, 1, 1)   # a phase's first molecule competes here; its copies flood the thoughts' slots
    phase_h: float = 4.0       # half-life of a phase molecule not refreshed by what produced it
    # inquiry (DRIFT.md, the user 2026-10-23): an SOV's open slots suggest experiments, molecules of
    # their own that fight for attention; what wins the top is what the agent does
    inquiry: bool = False      # off by default: the thought worlds have their own actions (Agent)
    exp_slots: tuple = (2, 1, 1)   # experiment molecules compete only with each other
    own_slots: tuple = (2, 1, 1)   # the ownership SOV's slot instances and questions, their own track
    # temperament (the user, 2026-10-25: "a mind with a low parking threshold is impatient ... neither is
    # broken. They're different characters"): how many claims running on a wanted region may fail before the
    # want is parked, given up (None: never; a want is otherwise pursued through action, not set aside)
    patience: int = None
    # credulity: the weight a told receipt funds at, against lived and worked-out ones at 1 (molecules'
    # "told at half" was this at 0.5): the trusting take a word nearly as their own experience
    credulity: float = 0.5
    # curiosity: the pull of unknowns no want pays for (an unclaimed region, a held region's uniqueness), as a
    # multiple of the territory's own (1: as REORG has it). The curious wander; the incurious stay on the want
    curiosity: float = 1.0
    # persistence: how slowly an experiment that keeps being done stops being worth doing, value x q / (q +
    # times done) (1: Inquiry's "the same experiment again teaches less", 1 / (1 + done)). Low: a question
    # let go soon; high: one that cannot be let go
    persistence: float = 1.0
    # constraint convergence (embodied): support from constraint molecules bound to a molecule at once,
    # added to its bid (Mind.support). None: off; "resolved": the bindings that resolved onto it;
    # "candidates": every constraint it could fill, in superposition
    support: str = None
    w_support: float = 1.0


@dataclass
class Molecule:
    id: str
    tags: frozenset = frozenset()
    sites: tuple = ()          # open sites: each is a tag that would fill it
    bond: tuple = None         # bonds only: (tag of one end, tag of the other end)
    strength: float = 1.0      # bonds only: scales the pull between its ends (a recognition: 1 + the error it accounts for)
    parts: tuple = ()          # composites only: the molecules it was formed from
    act: float = 1.0
    c: int = 0                 # complexity: bonding depth
    last_level: int = -1       # highest level reached at its last win

    def __post_init__(self):
        self.tags = frozenset(self.tags) | {self.id}


def clause(id, tags=(), sites=()):
    return Molecule(id, frozenset(tags), tuple(sites))


def bond(id, a, b, tags=(), strength=1.0):
    return Molecule(id, frozenset(tags), bond=(a, b), strength=strength)


def fills(x, y):
    """x fills one of y's open sites."""
    return any(s in x.tags for s in y.sites)


class Mind:
    def __init__(self, params=None, names=None):
        self.p = params or Params()
        self.names = names or {}   # (end, end, bond) -> readable composite id
        self.pool = {}
        self.exp = [dict() for _ in self.p.slots]   # per level: pair -> Dirichlet [good, neutral, bad]
        self.history = {}     # molecule -> molecules it has an experience record with, any level
        self.after = {}       # molecule -> {percept: count} on ticks after it won
        self.base = {}        # percept -> count, all ticks
        self.pi = {}          # molecule -> precision (running surprise reduction)
        self.prev = set()     # molecules that won a slot last tick
        self.t = 0
        self.last_win = {}    # molecule -> tick of its last slot win
        self.top_wins = {}    # molecule -> number of top-level wins (success)
        self.S = {}           # molecule -> surprise level, 0..1
        self.boxes = {}       # molecule -> closed thought in storage (see new_box)
        self.index = {}       # tag -> boxes with a key containing it
        self.mol_index = {}   # tag -> boxes whose molecule carries it
        self.hole = {}        # molecule -> what its blocked momentum points at, last tick
        self.fillers = {}     # molecule -> molecules that filled its sites while open
        self.blocked_for = {}  # molecule -> consecutive ticks blocked
        self.prev_tags = frozenset()  # tags of last tick's winners
        self.pending = []     # self-generated molecules to perceive next tick
        self.facts = {}       # facts register: slot -> the clause standing in it (see Agent.episode)
        self.contradicted = []  # boxes the world re-opened since last asked
        self._sig_t, self._sigs, self._by_elem = -1, {}, {}   # novelty index, per tick
        self.perceived = set()   # ids perceived this tick
        self.streak = {}      # molecule -> consecutive ticks it has won a slot
        self.pi_delta = {}    # molecule -> how much its precision moved at its last update
        self.S_prev = {}      # molecule -> its surprise level last tick
        self.flat_for = {}    # molecule -> consecutive ticks its surprise level stayed flat
        self.boost_until = -1  # novelty doubled until this tick (a noticed "nothing's happening")
        self.meta = Meta(self) if self.p.meta else None
        self.understanding = Understanding(self) if self.p.sov else None
        self.territory = Territory(self)   # every mind (REORG.md: no mind runs without it)
        self.phases = Phases(self) if self.p.phases else None
        self.inquiry = Inquiry(self) if self.p.inquiry and self.understanding else None

    # ---- state -------------------------------------------------------------------------------

    def present(self, m, act=1.0):
        """Perceive or re-present a molecule: raises its activation and resets its clock."""
        if self.meta:
            m = self.meta.distinguish(m)
        if m.id in self.pool:
            self.pool[m.id].act = max(self.pool[m.id].act, act)
        elif self.boxes.get(m.id, {}).get("settled"):
            return   # a finished thought, perceived again: it stays in storage until something needs or questions it
        else:   # success: a thought that has been conscious before comes back stronger
            self.pool[m.id] = replace(m, act=act * (1 + self.p.reentry * math.log1p(self.top_wins.get(m.id, 0))))

    def remove(self, id):
        self.pool.pop(id, None)

    def record(self, L, a, b):
        pair = frozenset((a, b))
        if pair not in self.exp[L]:
            self.exp[L][pair] = list(PRIOR)
            self.history.setdefault(a, set()).add(b)
            self.history.setdefault(b, set()).add(a)
        return self.exp[L][pair]

    def seed(self, L, a, b, good=0, neutral=0, bad=0):
        self.record(L, a, b)[:] = [PRIOR[0] + good, PRIOR[1] + neutral, PRIOR[2] + bad]

    def mu(self, L, a, b):
        g, z, d = self.exp[L].get(frozenset((a, b)), PRIOR)
        return (g - d) / (g + z + d)

    # ---- surprise reduction ------------------------------------------------------------------

    def perceive(self, ids):
        """Score last tick's winners on how well they predicted these percepts, then count them."""
        self.perceived = set(ids)
        if ids:
            tot = sum(self.base.values())
            vocab = len(set(self.base) | set(ids))
            base = {j: (self.base.get(j, 0) + 1) / (tot + vocab) for j in ids}
            for j in ids:   # surprise of arrival
                self.S[j] = max(self.S.get(j, 0.0), min(1.0, -math.log(base[j]) / math.log(tot + vocab + 1)))
            for m in self.prev:
                seen = self.after.get(m, {})
                n = sum(seen.values())
                score = sum(math.log((seen.get(j, 0) + self.p.kappa * base[j]) / (n + self.p.kappa))
                            - math.log(base[j]) for j in ids)
                new = (1 - self.p.ema) * self.pi.get(m, 0.0) + self.p.ema * score
                self.pi_delta[m] = abs(new - self.pi.get(m, 0.0))
                self.pi[m] = new
            for m in self.prev:
                seen = self.after.setdefault(m, {})
                for j in ids:
                    seen[j] = seen.get(j, 0) + 1
            for j in ids:
                self.base[j] = self.base.get(j, 0) + 1

    # ---- forces ------------------------------------------------------------------------------

    def force(self, L, m, p):
        a = self.exp[L].get(frozenset((m.id, p.id)))
        n = self.p.n * (2.0 if self.t < self.boost_until else 1.0)
        if a is None:   # never formed: mu is 0 and the novelty term is at its maximum
            f = n
        else:
            f = (a[0] - a[2]) / (a[0] + a[1] + a[2]) + n * info_gain(a) / IG0
        if fills(m, p) or fills(p, m):
            f += self.p.T
        if self.meta and self.meta.about_pair(m.id, p.id):   # a thought about a thought is drawn to it
            f += 0.5 * self.p.T
        return f

    def tension(self, m, binding):
        if not m.sites:
            return 0.0
        if m.id.startswith("sov:") and self.understanding and self.territory.served is not None:
            # paid by the ownership slots it serves (REORG.md step 3): a concept no slot needs pulls
            # nothing, whatever its level
            c = m.id[4:]
            pay = self.territory.served.get(c, (0.0, ()))[0]
            return self.p.T * self.understanding.needed_openness(c) * pay
        if m.id.startswith("sov:") and self.understanding:   # pull = the share of the concept still open,
            c = m.id[4:]                                      # plus its progress momentum (first the share
            return self.p.T * (1 - self.understanding.level(c) + self.understanding.progress.get(c, 0.0))
            # alone: a push 0.6 understood, its last try just contradicting its prediction, lost the top
            # to fresh gust concepts, and its investigation stopped the moment it began to pay)
        if is_own(m.id):   # an ownership slot instance pulls by its kind (REORG.md: lost > control > unclaimed)
            return self.p.T * self.territory.pull(m.id)
        if is_exp(m.id):   # an experiment's pull is its value (how open its slot, less for repeats;
            return self.p.T * m.act   # first the open site's full pull, and one repeated forever)
        filler = self.pool.get(binding[1]) if binding[0] == "partner" else None
        unfilled = [s for s in m.sites if filler is None or s not in filler.tags]
        return self.p.T * len(unfilled)

    def support(self, res, comps):
        """Constraint convergence (embodied, the user 2026-10-28: "it's noticing when constraints converge to
        a distinctive solution among the failures"; simultaneous binding). A molecule is supported by the
        constraint molecules (tagged "constraint") bound to it at once, each counted once, w_support x T
        apiece. Recomputed every tick from the bindings of that tick, never accumulated, so it lasts only as
        long as the constraints do (the chapter 4 lock-in came from attraction that fed on itself).
          resolved    the constraints whose binding resolved onto it (argmax: each constraint picks one)
          candidates  the constraints whose open site it fills among this level's competitors (the bindings
                      in superposition, before each constraint resolves to one of them)
        None: off (Gerundelle as it was)."""
        mode = self.p.support
        if mode is None:
            return {}
        cons = [m for m in comps if "constraint" in m.tags]
        out = {}
        if mode == "resolved":
            for m in cons:
                b = res.get(m.id)
                if b and b[0] == "partner":
                    out[b[1]] = out.get(b[1], 0.0) + 1.0
        elif mode == "candidates":
            for x in comps:
                if "constraint" in x.tags:
                    continue
                n = sum(m.act for m in cons if fills(x, m))   # each constraint by its weight (1: all alike)
                if n:
                    out[x.id] = float(n)
        return {i: self.p.w_support * self.p.T * n for i, n in out.items()}

    def forward(self, id):
        """Expected surprise reduction going forward (the user's reading, 2026-10-22): the surprise
        still attached to the thought, plus what attending to it would still teach about what
        follows it (large for a new arrival, near zero once its record is long). Replaces the
        running precision, which was credit for the past."""
        return self.S.get(id, 0.0) + 1.0 / (1 + sum(self.after.get(id, {}).values()))

    # ---- ties: expected surprise, then recency ------------------------------------------------

    def surprise(self, L, m, binding):
        """Expected surprise of a binding: what one more observation of the pair would teach."""
        if binding[0] != "partner":
            return 0.0
        return info_gain(self.exp[L].get(frozenset((m, binding[1])), PRIOR))

    def waited(self, id):
        return self.t - self.last_win.get(id, -10 ** 9)

    # ---- argmax superposition ----------------------------------------------------------------

    def level_index(self, comps):
        """Per-level indexes: molecules by tag, molecules by open site, the A most active."""
        by_tag, by_site = {}, {}
        for x in comps:
            for t in x.tags:
                by_tag.setdefault(t, []).append(x)
            for s in x.sites:
                by_site.setdefault(s, []).append(x)
        active = set()
        if self.p.A is not None:   # the A most active, and the A that have waited longest (the tie-break)
            base = [x for x in comps if not is_meta(x.id) and not is_sov(x.id) and not is_exp(x.id) and not is_own(x.id)]   # nobody's partner but their subject's
            active = {x.id for x in sorted(base, key=lambda x: (-x.act, x.id))[:self.p.A]}
            active |= {x.id for x in sorted(base, key=lambda x: (-self.waited(x.id), x.id))[:self.p.A]}
        tops = {}

        def top(t):
            """The most active carriers of a tag (all of them when A is None): the only ones
            that can be the argmax end of an edge."""
            if t not in tops:
                xs = sorted((x for x in by_tag.get(t, ()) if not is_meta(x.id)),   # aboutness is one-way: a
                            key=lambda x: (-x.act, x.id))   # meta molecule is no bond's end (SOV.Competition)
                if self.p.A is not None and len(xs) > self.p.A:   # keep ties at the cut
                    cut = xs[self.p.A - 1].act
                    xs = [x for x in xs if x.act >= cut]
                tops[t] = xs
            return tops[t]
        return dict(by_tag=by_tag, by_site=by_site, active=active, edge_pairs={}, top=top)

    def candidates(self, m, comps, ix):
        """Partners m considers: everyone when A is None; otherwise those it has history with,
        an open-site fit with, a bond to (a bond among the competitors whose other end it could
        be), plus the A most active and the A that have waited longest since a win (exact ties
        in score go to the longest wait, so the full search's choice stays among the candidates)."""
        if self.p.A is None:
            return [p for p in comps if p.id != m.id]
        keep = set(self.history.get(m.id, ())) | ix["active"]
        if self.meta and m.id in self.meta.about:
            keep.add(self.meta.about[m.id])
        if is_sov(m.id) and self.understanding:
            c = m.id[4:] if m.id.startswith("sov:") else m.id.split(":", 2)[2]
            keep |= {x.id for x in comps if not is_sov(x.id) and self.understanding.related(c, x.id)}
        for s in m.sites:                       # p fills m
            keep.update(x.id for x in ix["by_tag"].get(s, ()))
        for t in m.tags:                        # m fills p
            keep.update(x.id for x in ix["by_site"].get(t, ()))
        for x in comps:                         # bonds whose ends m could be one of
            if x.bond:
                ta, tb = x.bond
                if ta in m.tags:
                    keep.update(y.id for y in ix["by_tag"].get(tb, ()))
                if tb in m.tags:
                    keep.update(y.id for y in ix["by_tag"].get(ta, ()))
        return [p for p in comps if p.id != m.id and p.id in keep]

    def resolve(self, m, comps, L, ix):
        """All candidate bindings of m among this level's competitors; returns the argmax."""
        options = [(0.0, ("none",))]
        if m.bond:
            ta, tb = m.bond
            for a in ix["top"](ta):
                for c in ix["top"](tb):
                    if a.id != c.id and m.id not in (a.id, c.id):
                        options.append((self.p.w_edge * a.act * c.act, ("edge", a.id, c.id)))
        for p in self.candidates(m, comps, ix):
            if is_meta(p.id) and not is_meta(m.id):   # thoughts about thinking bind to their subjects,
                continue                              # not the other way: they do not lift a thought's bid
            if is_meta(m.id) and self.meta and self.meta.about.get(m.id) != p.id:
                continue                              # and to nothing but their subjects
            if is_sov(p.id) and not is_sov(m.id):     # SOV molecules and questions, one way too
                continue
            if is_phase(p.id) and not is_phase(m.id):  # phases too: they bind only to their anchor
                continue
            if is_own(m.id) or is_own(p.id):          # ownership instances bind to nothing yet: their
                continue                              # pull reaches concepts through `serves` (step 3)
            if is_exp(p.id):                          # experiments: one way, to an instance of their
                continue                              # concept (an experiment is about it)
            if is_exp(m.id) and self.inquiry and concept_of(p.id) != self.inquiry.concept(m.id):
                continue
            if is_phase(m.id) and self.phases and self.phases.anchor(m.id) != p.id:
                continue
            if is_sov(m.id) and self.understanding and (is_sov(p.id) or not self.understanding.related(
                    m.id[4:] if m.id.startswith("sov:") else m.id.split(":", 2)[2], p.id)):
                continue                              # an SOV or question binds only to knowns its concept has evidence with
            s = p.act * self.force(L, m, p)
            for b in ix["edge_pairs"].get(frozenset((m.id, p.id)), ()):
                s += self.p.w_edge * self.pool[b].act * self.pool[b].strength
            options.append((s, ("partner", p.id)))
        # argmax; exact ties: more expected surprise, then the partner that has waited longest, then key
        best = max(round(o[0], 9) for o in options)
        tied = [o for o in options if round(o[0], 9) == best]
        if len(tied) > 1:
            tied.sort(key=lambda o: (-round(self.surprise(L, m.id, o[1]), 9),
                                     -(self.waited(o[1][1]) if o[1][0] == "partner" else 0), o[1]))
        return tied[0][1], tied[0][0]

    # ---- one tick of thinking ----------------------------------------------------------------

    def think(self):
        if self.meta:
            self.meta.reread()
        comps = sorted(self.pool.values(), key=lambda m: (m.bond is None, m.id))  # bonds first
        levels = []
        for L, k in enumerate(self.p.slots):
            edges, res, bids, scores = {}, {}, {}, {}
            ix = self.level_index(comps)
            for m in comps:
                b, s = self.resolve(m, comps, L, ix)
                res[m.id], scores[m.id] = b, s
                if b[0] == "edge":          # acting as an edge: takes no slot at this level
                    edges[m.id] = (b[1], b[2])
                    ix["edge_pairs"].setdefault(frozenset((b[1], b[2])), []).append(m.id)
            # bids after every binding is resolved (embodied, 2026-10-28: first in the same pass, so a
            # molecule bid before the molecules after it had chosen, and support could not be counted)
            support = self.support(res, comps)
            for m in comps:
                b, s = res[m.id], scores[m.id]
                if b[0] == "edge" or (self.p.mute_meta and is_meta(m.id)):
                    continue
                bids[m.id] = (m.act * (1 + max(s, 0.0)) + self.tension(m, b) + self.p.w_pred * self.forward(m.id)
                              + support.get(m.id, 0.0))
            order = lambda ids: sorted(ids, key=lambda i: (-round(bids[i], 9), -round(self.surprise(L, i, res[i]), 9),
                                                           -self.waited(i), i))
            if self.p.meta_slots is None:
                winners = order([i for i in bids if not is_own(i)])[:k]
                winners += order([i for i in bids if is_own(i)])[:self.p.own_slots[L]]
            else:   # thoughts, thoughts about thinking, and understanding work compete in separate tracks
                own_sov = self.p.sov_slots is not None
                primary = self.phases.primaries() if self.phases else set()
                base = order([i for i in bids if not is_meta(i) and not (own_sov and is_sov(i))
                              and i not in primary and not is_exp(i) and not is_own(i)])[:k]
                flood = sum(1 for i in base if is_phase(i))   # phase copies holding thoughts' slots
                # meta slots are for operating (the user, 2026-10-24: "capability without receptor is
                # latent"): the kinds with an operation take them first, by bid among themselves; those
                # with none (torn, surprised, wrong, resolved) still live by their predictions and fill
                # what is left, by bid. First by bid alone, and torn molecules held the meta track 276
                # ticks of 300 while a push's conflation, its boundary found, faded unoperated
                # (in acting minds so far, those with inquiry: in the designed worlds' minds it moved
                # T15, T50 and T51; REORG.md step 6, open)
                operable = lambda i: bool(self.inquiry) and i.split(":")[1] in Meta.OPERATES
                metas = (order([i for i in bids if is_meta(i) and operable(i)])
                         + order([i for i in bids if is_meta(i) and not operable(i)]))
                winners = base + metas[:self.p.meta_slots[L]]
                if own_sov:
                    winners += order([i for i in bids if is_sov(i)])[:self.p.sov_slots[L]]
                if primary:
                    winners += order([i for i in bids if i in primary])[:self.p.phase_slots[L]]
                if self.inquiry:   # experiments compete for their own slots
                    winners += order([i for i in bids if is_exp(i)])[:self.p.exp_slots[L]]
                winners += order([i for i in bids if is_own(i)])[:self.p.own_slots[L]]   # and ownership
            levels.append(dict(res=res, edges=edges, bids=bids, scores=scores, winners=winners,
                               flood=flood if self.p.meta_slots is not None else 0))
            comps = sorted((self.pool[i] for i in winners), key=lambda m: (m.bond is None, m.id))

        rec = dict(levels=levels, pairs=[], formed=[], filled=[], removed=[])
        reached = {}
        for L, lv in enumerate(levels):
            win = set(lv["winners"])
            for i in win:
                reached[i] = L
            seen = set()
            for i in lv["winners"]:
                b = lv["res"][i]
                if b[0] == "partner" and b[1] in win:
                    pair = frozenset((i, b[1]))
                    if pair not in seen:
                        seen.add(pair)
                        rec["pairs"].append((L, pair))
            # composites: a bond acting as an edge between two winners bound to each other
            for bid_, (x, y) in lv["edges"].items():
                if x in win and y in win and (lv["res"][x] == ("partner", y) or lv["res"][y] == ("partner", x)):
                    rec["formed"].append((L, x, y, bid_))
            # open sites filled by a winner the open molecule resolved to
            for i in lv["winners"]:
                m, b = self.pool[i], lv["res"][i]
                if m.sites and b[0] == "partner" and b[1] in win:
                    filler = self.pool[b[1]]
                    done = tuple(s for s in m.sites if s in filler.tags)
                    if done:
                        rec["filled"].append((i, b[1]))
        rec["reached"] = reached
        rec["boredom"], rec["novelty_share"] = self.readouts(levels[0])
        self.prev = set(reached)
        self.prev_tags = frozenset().union(*(self.pool[i].tags for i in reached), *(m.tags for m in self.facts.values()))
        for i in reached:
            self.last_win[i] = self.t
        for i in self.pool:
            self.streak[i] = self.streak.get(i, 0) + 1 if i in reached else 0
            s = self.S.get(i, 0.0)
            self.flat_for[i] = self.flat_for.get(i, 0) + 1 if abs(s - self.S_prev.get(i, s)) < self.p.flat else 0
            self.S_prev[i] = s
        self.t += 1

        for i, L in reached.items():
            self.pool[i].last_level = L
        for i in levels[-1]["winners"]:
            self.top_wins[i] = self.top_wins.get(i, 0) + 1
        for i, f in rec["filled"]:
            m = self.pool[i]
            if "constraint" in m.tags:   # a constraint stands: every attempt is held against it, so meeting it
                continue                 # once does not close it (embodied; first its site was filled on the
                                         # first tick and it bound to nothing after)
            m.sites = tuple(s for s in m.sites if s not in self.pool[f].tags)
            self.fillers.setdefault(i, set()).add(f)

        new = []
        for L, x, y, b in rec["formed"]:
            key = tuple(sorted((x, y))) + (b,)
            cid = self.names.get(key, f"[{key[0]}+{key[1]}|{b}]")
            parts = (x, y, b)
            act = max(self.pool[x].act, self.pool[y].act)
            c = 1 + max(self.pool[j].c for j in parts)
            new.append(Molecule(cid, frozenset(), parts=parts, act=act, c=c, last_level=L))

        blocked, holes = self.blocked(rec)
        rec["closed"], rec["reopened"], rec["parked"], rec["settled"] = [], [], [], []
        if self.p.closure:
            self.close(rec, blocked)
        if self.p.closure and self.p.dwell:
            self.settled(rec, blocked)
        if self.p.park_after:
            self.park(rec, blocked)

        # half-life: only molecules that won no slot this tick decay
        for m in self.pool.values():
            if m.id not in reached:
                m.act *= 0.5 ** (1 / self.half_life(m, blocked.get(m.id, 0.0)))
        for i in self.S:
            self.S[i] *= self.p.s_keep
        for m in new:
            if m.id in self.pool:
                self.pool[m.id].act = max(self.pool[m.id].act, m.act)
                self.pool[m.id].last_level = max(self.pool[m.id].last_level, m.last_level)
            elif all(j in self.pool for j in m.parts):
                self.pool[m.id] = m
        self.hole = {i: h for i, h in holes.items() if i in self.pool}
        self.reopen(rec, holes)
        rec["blocked"] = blocked
        self._sweep(rec)
        if self.p.self_feed:   # the pool feeds itself: next tick's percepts include its own output
            gen = [i for i in levels[-1]["winners"] if i in self.pool and self.pool[i].parts]
            gen += [i for i, why in rec["reopened"] if why == "parked" and i in self.pool]
            self.pending = [replace(self.pool[i]) for i in dict.fromkeys(gen)]
        rec["generated"] = [m.id for m in self.pending]
        rec["meta"], rec["ops"], rec["questions"] = [], [], []
        if self.meta:
            self.meta.observe(rec)
        if self.understanding:
            self.understanding.observe(rec)
        rec["phases"] = []
        if self.phases:
            self.phases.observe(rec)
        rec["experiments"] = []
        if self.inquiry:
            self.inquiry.observe(rec)
        self.territory.observe(rec)
        return rec

    def runner_up(self, m, comps, L):
        """The two best learned pulls on m among comps at level L (for "torn"): only partners it has an
        experience record with count, so two untried partners tied on novelty are not a dilemma."""
        ix = self.level_index(comps)
        scores = sorted((p.act * self.force(L, m, p) for p in self.candidates(m, comps, ix)
                         if frozenset((m.id, p.id)) in self.exp[L] and not is_meta(p.id)), reverse=True) + [0.0, 0.0]
        return scores[0], scores[1]

    def readouts(self, lv0):
        """Boredom: mean surprise of the winners. Novelty share: how much of the winners' chosen
        bindings comes from novelty rather than experience or fit."""
        win = [i for i in lv0["winners"] if not is_own(i)]   # the ownership instances carry no surprise
        # of their own (first counted: the mean fell, and the pool read bored)
        boredom = sum(self.S.get(i, 0.0) for i in win) / len(win) if win else 0.0
        shares = []
        for i in win:
            b = lv0["res"][i]
            if b[0] != "partner" or b[1] not in self.pool:
                continue
            m, q = self.pool[i], self.pool[b[1]]
            a = self.exp[0].get(frozenset((i, q.id)), PRIOR)
            nov = self.p.n * info_gain(a) / IG0
            rest = max(self.mu(0, i, q.id), 0.0) + (self.p.T if fills(m, q) or fills(q, m) else 0.0)
            if nov + rest > 0:
                shares.append(nov / (nov + rest))
        return boredom, (sum(shares) / len(shares) if shares else 0.0)

    # ---- the five modulators -----------------------------------------------------------------

    def half_life(self, m, blocked):
        p = self.p
        h = p.h0 * (1 + 0.5 * max(m.last_level, 0)) * (1 + 0.5 * m.c)
        h *= 1 + p.a_success * math.log1p(self.top_wins.get(m.id, 0))   # success
        h *= 1 + p.a_surprise * self.S.get(m.id, 0.0)                     # surprise
        h *= 1 + p.a_novelty * self.novelty(m)                            # novelty
        h *= 1 + p.a_blocked * blocked                                    # blocked momentum
        return h

    @staticmethod
    def signature(m):
        return (m.tags - {m.id}) | set(m.sites) | set(m.parts)

    def novelty(self, m):
        """1 minus the highest Jaccard similarity of its structure to any other configuration.
        Only configurations sharing an element can have a similarity above 0, so they are found
        through an index of signatures by element, rebuilt once per tick."""
        if self._sig_t != self.t:
            self._sigs, self._by_elem = {}, {}
            for x in list(self.pool.values()) + [b["mol"] for i, b in self.boxes.items() if i not in self.pool]:
                self._sigs[x.id] = sig = self.signature(x)
                for e in sig:
                    self._by_elem.setdefault(e, set()).add(x.id)
            self._sig_t = self.t
        sig = self._sigs.get(m.id)
        if sig is None:
            sig = self.signature(m)
        others = len(self._sigs) - (m.id in self._sigs)
        if others == 0:
            return 1.0
        if not sig:   # an empty signature only ties with another empty one
            return 0.0 if any(not s for i, s in self._sigs.items() if i != m.id) else 1.0
        near = set().union(*(self._by_elem.get(e, set()) for e in sig)) - {m.id}
        best = 0.0
        for i in near:
            o = self._sigs[i]
            best = max(best, len(sig & o) / len(sig | o))
        return 1.0 - best

    def blocked(self, rec):
        """Directional energy that hits resistance, and the hole it points at.

        Direction comes from an unfilled site (tension T) or from learned attraction (mu > 0)
        toward a partner the bond could not form with this tick: the partner is absent, or the
        molecule resolved to it but they did not win together. Choosing another partner by argmax
        is not resistance.
        """
        bonded = {pair for _, pair in rec["pairs"]}
        res0 = rec["levels"][0]["res"]
        by_mol = {}
        for recs in self.exp:
            for pair, a in recs.items():
                mu = (a[0] - a[2]) / sum(a)
                if mu > 0:
                    for i in pair:
                        q = next(iter(pair - {i}))
                        if q in self.pool and self.pool[q].bond:
                            continue   # a pull toward a recognition is not a thought reaching for a partner
                        by_mol.setdefault(i, []).append((mu, pair))
        blocked, holes = {}, {}
        for m in self.pool.values():
            b, hole = 0.0, None
            if is_meta(m.id) or is_own(m.id):   # a meta molecule lives by its prediction, an ownership
                continue                          # instance by the territory register: not by momentum
            if m.sites:
                b, hole = self.p.T * len(m.sites), ("site", m.sites[0])
            for mu, pair in by_mol.get(m.id, ()):
                q = next(iter(pair - {m.id}))
                if is_meta(q):   # a thought is not blocked because a thought about it left
                    continue
                resolved = q in self.boxes and q not in self.pool and \
                    any(k <= m.tags for k in self.boxes[q]["keys"])
                resisted = (q not in self.pool and not resolved) or \
                    (res0.get(m.id) == ("partner", q) and pair not in bonded)
                if mu > b and resisted:
                    b, hole = mu, ("partner", q)
            if b > 0:
                blocked[m.id], holes[m.id] = b, hole
        return blocked, holes

    # ---- storage: boxes, keys as sites, warmth ------------------------------------------------
    #
    # A box is a closed thought out of the pool. Its keys are sites: each key is a set of tags, and
    # a winner (or two winners bound together) fills it if it carries all of them. Each key has a
    # warmth that halves every h_site ticks it goes unfilled; below `cold` it is no longer checked.

    @staticmethod
    def as_key(k):
        return frozenset((k,)) if isinstance(k, str) else frozenset(k)

    def new_box(self, m, keys=(), told=False, parked=False, sites=(), needs=(), predicts=None,
                rationalized=False, warmth=None):
        keys = [self.as_key(k) for k in keys]
        last = {}
        for k in keys:
            w = (warmth or {}).get(k, 1.0)
            last[k] = self.t - self.p.h_site * math.log2(1 / w) if w > 0 else -math.inf
        b = dict(mol=replace(m, sites=()), keys=last, told=told, parked=parked, sites=tuple(sites),
                 needs=tuple(needs), predicts=predicts, rationalized=rationalized, seen={},
                 last_resonant=self.t if not parked else -math.inf)
        self.boxes[m.id] = b
        for k in keys:
            self.index.setdefault(min(k), set()).add(m.id)
        for t in m.tags:
            self.mol_index.setdefault(t, set()).add(m.id)
        return b

    def warm(self, b, k):
        return 0.5 ** ((self.t - b["keys"][k]) / self.p.h_site) >= self.p.cold

    def box(self, m, keys, warmth=None, predicts=None):
        """Put a closed thought straight into storage (for scenarios)."""
        b = self.new_box(m, keys, warmth={self.as_key(k): w for k, w in (warmth or {}).items()}, predicts=predicts)
        b["last_resonant"] = -math.inf
        return b

    def tell(self, m, needs=(), predicts=None):
        """A told clause: a box that arrives already closed, with no keys of the person's own."""
        return self.new_box(m, (), told=True, needs=needs, predicts=predicts)

    def experience(self, m, needs):
        """Something happens to the person (sec. 5d). New: it arrives told and is decomposed at once,
        open on its needs. Boxed but rationalized (closed on a bad key, never understood), or its
        needs never filled (no keys of its own, e.g. the pool was cleared while it was open): it
        re-opens on its sites or needs, the question is back. A thought with open needs does not
        settle (the user, 2026-10-22). Understood or settled: perceived as usual."""
        b = self.boxes.get(m.id)
        if m.id in self.pool:
            self.present(m)
        elif b is None:
            self.tell(m, needs=needs)
            self.decompose(m.id)
        elif b.get("rationalized") or (b["needs"] and not b["keys"]):
            self.pool[m.id] = replace(b["mol"], sites=b["sites"] or b["needs"], act=1.0)
            b["rationalized"] = False
        else:
            self.present(m)

    def decompose(self, id):
        """Open a box as a molecule whose open sites are what it would have to be bonded from."""
        b = self.boxes[id]
        self.pool[id] = replace(b["mol"], sites=b["needs"] or b["sites"], act=1.0)
        b["told"] = False

    def park(self, rec, blocked):
        """A thought blocked with too many holes for too long is boxed on its questions: its keys
        are its open sites, and the pool is free again."""
        for i in list(self.pool):
            m = self.pool[i]
            if len(m.sites) >= self.p.park_holes and blocked.get(i, 0.0) > 0:
                self.blocked_for[i] = self.blocked_for.get(i, 0) + 1
            else:
                self.blocked_for[i] = 0
            if self.blocked_for[i] >= self.p.park_after:
                self.new_box(m, m.sites, parked=True, sites=m.sites)
                del self.pool[i]
                self.blocked_for[i] = 0
                rec["parked"].append(i)

    def close(self, rec, blocked):
        """A thought whose opening (last tick's hole) is resolved while it holds a slot
        crystallizes into a box, keyed by what resolved it, and leaves the tournament.

        Rationalization: an open thought bound to a co-winning partner that does not fit, with a
        binding score of at least `rationalize`, closes anyway, keyed by that partner."""
        bonded = {pair for _, pair in rec["pairs"]}
        sc0, res0 = rec["levels"][0]["scores"], rec["levels"][0]["res"]
        filled_by = {}
        for j, f in rec["filled"]:
            filled_by.setdefault(j, set()).add(f)
        for i, hole in list(self.hole.items()):
            if i not in self.pool or i not in rec["reached"]:
                continue
            m = self.pool[i]
            rational = False
            if blocked.get(i, 0.0) > 0:
                b = res0.get(i, ("none",))
                # a partner that filled one of its sites this tick is a fit, not a rationalization
                fit = b[0] == "partner" and b[1] in self.pool and \
                    (b[1] in filled_by.get(i, ()) or fills(self.pool[b[1]], m))
                if not (self.p.rationalize is not None and m.sites and b[0] == "partner"
                        and b[1] in self.pool   # the partner may have closed earlier this tick
                        and not is_meta(b[1])   # a thought about the question is not an answer to it
                        and not is_sov(i) and not is_sov(b[1]) and not is_phase(i) and not is_phase(b[1])
                        and (self.understanding is None or self.understanding.level(concept_of(b[1]) or b[1]) >= 0.5)
                        and frozenset((i, b[1])) in bonded and not fit
                        and sc0.get(i, 0.0) >= self.p.rationalize):
                    continue
                rational = True
            keys = {q for _, pair in rec["pairs"] if i in pair for q in pair - {i} if not is_meta(q) and not is_sov(q) and not is_phase(q)}   # a thought about X is not what resolved X
            keys |= {f for j, f in rec["filled"] if j == i} | self.fillers.pop(i, set())
            if hole[0] == "partner":
                keys.add(hole[1])
            old = self.boxes.get(i, {})
            self.new_box(m, keys or {i}, sites=m.sites if rational else (), rationalized=rational,
                         predicts=old.get("predicts"), needs=old.get("needs", ()))
            del self.pool[i]
            rec["closed"].append((i, "rationalized") if rational else i)

    def settled(self, rec, blocked):
        """A thought with no hole that keeps winning on past precision is finished: once it has won
        `dwell` ticks running with its precision flat (nothing left to learn from what follows
        it), it precipitates into a box keyed by what it was winning with, and leaves the pool.
        Perceived again, it stays there; a hole, recognition or contradiction brings it back."""
        for i in list(self.pool):
            m = self.pool[i]
            if m.sites or i in blocked or i not in rec["reached"] or self.streak.get(i, 0) < self.p.dwell:
                continue
            if is_meta(i) or is_phase(i) or (self.meta and self.meta.split_record(i)):   # metas live by prediction;
                continue                                                   # a split record has more to learn
            if self.pi_delta.get(i, math.inf) >= self.p.flat:   # its precision is still moving
                continue
            keys = {q for _, pair in rec["pairs"] if i in pair for q in pair - {i} if not is_meta(q) and not is_sov(q) and not is_phase(q)}   # a thought about X is not what resolved X
            self.new_box(m, keys or {i})["settled"] = True
            del self.pool[i]
            rec["settled"].append(i)

    def bring_back(self, rec, i, act, why, sites=()):
        b = self.boxes[i]
        self.pool[i] = replace(b["mol"], act=act, sites=sites)
        if sites:   # back with its holes open: it has a hole now, so filling them can close it
            self.hole[i] = ("site", sites[0])
        rec["reopened"].append((i, why))

    def reopen(self, rec, holes):
        """Boxes re-open through recognition. Ordinary boxes: at least `resonance` of their keys
        filled by this tick's winners, after having gone out of resonance since closing. Parked
        boxes: keys accumulate over time; when enough have been filled, the box re-opens with its
        sites open and the clauses that filled them come back with it. Told boxes have no keys.
        A blocked thought's hole also searches the boxes (through warm keys only)."""
        reached = [i for i in rec["reached"] if i in self.pool]
        fills_ = [(self.pool[i].tags, (i,)) for i in reached]
        # a settled thought perceived again stays in storage but is recognized: it fills keys too
        fills_ += [(self.boxes[i]["mol"].tags, (i,)) for i in self.perceived
                   if i in self.boxes and self.boxes[i].get("settled") and i not in self.pool]
        fills_ += [(self.pool[a].tags | self.pool[b].tags, (a, b)) for _, pair in rec["pairs"]
                   for a, b in [tuple(pair)] if a in self.pool and b in self.pool]
        cand = set()
        for tags, _ in fills_:
            for t in tags:
                cand |= self.index.get(t, set())
        for i in sorted(cand):
            b = self.boxes.get(i)
            if b is None or i in self.pool or not b["keys"]:
                continue
            hit = {}
            for k in b["keys"]:
                if not self.warm(b, k):
                    continue
                for tags, who in fills_:
                    if k <= tags:
                        hit[k] = who
                        break
            for k in hit:
                b["keys"][k] = self.t
            if b["parked"]:
                for k, who in hit.items():
                    b["seen"][k] = [replace(self.pool[w] if w in self.pool else self.boxes[w]["mol"]) for w in who]
                if len(b["seen"]) / len(b["keys"]) >= self.p.resonance:
                    self.bring_back(rec, i, 1.0, "parked", sites=b["sites"])
                    for ms in b["seen"].values():
                        for f in ms:
                            self.present(f)
                    b["seen"] = {}
                continue
            r = len(hit) / len(b["keys"])
            if r >= self.p.resonance:
                if b["last_resonant"] < self.t - 1:
                    self.bring_back(rec, i, r, "resonance")
                b["last_resonant"] = self.t
        for i, (kind, target) in holes.items():
            if kind == "partner":
                found = {target} if target in self.boxes else set()
            else:
                found = set(self.mol_index.get(target, set()))
            for j in sorted(found):
                b = self.boxes[j]
                if j in self.pool or b["told"] or not any(self.warm(b, k) for k in b["keys"]):
                    continue
                self.bring_back(rec, j, 1.0, f"hole of {i}")

    def contradict(self, ids):
        """The world opening a box from outside: a box predicts `expect` whenever its `when` tags
        were among last tick's winners. If the world answers and `expect` is not in it, the box
        re-opens with its holes (original sites, or what it would need) and full surprise."""
        for i, b in self.boxes.items():
            pr = b["predicts"]
            if not pr or i in self.pool:
                continue
            when, expect = pr
            if frozenset(when) <= self.prev_tags and expect not in ids:
                self.pool[i] = replace(b["mol"], act=1.0, sites=b["sites"] or b["needs"])
                b["told"] = False
                u = self.understanding.level(concept_of(i) or i) if self.understanding else 1.0
                self.S[i] = 0.5 + 0.5 * u
                self.contradicted.append(i)

    # ---- conversation ----------------------------------------------------------------------------

    def say(self, id, show_keys=True):
        """What passes is the clause; showing your work hands over the keys too."""
        b = self.boxes[id]
        keys = sorted(t for k in b["keys"] for t in k) if show_keys and not b["told"] else None
        return replace(b["mol"]), keys

    def hear(self, m, keys=None):
        """With keys visible, the clause enters the pool open on them, to be bonded; without, it is
        stored as a told box."""
        if keys:
            if self.meta:
                m = self.meta.distinguish(m)
            self.pool[m.id] = replace(m, sites=tuple(keys), act=1.0)
            if self.understanding and concept_of(m.id):
                for k in keys:
                    self.understanding.add(concept_of(m.id), "co_occurs", k, "told")
        else:
            self.tell(m)

    def _sweep(self, rec):
        for i in [i for i, m in self.pool.items() if m.act < self.p.floor]:
            rec["removed"].append(i)
            del self.pool[i]
        changed = True
        held = {m.id for m in self.facts.values()}
        while changed:   # composites come apart when a part is gone (in storage or the facts register is not gone)
            changed = False
            for i in [i for i, m in self.pool.items()
                      if m.parts and any(j not in self.pool and j not in self.boxes and j not in held for j in m.parts)]:
                rec["removed"].append(i)
                del self.pool[i]
                changed = True

    def learn(self, rec, outcome):
        """outcome > 0 good, 0 neutral, < 0 bad. Credits every pair bound and co-winning at a level.

        Adding a Dirichlet count moves the pair's predicted outcome by its prediction error / (total + 1).
        """
        k = 0 if outcome > 0 else (2 if outcome < 0 else 1)
        o = (outcome > 0) - (outcome < 0)
        for L, pair in rec["pairs"]:
            a, b = tuple(pair)
            err = abs(o - self.mu(L, a, b)) / 2   # surprise of what it generated
            for i in (a, b):
                self.S[i] = max(self.S.get(i, 0.0), err)
            self.record(L, a, b)[k] += 1
        if self.meta:
            self.meta.outcome(rec, outcome)
        if self.phases:
            self.phases.last_outcome = outcome

    def tick(self, inputs=(), outcome=0):
        """Mind alone, no world: present inputs (and its own output from last tick), think, learn."""
        world = [m.id for m in inputs]
        inputs = list(inputs) + self.pending
        self.pending = []
        self.perceive([m.id for m in inputs])
        if world:
            self.contradict(world)
        for m in inputs:
            self.present(m)
        rec = self.think()
        self.learn(rec, outcome)
        return rec

    def top(self, rec):
        return rec["levels"][-1]["winners"]


def is_meta(id):
    return id.startswith("meta:")


def is_sov(id):
    return id.startswith("sov:") or id.startswith("q:")


def is_phase(id):
    return id.startswith("phase:")


def is_exp(id):
    return id.startswith("exp:")


def is_own(id):
    """The ownership SOV's slot instances and their questions (REORG.md): own:<kind>:<region>,
    own:q:<kind>:<region>."""
    return id.startswith("own:")


def concept_of(id):
    """The concept a clause is an instance of: the clause itself, or the parent of a split half.
    SOV molecules, questions, meta molecules, bonds and composites are not instances."""
    if is_meta(id) or is_sov(id) or is_phase(id) or is_exp(id) or is_own(id) or id.startswith("[") or "~" in id:
        return None
    return id.split("|")[0]


class Meta:
    """The meta layer: processing states become molecules (ABI's meta-receptors; SOV's Quote; the
    reflection tower's first rung), coupled to the rest only through the pool (the federation law).

    Each meta molecule is formed from the base event stream, is about one subject (a molecule, or
    the pool), and carries a prediction about the base's dynamics. It earns its existence by that
    prediction (the mirror trap: a meta level funded by copying the base is rent without yield):
    confirmed within `meta_horizon` ticks, it is refreshed and predicts again; refuted, it is
    dropped. An operation on its subject fires only when the meta molecule wins a top slot
    (capability without receptor is latent).

    kind         formed when                                predicts                          operation
    stuck        subject blocked 3 ticks running            still open at the deadline         park it
    looping      blocked and at the top 3 of the last 5     at the top again                   park it
    wrong        a box of the subject was contradicted      not re-closed on the same keys     -
    torn         its top binding nearly tied (within 5%)    its top binding flips              -
    surprised    surprise >= 0.8 while it holds a slot      another event involving it         -
    resolved     it closed                                  not re-opened                      -
    bored        mean surprise of winners < 0.05, 5 ticks   no events                          novelty doubled 5 ticks
    conflated    its outcomes bimodal (good and bad both    a boundary splits it into two      differentiate it
                 >= 2, the minority >= 25%)                  predictable halves
    distinction  both halves of a split unimodal (>= 80%)   they stay unimodal                 the conflation is closed
    same         both halves' good rates within 0.15        they stay matched                  unify the halves
    """
    KINDS = ("stuck", "looping", "wrong", "torn", "surprised", "resolved", "bored",
             "conflated", "distinction", "same")
    OPERATES = ("stuck", "looping", "bored", "conflated", "distinction", "same")   # the kinds with an operation

    def __init__(self, mind):
        self.mind = mind
        self.about = {}       # meta id -> subject id
        self.watch = {}       # meta id -> (kind, subject, deadline, state)
        self.earned = {}      # meta id -> [confirmed, refuted]
        self.stuck = {}       # molecule -> consecutive blocked ticks
        self.tops = []        # top winners of recent ticks
        self.flat = 0         # consecutive ticks with flat surprise
        self.seen_contra = 0  # how much of mind.contradicted has been read
        self.events = []      # (tick, subject) of base events, for the predictions
        self.outcomes = {}    # molecule -> [(tick, context tags, +1/-1)]
        self.splits = {}      # parent -> dict(tag, yes, no, t, parent molecule)
        self.parent = {}      # child -> parent
        self.log = []         # (tick, what, meta id): formed, confirmed, refuted, op
        self.no_boundary = {}  # molecule -> its outcome count when a conflation search last found no boundary
        self.unexplained = set()   # concepts conflated with no boundary in the situation (a hidden cause?)
        self.modes = {}       # molecule -> [(tick, context tags, mode)]: outcomes that are not good or bad
        # but one of several kinds (what an action did, 2026-10-23); conflation is two kinds both likely

    # ---- forming ------------------------------------------------------------------------------

    def depth(self, id):
        return id.count("meta:")

    def about_pair(self, a, b):
        return self.about.get(a) == b or self.about.get(b) == a

    def emit(self, kind, subject, rec, state=None):
        if self.depth(subject) >= self.mind.p.meta_depth or kind in self.mind.p.meta_off:
            return
        mid = f"meta:{kind}:{subject}"
        if mid in self.watch:   # already standing: it lives by its prediction, not by being re-seen
            return
        self.mind.present(clause(mid, tags=("meta", kind, f"about:{subject}")))
        self.about[mid] = subject
        self.watch[mid] = (kind, subject, self.mind.t + self.mind.p.meta_horizon, state)
        self.earned.setdefault(mid, [0, 0])
        self.log.append((self.mind.t, "formed", mid))
        rec["meta"].append(mid)

    def observe(self, rec):
        """After a tick: fire the operations whose meta molecules won the top, score predictions,
        then form new meta molecules from this tick's events."""
        mind = self.mind
        top = rec["levels"][-1]["winners"]
        for mid in [i for i in top if is_meta(i) and i in self.watch]:
            self.operate(mid, rec)
        for i in {c if isinstance(c, str) else c[0] for c in rec["closed"]} | {i for i, _ in rec["reopened"]} \
                | {i for i, _ in rec["filled"]}:
            self.events.append((mind.t, i))
        self.check(rec)
        blocked = rec["blocked"]
        self.tops = (self.tops + [set(top)])[-5:]
        for i in list(mind.pool):
            # these live by their own registers, not by momentum: SOV molecules and phases; experiments
            # (pursued through action, as a want is); and a question an experiment can answer (the
            # parking rule: park only when nothing could fill the hole). First they were parked as
            # stuck, and a parked question, still standing, was never asked again: inquiry stalled
            if i.startswith("sov:") or is_phase(i) or is_exp(i) or is_own(i) or (is_sov(i) and self.answerable(i)):
                continue
            self.stuck[i] = self.stuck.get(i, 0) + 1 if blocked.get(i, 0) > 0 else 0
            if self.stuck[i] == 3:
                self.emit("stuck", i, rec)
            if blocked.get(i, 0) > 0 and sum(i in t for t in self.tops) >= 3 and len(self.tops) == 5:
                self.emit("looping", i, rec)
        for i in mind.contradicted[self.seen_contra:]:
            keys = frozenset(mind.boxes[i]["keys"]) if i in mind.boxes else frozenset()
            self.emit("wrong", i, rec, state=keys)
        self.seen_contra = len(mind.contradicted)
        if len(rec["levels"]) > 1:
            comps = [mind.pool[i] for i in rec["levels"][-2]["winners"] if i in mind.pool]
            for i in top:
                if i in mind.pool and not is_meta(i):
                    best, second = mind.runner_up(mind.pool[i], comps, len(rec["levels"]) - 1)
                    if best > 0 and second > 0 and best - second < 0.05 * best:
                        self.emit("torn", i, rec, state=rec["levels"][-1]["res"].get(i))
        for i in rec["reached"]:   # the surprise it arrived with (before this tick's decay)
            if max(mind.S.get(i, 0.0), mind.S_prev.get(i, 0.0)) >= 0.8:
                self.emit("surprised", i, rec)
        for c in rec["closed"]:
            self.emit("resolved", c if isinstance(c, str) else c[0], rec)
        self.flat = self.flat + 1 if rec["boredom"] < 0.05 else 0
        if self.flat == 5:
            self.emit("bored", "pool", rec)
        # meta molecules fade by their half-life whether or not they win their slots; a confirmed
        # prediction refreshes them (settle). First they did not decay while winning, and old ones
        # held the meta track: a new conflation never won the top.
        for mid in list(self.watch):
            if mid in mind.pool:
                mind.pool[mid].act *= 0.5 ** (1 / mind.p.h0)

    def answerable(self, q):
        """A question an experiment could answer now (the mind has inquiry, and it suggests one)."""
        inq, und = self.mind.inquiry, self.mind.understanding
        if inq is None or und is None or q not in und.questions:
            return False
        c, r = und.questions[q]
        return bool(inq.suggest(r, c))

    # ---- earning ------------------------------------------------------------------------------

    def holds(self, kind, subject, state, rec, final):
        """True: confirmed now. False: refuted. None: not yet decided."""
        mind, t = self.mind, self.mind.t
        since = [i for (u, i) in self.events if i == subject]
        if kind == "stuck":
            if subject in mind.boxes and subject not in mind.pool and not mind.boxes[subject].get("parked"):
                return False                                   # it closed: not stuck after all
            return True if final else None
        if kind == "looping":
            return True if subject in rec["levels"][-1]["winners"] else (False if final else None)
        if kind == "wrong":
            b = mind.boxes.get(subject)
            if b is not None and subject not in mind.pool and frozenset(b["keys"]) == state:
                return False                                   # closed again on the same keys
            return True if final else None
        if kind == "torn":
            now = rec["levels"][-1]["res"].get(subject)
            return True if now is not None and now != state else (False if final else None)
        if kind == "surprised":
            return True if since else (False if final else None)
        if kind == "resolved":
            return False if subject in mind.pool else (True if final else None)
        if kind == "bored":
            return False if rec["closed"] or rec["reopened"] or rec["filled"] else (True if final else None)
        return None   # conflated, distinction, same: decided by outcomes (see outcome)

    def check(self, rec):
        for mid, (kind, subject, deadline, state) in list(self.watch.items()):
            if mid not in self.mind.pool:   # faded out: archived, so it can form again later
                del self.watch[mid]
                continue
            v = self.holds(kind, subject, state, rec, self.mind.t >= deadline)
            if v is not None:
                self.settle(mid, v)
        self.events = [(u, i) for (u, i) in self.events if u > self.mind.t - self.mind.p.meta_horizon]

    def settle(self, mid, ok):
        """A prediction decided: confirmed, the meta molecule is refreshed and predicts again;
        refuted, it is dropped (it earned nothing)."""
        kind, subject, _, state = self.watch[mid]
        self.earned[mid][0 if ok else 1] += 1
        self.log.append((self.mind.t, "confirmed" if ok else "refuted", mid))
        if not self.mind.p.meta_funding:
            self.watch[mid] = (kind, subject, self.mind.t + self.mind.p.meta_horizon, state)
            return
        if ok:
            if mid in self.mind.pool:
                self.mind.pool[mid].act = 1.0
            self.watch[mid] = (kind, subject, self.mind.t + self.mind.p.meta_horizon, state)
        else:
            self.mind.remove(mid)
            del self.watch[mid]

    # ---- operating ----------------------------------------------------------------------------

    def operate(self, mid, rec):
        kind, subject, _, _ = self.watch[mid]
        mind, done = self.mind, None
        if kind in ("stuck", "looping") and subject in mind.pool:
            m, hole = mind.pool[subject], mind.hole.get(subject)
            keys = m.sites or ((hole[1],) if hole else ())
            und = mind.understanding
            if und and mind.inquiry and subject in und.questions:   # with inquiry, a question is keyed
                keys = (und.questions[subject][0],)   # by its concept: back when an instance of it is
                # attended again, an experiment may answer it then (first by its own site, which nothing
                # else carries: never back; without inquiry, nothing could answer it then either)
            if keys and self.parkable(m, keys):
                mind.new_box(m, keys, parked=True, sites=m.sites)
                del mind.pool[subject]
                rec["parked"].append(subject)
                done = "parked"
        elif kind == "conflated":
            done = "differentiated" if self.differentiate(subject, rec=rec) else "no boundary"
            if done == "no boundary":   # it may form again only after four more outcomes
                self.no_boundary[subject] = len(self.outcomes.get(subject, []) or self.modes.get(subject, []))
                self.unexplained.add(concept_of(subject) or subject)   # nothing in the situation splits it:
                self.settle(mid, False)                                # what is left to vary is the moment
        elif kind == "distinction":
            c = f"meta:conflated:{subject}"
            if c in self.watch:
                self.settle(c, True)
                mind.remove(c)
                del self.watch[c]
            done = "conflation closed"
        elif kind == "same":
            done = "unified" if self.unify(subject) else None
        elif kind == "bored":
            mind.boost_until = mind.t + 5
            done = "novelty doubled"
        if done:
            rec["ops"].append((mid, done))
            self.log.append((mind.t, f"op:{done}", mid))

    def parkable(self, m, keys):
        """Parking is for questions there is nothing to work with right now (the user, 2026-10-22):
        never a want (tagged "goal": pursued through action, not set aside), and never while some
        thought in the pool, the facts register or storage carries what one of its holes needs."""
        if "goal" in m.tags or is_exp(m.id) or is_own(m.id) or (is_sov(m.id) and self.answerable(m.id)):
            return False   # (and never an experiment, or a question an experiment can answer: also
        mind = self.mind   # pursued through action; first only checked when stuck was formed)
        near = [x for x in mind.pool.values() if x.id != m.id and not is_meta(x.id)]
        near += list(mind.facts.values())
        near += [b["mol"] for i, b in mind.boxes.items() if i not in mind.pool and not b.get("told")]
        for k in keys:
            if any(k in x.tags for x in near):
                return False
        return True

    # ---- conflation: differentiate, distinction, unify -------------------------------------------

    def context(self, rec, i):
        """The situation an outcome happened in: the facts register and what was perceived this tick
        (first: everything holding a slot, so leftovers from earlier episodes and meta, SOV and
        question molecules were read as the situation)."""
        mind = self.mind
        tags = set().union(*(m.tags for m in mind.facts.values()))
        for j in mind.perceived:
            if j != i and not is_meta(j) and not is_sov(j):
                m = mind.pool.get(j) or (mind.boxes[j]["mol"] if j in mind.boxes else None)
                tags |= m.tags if m is not None else {j}
        own = mind.pool[i].tags if i in mind.pool else {i}
        return frozenset(tags - own)

    def split_record(self, i):
        """Its outcomes still go both ways (the minority at least a quarter): not finished."""
        g, b = self.rate(self.outcomes.get(i, []))
        return g >= 1 and b >= 1 and min(g, b) / (g + b) >= 0.25

    @staticmethod
    def rate(hist):
        good = sum(1 for _, _, o in hist if o > 0)
        return good, len(hist) - good

    def outcome(self, rec, outcome):
        """Record a good or bad outcome against every non-meta molecule that held a slot, with what
        else was present (the context); then look for conflation, distinctions and collapses."""
        if outcome == 0:
            return
        o = 1 if outcome > 0 else -1
        # an outcome belongs to what arrived with it: what was perceived this tick, read as the half
        # of a split the situation selects (in the pool, or settled in storage); first: every thought
        # holding a slot, so noise and leftovers from earlier episodes looked conflated
        credited = []
        for i in sorted(self.mind.perceived):
            if is_meta(i) or is_sov(i):
                continue
            j = self.reading(i)
            m = self.mind.pool.get(j)
            b = self.mind.boxes.get(j)
            if (m is not None and not m.bond) or (m is None and b is not None and b.get("settled")):
                if j not in credited:
                    credited.append(j)
        for i in credited:
            self.outcomes.setdefault(i, []).append((self.mind.t, self.context(rec, i), o))
        for i, hist in self.outcomes.items():
            if i in self.splits or i not in self.mind.pool:
                continue
            g, b = self.rate(hist)
            if g >= 2 and b >= 2 and min(g, b) / (g + b) >= 0.25 and len(hist) >= self.no_boundary.get(i, -4) + 4:
                self.emit("conflated", i, rec)
        for parent, sp in self.splits.items():
            ys = [h for h in self.outcomes.get(sp["yes"], []) if h[0] >= sp["t"]]
            ns = [h for h in self.outcomes.get(sp["no"], []) if h[0] >= sp["t"]]
            (gy, by), (gn, bn) = self.rate(ys), self.rate(ns)
            uni = lambda g, b: g + b >= 2 and max(g, b) / (g + b) >= 0.8
            if uni(gy, by) and uni(gn, bn) and (gy > by) != (gn > bn):
                self.emit("distinction", parent, rec, state=(self.mind.t, gy > by, gn > bn))
            if gy + by >= 3 and gn + bn >= 3 and abs(gy / (gy + by) - gn / (gn + bn)) < 0.15:
                self.emit("same", parent, rec)
        # a distinction predicts that each half keeps its sign: judged only on outcomes after it formed
        for mid, (kind, subject, _, state) in list(self.watch.items()):
            if kind != "distinction" or subject not in self.splits or mid not in self.mind.pool:
                continue
            t0, yes_good, no_good = state
            sp = self.splits[subject]
            new = [(o > 0) == yes_good for t, _, o in self.outcomes.get(sp["yes"], []) if t > t0]
            new += [(o > 0) == no_good for t, _, o in self.outcomes.get(sp["no"], []) if t > t0]
            if new:
                self.settle(mid, all(new))

    def observe_mode(self, subject, mode, context, rec):
        """An outcome of a kind rather than a sign: what an action did this time (its mode: the changes
        that followed it), in the situation it was done in. Recorded against the reading of the subject
        the situation selects. Two outcomes in opposition, both likely, are a change that came in some
        of its tries and not in others (each way twice or more, the lesser at least a quarter): the
        subject is conflated (DRIFT.md: the meta layer's split; first written outside it as a
        conditions search in the force agent; then judged on whole outcomes, and a gust's flag swing,
        in some outcomes and not others, made every outcome a different one)."""
        x = self.reading_in(subject, context)

        def judgeable(hist):   # the tags with at least two outcomes on each side (a boundary can be read)
            tags = set().union(*(h[1] for h in hist)) if hist else set()
            return {c for c in tags if sum(c in h[1] for h in hist) >= 2 and sum(c not in h[1] for h in hist) >= 2}
        was = judgeable(self.modes.get(x, []))
        self.modes.setdefault(x, []).append((self.mind.t, frozenset(context), frozenset(mode)))
        novel = bool(judgeable(self.modes[x]) - was)   # new evidence: a tag that can now be judged
        if self.mind.understanding:   # an outcome, confirming or not: the investigation has momentum
            self.mind.understanding.progress[subject] = 1.0
        # sought again after a failed search when 4 more outcomes have come, or at once when an outcome
        # makes a tag judgeable (two each side): new evidence (first after 4 only, and a push tried 6
        # times never had its boundary sought again after a search at its 4th, too early to see the arm's
        # part)
        if self.opposed(self.modes[x]) and x not in self.splits                 and (len(self.modes[x]) >= self.no_boundary.get(x, -4) + 4 or (novel and x in self.no_boundary)):
            self.emit("conflated", x, rec)
        return x

    @staticmethod
    def opposed(hist):
        """The changes that came in some outcomes and not in others, both ways likely."""
        n = len(hist)
        out = []
        for e in sorted(set().union(*(h[2] for h in hist))) if hist else ():
            k = sum(1 for h in hist if e in h[2])
            if k >= 2 and n - k >= 2 and min(k, n - k) / n >= 0.25:
                out.append(e)
        return out

    def mode_boundary(self, hist):
        """The context tag that best separates an opposed change's presence from its absence (at least
        two outcomes each side; one side 75% one way, the two 0.5 apart), over the opposed changes; a
        change no tag separates (a hidden driver's) gives none. None if no change has one."""
        best = None
        for e in self.opposed(hist):
            for c in sorted(set().union(*(ctx for _, ctx, _ in hist))):
                yes = [e in m for _, ctx, m in hist if c in ctx]
                no = [e in m for _, ctx, m in hist if c not in ctx]
                if len(yes) < 2 or len(no) < 2:
                    continue
                py, pn = sum(yes) / len(yes), sum(no) / len(no)
                # one side predictable (75% one way) and the sides clearly apart (rates 0.5 or more
                # apart): the mixed side stays conflated and is split again on its own (first: both
                # sides predictable, and an AND, half lit on either plug alone, had no boundary)
                if max(max(py, 1 - py), max(pn, 1 - pn)) >= 0.75 and abs(py - pn) >= 0.5:
                    purity = max(py, 1 - py) + max(pn, 1 - pn)
                    if best is None or purity > best[0]:
                        best = (purity, c)
        return best[1] if best else None

    def reading_in(self, id, context):
        """The reading of id in a given situation (its context tags), through nested splits."""
        while id in self.splits:
            sp = self.splits[id]
            id = sp["yes"] if sp["tag"] in context else sp["no"]
        return id

    def boundary(self, hist):
        """The context tag that best separates good from bad outcomes into two predictable halves
        (each at least 75% one way, opposite ways, at least two outcomes each), or None."""
        tags = sorted(set().union(*(ctx for _, ctx, _ in hist)))
        best = None
        for c in tags:
            yes = [o for _, ctx, o in hist if c in ctx]
            no = [o for _, ctx, o in hist if c not in ctx]
            if len(yes) < 2 or len(no) < 2:
                continue
            py, pn = sum(o > 0 for o in yes) / len(yes), sum(o > 0 for o in no) / len(no)
            purity = max(py, 1 - py) + max(pn, 1 - pn)
            if max(py, 1 - py) >= 0.75 and max(pn, 1 - pn) >= 0.75 and (py > 0.5) != (pn > 0.5):
                if best is None or purity > best[0]:
                    best = (purity, c)
        return best[1] if best else None

    def differentiate(self, x, tag=None, rec=None):
        """Split x on the boundary tag: two new molecules, x when the tag is present and x when it is
        not, carrying x's tags (so they fill what x filled) and its sites; x's outcomes are
        partitioned between them. Returns False when no boundary separates the outcomes."""
        mind = self.mind
        modes = x in self.modes and not self.outcomes.get(x)
        hist = self.modes[x] if modes else self.outcomes.get(x, [])
        tag = tag or (self.mode_boundary(hist) if modes else self.boundary(hist))
        if tag is None or x in self.splits:
            return False
        src = mind.pool.get(x) or (mind.boxes[x]["mol"] if x in mind.boxes else None)
        if src is None:
            return False
        yes = replace(src, id=f"{x}|{tag}", tags=src.tags | {x})
        no = replace(src, id=f"{x}|not_{tag}", tags=src.tags | {x})
        self.splits[x] = dict(tag=tag, yes=yes.id, no=no.id, t=mind.t, parent=replace(src), mols=(yes, no))
        if mind.understanding:   # the boundary conditions x: worked out by the pool; and x's own
            mind.understanding.add(concept_of(tag) or tag, "conditions", x, "worked")   # conditions slot
            if mind.inquiry:   # holds it, in an acting mind (first only under the tag, so the split
                mind.understanding.add(concept_of(x) or x, "conditioned_by", tag, "worked")  # concept's
            # slot stayed empty and its question, which an experiment could answer, never closed)
            und = mind.understanding   # what brings the boundary about has a role in x (the cable's push
            for k, rels in list(und.rel.items()) if mind.inquiry else ():   # in the press; first no role was
                if k != x and und.rel[k].get(("causes", tag)):   # ever written for an action, and its slot
                    und.add(k, "role", x, "worked")              # drew attention forever; an acting mind's)
        self.parent[yes.id] = self.parent[no.id] = x
        (self.modes if modes else self.outcomes)[yes.id] = [h for h in hist if tag in h[1]]
        (self.modes if modes else self.outcomes)[no.id] = [h for h in hist if tag not in h[1]]
        if modes and rec is not None:   # a half still mixed is conflated in turn, now (first only when a
            for half in (yes.id, no.id):   # new outcome came for it, and an AND's half waited forever)
                if self.opposed(self.modes[half]):
                    self.emit("conflated", half, rec)
        if x in mind.pool:
            act = mind.pool.pop(x).act
            mind.present(src, act)          # comes back as whichever half the present context selects
        return True

    def here(self):
        """The situation a split thought is read in: the facts register and what is perceived this
        tick (first: everything in the pool, so a condition left over from an earlier episode
        selected the wrong half)."""
        mind = self.mind
        tags = set().union(*(f.tags for f in mind.facts.values()))
        for j in mind.perceived:
            m = mind.pool.get(j) or (mind.boxes[j]["mol"] if j in mind.boxes else None)
            tags |= m.tags if m is not None else {j}
        return tags

    def reread(self):
        """Each tick a distinction reads the present context again: a half in the pool whose
        condition no longer holds is replaced by the other half (keeping its activation)."""
        for parent, sp in self.splits.items():
            yes, no = sp["mols"]
            here = self.here() - yes.tags - no.tags
            right, wrong = (yes, no) if sp["tag"] in here else (no, yes)
            if wrong.id in self.mind.pool:
                old = self.mind.pool.pop(wrong.id)
                if right.id not in self.mind.pool:
                    self.mind.pool[right.id] = replace(right, act=old.act, sites=old.sites)

    def reading(self, id):
        """The id a perceived clause is read as: itself, or the half of its split the context selects
        (and the half of that half's split: a half can be split again)."""
        while id in self.splits:
            sp = self.splits[id]
            yes, no = sp["mols"]
            id = yes.id if sp["tag"] in self.here() - yes.tags - no.tags else no.id
        return id

    def distinguish(self, m):
        """A molecule that has been split is perceived as the half the present context selects (through
        nested splits)."""
        out = m
        while out.id in self.splits:
            sp = self.splits[out.id]
            yes, no = sp["mols"]
            out = yes if sp["tag"] in self.here() - yes.tags - no.tags else no
        return m if out is m else replace(out, act=m.act, sites=m.sites)

    def unify(self, x):
        """The halves of a split behave alike: merge them back into x, pooling their outcomes."""
        sp = self.splits.pop(x, None)
        if sp is None:
            return False
        act = 0.0
        for c in (sp["yes"], sp["no"]):
            if c in self.mind.pool:
                act = max(act, self.mind.pool.pop(c).act)
            self.mind.boxes.pop(c, None)   # the distinction no longer exists: its halves leave storage too
            self.parent.pop(c, None)
        self.outcomes[x] = self.outcomes.pop(sp["yes"], []) + self.outcomes.pop(sp["no"], [])
        if act:
            self.mind.pool[x] = replace(sp["parent"], act=act)
        return True


class Understanding:
    """The understanding register (THOUGHT_MOLECULES.md sec. 5g): per concept its SOV, the relations
    worked out so far, each with receipts by provenance (seen, told, worked out); the relation types
    with too little funding are its open slots. Read directly, without competing.

    Relations are written in two ways. Directly, from what is already the pool's own work: a split's
    boundary conditions the split thought; a recognition's clause conditions the action's goal; a
    filler has a role in what it filled; a part has a role in its composite; an explanation heard
    with its keys gives told co-occurrences. And by working it out: a concept in play (an instance
    wins the top while the concept is not fully understood) is cued into the pool as an SOV molecule
    whose sites are its open slots; it binds only to knowns it has evidence with in the raw records
    (co-wins, what followed what); when it wins together with one, that relation is written back.
    At the top, an SOV molecule poses a question for each open slot; a question closes when the
    register fills its slot.
    """
    RELS = ("causes", "caused_by", "co_occurs", "role", "conditions")
    HOW = {"seen": 0, "told": 1, "worked": 2}

    def __init__(self, mind):
        self.mind = mind
        self.rel = {}          # concept -> {(relation, other): [seen, told, worked]}
        self.questions = {}    # question id -> (concept, relation)
        self.log = []          # (tick, what, detail)
        self.follows = {}      # perceived id -> {perceived on the next tick: count}
        self.arrivals = {}     # perceived id -> ticks it was perceived
        self.last = set()      # what was perceived last tick
        self.before = set()    # and the tick before
        self.matters = set()   # concepts that took part in an outcome, a surprise, a goal or a conflation
        self.abstracts = []    # analogies: dict(id, pattern, members=[{role: concept}])
        self.expect = {}       # (concept, relation) -> expectation weight, transferred from an abstract
        self.kind = lambda c: None   # a concept's kind for matching; the force agent marks its pushes "act"
        self.owners = {}             # concept -> who it is about (written by the world the mind lives in)
        self.owner = lambda c: (c.split(":", 1)[1].rsplit("_", 1)[0] if "_push:" in c else self.owners.get(c))
        self.refuted = set()   # (concept, relation, other) refuted by intervention; not written again
        self.shared_cache = {}  # (structure, structure) pairs already searched for a shared structure
        self.recast = {}        # (concept, relation, other) -> the relation it is written as instead
        self.inert = set()      # ids that are not concepts (a world's "nothing changed"): no part of structure
        self.tellers = {}       # (concept, relation, other) -> who told it (written by the world the mind lives in)
        self.belied = []        # (tick, teller, concept): told receipts the world contradicted
        self.progress = {}      # concept -> progress momentum (the user, 2026-10-24): an investigation that
                                # just got an outcome keeps its pull to follow it up; fades by half-life

    # ---- reading ------------------------------------------------------------------------------

    def add(self, c, rel, other, how, w=1.0):
        if c is None or other is None or c == other or (c, rel, other) in self.refuted:
            return
        rel = self.recast.get((c, rel, other), rel)   # an observed-only link is written as co-occurrence
        e = self.rel.setdefault(c, {}).setdefault((rel, other), [0.0, 0.0, 0.0])
        e[self.HOW[how]] += w
        self.log.append((self.mind.t, f"{how}:{rel}", (c, other)))

    def funding(self, c, rel):
        """Funding of one relation type: lived and worked-out receipts at full weight, told at half. A
        concept's conditions slot holds what conditions it too (conditioned_by, written by a split or by
        experiments that found a change not to matter)."""
        rels = (rel, "conditioned_by") if rel == "conditions" else (rel,)
        told = self.mind.p.credulity   # temperament (Params.credulity; 0.5: "told at half")
        return sum(e[0] + e[2] + told * e[1] for (r, _), e in self.rel.get(c, {}).items() if r in rels)

    def level(self, c):
        """How well the concept is understood: the mean over relation types of their funding, capped
        at sov_m0 each, as a share of sov_m0."""
        m0 = self.mind.p.sov_m0
        return sum(min(1.0, self.funding(c, r) / m0) for r in self.RELS) / len(self.RELS)

    def open_slots(self, c):
        return tuple(r for r in self.RELS if self.funding(c, r) < 1.0)

    def needed(self, c):
        """The open slots a served concept is paid for (step 3: only what its ownership slot needs; first
        any open slot, and a change served for what moves it, already known, held the top asking its
        role, which no experiment answers). None where the mind has no territory: every open slot."""
        served = self.mind.territory.served
        if served is None:
            return None
        return tuple(r for r in served.get(c, (0.0, ()))[1] if self.funding(c, r) < 1.0)

    def needed_openness(self, c):
        """How open the relations a served concept is paid for are, 0..1."""
        rs = self.mind.territory.served.get(c, (0.0, ()))[1]
        m0 = self.mind.p.sov_m0
        return sum(1 - min(1.0, self.funding(c, r) / m0) for r in rs) / len(rs) if rs else 0.0

    def relations(self, c):
        """The filled relations: relation -> [(other, funding, provenance)]."""
        out = {}
        for (r, o), e in self.rel.get(c, {}).items():
            how = max(self.HOW, key=lambda h: e[self.HOW[h]])
            out.setdefault(r, []).append((o, round(e[0] + e[2] + 0.5 * e[1], 2), how))
        return out

    def evidence(self, c, k):
        """What the raw records say relates concept c and known k (not yet worked out)."""
        mind, ev = self.mind, []
        kc = concept_of(k) or k
        a = mind.exp[0].get(frozenset((c, k)))
        if a is not None and sum(a) - sum(PRIOR) >= 2:
            ev.append(("co_occurs", sum(a) - sum(PRIOR)))
        # causes: k is perceived on the tick after c is perceived (arrivals, not slot wins: a thought
        # that stays in the pool wins every tick), reliably (at least 60% of c's arrivals) and at least
        # twice as often as k at all (first 1.5x with no reliability floor: noise that happened to
        # precede a chain passed)
        ticks = max(1, mind.t)
        for src, dst, rel in ((c, k, "causes"), (k, c, "caused_by")):
            best = 0
            for s_ in self.readings(src):   # a split concept is also judged by each of its halves
                for d_ in self.readings(dst):
                    n, m = self.follows.get(s_, {}).get(d_, 0), self.arrivals.get(s_, 0)
                    if n >= 2 and m and n / m >= 0.6 and n / m >= 2 * self.arrivals.get(d_, 0) / ticks:
                        best = max(best, n)
            if best:
                ev.append((rel, best))
        m = mind.pool.get(k)
        if m is not None and c in m.parts:
            ev.append(("role", 1.0))
        return ev

    def most_answerable(self, c):
        """The open slot of c with the most evidence already waiting in the records (summed over the
        knowns in the pool and the facts register), as a question id; ties in relation order. None
        when every open slot already has a standing question."""
        mind = self.mind
        knowns = [x.id for x in mind.pool.values() if concept_of(x.id)] + [m.id for m in mind.facts.values()]
        need = self.needed(c)
        waiting = {r: 0.0 for r in (self.open_slots(c) if need is None else need) if f"q:{r}:{c}" not in self.questions}
        for k in knowns:
            for r, strength in self.evidence(c, k):
                if r in waiting:
                    waiting[r] += strength
        for r in waiting:   # what an analogy predicts is also evidence waiting
            waiting[r] += self.expect.get((c, r), 0.0)
        if mind.inquiry:    # and a slot an experiment can answer is answerable (first: questions no
            for r in waiting:   # experiment could answer, role for an action, took the attention)
                if mind.inquiry.suggest(r, c):
                    waiting[r] += 1.0
        served = mind.territory.served
        if served is not None and c in served:   # the slot that pays for it points the question (step 3)
            for r in served[c][1]:
                if r in waiting:
                    waiting[r] += 2.0
        dom = mind.phases.dominant() if mind.phases else None
        if dom:   # the phase points the question (sec. 5h): its slots first
            for r in Phases.STEER.get(dom[0], ()):
                if r in waiting:
                    waiting[r] += 2.0
        if not waiting:
            return None
        best = max(waiting, key=lambda r: (waiting[r], -self.RELS.index(r)))
        return f"q:{best}:{c}"

    def readings(self, c):
        """c, and the halves of c if it has been split."""
        meta = self.mind.meta
        if meta and c in meta.splits:
            return [c, meta.splits[c]["yes"], meta.splits[c]["no"]]
        return [c]

    def related(self, c, k):
        return k == c or (concept_of(k) == c) or bool(self.evidence(c, k))

    # ---- each tick ------------------------------------------------------------------------------

    def observe(self, rec):
        mind = self.mind
        now = {i for i in mind.perceived if concept_of(i)}
        if mind.meta:   # also counted as the half of a split each was read as (per-reading counts)
            now |= {mind.meta.reading(i) for i in now}
        for i in now:
            self.arrivals[i] = self.arrivals.get(i, 0) + 1
        for a in self.last:
            for b in now:
                self.follows.setdefault(a, {})[b] = self.follows.get(a, {}).get(b, 0) + 1
        self.before, self.last = self.last, now
        for i, f in rec["filled"]:                       # a filler has a role in what it filled
            self.add(concept_of(f), "role", i, "worked")
        for _, x, y, b in rec["formed"]:                 # parts have a role in their composite
            for part in (x, y):
                self.add(concept_of(part), "role", f"[{x}+{y}|{b}]", "worked", 0.5)
        # an SOV molecule that wins a slot works out its concept's relations with what is at hand: the
        # knowns in the pool and what was perceived in the last two ticks (first: only a known it won
        # together with as a bound pair, which a thing that arrived a tick ago rarely is)
        at_hand = {i for i in mind.pool if concept_of(i)} | self.last | self.before
        for sov in [i for i in rec["reached"] if i.startswith("sov:") and i in mind.pool]:
            c = sov[4:]
            for k in sorted(at_hand - {c}):
                for rel, strength in self.evidence(c, k):
                    if rel in ("causes", "caused_by") and self.kind(c) == "act" and self.kind(concept_of(k) or k) == "act":
                        continue   # a potential force does not cause another: two invitations perceived one
                                   # after the other are not a cause (first worked out, and an untried
                                   # push's causes slot read filled, so its unclaimed slot was parked)
                    if (rel, k) not in self.rel.get(c, {}) or self.rel[c][(rel, k)][2] < 1.0:
                        self.add(c, rel, k, "worked", min(1.0, strength / 2))
        # SOV molecules: keep their sites at the open slots; an understood one leaves. SOV molecules and
        # questions fade unless their concept is in play (perceived or holding a slot) and are
        # refreshed while it is: winning their own slots kept them from decaying, so the first
        # concepts worked on held the track forever. A question that fades is forgotten (can be
        # asked again later).
        in_play = {concept_of(i) for i in set(mind.perceived) | set(rec["reached"]) if concept_of(i)}
        for q in [q for q in self.questions if mind.inquiry and q not in mind.pool and q not in mind.boxes]:
            del self.questions[q]   # faded and swept from the pool: forgotten, so it can be asked again
                                    # (first left standing, and a push's conditions question, swept
                                    # out, blocked its SOV from ever asking it again). Only in an acting
                                    # mind so far: in the designed worlds' minds it moved T34, T49-T51
                                    # (REORG.md step 3, open)
        for c in list(self.progress):   # progress momentum fades by its half-life without new outcomes
            self.progress[c] *= 0.5 ** (1 / mind.p.h0)
            if self.progress[c] < mind.p.floor:
                del self.progress[c]
        for i in [i for i in mind.pool if is_sov(i)]:
            c = i[4:] if i.startswith("sov:") else i.split(":", 2)[2]
            # in an acting mind a question is not refreshed: posed, it decays by its half-life (its
            # experiments carry it meanwhile), leaving the top to SOVs with questions to pose (first refreshed
            # while its concept was in play; a potential force is perceived every tick, so standing
            # questions held the SOV track's top 269 ticks of 300 and SOVs reached it 29 times)
            asked = mind.inquiry and i in self.questions   # (any question: one with no experiment, a role
            served = mind.territory.served                  # or a change's cause, held the top just as well)
            alive = (c in served) if served is not None else (c in in_play)   # step 3: refreshed while a slot
            if alive and not asked:                                           # it serves is open
                mind.pool[i].act = 1.0
            else:
                mind.pool[i].act *= 0.5 ** (1 / mind.p.h0)
            if mind.pool[i].act < mind.p.floor:
                del mind.pool[i]
                self.questions.pop(i, None)
                continue
            if i.startswith("sov:"):
                need = self.needed(c)
                open_ = self.open_slots(c) if need is None else need
                if not open_:
                    del mind.pool[i]
                    rec["closed"].append(i)
                else:
                    mind.pool[i].sites = tuple(f"{r}?{c}" for r in open_)
        # at the top, an SOV molecule poses a question per open slot
        for i in rec["levels"][-1]["winners"]:
            if i.startswith("sov:") and i in mind.pool:
                c = i[4:]
                q = self.most_answerable(c)
                if q is not None:
                    r = q.split(":")[1]
                    self.questions[q] = (c, r)
                    mind.pool[q] = clause(q, tags=("question", f"about:{c}"), sites=(f"{r}?{c}",))
                    rec["questions"].append(q)
        # a question closes when the register fills its slot
        for q, (c, r) in list(self.questions.items()):
            if self.funding(c, r) >= 1.0:
                if q in mind.pool:
                    del mind.pool[q]
                    rec["closed"].append(q)
                b = mind.boxes.get(q)
                if b is not None:
                    b["parked"] = False
                    b["keys"] = {}
                del self.questions[q]
                self.log.append((mind.t, "answered", q))
        self.upkeep()
        self.analogize(rec)
        # concepts that matter (the user, 2026-10-22): in an outcome, a surprise, a goal or a conflation.
        # Step 3 (REORG.md): what an open ownership slot serves, where the mind has a territory; the
        # triggers stand only where its register is empty
        meta = mind.meta
        served = mind.territory.served
        if served is not None:
            self.matters = set(served)
        for i in ([] if served is not None else rec["reached"]):
            c = concept_of(i)
            if c is None or c in self.matters or i not in mind.pool:
                continue
            if max(mind.S.get(i, 0.0), mind.S_prev.get(i, 0.0)) >= 0.8 or "goal" in mind.pool[i].tags \
                    or (meta and (meta.outcomes.get(i) or c in meta.splits or f"meta:conflated:{i}" in meta.watch)):
                self.matters.add(c)
        # what leads to something that matters also matters: mattering spreads backward along
        # worked-out causes and conditions links (my extension of the user's rule)
        for c, rels in list(self.rel.items()):
            for (r, o), e in rels.items():
                if e[0] + e[2] + 0.5 * e[1] < 1.0:
                    continue
                src = o if r == "caused_by" else c if r in ("causes", "conditions") else None
                dst = c if r == "caused_by" else o if r in ("causes", "conditions") else None
                if src and dst and (concept_of(dst) or dst) in self.matters and concept_of(src):
                    self.matters.add(concept_of(src))
        # the dominant phase points attention at its anchor first (sec. 5h)
        dom = mind.phases.dominant() if mind.phases else None
        cued = 0
        if dom and concept_of(dom[1]) and f"sov:{concept_of(dom[1])}" not in mind.pool and self.open_slots(concept_of(dom[1])):
            c = concept_of(dom[1])
            mind.pool[f"sov:{c}"] = clause(f"sov:{c}", tags=("sov", f"about:{c}"), sites=tuple(f"{r}?{c}" for r in self.open_slots(c)))
            self.matters.add(c)
            cued = 1
        # an ownership instance at the top reaches the concepts it serves (step 3, the `serves` link):
        # their SOVs are cued, most paid first (first only a concept's own instance winning the top
        # cued one, and with the invitations no longer winning, the lid's control slot held the top
        # with no SOV to work for it)
        if served is not None:
            for i in rec["levels"][-1]["winners"]:
                for c in sorted(mind.territory.serves_of.get(i, ()), key=lambda c: (-served[c][0], c)):
                    if cued >= mind.p.sov_cues or f"sov:{c}" in mind.pool or not self.needed(c):
                        continue
                    mind.pool[f"sov:{c}"] = clause(f"sov:{c}", tags=("sov", f"about:{c}"),
                                                   sites=tuple(f"{r}?{c}" for r in self.needed(c)))
                    cued += 1
        # a concept in play: an instance that matters won the top while the concept has open slots
        for i in rec["levels"][-1]["winners"]:
            c = concept_of(i)
            if c is None or c not in self.matters or f"sov:{c}" in mind.pool or cued >= mind.p.sov_cues:
                continue
            need = self.needed(c)
            open_ = self.open_slots(c) if need is None else need
            if open_:
                mind.pool[f"sov:{c}"] = clause(f"sov:{c}", tags=("sov", f"about:{c}"),
                                               sites=tuple(f"{r}?{c}" for r in open_))
                cued += 1

    # ---- structure: matching, analogy, transfer -------------------------------------------------
    #
    # A structure is the graph of funded relations (funding >= 1) between concepts: edges typed and
    # directed (causes: a -> b, with caused_by folded in as its inverse; conditions: a -> b; role:
    # part -> whole). Co-occurrence is left out of matching: co-wins are noisy and would make two
    # otherwise identical worlds differ. Matching is content-free: a mapping of nodes that preserves
    # every typed edge, never looking at what a concept is.

    SHAPE = ("causes", "conditions", "role", "enables", "prevents")   # a condition's polarity too (2026-10-23)
    MAX_SHARED = 5   # largest shared sub-structure searched for (patterns so far are 2-3 links)

    def edges(self):
        out = set()
        for c, rels in self.rel.items():
            for (r, o), e in rels.items():
                if e[0] + e[2] + 0.5 * e[1] < 1.0 or o.startswith("[") or o in self.inert or c in self.inert:
                    continue
                c_, o_ = concept_of(c) or c, concept_of(o) or o   # a half counts as its concept
                if c_ == o_:
                    continue
                if r == "caused_by":
                    out.add(("causes", o_, c_))
                elif r in self.SHAPE:
                    out.add((r, c_, o_))
        # a condition with a polarity is seen by its polarity (first: both, and analogy kept matching
        # the bare condition, so a latch that prevents still matched a cable that enables)
        polar = {b for r, _, b in out if r in ("enables", "prevents")}
        return {e for e in out if not (e[0] == "conditions" and e[2] in polar)}

    @staticmethod
    def components(edges):
        nodes = sorted({x for _, a, b in edges for x in (a, b)})
        parent = {n: n for n in nodes}

        def find(n):
            while parent[n] != n:
                n = parent[n]
            return n
        for _, a, b in edges:
            parent[find(a)] = find(b)
        groups = {}
        for n in nodes:
            groups.setdefault(find(n), set()).add(n)
        return [(frozenset(g), frozenset(e for e in edges if e[1] in g)) for g in groups.values()]

    @staticmethod
    def embed(p_nodes, p_edges, g_nodes, g_edges, exact=False, first=False, pk=None, gk=None, limit=None):
        """Every injective mapping of pattern nodes to graph nodes that preserves each typed pattern
        edge (exact: same size and no extra graph edges among the image). Deterministic order.
        first: stop at the first (callers that use only it; enumerating all of them on a hub took
        two minutes a tick in the calculator world). pk, gk: the kind of a pattern node and of a
        graph node; a node maps only to one of its kind (an action only to an action)."""
        order = sorted(p_nodes, key=lambda n: (-sum(n in (a, b) for _, a, b in p_edges), n))
        g_sorted = sorted(g_nodes)
        found = []

        def ok(m):
            for r, a, b in p_edges:
                if a in m and b in m and (r, m[a], m[b]) not in g_edges:
                    return False
            return True

        def go(i, m):
            if first and found or limit and len(found) >= limit:
                return
            if i == len(order):
                if exact:
                    image = set(m.values())
                    inv = {v: k for k, v in m.items()}
                    extra = [e for e in g_edges if e[1] in image and e[2] in image and (e[0], inv[e[1]], inv[e[2]]) not in p_edges]
                    if extra or len(g_nodes) != len(p_nodes):
                        return
                found.append(dict(m))
                return
            for g in g_sorted:
                if g in m.values() or (pk is not None and pk(order[i]) != gk(g)):
                    continue
                m[order[i]] = g
                if ok(m):
                    go(i + 1, m)
                del m[order[i]]
        go(0, {})
        return found

    def match(self, target):
        """How much of a target structure (typed edges over abstract role names) the register
        preserves: the best share of target edges kept by any injective mapping of roles to
        concepts, with that mapping."""
        g_edges = self.edges()
        g_nodes = sorted({x for _, a, b in g_edges for x in (a, b)})
        roles = sorted({x for _, a, b in target for x in (a, b)})
        best = (0.0, None)
        if len(g_nodes) < len(roles):
            return best

        def go(i, m):
            nonlocal best
            if i == len(roles):
                kept = sum((r, m[a], m[b]) in g_edges for r, a, b in target) / len(target)
                if kept > best[0]:
                    best = (kept, dict(m))
                return
            for g in g_nodes:
                if g not in m.values():
                    m[roles[i]] = g
                    go(i + 1, m)
                    del m[roles[i]]
        go(0, {})
        return best

    def upkeep(self):
        """The register's own upkeep each tick (like SOV's Anneal and Archaise, applied by the economy,
        not the organism). Retract: a relation worked out from the records that the records no
        longer support is withdrawn, licensed by the failing evidence (first done only when the
        concept's SOV molecule won a slot, so a link written early on tiny counts could outlive its
        evidence). An abstract structure drops a member whose relations no longer all hold, and
        dissolves below two members, so it can re-form."""
        mind = self.mind
        for c, rels in self.rel.items():
            for (rel, o), e in rels.items():
                if rel in ("causes", "caused_by", "co_occurs") and e[2] > 0 and                         rel not in {r for r, _ in self.evidence(c, o)}:
                    e[2] = 0.0
                    self.log.append((mind.t, f"retract:{rel}", (c, o)))
        edges = self.edges()
        for a in list(self.abstracts):
            a["members"] = [m for m in a["members"] if all((r, m[x], m[y]) in edges for r, x, y in a["pattern"])]
            if len(a["members"]) < 2:
                self.abstracts.remove(a)
                self.log.append((mind.t, "dissolved", a["id"]))

    @staticmethod
    def connected_subsets(edges, k):
        """Connected subsets of exactly k edges, in a deterministic order. Each partial subset is
        explored once (first: every ordering of the same subset was explored, factorial on a hub;
        one tick in the force world took 332 s at 12 links)."""
        edges = sorted(edges)
        out, seen, visited = [], set(), set()

        def grow(cur, nodes):
            key = frozenset(cur)
            if key in visited:
                return
            visited.add(key)
            if len(cur) == k:
                if key not in seen:
                    seen.add(key)
                    out.append(key)
                return
            for e in edges:
                if e not in cur and (e[1] in nodes or e[2] in nodes):
                    grow(cur | {e}, nodes | {e[1], e[2]})
        for e in edges:
            grow({e}, {e[1], e[2]})
        return out

    def edge_funding(self, e):
        """How well a typed edge (relation, a, b) is funded, read from either end."""
        r, a, b = e
        f = lambda c, rel, o: sum(x[0] + x[2] + 0.5 * x[1] for (rr, oo), x in self.rel.get(c, {}).items()
                                  if rr == rel and (concept_of(oo) or oo) == o)
        return max(f(a, r, b), f(b, "caused_by", a) if r == "causes" else 0.0)

    def shared(self, e1, e2, least=2, exclude=()):
        """The largest connected sub-structure of e1 (at least `least` edges) that also occurs in e2:
        (pattern edges, mapping into e2), or None. SOV's Abstract holds exactly the shared sub-pattern;
        the two structures need not be identical."""
        n2 = {x for _, a, b in e2 for x in (a, b)}
        for k in range(min(len(e1), self.MAX_SHARED), least - 1, -1):
            for sub in self.ranked(self.connected_subsets(e1, k)):
                nodes = {x for _, a, b in sub for x in (a, b)}
                if any(len(p) == len(sub) and self.embed(nodes, sub, roles, p, exact=True, first=True)
                       for roles, p in exclude):
                    continue   # the correspondence these two already share: look for another
                maps = self.embed(nodes, sub, n2, e2, pk=self.kind, gk=self.kind, limit=200)
                if maps:
                    return sub, self.best_image(sub, maps)
        return None

    CORE = 12
    ANALOGY_MIN = 1.0   # a floor on links in an analogy; at 2 or 1.5 the designed worlds' worked-out links (funded 1) fell out (2026-10-23)

    def core(self, e):
        """A structure as analogy sees it: its CORE best-funded links, and of those the connected part
        holding the best-funded one (first: whole structures, and a hub of 30 links, re-searched
        against every other structure each time it grew, took two minutes a tick)."""
        # confirmed links only; a condition is confirmed by its own making (it needs tries that split)
        e = {x for x in e if x[0] in ("conditions", "enables", "prevents") or self.edge_funding(x) >= self.ANALOGY_MIN}
        if len(e) <= self.CORE:
            return frozenset(e)
        # conditions first (funded about once a try, they would never make the cut by funding; first,
        # the button's enabling cable was left out of its core), then the best-funded links
        # (at most four: first any number, and incidental ones crowded a release chain out)
        isc = lambda x: x[0] in ("conditions", "enables", "prevents")
        conds = sorted((x for x in e if isc(x)), key=lambda x: (-self.edge_funding(x), x))[:4]
        rest = sorted((x for x in e if x not in conds), key=lambda x: (-self.edge_funding(x), x))
        keep = (conds + rest)[:self.CORE]
        comps = self.components(set(keep))
        return max((ed for _, ed in comps), key=lambda ed: (sum(self.edge_funding(x) for x in ed), len(ed), sorted(ed)))

    def ranked(self, subs):
        """Sub-structures in the order a correspondence is sought: one holding an action first (it
        anchors the correspondence; first, the middle of one release was matched onto the push of
        the other), and among those the best-funded, the most-confirmed experience (first, the first
        in plain order, and a gust's coincidences, funded once, were matched onto a lived release)."""
        return sorted(subs, key=lambda sub: (not any(self.kind(x) == "act" for _, a, b in sub for x in (a, b)),
                                             -sum(self.edge_funding(e) for e in sub)))

    def best_image(self, pattern, maps, via=None):
        """Of the mappings of a pattern, the one that keeps owners together (each owner's concepts
        mapped onto one owner's; `owner` is set by the world the mind lives in, none by default), then
        whose image is best funded (first: funding only, and the clamp's launch was mapped onto the
        weight's, though the clamp's release went to the catch's)."""
        return max(maps, key=lambda m: (self.consistency(m, via), sum(self.edge_funding((r, m[a], m[b])) for r, a, b in pattern)))

    def consistency(self, m, via=None):
        """How well a mapping keeps owners together: minus the extra owners any one owner maps onto."""
        pairs = {}
        for c, d in m.items():
            o, p = self.owner(via[c] if via else c), self.owner(d)
            if o is not None and p is not None:
                pairs.setdefault(o, set()).add(p)
        return -sum(len(v) - 1 for v in pairs.values())

    def refine(self, comps, rec):
        """An abstract structure grows with its members: when every member's structure now shares a
        larger connected sub-structure than the pattern, the pattern becomes that (first: a pattern
        stayed at whatever the first two members shared when it formed)."""
        where = {c: (n, e) for n, e in comps for c in n}
        for a in self.abstracts:
            homes = [where.get(next(iter(m.values()))) for m in a["members"]]
            if any(h is None for h in homes):
                continue
            # one member per structure: two members whose structures have since joined into one
            # would be mapped onto themselves (first: the same member three times over)
            keep, seen_homes = [], []
            for m, h in zip(a["members"], homes):
                if h[0] not in seen_homes:
                    keep.append((m, h))
                    seen_homes.append(h[0])
            if len(keep) < 2:
                continue
            a["members"], homes = [m for m, _ in keep], [h for _, h in keep]
            first = homes[0][1]
            # the search is repeated only when a member's structure or the pattern changed (first:
            # every tick, 20 s a tick once the calculator's register was a hub of 30 links)
            key = (a["pattern"], tuple(e for _, e in homes))
            # and at most every 10 ticks while they keep changing (first: every tick, and with one
            # mind across twelve worlds a tick took 11 s)
            if a.get("refined") == key or self.mind.t - a.get("refined_at", -99) < 10:
                continue
            a["refined"], a["refined_at"] = key, self.mind.t
            for k in range(min(len(first), self.MAX_SHARED), len(a["pattern"]), -1):
                found = None
                for sub in self.ranked(self.connected_subsets(first, k)):
                    nodes = {x for _, p, q in sub for x in (p, q)}
                    # whether it fits every other member first (stopping at one mapping), and only
                    # then the best-funded image (first: up to 200 images for every sub-structure tried)
                    if all(self.embed(nodes, sub, n, e, first=True, pk=self.kind, gk=self.kind) for n, e in homes[1:]):
                        maps = [self.embed(nodes, sub, n, e, pk=self.kind, gk=self.kind, limit=200) for n, e in homes[1:]]
                        found = (sub, nodes, [self.best_image(sub, m) for m in maps])
                        break
                if found:
                    sub, nodes, maps = found
                    roles = {c: f"r{i}" for i, c in enumerate(sorted(nodes))}
                    a["pattern"] = frozenset((r, roles[x], roles[y]) for r, x, y in sub)
                    a["roles"] = frozenset(roles.values())
                    a["members"] = [{roles[c]: c for c in nodes}] + [{roles[c]: m[c] for c in nodes} for m in maps]
                    self.log.append((self.mind.t, "refined", (a["id"], len(sub))))
                    break
            else:
                # the pattern did not grow: each later member's image is chosen again, its structure
                # having grown since (first: chosen once, when the consistent image did not exist yet,
                # and the clamp's launch stayed mapped onto the weight's)
                first_m = a["members"][0]
                for j in range(1, len(a["members"])):
                    maps = self.embed(a["roles"], a["pattern"], homes[j][0], homes[j][1],
                                      pk=lambda r: self.kind(first_m[r]), gk=self.kind, limit=200)
                    if maps:
                        new = self.best_image(a["pattern"], maps, via=first_m)
                        if self.consistency(new, first_m) > self.consistency(a["members"][j], first_m):
                            a["members"][j] = new   # only for one that keeps owners together better

    def analogize(self, rec):
        """Analogy (SOV's Abstract): two separate structures sharing a sub-structure of at least two
        edges become members of one abstract structure whose roles are that shared pattern. A further
        structure containing the whole pattern joins as a member. Transfer: the largest part of an
        abstract pattern found in a structure that lacks the rest expects the missing relations
        (Abstract then Constrain)."""
        comps = [(n, self.core(e)) for n, e in self.components(self.edges()) if e]
        comps = [(frozenset(x for _, p, q in e for x in (p, q)), e) for _, e in comps]
        self.refine(comps, rec)
        same = lambda a, b: len(a["pattern"]) == len(b["pattern"]) and bool(self.embed(
            a["roles"], a["pattern"], b["roles"], b["pattern"], exact=True, first=True))
        for j in range(len(self.abstracts) - 1, 0, -1):   # two abstracts refined into one
            if any(same(self.abstracts[j], self.abstracts[i]) for i in range(j)):   # correspondence:
                self.log.append((self.mind.t, "merged", self.abstracts[j]["id"]))   # the later goes,
                del self.abstracts[j]                                                # its members rejoin
        # a structure may take part in several abstracts, one per kind of correspondence (first: in
        # one at most, so the first trivial analogy formed, a press against a flag's push, claimed
        # both worlds, and the enabling structure they shared could never form one)
        member = lambda n, a: any(set(m.values()) & n for m in a["members"])
        for i, (n1, e1) in enumerate(comps):
            if len(e1) < 2:
                continue
            joined = False
            for a in self.abstracts:
                if member(n1, a):
                    continue
                rk = lambda r, a=a: self.kind(a["members"][0][r])
                maps = self.embed(a["roles"], a["pattern"], n1, e1, pk=rk, gk=self.kind, limit=200)
                if maps:
                    best = self.best_image(a["pattern"], maps, via=a["members"][0])
                    a["members"].append(best)
                    rec.setdefault("analogies", []).append((a["id"], best))
                    joined = True
                    break
            if joined:
                continue
            for n2, e2 in comps[i + 1:]:
                if len(e2) < 2 or n1 & n2:
                    continue
                # two structures already in one abstract may still share more: the largest shared
                # structure is sought again only when either changed (cached per pair)
                key = (e1, e2)
                if key in self.shared_cache:
                    continue
                self.shared_cache[key] = True
                both = [(a["roles"], a["pattern"]) for a in self.abstracts if member(n1, a) and member(n2, a)]
                found = self.shared(e1, e2, exclude=both)
                if found and any(len(a["pattern"]) == len(found[0]) and self.embed(
                        {x for _, p, q in found[0] for x in (p, q)}, found[0], a["roles"], a["pattern"],
                        exact=True, first=True) for a in self.abstracts):
                    continue   # that correspondence exists already: the structures join it instead
                if found:
                    sub, m = found
                    nodes = sorted({x for _, a, b in sub for x in (a, b)})
                    roles = {c: f"r{k}" for k, c in enumerate(nodes)}
                    pattern = frozenset((r, roles[a], roles[b]) for r, a, b in sub)
                    self.next_abs = getattr(self, "next_abs", len(self.abstracts)) + 1   # ids never reused
                    aid = f"abs:{self.next_abs - 1}"
                    m1 = {roles[c]: c for c in nodes}
                    m2 = {roles[c]: m[c] for c in nodes}
                    self.abstracts.append(dict(id=aid, roles=frozenset(roles.values()), pattern=pattern, members=[m1, m2]))
                    rec.setdefault("analogies", []).append((aid, m2))
                    self.log.append((self.mind.t, "analogy", (aid, tuple(m1[r] for r in sorted(m1)), tuple(m2[r] for r in sorted(m2)))))
                    break
        # transfer onto structures that hold part of an abstract pattern
        for n, e in comps:
            for a in self.abstracts:
                if member(n, a):
                    continue
                # every reading of the largest part of the pattern that fits: a single link fits either
                # link of a chain, and both readings are held as expectations (first: only the first
                # reading found)
                found = []
                for k in range(len(a["pattern"]) - 1, 0, -1):
                    for sub in self.connected_subsets(a["pattern"], k):
                        nodes = {x for _, p, q in sub for x in (p, q)}
                        rk = lambda r, a=a: self.kind(a["members"][0][r])
                        found += [(sub, m) for m in self.embed(nodes, sub, n, e, pk=rk, gk=self.kind)]
                    if found:
                        break
                for sub, m in found:
                    for r, x, y in a["pattern"] - sub:
                        if x in m and r in ("causes", "conditions", "role"):
                            key = (m[x], r)
                        elif y in m and r == "causes":
                            key = (m[y], "caused_by")
                        elif y in m and r == "conditions":   # what it turns on is not known yet
                            key = (m[y], "conditioned_by")
                        else:
                            continue
                        if key not in self.expect:
                            self.expect[key] = 1.5
                            self.log.append((self.mind.t, "expect", key))

    # ---- speech ---------------------------------------------------------------------------------

    def explain(self, c):
        """Speech by understanding: a relation funded to sov_m0 or more is stated, a weaker or only told
        one is hedged, an open slot is asked."""
        m0 = self.mind.p.sov_m0
        state, hedge = [], []
        for r, items in self.relations(c).items():
            for o, f, how in items:
                (state if f >= m0 and how != "told" else hedge).append((r, o))
        return dict(states=sorted(state), hedges=sorted(hedge), asks=list(self.open_slots(c)))


class Phases:
    """Emotional phases (THOUGHT_MOLECULES.md sec. 5h). A phase is collective: formed from the
    configuration, not assigned. Each is a molecule with an anchor (what it is about), a half-life
    (it fades unless what produced it keeps refreshing it, which gives hysteresis), and, for the
    phases that can be resolved, open sites (what would close it): the molecule attracts closure.
    Ending by closure, it is gone; ending by its half-life with its sites open, it goes to storage
    open and re-opens when its anchor comes back (Pandora). A phase's first molecule competes in its
    own slots; anger replicates when blame spreads (each new thing filling the blocked goal's
    "caused by" slot gets a copy anchored to it), and copies compete in the thoughts' slots: the
    cancer that floods the mind. The dominant phase steers the SOV's attention (Understanding).
    How each phase is detected is my choice:

    frustration  a want blocked 4 ticks running           anchor the want    closes when the want is met
    anger        a frustrated want's "caused by" filled    anchor the blamed  a grounded copy closes when the
                 (each blamed thing a copy; a copy whose                        want is met; an ungrounded one
                 blame the records do not support is                           only fades (escapes closure)
                 ungrounded: false closure, cancerous)
    anxiety      a concept that matters, bad outcomes      anchor the concept closes at understanding 0.5
                 the majority, understood below 0.4
    sadness      a concept understood 0.5+ contradicted    anchor the concept closes when understood again
    joy          a good outcome                            anchor what it was about   expires
    curiosity    a question posed                          anchor its concept         expires
    calm         nothing blocked, surprise flat, 5 ticks   anchor the pool            expires
    """
    KINDS = ("frustration", "anger", "anxiety", "sadness", "joy", "curiosity", "calm", "resignation", "gratitude")
    STEER = {"curiosity": (), "frustration": ("caused_by", "conditions"), "anxiety": ("conditions", "causes"),
             "anger": ("caused_by", "conditions"), "sadness": ("conditions", "caused_by"), "joy": ("caused_by",),
             "calm": (), "resignation": (), "gratitude": ()}
    CLOSABLE = ("frustration", "anger", "anxiety", "sadness")

    def __init__(self, mind):
        self.mind = mind
        self.info = {}        # phase id -> dict(kind, anchor, born, grounded, goal)
        self.stored = {}      # phase id -> molecule: expired with its sites open
        self.streak = {}      # want -> consecutive ticks blocked
        self.loss = {}        # concept -> its understanding when it was lost
        self.seen_contra = 0
        self.calm_for = 0
        self.last_outcome = 0
        self.prev_live = set()        # the graph's live instances last tick (to see which closed)
        self.prev_open = set()        # and its open ones, parked or not
        self.closed_by_claim = set()  # instances closed by a claim taking this tick
        self.log = []         # (tick, what, phase id)

    @staticmethod
    def pid(kind, anchor):
        return f"phase:{kind}:{anchor}"

    def anchor(self, pid):
        return self.info.get(pid, {}).get("anchor")

    def live(self):
        return [p for p in self.info if p in self.mind.pool]

    def primaries(self):
        """The phase molecules that compete in the phases' own slots: all but anger's copies (anger
        beyond its first-formed molecule: replication by spreading blame, the cancer that floods the
        thoughts' slots). Several phases of another kind (curiosity about several concepts) are not
        replication. (First: every molecule beyond its kind's first counted as a copy.)"""
        live = self.live()
        angers = sorted((self.info[p]["born"], p) for p in live if self.info[p]["kind"] == "anger")
        copies = {p for _, p in angers[1:]}
        return {p for p in live if p not in copies}

    def dominant(self):
        live = self.live()
        if not live:
            return None
        p = max(live, key=lambda x: (self.mind.pool[x].act, -self.info[x]["born"], x))
        return self.info[p]["kind"], self.info[p]["anchor"]

    def form(self, kind, anchor, rec, sites=(), grounded=True, goal=None):
        """Form or refresh a phase molecule."""
        mind, p = self.mind, self.pid(kind, anchor)
        if p in mind.pool:
            mind.pool[p].act = 1.0
            return p
        old = self.stored.pop(p, None)   # stored open: this is the same phase re-opening (Pandora)
        m = old or clause(p, tags=("phase", kind, f"about:{anchor}"), sites=sites)
        mind.pool[p] = replace(m, act=1.0)
        self.info[p] = dict(kind=kind, anchor=anchor, born=mind.t, grounded=grounded, goal=goal)
        self.log.append((mind.t, "re-opened" if old else "formed", p))
        rec["phases"].append(p)
        return p

    def graph(self, rec):
        """The phases as readings of the ownership graph (REORG.md step 7; OWNERSHIP_SOV.md sec. 7), in
        an acting mind with a territory register. Each phase is anchored on its ownership instance
        (own:<kind>:<region>), so a phase stored open re-opens when its instance opens again.
          anxiety      a held region's claim failed once: contested by its own failure
          frustration  a control or contested-by-failure slot whose claims failed twice running (one
                       failure is not enough: the slot keeps not taking; the user, 2026-10-25)
          sadness      a lost slot
          joy          an instance closed because a claim took on its region (not any good outcome)
          curiosity    an unclaimed slot winning the ownership track
          calm         no open instance with a pull (parked ones have none) for five ticks
        Anger, a control slot with another agent's push behind the prevents, has no world to be read
        in before Stage 6 (left open)."""
        mind, terr = self.mind, self.mind.territory
        refreshed = set()
        live = terr.live()
        top = set(rec["levels"][-1]["winners"]) if rec.get("levels") else set()
        for k, r in sorted(live):
            row, inst = terr.rows.get(r, {}), f"own:{k}:{r}"
            failing = k == "control" or (k == "contested" and row.get("failed") and not row.get("other_since"))
            if failing and row.get("fails", 0) >= 2:
                refreshed.add(self.form("frustration", inst, rec, sites=(f"take?{r}",), goal=inst))
            elif k == "contested" and row.get("failed") and not row.get("other_since") and row.get("fails", 0) == 1:
                refreshed.add(self.form("anxiety", inst, rec, sites=(f"take?{r}",), goal=inst))
            if k == "lost":
                refreshed.add(self.form("sadness", inst, rec, sites=(f"take?{r}",), goal=inst))
                who = row.get("taken_by")   # anger at the one who took it (blame, grounded: it was seen taken)
                if who:
                    refreshed.add(self.form("anger", f"other:{who}", rec, sites=(f"blame?{who}",), grounded=True,
                                            goal=inst))
            if k == "unclaimed" and inst in top:   # only live instances enter the pool, so only here can it win
                refreshed.add(self.form("curiosity", inst, rec))
        for k, r in sorted(terr.open_slots() - live):   # a lost slot opening while parked (nothing could fill
            if k == "lost" and (k, r) not in self.prev_open:   # it now: the thing is gone) still grieves, once
                row, inst = terr.rows.get(r, {}), f"own:lost:{r}"   # (first only live slots formed phases, and a
                refreshed.add(self.form("sadness", inst, rec, sites=(f"take?{r}",), goal=inst))   # toy carried
                if row.get("taken_by"):                                                           # off formed none)
                    refreshed.add(self.form("anger", f"other:{row['taken_by']}", rec,
                                            sites=(f"blame?{row['taken_by']}",), grounded=True, goal=inst))
        # anger: a frustrated slot whose claim is conditioned on a state a purposeful other keeps (S6-W01:
        # another's push behind the prevents, inferred, not seen). First open until Stage 6
        others = terr.others()
        meta, und = mind.meta, mind.understanding
        for p in [p for p in self.live() if self.info[p]["kind"] == "frustration"]:
            inst = self.info[p]["anchor"]
            r = inst.split(":")[-1]
            conds = set()
            for c in terr.rows.get(r, {}).get("claims", {}):
                x, todo = c, [c]
                while todo:
                    x = todo.pop()
                    if meta and x in meta.splits:
                        conds.add(meta.splits[x]["tag"])
                        todo += [meta.splits[x]["yes"], meta.splits[x]["no"]]
                conds |= {o for (rel, o) in (und.rel.get(c, {}) if und else {}) if rel == "conditioned_by"}
            for o, g in others.items():
                if o != r and any(f in conds for f in (f"{o}_{g}", f"not_{o}_{g}")):
                    refreshed.add(self.form("anger", f"other:{o}", rec, sites=(f"blame?{o}",), grounded=True, goal=inst))
        # closed by a claim taking: any open instance, parked or not (a parked one is one nothing could fill
        # then; when a claim fills it anyway, it closed by the claim. First only live ones, and a want parked
        # the tick before the push that met it closed with no joy; fiction ladder, rung 0)
        is_open = terr.open_slots()
        lost_now = {r for k, r in is_open if k == "lost"}   # a slot that closed because its region is now lost did
        closed_by_claim = {(k, r) for k, r in (self.prev_live | self.prev_open) - is_open   # not close by a claim
                           if r in terr.took_now and r not in lost_now}
        for k, r in sorted(closed_by_claim):
            refreshed.add(self.form("joy", f"own:{k}:{r}", rec))
        self.closed_by_claim = {f"own:{k}:{r}" for k, r in closed_by_claim}
        und = mind.understanding   # anger at a teller whose word the world contradicted: blame for a blocked want,
        for t, who, _ in (und.belied if und else []):   # grounded, the word being what failed (Phases' anger,
            if t == mind.t - 1 and who:                  # read off the told receipt refuted; fiction ladder, rung 3)
                refreshed.add(self.form("anger", f"other:{who}", rec, sites=(f"blame?{who}",), grounded=True))
        for r, who in sorted(terr.helped_now.items()):   # a want met by another's act, seen: gratitude toward
            refreshed.add(self.form("gratitude", f"other:{who}", rec))   # them (it closed, not by a claim of one's own)
            self.closed_by_claim.add(f"own:control:{r}")   # its frustration ends with it
        terr.helped_now = {}
        for r in sorted(terr.gave_up_now):   # a want given up: resignation (a threshold crossed in the mind,
            refreshed.add(self.form("resignation", f"own:control:{r}", rec))   # not a slot closed by a claim)
            self.closed_by_claim.add(f"own:control:{r}")   # its frustration ends with it
        terr.gave_up_now = set()
        terr.took_now = set()
        self.prev_live, self.prev_open = live, is_open
        self.calm_for = self.calm_for + 1 if not live else 0
        if self.calm_for >= 5:
            refreshed.add(self.form("calm", "pool", rec))
        return refreshed

    def observe(self, rec):
        mind, und, meta = self.mind, self.mind.understanding, self.mind.meta
        if mind.territory.served is not None:   # an acting mind: the phases read off the ownership graph
            self.finish(rec, self.graph(rec), graph=True)
            return
        refreshed = set()
        blocked = rec["blocked"]
        # frustration: a want blocked 4 ticks running
        for i in [i for i in self.streak if i not in mind.pool]:
            self.streak[i] = 0
        for i, m in list(mind.pool.items()):
            if "goal" not in m.tags or is_phase(i):
                continue
            self.streak[i] = self.streak.get(i, 0) + 1 if blocked.get(i, 0) > 0 else 0
            if self.streak[i] >= 4:
                refreshed.add(self.form("frustration", i, rec, sites=m.sites, goal=i))
        # anger: each thing filling a frustrated want's "caused by" slot gets a copy anchored to it
        if und:
            for p in [p for p in self.live() if self.info[p]["kind"] == "frustration"]:
                g = self.info[p]["anchor"]
                c = concept_of(g) or g
                for (r, o), e in und.rel.get(c, {}).items():
                    if r == "caused_by" and e[0] + e[2] + 0.5 * e[1] > 0:
                        # grounded: the blame is lived or worked out (or the records support it),
                        # not only told; an ungrounded blame is false closure (my definition)
                        grounded = e[0] + e[2] >= 1.0 or "caused_by" in {x for x, _ in und.evidence(c, o)}
                        refreshed.add(self.form("anger", o, rec, sites=(f"blame?{o}",), grounded=grounded, goal=g))
            # anxiety: a concept that matters, its outcomes mostly bad, understood below 0.4
            if meta:
                for c in sorted(und.matters):
                    hist = meta.outcomes.get(c, [])
                    bad = sum(1 for _, _, o in hist if o < 0)
                    if len(hist) >= 2 and bad * 2 > len(hist) and und.level(c) < 0.4:
                        refreshed.add(self.form("anxiety", c, rec, sites=(f"understood?{c}",)))
            # sadness: a well understood concept contradicted
            for i in mind.contradicted[self.seen_contra:]:
                c = concept_of(i) or i
                if und.level(c) >= 0.5:
                    self.loss[c] = und.level(c)
                    refreshed.add(self.form("sadness", c, rec, sites=(f"remade?{c}",)))
            self.seen_contra = len(mind.contradicted)
            # curiosity: a question posed
            for q in rec["questions"]:
                refreshed.add(self.form("curiosity", q.split(":", 2)[2], rec))
        # joy: a good outcome, about a want just met or else what arrived with it
        if self.last_outcome > 0:
            met = [c if isinstance(c, str) else c[0] for c in rec["closed"]]
            met = [c for c in met if c in self.streak] or sorted(i for i in mind.perceived if concept_of(i))
            if met:
                refreshed.add(self.form("joy", met[0], rec))
        self.last_outcome = 0
        # calm: nothing blocked, surprise flat, five ticks running
        self.calm_for = self.calm_for + 1 if not blocked and rec["boredom"] < 0.1 else 0
        if self.calm_for >= 5:
            refreshed.add(self.form("calm", "pool", rec))
        self.finish(rec, refreshed)

    def finish(self, rec, refreshed, graph=False):
        """Closure, half-life and Pandora, the same for the hand-written rules and the graph's."""
        mind = self.mind
        self.close(rec, graph)
        # half-life: a phase not refreshed fades; expired with its sites open, it is stored open
        for p in self.live():
            if p in refreshed:
                continue
            # anger copies are refreshed only while their want is still frustrated
            mind.pool[p].act *= 0.5 ** (1 / mind.p.phase_h)
            if mind.pool[p].act < mind.p.floor:
                m = mind.pool.pop(p)
                if self.info[p]["kind"] in self.CLOSABLE:
                    self.stored[p] = m
                    self.log.append((mind.t, "expired open", p))
                else:
                    self.log.append((mind.t, "expired", p))
        # Pandora: a phase stored open re-opens when its anchor comes back (in the graph: its instance
        # open again)
        back = set(mind.perceived) | set(rec["reached"])
        if graph:
            back |= {f"own:{k}:{r}" for k, r in mind.territory.live()}
        for p, m in list(self.stored.items()):
            if self.info[p]["anchor"] in back:
                mind.pool[p] = replace(self.stored.pop(p), act=1.0)
                self.info[p]["born"] = mind.t
                self.log.append((mind.t, "re-opened", p))
                rec["phases"].append(p)

    def close(self, rec, graph=False):
        """Closure: what would resolve the phase has happened. In the graph: frustration, anxiety and
        sadness close when their instance closes because a claim took on its region."""
        mind, und = self.mind, self.mind.understanding
        if graph:
            for p in list(self.live()) + list(self.stored):
                inf = self.info[p]
                anger_met = inf["kind"] == "anger" and inf.get("grounded") and inf.get("goal") in self.closed_by_claim
                if anger_met:   # a grudge whose goal is met (the thing held again): it closes, stored or active
                    mind.pool.pop(p, None)
                    self.stored.pop(p, None)
                    rec["closed"].append(p)
                    self.log.append((mind.t, "closed", p))
            for p in self.live():
                if self.info[p]["kind"] in ("frustration", "anxiety", "sadness") and self.info[p]["anchor"] in self.closed_by_claim:
                    del mind.pool[p]
                    self.stored.pop(p, None)
                    rec["closed"].append(p)
                    self.log.append((mind.t, "closed", p))
            return
        def met(g):   # fulfilled: its holes filled, or closed into storage (not merely gone)
            if g in mind.pool:
                return not mind.pool[g].sites
            b = mind.boxes.get(g)
            return b is not None and not b.get("parked") and not b.get("told")
        for p in self.live():
            inf = self.info[p]
            k, a = inf["kind"], inf["anchor"]
            done = (k == "frustration" and met(a)) \
                or (k == "anger" and inf["grounded"] and inf["goal"] is not None and met(inf["goal"])) \
                or (k == "anxiety" and und and und.level(a) >= 0.5) \
                or (k == "sadness" and und and und.level(a) >= self.loss.get(a, 1.0))
            if done:
                del mind.pool[p]
                self.stored.pop(p, None)
                rec["closed"].append(p)
                self.log.append((mind.t, "closed", p))


# ---- designed worlds: a target structure made discoverable (THOUGHT_MOLECULES.md sec. 5j) -------

class Territory:
    """The territory register (REORG.md sec. 4, step 1; the user, 2026-10-24: territorial ownership,
    or the perception thereof, is the foundational motivation). One row per region (an object), read
    directly, never competing for a slot. It holds the agent's *perceived* ownership, not the answer
    key: a coincidence counts, and only a failed test corrects it.

    Written by the world the mind lives in, from what the agent perceives:
      claimed(push, pushed, changed)  a push's watch ended: the object pushed, and the objects
                                      changed while it was watched (each change's owner)
      moved(changed)                  objects that changed with no push of the agent's in flight

    A region's claims are the pushes on it and the pushes ever followed by a change in it. Each watch
    of a claim is a try on the region; it took if the region changed. Holding strength is the rate of
    claims taking, shrunk toward the agent's base rate b across all regions (the form blame uses,
    `Memory.error`, with kappa):  (took + kappa*b) / (tried + kappa).

    Holder, as perceived (the reading of strength against b, and of others' moves, is my choice):
      mine       held (strength above b) and nothing else seen moving it since it was claimed
      contested  held, and something else moves it too (a gust, a timer; later another agent)
      lost       was mine, strength fell to b, nothing else seen moving it
      another    strength at or below b (or never claimed) and something else moves it
      nobody     tried and never taking, nothing else moves it
      unknown    never tried, never seen moving
    b before any try is 1/2 (no record either way).

    The ownership SOV (step 2) is read off it: one SOV, its slot instances per region, molecules
    own:<kind>:<region> in their own track (own_slots), alive while the register says the slot is
    open, gone when it closes. Which slots open (REORG.md sec. 5; contested opens one too, the
    user's decision on a change out of the agent's control):
      unclaimed  claims never tried (perceived, or the region moved by something else): "what happens
                 if I push here?"
      control    tried and not taking (nobody): "what blocks it?"
      contested  held, and something else moves it too: "what else moves it?"
      lost       was mine, fell to b: "what took it?"
    another (tried, not taking, something else moves it) is a border: closed. mine opens nothing yet
    (uniqueness, step 6). Pull (times T), my choice within the user's order lost > control >
    unclaimed: unclaimed u = kappa/(kappa + other moves) (uniqueness weighting: a region something
    else also moves pulls less; at most 1); control and contested 1 + tried/(tried + kappa) (a claim
    started, more the more it was tried: in [1, 2)); lost 1 + held (at least 2: the more held, the
    more to lose). At the top an instance poses its question, own:q:<kind>:<region>, which fades by
    the half-life and leaves when its instance closes. Nothing reads the questions yet (step 3).
    """

    # what each kind needs of the claims on its region (contested needs nothing of the claims: its
    # question, "what else moves it?", is the changes' caused_by; first conditions of the claims too,
    # and the gust's flag paid its pushes' SOVs)
    NEEDS = dict(unclaimed=("causes",), control=("conditions",), contested=(), lost=("conditions",))

    QUESTION = dict(unclaimed="what happens if I push here?", control="what blocks it?",
                    contested="what else moves it?", lost="what took it?", uniqueness="is it mine alone?",
                    relation="will they be there?")

    def __init__(self, mind):
        self.mind = mind
        self.asked = {}  # question id -> (kind, region, tick posed)
        self.serves_of = {}    # instance id -> the concepts it serves
        self.parked = set()    # instances nothing could fill now (the parking rule)
        self.took_now = set()  # regions where a claim took since the phases last read the graph
        self.facts = frozenset()   # what the agent perceives now (set by the world the mind lives in)
        self.wants = {}        # region -> the change wanted there: a control slot the agent opens itself
                               # (REORG.md step 4, the force world: a wanted change is a region to hold)
        self.had = set()       # regions whose wanted change came: their control slot stays closed
        self.given_up = set()  # regions whose want was given up (Params.patience)
        self.gave_up_now = set()   # given up since the phases last read the graph
        self.helped_now = {}       # region -> who met the want there by their act, since the phases last read
        self.served = None     # concept -> (pay, relations needed): what the open instances fund (step 3);
                               # None while the register has no regions (the old triggers stand)
        self.momentum = {}     # (kind, region) -> progress momentum: a try on the region gave an outcome
        self.provided = None   # (kind, region) -> pull: the open instances, when the agent reads them off
                               # what it holds now (the thought world's possessions, minds, the body)
        self.rows = {}   # region -> dict(claims={push: [tried, took]}, other=int, other_since=int,
                         #                ever=bool, holder=str, history=[(tick, event)])

    def row(self, r):
        if r not in self.rows:
            self.rows[r] = dict(claims={}, other=0, other_since=0, ever=False, holder="unknown", history=[])
        return self.rows[r]

    def perceived(self, claims):
        """Regions perceived with their claims (region -> pushes on it): rows for them, claims untried."""
        for r, pushes in claims.items():
            row = self.row(r)
            for p in pushes:
                row["claims"].setdefault(p, [0, 0])

    def open_slots(self):
        """The ownership SOV's open slot instances: {(kind, region)}."""
        if self.provided is not None:
            return set(self.provided)
        out = {("relation", r) for r in self.relation_of()}
        for r, row in self.rows.items():
            tried = sum(c[0] for c in row["claims"].values())
            h = row["holder"]
            if r in self.wants:   # wanted, not yet had: a claim to make take, whatever its holder now
                out.add(("control", r))   # (REORG.md step 4)
            elif r in self.given_up:
                continue   # a want given up: its slot parked for good (nothing pays for it now)
            elif r in self.had and h in ("nobody", "another", "unknown"):
                continue   # had: the want's slot closed, however few of its tries took (first it fell back
                           # to "nobody" and reopened "what blocks it?" on a box already open; fiction ladder)
            elif h in ("unknown", "another") and not tried and (row["claims"] or row["other"]):
                out.add(("unclaimed", r))
            elif h == "nobody":
                out.add(("control", r))
            elif h in ("contested", "lost"):
                out.add((h, r))
            elif h == "mine":   # held: "is it mine alone?" stays open, answered by probes (REORG.md
                out.add(("uniqueness", r))   # sec. 5; first mine opened nothing, and an agent that
        return out                           # perceived everything as its own, on coincidences, went calm
                                             # and never tested a holding again)

    def pull(self, id):
        """An instance's (or its question's) pull, a multiple of T."""
        kind, r = id.split(":")[-2:]
        if self.provided is not None:
            return self.provided.get((kind, r), 0.0)
        row = self.rows.get(r)
        if row is None:
            return 0.0
        k = self.mind.p.kappa
        tried = sum(c[0] for c in row["claims"].values())
        if kind == "unclaimed":
            return self.mind.p.curiosity * k / (k + row["other"])   # temperament: curiosity
        if kind == "control":
            return 1.0 + tried / (tried + k)
        if kind == "contested":   # what is defended is how reliably it is mine now (the user,
            # 2026-10-24): 1 + holding strength x the uniqueness weight (REORG.md: a region something
            # else keeps moving pulls less). First 1 + held/2: the gust's flag, held on 20
            # coincidences, took the track 98 ticks of 150; a count, where lost's grief is the count
            return 1.0 + self.strength(r) * k / (k + row["other"])
        if kind == "lost":
            return 1.0 + self.held(r)
        if kind == "relation":   # "will they be there?": as hard as the slot it would help close, on the
            c = self.relation_of().get(r)   # region whose claim needs it (first a flat 1, the least of the
            x = next((x for x, rw in self.rows.items() if c in rw["claims"]), None) if c else None   # kinds,
            row = self.rows.get(x, {})   # and it never won the ownership track): the claim's control pull
            tried = sum(cc[0] for cc in row.get("claims", {}).values())
            return 1.0 + tried / (tried + k)
        if kind == "uniqueness":   # how much is still in doubt: how few tries back the holding, strong
            return k / (k + tried)  # on a coincidence, fading as probes confirm it (first 1 - strength:
                                    # with every early claim taking, b = 1, and one coincidence read as
                                    # certain)
        return 0.0

    def serve(self):
        """What the open instances fund (REORG.md step 3, the `serves` link): concept -> (pay, relations
        needed). An instance serves the claims on its region (the pushes, for the relation its kind
        needs: causes for unclaimed, conditions for control, contested and lost) and, but for
        unclaimed, the changes on its region (caused_by: what moves it). Pay is the instance's pull
        plus its momentum; a concept served by several takes the most. None while the register has
        no regions, or the agent provides its instances (the thought world reads them off what it
        holds): the old triggers stand there, until those minds' territory readings are decided."""
        if self.provided is not None or not any(row["claims"] for row in self.rows.values()):
            return None

        def reading(c):   # a gauge's reading (register_filling_+2): a detail of its change, not a concept
            tail = c.rsplit("_", 1)[-1]   # of its own to pay for (first paid one by one, and a contested
            try:                          # register's readings, each seen rarely, kept the calculator
                float(tail)               # agent waiting to watch what moved them)
                return True
            except ValueError:
                return False
        und = self.mind.understanding
        out = {}
        self.serves_of = {}   # instance id -> the concepts it serves (for cueing their SOVs)

        def fund(c, pay, needs):
            p, n = out.get(c, (0.0, ()))
            out[c] = (max(p, pay), tuple(sorted(set(n) | set(needs))))
            self.serves_of.setdefault(f"own:{k}:{r}", []).append(c)

        inv = self.mind.inquiry.actions if self.mind.inquiry else None
        for k, r in self.open_slots():
            pay = self.pull(f"own:{k}:{r}") + self.momentum.get((k, r), 0.0)
            needs = self.NEEDS.get(k, ())
            if k == "uniqueness":   # "you explore conceptually what's unique to you; which explains why we
                # form our own niches of specialization" (the user, 2026-10-24; REORG.md step 6): a held
                # region pays for every open relation of its concepts, as much as its hold is unique
                # (first it paid for nothing but probes, and lamp A, the agent's alone, stayed as thin
                # as lamp B, a timer's)
                pay = self.mind.p.curiosity * self.mind.p.kappa / (self.mind.p.kappa + self.rows[r]["other"])
                needs = tuple(und.RELS) if und else ()
                for c, o in (und.owners.items() if und else ()):
                    if o == r and c in und.rel and "_push:" not in c and not reading(c):
                        fund(c, pay, needs)
            if k == "contested" and self.rows[r].get("failed") and not self.rows[r]["other_since"]:
                needs = ("conditions",)   # contested by its own claim failing, nothing else seen moving
                                          # it: "what blocks it?" is the claims' conditions
            for c in self.rows[r]["claims"] if needs else ():
                if self.futile(c):   # its learned condition is not met here: nothing could fill it now, so it
                    continue         # is parked (the agent waits; S6-W03)
                if inv is not None and c not in inv:   # not invited now: nothing could fill it now, so
                    continue                           # it is parked, not paid (the parking rule; first
                                                       # paid, and a push invited only while a gust swung
                                                       # the flag held the SOV track 134 ticks of 150)
                fund(c, pay, needs)
            if k != "unclaimed" and und:
                for c, o in und.owners.items():
                    if o == r and c in und.rel and "_push:" not in c and not reading(c):
                        fund(c, pay, ("caused_by",))
        return out

    def live(self):
        """The open instances with a pull: open and not parked."""
        return {(k, r) for k, r in self.open_slots() if f"own:{k}:{r}" not in self.parked}

    def futile(self, c):
        """A claim predicted to do nothing in the situation now, by a reading the meta layer split from
        it (a learned condition, not yet met): its outcomes in this reading, two or more, mostly none."""
        meta = self.mind.meta
        if not meta or c not in meta.splits:
            return False
        hist = meta.modes.get(meta.reading_in(c, self.facts), [])
        none = sum(1 for h in hist if h[2] == frozenset({"no_change"}))
        return len(hist) >= 2 and none * 2 > len(hist)

    def unfillable(self):
        """Instances nothing could fill now, parked (the parking rule), where the register serves: one
        whose served concepts need nothing open, and a uniqueness instance with no claim invited to
        probe it (first they held the own track with nothing to do: a contested key whose movers were
        known kept the top, and the calculator agent pushed 6 times in 150 ticks)."""
        if self.served is None:
            return set()
        und, inv = self.mind.understanding, (self.mind.inquiry.actions if self.mind.inquiry else set())
        out = set()
        for k, r in self.open_slots():
            i = f"own:{k}:{r}"
            if self.rows.get(r, {}).get("gone"):   # its region is not here: nothing could fill it now (first a lost
                out.add(i)                         # toy's slot stayed live on its old changes' questions, and the
                continue                           # grief was refreshed forever; fiction ladder, rung 5)
            if k == "relation":   # parked only when its summoning claim is not invited now
                if self.relation_of().get(r) not in inv:
                    out.add(i)
                continue
            if k == "uniqueness":   # parked with no claim to probe and nothing of its concepts left to study
                if not any(c in inv for c in self.rows[r]["claims"]) and                         not any(und.needed(c) for c in self.serves_of.get(i, ())):
                    out.add(i)
            elif not any(und.needed(c) for c in self.serves_of.get(i, ())) and                     not (k == "contested" and any(c in inv for c in self.rows[r]["claims"])):
                out.add(i)   # (a contested region with an invited claim can still probe it)
        return out

    def observe(self, rec):
        """Each tick: the open instances are in the pool (refreshed: they live by the register, not by
        momentum); a closed one leaves with its question; one at the top poses its question."""
        mind = self.mind
        for key in list(self.momentum):   # momentum fades by the half-life without new tries
            self.momentum[key] *= 0.5 ** (1 / mind.p.h0)
            if self.momentum[key] < mind.p.floor:
                del self.momentum[key]
        self.served = self.serve()
        self.parked = self.unfillable()
        rec["own_open"], rec["own_closed"], rec["own_questions"] = [], [], []
        live = {f"own:{k}:{r}" for k, r in self.open_slots()} - self.parked
        for i in sorted(live):
            k, r = i.split(":")[1:]
            if i not in mind.pool:
                mind.pool[i] = clause(i, tags=("ownership", f"region:{r}"), sites=(f"{k}?{r}",))
            mind.pool[i].act = 1.0
            rec["own_open"].append(i)
        for i in [i for i in mind.pool if is_own(i) and not i.startswith("own:q:") and i not in live]:
            del mind.pool[i]
            rec["own_closed"].append(i)
        for q in [q for q in mind.pool if q.startswith("own:q:")]:
            if "own:" + q[6:] not in live:   # its instance closed: answered
                del mind.pool[q]
                self.asked.pop(q, None)
            else:
                mind.pool[q].act *= 0.5 ** (1 / mind.p.h0)
                if mind.pool[q].act < mind.p.floor:
                    del mind.pool[q]
                    self.asked.pop(q, None)
        for i in rec["levels"][-1]["winners"] if rec.get("levels") else ():
            if i in live and i in mind.pool:
                q = "own:q:" + i[4:]
                if q not in mind.pool:
                    k, r = i.split(":")[1:]
                    mind.pool[q] = clause(q, tags=("question", "ownership", f"region:{r}"), sites=(f"{k}?{r}",))
                    self.asked[q] = (k, r, mind.t)
                    rec["own_questions"].append(q)

    def base(self):
        """The agent's base rate of claims taking, over every region (1/2 before any try)."""
        tried = sum(c[0] for row in self.rows.values() for c in row["claims"].values())
        took = sum(c[1] for row in self.rows.values() for c in row["claims"].values())
        return took / tried if tried else 0.5

    def strength(self, r, b=None):
        row = self.rows.get(r)
        if row is None:
            return 0.0
        b = self.base() if b is None else b
        k = self.mind.p.kappa
        tried = sum(c[0] for c in row["claims"].values())
        took = sum(c[1] for c in row["claims"].values())
        return (took + k * b) / (tried + k) if tried else 0.0

    def held(self, r):
        """What was held: the claims on the region that took."""
        return sum(c[1] for c in self.rows.get(r, {}).get("claims", {}).values())

    def claimed(self, push, pushed, changed, predicted=None, seen=None):
        """A push's watch ended. Its claims: the region pushed, and every region it was ever followed
        by a change in (and those changed now). Each is tried; it took if the region changed and the
        changes predicted there came (the user's knowns: "my push filled the slot and the predicted
        effect came"; first any change, and a braced push that only pressed the block took as well as
        the slide it was predicted to give). With no prediction yet, a change is enough. A gauge's
        number is a detail, not a predicted change."""
        changed = set(changed)
        seen = set(seen or ())

        def gerund(e):
            tail = e.rsplit("_", 1)[-1]
            try:
                float(tail)
                return False
            except ValueError:
                return True

        def came(r):
            want = {e for e in (predicted or ()) if e.startswith(r + "_") and gerund(e)}
            return want <= seen
        regions = {pushed} | changed | {r for r, row in self.rows.items() if push in row["claims"]}
        for k, r in self.open_slots():   # a try on a region with an open slot: its investigation has
            if r in regions:              # momentum (moved here from the concept, REORG.md sec. 3)
                self.momentum[(k, r)] = 1.0
        for r in regions:
            row = self.row(r)
            c = row["claims"].setdefault(push, [0, 0])
            took = r in changed and came(r)
            c[0] += 1
            c[1] += took
            row["fails"] = 0 if took else row.get("fails", 0) + 1   # tries running that did not take
            if not took:
                row.setdefault("fail_times", []).append(self.mind.t)
            if took:
                self.took_now.add(r)
            if row["ever"]:   # a claim on a held region that didn't take: contested until one takes again
                row["failed"] = not took           # (the user, 2026-10-24: "a single failure opens
                                                   # contested, not lost")
        self.update(self.rows)   # b is every region's: each row is read against it again

    def moved(self, changed, effects=(), context=None):
        """Regions that changed with no push of the agent's in flight: something else moved them. The
        state each move left its region in is recorded (`other_to`), for the purpose behind them."""
        for r in set(changed):
            row = self.row(r)
            row["other"] += 1
            row["other_last"] = self.mind.t
            if row["ever"]:
                row["other_since"] += 1
        for e in effects:
            r = next((x for x in set(changed) if e.startswith(x + "_")), None)
            g = e[len(r) + 1:] if r else None
            if g and not g.lstrip("+-").replace(".", "").isdigit():
                self.record_other(r, g, context)
        self.update(self.rows)

    def record_other(self, r, g, context):
        """A move by something else left region r in state g, in this context (the facts)."""
        row = self.row(r)
        to = row.setdefault("other_to", {})
        to[g] = to.get(g, 0) + 1
        row.setdefault("other_moves", []).append((g, frozenset(context or ())))
        row.setdefault("other_times", []).append(self.mind.t)

    def unexplained(self, r, e, context=None):
        """A change on a region the agent's push did not act on and did not predict: recorded with the
        moves something else made (inside a watch: first only moves with no push in flight counted, and
        a neighbour whose pushes all fell inside the agent's watches was never seen moving anything)."""
        g = e[len(r) + 1:] if e.startswith(r + "_") else None
        if g and not g.lstrip("+-").replace(".", "").isdigit():
            self.record_other(r, g, context)

    def purpose(self, r):
        """The state something else keeps a region in, if its moves are directed (S6-W01; the user,
        2026-10-25: intentionality before identity): at least two moves by something else, every one
        leaving the region in the same state. A gust that moves it both ways has no single target. The
        agent infers a purposeful other from the pattern alone: nothing tells it a doer exists."""
        to = self.rows.get(r, {}).get("other_to", {})
        return next(iter(to)) if len(to) == 1 and sum(to.values()) >= 2 else None

    def goals(self, r):
        """The purposes behind something else's moves on a region, read by context (S6-W02, same action,
        different goal): {None: state} if every move leaves it in one state; {fact: state, "not " +
        fact: state} if a fact of the context splits the moves into two halves (two or more each), each
        to one state, the states different, as the meta layer splits a conflated push; None when no
        fact tells them apart: uncertain (the curriculum: remain uncertain when behaviour is
        ambiguous)."""
        p = self.purpose(r)
        if p:
            return {None: p}
        moves = self.rows.get(r, {}).get("other_moves", [])
        for tag in sorted(set().union(*(c for _, c in moves)) if moves else ()):
            if tag.startswith(r + "_"):   # the region's own state is where a move starts, not its context
                continue                  # (first counted: any toggle, a gust's too, split on it)
            yes = [g for g, c in moves if tag in c]
            no = [g for g, c in moves if tag not in c]
            if len(yes) < 2 or len(no) < 2:
                continue
            gy, gn = max(set(yes), key=yes.count), max(set(no), key=no.count)
            # each half 75% one state, the meta layer's tolerance for a boundary (first all of each
            # half, and one stray move kept a neighbour's two goals unread)
            if gy != gn and yes.count(gy) >= 0.75 * len(yes) and no.count(gn) >= 0.75 * len(no):
                return {tag: gy, "not " + tag: gn}
        return None

    def responsive(self, r, x, k=6):
        """Whether something else's moves on region r answer the agent's need on region x (S6-W03; the
        user, 2026-10-25: a relation is a purpose conditioned on the agent's own situation): its rate of
        moving r within k ticks after a claim of the agent's on x failed, against its rate at other
        times. The window is 6 ticks: a move seen inside a watch is stamped at the watch's end, up to 3
        ticks after it happened (first 3, and a partner's answers fell just outside). Returns (rate
        inside, rate outside, moves)."""
        self._outside = 1.0   # the share of its moves outside the windows (1 until there are any)
        self._expected_out = 0.0
        row = self.rows.get(r, {})
        need = self.needed_states(r, x)   # moves toward a state the agent's claim on x has taken in; the
        moves = [t for t, (g, _) in zip(row.get("other_times", []), row.get("other_moves", []))
                 if not need or g in need]  # rest (a spring seating it again) is not the other answering
        fails = self.rows.get(x, {}).get("fail_times", [])
        if not moves or not fails:
            return 0.0, 0.0, len(moves)
        near = lambda t: any(0 <= t - f <= k for f in fails)   # (a move inside the failed push's own watch
                                                               # is recorded at the same tick as the failure)
        span = max(1, self.mind.t)
        covered = set()   # the ticks within k after a failure
        for f in fails:
            covered.update(range(f, min(span, f + k + 1)))
        inside = sum(1 for t in moves if near(t))
        # its rate of moving inside those windows against its rate outside them (first the share of its
        # moves inside against the share of time they cover: with the agent trying often the windows
        # covered half the ticks, and a timed partner read as answering)
        rate_in = inside / max(1, len(covered))
        rate_out = (len(moves) - inside) / max(1, span - len(covered))
        self._outside = (len(moves) - inside) / len(moves)   # the share of its moves outside those windows
        # the moves one would expect outside the windows if it moved regardless of the agent: with the windows
        # covering nearly every tick (an agent that tries all the time) none are expected there, and none seen
        # is no evidence of answering (first read as a relation, and the wind, which blows on its own, was
        # summoned forty times; fiction ladder, rung 1)
        self._expected_out = len(moves) * (span - len(covered)) / span
        return round(rate_in, 3), round(rate_out, 3), len(moves)

    def needed_states(self, r, x):
        """The states of region r the agent's claims on region x have taken in (from the meta layer's
        record of their outcomes and the situations they came in)."""
        meta, out = self.mind.meta, set()
        if not meta:
            return out
        for c in self.rows.get(x, {}).get("claims", {}):
            todo = [c]
            while todo:
                y = todo.pop()
                for _, ctx, mode in meta.modes.get(y, []):
                    if mode != frozenset({"no_change"}) and any(e.startswith(x + "_") for e in mode):
                        out |= {f[len(r) + 1:] for f in ctx if f.startswith(r + "_")}
                if y in meta.splits:
                    todo += [meta.splits[y]["yes"], meta.splits[y]["no"]]
        return out

    def relation_of(self):
        """Relation slots (S6-W03; the user, 2026-10-25: "will they be there?"): region r -> the agent's
        claim on another region x whose outcome on r varies with nothing in the situation to tell when
        (the meta layer: unexplained, a hidden choice), where something else's moves on r answer the
        agent's failed claims on x (responsive: at most one of its moves in ten outside the windows after
        them, five moves or more (three let a timed partner in on chance); first twice its outside rate, and a timed partner, unable to start
        a hold while holding, read as answering). First: a
        claim futile alone, and a partner who always answered read as part of the push's own effect,
        so it never was; that is right, an always-answering partner is a mechanism. A relation is
        another's doing the agent can rely on but cannot be sure of."""
        if getattr(self, "_rel_at", None) == self.mind.t:   # once per tick (it is read by every pull)
            return self._rel
        out = {}
        meta = self.mind.meta
        self._rel_at, self._rel = self.mind.t, out
        if not meta:
            return out
        for x, row in self.rows.items():
            for c in row["claims"]:
                readings, todo = [], [c]
                while todo:
                    y = todo.pop()
                    readings.append(y)
                    if y in meta.splits:
                        todo += [meta.splits[y]["yes"], meta.splits[y]["no"]]
                for y in readings:
                    if y not in meta.unexplained:
                        continue
                    for e in meta.opposed(meta.modes.get(y, [])):
                        r = next((rr for rr in self.rows if e.startswith(rr + "_") and rr != x), None)
                        if not r:
                            continue
                        if not self.needed_states(r, x):   # what the claim needs is not known until it has
                            continue                       # taken once (first counted every move, and the
                                                           # spring, set off by the agent's own preparation,
                                                           # read as answering)
                        rate_in, rate_out, n = self.responsive(r, x)
                        seen_out = round(self._outside * n)
                        lam = self._expected_out   # P(this few outside | it moves regardless of the agent)
                        p_few = sum(math.exp(-lam) * lam ** j / math.factorial(j) for j in range(seen_out + 1))
                        if n >= 5 and self._outside <= 0.1 and p_few < 0.05:   # it moves almost only when the
                            # agent needs it, and that few moves outside would be unlikely if it did not answer
                            out[r] = c
        return out

    def others(self):
        """The purposeful others inferred: region -> the state kept there."""
        return {r: g for r in self.rows if (g := self.purpose(r))}

    def update(self, regions):
        b = self.base()
        t = self.mind.t
        for r in regions:
            row = self.rows[r]
            tried = sum(c[0] for c in row["claims"].values())
            took = sum(c[1] for c in row["claims"].values())
            s = self.strength(r, b)
            if row["ever"] and (row.get("gone") or row.get("lost_at") == took):
                # a held thing gone from view (taken: the world says who, `gone`) is lost, past any strength, and
                # stays lost until a claim on it takes again (first a region's holding was its claims' rate only,
                # and a toy carried off was still "mine"; fiction ladder, rung 5)
                if row.get("lost_at") is None:
                    row["lost_at"] = took
                h = "lost"
            elif tried and took and (s > b or took == tried):   # every try took: nothing contradicts it
                                                                # (first s > b alone, and with every claim
                                                                # taking, b = 1 and nothing was held)
                if not row["ever"]:
                    row["ever"] = True
                    row["other_since"] = 0
                # contested while the other's last move is still warm (it cools by the half-life, h0, below cold:
                # a contest no one keeps up is over; first contested for good once anyone else had moved it, and
                # Mara probed a latch Leo had long stopped touching; fiction ladder, rung 4)
                warm = 0.5 ** ((t - row.get("other_last", t)) / self.mind.p.h0) >= self.mind.p.cold
                h = "contested" if (row["other_since"] and warm) or row.get("failed") else "mine"
                row["below_since"] = None
            elif row["ever"]:
                # hysteresis (the user, 2026-10-24): a held region whose strength falls to b is contested
                # first; it goes lost (or another's) only if it stays below for the mind's half-life
                # (first lost at once, and the catch's latch and spring flipped mine, lost, mine)
                if row.get("below_since") is None:
                    row["below_since"] = t
                if t - row["below_since"] < self.mind.p.h0:
                    h = "contested"
                else:
                    h = "another" if row["other"] else "lost"
            elif row["other"]:
                h = "another"
            elif tried:
                h = "nobody"
            else:
                h = "unknown"
            if h != "lost":
                row["lost_at"] = None
            if h != row["holder"]:
                was = row["holder"]
                event = ("claimed" if h == "mine" and was in ("unknown", "nobody", "another") else
                         "re-tested" if h in ("mine", "contested") and was == "lost" else
                         "lost" if h == "lost" else h)
                row["history"].append((t, event))
                row["holder"] = h

    def readout(self):
        """The register as rows: region -> holder, strength, held, claims, the understanding of each
        claim's concept (the understanding register), history."""
        und, b = self.mind.understanding, self.base()
        out = {}
        for r, row in sorted(self.rows.items()):
            out[r] = dict(holder=row["holder"], strength=round(self.strength(r, b), 2), held=self.held(r),
                          claims={p: tuple(c) for p, c in sorted(row["claims"].items())},
                          understanding={p: round(und.level(p), 2) for p in row["claims"]} if und else {},
                          history=list(row["history"]))
        return out


class Inquiry:
    """Experiments as molecules (DRIFT.md; the user, 2026-10-23: "based on the structure of the SOV, it
    would suggest experiments that would promote understanding to resolve the hole. Where the
    experiment suggestions would be their own molecules that fight for attention").

    A standing question (an SOV's open slot, posed at the top) suggests experiments by its slot:
      causes?c     c is an action: do c.
      conditions?c c is an action: change something first, then do c (each other action that changes
                   something, and each not yet tried, as the change).
      caused_by?c  c is a change: do an action not yet tried, or wait and watch.
      co_occurs?c  wait and watch.
    And a push conflated with no boundary in the situation (meta: unexplained) is tried after a wait
    of one or two ticks: what is left to vary is the moment.
    An experiment is a molecule `exp:<slot>:<c>[:<first>]` whose activation is how open its slot is;
    it binds only to an instance of c, competes in its own track (exp_slots), and fades with its
    question. The world the mind lives in says which concepts are actions (`actions`); the one that
    wins the top is offered to it (rec["experiments"]), and an experiment done leaves the pool.
    """

    def __init__(self, mind):
        self.mind = mind
        self.actions = set()   # concepts that are actions now (set by the world the mind lives in)
        self.plans = {}        # experiment id -> (slot, concept, steps)
        self.done = {}         # experiment id -> times done
        self.leaves = {}       # action -> the facts its last try left (set by the world the mind lives in)
        self.still = False     # the world changes only when the agent acts (set by the world the mind lives in):
        # then waiting varies nothing, and experiments made only of waiting are not suggested (cognitive code
        # ladder, Gerundelle arm: in a code world the same fill was retried after a tick's wait, again and again)

    def concept(self, eid):
        return self.plans[eid][1] if eid in self.plans else eid.split(":", 3)[2]

    def decay(self, eid):
        """What an experiment is still worth for having been done before: q / (q + times done), q the mind's
        persistence (temperament; 1 is Inquiry's own 1 / (1 + done))."""
        q = self.mind.p.persistence
        return q / (q + self.done.get(eid, 0))

    def changes(self):
        """Actions that change something: seen to cause something (in the register)."""
        und = self.mind.understanding
        return {a for a in self.actions if und.funding(a, "causes") >= 1.0}

    def suggest(self, r, c):
        """The experiments a question about c's slot r suggests: [(id, steps)]."""
        und, out = self.mind.understanding, []
        tried = lambda a: und.funding(a, "causes") > 0
        if r == "causes" and c in self.actions:
            out.append((f"exp:causes:{c}", [c]))
        if r in ("causes", "conditions") and c in self.actions and self.mind.meta and c in self.mind.meta.unexplained                 and not self.still:   # (in a still world the moment does not vary: nothing is left to vary)
            # its outcomes split and nothing in the situation tells them apart: try it at another moment
            # (DRIFT.md: the earlier agent's rest ticks; their home is a conflation with no boundary)
            for k in (1, 2):
                out.append((f"exp:{r}:{c}:after_{k}", ["wait"] * k + [c]))
        if r == "conditions" and c in self.actions:   # and a situation not yet tried, where a boundary
            firsts = self.preparations(c)              # may yet show (first: elif, and a gust's flag swing
                                                       # that marked the lid unexplained left it timing alone)
            new = self.untried_for(c)   # a change that makes a situation c was never tried in is the one
            leads = [a for a in firsts   # to try first: only it can show a
                     if any(e in new for (rel, e) in und.rel.get(a, {}) if rel == "causes")]   # condition
            # a condition the mind was told is a hypothesis to test: what would bring it about is the
            # preparation to try first (a push known to cause it, else a push on the object it is about). First
            # told receipts reached the register and no experiment, and a mind told "the latch holds it shut"
            # went back to the flag (fiction ladder, rung 2; the finding: Attest reached understanding, not action)
            told = [o for (rel, o), e in und.rel.get(c, {}).items()
                    if rel == "conditioned_by" and e[1] > 0 and not o.startswith("not:")]
            told_leads = [a for a in self.preparations(c) if any(("causes", o) in und.rel.get(a, {}) for o in told)]
            if told and not told_leads:
                objs = {o.rsplit("_", 1)[0] for o in told}
                told_leads = [a for a in self.preparations(c) if und.owners.get(a) in objs]
            # no lead, in a still world: a known preparation can only re-make a known situation (nothing else moves
            # between tries), and only one not yet tried can make a situation c was never tried in. First the four
            # first known changes, and in a code world of 159 fills the same four were re-tried before every run,
            # one 29 times, and the answer was never tried (the cognitive code ladder, Gerundelle arm). Not in a
            # moving world: there a known preparation may meet a new moment (applied everywhere, it moved T78's
            # specialization: one seed of five lost)
            untried_preps = [a for a in firsts if und.funding(a, "causes") <= 0] if self.still else []
            rest = leads or untried_preps[:4] or firsts[:4]   # (first: the alphabetically first changes, and the
                                                              # latch was never parted before the lid was pushed)
            if told_leads and self.mind.p.credulity < 0.5:   # a skeptic tests the alternatives beside the word
                firsts = told_leads + [a for a in rest if a not in told_leads]
            else:
                firsts = told_leads or rest
            for a in firsts:
                out.append((f"exp:conditions:{c}:{a}", [a, c]))
        if r == "caused_by" and c not in self.actions:
            for a in sorted(a for a in self.actions if not tried(a))[:2]:
                out.append((f"exp:caused_by:{c}:{a}", [a]))
            if not self.still:   # waiting to watch: nothing comes in a still world but what the agent does
                out.append((f"exp:caused_by:{c}:wait", []))
        elif r == "co_occurs" and c in self.actions:   # what an action comes with: seen by doing it
            out.append((f"exp:co_occurs:{c}", [c]))
        elif r == "co_occurs" and not self.still:
            out.append((f"exp:co_occurs:{c}:wait", []))
        return out

    def preparations(self, c):
        """What could be changed before c: each other action that changes something, and each not yet
        tried."""
        und = self.mind.understanding
        out = sorted(self.changes() - {c}) + sorted(a for a in self.actions - {c} if und.funding(a, "causes") <= 0)
        # one ruled out ("not:a", its experiment found the push as usual) is answered: not suggested again
        # (first suggested on, and a gust's coincidence kept the flag pushes ahead of the latch)
        return [a for a in out if ("conditioned_by", f"not:{a}") not in und.rel.get(c, {})]

    def untried_for(self, c):
        """The facts c has been tried with fewer than twice (an outcome that comes in some tries and not
        others counts from twice each way: the meta layer's `opposed`): changes the actions cause,
        seen in under two of the situations recorded for c's readings (the meta register's modes,
        through its splits)."""
        meta = self.mind.meta
        if meta is None:
            return set()
        seen, todo, n = {}, [c], 0
        while todo:
            x = todo.pop()
            for _, ctx, _ in meta.modes.get(x, []):
                n += 1
                for f in ctx:
                    seen[f] = seen.get(f, 0) + 1
            if x in meta.splits:
                todo += [meta.splits[x]["yes"], meta.splits[x]["no"]]
        if not n:
            return set()
        made = {e for a in self.actions for (rel, e) in self.mind.understanding.rel.get(a, {}) if rel == "causes"}
        # in a still world once is enough: a situation gives the outcome it gave (twice is for a moving world, where an
        # outcome can come and go; with twice nearly every fill in a code world was a lead, and the one that made a
        # situation never tried did not stand out; the cognitive code ladder, Gerundelle arm)
        return {e for e in made if seen.get(e, 0) < (1 if self.still else 2)}

    def observe(self, rec):
        mind, und = self.mind, self.mind.understanding
        m0 = mind.p.sov_m0
        standing = set()
        for q, (c, r) in und.questions.items():
            if q not in mind.pool:
                continue
            value = 1.0 - min(1.0, und.funding(c, r) / m0)   # how open the slot is
            if mind.territory.served is not None:   # times what the ownership slot it serves pays (step 3)
                value *= mind.territory.served.get(c, (0.0, ()))[0]
            for eid, steps in self.suggest(r, c):
                standing.add(eid)
                self.plans[eid] = (r, c, steps)
                v = value * self.decay(eid)   # the same experiment again teaches less
                if v < mind.p.floor:   # worth nothing more: not offered
                    continue
                if eid in mind.pool:
                    mind.pool[eid].act = max(mind.pool[eid].act, v)
                else:
                    mind.pool[eid] = clause(eid, tags=("experiment", f"about:{c}"), sites=(f"{r}?{c}",))
                    mind.pool[eid].act = v
        terr = mind.territory   # a uniqueness question ("is it mine alone?") suggests probes: try a claim
        for q in [q for q in mind.pool if q.startswith(("own:q:uniqueness:", "own:q:contested:"))]:   # on the
            r = q.split(":")[-1]   # region again; its outcome tests the holding. A contested region probes
            kind = q.split(":")[2]   # too: still held, "is the change mine?" stays open beside "what else
            if r not in terr.rows:   # moves it?" (first only uniqueness, and a block contested by a gust
                continue             # kept the effect of one push tried in the gust, never tried again)
            for c in sorted(a for a in terr.rows[r]["claims"] if a in self.actions and not terr.futile(a)):
                eid = f"exp:probe:{c}"   # (a claim predicted to do nothing here is not probed: parked)
                standing.add(eid)
                self.plans[eid] = ("probe", c, [c])
                v = terr.pull(f"own:{kind}:{r}") * self.decay(eid)
                if v < mind.p.floor:
                    continue
                if eid in mind.pool:
                    mind.pool[eid].act = max(mind.pool[eid].act, v)
                else:
                    mind.pool[eid] = clause(eid, tags=("experiment", f"about:{c}"), sites=(f"probe?{c}",))
                    mind.pool[eid].act = v
        meta = mind.meta   # a want whose way is known but whose condition is not met, and not the agent's to
        for r, goal in sorted(terr.wants.items()) if meta and not self.still else ():   # make (its own preparations ruled out, or
            for c in sorted(terr.rows.get(r, {}).get("claims", {})):   # none known to make it): wait for it,
                if c not in meta.splits:                              # watching (S6-W03: the agent waits). An
                    continue                                          # experiment like the others, paid by
                sp = meta.splits[c]                                   # the want's control pull, fading with
                tag = sp["tag"]                                       # repeats: whether a mind waits or
                if tag in terr.facts:                                 # wanders off is its pulls' doing
                    continue
                if not any(goal in h[2] for h in meta.modes.get(sp["yes"], [])):
                    continue
                makers = [a for a in self.actions if tag in self.leaves.get(a, ())]   # pushes seen to leave it
                if any(("conditioned_by", f"not:{a}") not in und.rel.get(c, {}) for a in makers):
                    continue   # the agent can bring it about itself: a preparation, not a wait
                eid = f"exp:await:{c}"
                standing.add(eid)
                self.plans[eid] = ("await", c, ["wait"])
                v = terr.pull(f"own:control:{r}") * self.decay(eid)
                if v < mind.p.floor:
                    continue
                if eid in mind.pool:
                    mind.pool[eid].act = max(mind.pool[eid].act, v)
                else:
                    mind.pool[eid] = clause(eid, tags=("experiment", f"about:{c}"), sites=(f"await?{c}",))
                    mind.pool[eid].act = v
        for q in [q for q in mind.pool if q.startswith("own:q:unclaimed:")]:   # "what happens if I push here?",
            r = q.split(":")[-1]   # posed at the top (curiosity about the region): its claims' own causes
            if r not in terr.rows:   # experiments are what answer it, paid by the instance's pull (REORG step 3:
                continue             # the questions read. First unread, and a mind curious about the latch
            pay = terr.pull(f"own:unclaimed:{r}")   # pushed the flag; fiction ladder, rung 0)
            for c in sorted(a for a in terr.rows[r]["claims"] if a in self.actions and und.funding(a, "causes") <= 0):
                eid = f"exp:causes:{c}"
                standing.add(eid)
                self.plans[eid] = ("causes", c, [c])
                v = pay * self.decay(eid)
                if v < mind.p.floor:
                    continue
                if eid in mind.pool:
                    mind.pool[eid].act = max(mind.pool[eid].act, v)
                else:
                    mind.pool[eid] = clause(eid, tags=("experiment", f"about:{c}"), sites=(f"causes?{c}",))
                    mind.pool[eid].act = v
        for q in [q for q in mind.pool if q.startswith("own:q:relation:")]:   # "will they be there?": try the
            r = q.split(":")[-1]   # claim to signal the need (it won't take alone), then again once the watch
            c = terr.relation_of().get(r)   # ends; whether the other came is the answer (the user, 2026-10-25:
            if not c or c not in self.actions:   # the claim is the probe, not the intended action)
                continue
            eid = f"exp:summon:{c}"
            standing.add(eid)
            self.plans[eid] = ("summon", c, [c, c])
            v = terr.pull(f"own:relation:{r}") * self.decay(eid)
            if v >= mind.p.floor:
                if eid in mind.pool:
                    mind.pool[eid].act = max(mind.pool[eid].act, v)
                else:
                    mind.pool[eid] = clause(eid, tags=("experiment", f"about:{c}"), sites=(f"summon?{c}",))
                    mind.pool[eid].act = v
        for eid in [i for i in mind.pool if is_exp(i) and i not in standing]:
            del mind.pool[eid]   # its question is answered or forgotten
        top = [i for i in rec["levels"][-1]["winners"] if is_exp(i) and i in mind.pool]
        bids = rec["levels"][-1]["bids"]
        rec["experiments"] = sorted(top, key=lambda i: (-bids.get(i, 0.0), i))

    def result(self, eid, same):
        """What an experiment found. A conditions experiment whose push came out as it usually does
        (same) rules its preparation out: "not this", funding the slot by one part in as many
        preparations as were suggested; all ruled out, the question is answered ("it turns on none of
        these"). First a conditions slot with no condition to find stayed open forever, and its
        experiments cycled."""
        if eid not in self.plans:
            return
        r, c, steps = self.plans[eid]
        if r == "conditions" and same and len(steps) == 2:
            und = self.mind.understanding
            ruled = sum(1 for (rel, o) in und.rel.get(c, {}) if rel == "conditioned_by" and o.startswith("not:"))
            # in a still world, every preparation there is, those already ruled out too (preparations() leaves them
            # out: counted among those left, later ones weigh more, and in a code world the run's question closed at
            # about two thirds; 2026-10-28). Not in a moving world: tried there, the null world's agent stopped
            # experimenting before every preparation was ruled out, its slots never closed, and it went quiet with its
            # graph still live, the reverse of T80's collapse. Open: when a question should stop, in a world where the
            # agent can stop asking it
            n = max(1, len(self.preparations(c)) + (ruled if self.still else 0))   # one part in every preparation (first: in
                                                     # those suggested, and with one lead suggested, one
                                                     # ruled out nearly closed the slot)
            # each part a 1/n share of the funding at which a slot stops being open (1.0, Understanding.open_slots),
            # so the question is answered when all are ruled out, as above. First m0/n: a part written in the units of
            # understanding (m0) against a question that closes in the units of answering (1.0), so it closed when half
            # were ruled out, against this docstring and DRIFT.md's fix ("one part in all preparations", against
            # closing early). In a code world of 159 fills the half rule closed the run's question after 64 runs, the
            # want's slot parked, and the agent surveyed fills instead of testing them (the cognitive code ladder,
            # Gerundelle arm). The user, 2026-10-28: the honest repair, everywhere. Three tests had grown around the
            # half rule and were repaired to test what they describe (T79's sadness against a no-push control, T80's
            # null world given the ticks its collapse now takes, T71 rechecked)
            und.add(c, "conditioned_by", f"not:{steps[0]}", "worked", 1.0 / n)
            und.inert.add(f"not:{steps[0]}")

    def carried(self, q):
        """Whether a question has experiments of its own in the pool to carry it."""
        return any(p[1] == self.mind.understanding.questions[q][0] and p[0] == self.mind.understanding.questions[q][1]
                   and eid in self.mind.pool for eid, p in self.plans.items())

    def did(self, eid):
        """The world did the experiment: it leaves the pool (asked again only by its question)."""
        self.done[eid] = self.done.get(eid, 0) + 1
        self.mind.pool.pop(eid, None)


class DesignedWorld:
    """A world built from a target structure so that experience of it can teach that structure.

    target: typed links over role names, ("causes", X, Y) or ("conditions", C, X). names: role ->
    clause id (the domain). How a link becomes experience:
      causes X Y      Y is perceived on the tick after X.
      conditions C X  X goes well (outcome +1) when C is present and badly (-1) when it is absent;
                      each episode C is present at random with probability p. With gate=True,
                      X's effects (what it causes) also happen only when C holds: C enables X.
    A chain step with nothing conditioning it is good when it is a leaf (it gives the chain stakes).
    Episodes are separated by gaps of random noise. A decoy clause is either absent, present at
    random independently of everything (an honest world), or present exactly when the first
    condition is (a shortcut world: condition and decoy cannot be told apart from experience).
    Deterministic for a seed.
    """

    def __init__(self, target, names, gaps=(1, 3), noise=6, p=0.5, decoy=None, decoy_name="a_blue_light", seed=0,
                 gate=False):
        self.target, self.names, self.gate = list(target), dict(names), gate
        self.gaps, self.noise, self.p, self.decoy, self.decoy_name = gaps, noise, p, decoy, decoy_name
        self.rng = random.Random(seed)
        self.conds = {}
        for r, a, b in self.target:
            if r == "conditions":
                self.conds.setdefault(b, []).append(a)
        caused = {b for r, a, b in self.target if r == "causes"}
        self.steps = {a: [b for r, x, b in self.target if r == "causes" and x == a] for a in self.roles()}
        self.roots = [x for x in self.roles() if x not in caused and x not in {a for r, a, b in self.target if r == "conditions"}]

    def roles(self):
        return sorted({x for _, a, b in self.target for x in (a, b)})

    def episode(self):
        on = {c: self.rng.random() < self.p for cs in self.conds.values() for c in cs}
        first = sorted(on)[0] if on else None
        shortcut = self.decoy == "correlated" and first is not None and on[first]
        ticks, frontier = [], list(self.roots)
        states = [clause(self.names[c]) for c in sorted(on) if on[c]] + ([clause(self.decoy_name)] if shortcut else [])
        while frontier:
            ins, out, nxt = [], 0, []
            for x in frontier:
                ins.append(clause(self.names[x]))
                held = all(on[c] for c in self.conds.get(x, ()))
                if x in self.conds:
                    out = 1 if held else -1
                elif not self.steps[x]:
                    out = out or 1
                if held or not self.gate:   # gate: a conditioned step's effects happen only when its condition holds
                    nxt += self.steps[x]
            ticks.append((states + ins if not ticks else ins, out))
            frontier = nxt
        for _ in range(self.rng.randint(*self.gaps)):
            ticks.append(([clause(f"n{self.rng.randrange(self.noise)}")], 0))
        # an honest decoy varies independently in time too: at a random tick of the episode or its gap
        # (first: on the root step's tick, which put it in exactly the root's place in the structure)
        if self.decoy == "independent" and self.rng.random() < self.p:
            k = self.rng.randrange(len(ticks))
            ticks[k] = (ticks[k][0] + [clause(self.decoy_name)], ticks[k][1])
        return ticks

    def plan(self, ticks):
        out = []
        while len(out) < ticks:
            out += self.episode()
        return out[:ticks]

    def run(self, mind, ticks):
        for ins, outcome in self.plan(ticks):
            mind.tick(ins, outcome=outcome)
        return mind

    def learned(self, mind):
        """(best share of the target any mapping preserves, share the intended mapping preserves).
        The second is what was learned: the first can be reached through a stand-in."""
        score, _ = mind.understanding.match(self.target)
        edges = mind.understanding.edges()
        intended = sum((r, self.names[a], self.names[b]) in edges for r, a, b in self.target) / len(self.target)
        return score, intended


def curriculum(mind, library, ticks_per_world, rounds, seed=0, adaptive=True):
    """Pick the next world from a library of DesignedWorld makers: adaptively the target the mind has
    learned least (a fully learned one is spent and retired), or round robin. Returns the picks."""
    picks = []
    for k in range(rounds):
        if adaptive:
            scored = [(world(seed + k).learned(mind)[1], i) for i, world in enumerate(library)]   # intended, not a stand-in
            live = [x for x in scored if x[0] < 1.0]
            if not live:
                break
            i = min(live)[1]
        else:
            i = k % len(library)
        picks.append(i)
        library[i](seed + k).run(mind, ticks_per_world)
    return picks


# ---- acting: rule-based worlds and MCTS -----------------------------------------------------
#
# A world offers: start(), actions(s), step(s, a) -> (s2, reward, seen), percepts(s) -> clause ids
# the person perceives in s, clause(id) -> the Molecule for a percept id, and own(s, corrections)
# -> the person's model of it (the rules they know, corrected by held recognitions).

ACTIONS = ("wait", "call", "shop")


class World:
    """The step-2 scene. State: (t, called, shopped). Weather is a fixed schedule.

    call_needs_sun: the true rule that she only answers on sunny ticks. The person's own model
    (used inside MCTS) does not know it.
    """
    CLAUSES = {"it_is_raining": ("rain",), "it_is_sunny": (), "she_answered": (), "she_didnt_answer": (),
               "i_have_groceries": (), "i_got_wet": ()}

    def __init__(self, weather, call_needs_sun=True):
        self.weather = weather
        self.call_needs_sun = call_needs_sun

    def sky(self, t):
        return self.weather[min(t, len(self.weather) - 1)]

    def start(self):
        return (0, False, False)

    def actions(self, s):
        return ACTIONS

    def percepts(self, s):
        return ["it_is_raining" if self.sky(s[0]) == "rain" else "it_is_sunny"]

    def clause(self, id):
        return clause(id, tags=self.CLAUSES.get(id, ()))

    def own(self, s, corrections):
        return PersonModel(World([self.sky(s[0])], call_needs_sun=False), corrections)

    def step(self, s, a):
        t, called, shopped = s
        sky = self.sky(t)
        reward, seen = 0.0, []
        if a == "call" and not called:
            if sky == "sun" or not self.call_needs_sun:
                reward, called = 1.0, True
                seen.append("she_answered")
            else:
                reward = -0.3
                seen.append("she_didnt_answer")
        elif a == "shop" and not shopped:
            reward, shopped = 1.0, True
            seen.append("i_have_groceries")
            if sky == "rain":
                reward -= 0.5
                seen.append("i_got_wet")
        return (t + 1, called, shopped), reward, seen


RULES = frozenset(("sun_call", "rain_wets", "store_closes", "friend_sun", "events"))
PLACES = ("home", "store", "park")

# Events (sec. 5d): things that happen to the person. p: probability of arriving on a tick it is
# not already active; life: ticks it lasts; responses: action -> (reward, seen, effect) while it
# lasts; expire: (reward, seen) if it ends unanswered; soak: reward per tick while active for a
# person at the park, with what they see.
# needs: what the event would have to be bonded from, the open sites it gets when the person
# decomposes it on arrival (thread sec. 7): what it means for me, and what I do about it.
EVENTS = {
    "a_storm_rolls_in": dict(p=0.15, life=3, tags=("weather", "storm"), needs=("wet", "indoors"), responses={},
                             expire=(0.0, []), soak=(-0.5, "i_got_soaked")),
    "someone_calls_my_name": dict(p=0.15, life=2, tags=("voice", "person"), needs=("who",),
                                  responses={"answer_voice": (0.5, ["it_was_my_friend"], None)},
                                  expire=(-0.2, ["they_walked_away"]), soak=None),
    "the_phone_rings": dict(p=0.1, life=2, tags=("phone", "call"), needs=("call",),
                            responses={"pick_up": (1.0, ["she_answered"], "called")},
                            expire=(-0.3, ["missed_her_call"]), soak=None),
}
# Goals come in through voices (the user, 2026-10-22): someone says it, and the person hears it
# open on its key, the percept that would fulfil it. The saying lasts a tick; the want lasts until
# it is filled. `goal` links the heard clause to an action, for MCTS guidance.
VOICES = {
    "she_says_call_me": dict(p=0.35, life=1, tags=("voice", "goal"), heard=("she_answered",), goal="call",
                             responses={}, expire=(0.0, []), soak=None),
    "we_need_groceries": dict(p=0.35, life=1, tags=("voice", "goal"), heard=("i_have_groceries",), goal="shop",
                              responses={}, expire=(0.0, []), soak=None),
    "my_friend_asks_me_over": dict(p=0.35, life=1, tags=("voice", "goal"), heard=("greeted_friend",), goal="greet",
                                   responses={}, expire=(0.0, []), soak=None),
}
EVENTS.update(VOICES)
EVENT_CLAUSES = {"it_was_my_friend": ("who", "person", "friend"), "they_walked_away": ("voice", "bad"),
                 "missed_her_call": ("call", "bad"), "i_got_soaked": ("wet", "storm")}


class BigWorld:
    """Step 3b. State: (t, place, umbrella, called, shopped, greeted, events). Weather is a schedule;
    events (sec. 5d) arrive by chance from the world's own seeded random source, and sit in the
    state as (name, ticks left).

    rules: which of the true rules this world applies. The real world applies all of them; the
    person's own model applies only the ones in `known` (none, by default), carries the events
    already present but does not spawn new ones (rng None), and offers their responses without
    knowing what they pay. Everything else (moving, taking the umbrella, shopping, calling,
    greeting) the person knows.
    """
    CLOSES = 5   # the store is closed from this tick on
    CLAUSES = {
        "it_is_raining": ("sky", "rain"), "it_is_sunny": ("sky", "sun"),
        "i_am_home": ("place", "home", "indoors"), "i_am_at_store": ("place", "store", "indoors"),
        "i_am_at_park": ("place", "park", "outdoors"),
        "i_have_umbrella": ("carrying", "umbrella"),
        "it_is_early": ("time", "early"), "it_is_late": ("time", "late"),
        "store_is_open": ("store", "open"), "store_is_closed": ("store", "closed"),
        "friend_is_here": ("friend", "present"), "friend_is_not_here": ("friend", "absent"),
        "she_answered": ("call", "good"), "she_didnt_answer": ("call", "bad"),
        "i_have_groceries": ("groceries",), "i_got_wet": ("wet",), "greeted_friend": ("friend", "good"),
    }
    FACTS = {   # standing conditions: held in the facts register, enter the pool only when they change
        "it_is_raining": "sky", "it_is_sunny": "sky",
        "i_am_home": "place", "i_am_at_store": "place", "i_am_at_park": "place",
        "i_have_umbrella": "carrying", "it_is_early": "time", "it_is_late": "time",
        "store_is_open": "store", "store_is_closed": "store",
        "friend_is_here": "friend", "friend_is_not_here": "friend",
    }

    @property
    def GOALS(self):
        """Heard clause -> the action it is about (the goals that come in through this world's voices)."""
        return {name: e["goal"] for name, e in self.events.items() if e.get("goal")}

    def __init__(self, weather, rules=RULES, known=frozenset(), events=None, seed=0, rng=True):
        self.weather, self.rules, self.known = weather, frozenset(rules), frozenset(known)
        self.events = events if events is not None else dict(VOICES)
        self.rng = random.Random(seed) if rng else None
        self.seed = seed

    def sky(self, t):
        return self.weather[min(t, len(self.weather) - 1)]

    def start(self):
        return (0, "home", False, False, False, False, ())

    def actions(self, s):
        t, place, umbrella, called, shopped, greeted, events = s
        out = ["wait"]
        for name, _ in events:
            out += [a for a in self.events[name]["responses"] if a not in out]
        if not called:
            out.append("call")
        out += ["go_" + p for p in PLACES if p != place]
        if place == "home" and not umbrella:
            out.append("take_umbrella")
        if place == "store" and not shopped:
            out.append("shop")
        if place == "park" and not greeted:
            out.append("greet")
        return tuple(out)

    def responses(self, s):
        """The actions the events happening now offer."""
        return {a for name, _ in s[6] for a in self.events[name]["responses"]}

    def store_open(self, t):
        return not ("store_closes" in self.rules and t >= self.CLOSES)

    def friend_here(self, t):
        return not ("friend_sun" in self.rules and self.sky(t) != "sun")

    def percepts(self, s):
        t, place, umbrella, events = s[0], s[1], s[2], s[6]
        out = ["it_is_raining" if self.sky(t) == "rain" else "it_is_sunny",
               "i_am_home" if place == "home" else "i_am_at_" + place,
               "it_is_late" if t >= self.CLOSES else "it_is_early"]
        if umbrella:
            out.append("i_have_umbrella")
        if place == "store":
            out.append("store_is_open" if self.store_open(t) else "store_is_closed")
        if place == "park":
            out.append("friend_is_here" if self.friend_here(t) else "friend_is_not_here")
        out += [name for name, _ in events]   # what is happening
        return out

    def clause(self, id):
        if id in self.events:
            return clause(id, tags=self.events[id]["tags"] + ((id,) if self.events[id].get("goal") else ()))
        return clause(id, tags=self.CLAUSES.get(id) or EVENT_CLAUSES.get(id, ()))

    def own(self, s, corrections):
        return PersonModel(BigWorld([self.sky(s[0])], rules=self.known, known=self.known,
                                    events=self.events, rng=False), corrections)

    def step(self, s, a):
        t, place, umbrella, called, shopped, greeted, events = s
        sky = self.sky(t)
        reward, seen = 0.0, []
        responded = set()
        for name, _ in events:
            e = self.events[name]
            if a in e["responses"]:
                responded.add(name)
                if "events" in self.rules:
                    r, saw, effect = e["responses"][a]
                    reward += r
                    seen += saw
                    if effect == "called":
                        called = True
        if a == "call" and not called:
            if sky == "sun" or "sun_call" not in self.rules:
                reward, called = 1.0, True
                seen.append("she_answered")
            else:
                reward = -0.3
                seen.append("she_didnt_answer")
        elif a.startswith("go_") and a[3:] != place:
            place = a[3:]
            if sky == "rain" and "rain_wets" in self.rules and not umbrella:
                reward = -0.5
                seen.append("i_got_wet")
        elif a == "take_umbrella" and place == "home" and not umbrella:
            umbrella = True
        elif a == "shop" and place == "store" and not shopped:
            if self.store_open(t):
                reward, shopped = 1.0, True
                seen.append("i_have_groceries")
            else:
                reward = -0.2
        elif a == "greet" and place == "park" and not greeted:
            if self.friend_here(t):
                reward, greeted = 1.0, True
                seen.append("greeted_friend")
            else:
                reward = -0.2
        # events: what is happening acts on the person, then runs down, then new ones arrive
        nxt = []
        for name, left in events:
            e = self.events[name]
            if name in responded:
                continue
            if "events" in self.rules and e["soak"] and place == "park":
                reward += e["soak"][0]
                seen.append(e["soak"][1])
            if left > 1:
                nxt.append((name, left - 1))
            elif "events" in self.rules:
                reward += e["expire"][0]
                seen += e["expire"][1]
        if self.rng is not None:
            active = {name for name, _ in nxt}
            for name, e in self.events.items():
                if name not in active and self.rng.random() < e["p"]:
                    nxt.append((name, e["life"]))
        return (t + 1, place, umbrella, called, shopped, greeted, tuple(nxt)), reward, seen


class PersonModel:
    """The person's own rules, corrected by the recognitions they currently hold.

    A held recognition carries an expected prediction error for one action; simulated rewards for
    that action add the mean over the recognitions held. See Agent.held for what counts as held.
    """

    def __init__(self, rules, corrections):
        self.rules = rules
        self.corrections = corrections   # action -> expected prediction error

    def actions(self, s):
        return self.rules.actions(s)

    def expected(self, s, a):
        return self.rules.step(s, a)[1]

    def step(self, s, a):
        s2, r, seen = self.rules.step(s, a)
        if r != 0.0 or a in self.corrections:
            r += self.corrections.get(a, 0.0)
        return s2, r, seen


def mcts(model, s, prior, budget=6, horizon=3, c=1.0, prefer=(), value=False, gamma=1.0):
    """PUCT over the person's own model; deterministic rollouts, no randomness.

    The model is deterministic, so the chosen action is the one whose best path found is highest
    (ties: more visits, then the model's action order). Choosing by visits alone let a strong
    prior outvote the values. `prior` maps an action to its weight; unlisted actions get 1.
    """
    N, W, B = {}, {}, {}
    z = sum(prior.get(a, 1.0) for a in model.actions(s))

    def pick(path, state):
        acts = model.actions(state)
        untried = [a for a in acts if N.get(path + (a,), 0) == 0]
        if untried:   # every action is tried once before any is favoured (an unvisited action
            # scored as 0 lost to the first one tried whenever values were positive)
            return max(untried, key=lambda a: (prior.get(a, 1.0), -acts.index(a)))
        n_tot = sum(N.get(path + (a,), 0) for a in acts)
        best = None
        for a in acts:
            k = path + (a,)
            n = N.get(k, 0)
            q = W.get(k, 0.0) / n if n else 0.0
            u = q + c * (prior.get(a, 1.0) / z) * math.sqrt(n_tot + 1) / (1 + n)
            if best is None or u > best[0]:
                best = (u, a)
        return best[1]

    for _ in range(budget):
        path, state, total, visited = (), s, 0.0, []
        for depth in range(horizon):
            a = pick(path, state)
            path = path + (a,)
            state, r, _ = model.step(state, a)
            total += gamma ** depth * r   # imagination's discount (the force world's gamma); 1: none
            visited.append(path)
            if N.get(path, 0) == 0:
                break
        for k in visited:
            N[k] = N.get(k, 0) + 1
            W[k] = W.get(k, 0.0) + total
            B[k] = max(B.get(k, -math.inf), total)
    acts = model.actions(s)
    # ties in value: a response offered by what is happening now (prefer) wins (the user,
    # 2026-10-22); then more visits; then the model's action order
    best = max(acts, key=lambda a: (round(B.get((a,), -math.inf), 9), a in prefer, N.get((a,), 0), -acts.index(a)))
    if value:   # and the best path's value (2026-10-23: a want's planner tells "no way known" from a plan)
        return best, B.get((best,), -math.inf)
    return best


class Memory:
    """The memory register: the structure of successes and failures, read directly by MCTS.

    Each action's base rate of prediction error over every try (shrunk toward the rules' own
    prediction with `kappa`); each (action, clause) error over the tries with that clause present,
    shrunk toward the base rate; the recognitions formed from the contrasts; how often each action
    was tried in each situation. None of it has to win a slot to act on a decision.
    """

    def __init__(self, kappa, theta, min_count, explore, clause_for):
        self.kappa, self.theta, self.min_count, self.explore = kappa, theta, min_count, explore
        self.clause_for = clause_for
        self.resid = {}   # (action, clause) -> [sum, count] of prediction errors with the clause present
        self.total = {}   # action -> [sum, count] of prediction errors over every try
        self.recog = {}   # recognition id -> (action, clause)
        self.tries = {}   # (action, situation) -> how often the action was tried in that situation
        self.tries_log = {}   # action -> [(clauses present, prediction error)] per try (for explaining away)

    def base(self, a):
        """The action's own lesson: its mean prediction error, shrunk toward the rules' prediction (0)."""
        s, n = self.total.get(a, (0.0, 0))
        return s / (n + self.kappa)

    def error(self, a, m):
        """Contrast: the error with m present, shrunk toward the action's base rate, minus the base rate."""
        s, n = self.resid.get((a, m), (0.0, 0))
        b = self.base(a)
        return (s + self.kappa * b) / (n + self.kappa) - b

    def curiosity(self, a, situation):
        """What trying a here would teach: the novelty of the (action, situation) pair, falling with
        how often a has been tried in this situation (the set of the world's percepts this tick)."""
        return self.explore / (1 + self.tries.get((a, situation), 0))

    def corrections(self, actions, situation, active):
        """What the register says about each action here: own lesson + curiosity + active contrasts."""
        out = {a: self.base(a) + self.curiosity(a, situation) for a in actions}
        for rid in active:
            a, m = self.recog[rid]
            out[a] = out.get(a, self.base(a)) + self.error(a, m)
        return out

    def record(self, a, present, err):
        """Record the error of action a for its base rate and against the clauses present, then re-read
        every record of a. Returns (formed, dropped) recognition ids."""
        tot = self.total.setdefault(a, [0.0, 0])
        tot[0] += err
        tot[1] += 1
        for m in present:
            e = self.resid.setdefault((a, m), [0.0, 0])
            e[0] += err
            e[1] += 1
        self.tries_log.setdefault(a, []).append((frozenset(present), err))
        formed, dropped = [], []
        # every record of this action is re-read: the contrast is over the records, and new
        # evidence from one clause can make another's failures stand out in hindsight
        contrasts = {m: self.error(a, m) for (a2, m) in self.resid if a2 == a}
        for m in sorted(contrasts):
            c = contrasts[m]
            rid = f"{m}~{a}:{'worse' if c < 0 else 'better'}"
            explained = self.explained(a, m, c, contrasts)
            for r in [r for r, am in self.recog.items() if am == (a, m)]:
                if abs(c) < self.theta / 2 or r != rid or explained:   # faded, sign flipped, or explained away
                    del self.recog[r]
                    dropped.append(r)
            if self.resid[(a, m)][1] >= self.min_count and abs(c) >= self.theta and not explained \
                    and a in self.clause_for and m != self.clause_for[a] and rid not in self.recog:
                self.recog[rid] = (a, m)
                formed.append(rid)
        return formed, dropped

    def explained(self, a, m, c, contrasts):
        """Explaining away: m's contrast is explained by a stronger clause r of the same sign if,
        among the tries where r was present, m's presence makes less than half theta of a
        difference (first: no such test, so a clause that happened to be present only on the
        failures a stronger clause explains, like needing groceries on rainy calls, formed its own
        recognition). If r was never present without m, the data cannot tell them apart and m is
        kept."""
        log = self.tries_log.get(a, [])
        for r, cr in contrasts.items():
            if r == m or abs(cr) <= abs(c) or (cr < 0) != (c < 0):
                continue
            with_m = [e for p, e in log if r in p and m in p]
            without = [e for p, e in log if r in p and m not in p]
            if with_m and without and abs(sum(with_m) / len(with_m) - sum(without) / len(without)) < self.theta / 2:
                return True
        return False


class Agent:
    """Mind + world. Top-level winners guide MCTS; what is seen comes back as clauses.

    Recognitions come from surprise. Each action keeps the base rate of its prediction error over
    every try (shrunk toward the rules' own prediction with `kappa`, the percept predictor's
    shrinkage), and each (action, clause) the error over the tries with that clause present,
    shrunk toward the base rate the same way. A clause earns blame
    only by its contrast: the shrunk error with it present minus the base rate. "Present" is what
    the person sees this tick and what they recognize (see blamed). When a clause's contrast
    reaches `theta` after `min_count` presences, a recognition forms: a bond between that clause
    and the clause linked to the action, carrying the contrast. It is dropped when the contrast
    falls below half of `theta` or changes sign. If an action is only ever tried in one situation,
    nothing stands out; exploratory tries are what tell the situations apart. All of this is held
    in the memory register (Memory).

    The simulated reward of an action adds its base rate (the action's own lesson), a curiosity
    bonus (see curiosity: the novelty of trying it in this situation; without it the base rate
    alone taught helplessness), and the contrasts of the recognitions active. A recognition acts on action as an edge: it is active
    whenever its clause is perceived this tick and the action's clause is present. It does not
    have to win a slot for that; it is also cued into the pool, where it competes like any
    molecule, to be examined.
    """

    def __init__(self, mind, world, catalog=None, links=None, guide=3.0, budget=50, min_count=2, theta=0.3,
                 kappa=None, explore=0.5, facts=True):
        self.mind, self.world = mind, world
        self.catalog = catalog or {}                               # hand-written clauses (goals)
        self.links = links if links is not None else getattr(world, "GOALS", {})
        self.guide, self.budget, self.min_count, self.theta = guide, budget, min_count, theta
        self.kappa = mind.p.kappa if kappa is None else kappa
        self.explore = explore   # exploration: a bored pool tries what it has not tried in this situation
        self.clause_for = {a: c for c, a in self.links.items()}
        self.memory = Memory(self.kappa, theta, min_count, explore, self.clause_for)
        # the facts register: standing percepts (the world's FACTS) are held in a slot and enter the
        # pool only when they change; off, every percept is presented every tick
        self.fact_slots = getattr(world, "FACTS", {}) if facts else {}

    # the memory register's contents, under the names the scenarios use
    recog = property(lambda self: self.memory.recog)
    resid = property(lambda self: self.memory.resid)
    total = property(lambda self: self.memory.total)
    tries = property(lambda self: self.memory.tries)

    def linked(self, id, out):
        m = self.mind.pool.get(id)
        meta = self.mind.meta
        root = id
        while meta and root in meta.parent:   # a distinction keeps its parent's link
            root = meta.parent[root]
        if root in self.links:
            out.add(self.links[root])
        if m:
            for j in m.parts:
                self.linked(j, out)
        return out

    def base(self, a):
        return self.memory.base(a)

    def error(self, a, m):
        return self.memory.error(a, m)

    def recognition(self, rid):
        a, m = self.recog[rid]
        return bond(rid, m, self.clause_for[a], tags=(f"reason_{a}",))

    def clause(self, id):
        return self.catalog.get(id) or self.world.clause(id)

    def curiosity(self, a, situation):
        return self.memory.curiosity(a, situation)

    def active(self, inputs):
        """Recognitions acting on action this tick: their clause is perceived and the action's clause is
        present (in the pool or perceived)."""
        seen = set(inputs)
        out = set()
        for rid, (a, m) in self.recog.items():
            if m in seen and (self.clause_for[a] in self.mind.pool or self.clause_for[a] in seen):
                out.add(rid)
        return out

    def blamed(self, rec, seen):
        """Clauses the prediction error is recorded against: what the person sees this tick and what they
        recognize (every base clause that won a slot or is a part of a winning composite). A world
        percept recalled from storage is a memory, not evidence about the world now, so percepts
        count only when seen. Bonds and composites are not blamed themselves."""
        out = set(seen)
        percepts = getattr(self.world, "CLAUSES", {})

        def walk(i):
            m = self.mind.pool.get(i)
            if m is None or m.bond or is_meta(i) or is_sov(i) or is_phase(i):
                return   # thoughts about thinking, understanding work and phases are not blamed (first they were)
            if m.parts:
                for j in m.parts:
                    walk(j)
            elif i not in percepts:   # a world percept counts only when seen now, not when recalled
                out.add(i)
        for i in rec["reached"]:
            walk(i)
        return out

    def notice(self, a, present, err):
        """Record the error in the memory register; a recognition formed while its clause is present is
        cued into the pool to be examined, and a dropped one leaves it. Returns the recognitions formed."""
        formed, dropped = self.memory.record(a, present, err)
        und = self.mind.understanding
        for rid in formed:   # a recognition: its clause conditions the action's goal (worked out)
            if und and self.recog[rid][0] in self.clause_for:
                und.add(concept_of(self.recog[rid][1]), "conditions", self.clause_for[self.recog[rid][0]], "worked")
        for r in dropped:
            self.mind.remove(r)
        for rid in formed:
            if self.recog[rid][1] in present:
                self.mind.present(self.recognition(rid))
        return formed

    def confidence(self, corrections, active, situation):
        """Confidence follows understanding (sec. 5g): a lesson whose clause is poorly understood
        counts for less (down to half); trying an action whose goal is poorly understood is worth
        more (curiosity up to doubled)."""
        und = self.mind.understanding
        if not und:
            return corrections
        out = dict(corrections)
        for rid in active:
            a, m = self.recog[rid]
            if a in out:
                out[a] -= (1 - und.level(concept_of(m) or m)) * 0.5 * self.error(a, m)
        for a in out:
            c = self.clause_for.get(a)
            if c:
                out[a] += (1 - und.level(c)) * self.curiosity(a, situation)
        return out

    def read_facts(self, percepts):
        """Hold standing percepts in the facts register. Returns the percepts that enter the pool: a
        fact whose slot was empty or held another value (a change), and every non-fact percept."""
        news, held = [], {}
        for i in percepts:
            slot = self.fact_slots.get(i)
            if slot is None:
                news.append(i)
                continue
            held[slot] = self.clause(i)
            if slot not in self.mind.facts or self.mind.facts[slot].id != i:
                news.append(i)
        self.mind.facts = held   # a slot no longer perceived is cleared; clearing is not a thought
        return news

    def episode(self, length, start):
        self.mind.pool = {}
        self.mind.prev = set()
        self.mind.pending = []
        self.mind.facts = {}
        s = self.world.start()
        inputs = list(start)
        log = []
        for _ in range(length):
            percepts = self.world.percepts(s)
            situation = frozenset(percepts)
            news = self.read_facts(sorted(situation))
            everything = inputs + sorted(situation)   # all that is readable: pool, register, outcomes
            inputs += news                            # what enters the pool
            gen, self.mind.pending = self.mind.pending, []
            self.mind.perceive(inputs + [m.id for m in gen])
            self.mind.contradict(everything)
            events = getattr(self.world, "events", {})
            for i in inputs:
                if i in events and events[i].get("heard"):   # a voice: heard open on its key, a want
                    if i not in self.mind.pool:
                        self.mind.hear(self.clause(i), events[i]["heard"])
                elif i in events:   # an experience: arrives told and is decomposed (thread sec. 7)
                    self.mind.experience(self.clause(i), events[i]["needs"])
                else:
                    self.mind.present(self.clause(i))
            for m in gen:
                self.mind.present(m)
            for rid, (_, m) in self.recog.items():   # cued recall, to be examined
                if m in inputs:
                    self.mind.present(self.recognition(rid))
            rec = self.mind.think()
            held = {m.id for m in self.mind.facts.values()}
            for i in self.mind.top(rec):   # a fact taken in: it leaves the pool and stays in the register
                if i in held:
                    self.mind.remove(i)
            acts = set()
            for i in self.mind.top(rec):
                self.linked(i, acts)
            prior = {a: 1.0 + self.guide for a in acts}
            active = self.active(everything)
            corrections = self.confidence(self.memory.corrections(self.world.actions(s), situation, active),
                                          active, situation)
            own = self.world.own(s, corrections)
            prefer = self.world.responses(s) if hasattr(self.world, "responses") else ()
            a = mcts(own, s, prior, budget=self.budget, prefer=prefer)
            expected = own.expected(s, a)
            self.tries[(a, situation)] = self.tries.get((a, situation), 0) + 1
            s, reward, seen = self.world.step(s, a)
            formed = self.notice(a, self.blamed(rec, everything), reward - expected)
            outcome = (reward > 0) - (reward < 0)
            self.mind.learn(rec, outcome)
            log.append(dict(rec=rec, action=a, reward=reward, seen=seen, top=self.mind.top(rec),
                            active=sorted(active), formed=formed, state=s, entered=list(inputs)))
            inputs = list(seen)
        return log
