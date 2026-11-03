"""The force-world agent rebuilt on the architecture (DRIFT.md, the repair; the user, 2026-10-23).

The world interface is thin: perceive (each object's state as a fact, the last slice's changes as
news, each potential force as a molecule), act (a push), and watch what follows a push. Everything
else is the mind's:
- **Holes and inquiry.** A potential force that matters (the user: a configuration that invites a
  force, and the question of what applying it does) is a concept. In play with open slots, it is
  cued as an SOV molecule (the understanding register's own rule). At the top, the SOV poses its most
  answerable question. The question suggests experiments by its slot; they are molecules competing in
  their own track (Inquiry), and the one that wins the top is what the agent does.
- **What a push did.** The push causes what changed in its watch, written as seen (intervened)
  relations. The outcome as a whole is a mode, recorded with the meta layer (`observe_mode`).
- **Conflation.** Two modes both likely is conflation (the meta layer's own `conflated`). When it
  wins the top, the push is split on the boundary (differentiate); the split writes the condition
  into the register, and the push is then read as the half the situation selects.
- **Prediction.** The commonest mode of the push's reading in that situation: the meta register's
  own record, nothing kept by the agent.

`ForceAgent` (force_world.py) is the earlier agent, kept as a baseline; DRIFT.md lists what it did
outside the mind and where each piece went.
"""
from force_world import AGENT, AMOUNTS, effect_id, inv_id
from molecules import Mind, Params, clause, mcts


