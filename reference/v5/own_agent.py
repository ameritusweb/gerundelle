"""The thought-world agent rebuilt on territory (REORG.md step 4; DRIFT.md, the thought-world inventory).

The earlier agent (`Agent`, molecules.py) planned over the world's scalar rewards: +1 for an answered
call, groceries or a greeting, -0.5 for getting wet, and so on. The voices only added a prior. This
agent never reads the world's reward. The world reports what happened (`seen`, the percepts); what
that is worth is what it does to the agent's territory (DRIFT.md rule 10), read with the decided
readings of TERRITORIAL_MAPPINGS.md sec. 2:

- groceries and the umbrella are unclaimed until held ("groceries 'become' yours");
- she is a mind: until she answers, the agent isn't on her mind (appreciation, open);
- the friend is a mind: until greeted, a relation open;
- the body is given territory; rain that wets it is an incursion (contested). Keeping dry while
  going out in the rain is the claim taking ("using the umbrella is a demonstration of territorial
  ownership");
- a call or a voice is a moment: a relational uniqueness instance while it lasts; missed, it goes
  to storage open and reopens when the moment comes again;
- a claim that can't take now (the closed store) leaves the slot parked: nothing could fill it
  now (the active recognitions say every claim on it is worse here).

Worth of an outcome = the pull of the instances it closes, less the pull of the instances an
incursion or a missed moment opens. That number is the register's, not the designer's: it is the
tension the outcome releases. It stands everywhere the earlier agent read the reward:
MCTS's value (through the person's own model, which does not know the world's rules), the
prediction error behind recognitions (blame), and the good or bad outcome the mind learns from.
What wins attention guides the search: actions on the region of a top ownership instance get the
prior (the user: "action is MCTS guided by the top-level winners").

The maps below are perception the world supplies (who a happening or an action is about), as the
force world names each change's object.
"""
from molecules import EVENTS, VOICES, Agent, BigWorld, mcts

ACTS_ON = {"call": "her", "pick_up": "her", "shop": "groceries", "greet": "friend", "answer_voice": "friend",
           "take_umbrella": "umbrella", "go_store": "body", "go_park": "body", "go_home": "body"}
MINDS = {"her": "appreciation", "friend": "relation"}   # the slot another mind holds open for the agent
HOLDS = {"she_answered": "her", "greeted_friend": "friend", "i_have_groceries": "groceries"}
INCURSIONS = {"i_got_wet": "body", "i_got_soaked": "body"}
MOMENTS = {"the_phone_rings": ("her", "pick_up"), "someone_calls_my_name": ("friend", "answer_voice")}
POSSESSIONS = ("groceries", "umbrella")
SERVES = {"umbrella": "body"}   # a possession that serves another region: open only while that region needs it
GAMMA = 0.7   # imagination's discount, the force world's (ForceWorld.gamma): a claim nearer counts more
EVENTS_NO_VOICES = {k: v for k, v in EVENTS.items() if k not in VOICES}


def view(actions, held, contested, moments, needed=frozenset(), carry=None):
    """The open instances, {(kind, region): pull}, from what is perceived and held now. A possession
    that serves another region (the umbrella, the body) is open only while that region needs it: the
    `serves` wire (first the umbrella was open in any weather, and taken every episode)."""
    regions = {ACTS_ON[a] for a in actions if a in ACTS_ON}
    out = {}
    for r, kind in MINDS.items():
        if r in regions and r not in held:
            out[(kind, r)] = 1.0
    for r in POSSESSIONS:
        if r in regions and r not in held and (r not in SERVES or SERVES[r] in needed):
            out[("unclaimed", r)] = 1.0
    if "body" in contested:
        out[("contested", "body")] = 1.0
    for r in moments:   # a moment missed before pulls by its misses too: regret (the user, 2026-10-24: "a
        # stored instance whose held-count includes the original miss"), as lost pulls by what was held
        out[("uniqueness", r)] = 1.0 + (carry or {}).get(r, 0)
    return out


def worth(before, after, held_after, answered=0.0, missed=0.0):
    """The tension an outcome releases: the pull of what its claims closed, less what an incursion or a
    missed moment opened. An instance closes only by its claim taking (its region held after; first
    any instance gone from view counted, and walking away from the park read as greeting the friend);
    a moment closes by being answered. answered and missed are the moments' pulls."""
    closed = sum(p for (k, r), p in before.items()
                 if (k, r) not in after and k not in ("uniqueness", "contested") and r in held_after)
    opened = sum(p for k, p in after.items() if k not in before and k[0] == "contested")
    return closed + answered - opened - missed


