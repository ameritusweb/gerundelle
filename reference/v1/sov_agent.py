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


def distinguishing(tags, others):
    """The smallest combination of `tags` that no other attempt carried in full, the tags commonest among the others let
    go first; None if some other attempt carried all of them (embodied/body/grasp.py's)."""
    s = set(tags)
    if any(s <= o for o in others):
        return None
    common = {t: sum(t in o for o in others) for t in s}
    for t in sorted(s, key=lambda x: (-common[x], x)):
        if len(s) > 1 and not any((s - {t}) <= o for o in others):
            s.discard(t)
    return frozenset(s)


def constraints_from(trials):
    """Each kind of failure's constraints among trials (what was met, what came of it): what is distinctive of its
    failures among the attempts, merged into what two share while that still tells them apart (grasp.py's)."""
    out = {}
    for e in sorted({ev for _, ev in trials if ev != "want"}):
        others = [t for t, ev in trials if ev != e]
        conj = []
        for t in [t for t, ev in trials if ev == e]:
            d = distinguishing(t, others)
            if d is not None and d not in conj:
                conj.append(d)
        merged = True
        while merged and len(conj) > 1:
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
        self.stack = []        # sub-wants (Params.subwants): the wants above the current one, outermost first
        self.sub_since = 0     # when the current sub-want was set
        self.failed_subs = set()   # sub-wants dropped (not met in time): not set again
        self.sub_log = []      # (tick, want, 'set' | 'met' | 'dropped' | 'tried' | 'kept' | 'restored' | 'used' | 'released')
        self.trials = []       # Params.converge: (what a push met, as the world said before it was made; what came of it)
        self.meeting = None    # what the push under way met
        self.noticed = []      # (tick, invitation): pushes noticed where the constraints converged
        self.serving = {}      # Params.sub_cost: a sub-want -> what the way it serves needs and had when it was set
        self.met_samples = {}  # Params.bridge: push -> [(situation, what the world said it would meet there)]
        self.kept = {}         # fact -> the want it was made for (Params.keep_subs): restored if another undoes it
        self.quiet = 0         # ticks running with no push of its own (Params.winner_acts: a patient mind watches first)
        self.news = []         # Params.news_in_structure: this tick's news, perceived but not presented

    # ---- perception ---------------------------------------------------------------------------------

    def facts_now(self, tree=None):
        """The situation: each object's state, read as a fact. Not the world's event objects (world.events: what just
        happened, an outcome, e.g. a reply), which are no condition a push is tried under (first they were part of the
        situation, and a chess mind learned "Rxd5 wins when Black's last answer was a pass" and stood still for 300
        ticks: cognitive chess rung 2). A world that names no events is read whole, as before."""
        ev = getattr(self.world, "events", ())
        return frozenset(f"{d}_{g.replace(' ', '_')}" for d, g in self.world.states(tree).items() if d not in ev)

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
        offers = [clause(c, tags=("invitation", inv[1])) for c, inv in invs.items()]
        if mind.p.news_in_structure:   # news perceived into the structure, not presented as a competitor
            self.news = news
            return wants + offers, invs
        self.news = []
        return news + wants + offers, invs

    # ---- a tick ------------------------------------------------------------------------------------

    def tick(self, force=None):
        """force: an invitation to push now (a scripted intervention, for tests)."""
        world = self.world
        if not self.watching and not self.queue:   # a scene is not set back in the middle of an
            world.renew()                           # experiment (first: between its two steps, and the
                                                    # latch was reseated before the lid was pushed)
        und = self.mind.understanding   # a wanted change opens a control slot on its region, open until
        terr = self.mind.territory      # the change comes (REORG.md step 4; first the want was only a
        if self.stack and self.mind.t - self.sub_since > self.mind.p.sub_budget:   # a sub-want not met in time:
            self.drop_sub()                                                         # dropped, the parent taken up
        if self.goal is not None and self.mind.p.patience is not None:   # temperament: claims running on the
            r = und.owners.get(self.goal) or self.goal.rsplit("_", 1)[0]  # wanted region that failed, as many
            if terr.rows.get(r, {}).get("fails", 0) >= self.mind.p.patience:   # as the mind's patience: the
                if self.stack:   # a sub-want's patience spent: it is dropped, not the want it served
                    self.drop_sub()
                else:
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
        if self.kept and not self.watching and not self.queue:
            self.keep_watch()
        rec = self.mind.tick(inputs, seen=self.news)
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
        elif self.goal is not None and (step := self.planned(invs)) is not None:
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
            if getattr(world, "still", False) and (known := self.foreseen(steps, invs)) is not None:
                # in a still world an experiment whose every step was already done in the situation it would meet
                # comes out as those did: reported, not done (the known last step's rule, for the whole experiment).
                # First its preparation was pushed again and the known last step skipped: in a chess puzzle, a rook
                # move replayed before each of the rook's other moves, 24 of 56 pushes (cognitivechess, rung 0)
                self.mind.inquiry.result(eid, known)
                steps = []
            if steps:
                choice = invs.get(steps[0])
                self.queue = steps[1:] if choice is not None else []
                self.running = eid if choice is not None else None
        if choice is None and self.mind.p.winner_acts and not self.queue:
            choice = self.winner(rec, invs)
        if choice is None:
            self.quiet += 1
            self.idle()   # waiting is watching too
            return None, rec
        self.quiet = 0
        if self.mind.p.converge and self.goal is not None and hasattr(world, "relations_of"):
            self.meeting = world.relations_of(choice)
        self.watching = (choice, self.facts_now(), 0, {})
        self.watched_objs = set()
        self.watch(world.act(choice, hold=bool(self.running) and force is None), rec)
        return choice, rec

    def winner(self, rec, invs):
        """Params.winner_acts: no way and no experiment, but pushes on offer won the top level. What wins attention is what
        the agent does, chosen among them by temperament (fiction/temperament.py: each trait one SOV quantity, every value a
        working mind, different values different characters), each trait neutral at its default:
          patience     an impatient mind (None) acts on attention at once; a patient one watches first, for up to its
                       patience in ticks, never past the world's watch (horizon), so a turn can't be watched away
          curiosity    a push's bid times (1 - familiarity) ** (curiosity - 1), familiarity n / (n + kappa) for a push made
                       n times: the curious lean to what they know least, the incurious to what they know
          persistence  a push on the piece of the last push is weighted by persistence: the persistent stay with what
                       they were doing, the restless move on
        A winning push need not be on offer now (a move from another position, still held in attention): it is tried all
        the same, and the world pushes back (nothing happens); the mind learns that as any outcome, and curiosity,
        boredom, patience and the meta layer move it on (the user, 2026-11-01). First only pushes on offer were tried,
        and pushes from other positions that held the top were never tested, so they kept it.
        Ties by name. None if no push won, or the mind is still watching."""
        p = self.mind.p
        lv = rec["levels"][-1]
        # with Params.imagined_lane only pushes perceived now act (nothing imagined is acted on: the firewall); without it,
        # any known push that won is tried, and the world may push back
        pool = invs if p.imagined_lane else self.known
        won = [c for c in lv["winners"] if c.split("|")[0] in pool]   # (a split push competes as its half)
        if not won:
            return None
        wait = 0 if p.patience is None else min(p.patience, getattr(self.world, "horizon", 1))
        if self.quiet < wait:
            return None
        last = self.pushed[-1][0][1] if self.pushed else None

        def pref(c):
            inv = self.known[c.split("|")[0]]
            n = sum(1 for i, _, _ in self.pushed if i == inv)
            familiarity = n / (n + p.kappa)
            v = max(lv["bids"].get(c, 0.0), 1e-9) * max(1.0 - familiarity, 1e-9) ** (p.curiosity - 1.0)
            return v * (p.persistence if inv[1] == last else 1.0)
        best = min(won, key=lambda c: (-round(pref(c), 9), c))
        return self.known[best.split("|")[0]]

    def foreseen(self, steps, invs):
        """An experiment (the action alone, or a preparation then the action) whose steps were all done before in the
        situations they would meet now: whether the action would come out as it usually does here (True: the
        preparation ruled out; for the action alone, always), read off the agent's own pushes; None if a step is new,
        or the action was never tried here."""
        if len(steps) == 1 and invs.get(steps[0]) is not None:
            now = self.facts_now()
            return True if any(i == invs[steps[0]] and f == now for i, f, _ in self.pushed) else None
        if len(steps) != 2 or invs.get(steps[0]) is None or invs.get(steps[1]) is None:
            return None
        prep, act, now = invs[steps[0]], invs[steps[1]], self.facts_now()
        made = next((m for i, f, m in reversed(self.pushed) if i == prep and f == now), None)
        if made is None or self.predict(act, now) is None:
            return None
        owners = self.mind.understanding.owners
        made = {e for e in made if e != "no_change"}
        moved = {owners.get(e) or e.rsplit("_", 1)[0] for e in made}
        after = frozenset({f for f in now if (owners.get(f) or f.rsplit("_", 1)[0]) not in moved} | made)
        if not any(i == act and f == after for i, f, _ in self.pushed):
            return None
        return self.predict(act, after) == self.predict(act, now)

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
        if self.meeting is not None:   # Params.converge: what it met, and what came of it (the want, or a failure's kind)
            if self.goal is not None and not self.stack:   # pushes for the root want only (not a sub-want's means)
                self.trials.append((self.meeting, "want" if self.goal in names else self.kind(names)))
            self.meeting = None
        after = self.facts_now()   # the state the push left (a flag swung by hand settles within the watch)
        self.left[c] = frozenset(after - facts)
        self.just = (c, after)     # the push just made, and the world as it left it (Params.told_effects)
        if self.stack and any(g in names for g in self.stack):   # a want a sub-want served came on the way: it
            k = next(i for i, g in enumerate(self.stack) if g in names)   # is had, and the sub-wants under it go
            for g in [self.goal] + self.stack[k + 1:][::-1]:
                self.sub_log.append((mind.t, g, "dropped"))
            self.goal, self.stack = self.stack[k], self.stack[:k]
        if self.goal is not None and self.goal in names:
            # the want is had: its control slot closes (the region held, if the claim took; the joy of a slot
            # closed by a claim). First the goal stayed set, the slot reopened at once, and no joy ever formed
            # at a want met (fiction ladder, rung 0)
            if self.stack:   # a sub-want met: the want it served is taken up again
                self.sub_log.append((mind.t, self.goal, "met"))
                if mind.p.keep_subs:   # and kept for it, until that want's push uses it
                    self.kept[self.goal] = self.stack[-1]
                    self.sub_log.append((mind.t, self.goal, "kept"))
            else:
                self.reached.append((mind.t, self.goal))
            r = mind.understanding.owners.get(self.goal) or self.goal.rsplit("_", 1)[0]
            mind.territory.had.add(r)
            mind.territory.took_now.add(r)
            self.goal = self.stack.pop() if self.stack else None
            self.sub_since = mind.t
        own = self.own(inv)   # what it did to its object, and to the wanted one
        after = [o for (rel, o), e in und.rel.get(c, {}).items() if rel == "after" and e[1] > 0]             if mind.p.told_effects else []
        out_of_order = bool(after) and not (len(self.pushed) >= 2 and inv_id(self.pushed[-2][0]) in after)
        if self.goal is not None and self.goal not in names and not out_of_order                 and und.rel.get(c, {}).get(("causes", self.goal), [0, 0, 0])[1] > 0:
            # a told way the world contradicts: refuted by intervention (never written again), the told receipt
            # gone, and the teller noted (the phases read it: anger at the one whose word failed)
            und.rel[c][("causes", self.goal)][1] = 0.0
            und.refuted.add((c, "causes", self.goal))
            und.belied.append((mind.t, und.tellers.get((c, "causes", self.goal)), c))
        if mind.p.told_effects:   # a told effect the world did not bring: refuted, as a told way is
            after = self.facts_now()
            for (rel, x), e in list(und.rel.get(c, {}).items()):
                if rel == "causes" and e[1] > 0 and x != self.goal and x not in names and x not in after:
                    e[1] = 0.0
                    und.refuted.add((c, "causes", x))
                    und.belied.append((mind.t, und.tellers.get((c, "causes", x)), c))
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
                    mind.meta.version += 1
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
        s = self.facts_now()
        just = getattr(self, "just", None)
        if self.mind.p.told_effects and just is not None and just[1] == s:
            s = s | {f"made:{just[0]}"}   # the push just made, while the world still stands as it left it
        # the first push is chosen from those the world offers now (perceived); deeper ones from the model. First
        # every known push whose configuration held was a first push: in a chess world a rook's configuration is its
        # state wherever it stands, the model offered 75 rook moves seen from other squares to a budget of 60
        # rollouts, the capture the sub-want had prepared went unexplored, and the move chosen was not on the board
        # (the cognitive chess ladder, rung 1)
        model = Model(self, self.goal, root=(s, set(invs)))
        if not model.actions(s):
            return None
        top = set(self.mind.top(self.last_rec)) if self.last_rec else set()
        prior = {a: 3.0 for a in model.actions(s) if a in top}
        a, v = mcts(model, s, prior, budget=budget, horizon=horizon, value=True)
        return invs.get(a) if v > 0 else None

    # ---- sub-wants (Params.subwants; the civilization ladder P6) ---------------------------------------------------
    #
    # A want the planner finds no way to (plan_step: no path over the agent's own model) sets a nearer want, by
    # means and ends over the mind's own records:
    # 1. A way known: a push that has brought the want before (self.pushed). What it needs and does not have now is
    #    the sub-want: its configuration (the object pushed, in the gerund the push is invited in) and the condition it
    #    was split on (the tag of the half whose outcomes brought the want). Recursively, a sub-want of a sub-want.
    # 2. No way known: Inquiry's "a situation it was never tried in", across steps. The pushes on the wanted object,
    #    and the objects their splits' conditions name: a combination of states of these, seen but never together at
    #    a push on the wanted object, is made, one fact at a time, each fact one some known push has brought about.
    # A sub-want met: the want it served is taken up again. Not met in sub_budget ticks, or its claims failing as often
    # as the mind's patience: dropped, and not set again. First a far want (the moon's way home, seven steps) was out of
    # reach of every temperament: experiments are a preparation and an action, the planner looks three ahead; an
    # authored curriculum of three wants carried three minds home (civilization LADDER.md, P5).

    def planned(self, invs):
        """plan_step, and, with sub-wants on, a nearer want set when it finds no way (then planned for); with
        Params.converge, last, the push the constraints converge on."""
        if self.stack and self.mind.p.sub_yield and self.goal in self.facts_now():
            # a sub-want that holds is had, whoever made it (first only a push of the mind's own that brought it met it:
            # one set where it already held was never met, idled out its budget, and was dropped for good, and the mind
            # stood still for 450 ticks; cognitive chess rung 1, seed 4)
            self.sub_log.append((self.mind.t, self.goal, "met"))
            self.goal, self.sub_since = self.stack.pop(), self.mind.t
        if self.stack and self.mind.p.sub_yield and not self.queue and not self.running:
            served, self.goal = self.goal, self.stack[0]   # the root want: does the planner find a way to it now?
            root_step = self.plan_step(invs)
            if root_step is not None and not (self.mind.p.converge and self.direct(root_step, invs)
                                              and self.runs_into(root_step)):
                self.sub_log.append((self.mind.t, served, "yielded"))
                self.stack, self.sub_since = [], self.mind.t
                return root_step
            self.goal = served
        step = self.plan_step(invs)
        if step is not None and self.mind.p.converge and not self.stack and self.direct(step, invs)                 and self.runs_into(step):
            # a direct way (the push itself expected to bring the want), read off this push's own records, that meets a
            # constraint the failures of other pushes revealed: contradicted, not taken. First the planner came first,
            # and in new positions a move's name that had mated elsewhere ("Ra8") was a way known: 297 of 486 pushes,
            # nearly all failing (cognitive chess 1e). A means (the first step of a longer way) is not judged by
            # constraints on direct ways: first it was, and the trade that removes a defender was vetoed (rung 1)
            self.noticed.append((self.mind.t, ("contradicted", step)))
            if self.mind.p.bridge and self.mind.p.subwants and not self.queue and not self.running:
                fact = self.clearing(step)   # what would let the contradicted way clear: wanted, nearer
                if fact is not None:
                    self.stack.append(self.goal)
                    self.goal, self.sub_since = fact, self.mind.t
                    self.sub_log.append((self.mind.t, fact, "set"))
                    self.sub_log.append((self.mind.t, fact, "bridged"))
                    return self.plan_step(invs)
            step = None
        if step is not None:
            return step
        free = not self.queue and not self.running
        if self.mind.p.subwants and free and len(self.stack) < 4:
            sub = self.subwant(self.facts_now(), invs)
            if isinstance(sub, tuple):   # the situation never tried is here: the push is tried in it now
                self.sub_log.append((self.mind.t, inv_id(sub[1]), "tried"))
                return sub[1]
            if sub is not None:
                self.stack.append(self.goal)
                self.goal, self.sub_since = sub, self.mind.t
                self.sub_log.append((self.mind.t, sub, "set"))
                return self.plan_step(invs)
        if self.mind.p.converge and free and not self.stack:
            # no way known and nothing nearer to want: the push the constraints converge on (first noticed before
            # sub-wants, and a sub-want that would have set up a combination was never set: rung 1)
            noticed = self.notice(invs)
            if noticed is not None:
                self.noticed.append((self.mind.t, noticed))
                return noticed
        return None

    def direct(self, inv, invs):
        """Whether a push is expected, by the agent's own model, to bring the want itself (not a means to it)."""
        s = self.facts_now()
        return Model(self, self.goal, root=(s, set(invs))).step(s, inv_id(inv))[1] > 0

    def keep_watch(self):
        """Kept facts (Params.keep_subs): one whose want is no longer held is released; one gone because this mind's own
        last push changed its object is used (a launch spends the jar it was filled for); one gone otherwise was undone
        by something else, and is restored: set again as the current want, the current one held above it. First a
        sub-want, once met, was not held: in a population another mind's curiosity could empty the jar between its
        filling and the launch it was filled for, and nothing answered it (the civilization ladder P7)."""
        facts, t = self.facts_now(), self.mind.t
        active = {self.goal, *self.stack}
        last = self.pushed[-1][2] if self.pushed else frozenset()
        for f, want in list(self.kept.items()):
            if want not in active:
                del self.kept[f]
                self.sub_log.append((t, f, "released"))
            elif f not in facts:
                del self.kept[f]
                if any(self.owner_of(e) == self.owner_of(f) and e != f for e in last):   # (not the push that made it)
                    self.sub_log.append((t, f, "used"))
                elif f != self.goal and f not in self.stack and len(self.stack) < 4:
                    self.stack.append(self.goal)
                    self.goal, self.sub_since = f, t
                    self.failed_subs.discard(f)
                    self.sub_log.append((t, f, "restored"))
                    return

    def drop_sub(self):
        """A sub-want not met: set aside for good, and the want it served taken up again."""
        self.failed_subs.add(self.goal)
        self.sub_log.append((self.mind.t, self.goal, "dropped"))
        self.goal, self.sub_since = self.stack.pop(), self.mind.t

    def owner_of(self, fact):
        """The object a fact is about: the longest object name it starts with (the world's objects), else its stem."""
        objs = getattr(self.world, "objs", {}) or {}
        return max((o for o in objs if fact.startswith(o + "_")), key=len, default=fact.rsplit("_", 1)[0])

    # ---- convergence (Params.converge; the cognitive chess ladder rung 1e) ---------------------------------------
    #
    # embodied/CONSTRAINT_DISCOVERY.md, as embodied/body/grasp.py does it for the hand: each failed push reveals a
    # constraint, what is distinctive of its kind of failure among the pushes; an untried push is perceived before it
    # is made (world.relations_of) and clears a constraint unless it would meet all of it; the constraints stand as
    # molecules whose open site is clearing them, each combination weighing by its receipts (1 - 1/2^n); a tournament
    # with candidate support in superposition notices the push they converge on. Nothing is noticed where the
    # constraints don't tell the pushes apart: then sub-wants and experiments go on as before.

    def kind(self, names):
        """A failure's kind: what the world's event objects are after the push (world.events, e.g. its reply), as
        perceived; else what changed. (First what they changed to: the same reply twice running is no change, and
        most failures were filed under whatever else had changed, thirty kinds where there were four.)"""
        ev = getattr(self.world, "events", ())
        out = sorted(f"{d}_{g}" for d, g in self.world.states().items() if d in ev)
        return "|".join(out) if out else "|".join(sorted(names))

    def runs_into(self, inv):
        """Whether a push would meet all of some constraint its failures revealed (Params.converge)."""
        cons = constraints_from(self.trials)
        meet = self.world.relations_of(inv) if hasattr(self.world, "relations_of") else frozenset()
        self.sample(inv, meet)
        return any(h <= meet for hs in cons.values() for h in hs)

    def sample(self, inv, meet):
        """What a push would meet here, kept with the situation (Params.bridge's evidence; the last 60 per push)."""
        if self.mind.p.bridge:
            rows = self.met_samples.setdefault(inv_id(inv), [])
            rows.append((self.facts_now(), frozenset(meet)))
            del rows[:-60]

    def clearing(self, inv):
        """Params.bridge: the fact that would let a contradicted push clear the constraints it meets here: present in
        every situation where it would have cleared them, absent from every one where it ran into them (this one too),
        and made by some known push. The most often seen first; None if no such fact."""
        cons = constraints_from(self.trials)
        now, meet = self.facts_now(), self.world.relations_of(inv)
        hits = [h for hs in cons.values() for h in hs if h <= meet]
        if not hits:
            return None
        rows = self.met_samples.get(inv_id(inv), [])
        clear = [f for f, m in rows if not any(h <= m for h in hits)]
        blocked = [f for f, m in rows if any(h <= m for h in hits)] + [now]
        if not clear:
            return None
        config = f"{inv[1]}_{inv[2].replace(' ', '_')}"
        candidates = (frozenset.intersection(*clear) - frozenset.union(*blocked)) - {config}
        taken = set(self.stack) | {self.goal} | self.failed_subs
        ok = [f for f in candidates if f not in taken and any(self.known.get(inv_id(i)) for i in self.makers(f))]
        return max(sorted(ok), key=lambda f: len(self.makers(f))) if ok else None

    def notice(self, invs):
        """The untried push the constraints converge on (supported most, ties by order), or None."""
        cons = constraints_from(self.trials)
        if not cons:
            return None
        now = self.facts_now()
        options = [i for _, i in sorted(invs.items()) if not any(j == i and f == now for j, f, _ in self.pushed)]
        if not options:
            return None
        meet = {i: self.world.relations_of(i) for i in options}
        for i, mt in meet.items():
            self.sample(i, mt)
        combos = [(f"{e}#{k}", h, sum(1 for t, ev in self.trials if ev == e and h <= t))
                  for e, hs in sorted(cons.items()) for k, h in enumerate(hs)]
        clears = {i: [c for c, h, _ in combos if not h <= meet[i]] for i in options}
        mind = Mind(Params(support="candidates", sov=False, meta=False, closure=False))
        mols = [clause(f"try:{inv_id(i)}", tags=("attempt",) + tuple(f"clears:{c}" for c in clears[i])) for i in options]
        for c, h, n in combos:
            mind.present(clause(f"constraint:{c}", tags=("constraint",), sites=(f"clears:{c}",)), 1 - 0.5 ** n)
        bids = mind.tick(mols)["levels"][0]["bids"]
        bid = lambda i: round(bids.get(f"try:{inv_id(i)}", 0.0), 9)
        ranked = sorted(options, key=lambda i: (-bid(i), i))   # ties among the top by the push itself (its order)
        top = ranked[0]
        # the push supported most, if the constraints tell the pushes apart at all (grasp.py's rule: over-constrained,
        # the receipts decide; among equals, the order). First only one that cleared every constraint (one over-general
        # constraint left nothing in 50 moves), then only one above every other (ties left the choice to experiments:
        # 9 noticed in 296 pushes)
        return top if clears[top] and bid(top) > bid(ranked[-1]) else None

    def costly(self, inv, fact, root):
        """With Params.sub_cost: a push that, where it brought `fact` about, also moved the root want's object to a state
        other than the root want (it undoes what the means are for)."""
        if not self.mind.p.sub_cost or root is None:
            return False
        obj = self.owner_of(root)
        return any(any(self.owner_of(e) == obj and e != root for e in names)
                   for i, _, names in self.pushed if i == inv and fact in names)

    def undoes(self, inv, fact, keep):
        """With Params.sub_cost: a push that, where it brought `fact` about, also changed something the way it would serve
        needs and has (`keep`) to another state: it undoes the way. (First only the root want's object counted, and a
        mind wanting "e8 held" for the mate Rxe8 met it with Re8, the bishop taking the rook that was to mate: 201
        rooks; cognitive chess 1e.)"""
        if not self.mind.p.sub_cost or not keep:
            return False
        objs = {self.owner_of(k): k for k in keep}
        return any(any(self.owner_of(e) in objs and e != objs[self.owner_of(e)] for e in names)
                   for i, _, names in self.pushed if i == inv and fact in names)

    def makers(self, fact):
        """The pushes that have brought a fact about, most often first: invitation -> times."""
        out = {}
        for inv, _, names in self.pushed:
            if fact in names:
                out[inv] = out.get(inv, 0) + 1
        return sorted(out, key=lambda i: (-out[i], i))

    def needs(self, inv, want):
        """What a push needs to bring a want: its configuration, and the conditions of the splits on it down to a half
        whose outcomes brought the want (yes halves only: a condition that must not hold is no want; with
        Params.polarity, it prevents the push, and its object as it stood where the want came is wanted)."""
        out = [f"{inv[1]}_{inv[2].replace(' ', '_')}"]
        meta, x = self.mind.meta, inv_id(inv)
        while x in meta.splits:
            sp = meta.splits[x]
            brought = lambda half: any(want in h[2] for h in meta.modes.get(half, []))
            if brought(sp["yes"]):
                if not (self.mind.p.sub_tested and not meta.modes.get(sp["no"])):   # (never seen absent: not known
                    out.append(sp["tag"])                                            # to matter, Params.sub_tested)
                if self.mind.p.polarity:   # the condition enables the push (written once: needs is read often)
                    self.polar(sp["tag"], "enables", inv_id(inv))
                x = sp["yes"]
            elif brought(sp["no"]):
                if self.mind.p.polarity:   # the condition prevents it: its object as it stood where the want came
                    self.polar(sp["tag"], "prevents", inv_id(inv))
                    obj = self.owner_of(sp["tag"])
                    stood = [f for h in meta.modes.get(sp["no"], []) if want in h[2] for f in h[1]
                             if self.owner_of(f) == obj and f != sp["tag"]]
                    if stood:
                        out.append(max(sorted(set(stood)), key=stood.count))
                x = sp["no"]
            else:
                break
        return out

    def polar(self, tag, rel, c):
        """A condition's polarity, written in the register once (worked out from the agent's own splits)."""
        und = self.mind.understanding
        if (rel, c) not in und.rel.get(tag, {}):
            und.add(tag, rel, c, "worked", 1.0)

    def states_seen(self, obj):
        """The states an object stood in when the mind acted (not the passing ones a slice shows: a hop, a launch)."""
        return sorted({x for _, facts, _ in self.pushed for x in facts if self.owner_of(x) == obj})

    def subwant(self, facts, invs=None):
        """The nearer want for the current one (see above), or None; or ("try", invitation) when the situation never
        tried is the one that holds now: the push is made in it rather than another sub-want set (first, a combination
        made by sub-wants was skipped once it held, the next one set at once, and the push it was made for never came:
        the civilization ladder P7, one mind re-making its jar's states 55 times and never launching)."""
        goal = self.goal
        taken = set(self.stack) | {goal} | self.failed_subs
        root = self.stack[0] if self.stack else goal   # the want the sub-wants serve
        makeable = lambda f, keep=(): f not in taken and any(
            self.known.get(inv_id(i)) and not self.costly(i, f, root) and not self.undoes(i, f, keep)
            for i in self.makers(f))
        for inv in self.makers(goal):   # 1. a way known
            needs = self.needs(inv, goal)
            keep = [f for f in needs if f in facts]   # what the way needs and has now: a means must not undo it
            need = [f for f in needs if f not in facts]
            need = [f for f in need if makeable(f, keep)]
            if need:
                self.serving[need[0]] = keep
                return need[0]
        obj = self.owner_of(goal)   # 2. a situation never tried, on the wanted object
        mine = {inv_id(i) for i in self.known.values() if i[1] == obj}
        conds = sorted({self.owner_of(sp["tag"]) for x, sp in self.mind.meta.splits.items()
                        if x.split("|")[0] in mine} - {obj})
        if not conds:
            return None
        objs = [obj] + conds
        tried = {frozenset(f for f in fs if self.owner_of(f) in objs) for i, fs, _ in self.pushed if i[1] == obj}
        here = frozenset(f for f in facts if self.owner_of(f) in objs)
        if here not in tried and invs:   # the untried situation holds now: try the conditioned push in it
            split = {x.split("|")[0] for x in self.mind.meta.splits}
            now = sorted((i for c, i in invs.items() if i[1] == obj), key=lambda i: (inv_id(i) not in split, i[0] != "hard", i))
            if now:
                return ("try", now[0])
        from itertools import product
        best = None
        for combo in product(*[self.states_seen(o) for o in objs]):
            if frozenset(combo) in tried:
                continue
            need = [f for f in combo if f not in facts]
            if not need or not all(makeable(f) for f in need):
                continue
            key = (len(need), need)
            if best is None or key < best[0]:
                best = (key, need)
        return best[1][0] if best else None

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

    def __init__(self, agent, goal, root=None):
        """root: (the state now, the pushes offered in it): there, the actions are the offered ones."""
        self.agent, self.goal, self.root = agent, goal, root

    def actions(self, s):
        if self.root is not None and s == self.root[0]:
            return sorted(c for c in self.root[1] if c in self.agent.known)
        return sorted(c for c, inv in self.agent.known.items() if f"{inv[1]}_{inv[2].replace(' ', '_')}" in s)

    def step(self, s, a):
        if self.costly(s, a):   # no means to a sub-want if it undoes the want the sub-want serves
            return frozenset(x for x in s if not x.startswith("made:")), 0.0, None
        return self.stepped(s, a)

    def stepped(self, s, a):
        """With Params.imagine and a world that can imagine: a push whose conditions question is open is imagined from the
        board now along the line of pushes that led to s (carried in s as 'line:...'); otherwise read off the records."""
        p, world = self.agent.mind.p, self.agent.world
        if not (p.imagine and hasattr(world, "imagine")):
            return self.recorded(s, a)
        line = next((x[5:] for x in s if x.startswith("line:")), "")
        moves = tuple(m for m in line.split("|") if m) + (self.agent.known[a][0],)
        base = frozenset(x for x in s if not x.startswith("line:"))
        if self.agent.mind.understanding.funding(a, "conditions") < 1.0:   # not understood: imagined
            got = world.imagine(moves)
            if got is None:   # not a move there
                return s, 0.0, None
            facts, effects = got
            r = p.credulity if self.goal in effects else 0.0   # believed as far as the mind believes what it has not lived
            return frozenset(facts) | {f"made:{a}", "line:" + "|".join(moves)}, r, None
        nxt, r, x = self.recorded(base, a)
        return frozenset(nxt) | {"line:" + "|".join(moves)}, r, x

    def costly(self, s, a):
        """Params.sub_cost: serving a sub-want, a push whose usual outcome here moves the root want's object away from
        it, or changes something the way the sub-want serves needs and had."""
        ag = self.agent
        if not (ag.mind.p.sub_cost and ag.stack):
            return False
        root = ag.stack[0]
        mode = ag.predict(ag.known[a], frozenset(x for x in s if not x.startswith(("made:", "line:"))))
        if not mode:
            return False
        obj = ag.owner_of(root)
        if any(ag.owner_of(e) == obj and e != root for e in mode):
            return True
        keep = {ag.owner_of(k): k for k in ag.serving.get(ag.goal, ())}   # and what the way it serves needs
        return any(ag.owner_of(e) in keep and e != keep[ag.owner_of(e)] for e in mode)

    def recorded(self, s, a):
        inv = self.agent.known[a]
        und = self.agent.mind.understanding
        made = {x[5:] for x in s if x.startswith("made:")}
        if any(("conditioned_by", f"not:{m}") in und.rel.get(a, {}) for m in made):
            # a preparation ruled out for this push (the state it made is not the one that works)
            return frozenset(x for x in s if not x.startswith("made:")), 0.0, None
        mode = self.agent.predict(inv, frozenset(x for x in s if not x.startswith("made:")))
        told_r = None
        if mode is None:   # never tried in this reading: a way the agent was told is expected to work as far as
            told = und.rel.get(a, {}).get(("causes", self.goal), [0, 0, 0])[1]   # it believes what it is told
            if self.agent.mind.p.told_effects:
                after = [o for (rel, o), e in und.rel.get(a, {}).items() if rel == "after" and e[1] > 0]
                if after and not any(f"made:{o}" in s for o in after):
                    told = 0   # told to work after another push: only along a line where that push was just made
            if self.agent.mind.p.told_effects:   # and what it was told the push causes is its outcome (a told line)
                out = {x for (rel, x), e in und.rel.get(a, {}).items()
                       if rel == "causes" and e[1] > 0 and x != self.goal and (a, "causes", x) not in und.refuted}
                if out or told > 0:
                    mode = frozenset(out | ({self.goal} if told > 0 else set()))
                    told_r = self.agent.mind.p.credulity if told > 0 else 0.0
            if mode is None:
                r = self.agent.mind.p.credulity if told > 0 else 0.0                  # (temperament: credulity)
                base = frozenset(x for x in s if not x.startswith("made:"))
                if self.agent.mind.p.told_effects:   # nothing known of what it does, but that it was made (a told
                    return base | {f"made:{a}"}, r, None   # line can be read on from it)
                return base, r, None
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
        if told_r is not None:   # a told outcome is believed as far as the mind believes what it is told
            r = told_r
        return frozenset(nxt), r, None

    def states_of(self, owner):
        """The gerunds an object has been perceived in (from the agent's perception log). Kept as the log grows, read
        on from where it was last read (first rescanned whole on every planner step: in a chess world a third of the
        run's time; the answer is the same)."""
        cache = self.agent.__dict__.setdefault("_states_of", {})
        upto, out = cache.get(owner, (0, set()))
        hist, pre = self.agent.history, owner + "_"
        for facts, _ in hist[upto:]:
            for x in facts:
                if x.startswith(pre):
                    out.add(x[len(pre):])
        cache[owner] = (len(hist), out)
        return set(out)

    def expected(self, s, a):
        return self.step(s, a)[1]
