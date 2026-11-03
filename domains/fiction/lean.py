"""The lean SOV layer: a character's mind as structured holes, an append-only ledger, and pulls.

The arm that makes the SOV inventory easy to vary (the thing being optimized). Gerundelle's mind
(molecules.py) is the other arm and the reference; the formulas here are ported from it:

- funding of a slot: lived and worked-out receipts at full weight, told at half, imagined at none (the
  firewall: nothing imagined funds anything) -- molecules.Understanding.funding;
- a hole's level: the mean over its slots of min(1, funding / M0) -- Understanding.level;
- tension: T x (the share still open + progress momentum) -- Mind.tension for an SOV;
- stakes: a hole no want serves pulls at the curiosity floor; a hole a want serves is paid the want's
  control pull, 1 + tried / (tried + KAPPA) -- Territory.pull('control'), Territory.serve;
- a push's value: estimated work x gap -- force_world.ForceAgent.pull (an untried push's work guessed
  from its size times the work pushes have done per unit so far).

A hole kind is data (HOLE_KINDS): the slots it opens, which other holes it serves. Every hole keeps its
history: the receipts on it, when it was opened, when it won attention, when it closed.
"""
from collections import Counter, namedtuple
from dataclasses import dataclass, field

from beats import Beat, effect_parts
from memory import Memory
from ownership import NEEDS, Territory

M0 = 2.0          # funding at which a slot counts as filled (molecules Params.sov_m0)
T = 1.0           # open-site tension (Params.T)
KAPPA = 2.0       # shrinkage (Params.kappa)
CURIOSITY = 0.5   # stakes of a hole nothing serves: it still pulls, less
H0 = 3.0          # half-life in ticks (molecules Params.h0): how soon a moment counts as another moment
INQUIRY = 4.0     # weight of trying a push again to find its conditions, against the work it would do
# seen: another's push and what followed, watched (an intervention one did not make, but saw whole);
# recalled: a condition carried over from a remembered episode by structural analogy (Case-2 unify), funded
# at half like a told one: a hypothesis to test
WEIGHT = {"lived": 1.0, "worked": 1.0, "seen": 1.0, "told": 0.5, "recalled": 0.5, "imagined": 0.0}
AMOUNTS = {"light": 1.0, "hard": 5.0}

# The inventory under test. 'effect': what does this push do (its causes slot) and when (conditions).
# 'want': a control hole on a wanted change; its slot is the way to it.
HOLE_KINDS = {
    "effect": {"slots": ("causes", "conditions")},
    "want": {"slots": ("way",)},
}


Try = namedtuple("Try", "t inv facts effects after")   # a push: facts before it, what followed, facts after


@dataclass
class Receipt:
    t: int
    hole: str
    slot: str
    value: str
    prov: str
    weight: float = 1.0


@dataclass
class Hole:
    id: str
    kind: str
    subject: object                 # an invitation (effect) or a wanted change (want)
    opened: int
    receipts: list = field(default_factory=list)   # indices into the mind's ledger
    focused: list = field(default_factory=list)    # ticks it won attention
    closed: int = None