def instance_worth(inst, before, after, held_after, answered=(), missed=()):
    """What an outcome did to one instance (step 5: credit to the slot, not the action): its pull if
    its claim took (or its moment was answered), less its pull if it was missed or an incursion opened
    it; 0 if it was untouched."""
    k, r = inst
    if k == "uniqueness":
        p = before.get(inst, 0.0)
        return p if r in answered else -p if r in missed else 0.0
    if inst in before and inst not in after and r in held_after:
        return before[inst]
    if inst not in before and inst in after and k == "contested":
        return -after[inst]
    return 0.0


def pulling(a, here):
    """The instance pulling hardest on the region an action acts on (None if none is open there)."""
    r = ACTS_ON.get(a)
    on = [(p, k) for (k, rr), p in here.items() if rr == r]
    return (max(on)[1], r) if on else None


def state_view(world, s, needed=frozenset(), carry=None):
    """The person's own reading of a (simulated) state: its open instances and what it holds."""
    t, place, umbrella, called, shopped, greeted, events = s
    held = {r for r, h in (("her", called), ("groceries", shopped), ("friend", greeted), ("umbrella", umbrella)) if h}
    moments = {MOMENTS[n][0] for n, _ in events if n in MOMENTS}
    return view(world.actions(s), held, set(), moments, needed, carry), held


class TerritoryModel:
    """The person's own model (their rules, which lack the world's), valued by territory: a step's
    value is the worth of the outcome it imagines, plus the recognitions' corrections."""

    def __init__(self, own, corrections, needed=frozenset(), carry=None):
        self.own, self.corrections = own, corrections   # own: a PersonModel (its .rules a BigWorld)
        self.needed = needed                            # regions that need serving now (the body in rain)
        self.carry = carry or {}                        # moments reopened from storage: region -> misses

    def actions(self, s):
        return self.own.actions(s)

    def imagine_views(self, s, a):
        """What the person imagines a push does to its territory (step 5: territory in the prediction):
        the next state, the open instances before and after, what it would hold, the moments it would
        answer and miss."""
        w = self.own.rules
        s2, _, seen = w.step(s, a)
        (before, _), (after, held) = state_view(w, s, self.needed, self.carry), state_view(w, s2, self.needed, self.carry)
        ended = {MOMENTS[n][0] for n, _ in s[6] if n in MOMENTS} - {MOMENTS[n][0] for n, _ in s2[6] if n in MOMENTS}
        answered = {r for r in ended if MOMENTS_BY[r] == a}
        return s2, seen, before, after, held, answered, ended - answered

    def imagine(self, s, a):
        s2, seen, before, after, held, answered, missed = self.imagine_views(s, a)
        pull = lambda rs: sum(before.get(("uniqueness", r), 1.0) for r in rs)
        return s2, worth(before, after, held, answered=pull(answered), missed=pull(missed)), seen

    def expected(self, s, a):
        return self.imagine(s, a)[1]

    def step(self, s, a):
        s2, r, seen = self.imagine(s, a)
        if r != 0.0 or a in self.corrections:
            r += self.corrections.get(a, 0.0)
        return s2, r, seen