class SovAgent:
    def __init__(self, world, mind=None):
        self.world = world
        self.mind = mind or Mind(Params(inquiry=True, phases=True))   # phases read off the ownership graph
                                                                      # (REORG.md step 7; the user, 2026-10-25)
        if self.mind.inquiry is None:   # a mind carried in without inquiry gets it
            from molecules import Inquiry
            self.mind.p.inquiry = True
            self.mind.inquiry = Inquiry(self.mind)
        und = self.mind.understanding
        und.kind = lambda c: "act" if c.split(":", 1)[0].endswith("_push") else "change"
        und.inert |= {"no_change", AGENT}
        self.watching = None   # (invitation, experiment, facts at the push, slices watched, effects)
        self.queue = []        # the rest of an experiment's steps
        self.running = None    # the experiment whose steps are under way
        self.intent = None     # an experiment that won the top while a push was being watched
        self.tried = []        # (tick, invitation, effects): a log for readouts
        self.pushed = []       # (invitation, facts at the push, effects): what each push met and did
        self.reached = []      # (tick, goal): wants had
        self.gave_up = []      # (tick, goal): wants given up (Params.patience)
        self.left = {}         # action concept -> the facts its last push left that were not there before
        self.seen_objs = set() # objects ever perceived (a held one no longer there is gone)
        self.recalled = []     # (tick, episode): conditions carried over from the past by shape
        self.known = {}        # action concept -> invitation, every potential force perceived
        self.goal = None       # a want: a change the agent wants (a goal-tagged clause in the pool)
        self.history = []      # per tick: (facts, what arrived): perception's log, for readouts
        self.last_rec = None
        self.watched_objs = set()   # objects changed while a push is watched (for the territory register)

    # ---- perception ---------------------------------------------------------------------------------

    def facts_now(self, tree=None):
        return frozenset(f"{d}_{g.replace(' ', '_')}" for d, g in self.world.states(tree).items())

    def perceive(self):
        """The facts register, the news (what changed in the last slice), and the potential forces."""
        mind, world = self.mind, self.world
        mind.facts = {d: clause(f"{d}_{g.replace(' ', '_')}") for d, g in world.states().items()}
        mind.territory.facts = self.facts_now()
        news = [clause(effect_id(e)) for e in world.diffs]
        for e in world.diffs:   # who a change is about (for analogy's owners)
            mind.understanding.owners[effect_id(e)] = e.split(": ", 1)[0]
        invs = {inv_id(i): i for i in world.invitations()}
        und = mind.understanding
        for c, inv in invs.items():   # the agent is what would apply a potential force (its caused_by,
            und.owners[c] = inv[1]     # seen as offered). Whether it matters is what an ownership slot
                                       # serves (REORG.md step 3; first every invitation mattered)
            if und.funding(c, "caused_by") < 1.0:
                und.add(c, "caused_by", AGENT, "seen", 1.0)
        mind.inquiry.actions = set(invs)
        mind.inquiry.leaves = self.left   # what each push was seen to leave (the agent's own record)
        mind.inquiry.still = getattr(world, "still", False)   # a world that moves only when the agent acts
        regions = {}   # the territory register: each object perceived with the pushes on it
        for c, inv in invs.items():
            regions.setdefault(inv[1], set()).add(c)
        mind.territory.perceived(regions)
        present = set(world.states())
        flipped = []
        for r, row in mind.territory.rows.items():   # what is no longer there is gone (and back when it is)
            if row.get("ever"):
                gone = r not in present and r in self.seen_objs
                if gone != bool(row.get("gone")):
                    row["gone"] = gone
                    flipped.append(r)
        self.seen_objs |= present
        if flipped:   # only the rows whose presence changed are read again
            mind.territory.update(flipped)
        self.known.update(invs)
        self.history.append((self.facts_now(), frozenset(effect_id(e) for e in world.diffs)))
        wants = [clause(self.goal, tags=("goal",))] if self.goal else []   # a want, held in the pool
        return news + wants + [clause(c, tags=("invitation", inv[1])) for c, inv in invs.items()], invs

    # ---- a tick ------------------------------------------------------------------------------------

    def tick(self, force=None):
        """force: an invitation to push now (a scripted intervention, for tests)."""
        world = self.world
        if not self.watching and not self.queue:   # a scene is not set back in the middle of an
            world.renew()                           # experiment (first: between its two steps, and the
                                                    # latch was reseated before the lid was pushed)
        und = self.mind.understanding   # a wanted change opens a control slot on its region, open until
        terr = self.mind.territory      # the change comes (REORG.md step 4; first the want was only a
        if self.goal is not None and self.mind.p.patience is not None:   # temperament: claims running on the
            r = und.owners.get(self.goal) or self.goal.rsplit("_", 1)[0]  # wanted region that failed, as many
            if terr.rows.get(r, {}).get("fails", 0) >= self.mind.p.patience:   # as the mind's patience: the
                self.gave_up.append((self.mind.t, self.goal))                  # want is parked, given up
                terr.given_up.add(r)
                terr.gave_up_now.add(r)
                self.goal = None
        if self.goal is not None:       # goal-tagged clause and the plan, and the ownership slots
            r = und.owners.get(self.goal) or self.goal.rsplit("_", 1)[0]   # worked for something else)
            terr.wants = {r: self.goal}
            terr.row(r)
        else:
            terr.wants = {}
        inputs, invs = self.perceive()
        rec = self.mind.tick(inputs)
        self.last_rec = rec
        if self.watching:
            world.act(None, hold=True)
            self.watch(world.diffs, rec)
            if rec["experiments"]:   # an experiment that wins meanwhile is held as the intention
                self.intent = rec["experiments"][0]
            return None, rec
        if not rec["experiments"] and self.intent in self.mind.inquiry.plans:
            rec["experiments"] = [self.intent]   # what won while watching, done now
        self.intent = None
        choice = None
        if force is not None:
            choice = force
        elif self.goal is not None and (step := self.plan_step(invs)) is not None:
            choice = step   # a want with a way known: act on it (MCTS over the agent's own model)
        elif self.queue:   # the next step of the experiment under way
            c = self.queue.pop(0)
            if c == "wait":   # a step of waiting (an experiment at another moment)
                self.idle(hold=True)
                return None, rec
            choice = invs.get(c)
            if choice is None:
                self.queue = []   # the step is no longer invited: the experiment is abandoned
            elif getattr(world, "still", False) and not self.queue and self.running and any(
                    i == choice and f == self.facts_now() for i, f, _ in self.pushed):
                # in a still world an action in a situation it was already tried in comes out as it did: the step
                # is known, not done, and the experiment reports as usual (its preparation ruled out). First every
                # conditions experiment ran its action after its preparation, and in a code world the spec was run
                # after nearly every fill, in situations already tried (the cognitive code ladder, Gerundelle arm)
                self.mind.inquiry.result(self.running, True)
                self.running, choice = None, None
        elif rec["experiments"]:
            eid = rec["experiments"][0]
            steps = list(self.mind.inquiry.plans[eid][2])
            self.mind.inquiry.did(eid)
            if steps and steps[0] == "wait":   # it starts by waiting
                self.queue, self.running = steps[1:], eid
                self.idle(hold=True)
                return None, rec
            if steps:
                choice = invs.get(steps[0])
                self.queue = steps[1:] if choice is not None else []
                self.running = eid if choice is not None else None
        if choice is None:
            self.idle()   # waiting is watching too
            return None, rec
        self.watching = (choice, self.facts_now(), 0, {})
        self.watched_objs = set()
        self.watch(world.act(choice, hold=bool(self.running) and force is None), rec)
        return choice, rec

    def idle(self, hold=False):
        """A slice with no push of the agent's in flight: what changed, something else moved (the
        territory register)."""
        diffs = self.world.act(None, hold=hold)
        self.mind.territory.moved({e.split(": ", 1)[0] for e in diffs}, [effect_id(e) for e in diffs], self.facts_now())
        return diffs

    def watch(self, diffs, rec):
        inv, facts, k, effects = self.watching
        for e in diffs:
            effects.setdefault(effect_id(e), k)
            self.watched_objs.add(e.split(": ", 1)[0])
        k += 1
        if k < self.world.horizon:
            self.watching = (inv, facts, k, effects)
            return
        self.watching = None
        mind, und = self.mind, self.mind.understanding
        c = inv_id(inv)
        names = sorted(effects) or ["no_change"]
        for e in effects:   # what followed the push: seen (the agent intervened)
            und.add(c, "causes", e, "seen", self.world.gamma ** effects[e])
            und.add(e, "caused_by", c, "seen", self.world.gamma ** effects[e])
            if effects[e] == 0:   # and what came with it, in its own slice: seen co-occurring
                und.add(c, "co_occurs", e, "seen", 1.0)
        if not effects:   # "it does nothing here" answers what it does (no_change is not a concept)
            und.add(c, "causes", "no_change", "seen", 1.0)
        und.add(c, "caused_by", AGENT, "seen", 1.0)   # an action is caused by the one who acts
        before = self.predict(inv, facts)   # its usual outcome in this reading, before this try
        if before is not None:   # changes it did not act on and did not predict: something else's (S6-W01)
            owners = mind.understanding.owners
            for e in effects:
                r = owners.get(e) or e.rsplit("_", 1)[0]
                if r != inv[1] and e not in before:
                    mind.territory.unexplained(r, e, facts)
        mind.territory.claimed(c, inv[1], self.watched_objs, before, names)   # perceived: whatever changed
                                                                               # was mine, if as predicted
        mind.meta.observe_mode(c, frozenset(names), facts, rec)
        self.tried.append((mind.t, inv, names))
        self.pushed.append((inv, facts, frozenset(names)))
        after = self.facts_now()   # the state the push left (a flag swung by hand settles within the watch)
        self.left[c] = frozenset(after - facts)
        if self.goal is not None and self.goal in names:
            # the want is had: its control slot closes (the region held, if the claim took; the joy of a slot
            # closed by a claim). First the goal stayed set, the slot reopened at once, and no joy ever formed
            # at a want met (fiction ladder, rung 0)
            self.reached.append((mind.t, self.goal))
            r = mind.understanding.owners.get(self.goal) or self.goal.rsplit("_", 1)[0]
            mind.territory.had.add(r)
            mind.territory.took_now.add(r)
            self.goal = None
        own = self.own(inv)   # what it did to its object, and to the wanted one
        if self.goal is not None and self.goal not in names and und.rel.get(c, {}).get(("causes", self.goal), [0, 0, 0])[1] > 0:
            # a told way the world contradicts: refuted by intervention (never written again), the told receipt
            # gone, and the teller noted (the phases read it: anger at the one whose word failed)
            und.rel[c][("causes", self.goal)][1] = 0.0
            und.refuted.add((c, "causes", self.goal))
            und.belied.append((mind.t, und.tellers.get((c, "causes", self.goal)), c))
        self.contrast(inv, c, facts, effects, names, before, rec)
        goal_obj = (mind.understanding.owners.get(self.goal) or self.goal.rsplit("_", 1)[0]) if self.goal else None
        if goal_obj == inv[1] and not any(e.startswith(inv[1] + "_") for e in effects):
            self.recall(inv)   # stuck on what is wanted: is there a past of the same shape?
        if self.running and not self.queue:   # the experiment's last step: report what it found
            mind.inquiry.result(self.running, before is not None and frozenset(names) == before)
            self.running = None

    def contrast(self, inv, c, facts, effects, names, before, rec, by=None):
        """What a push's outcome teaches against the push's history (one's own push, or another's watched whole):
        a single new fact in the situation, or a told condition borne out, splits it; a condition one's own last
        push made, failing, is ruled out as a preparation."""
        mind, und = self.mind, self.mind.understanding
        own = self.own(inv)   # what it did to its object, and to the wanted one
        told_c = [o for (rel, o), e in und.rel.get(c, {}).items()
                  if rel == "conditioned_by" and e[1] > 0 and not o.startswith("not:")]
        history = bool(self.alike(inv, own(names)))   # the object pushed before at another strength, alike
        if (before is not None and own(names) != own(before)) or (before is None and own(names) and (told_c or history)):
            # the push came out unlike its usual outcome on the object pushed: what is new in the situation, if
            # one fact, is the condition, and the push is split on it now (one contrast; the meta layer's
            # distinction and same checks can still undo it). First only "not this" was written by experiments,
            # and a found condition waited for the statistics of two outcomes each way; then only an
            # experiment's last step counted, and a crate that slid in the wind on an experiment's first step
            # taught nothing (fiction ladder, rungs 0-1, 2026-10-25)
            # the situation the push met: the facts before it, with what other objects turned into in its first
            # slice (a gust that came with the push is part of what it met; first the facts before it only, and
            # the crate that slid in a gust starting with the push showed no condition)
            met = set(facts)
            for e, k in effects.items():
                o = mind.understanding.owners.get(e) or e.rsplit("_", 1)[0]
                if k == 0 and o != inv[1] and not e[len(o) + 1:].lstrip("+-").replace(".", "").isdigit():
                    met = {f for f in met if not f.startswith(o + "_")} | {e}
            self.pushed[-1] = (inv, frozenset(met), frozenset(names))
            tag = self.new_condition(inv, frozenset(met), own(names))
            told = sorted(o for (rel, o), e in und.rel.get(c, {}).items()
                          if rel == "conditioned_by" and e[1] > 0 and not o.startswith("not:") and o in met)
            if tag is None and own(names) and told:
                # no contrast of its own, but a condition it was told held, and the push worked under it: the told
                # hypothesis tested and borne out (first a word confirmed by the push it was about taught nothing
                # without a failure of the push's own to set beside it; fiction ladder, rung 2)
                tag = told[0]
            x = mind.meta.reading_in(c, facts)
            if tag is None and own(names) and x not in mind.meta.splits:
                # no single fact new against every failure, but each failure lacked something the success had: the
                # smallest set of the success's facts every failure missed one of (a minimal hitting set) is the
                # condition, an AND, held as the meta layer's own nested split (split on one, the half split again on
                # the next). First only a single new fact was a condition, and a lamp that lit when both plugs were in
                # taught nothing (each plug had been in during some failed press; fiction ladder, the lamp)
                conj = self.conjunction(inv, frozenset(met), own(names))
                if conj and len(conj) > 1 and mind.meta.differentiate(x, tag=conj[0], rec=rec):
                    half, ok = mind.meta.splits[x]["yes"], True
                    for t in conj[1:]:
                        if half in mind.meta.splits or not mind.meta.differentiate(half, tag=t, rec=rec):
                            ok = False
                            break
                        mind.meta.splits[half]["by"] = by
                        half = mind.meta.splits[half]["yes"]
                    mind.meta.splits[x]["by"] = by
                    mind.meta.splits[x]["conjunction"] = tuple(conj) if ok else None
            if tag is not None and x not in mind.meta.splits and mind.meta.differentiate(x, tag=tag, rec=rec):
                sp = mind.meta.splits[x]   # this outcome met the tag (in its first slice): it is the yes half's
                sp["by"] = by              # learned by watching whom (None: by its own tries)
                # what the condition's object was in before (the gerund it left): the episode's shape, for recall
                cobj = tag.rsplit("_", 1)[0]
                was = sorted(f for _, ctx, _ in mind.meta.modes.get(sp["no"], []) for f in ctx
                             if f.startswith(cobj + "_") and f != tag)
                sp["was"] = was[0][len(cobj) + 1:] if was else None
                last = mind.meta.modes[sp["no"]][-1:] if tag not in facts else []
                if last:
                    mind.meta.modes[sp["no"]].pop()
                    mind.meta.modes[sp["yes"]].append(last[0])
            elif not own(names) and len(self.pushed) >= 2:
                # predicted to work and it did not, under the condition it was split on, which the agent's own
                # last push brought about: a condition one makes oneself is not the one that works (a sign, not
                # the cause: the flag Tom swings is not the wind). That preparation is ruled out for this push,
                # as an experiment rules out one ("not:a"), and the planner no longer counts on it
                prev, _, made = self.pushed[-2]
                conds = {sp["tag"] for y, sp in mind.meta.splits.items() if y == c or y.startswith(c + "|")}
                if prev != inv and any(t in made and t in facts for t in conds):
                    und.add(c, "conditioned_by", f"not:{inv_id(prev)}", "worked", mind.p.sov_m0)
                    und.inert.add(f"not:{inv_id(prev)}")

    def observe_other(self, inv, facts, effects, rec=None, by=None):
        """Another's push, watched whole (a person seen pushing): what followed is a seen receipt on this mind's
        own concept for that push, its outcome a mode in the meta register under the facts it met, and it is
        set against this mind's own tries of the push like one of its own (learned by watching). The territory
        is not claimed: the push was not this mind's (fiction ladder, rung 6)."""
        mind, und = self.mind, self.mind.understanding
        rec = rec if rec is not None else (self.last_rec or {"levels": [{"winners": [], "bids": {}}], "phases": [],
                                                               "closed": [], "reached": []})
        c = inv_id(inv)
        names = sorted(effects) or ["no_change"]
        for e in effects:
            und.add(c, "causes", e, "seen", self.world.gamma ** effects[e])
            und.add(e, "caused_by", c, "seen", self.world.gamma ** effects[e])
        before = self.predict(inv, facts)
        mind.meta.observe_mode(c, frozenset(names), facts, rec)
        self.pushed.append((inv, facts, frozenset(names)))
        self.known.setdefault(c, inv)
        self.contrast(inv, c, facts, effects, names, before, rec, by=by)

    def recall(self, inv):
        """SOV's Case 2, unknown to unknown by shape: stuck on a push on the wanted object, nothing held about its
        conditions, is there a split from the past on a push of the same strength and gerund, still warm, whose
        condition's object left a gerund that an object here is in now? Its condition is carried over to that
        object, held as a hypothesis (told weight: a word from one's own past, to be tested). Returns the recalled
        condition and the episode, or None. (A port of the lean arm's recall; Gerundelle's analogy layer
        transfers that a relation is expected, not what fills it. Fiction ladder, rung 6.)"""
        mind, und = self.mind, self.mind.understanding
        c = inv_id(inv)
        if any(r == "conditioned_by" for (r, _) in und.rel.get(c, {})) or c in mind.meta.splits:
            return None
        states = self.world.states()
        for x, sp in sorted(mind.meta.splits.items(), key=lambda kv: -kv[1]["t"]):
            if "_push:" not in x or x == c or not sp.get("was"):
                continue
            strength, rest = x.split("_push:")
            if strength != inv[0] or not rest.endswith("_" + inv[2].replace(" ", "_")):
                continue
            warmth = 0.5 ** ((mind.t - sp["t"]) / mind.p.h_site)
            if warmth < mind.p.cold:
                continue
            target = next((d for d, g in sorted(states.items()) if g == sp["was"] and d != inv[1]), None)
            if target is None:
                continue
            cond = f"{target}_{sp['tag'].rsplit('_', 1)[1]}"
            for k, i in self.known.items():   # every push on the object, as a told condition does
                if i[1] == inv[1]:
                    und.add(k, "conditioned_by", cond, "told", 1.0)
            und.tellers[(c, "conditioned_by", cond)] = "memory"
            ep = dict(push=x, cond=cond, from_obj=rest.rsplit("_", 1)[0], from_cond=sp["tag"].rsplit("_", 1)[0],
                      by=sp.get("by"), warmth=round(warmth, 2))
            self.recalled.append((mind.t, ep))
            return ep
        return None

    def own(self, inv):
        """What a push did that counts for it: the changes to the object pushed and to the wanted object (a button's
        press is judged by the lamp it lights, not only by the button; first only the object pushed, and a press
        that lit the lamp looked like every press that did not)."""
        goal = self.goal or (self.reached[-1][1] if self.reached else None)
        wanted = (self.mind.understanding.owners.get(goal) or goal.rsplit("_", 1)[0]) if goal else None
        return lambda m: frozenset(e for e in m if e.startswith(inv[1] + "_") or (wanted and e.startswith(wanted + "_")))

    def alike(self, inv, mode):
        """The situations of earlier pushes on the same object at another strength that did the same to the object
        pushed as this one did, and otherwise came out differently: comparable tries (a button goes down and springs
        back under a light press or a hard one; a plug a light push leaves and a hard one toggles is not, there the
        strength is what differed)."""
        own = self.own(inv)
        mine = frozenset(e for e in mode if e.startswith(inv[1] + "_"))
        return [f for i, f, m in self.pushed[:-1] if i[1:] == inv[1:] and i != inv and own(m) != mode
                and frozenset(e for e in m if e.startswith(inv[1] + "_")) == mine]

    def conjunction(self, inv, facts, mode, most=3):
        """The smallest set of facts of this situation (of other objects) such that every earlier try of the push that
        came out otherwise lacked at least one of them: [facts] (a minimal hitting set, at most `most`), or None.
        Among sets of the same size, those of facts the agent's own pushes made come first."""
        from itertools import combinations
        own = self.own(inv)
        fails = [f for i, f, m in self.pushed[:-1] if i == inv and own(m) != mode]
        if len(fails) < 2:   # the same object's other pushes too, where they did the same to it (as new_condition)
            fails = fails + self.alike(inv, mode)
        if len(fails) < 2:
            return None
        diffs = [frozenset(f2 for f2 in set(facts) - set(f) if not f2.startswith(inv[1] + "_")) for f in fails]
        if any(not d for d in diffs):   # a failure in a situation with everything this one had: no AND explains it
            return None
        made = {e for _, _, m in self.pushed[:-1] for e in m}
        left = set().union(*self.left.values()) if self.left else set()   # states the agent's pushes left in place
        pool = sorted(set().union(*diffs) & left)   # an AND of what the agent set up (a gust's flag, settling by
        diffs = [d & set(pool) for d in diffs]       # itself, is no preparation; first any fact, and a restless Mara
                                                     # learned that the button needed the flag still)
        if any(not d for d in diffs):
            return None
        for k in range(2, most + 1):
            hits = [h for h in combinations(pool, k) if all(set(h) & d for d in diffs)]
            if hits:
                return list(max(hits, key=lambda h: (sum(f in made for f in h), [-ord(c) for c in "".join(h)])))
        return None

    def new_condition(self, inv, facts, mode):
        """The fact that is new in this situation against every earlier try of the push that came out
        otherwise: a state of another object, the one the agent's own pushes brought about if there are
        several. None if no single one."""
        own = self.own(inv)
        others = [f for i, f, m in self.pushed[:-1] if i == inv and own(m) != mode]
        if not others:   # no history of its own: the same object's other pushes, where they did the same to the object
            others = self.alike(inv, mode)   # (a press is a press; first the light press that lit the lamp had nothing
                                             # to set beside it, every failure having been a hard one)
        if not others:
            return None
        new = set(facts) - set().union(*others)
        new = {f for f in new if not f.startswith(inv[1] + "_")}
        if len(new) > 1:   # several: the one a push of the agent's made
            made = {e for _, _, m in self.pushed[:-1] for e in m}
            new = {f for f in new if f in made} or new
        if len(new) > 1 and len(self.pushed) >= 2:   # still several: the one its last push before this made (the
            last = set(self.pushed[-2][2]) & new        # preparation; first none, and a door opened after the lock
            new = last if len(last) == 1 else new       # learned nothing for a settling flag beside it)
        return min(new) if len(new) == 1 else None

    def plan_step(self, invs, budget=60, horizon=3):
        """The first push of the best path MCTS finds to the wanted change over the agent's own model,
        if any path reaches it; the top winners' actions guide it (the prior)."""
        model = Model(self, self.goal)
        s = self.facts_now()
        if not model.actions(s):
            return None
        top = set(self.mind.top(self.last_rec)) if self.last_rec else set()
        prior = {a: 3.0 for a in model.actions(s) if a in top}
        a, v = mcts(model, s, prior, budget=budget, horizon=horizon, value=True)
        return invs.get(a) if v > 0 else None

    def plan(self, goal, state=None, depth=3):
        """The pushes the agent's own model says reach the goal from a state (a readout: following the
        best first push, step by step)."""
        model, s, out, r = Model(self, goal), state if state is not None else self.facts_now(), [], 0.0
        for _ in range(depth):
            if not model.actions(s):
                break
            a, v = mcts(model, s, {}, budget=60, horizon=depth, value=True)
            if v <= 0:
                break
            out.append(self.known[a])
            s, r, _ = model.step(s, a)
            if r > 0:
                break
        return out if out and r > 0 else []

    # ---- readouts (the mind's own records) ---------------------------------------------------------

    def predict(self, inv, facts=None, tree=None):
        """The commonest mode of the push's reading in that situation (meta register); None if that
        reading has never been tried."""
        facts = self.facts_now(tree) if facts is None else facts
        x = self.mind.meta.reading_in(inv_id(inv), facts)
        hist = self.mind.meta.modes.get(x, [])
        if not hist:
            return None
        modes = [h[2] for h in hist]
        return max(set(modes), key=lambda m: (modes.count(m), sorted(m)))

    def gap(self, inv, facts=None):
        """How much of the push is not understood: the share of its SOV still open (the register)."""
        return 1.0 - self.mind.understanding.level(inv_id(inv))

    def conditions_of(self, inv):
        """The boundaries the push has been split on (the meta layer's splits), outermost first."""
        meta, out, todo = self.mind.meta, [], [inv_id(inv)]
        while todo:
            x = todo.pop(0)
            if x in meta.splits:
                out.append(meta.splits[x]["tag"])
                todo += [meta.splits[x]["yes"], meta.splits[x]["no"]]
        return out