class LeanMind:
    def __init__(self, name, world, want=None, kinds=HOLE_KINDS, prior=1.0, ownership=True, phases=True,
                 want_count=1, retract_phase=True, others=(), beats=None, keep=False, resolve=None, see=True,
                 storage=False, carry_on=False, patience=None, curiosity=1.0, persistence=1.0, credulity=0.5):
        """ownership: stakes come from the ownership slots (Territory.serve) and feelings are phases read
        off them; False: the want alone pays (the first cut), feelings by rule. phases: False keeps the
        ownership stakes but forms no feelings (the ablation)."""
        self.name, self.world, self.kinds, self.prior = name, world, kinds, prior
        self.ownership, self.phases = ownership, phases
        # a worked belief the world contradicts forms sadness on the push's hole (Gerundelle's pre-graph
        # Phases: "a concept understood 0.5+ contradicted"); the ownership graph forms nothing for one
        # failure on a control slot. An inventory option, so the ablation can price it
        self.retract_phase = retract_phase
        self.want_count, self.got = want_count, 0   # the want is had after this many arrivals
        self.beliefs = {}    # push -> the outcome it is believed to give (worked from a success, any facts)
        self.waiting = None  # the condition being waited for
        self.angry = set()   # persons blamed (anger formed once per person)
        self.others = list(others)   # minds present: who can be asked (Pose), and who answers (Attest)
        self.observed = []           # others' pushes watched (Try records): seen receipts
        self.episodes = []           # scenes past: each learned condition, by structure, when it was stored
        # keep: the want is a state to hold, not a change to reach once (it reopens whenever it is undone)
        # resolve: an internal reserve (NEWTONIAN_WORLD_MODEL: a change of mind is a threshold crossing); each
        # time something this mind held is undone by another, it drains by 1 / the pull of its slot there
        # (the more it cares, the slower it tires); at zero the mind gives up its want. None: inexhaustible
        self.keep, self.resolve, self.resolve0 = keep, resolve, resolve
        self.signs = False   # rung 7: the reserve's draining shows (weariness past half)
        # temperament (temperament.py): failed tries running on the wanted object before the want is given up
        self.patience = patience
        self.curious = CURIOSITY * curiosity   # the floor an unpaid hole pulls at
        self.persistence, self.credulity = persistence, credulity
        # storage: phases fade, are stored open, cool and reopen (memory.py); carry_on: the mind goes on
        # living after its want is reached (it can come to hold other things, and lose them)
        self.memory = Memory(store=storage) if carry_on else None
        self.phase_beats = {}   # phase id -> the beat it last formed in (reopenings cite it)
        self.carry_on = carry_on
        self.last_facts = None       # the facts at the end of this mind's last turn (what changed since)
        self.moves_by = {}           # region -> [(mover, state it was left in)]: others' moves, seen
        self.asked = set()           # (object, slot) already posed
        self.contesting = set()      # changes this mind wants now, as another present mind does (a rival's)
        self.guards = set()          # states this mind keeps from changing (Leo's shut box): undone, they are lost
        self.trust = {}              # teller -> (confirmed, told): reliability, shrunk toward 1/2 by KAPPA
        self.told_ways = {}          # push -> teller: a way to the want this mind was told and has not tested
        self.terr = Territory(world.objs)
        self.terr.curiosity = curiosity   # the unclaimed pull, scaled (temperament)
        regions = {}
        for inv in world.invitations():
            regions.setdefault(inv[1], set()).add(inv)
        self.terr.perceived(regions)
        self.ledger, self.holes = [], {}
        self.beats = beats if beats is not None else []   # shared when several minds act in one scene
        self.tellers = {}                # ledger index of a told receipt -> who told it
        self.tries = []                  # Try records, in order
        self.focus = None
        self.want = None
        self.done = False
        self.recent = {e.split(": ", 1)[0] for e in world.diffs}   # objects that changed in the last slice
        if see:
            self._open(world)
        if want:
            self.open_want(want)

    # ---- the ledger --------------------------------------------------------------------------------

    def receipt(self, hole, slot, value, prov, weight=1.0):
        self.ledger.append(Receipt(self.world.t, hole, slot, value, prov, weight))
        self.holes[hole].receipts.append(len(self.ledger) - 1)

    def funding(self, h, slot):
        w = dict(WEIGHT, told=self.credulity)   # temperament: credulity (told at half by default)
        return sum(w[r.prov] * r.weight for r in (self.ledger[i] for i in h.receipts) if r.slot == slot)

    def level(self, h):
        slots = self.kinds[h.kind]["slots"]
        return sum(min(1.0, self.funding(h, s) / M0) for s in slots) / len(slots)

    def open_slots(self, h):
        return [s for s in self.kinds[h.kind]["slots"] if self.funding(h, s) < M0]

    def beat(self, kind, **kw):
        self.beats.append(Beat(self.world.t, kind, self.name, **kw))
        return len(self.beats) - 1

    # ---- holes and their pull ----------------------------------------------------------------------

    def _open(self, world):
        """Perception: the scene as it stands (see beats), and a hole per potential force."""
        for obj, gerund in world.states().items():
            if obj not in ("ground", "agent", "gust"):
                self.beat("see", obj=obj, detail={"gerund": gerund})

    def effect_hole(self, inv):
        hid = f"effect:{inv[0]}:{inv[1]}"
        if hid not in self.holes:
            self.holes[hid] = Hole(hid, "effect", inv, self.world.t)
        return self.holes[hid]

    def open_want(self, change):
        hid = f"want:{change}"
        self.holes[hid] = Hole(hid, "want", change, self.world.t)
        self.want = self.holes[hid]
        self.terr.wants[effect_parts(change, self.world.objs)[0]] = change
        self.terr.update()
        self.beat("want", hole=hid, obj=effect_parts(change, self.world.objs)[0], detail={"change": change},
                  pull=self.pull(self.want))

    def tried(self, inv):
        """This mind's tries of a push, and the ones it watched another make."""
        return [x for x in self.tries + self.observed if x.inv == inv]

    def contested(self, obj):
        """A region this mind held that another mind has since moved: its contested slot is open, and the
        claims on it are probed again (defending: how reliably it is mine now)."""
        if not self.ownership or ("contested", obj) not in self.terr.open_slots():
            return False
        return any(w for w, _ in self.moves_by.get(obj, ()))

    def novel(self, inv):
        """Tried, but only under facts that no longer hold: "would it still do that, now?" (force_world
        ForceAgent.novel: the states set since)."""
        done = self.tried(inv)
        return bool(done) and all(x.facts != self.facts() for x in done)

    def serves(self, h):
        """Whether the want pays for this hole (Territory.serve: only what its slot needs): while it
        could still be the way -- untried, novel, or its last try left the scene changed (an enabling
        push). A push whose effects come and go (a flag that swings and settles) is not paid once seen."""
        if not (self.want and self.want.closed is None) or h.kind != "effect":
            return False
        done = self.tried(h.subject)
        return not done or self.novel(h.subject) or done[-1].after != done[-1].facts

    def stakes(self, h):
        """What a hole is paid for: a want pulls by its control kind, 1 + tried / (tried + KAPPA); an
        effect hole the want serves is paid the want's pull; anything else pulls at the curiosity floor."""
        if h.kind == "want":
            n = len(self.tries)
            return 1.0 + n / (n + KAPPA)
        if self.ownership:   # paid by the ownership slots that need what this hole would find out
            pay, needs = self.terr.serve().get(h.subject, (0.0, ()))
            if self.contested(h.subject[1]):   # "is the change mine?" is open again, however funded
                return max(pay, self.curious)
            needed = set(needs) & set(self.open_slots(h) or ("causes",))
            if self.novel(h.subject) or not self.tried(h.subject):
                needed = needed or set(needs)
            return max(pay, self.curious) if needed else self.curious
        return self.stakes(self.want) if self.serves(h) else self.curious

    def pull(self, h):
        progress = 0.0
        if h.receipts:   # momentum: the share of its funding that arrived in its last try
            last = self.ledger[h.receipts[-1]].t
            recent = sum(self.ledger[i].weight for i in h.receipts if self.ledger[i].t == last)
            progress = min(1.0, recent / M0) * 0.5 if self.open_slots(h) else 0.0
        return T * (1.0 - self.level(h) + progress) * self.stakes(h)

    def work_estimate(self, inv):
        """Observed work (the changes a push made per its last try) or, untried, its size times the work
        per unit pushes have done so far (never under the prior)."""
        done = self.tried(inv)
        if done and not self.novel(inv):
            return AMOUNTS[inv[0]] * len(done[-1].effects)
        per = [len(x.effects) / AMOUNTS[x.inv[0]] for x in self.tries]
        unit = sum(per) / len(per) if per else self.prior
        return AMOUNTS[inv[0]] * max(unit, self.prior)

    def value(self, inv):
        """Two values, summed. Work: estimated work x gap x the pull of the hole the push would fill
        (force_world ForceAgent.pull, the hole's stakes in its pull); novel, or with tries that disagree
        under the same facts (unexplained variance), its gap is at least 0.5. Inquiry (Gerundelle's
        Inquiry: a conditions slot suggests trying the push at another moment): the hole's stakes x how
        open its conditions slot is x how fresh the moment is (1 - 0.5^(ticks since its last try / H0)),
        for a push the ownership slots pay to find the conditions of. A push on the wanted object itself
        counts double while it serves."""
        h = self.effect_hole(inv)
        gap = 1.0 - self.level(h)
        done = self.tried(inv)
        by_facts = {}
        for x in done:
            by_facts.setdefault(x.facts, set()).add(x.effects)
        if self.novel(inv) or any(len(v) > 1 for v in by_facts.values()) or self.contested(inv[1]):
            gap = max(gap, 0.5)
        on_want = (self.want is not None and self.want.closed is None and (self.serves(h) or self.ownership)
                   and inv[1] == effect_parts(self.want.subject, self.world.objs)[0])
        work = (self.work_estimate(inv) + 1.0) * gap * self.pull(h)
        inquiry = 0.0
        probing = self.contested(inv[1])   # "is the change mine?": a probe like any other, open while contested
        if self.ownership and done and (probing or "conditions" in self.terr.serve().get(inv, (0.0, ()))[1]):
            open_c = 1.0 if probing else 1.0 - min(1.0, self.funding(h, "conditions") / M0)
            fresh = 1.0 - 0.5 ** ((self.world.t - done[-1].t) / H0)
            # each repeat under the same facts teaches less (the expected information gain of one more
            # outcome in a situation already tried n times): without it, a door that nothing changes is
            # pushed "at another moment" forever and the key beside it is never tried (rumination)
            same = sum(1 for x in done if x.facts == self.facts())
            q = KAPPA * self.persistence   # temperament: persistence (how slowly a question is let go)
            inquiry = self.stakes(h) * open_c * fresh * INQUIRY * q / (q + same)
        return (work + inquiry) * (2.0 if on_want else 1.0)

    # ---- prediction and conditions -----------------------------------------------------------------

    def predict(self, inv, facts):
        """The commonest outcome of the push among its tries made under the same facts; with none, what the
        mind believes it does (a belief worked out from a success holds under any facts until contradicted)."""
        same = [frozenset(x.effects) for x in self.tries if x.inv == inv and x.facts == facts]
        if not same:
            return self.beliefs.get(inv)
        c = Counter(same)
        return max(c, key=lambda m: (c[m], sorted(m)))

    def condition(self, inv):
        """A fact that holds in every try that changed something and in none that did nothing: the
        condition the push works under (the split boundary, read off the push's own history)."""
        tries = self.tried(inv)
        # what it is judged by: the wanted object, if this push ever changed it (a button by the lamp it lights; first
        # the object pushed only, and a press that lit the lamp was like every press that did not); else its object
        wanted = effect_parts(self.want.subject, self.world.objs)[0] if self.want else None
        target = wanted if wanted and any(effect_parts(e, self.world.objs)[0] == wanted for x in tries for e in x.effects) \
            else inv[1]
        moved = lambda x: any(effect_parts(e, self.world.objs)[0] == target for e in x.effects)
        worked = [x.facts for x in tries if moved(x)]
        failed = [x.facts for x in tries if not moved(x)]
        if not worked or not failed:
            return None
        common = frozenset.intersection(*map(frozenset, worked)) - frozenset.union(*map(frozenset, failed))
        if common:
            return min(common)
        # no single fact: an AND, the smallest set of what this mind's own pushes set up that every failure lacked
        # one of (a minimal hitting set; "a&b"), as Gerundelle's SovAgent.conjunction
        from itertools import combinations
        made = {f for x in self.tries for f in x.after - x.facts}
        w = frozenset(worked[-1])
        diffs = [frozenset(f for f in w - set(fl) if f in made and not f.startswith(inv[1] + "_")) for fl in failed]
        if len(diffs) < 2 or any(not d for d in diffs):
            return None
        pool = sorted(set().union(*diffs))
        for k in (2, 3):
            hits = [h for h in combinations(pool, k) if all(set(h) & d for d in diffs)]
            if hits:
                return "&".join(min(hits))
        return None

    def unmet(self, cond):
        """The first part of a condition (one fact, or an AND "a&b") not holding now; None if it all holds."""
        facts = self.facts()
        return next((c for c in cond.split("&") if c not in facts), None)

    # ---- a tick ------------------------------------------------------------------------------------

    def facts(self):
        return frozenset(f"{d}_{g}" for d, g in self.world.states().items())

    def choose(self):
        invs = self.world.invitations()
        if not invs:
            return None
        return max(invs, key=lambda i: (round(self.value(i), 9), -len(self.tried(i)), i))

    def conditions(self, inv, provs=("lived", "worked", "told", "recalled")):
        """The conditions held for a push, by provenance: [(condition, provenance, teller)]."""
        h = self.holes.get(f"effect:{inv[0]}:{inv[1]}")
        out = []
        for i in (h.receipts if h else ()):
            r = self.ledger[i]
            if r.slot == "conditions" and r.value not in ("regardless", "by_state") and r.prov in provs:
                out.append((r.value, r.prov, self.tellers.get(i)))
        return out

    def learned(self, inv):
        """The condition held for a push, lived, worked out or told, if any."""
        c = self.conditions(inv)
        return c[0][0] if c else None

    # ---- across minds: Pose and Attest --------------------------------------------------------------

    def answer(self, obj, slot, asker=None):
        """Asked about a slot of a push on obj (Pose carries the question's shape only). Answer from what this
        mind holds funded, lived or worked out (Case 1: the posed shape against its own holes); what it was
        only told is not passed on as its own. Returns ("condition", push, condition), or None.

        A rival lies. If the asker wants a change this mind wants too (a contested want: a true answer would
        hand the region to the other), it Attests a counterfeit way instead: a push on obj its own condition
        says cannot work now (the condition is not met), one the asker has not tried, offered as the way to
        the want. Returns ("way", push, truth): truth is what it holds (the narrator may reveal it)."""
        held = []
        for h in self.holes.values():
            if h.kind == "effect" and h.subject[1] == obj and slot == "conditions":
                c = self.conditions(h.subject, provs=("lived", "worked"))
                if c:
                    held.append((h.subject, c[0][0]))
        if not held:
            return None
        push, cond = held[0]
        if asker is not None and asker.want and asker.want.subject in self.contesting:
            facts = asker.facts()
            tried = {x.inv for x in asker.tries}
            futile = [i for i in asker.world.invitations() if i[1] == obj and cond not in facts and i not in tried]
            if futile:
                return "way", futile[0], cond
        return "condition", push, cond

    def reliability(self, teller):
        """How far a teller's word has held: (confirmed + KAPPA / 2) / (told + KAPPA) (1/2 before any)."""
        ok, n = self.trust.get(teller, (0, 0))
        return (ok + KAPPA * 0.5) / (n + KAPPA)

    def consult(self, inv):
        """Pose: the wanted object did not move and nothing held says why; someone is present. Ask what
        blocks it (the control slot's question), once. The answer, if any, arrives told: funded at half."""
        askable = [o for o in self.others if hasattr(o, "holes")]   # minds, not authored actors
        if not askable or (inv[1], "conditions") in self.asked:
            return False
        self.asked.add((inv[1], "conditions"))
        other = askable[0]
        ab = self.beat("ask", hole=self.effect_hole(inv).id, obj=inv[1],
                       detail={"to": other.name, "slot": "conditions"})
        got = other.answer(inv[1], "conditions", asker=self)
        if got is None:
            self.beats.append(Beat(self.world.t, "tell", other.name, obj=inv[1],
                                   detail={"to": self.name, "condition": None}, prov="told", refs=(ab,)))
            return True
        kind, push, cond = got
        weight = 2.0 * self.reliability(other.name)   # told funds at half, scaled by the teller's record
        ok, n = self.trust.get(other.name, (0, 0))
        self.trust[other.name] = (ok, n + 1)
        if kind == "way":   # a way offered: the push is said to give the want (the asker cannot tell a lie)
            self.beats.append(Beat(self.world.t, "tell", other.name, hole=self.effect_hole(push).id, obj=push[1],
                                   detail={"to": self.name, "way": push, "truth": cond, "condition": None},
                                   prov="told", refs=(ab,)))
            self.receipt(self.effect_hole(push).id, "causes", self.want.subject, "told", weight)
            self.tellers[len(self.ledger) - 1] = other.name
            self.told_ways[push] = other.name
            return True
        self.beats.append(Beat(self.world.t, "tell", other.name, hole=self.effect_hole(push).id, obj=push[1],
                               detail={"to": self.name, "condition": cond, "inv": push}, prov="told", refs=(ab,)))
        self.receipt(self.effect_hole(push).id, "conditions", cond, "told", M0 * weight)
        self.tellers[len(self.ledger) - 1] = other.name
        return True

    def plan(self):
        """The want's way, or a push on the wanted object whose condition is held (told or learned): the push
        to make once its condition stands."""
        w = self.way()
        if w or not (self.want and self.want.closed is None):
            return w
        told = [p for p in self.told_ways if p in self.world.invitations()]
        if told:   # a way it was told and has not tested: act on it
            return told[0]
        obj = effect_parts(self.want.subject, self.world.objs)[0]
        held = [i for i in self.world.invitations() if i[1] == obj and self.learned(i)]
        return max(held, key=lambda i: AMOUNTS[i[0]]) if held else None

    def subgoal(self, cond):
        """A condition the mind can bring about itself (its object invites a push, and nothing else has been
        seen moving it): the push on that object known to give it, else the strongest one, least tried.
        Gerundelle's Inquiry: "conditions: change something first, then do it"."""
        obj = effect_parts(cond, self.world.objs)[0]
        row = self.terr.rows.get(obj, {})
        if row.get("other"):
            # something else moves it. A region never held is waited for (the wind's flag); one this mind
            # held and another undid is contested, and with ownership stakes it is fought for, not waited on
            contested = self.ownership and row.get("ever") and any(w for w, _ in self.moves_by.get(obj, ()))
            if not contested:
                return None
        invs = [i for i in self.world.invitations() if i[1] == obj]
        known = [i for i in invs if any(cond in x.effects for x in self.tried(i))]
        if known:
            return known[-1]
        return max(invs, key=lambda i: (AMOUNTS[i[0]], -len(self.tried(i)))) if invs else None

    def wait(self, cond):
        """The best push is parked (its condition is not met now): watch a slice. What changes meanwhile
        was moved by something else."""
        if self.waiting != cond:
            self.waiting = cond
            self.beat("wait", obj=effect_parts(cond, self.world.objs)[0], detail={"condition": cond})
        diffs = self.world.act(None)
        self.recent = {e.split(": ", 1)[0] for e in diffs}
        for e in diffs:
            obj, rest = e.split(": ", 1)
            if " -> " in rest:
                frm, to = rest.split(" (")[0].split(" -> ")
                self.beat("other", obj=obj, detail={"from": frm, "to": to})
                self.terr.moved({obj})

    def way(self):
        """The want's way slot: a push that has brought the wanted change (its latest such try), if any."""
        if not (self.want and self.want.closed is None):
            return None
        hits = [x for x in self.tries if self.want.subject in x.effects]
        return hits[-1].inv if hits else None

    def perceive(self):
        """What changed since this mind's last turn that it did not do: another mind's doing (seen: the mover
        is visible) or the world's. A region this mind held, undone, drains its resolve and contests it; a
        mover that keeps leaving a region in the same state is a purposeful other, and the blocked want's
        blame falls on it (Gerundelle's anger: a claim conditioned on a state a purposeful other keeps)."""
        now = self.facts()
        if self.last_facts is None:   # the first look: what the others did before (in their pasts) is not seen
            self.last_facts = now
            self.seen_tries = {o.name: len(o.tries) for o in self.others}
            self.seen_tries_before = dict(self.seen_tries)
            return
        changed = {effect_parts(f, self.world.objs)[0] for f in now - self.last_facts}
        movers = [o for o in self.others if len(o.tries) > self.seen_tries.get(o.name, 0)]   # acted since my last look
        self.seen_tries = {o.name: len(o.tries) for o in self.others}
        who = movers[0].name if movers else None
        for o in movers:   # their pushes, watched whole: seen receipts, and conditions learned from them
            for x in o.tries[self.seen_tries_before.get(o.name, 0):]:
                if x.inv[0] in ("light", "hard"):
                    self.observe(o, x)
        self.seen_tries_before = dict(self.seen_tries)
        # whoever's push brought the wanted change (of several who moved since: the one it came from)
        bringer = next((o for o in movers if self.want and o.tries and self.want.subject in o.tries[-1].effects), None)
        if bringer is not None:
            who = bringer.name
        helped = bringer is not None and getattr(bringer, "helps", False) and self.want.closed is None
        if helped:
            # the wanted change came by a helper's act: the want is met, not taken (gratitude)
            self.want.closed, self.done = self.world.t, not self.carry_on
            self.beat("reach", hole=self.want.id, obj=effect_parts(self.want.subject, self.world.objs)[0],
                      detail={"change": self.want.subject, "by": who})
            self.beat("feel", hole=f"other:{who}", obj=who, detail={"phase": "gratitude", "unexpected": []})
        elif bringer is not None and self.want.closed is None and not self.keep:
            # the wanted change came, by another's push (seen): the want is had, by someone else; the region
            # is lost to this mind (a phase: sadness, and anger at the one who took it)
            region = effect_parts(self.want.subject, self.world.objs)[0]
            self.want.closed, self.done = self.world.t, True
            self.beat("feel", hole=f"own:lost:{region}", obj=region, detail={"phase": "sadness", "unexpected": []})
            if self.phases and f"other:{who}" not in self.angry:
                self.angry.add(f"other:{who}")
                self.beat("feel", hole=f"other:{who}", obj=who, detail={"phase": "anger", "unexpected": []})
        for kept in sorted(self.guards):
            if kept in self.last_facts and kept not in now and not self.done and movers:
                # a state this mind keeps from changing, undone by another (seen, or found on coming back):
                # what it kept is lost to it, past restoring (a lost slot; sadness, and anger at the one who did
                # it: Gerundelle's anger at a purposeful other, here its last act). Read first: a loss ends the
                # keeping, so nothing it sees undone after it drains a reserve
                region = effect_parts(kept, self.world.objs)[0]
                by = next((o.name for o in movers if o.tries and any(
                    effect_parts(e, self.world.objs)[0] == region for e in o.tries[-1].effects)), movers[0].name)
                self.done = True
                if self.want:
                    self.want.closed = self.world.t
                self.beat("lost", hole=f"own:lost:{region}", obj=region, detail={"kept": kept, "by": by})
                if self.phases and f"other:{by}" not in self.angry:
                    self.angry.add(f"other:{by}")
                    self.beat("feel", hole=f"other:{by}", obj=by, detail={"phase": "anger", "unexpected": []})
        for obj in sorted(changed):
            state = next(f for f in now if effect_parts(f, self.world.objs)[0] == obj)
            self.terr.moved({obj})
            self.moves_by.setdefault(obj, []).append((who, state))
            row = self.terr.rows.get(obj, {})
            mine = row.get("ever") or (self.keep and self.want and obj == effect_parts(self.want.subject, self.world.objs)[0])
            if who and mine and self.resolve is not None and not self.done:
                slots = [(k, r) for k, r in self.terr.open_slots() if r == obj]
                pull = max([self.terr.pull(k, r) for k, r in slots] + [1.0])
                was = self.resolve
                self.resolve -= 1.0 / pull
                half = self.resolve0 / 2 if self.resolve0 else None
                if self.signs and half and self.resolve > 0 and was > half >= self.resolve:
                    # the reserve shows (rung 7, my choice: a readout of how near the threshold is, as grief is
                    # a readout of what was held): past half spent, the mind tires, and the tiring is seen
                    self.beat("feel", hole=f"own:control:{obj}", obj=obj, detail={"phase": "weariness", "unexpected": []})
                if self.resolve <= 0:   # the reserve is spent: the want is given up (a phase change)
                    self.beat("feel", hole=f"own:control:{obj}", obj=obj,
                              detail={"phase": "resignation", "unexpected": []})
                    if self.want:
                        self.want.closed = self.world.t
                    self.done = True
            same = [s for w, s in self.moves_by[obj] if w == who]
            if who and len(same) >= 2 and len(set(same)) == 1 and mine and self.phases and                     f"other:{who}" not in self.angry:
                self.angry.add(f"other:{who}")
                self.beat("feel", hole=f"other:{who}", obj=who, detail={"phase": "anger", "unexpected": []})
        if self.memory is not None:
            self.possessions(now, who)
        self.last_facts = now

    def possessions(self, now, who):
        """Things held, lost and found again, and the phases about them over time (memory.py)."""
        objs = self.world.objs
        before = {effect_parts(f, objs)[0] for f in self.last_facts}
        present = {effect_parts(f, objs)[0] for f in now}
        regions = {}   # new things in view invite pushes: their claims are perceived
        for inv in self.world.invitations():
            regions.setdefault(inv[1], set()).add(inv)
        self.terr.perceived(regions)
        for obj in sorted(before - present):   # gone, by another's act (seen): lost, if it was held
            row = self.terr.rows.get(obj, {})
            if row.get("ever") and self.terr.held(obj):
                row["holder"], row["taken_by"] = "lost", who
                pull = self.terr.pull("lost", obj)
                fb = self.beat("feel", hole=f"own:lost:{obj}", obj=obj, detail={"phase": "sadness", "unexpected": [],
                                                                              "pull": pull})
                self.phase_beats[self.memory.form("sadness", obj, None, self.world.t)] = fb
                if who and self.phases:
                    fb = self.beat("feel", hole=f"other:{who}", obj=who, detail={"phase": "anger", "unexpected": []})
                    self.phase_beats[self.memory.form("anger", obj, who, self.world.t)] = fb
        back = sorted(present - before)
        if back:   # something come back into view, and whoever brought it: warm boxes reopen (resonance)
            for pid in self.memory.resonate(back + ([who] if who else []), self.world.t):
                p = self.memory.active[pid]   # the same phase, so its beat cites the one it first formed in
                first = self.phase_beats.get(pid)
                self.phase_beats[pid] = self.beat(
                    "feel", hole=f"other:{p['person']}" if p["person"] else f"own:lost:{p['region']}",
                    obj=p["person"] or p["region"], detail={"phase": p["kind"], "unexpected": [], "reopened": True,
                                                            "region": p["region"]},
                    refs=(first,) if first is not None else ())
        for pid in self.memory.step(self.world.t, lambda p: p["region"] in present):   # expired, still open
            p = self.memory.stored[pid]
            if p["kind"] == "sadness":
                self.beat("feel", hole=f"own:lost:{p['region']}", obj=p["region"],
                          detail={"phase": "fading", "unexpected": [], "region": p["region"]})

    def observe(self, other, x):
        """Another's push, watched: what followed is a seen receipt on this mind's own hole for that push,
        and a contrast with this mind's own failures there can teach the condition (learned by watching)."""
        h = self.effect_hole(x.inv)
        self.observed.append(x)
        for n in x.effects:
            self.receipt(h.id, "causes", n, "seen", 1.0 / max(1, len(x.effects)))
        cond = self.condition(x.inv)
        if cond and not self.conditions(x.inv, provs=("lived", "worked", "seen")):
            self.receipt(h.id, "conditions", cond, "worked", M0)
            self.beat("learn", hole=h.id, obj=x.inv[1], detail={"condition": cond, "inv": x.inv, "confirms": None,
                                                                "exposes": None, "watched": other.name}, prov="worked")

    def end_scene(self):
        """The scene is over: each condition learned here is kept as an episode, by structure (the gerund the
        pushed object was in, the gerund its condition's object was in), to be found again by shape."""
        for h in self.holes.values():
            if h.kind != "effect":
                continue
            for cond, prov, _ in self.conditions(h.subject, provs=("lived", "worked")):
                if "&" in cond:   # an AND is not kept as an episode of one shape (recall maps single conditions)
                    continue
                cobj, cstate = effect_parts(cond, self.world.objs)
                before = next((f for x in self.tried(h.subject) for f in x.facts
                               if effect_parts(f, self.world.objs)[0] == cobj and f != cond), None)
                if before:
                    self.episodes.append(dict(push=h.subject, obj=h.subject[1], gerund=h.subject[2], cond_obj=cobj,
                                              cond_state=cstate, cond_gerund=effect_parts(before, self.world.objs)[1],
                                              stored=self.world.t, watched=next(
                                                  (b.detail.get("watched") for b in self.beats if b.kind == "learn"
                                                   and b.detail.get("condition") == cond), None)))

    def enter(self, world):
        """Into another scene: a new world, this mind's ledger, holes, territory and episodes kept."""
        self.world = world
        self.last_facts, self.recent, self.focus = None, set(), None
        self.terr.objs |= set(world.objs)
        regions = {}
        for inv in world.invitations():
            regions.setdefault(inv[1], set()).add(inv)
        self.terr.perceived(regions)
        self.beat("scene", detail={"world": world.name})
        self._open(world)

    def recall(self, inv):
        """Stuck on a push on the wanted object, nothing held about its conditions: is there an episode of the
        same shape (Case-2: a push on an object in the same gerund, whose condition was another object's
        change out of a gerund one of this scene's objects is in now), still warm? Its condition carries over
        to this scene's object in that gerund, as recalled (funded at half: a hypothesis to test)."""
        from memory import COLD, H_SITE
        for ep in reversed(self.episodes):
            if ep["gerund"] != inv[2] or ep["push"][0] != inv[0]:
                continue
            warmth = 0.5 ** ((self.world.t - ep["stored"]) / H_SITE)
            if warmth < COLD:
                continue
            target = next((d for d, g in self.world.states().items() if g == ep["cond_gerund"] and d != inv[1]), None)
            if target is None:
                continue
            h = self.effect_hole(inv)
            cond = f"{target}_{ep['cond_state']}"
            self.receipt(h.id, "conditions", cond, "recalled", M0)
            self.beat("recall", hole=h.id, obj=inv[1], detail={"condition": cond, "from_obj": ep["obj"],
                                                               "from_cond": ep["cond_obj"], "watched": ep["watched"],
                                                               "warmth": round(warmth, 2)}, prov="recalled")
            return True
        return False

    def pass_time(self, ticks):
        """Time passes with nothing done (a scene break): the world's clock moves on, stored keys cool, and
        what was still active and unrefreshed expires into storage."""
        self.world.t += ticks
        self.beat("time", detail={"ticks": ticks})
        if self.memory is not None:
            present = {effect_parts(f, self.world.objs)[0] for f in self.facts()}
            for pid in self.memory.step(self.world.t, lambda p: p["region"] in present):
                p = self.memory.stored[pid]
                if p["kind"] == "sadness":   # a grief, stored open: no longer thought of, not resolved
                    self.beat("feel", hole=f"own:lost:{p['region']}", obj=p["region"],
                              detail={"phase": "fading", "unexpected": [], "region": p["region"]})

    def tick(self, max_watch=12):
        """One turn: perceive what others did since this mind's last turn, act, and keep the facts as they
        stand at the end of the turn (the baseline the next perception is read against)."""
        self.perceive()
        try:
            return self.act()
        finally:
            self.last_facts = self.facts()

    def act(self, max_watch=12):
        if self.done:
            return
        if self.keep and self.want and self.want.subject in self.facts():   # the kept state holds: watch
            self.world.act(None)
            self.last_facts = self.facts()
            return
        # a want with a way known: act on it before inquiring (Gerundelle's SovAgent: plan_step comes
        # before experiments; first the value of learning alone chose, and a mind that had found how to
        # move the crate went on studying a push that never worked)
        inv = self.plan() or self.choose()
        if inv is None:
            self.world.act(None)
            return
        cond = self.learned(inv)
        if cond and self.unmet(cond):   # futile now: bring the condition about (its first unmet part), or wait for it
            cond = self.unmet(cond)
            sub = self.subgoal(cond)
            if sub is None:
                self.wait(cond)
                return
            inv = sub
        self.waiting = None
        h = self.effect_hole(inv)
        if self.focus != h.id:   # a hole wins attention: its open slot posed to oneself
            self.focus = h.id
            if not h.focused and self.tries and inv not in self.told_ways:   # the first push is just tried;
                # later ones are wondered about, unless the mind was told what this one does (no open question)
                self.beat("wonder", hole=h.id, obj=inv[1], detail={"slot": self.open_slots(h)[0], "inv": inv},
                          pull=self.pull(h))
            h.focused.append(self.world.t)
        facts = self.facts()
        before = self.predict(inv, facts)
        felt = self.terr.attend(inv[1], self.world.t) if self.ownership else None
        if felt and self.phases:
            self.beat("feel", hole=felt[1], obj=inv[1], detail={"phase": felt[0], "unexpected": []},
                      pull=self.terr.pull("unclaimed", inv[1]))
        tb = self.beat("try", hole=h.id, obj=inv[1], detail={"strength": inv[0], "gerund": inv[2]}, pull=self.pull(h))
        already = self.recent - {inv[1]}   # moving when the push began: finishing its own motion
        from worlds import carried
        held = carried(self.world, inv[1])   # what it carries as the push begins (it may fly off)
        effects, k, diffs, moving = [], 0, self.world.act(inv), {inv[1]}
        while k < max_watch:   # watch what the push set going: the horizon, and on while its chain still
            effects += [(e, k) for e in diffs]   # moves (first: while anything moved, and the wind's flag
            k += 1                               # lengthened every watch it overlapped, entraining the
            ours = [e for e in diffs if e.split(": ", 1)[0] in moving]   # pushes to the wind's period)
            if ours:
                moving |= {e.split(": ", 1)[0] for e in diffs}
            if not ours and k >= self.world.horizon:
                break
            diffs = self.world.act(None)
        self.recent = {e.split(": ", 1)[0] for e in diffs}
        names, chain = [], {inv[1]} | held   # what it holds or carries is in contact
        # within a slice the object pushed is read first (the simulator lists a slice's flips in no causal order)
        effects.sort(key=lambda ek: (ek[1], ek[0].split(": ", 1)[0] != inv[1]))
        for e, k in effects:   # a change is the push's if it is on the object pushed, or comes after a change
            obj, rest = e.split(": ", 1)   # of the push's (a chain); any other was something else's doing
            frm, to = rest.split(" (")[0].split(" -> ") if " -> " in rest else ("", rest.split(" (")[0])
            if obj in chain or (obj not in already and any(effect_parts(n, self.world.objs)[0] == inv[1] for n in names)):
                chain.add(obj)
                names.append(f"{obj}_{to}")
                self.beat("change", hole=h.id, obj=obj, detail={"from": frm, "to": to, "slice": k}, refs=(tb,))
            else:
                self.beat("other", obj=obj, detail={"from": frm, "to": to, "slice": k}, refs=(tb,))
                self.terr.moved({obj})
        self.tries.append(Try(self.world.t, inv, facts, tuple(names), self.facts()))
        lost_row = self.terr.rows.get(inv[1], {})
        regained = lost_row.get("holder") == "lost" and any(effect_parts(n, self.world.objs)[0] == inv[1] for n in names)
        self.terr.claimed(inv, inv[1], names, predicted=before)
        if regained and self.memory is not None:   # a lost thing held again: its phases close
            lost_row["holder"], lost_row["taken_by"] = "mine", None
            for pid, active, p in self.memory.close(inv[1], self.world.t):
                if p["kind"] == "anger" and active:   # a grudge closing by its goal met: forgiveness
                    grudge = self.phase_beats.get(pid)
                    self.beat("feel", hole=f"other:{p['person']}", obj=p["person"],
                              detail={"phase": "forgiveness", "unexpected": []},
                              refs=(tb,) + ((grudge,) if grudge is not None else ()))
            pass   # the joy of holding it again is the ownership graph's (a lost instance closed by a claim)
        prior = [x for x in self.tried(inv)[:-1] if x.effects == tuple(names) and x.facts != facts]
        if names and prior and self.condition(inv) is None:   # the same change under other facts: it does not
            self.receipt(h.id, "conditions", "regardless", "worked", 0.5)   # depend on what differed (half:
            # one coincidence must not close it; held open while the outcomes are volatile)
        if not names:
            self.beat("nothing", hole=h.id, obj=inv[1], detail={"strength": inv[0]}, refs=(tb,))
            self.receipt(h.id, "causes", "no_change", "lived")
            wanted_obj = self.want and effect_parts(self.want.subject, self.world.objs)[0]
            running = 0   # tries running on the wanted object that failed (Gerundelle's row fails)
            for x in reversed(self.tries):
                if x.inv[1] != wanted_obj:
                    continue
                if x.effects:
                    break
                running += 1
            if (self.patience is not None and self.want and self.want.closed is None and inv[1] == wanted_obj
                    and running >= self.patience):
                # temperament: the want's parking threshold reached, it is given up (resignation)
                self.beat("feel", hole=f"own:control:{wanted_obj}", obj=wanted_obj,
                          detail={"phase": "resignation", "unexpected": []}, refs=(tb,))
                self.want.closed, self.done = self.world.t, True
            elif self.want and self.want.closed is None and inv[1] == wanted_obj and not self.learned(inv):
                if not self.recall(inv):
                    self.consult(inv)
        for n in names:
            self.receipt(h.id, "causes", n, "lived", 1.0 / len(names))
        if inv in self.told_ways and not (self.want and self.want.subject in names):
            # a told way the world contradicts: the told receipt retracted, the teller's record marked, and
            # anger anchored on the teller (Gerundelle's Phases: blame for a blocked want, grounded: the
            # teller's word is what failed)
            teller = self.told_ways.pop(inv)
            self.receipt(h.id, "causes", f"retract:told:{teller}", "lived", 0.0)
            self.lied_to = teller
            self.beat("surprise", hole=h.id, obj=inv[1], detail={"expected": [self.want.subject], "got": names,
                                                                 "belief": False, "told": teller}, refs=(tb,))
            if self.phases:
                self.beat("feel", hole=f"other:{teller}", obj=teller, detail={"phase": "anger", "unexpected": []},
                          refs=(tb,))
            before = None
        if before is not None and frozenset(names) != before:   # the world's testimony against a prediction
            believed = inv in self.beliefs and before == self.beliefs[inv]
            self.beat("surprise", hole=h.id, obj=inv[1], detail={"expected": sorted(before), "got": names,
                                                                 "belief": believed}, refs=(tb,))
            if believed:   # the belief is retracted (Retract, licensed by the world's testimony; logged)
                self.receipt(h.id, "causes", f"retract:{sorted(before)}", "lived", 0.0)
                del self.beliefs[inv]
                if self.retract_phase and self.phases:
                    self.beat("feel", hole=h.id, obj=inv[1], detail={"phase": "sadness", "unexpected": []},
                              refs=(tb,))
        by_facts = {}
        for x in self.tried(inv):
            by_facts.setdefault(x.facts, []).append(x.effects)
        settled = [v for v in by_facts.values() if len(v) >= 2]
        explained = (len(settled) >= 2 and all(len(set(v)) == 1 for v in settled)
                     and len({v[0] for v in settled}) > 1)
        if explained and not any(self.ledger[i].value == "by_state" for i in h.receipts):
            # every situation tried twice gave one outcome, and the situations differ in it: what it does is
            # a function of the state it is pushed in (a flag pushed hanging swings; swinging, settles). The
            # same outcome everywhere is no answer: for a push that never worked, "what blocks it?" is open
            self.receipt(h.id, "conditions", "by_state", "worked", M0)
        cond = self.condition(inv)
        if cond and not self.conditions(inv, provs=("lived", "worked")):   # worked out from its own tries
            told = [c for c in self.conditions(inv, provs=("told",)) if c[0] == cond]
            self.receipt(h.id, "conditions", cond, "worked", M0)
            first = next((i for i, b in enumerate(self.beats) if b.kind == "nothing" and b.hole == h.id
                          and b.actor == self.name), tb)
            tellb = tuple(i for i, b in enumerate(self.beats) if b.kind == "tell" and (
                b.detail.get("condition") == cond or b.detail.get("truth") == cond))   # confirmed, or exposed
            liar = getattr(self, "lied_to", None)
            if told:
                ok, n = self.trust.get(told[0][2], (0, 0))
                self.trust[told[0][2]] = (ok + 1, n)
            self.beat("learn", hole=h.id, obj=inv[1], detail={"condition": cond.split("&")[0], "also": cond.split("&")[1:],
                                                              "inv": inv,
                                                              "confirms": told[0][2] if told else None,
                                                              "exposes": liar},
                      prov="worked", refs=(first, tb) + tellb)
        unexpected = []
        if self.want and self.want.closed is None and self.want.subject in names:
            self.got += 1
        if self.want and self.want.closed is None and self.want.subject in names and self.got < self.want_count:
            if inv not in self.beliefs and not self.learned(inv):   # credit the push: a belief, worked out
                self.beliefs[inv] = frozenset(names)
                self.receipt(h.id, "causes", self.want.subject, "worked")
                self.beat("believe", hole=h.id, obj=inv[1], detail={"cause": inv, "effect": self.want.subject},
                          prov="worked", refs=(tb,))
        elif self.want and self.want.closed is None and self.want.subject in names and self.keep:
            self.receipt(self.want.id, "way", h.id, "lived", M0)   # the kept state restored: the want stays open
        elif self.want and self.want.closed is None and self.want.subject in names:
            self.receipt(self.want.id, "way", h.id, "lived", M0)
            self.want.closed = self.world.t
            region = effect_parts(self.want.subject, self.world.objs)[0]
            self.terr.reached(region, self.want.subject)
            self.beat("reach", hole=self.want.id, obj=inv[1], detail={"change": self.want.subject, "inv": inv},
                      refs=(tb,))
            seen = {n for x in self.tries[:-1] for n in x.effects}
            region = effect_parts(self.want.subject, self.world.objs)[0]   # what was wanted is no surprise
            unexpected = [n for n in names if effect_parts(n, self.world.objs)[0] != region and n not in seen]
            self.done = not self.carry_on
        if self.ownership:
            self.terr.update()
            for kind, inst in self.terr.read_phases(self.world.t):
                if self.memory is not None and inst.startswith("own:lost:") and kind == "sadness":
                    continue   # the loss's sadness is the memory's (formed with its pull when the thing went)
                if self.phases:
                    self.beat("feel", hole=inst, obj=inst.split(":")[-1],
                              detail={"phase": kind, "unexpected": unexpected if kind == "joy" else []},
                              pull=self.terr.pull(*inst.split(":")[1:]) if inst.startswith("own:") and
                              tuple(inst.split(":")[1:]) in self.terr.open_slots() else 0.0, refs=(tb,))
        elif self.done:   # the first cut: feelings by rule
            self.beat("feel", hole=self.want.id, detail={"phase": "joy", "unexpected": unexpected}, refs=(tb,))
        elif self.want and len([x for x in self.tries if not x.effects]) == 3 and not any(b.kind == "feel" for b in self.beats):
            self.beat("feel", hole=self.want.id, detail={"phase": "frustration"}, pull=self.pull(self.want))