class OwnAgent(Agent):
    """The thought-world agent on territory. Same perception, tournament, recognitions and MCTS as
    `Agent`; the world's reward is never read."""

    def __init__(self, mind, world, **kw):
        kw.setdefault("explore", 0.0)   # no curiosity bonus: novelty is the unclaimed slot's (DRIFT.md)
        super().__init__(mind, world, links={}, **kw)
        self.clause_for.update(ACTS_ON)   # each claim's clause: the region it acts on
        self.memory.clause_for = self.clause_for
        self.stored = {}                  # moments missed: storage open (region -> misses), reopened by their anchor
        self.carry = {}                   # moments reopened from storage, while they last: region -> misses
        self.elig = {}                    # moment region -> [(key, present)]: actions taken while it pulled

    def active(self, inputs):
        seen = set(inputs)
        return {rid for rid, (a, m) in self.recog.items() if m in seen}

    def needs(self, situation, contested):
        """Regions that need serving now: the body when contested, or when rain is perceived and the
        agent has learned that rain reaches it (a recognition on going out: rain, getting wet, or the
        umbrella)."""
        learned = any(a.startswith("go_") and m in ("it_is_raining", "i_got_wet", "i_have_umbrella")
                      for a, m in self.recog.values())
        return frozenset({"body"}) if "body" in contested or ("it_is_raining" in situation and learned) else frozenset()

    def key(self, a, here):
        """The memory record a push is credited to: the push and the instance pulling on its region
        (step 5: contrastive blame against (slot instance, action) pairs)."""
        inst = pulling(a, here)
        if inst is None:
            return a
        k = f"{a}@{inst[0]}:{inst[1]}"
        self.clause_for.setdefault(k, ACTS_ON.get(a))
        return k

    def parked(self, inst, actions, active, here=None):
        """Nothing could fill it now: every claim on its region here has an active recognition that
        makes it worse (the closed store: shop is worse when the store is closed)."""
        r = inst[1]
        claims = [a for a in actions if ACTS_ON.get(a) == r]
        if not claims:
            return False
        keyof = (lambda a: self.key(a, here)) if here is not None else (lambda a: a)
        bad = lambda a: any(self.recog[rid][0] == keyof(a) and self.memory.error(keyof(a), self.recog[rid][1]) < 0
                            for rid in active)
        return all(bad(a) for a in claims)

    def explain(self, model, s, a, depth=3):
        """The instance the chosen action is for: the first one its imagined path closes (following
        the model's best push after the first). None if the path closes nothing."""
        w = model.own.rules
        for k in range(depth):
            s2, _, _ = model.imagine(s, a)
            (v1, _), (v2, held2) = state_view(w, s, model.needed, model.carry), state_view(w, s2, model.needed, model.carry)
            closed = {k for k in set(v1) - set(v2) if k[1] in held2}
            if closed:
                return sorted(closed)[0]
            s = s2
            if not model.actions(s):
                break
            a = mcts(model, s, {}, budget=20, horizon=depth - k - 1 or 1, gamma=GAMMA)
        return None

    def episode(self, length, start=(), state=None, force=None):
        """state: a start state (a scripted scene, for tests); force: tick -> action (a scripted
        intervention, as the force world's tests push)."""
        mind, world = self.mind, self.world
        mind.pool, mind.prev, mind.pending, mind.facts = {}, set(), [], {}
        s = world.start() if state is None else state
        force = force or {}
        inputs = list(start)
        held, contested, log = set(), set(), []
        for tick in range(length):
            percepts = world.percepts(s)
            situation = frozenset(percepts)
            news = self.read_facts(sorted(situation))
            everything = inputs + sorted(situation)
            inputs += news
            gen, mind.pending = mind.pending, []
            mind.perceive(inputs + [m.id for m in gen])
            mind.contradict(everything)
            events = getattr(world, "events", {})
            for i in inputs:
                if i in events:
                    mind.experience(self.clause(i), events[i]["needs"])
                else:
                    mind.present(self.clause(i))
            for m in gen:
                mind.present(m)
            for rid, (_, m) in self.recog.items():
                if m in inputs:
                    mind.present(self.recognition(rid))
            actions = world.actions(s)
            moments = {MOMENTS[n][0] for n, _ in s[6] if n in MOMENTS}
            reopened = sorted(r for r in moments if r in self.stored)
            for r in reopened:
                self.carry[r] = self.stored.pop(r)
            needed = self.needs(situation, contested)
            here = view(actions, held | ({"umbrella"} if "i_have_umbrella" in situation else set()), contested, moments,
                        needed, self.carry)
            active = self.active(everything)
            parked = sorted(k for k in here if self.parked(k, actions, active, here))
            mind.territory.provided = {k: p for k, p in here.items() if k not in parked}
            rec = mind.think()
            facts_held = {m.id for m in mind.facts.values()}
            for i in mind.top(rec):
                if i in facts_held:
                    mind.remove(i)
            top_regions = {i.split(":")[-1] for i in rec["levels"][-1]["winners"] if i.startswith("own:")}
            prior = {a: 1.0 + self.guide for a in actions if ACTS_ON.get(a) in top_regions}
            keys = {a: self.key(a, here) for a in actions}
            by_key = self.confidence(self.memory.corrections(list(keys.values()), situation, active), active, situation)
            corrections = {a: by_key.get(keys[a], 0.0) for a in actions}
            model = TerritoryModel(world.own(s, corrections), corrections, needed, dict(self.carry))
            prefer = world.responses(s)
            a = force.get(tick) or mcts(model, s, prior, budget=self.budget, prefer=prefer, gamma=GAMMA)
            expected = model.expected(s, a)
            inst = pulling(a, here)
            if inst is not None:   # what imagination expected for the instance it was chosen under
                _, _, ib, ia, ih, ians, imis = model.imagine_views(s, a)
                expected_inst = instance_worth(inst, ib, ia, ih, ians, imis)
            key = keys.get(a) or self.key(a, here)
            why = self.explain(model, s, a)
            self.tries[(a, situation)] = self.tries.get((a, situation), 0) + 1
            raining = "it_is_raining" in situation
            s2, _, seen = world.step(s, a)   # the world's reward is not read
            # what happened, read as territory
            after_held = set(held) | {HOLDS[x] for x in seen if x in HOLDS}
            if "i_have_umbrella" in world.percepts(s2):   # what it perceives next, not the world's state
                after_held.add("umbrella")
            hit = {INCURSIONS[x] for x in seen if x in INCURSIONS}
            after_contested = set(contested) | hit
            defended = a.startswith("go_") and raining and not hit and "body" in contested
            if defended:   # out in the rain and dry: the boundary held, the claim took
                after_contested.discard("body")
            next_moments = {MOMENTS[n][0] for n, _ in s2[6] if n in MOMENTS}
            answered = {r for r in moments if MOMENTS_BY[r] == a}
            missed = moments - next_moments - answered
            pull = lambda rs: sum(here[("uniqueness", r)] for r in rs)
            answered_pull, missed_pull = pull(answered), pull(missed)
            for r in missed:   # missed again: stored with one more miss
                self.stored[r] = self.carry.pop(r, 0) + 1
            for r in answered:
                self.carry.pop(r, None)
            before = here
            after = view(world.actions(s2), after_held, after_contested, next_moments,
                         needed | self.needs(frozenset(world.percepts(s2)), after_contested), self.carry)
            w = worth(before, after, after_held | ({"body"} if defended else set()),
                      answered=answered_pull, missed=missed_pull)
            present = self.blamed(rec, everything)
            # keeping dry in the rain closes the contested body (the boundary held) and is credited
            # nowhere else: the umbrella's worth is its own instance closing while the body needs it
            # (the serves wire). First credited to the walk (going out learned as good in any
            # weather), then to the umbrella's record (taken on dry sunny days: its base rate rose)
            if inst is not None:   # credited to the instance it was chosen under (step 5)
                w_inst = instance_worth(inst, before, after, after_held | ({"body"} if defended else set()),
                                        answered, missed)
                formed = self.notice(key, present, w_inst - expected_inst)
            else:                  # nothing pulling on its region: the whole outcome is its own
                w_inst = w
                formed = self.notice(key, present, w - expected)
            credited = [(key, round(w_inst, 3))]
            if inst is not None and inst[0] == "uniqueness" and inst[1] not in answered:
                self.elig.setdefault(inst[1], []).append((key, present))
            for r in missed:   # a moment lost: its loss goes to the pushes made while it pulled
                for k2, pres in self.elig.pop(r, []):
                    formed += self.notice(k2, pres, -here[("uniqueness", r)])
                    credited.append((k2, -here[("uniqueness", r)]))
            for r in answered:
                self.elig.pop(r, None)
            outcome = (w > 0) - (w < 0)
            mind.learn(rec, outcome)
            log.append(dict(rec=rec, action=a, key=key, credited=credited, worth=round(w, 3), expected=round(expected, 3), why=why,
                            seen=seen, top=mind.top(rec), open=sorted(here), parked=parked,
                            missed=sorted(missed), reopened=reopened, defended=defended,
                            formed=formed, state=s2, entered=list(inputs)))
            held, contested, s = after_held, after_contested, s2
            inputs = list(seen)
        return log


MOMENTS_BY = {r: a for r, a in MOMENTS.values()}


def world(seed=0):
    """BigWorld with its events (a storm, a voice calling my name, the phone) and no voice goals."""
    return BigWorld(["rain"] * 8, events=dict(EVENTS_NO_VOICES), seed=seed)