class Model:
    """The agent's own model of the world, read from the mind's records, for MCTS (a want's plan): a
    state is the facts; the actions are the pushes the mind knows whose configuration holds there; a
    push's outcome is the commonest mode of its reading in that state (the meta register), and the
    state it leaves is the facts its changes name (a change 'cable_parting' is the cable now parting).
    Reward: the wanted change in the outcome."""

    def __init__(self, agent, goal):
        self.agent, self.goal = agent, goal

    def actions(self, s):
        return sorted(c for c, inv in self.agent.known.items() if f"{inv[1]}_{inv[2].replace(' ', '_')}" in s)

    def step(self, s, a):
        inv = self.agent.known[a]
        und = self.agent.mind.understanding
        made = {x[5:] for x in s if x.startswith("made:")}
        if any(("conditioned_by", f"not:{m}") in und.rel.get(a, {}) for m in made):
            # a preparation ruled out for this push (the state it made is not the one that works)
            return frozenset(x for x in s if not x.startswith("made:")), 0.0, None
        mode = self.agent.predict(inv, frozenset(x for x in s if not x.startswith("made:")))
        if mode is None:   # never tried in this reading: a way the agent was told is expected to work as far as
            told = und.rel.get(a, {}).get(("causes", self.goal), [0, 0, 0])[1]   # it believes what it is told
            r = self.agent.mind.p.credulity if told > 0 else 0.0                  # (temperament: credulity)
            return frozenset(x for x in s if not x.startswith("made:")), r, None
        owners = und.owners
        objs = {o for o in owners.values()}
        nxt = {x for x in s if not x.startswith("made:")}
        left = self.agent.left.get(a)
        for e in (sorted(left) if left is not None else mode):   # a change on a known object: that object is
            owner = owners.get(e)   # now in that state; the state the push was seen to leave, if it was tried
            if owner in objs and e.startswith(owner + "_") and not e[len(owner) + 1:].lstrip("+-").replace(".", "").isdigit():
                nxt = {x for x in nxt if not (x.startswith(owner + "_") and x[len(owner) + 1:] in self.states_of(owner))} | {e}
        # (first every change in the outcome, the last alphabetically winning: a flag pushed by hand was read as
        # left swinging, though it settles within the watch, and the planner swung it again and again)
        nxt.add(f"made:{a}")   # the state this action made (so a ruling on it can be read at the next step)
        # the reward expected, not the commonest outcome's: the share of the push's outcomes in this reading
        # that brought the goal (first the commonest outcome alone, and a push that worked half the time when
        # the flag swung was planned as never working; fiction ladder, rung 1)
        meta = self.agent.mind.meta
        hist = meta.modes.get(meta.reading_in(inv_id(inv), frozenset(x for x in s if not x.startswith("made:"))), [])
        r = sum(1 for h in hist if self.goal in h[2]) / len(hist) if hist else (1.0 if self.goal in mode else 0.0)
        return frozenset(nxt), r, None

    def states_of(self, owner):
        """The gerunds an object has been perceived in (from the agent's perception log)."""
        out = set()
        for facts, _ in self.agent.history:
            for x in facts:
                if x.startswith(owner + "_"):
                    out.add(x[len(owner) + 1:])
        return out

    def expected(self, s, a):
        return self.step(s, a)[1]
