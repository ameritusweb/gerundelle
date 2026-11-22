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
from dataclasses import replace

from molecules import Mind, Params, clause, concept_of, mcts
OPEN_LOSS_MOVES = 3   # (how many of the mind's later moves an unblamed lived loss stays open for, Params.open_loss_blame; my choice)
import re as _re_counted
_COUNTED_EFFECT = _re_counted.compile(r"_(closing|widening)_\d+$")   # a counted change effect (own_prediction guard)


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
        self.dreamed = []      # Params.dreams: the imagination register, (invitation, facts, effects) from dreams; funds nothing
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
        out = frozenset(f"{d}_{g.replace(' ', '_')}" for d, g in self.world.states(tree).items() if d not in ev)
        if self.mind.p.own_doings and tree is None:   # what the mind itself just did is part of its situation (the user: "FIX IT"):
            p, t = self.mind.p, self.mind.t           # each push it made, while its trace (halving every h0 ticks) is above the floor.
            out |= {f"did_{inv[0]}" for tt, inv in self.__dict__.get("did_log", ())   # First the situation was the world's states
                    if 0.5 ** ((t - tt) / p.h0) >= p.floor}                          # alone, and a word that opened a wall once and
        return out                                                                    # failed after looked the same both times

    def perceive(self):
        """The facts register, the news (what changed in the last slice), and the potential forces."""
        mind, world = self.mind, self.world
        mind.facts = {d: clause(f"{d}_{g.replace(' ', '_')}") for d, g in world.states().items()}
        mind.territory.facts = self.facts_now()
        news = [clause(effect_id(e)) for e in world.diffs]
        for e in world.diffs:   # who a change is about (for analogy's owners)
            mind.understanding.owners[effect_id(e)] = e.split(": ", 1)[0]
        invs = {inv_id(i): i for i in world.invitations()}
        if mind.p.affords_chain:   # what enables a push, per way in: what has held every time it was on offer that way (its potential
            und_ = mind.understanding   # force there). A way in is what the push's force reaches, but its target, as it stands (a walk: the
            now_ = self.facts_now()     # position underfoot). Kept in the SOV as lived enables; one no longer held on any way is retracted.
            ways = self.__dict__.setdefault("offered_ways", {})   # (First what held at every offer, all ways together: the walk onto a
            for c_, inv_ in invs.items():                          # position is offered from each neighbour, and only what never
                objs = set(world.reaches(inv_)) - {inv_[1]} if hasattr(world, "reaches") else set()   # changes was kept)
                key = frozenset(f for f in now_ if self.owner_of(f) in objs)
                by = ways.setdefault(c_, {})
                before = set().union(*(w_[0] for w_ in by.values())) if by else set()
                held, n = by.get(key, (now_, 0))
                by[key] = (held & now_, n + 1)
                after = set().union(*(w_[0] for w_ in by.values()))
                rel_ = "affords" if mind.p.affords_relation else "enables"   # (Params.affords_relation: its own relation, not Abstract's)
                for f in before - after:
                    und_.rel.get(f, {}).pop((rel_, c_), None)
                    und_.changed(f)
                for f in after - before:
                    und_.add(f, rel_, c_, "seen", 1.0)
        if mind.p.commit:   # committing to a prediction that stands (Params.commit; the user, 2026-11-12)
            for inv_ in self.commit_offers(bool(invs)):
                invs[inv_id(inv_)] = inv_
                if mind.p.commit_told:   # told what it commits to, as it is offered (Params.commit_told; the user, 2026-11-13, "Keep, told
                    pot_ = f"potential:{inv_[1][len('potential_'):]}"   # on offer"): so an anti-want weighs against a commit on a loss from
                    e_ = mind.understanding.rel.get(inv_id(inv_), {}).get(("causes", pot_))   # its first offer (first a commit carried
                    if e_ is None or e_[0] + e_[1] <= 0:                                      # no link until made, and in go the mind
                        mind.understanding.add(inv_id(inv_), "causes", pot_, "told", 1.0)    # committed to 5 of its 19 fills in one
                        mind.understanding.add(pot_, "caused_by", inv_id(inv_), "told", 1.0)   # endgame)
        if mind.p.tool_use and getattr(self, "tool", None) is not None and not self.__dict__.get("asking"):
            # (Params.tool_use; the user, 2026-11-13) a question standing in the pool about a concept the agent's tool can answer:
            # asking the tool is on offer, a push of the mind's own on that concept's region, competing as any push does
            asked_ = self.__dict__.get("asked_here", set()) if mind.p.ask_once_here else set()
            here_ = self.facts_now() if mind.p.ask_once_here else None
            for q_, (c_, r_) in list(mind.understanding.questions.items()):
                if mind.p.ask_once_here and (c_, here_) in asked_:   # (Params.ask_once_here) asked and answered in this very situation:
                    continue                                         # asking again here tells nothing new
                if q_ in mind.pool and self.tool.can_answer(c_):
                    inv_ = ("ask", self.owner_of(c_), c_)
                    invs[inv_id(inv_)] = inv_
        und = mind.understanding
        for c, inv in invs.items():   # the agent is what would apply a potential force (its caused_by,
            und.owners[c] = inv[1]     # seen as offered). Whether it matters is what an ownership slot
                                       # serves (REORG.md step 3; first every invitation mattered)
            if und.funding(c, "caused_by") < 1.0:
                und.add(c, "caused_by", AGENT, "seen", 1.0)
            if mind.p.reach_relations and inv[0] not in ("commit", "ask") and hasattr(world, "reaches"):   # what its force reaches, as it is
                for x in world.reaches(inv):                                                  # offered (Params.reach_relations: once
                    if ("reaches", x) not in und.rel.get(c, {}):                              # each, seen: the world shows the force)
                        und.add(c, "reaches", x, "seen", 1.0)
        sides = list(world.forces()) if (mind.p.side_forces or mind.p.unknown_slots) and hasattr(world, "forces") else []
        if mind.p.side_forces:   # each side of a location in view is a force on its neighbour (Params.side_forces), written once, seen
            for a_, b_ in sides:
                if ("forces", b_) not in und.rel.get(a_, {}):
                    und.add(a_, "forces", b_, "seen", 1.0)
        mind.inquiry.actions = set(invs)
        mind.inquiry.leaves = self.left   # what each push was seen to leave (the agent's own record)
        mind.inquiry.still = getattr(world, "still", False)   # a world that moves only when the agent acts
        regions = {}   # the territory register: each object perceived with the pushes on it
        skip0 = tuple(getattr(world, "unclaimable", None) or ())
        for c, inv in invs.items():
            regions.setdefault(inv[1], set()).add(c)
            if mind.p.reach_claims and inv[0] not in ("commit", "ask") and hasattr(world, "reaches"):   # a push is a claim on what its force reaches
                for x in world.reaches(inv):                                               # (Params.reach_claims), the claimable part
                    if not (skip0 and x.startswith(skip0)):
                        regions.setdefault(x, set()).add(c)
        mind.territory.perceived(regions)
        if getattr(world, "read_held", None):   # regions held by reading only, never by claims (Territory.update; the user, 2026-11-13)
            mind.territory.read_held = tuple(world.read_held)
        skip = getattr(world, "unclaimable", None)   # objects the world says are no one's to claim (tetris: its cells, the open space, and the
        if skip:                                     # blocks that fill them; the user, 2026-11-11, "FIX THIS CRAZINESS": first every cell a push
            skip = tuple(skip)                       # moved the piece into was claimed, the tower was the mind's territory, its wants were
            terr_ = mind.territory                   # cells near the top, and it stacked)
            terr_.unclaimable = skip
            for r_ in [r_ for r_, row_ in terr_.rows.items() if r_.startswith(skip) and not row_.get("tracked")]:
                del terr_.rows[r_]
                terr_.given.discard(r_)
            gone_ = lambda g: any(self.owner_of(x).startswith(skip) for x in (g[4:].split("&") if g.startswith("all:") else [g]))
            if self.goal is not None and not self.stack and gone_(self.goal):   # a root want about one of them is no want of territory
                self.goal = None   # (a sub-want about one is a step on a way, a means: kept; first dropped too, and set again every slice)
        present = set(world.states())
        if mind.p.dormancy:   # a stored region perceived again is woken (Params.dormancy)
            for o in present & set(mind.territory.__dict__.get("dormant", ())):
                mind.territory.row(o)
        flipped = []
        for r, row in mind.territory.rows.items():   # what is no longer there is gone (and back when it is)
            if row.get("ever") and not row.get("tracked"):   # (a region the agent tracks itself, a held prediction, isn't the world's to show)
                gone = r not in present and r in self.seen_objs and r not in getattr(world, "kept", ())   # (a world can say an
                # object out of view isn't gone, as it says who took a piece: the maze's positions; first a position left behind read as lost)
                if gone != bool(row.get("gone")):
                    row["gone"] = gone
                    flipped.append(r)
        self.seen_objs |= present
        if flipped:   # only the rows whose presence changed are read again
            mind.territory.update(flipped)
        if mind.p.unknown_slots:
            self.unknowns(sides, present)
        if mind.p.force_walks:
            self.remember_sides()
        if mind.p.plan_discovery:
            self.count_turns()
        self.known.update(invs)
        self.history.append((self.facts_now(), frozenset(effect_id(e) for e in world.diffs)))
        if mind.p.held_wants_only:   # a want not pursued now leaves the pool (only wants this agent set): the wants above the goal stay
            held = {self.goal} - {None}   # on the stack, served through it (Params.stack_supports), not competing (first the stack's wants
                                          # stayed too, four of them held the top level at a corner, and no push reached it; seed 4)
            wanted = self.__dict__.setdefault("wanted", set())
            wanted |= held
            for i in [i for i, x in mind.pool.items() if i in wanted and i not in held and "goal" in x.tags]:
                del mind.pool[i]
        wants = [clause(self.goal, tags=("goal",))] if self.goal else []   # a want, held in the pool
        offers = [clause(c, tags=("invitation", inv[1])) for c, inv in invs.items()]
        if mind.p.want_site:   # the want held open on what brings it; a move tagged with what its funded relations say it causes
            site = f"causes:{self.goal}"
            wants = [clause(self.goal, tags=("goal",), sites=(site,))] if self.goal else []
            # wanted again while the change isn't had (the user, 2026-11-06): a new wanting, so its question is open again. Once
            # filled, the want stayed in the pool with no site: present() only raises a pooled molecule's activation, so nothing
            # needed the move that had answered it, and that move stayed in storage (rung 1g, seed 0: met 10 times in 200 slices,
            # 2 in the next 800). As the territory holds a wanted region, open until the change comes
            box = mind.boxes.get(self.goal) if self.goal else None
            if box and box.get("settled") and self.goal not in self.facts_now():   # settled before it was held: held, it isn't finished
                box["settled"] = False
            held = mind.pool.get(self.goal)
            if self.goal and held is not None and site not in held.sites and self.goal not in self.facts_now():
                mind.pool[self.goal] = replace(held, sites=held.sites + (site,))
            told = mind.p.credulity
            here = self.__dict__.get("push_leads") if mind.p.force_predictions else None
            offers = [clause(c, tags=("invitation", inv[1]) + tuple(sorted(
                {f"causes:{e}" for (r, e), f in und.rel.get(c, {}).items()
                 if r == "causes" and f[0] + f[2] + told * f[1] > 0 and not (here is not None and e.startswith("potential:"))}
                | {f"causes:{e}" for e in (here or {}).get(c, ())})))   # (a potential effect: as the forces predict it from here, not as
                      for c, inv in invs.items()]   # once told: the user, 2026-11-12; first every push carried every one it ever led to)
            if here is not None:   # and the push molecules already in the pool (split halves too) carry this slice's, not the tags they were
                for i, m in list(mind.pool.items()):   # made with (present raises a pooled molecule's activation, never its tags: first
                    if "invitation" not in m.tags:     # a push kept pulling toward clears no longer in reach)
                        continue
                    c = concept_of(i) or i.split("|")[0]
                    fresh = frozenset(x for x in m.tags if not x.startswith("causes:potential:")) | {f"causes:{e}" for e in here.get(c, ())}
                    if fresh != m.tags:
                        mind.pool[i] = replace(m, tags=fresh)
        if mind.p.own_wants:
            offers += self.own_candidates()
        if mind.p.setup_support:   # a move not on offer is open on its conditions; on offer, it isn't (Mind.support_unsetup)
            told = mind.p.credulity
            for i, mol in list(mind.pool.items()):
                if "invitation" not in mol.tags:
                    continue
                c = concept_of(i) or i
                if c in invs:
                    if mol.sites:
                        mind.pool[i] = replace(mol, sites=())
                    continue
                held = self.facts_now() if mind.p.setup_unmet else frozenset()   # (Params.setup_unmet: a condition that holds is not open)
                conds = tuple(sorted(f"causes:{t}" for (r, t), f in und.rel.get(c, {}).items()
                                     if r == "conditioned_by" and f[0] + f[2] + told * f[1] > 0 and t not in held))
                if conds != mol.sites:
                    mind.pool[i] = replace(mol, sites=conds)
        if mind.p.meta_binds:   # a push that would change something here has an open site the loop's meta molecule fills (the user)
            self.loop_sites(invs)
        if mind.p.catalyst:
            mind.catalysis_now = self.catalysis(invs)
        if mind.p.anti_wants and self.__dict__.get("anti"):   # the anti-want held, in the pool as a want is (Params.anti_wants)
            wants = wants + [clause(f"anti:{self.anti}", tags=("anti", f"region:{self.anti}"))]
        if mind.p.news_in_structure:   # news perceived into the structure, not presented as a competitor
            self.news = news
            return wants + offers, invs
        self.news = []
        return news + wants + offers, invs

    # ---- a tick ------------------------------------------------------------------------------------

    def noticing(self):
        """Params.self_noticed: the world's act is read through the mind's own perception. After each slice the changes are what the mind
        notices: each object it perceives now whose state differs from the state it last perceived it in (remembered while out of view).
        A first sighting, or an object back in view as it was, is no change. The world's own list of changes is not read."""
        world = self.world
        if world.__dict__.get("_noticed_by") is self:
            return
        act = world.act
        seen = self.__dict__.setdefault("last_seen", dict(world.states()))

        def noticed(inv=None, hold=False):
            if world.__dict__.get("dreaming"):   # a dreamed slice is not perceived: the memory of what was seen stays lived (the
                return act(inv, hold)            # firewall; first the dream's trials were written into it)
            act(inv, hold)
            now = world.states()
            out = [f"{o}: {seen[o]} -> {st}" for o, st in sorted(now.items()) if o in seen and seen[o] != st]
            seen.update(now)
            world.diffs = out
            return out
        world.act = noticed
        world.__dict__["_noticed_by"] = self

    def tick(self, force=None):
        """force: an invitation to push now (a scripted intervention, for tests)."""
        world = self.world
        if self.mind.p.self_noticed:
            self.noticing()
        if self.mind.p.improvement_territory:   # improvement is territory (Params.improvement_territory): last slice's ways read first
            self.improvement_update()
        if not self.watching and not self.queue and not self.__dict__.get("committed"):   # a scene is not set back in the middle of an
            before_renew = dict(world.states()) if self.mind.p.reset_clears_plan else None
            world.renew()                           # experiment (first: between its two steps, and the
                                                    # latch was reseated before the lid was pushed)
            self._owner_memo = None   # (a set-back can change the world's objects without moving its counter)
            if before_renew is not None and self.stack and dict(world.states()) != before_renew:   # set back: the plan was for a
                root = self.stack[0]                                                             # scene that is gone (Params.reset_clears_plan)
                self.sub_log.extend((self.mind.t, g, "cleared") for g in [self.goal, *self.stack[1:]])
                self.goal, self.stack, self.sub_since = root, [], self.mind.t
        und = self.mind.understanding   # a wanted change opens a control slot on its region, open until
        terr = self.mind.territory      # the change comes (REORG.md step 4; first the want was only a
        if self.stack and self.mind.t - self.sub_since > self.mind.p.sub_budget:   # a sub-want not met in time:
            self.drop_sub()                                                         # dropped, the parent taken up
        if self.goal is not None and self.mind.p.patience is not None and self.mind.p.patience_reach:   # temperament: slices out of
            g_ = self.goal                                                                                # reach (Params.patience_reach)
            n_ = 0 if self.within_reach(g_) else (self.__dict__.get("_out_of_reach", (None, 0))[1] + 1
                                                  if self.__dict__.get("_out_of_reach", (None, 0))[0] == g_ else 1)
            self._out_of_reach = (g_, n_)
            if n_ >= self.mind.p.patience:
                self.sub_log.append((self.mind.t, g_, "stepped_aside"))
                self._out_of_reach = (None, 0)
                if self.stack:
                    self.drop_sub()
                else:
                    self.goal = None
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
        if self.mind.p.force_predictions and hasattr(world, "potential_effects"):
            self.force_predict()   # (before perceiving: the pushes on offer carry what the forces predict from here, Params.force_predictions)
        if self.mind.p.plan_discovery and self.mind.p.commit and not hasattr(world, "potential_effects"):
            self.plan_sequences()   # (a remembered plan, offered to commit to: Params.plan_discovery)
        inputs, invs = self.perceive()
        if self.kept and not self.watching and not self.queue:
            self.keep_watch()
        self.mind.wants_above = list(self.stack)   # (Params.stack_supports) the wants the held sub-want serves
        if self.mind.p.anti_wants and self.mind.p.defense_still:   # the felt losses read before this slice's tournament, from the
            self.defense_now(invs)   # pushes on offer now (first only in anti_update, after it: each tournament pressed the last
            #                          slice's defense, read for the last position's pushes, and none in the first slice after a move)
        self.mind.plan_pull = None   # (Params.plan_as_pull) the held want's planned step, a pull in this slice's tournament
        if self.mind.p.plan_as_pull and self.goal is not None and force is None and not self.queue \
                and not self.__dict__.get("committed") and not self.watching:
            step_ = self.planned(invs)
            if step_ is not None and len(step_) == 3:
                self.mind.plan_pull = {inv_id(step_): 1.0}
                self.__dict__.setdefault("plan_pulls", []).append((self.mind.t, self.goal, inv_id(step_)))
        rec = self.mind.tick(inputs, seen=self.news)
        if self.mind.p.dream_when_stuck and callable(getattr(self, "dreamer", None)):
            self.dream_if_stuck()
        if self.mind.p.meta_territory:   # before own_subwant: a region let go offers nothing this tick (Params.meta_territory)
            self.meta_release(rec)
        if self.mind.p.own_wants:
            self.own_subwant(rec)
            self.situations_remember()
        if self.mind.p.anti_wants:
            self.anti_update(invs)
        if self.mind.p.dormancy:
            self.cleanup()
        self.last_rec = rec
        if self.__dict__.get("committed") and getattr(world, "others", None):   # another moved something while it is committed
            self.committed["other_moved"] = True                                 # (the world says who; only then can it dissolve)
        if self.__dict__.get("committed") and self.watching:   # every tick of the sequence is kept: here, watching what its push did
            self.committed["steps"].append("watching")
        if self.__dict__.get("asking"):   # (Params.tool_use) waiting for the tool's answer: the slices it takes (the user: "it just
            ask_ = self.asking            # costs time"); the mind holds still meanwhile, and the world goes on
            ask_["left"] -= 1
            if ask_["left"] > 0:
                self.idle(hold=True)
                return None, rec
            self.answer_told(ask_)
            self.asking = None
        if self.__dict__.get("committed") and not self.watching:   # committed (Params.commit): the next step of its sequence, a push
            step = self.commit_step(rec, invs)                      # or a slice watched, until the world answers the prediction
            if step == "wait":
                return None, rec
            if step is not None:
                force = step
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
        if self.mind.p.experimentation is not None and force is None:   # temperament: an experiment yields to what is at stake on the
            # board (Params.experimentation): its next step, or the first step of the one that won, against the best push on offer
            if self.queue and self.yields(self.queue[0], invs):
                self.__dict__.setdefault("experiment_yields", []).append((self.mind.t, self.running, self.queue[0]))
                self.queue, self.running = [], None
            if rec["experiments"]:
                first = (self.mind.inquiry.plans.get(rec["experiments"][0]) or (None, None, []))[2]
                if first and self.yields(first[0], invs):
                    self.__dict__.setdefault("experiment_yields", []).append((self.mind.t, rec["experiments"][0], first[0]))
                    rec["experiments"] = []
        if self.mind.p.starved_experiments_go and self.queue:   # (Params.starved_experiments_go: a step waiting past the mind's patience)
            head = (self.running, self.queue[0])
            if self.__dict__.get("_queue_head", (None, None, 0))[:2] != head:
                self._queue_head = (*head, self.mind.t)
            limit = self.mind.p.patience if self.mind.p.patience is not None else self.mind.p.sub_budget
            if self.mind.t - self._queue_head[2] > limit:
                self.__dict__.setdefault("experiment_yields", []).append((self.mind.t, self.running, f"starved:{self.queue[0]}"))
                self.queue, self.running = [], None
                self.__dict__.pop("_queue_head", None)
        if self.mind.p.experiment_spares_want and force is None:   # (Params.experiment_spares_want: a step that would undo a held
            needs = self.want_conditions_holding()                     #  condition of the want in hand yields, its experiment dropped)
            undoes = lambda c: c in invs and invs[c][1] in needs
            if needs and self.queue and undoes(self.queue[0]):
                self.__dict__.setdefault("experiment_yields", []).append((self.mind.t, self.running, self.queue[0]))
                self.queue, self.running = [], None
            if needs and rec["experiments"]:
                first = (self.mind.inquiry.plans.get(rec["experiments"][0]) or (None, None, []))[2]
                if first and undoes(first[0]):
                    self.__dict__.setdefault("experiment_yields", []).append((self.mind.t, rec["experiments"][0], first[0]))
                    rec["experiments"] = []
        if force is not None:
            choice = force
        elif self.goal is not None and not self.mind.p.plan_as_pull and (step := self.planned(invs)) is not None:
            choice = step   # a want with a way known: act on it (MCTS over the agent's own model; Params.plan_as_pull: a pull instead)
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
            if self.mind.p.decision_paths and invs:   # a wait with pushes on offer is a decision too
                self.record_decision("wait", rec, invs)
            self.idle()   # waiting is watching too
            return None, rec
        self.quiet = 0
        if choice[0] == "ask" and self.mind.p.tool_use:   # (Params.tool_use) the tool is asked; its answer comes after the slices it takes
            answer, slices = self.tool.ask(choice[2])
            self.asking = dict(inv=choice, concept=choice[2], answer=answer, left=slices - 1, made=self.mind.t, slices=slices)
            self.__dict__.setdefault("tool_log", []).append((self.mind.t, choice[2], answer, slices))
            if self.mind.p.ask_once_here:   # (Params.ask_once_here) asked here: not offered again in this same situation
                self.__dict__.setdefault("asked_here", set()).add((choice[2], self.facts_now()))
            if self.mind.p.decision_paths:
                self.record_decision(inv_id(choice), rec, invs)
            if self.asking["left"] <= 0:
                self.answer_told(self.asking)
                self.asking = None
            self.idle(hold=True)
            return choice, rec
        if choice[0] == "commit" and self.mind.p.commit:   # the commit is the mind's own act: from here its sequence is followed
            first = self.commit_to(choice, rec, invs)
            if first is None:   # a sequence that begins by watching (a prediction that already stands), or nothing to commit to
                return choice, rec
            choice = first      # the sequence's first push, made in the commit's own slice
        if self.mind.p.converge and self.goal is not None and hasattr(world, "relations_of"):
            self.meeting = world.relations_of(choice)
        if (self.mind.p.force_reach_claims or self.mind.p.affords_chain) and hasattr(world, "reaches"):   # what its force reaches, as made
            self.reach_now = set(world.reaches(choice))   # (a commit never gets here: it is no push on the world)
        self.watching = (choice, self.facts_now(), 0, {})
        self.watched_objs = set()
        self.watch(world.act(choice, hold=bool(self.running) and force is None), rec)
        if self.mind.p.decision_paths:
            self.record_decision(inv_id(choice), rec, invs)
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
        pool = invs if (p.imagined_lane or p.setup_support) else self.known   # Params.setup_support: a move not on offer supports what sets it up, it isn't acted on (the user)
        won = [c for c in lv["winners"] if c.split("|")[0] in pool]   # (a split push competes as its half)
        if not won:
            return None
        watch_ = p.patience if p.watchfulness is None else p.watchfulness   # (Params.watchfulness: the watch its own trait; None reads patience)
        wait = 0 if watch_ is None else min(watch_, getattr(self.world, "horizon", 1))
        if self.quiet < wait:
            return None
        if p.faithful_choice:   # the hands faithful to the tournament (Params.faithful_choice; the user, 2026-11-15): the
            made = {}           # bids decide among the winners — temperament spoke upstream, in the bids, once — and ties go
            for k, (i, _, _) in enumerate(self.pushed):   # to the push made least recently (a tie-break is not a judgment)
                made[i] = k
            best = min(won, key=lambda c: (-round(lv["bids"].get(c, 0.0), 9),
                                           made.get(self.known[c.split("|")[0]], -1), c))
            return self.known[best.split("|")[0]]
        last = self.pushed[-1][0][1] if self.pushed else None

        def pref(c):
            inv = self.known[c.split("|")[0]]
            n = sum(1 for i, _, _ in self.pushed if i == inv)
            familiarity = n / (n + p.kappa)
            v = max(lv["bids"].get(c, 0.0), 1e-9) * max(1.0 - familiarity, 1e-9) ** (p.curiosity - 1.0)
            return v * (p.persistence if inv[1] == last else 1.0)
        if p.tie_lru:   # ties: the push made least recently first, one never made before any (the user: "why can't ties be LRU?"); the
            made = {}   # tournament's own tie-break is the same (Mind.waited, since a win). First by name, and a walk never made sorted
            for k, (i, _, _) in enumerate(self.pushed):   # after 26 words that tied with it, and a maze mind never left its start cell
                made[i] = k
            best = min(won, key=lambda c: (-round(pref(c), 9), made.get(self.known[c.split("|")[0]], -1), c))
        else:
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

    # ---- committing to a sequence (Params.commit; the user, 2026-11-12) -------------------------------------------------
    #
    # "There would be a new action called 'commit'. It would be forced to 'watch' until the potential effect is expected. Where it
    # either does or does not occur." Then: "maybe it should instead save the sequence of actions at every tick leading up to the
    # potential effect. That way, it works for Go and tetris generally, and isn't limited to these wait and see games", and: "it
    # commits to the sequence, which gets saved in the prediction SOV."
    #
    # A prediction comes with the sequence that leads to its potential effect: the pushes the world's forces were followed after
    # (world.push_predictions: its chain), then nothing pushed until the effect is due; for a prediction that already stands, nothing
    # pushed at all. The commit is a push of the mind's own on the prediction's region, named for that sequence
    # (commit_push:potential_<relative effect>_<the pushes, or "standing">: relative, so committing to the same sequence toward the
    # same kind of effect is the same push each time). Made, the mind follows the sequence and nothing else: each of its pushes when
    # its turn comes (a watch apart, as the world followed them), every other slice watched, until the world answers the
    # prediction. What it did at every tick, and how the world answered, is saved in the prediction SOV (its "sequences").
    # Answered yes: "I committed to this and it came" is lived, at full weight (it watched the whole way), and its claim on the
    # prediction's region took.
    #
    # A commitment dissolves when the unexpected happens (the user, 2026-11-12: "you have your expectation about what your opponent
    # does, and if the opponent does something unexpected, the commitment dissolves during the time between when you commit and the
    # potential effect"): when another has moved something since the commit (the world says who: world.others) and the forces,
    # followed forward along what is left of the sequence, no longer predict the effect, and it hasn't come. Then the mind is free
    # again, the prediction is an ordinary one again (answered at its due slice), and the sequence is saved as dissolved, with no
    # receipt either way: it wasn't seen through. In a world with another player the expected reply is part of what the forces are
    # followed through, so a reply that isn't the expected one dissolves it. Where nothing else moves, nothing can (the user: "in
    # tetris, the commitment can't dissolve because there is no opponent"): the sequence is followed to the answer, and a push of
    # it the world doesn't offer when its turn comes is left out. (First it dissolved whenever the forces stopped predicting the
    # effect, in tetris too.)
    #
    # My readings, for the user to change: a commit is on offer only while the world offers a push too (something is given up by
    # committing); the mind's choice among sequences is the tournament's.

    def dream_if_stuck(self):
        """Params.dream_when_stuck (the user, 2026-11-13: "When it is stuck on something not on offer, it should go straight into the dream
        planner and pause the game"): a "stuck" that formed this tick on a question whose concept isn't on offer now (nothing the mind
        could do would answer it) sends the mind into its world's dream planner at once, about that concept (self.dreamer(self, concept),
        the domain's), in this tick, so the world waits. First such a question stood, blocked, until it went stale (warpchess/
        trace_untried_commit.py: a commit on offer 3 slices, its question formed as it went, stood 12 more)."""
        mind = self.mind
        log = mind.meta.log
        seen = self.__dict__.get("_stuck_read", 0)
        self._stuck_read = len(log)
        on_offer = set(mind.inquiry.actions) if mind.inquiry else set()
        und = mind.understanding
        for t, kind, mid in log[seen:]:
            if kind != "formed" or not str(mid).startswith("meta:stuck:"):
                continue
            q = mid[len("meta:stuck:"):]
            c = und.questions.get(q, (None, None))[0]
            if c is not None and c not in on_offer:
                trials = self.dreamer(self, c)
                self.__dict__.setdefault("dream_log", []).append((mind.t, q, c, trials))
                if trials:   # dreamed through: it satisfies the meta layer (the user, 2026-11-13: "it should still satisfy the meta layer"),
                    # though what it imagined funds nothing (the firewall): the stuck is resolved, and the question is let go as acceptance
                    # lets one go (its slot stays open in the SOV; it pulls again when its funding changes). First nothing was resolved,
                    # and the question would go stuck again three ticks later and send the mind back into the same dream
                    if mid in mind.pool:
                        mind.remove(mid)
                    mind.meta.watch.pop(mid, None)
                    mind.meta.stuck[q] = 0
                    mind.meta.log.append((mind.t, "resolved by dream", mid))
                    und.release(c, und.questions.get(q, (c, None))[1])

    def answer_told(self, ask):
        """Params.tool_use: the tool's answer, written as told (the user, 2026-11-13: "told of course"): each relation it names, at
        credulity, as self-talk is, until the world bears it out (lived receipts when the push is made and watched) or contradicts it.
        That asking brought an answer about the concept is written too, seen: the ask push's own record."""
        und = self.mind.understanding
        for x, rel, y in ask["answer"] or ():
            und.add(x, rel, y, "told", 1.0)
            if rel == "causes":
                und.add(y, "caused_by", x, "told", 1.0)
        und.add(inv_id(ask["inv"]), "causes", f"answered_{ask['concept']}", "seen", 1.0)

    def commit_offers(self, pushes_on_offer):
        """The commit pushes on offer now: one for each prediction of the mind's that stands unbroken (its sequence: nothing pushed),
        and one for each sequence of pushes the world's forces predict leads to a potential effect from here."""
        if not pushes_on_offer or self.__dict__.get("committed"):
            return []
        sovs = self.mind.understanding.__dict__.get("prediction_sovs", {})
        out = {("commit", f"potential_{sovs[ins['sov']]['effect']}", "standing")
               for ins in self.__dict__.get("predicted", {}).values() if not ins.get("broken") and not ins.get("outcome")}
        out |= {("commit", f"potential_{rel}", "+".join(chain)) for _, _, rel, _, chain in self.__dict__.get("sequence_predicted", [])}
        return sorted(out)

    def commit_to(self, inv, rec, invs):
        """The commit made. -> the sequence's first push, to be made now, or None (it begins by watching, or nothing stands to commit
        to). The prediction committed to stands from here, for the world to answer."""
        mind, und = self.mind, self.mind.understanding
        sovs = und.__dict__.get("prediction_sovs", {})
        rel, c = inv[1][len("potential_"):], inv_id(inv)
        if inv[2] == "standing":
            mine = [ins for ins in self.__dict__.get("predicted", {}).values()
                    if sovs[ins["sov"]]["effect"] == rel and not ins.get("broken") and not ins.get("outcome")]
            ins, chain = (min(mine, key=lambda i: i["due"]) if mine else None), []
        else:
            found = next(((e, n, pid, ch) for e, n, r_, pid, ch in self.__dict__.get("sequence_predicted", [])
                          if r_ == rel and "+".join(ch) == inv[2]), None)
            ins, chain = None, []
            if found is not None:
                effect, n, pid, chain = found
                ins = self.__dict__.get("predicted", {}).get((effect, mind.t + n)) or self.stand_prediction(effect, mind.t, n, rel, pid, c)
        if ins is None:   # no longer there to commit to (answered, or the forces moved on, this slice)
            self.idle()
            return None
        ins["committed"] = mind.t
        self.committed = dict(inv=inv, ins=ins, facts=self.facts_now(), since=mind.t, left=list(chain), steps=[])
        self.__dict__.setdefault("commit_log", []).append((mind.t, c, "made", ins["due"]))
        if self.mind.p.decision_paths:
            self.record_decision(c, rec, invs)
        return self.commit_step(rec, invs, first=True)

    def commit_step(self, rec, invs, first=False):
        """The next step of the sequence committed to. -> a push to make now; "wait" (the slice was watched, nothing pushed); or None,
        once the world has answered the prediction (the commitment is over and the mind is free again this slice). (first: called
        from commit_to, whose slice it is: a watched first slice is the caller's to spend.)"""
        com = self.committed
        ins = com["ins"]
        if ins.get("outcome") or self.mind.t > ins["due"] + getattr(self.world, "horizon", 1):
            self.commit_answered(rec)
            return None
        if not first and com.get("other_moved") and not ins.get("happened") and not self.commit_on_track(com):
            self.commit_dissolved()   # another did the unexpected: the commitment dissolves
            return None
        by_name = {i[0]: i for i in invs.values() if i[0] != "commit"}   # a step named by its push's name (tetris: "rotate"), or by
        by_name.update({inv_id(i): i for i in invs.values() if i[0] != "commit"})   # its whole id where pushes share a name (Go: "place")
        if self.mind.p.commit_waits_turn and com["left"] and not by_name:
            # nothing is on offer: it isn't the mind's turn (the other side to move). The next step waits for it rather than being left
            # out (Params.commit_waits_turn; the user, 2026-11-13, Warp chess step 4: a line through the other side's reply; first a
            # step not on offer was skipped, and in a turn-based world every step after the first would have been)
            com["steps"].append("waiting for its turn")
            self.idle(hold=True)
            return None if first else "wait"
        while com["left"]:
            name = com["left"].pop(0)
            if name in by_name:
                com["steps"].append(name)
                com["last_facts"] = self.facts_now()   # (the situation its push is made in: Params.commit_facts_now)
                return by_name[name]
            com["steps"].append(f"not on offer: {name}")   # the world doesn't offer it now: left out, the rest followed to the answer
        com["steps"].append("wait")
        self.idle(hold=True)
        return None if first else "wait"

    def commit_on_track(self, com):
        """Whether the forces, followed forward along what is left of the sequence, still predict the effect committed to (as
        force_predict read them this slice): with pushes left, that very run of pushes is still predicted to lead to it; with none
        left, it is predicted with nothing pushed."""
        effect = com["ins"]["effect"]
        if com["left"]:
            left = tuple(com["left"])
            return any(e == effect and tuple(chain) == left for e, _, _, _, chain in self.__dict__.get("sequence_predicted", []))
        return effect in self.__dict__.get("predicted_now", ())

    def commit_dissolved(self):
        """The unexpected happened between the commit and the potential effect: the commitment is over, the mind free again. The
        sequence as far as it went is saved in the prediction SOV as dissolved; no receipt is written (it wasn't seen through), and
        the prediction is an ordinary one again."""
        com, self.committed = self.committed, None
        ins, c = com["ins"], inv_id(com["inv"])
        ins.pop("committed", None)
        sov = self.mind.understanding.__dict__.get("prediction_sovs", {}).get(ins["sov"])
        if sov is not None:
            sov.setdefault("sequences", []).append(dict(commit=c, made=com["since"], due=ins["due"], steps=list(com["steps"]),
                                                         left=list(com["left"]), outcome="dissolved"))
        self.__dict__.setdefault("commit_log", []).append((self.mind.t, c, "dissolved", self.mind.t - com["since"]))

    def commit_answered(self, rec):
        """The world has answered the prediction committed to: the sequence, as followed tick by tick, is saved in the prediction SOV
        with its answer; if the effect came, "I committed to this and it came" is lived at full weight and the claim on the
        prediction's region took; if not, the commit did nothing here."""
        com, self.committed = self.committed, None
        ins, inv = com["ins"], com["inv"]
        mind, und = self.mind, self.mind.understanding
        c, pot = inv_id(inv), f"potential:{inv[1][len('potential_'):]}"
        came = ins.get("outcome") == "confirmed"
        sov = und.__dict__.get("prediction_sovs", {}).get(ins["sov"])
        if sov is not None:   # the sequence of actions at every tick leading up to the potential effect, in the prediction SOV (the user)
            sov.setdefault("sequences", []).append(dict(commit=c, made=com["since"], due=ins["due"], steps=list(com["steps"]),
                                                         outcome="came" if came else "did not come"))
        if came:
            und.add(c, "causes", pot, "seen", 1.0)
            und.add(pot, "caused_by", c, "seen", 1.0)
        else:
            und.add(c, "causes", "no_change", "seen", 1.0)
        und.add(c, "caused_by", AGENT, "seen", 1.0)
        names = frozenset([pot] if came else ["no_change"])
        facts_ = com.get("last_facts", com["facts"]) if mind.p.commit_facts_now else com["facts"]   # (Params.commit_facts_now: the
        # outcome is read in the situation its last push was made in, as a bare push's is; first the one the commitment was made in, which
        # can be slices old: in zodiac the meta layer sorted a split's cases 226/29 where the world, by the facts at each strike, had
        # 157/167, and conditions were split on stale facts: trace_conditions.py, 2026-11-22)
        before = self.predict(inv, facts_)   # its usual outcome in this reading, before this try (as SovAgent.watch)
        mind.territory.reach = None
        took = {inv[1]} if came and not ins.get("loss") else set()   # (a predicted loss that came gains nothing: Params.predicted_losses)
        mind.territory.claimed(c, inv[1], took, None, names)
        mind.meta.observe_mode(c, names, facts_, rec)
        if self.running and not self.queue:   # an experiment whose last step was the commit: report what it found (as watch does)
            mind.inquiry.result(self.running, before is not None and names == before)
            self.running = None
        self.tried.append((mind.t, inv, sorted(names)))
        self.pushed.append((inv, facts_, names))
        self.left[c] = frozenset()
        self.__dict__.setdefault("commit_log", []).append((mind.t, c, "came" if came else "did not come", mind.t - com["since"]))

    def idle(self, hold=False):
        """A slice with no push of the agent's in flight: what changed, something else moved (the
        territory register)."""
        diffs = self.world.act(None, hold=hold)
        self.mind.territory.moved({e.split(": ", 1)[0] for e in diffs}, [effect_id(e) for e in diffs], self.facts_now())
        return diffs

    def watch(self, diffs, rec):
        inv, facts, k, effects = self.watching
        if k == 0 and self.mind.p.improvement_territory:   # (a move made: the cost a way counts, Params.improvement_territory)
            self.__dict__["_moves_made"] = self.__dict__.get("_moves_made", 0) + 1
            ml = self.__dict__.setdefault("_moves_log", [])   # (each move with its slice: a way's chain, Params.improvement_options)
            ml.append((self.mind.t, inv_id(inv)))
            del ml[:-400]
        if k == 0 and self.mind.p.lived_loss_lessons:   # (the move a lived loss is filed against, Params.lived_loss_lessons)
            self.__dict__["_last_own_push"] = (self.mind.t, inv)
            self.__dict__["_regions_at_move"] = (inv_id(inv), self.__dict__.get("_decision_regions") or {})   # (what each move on offer was
            #   predicted to touch when this one was made: SovAgent.anti_update's "made a difference")
            com = self.__dict__.get("committed")   # and the move's reasons, as the mind held them making it (the user, 2026-11-21, "A,
            rl = self.__dict__.setdefault("reason_log", [])   # through its reasons": a lived loss is traced back through them)
            def since(g):   # when the want in hand was last set: each setting a pursuit of its own (2026-11-21)
                return next((t_ for t_, g_, k_ in reversed(self.sub_log) if g_ == g and k_ == "set"), None) if g is not None else None
            rl.append(dict(t=self.mind.t, move=inv_id(inv), commit=inv_id(com["inv"]) if com else None,
                           commit_since=com["since"] if com else None, goal=self.goal, stack=tuple(self.stack),
                           goal_since=since(self.goal), root_since=since(self.stack[0]) if self.stack else since(self.goal),
                           episode=len(getattr(self.world, "games", ()) or ())))
            del rl[:-200]
            if self.mind.p.open_loss_blame and self.__dict__.get("_open_losses"):
                self.open_loss_blame(inv_id(inv))
        if k == 0 and self.mind.p.own_doings:   # the push made now: remembered as the mind's own doing (facts_now)
            log = self.__dict__.setdefault("did_log", [])
            log.append((self.mind.t, inv))
            del log[:-64]
        others = getattr(self.world, "others", None) or set()   # what the world says another changed in this slice
        theirs = []
        for e in diffs:
            if self.mind.p.others_not_caused and e.split(": ", 1)[0] in others:   # (Params.others_not_caused: another's doing is not
                theirs.append(e)                                                 # what the push caused; first every change in the
                continue                                                         # watch was, and in zodiac 9 of the 25 most-funded
                # relations were false, "my strike causes me struck", 0 of 469 truly: trace_relations.py, 2026-11-22)
            effects.setdefault(effect_id(e), k)   # (what followed the push, whoever made it: the watch spans the answer)
            o = e.split(": ", 1)[0]
            if o in others:   # another's doing: something else moved it, not the mind's claim (first claimed as the mind's own,
                theirs.append(e)   # and a duel mind held the other side's pieces as "mine"; warpchess test_wants_arise_from_slots)
            elif o not in (getattr(self.world, "seen_only", None) or ()):   # (what only came into or left view: perception, not a
                self.watched_objs.add(o)   # change the push made to it; first a maze turn claimed the positions it brought into view)
        if theirs:
            self.mind.territory.moved({e.split(": ", 1)[0] for e in theirs}, [effect_id(e) for e in theirs], self.facts_now())
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
        if mind.p.acted_on_conditions:   # it acted on each object it changed as that object stood: those states condition it
            acted = und.__dict__.setdefault("acted_on", set())
            for e in effects:
                o = und.owners.get(e) or self.owner_of(e)
                for f in facts:
                    if f != e and self.owner_of(f) == o:
                        und.add(c, "conditioned_by", f, "seen", 1.0)
                        und.add(f, "conditions", c, "seen", 1.0)
                        acted.update({(c, f), (f, c)})
        before = self.predict(inv, facts)   # its usual outcome in this reading, before this try
        if before is not None:   # changes it did not act on and did not predict: something else's (S6-W01)
            owners = mind.understanding.owners
            for e in effects:
                r = owners.get(e) or e.rsplit("_", 1)[0]
                if r != inv[1] and e not in before:
                    mind.territory.unexplained(r, e, facts)
        mind.territory.reach = self.__dict__.get("reach_now") if mind.p.force_reach_claims else None
        mind.territory.claimed(c, inv[1], self.watched_objs, before, names)   # perceived: whatever changed
                                                                               # was mine, if as predicted
        mind.meta.observe_mode(c, frozenset(names), facts, rec)
        self.tried.append((mind.t, inv, names))
        self.pushed.append((inv, facts, frozenset(names)))
        if mind.p.undo_loops and len(self.pushed) >= 2:   # Params.undo_loops: a loop of SUCCESSES is perceived (the
            # self-awareness layer; balance rung 2, 2026-11-16: attach, detach, attach — 23 same-spring toggle pairs in 50
            # choices, each one working, and meta's looping detector, gated on `blocked`, saw none of it. An undoing: this
            # push's effects restore exactly the facts the last push changed. Three undoings of one pair are a loop, told
            # to the meta layer as any frustrated loop is; what the mind does about a loop it can now see is its own)
            (i1, f1, m1), (i2, f2, m2) = self.pushed[-2], self.pushed[-1]
            own = lambda es: {self.owner_of(e) for e in es if e != "no_change"}
            if m2 != {"no_change"} and own(m1) == own(m2) and all(
                    any(e in f1 for e in m2 if self.owner_of(e) == o) for o in own(m2)):
                pairs = self.__dict__.setdefault("undo_pairs", {})
                key = frozenset((inv_id(i1), inv_id(i2)))
                pairs[key] = pairs.get(key, 0) + 1
                if pairs[key] >= 3:
                    for cid in key:
                        mind.meta.emit("looping", cid, rec)
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
        if self.goal is not None and (self.goal in names or (self.goal.startswith("all:") and self.held(self.goal, after))):
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
                if mind.p.lived_chain:
                    self.lived_chain(self.goal)
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
                    und.changed(c)
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
        if self.mind.p.force_walks:   # imagined as far ahead as the view reaches (Params.force_walks; the user, 2026-11-19: the view
            horizon = 2 * getattr(self.world, "view_reach", horizon)   # "constrains the steps to look ahead"; then "B": anywhere in view,
            # so as many walks as the farthest location in view takes round its corners; Model.in_view bounds where)
        if not model.actions(s):
            return None
        if self.mind.p.imagined_tournament:   # a train of thought, not a search: each winner's line (imagined_lines)
            roots = self.top_moves(model.actions(s))
            if self.mind.p.force_walks and model.body_at(s) is not None:   # walking (the user, 2026-11-19, "A"): every walk on offer is
                # imagined, not only the winners, and the best line is pulled for ("imagine options, choose the best"). First only the
                # winners: any walk could still reach the want within the view, so whichever won was pulled for, detour or not, and the
                # pull made it win again (trace_roots.py: west worth 4, east 3, east the only root, east walked; a circle beside Leo)
                roots = roots + [c for c in model.actions(s) if c.startswith("walk_") and c not in roots]
            a, v = imagined_lines(model, s, roots, horizon)
            if self.mind.p.plan_discovery:
                self.discovered(model)
            return invs.get(a) if v > 0 else None
        top = set(self.mind.top(self.last_rec)) if self.last_rec else set()
        prior = {a: 3.0 for a in model.actions(s) if a in top}
        a, v = mcts(model, s, prior, budget=budget, horizon=horizon, value=True)
        return invs.get(a) if v > 0 else None

    def top_moves(self, offered):
        """Params.imagined_tournament: the moves on offer that won the top level of this slice's tournament, in the order
        of their bids (a split move wins as its half, and is the move it is a half of)."""
        if not self.last_rec:
            return []
        lv = self.mind.top(self.last_rec)
        bids = self.last_rec["levels"][-1]["bids"]
        out = []
        for w in sorted(lv, key=lambda i: (-round(bids.get(i, 0.0), 9), i)):
            c = concept_of(w) or w
            if c in offered and c not in out:
                out.append(c)
        return out

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
        if self.stack and self.mind.p.sub_yield and self.held(self.goal, self.facts_now()):
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

    def catalysis(self, invs):
        """Params.catalyst (the user, 2026-11-07): the questions a push leads to, read off the SOV: its own open slots, and the open slots of
        what the register says it causes (lived or worked out, told at credulity). A push that causes nothing leads to none; as what it causes is understood, its
        slots fill and the pull fades. (First I kept lists of my own, views seen here and a body's move renewing them: the SOV holds this.)
        Returns push -> count."""
        und, told = self.mind.understanding, self.mind.p.credulity
        return {c: len(und.open_slots(c)) + sum(len(und.open_slots(e)) for (r, e), f in und.rel.get(c, {}).items()
                                                if r == "causes" and e != "no_change" and f[0] + f[2] + told * f[1] > 0)
                for c in invs}   # its own open slots too (the user: no experiment needed: a push with "what conditions it?" open stays
                                 # worth doing, and done after a turn, the combination is lived; first only what it causes counted, and
                                 # one walk into the edge, causing nothing, left the walk at 0 for good)

    def loop_sites(self, invs):
        """Params.meta_binds: while a looping or stuck meta molecule stands on the held want, each push on offer whose reading here
        predicts a change, or that is untried here, has the open site loop:<want> (the meta molecule carries that tag); one predicted
        to do nothing here has none. The site is set on the pooled molecules (a split push as its halves), and taken off when the
        meta molecule is gone."""
        mind = self.mind
        site = f"loop:{self.goal}" if self.goal else None
        on = site is not None and any(f"meta:{k}:{self.goal}" in mind.pool for k in ("looping", "stuck"))
        facts = self.facts_now()
        if not on or self.__dict__.get("loop_want") != self.goal:   # this loop: since the meta molecule on the held want stood
            self.loop_since, self.loop_want = (mind.t if on else None), (self.goal if on else None)
        in_loop = {inv_id(i) for t, i, _ in self.tried if self.__dict__.get("loop_since") is not None and t >= self.loop_since}
        for i, mol in list(mind.pool.items()):
            if "invitation" not in mol.tags:
                continue
            c = i.split("|")[0]
            keep = tuple(s for s in mol.sites if not s.startswith("loop:"))
            want = keep
            looping = mind.p.loop_spares_looping and c in in_loop   # (made in this loop; first any looping mark on the push, from any
                                                                    # loop anywhere, and at a corner the two presses out were held down)
            if on and c in invs and not looping:   # (Params.loop_spares_looping: a push the loop includes is not lifted by it)
                pred = self.predict(invs[c], facts)
                if pred is None or set(pred) != {"no_change"}:
                    want = keep + (site,)
            if want != mol.sites:
                mind.pool[i] = replace(mol, sites=want)

    def meta_release(self, rec):
        """Params.meta_territory: territory dynamic by meta-cognition (the user, 2026-11-15). A held want whose meta molecule, looping or
        stuck, won the top level, on a region held by nobody, lets the region go (Territory.released) and drops the want; a region let
        go comes back when this slice's news names it (perceived changing) or when a sub-want or a way is set on it (a way needs it)."""
        terr, mind = self.mind.territory, self.mind
        released = terr.__dict__.setdefault("released", {})
        admitted = terr.__dict__.setdefault("admitted", set())   # nothing is territory at first (the user, 2026-11-15)
        log = self.__dict__.setdefault("released_log", [])
        if released:   # coming back: perceived changing, or wanted again by a way (sub-wants set since the last reading)
            changed = {d.split(":", 1)[0] for d in (self.world.diffs or [])}
            seen = self.__dict__.get("_release_sub_read", 0)
            named = {self.owner_of(g) for _, g, k in self.sub_log[seen:] if k == "set" and isinstance(g, str)}
            self._release_sub_read = len(self.sub_log)
            for r in [r for r in released if r in changed or r in named]:
                del released[r]
                terr.__dict__.pop("_memo", None)
                log.append((mind.t, r, "back", "changed" if r in changed else "needed"))
        lv = rec["levels"][-1] if rec.get("levels") else {"winners": []}
        for i in lv["winners"]:   # admitted: meta:relevant about one of a region's concepts won the top level
            if i.startswith("meta:relevant:"):
                c = i[len("meta:relevant:"):]
                base = concept_of(c) or c.split("|")[0]
                inv = self.known.get(base)   # a push: the object it acts on (first its own name, never a region: the voice wasn't admitted)
                r = inv[1] if inv is not None else self.owner_of(base)
                if r and r not in admitted:
                    admitted.add(r)
                    released.pop(r, None)
                    terr.__dict__.pop("_memo", None)
                    log.append((mind.t, r, "admitted", c[:60]))
        held = [self.goal, *self.stack]
        for i in lv["winners"]:
            if not i.startswith(("meta:looping:", "meta:stuck:")):
                continue
            x = i.split(":", 2)[2]
            recon = self.__dict__.setdefault("meta_recon", {})   # (Params.reconsider: wins of looping/stuck per held want, toward
            dropped_under = self.__dict__.setdefault("meta_dropped", {})   # bringing back what was set aside under it)
            if x in held:
                recon[x] = recon.get(x, 0) + 1
                if recon[x] >= mind.p.reconsider:
                    back = [d for d, served in dropped_under.items() if served == x]
                    for d in back:
                        self.failed_subs.discard(d)
                        del dropped_under[d]
                        log.append((mind.t, d, "reconsidered", x[:60]))
                    recon[x] = 0
            wins = self.__dict__.setdefault("meta_wins", {})   # (Params.tenacity: wins of looping/stuck per want while it is held)
            for k in [k for k in wins if k not in held]:
                del wins[k]
            root = self.stack[0] if self.stack else self.goal   # the root want, the one every sub-want serves: never dropped (first
            if x not in held or x == root:                       # the cheese was let go at slice 4; then held[-1] was taken for the root,
                continue                                         # the last parent, and the cheese was dropped on every maze, mysterymaze_v2)
            # the want is dropped, whoever holds its region (the user, 2026-11-15, "DUH": meta-cognition caught the loop, so the
            # pursuit ends; first only wants on regions nobody holds, and a want on a held position out of view, meta:looping on it
            # winning the top 22 times, was held 80 slices, mysterymaze_v2/trace_voice.py)
            wins[x] = wins.get(x, 0) + 1
            if wins[x] < mind.p.tenacity:   # not yet sustained enough for this temperament (Params.tenacity)
                continue
            del wins[x]
            r = self.owner_of(x) if not x.startswith("all:") else None
            row = terr.rows.get(r) if r else None
            if (row is not None and r not in released and r not in terr.given and not row.get("tracked")
                    and row.get("holder") in ("unknown", "nobody", "another")):
                released[r] = (mind.t, x)   # and its region, held by nobody, let go from territory
                admitted.discard(r)
                terr.__dict__.pop("_memo", None)
                terr.wants.pop(r, None)
                for pid in [p for p in mind.pool if p.startswith("own:") and p.endswith(":" + r)]:
                    del mind.pool[pid]
                log.append((mind.t, r, "released", i.split(":")[1]))
            mind.pool.pop(f"subwant:{x}", None)
            served = self.stack[-1] if self.goal == x else (held[held.index(x) - 1] if held.index(x) > 1 else self.goal)
            self.__dict__.setdefault("meta_dropped", {})[x] = served   # the want it served: its looping brings this back (Params.reconsider)
            if self.goal == x and self.stack:
                self.drop_sub()
            elif x in self.stack:
                self.stack.remove(x)
                self.failed_subs.add(x)
                self.sub_log.append((mind.t, x, "dropped"))
            log.append((mind.t, x, "dropped", i.split(":")[1]))
            return

    def drop_sub(self):
        """A sub-want not met: set aside for good, and the want it served taken up again."""
        self.failed_subs.add(self.goal)
        self.sub_log.append((self.mind.t, self.goal, "dropped"))
        self.goal, self.sub_since = self.stack.pop(), self.mind.t

    # ---- wants from ownership slots (Params.own_wants; REORG.md step 4, carried from own_agent.py) ------------------------

    def lived_chain(self, want):
        """Params.lived_chain: the want just had, walked back through the pushes since it was last had. Each state a push on the way
        needed co-occurs with the facts of the situation the push that brought it was made in (a lived receipt)."""
        start = self.__dict__.get("_chain_from", 0)
        run = self.pushed[start:]
        self._chain_from = len(self.pushed)
        und = self.mind.understanding
        todo, seen, end = [(want, len(run))], {want}, len(run)
        while todo:
            f, before = todo.pop()
            k = next((i for i in range(before - 1, -1, -1) if f in run[i][2]), None)   # the last push before that brought f
            if k is None:
                continue
            inv, facts, _ = run[k]
            if f != want:
                for g in facts:
                    if g != f:
                        und.add(f, "co_occurs", g, "seen")
            for n in self.needs(inv, f):
                if n not in seen:
                    seen.add(n)
                    todo.append((n, k))
        self.__dict__.setdefault("chains", []).append((self.mind.t, sorted(seen - {want})))

    def force_predict(self):
        """Params.force_predictions (the user, 2026-11-10). Each potential effect the world's force structure predicts with certainty
        (world.potential_effects: the effect as the world will show it, in how many slices, the forces "a has a force on b" read relative
        to the pushed thing, and the effect relative to it) is a prediction SOV: its relations are those forces, relative, so the same
        structure anywhere is the same SOV (the user: "absolute is plain wrong"), prediction:<relative effect>:<the structure's mark>
        (Understanding.prediction_sovs); it entails the potential effect, potential:<relative effect>, told (the prediction is self-talk:
        the user), as is the link from the push before it. Each time it comes up is an instance, linked to the push the mind made just before (within the world's watch) or to none
        ("wait"). When its slices are up the world answers the instance: the effect holds, confirmed (the told receipts stand; nothing is
        lived, since the effect came slices after the push), or it doesn't, rejected (the told link from the push before it is taken back,
        not closed for good, the mind its own teller; only the push that broke it, the one after which the forces stopped predicting it,
        is told to prevent the potential effect, and only then is the owned prediction lost). An effect that comes sooner than due (a
        drop) is confirmed when it comes."""
        import hashlib
        mind, und, world = self.mind, self.mind.understanding, self.world
        role_of = getattr(world, "role_of", None)   # the world says each node's role kind and whether it is on the effect's side (first
        if not und.__dict__.get("_role_kinds"):    # tetris's role names were written here, in the mind; the go world's weren't known)
            plain = und.kind                       # a prediction SOV's node is matched by its role, as a push is matched as an act
            def kind(c, plain=plain):
                if "#" not in c:
                    return plain(c)
                r = c.split("#", 1)[1]
                return role_of(r)[0] if role_of else r
            und.kind, und._role_kinds = kind, True
        if role_of and not und.__dict__.get("_effect_nodes_built"):   # each node on its effect's side marked, for Abstract's anchor
            marks = und.__dict__.setdefault("effect_nodes", set())    # (rebuilt for prediction SOVs a checkpoint saved before the marks)
            for c in list(und.rel):
                for x in [c] + [o for (r_, o) in und.rel[c] if r_ == "forces"]:
                    if x.startswith("prediction:") and "#" in x and role_of(x.split("#", 1)[1])[1]:
                        marks.add(x)
            und._effect_nodes_built = True
        t, facts = mind.t, self.facts_now()
        sovs = und.__dict__.setdefault("prediction_sovs", {})
        open_ = self.__dict__.setdefault("predicted", {})   # (effect as the world shows it, slice due) -> the instance
        did = self.__dict__.get("did_log", [])
        log = self.__dict__.setdefault("prediction_log", [])
        h = getattr(world, "horizon", 1)
        now_items = list(world.potential_effects())   # what the forces predict now
        predicted_now = {item[0] for item in now_items}
        self.predicted_now = predicted_now   # (read by a commitment: is what it committed to still predicted? Params.commit)
        for key, ins in open_.items():   # each slice: did its effect come (perhaps sooner, a drop), or did the forces stop predicting it?
            if ins["effect"] in facts:
                ins["happened"] = True
            elif ins["effect"] not in predicted_now and not ins.get("broken") and not ins.get("committed"):   # (one committed to
                # is answered when it is due: the pushes of its own sequence are on the way to it, not breaking it; Params.commit)
                # the forces no longer predict it: the push that changed them broke it, the mind's latest since the prediction, within the
                # world's watch (the user, 2026-11-11: "blame only the push that broke it"; first every push made in between was told to
                # prevent it, every push came to, and a lost prediction's anti-want pushed down every push, the clearing one too)
                ins["broken"] = True
                ins["broken_by"] = next((inv for tt, inv in reversed(did) if tt >= ins["made"] and tt >= t - h), None)
        for key, ins in list(open_.items()):   # the world answers
            if t < ins["due"] and not ins.get("happened"):
                continue
            del open_[key]
            pot = f"potential:{sovs[ins['sov']]['effect']}"
            if ins.get("happened") or ins["effect"] in facts:   # confirmed (also when it came sooner): the told receipts stand; nothing is lived (the user: the time lapse makes a lived
                ins["outcome"] = "confirmed"   # confirmation impossible; first written as lived). What the mind owned came true: kept
            else:   # rejected: the told receipt is taken back, the mind its own teller (belied); not closed for good: the next prediction
                ins["outcome"] = "rejected"   # can tell it again (the user: "it doesn't have to close it for good"; a told way the world
                e = und.rel.get(ins["by"], {}).get(("causes", pot))   # contradicts is refuted and never written again, SovAgent.watch)
                if e is not None and e[1] > 0:
                    e[1] = 0.0
                    und.changed(ins["by"])
                    und.belied.append((t, "self", ins["by"]))
                inv = ins.get("broken_by")   # only the push that broke it (told: the same time lapse)
                if inv is not None and not ins.get("loss"):   # (a predicted loss that didn't come was kept from coming: no blame, nothing
                    # owned was lost; Params.predicted_losses)
                    und.add(inv_id(inv), "prevents", pot, "told", 1.0)   # (one way, as polar() writes it)
                    tree = self.mind.__dict__.get("decision_tree")   # the decision went wrong: its path is marked failed
                    for td, dec, nodes in reversed((tree or {}).get("records", [])):   # (Params.meta_targets)
                        if dec == inv_id(inv) and td >= ins["made"]:
                            for node in nodes:
                                tree["failed"][node] = tree["failed"].get(node, 0) + 1
                            break
                    # it intervened and lost what it owned (the user: "if you lose the prediction by intervening, you've lost what you own")
                    self.own_prediction(pot, held=False)
            log.append((t, ins["sov"], ins["outcome"], ins["by"]))
            self.__dict__.setdefault("prediction_answers", []).append((t, ins["effect"], ins["outcome"], ins["by"]))   # (as the world showed it)
        last = next((inv for tt, inv in reversed(did) if tt >= t - h), None)
        by = inv_id(last) if last is not None else "wait"
        def sov_of(rel, forces):   # the prediction SOV of a relative force structure (one per structure)
            mark = hashlib.md5(repr(sorted(forces)).encode()).hexdigest()[:8]
            pid = f"prediction:{rel}:{mark}"
            if pid not in sovs:
                sovs[pid] = dict(effect=rel, forces=frozenset(forces), instances=[])
                und.add(pid, "causes", f"potential:{rel}", "told", 1.0)   # told: the prediction is self-talk (the user, 2026-11-10),
                und.add(f"potential:{rel}", "caused_by", pid, "told", 1.0)   # funding at credulity until the world answers
            return pid

        stand = self.stand_prediction   # an instance the world will answer (a method: a commit stands one too, Params.commit)

        made_push = next((inv for tt, inv in reversed(did) if tt == t - 1), None)   # what was predicted for the push it just made stands now
        for effect, n, rel, pid, c in self.__dict__.get("push_predicted", []):   # (Params.force_predictions; the user, 2026-11-12)
            if made_push is not None and inv_id(made_push) == c and (effect, t - 1 + n) not in open_:
                stand(effect, t - 1, n, rel, pid, c)
        for item in now_items:   # what the forces predict now
            effect, n, forces = item[:3]
            rel = item[3] if len(item) > 3 else effect
            if (effect, t + n) in open_:
                continue
            pid = sov_of(rel, forces)
            und.add(by, "causes", f"potential:{rel}", "told", 1.0)   # the push before it, told to itself until the world answers
            und.add(f"potential:{rel}", "caused_by", by, "told", 1.0)
            stand(effect, t, n, rel, pid, by)
        # what the forces predict after each push on offer, and after each sequence of pushes that reaches a place the piece would clear
        # from (the user, 2026-11-12: "you use a force to rotate it, you then predict the new force configuration ... follow the forces down
        # ... potential effect"; first only the piece falling with no push was predicted, and nothing told a piece in one column that a
        # clear lay three shifts away). The first push of each is told it causes the potential effect; a one-push prediction stands, for
        # the world to answer, if the mind makes that push; a longer one is predicted again from wherever the piece is next slice
        push_predicted = []
        sequences = []
        situational = {}   # push on offer -> the potential effects the forces predict it leads to from here (Params.force_predictions)
        offered = world.invitations() if hasattr(world, "invitations") else []
        by_name = {inv[0]: inv for inv in offered}
        by_name.update({inv_id(inv): inv for inv in offered})   # (as commit_step: a sequence's push named by its whole id where
        # pushes share a name, Go's "place")
        tool_items = (list(self.tool.predictions()) if mind.p.tool_use and hasattr(getattr(self, "tool", None), "predictions") else [])
        for item in list(world.push_predictions() if hasattr(world, "push_predictions") else ()) + tool_items:   # (and the tool's answers
            # standing as predictions, Params.tool_use: the user, 2026-11-13, "Stoppability as the tool's prediction")
            effect, n, forces, rel, chain = item
            first = by_name.get(chain[0])
            if first is None:
                continue
            c = inv_id(first)
            pid = sov_of(rel, forces)
            e = und.rel.get(c, {}).get(("causes", f"potential:{rel}"))
            if e is None or e[1] <= 0:   # told once (not again every slice it is predicted)
                und.add(c, "causes", f"potential:{rel}", "told", 1.0)
                und.add(f"potential:{rel}", "caused_by", c, "told", 1.0)
            situational.setdefault(c, set()).add(f"potential:{rel}")
            if len(chain) == 1:
                push_predicted.append((effect, n, rel, pid, c))
            sequences.append((effect, n, rel, pid, tuple(chain)))
        if mind.p.situational_told:   # a push's told link from a push prediction holds only while the forces predict it now (Params.
            told_by = und.__dict__.setdefault("situational_told", {})   # situational_told; the user, 2026-11-13): offered again with no such
            for c, pots in situational.items():                        # prediction, the told receipt is taken back (as a rejected
                told_by.setdefault(c, set()).update(pots)              # prediction's is), and told again when predicted again. First told
            for inv in offered:                                        # once and kept: in go a held want's plan made 8 of 19 fills on
                c = inv_id(inv)                                        # "this placement causes a kill one step away", told in a board
                for pot in told_by.get(c, set()) - situational.get(c, set()):   # long gone
                    for x, rr, y in ((c, "causes", pot), (pot, "caused_by", c)):
                        e = und.rel.get(x, {}).get((rr, y))
                        if e is not None:
                            e[1] = 0.0
                            und.changed(x)
                    told_by[c].discard(pot)
        self.push_predicted = push_predicted
        self.push_leads = situational   # (its own name: first `situational`, which warpchess's piece minds use for a flag of their own)
        self.sequence_predicted = sequences   # each sequence of pushes the forces predict leads to an effect from here (Params.commit)

    def stand_prediction(self, effect, n0, n, rel, pid, by_):
        """An instance of a prediction SOV that the world will answer (force_predict's, a method so a commit can stand the prediction it
        commits to): its forces written where Abstract can see them, the instance kept open until its due slice, the potential effect
        owned while it stands, and a want for it met. -> the instance."""
        mind, und = self.mind, self.mind.understanding
        sovs = und.__dict__.setdefault("prediction_sovs", {})
        open_ = self.__dict__.setdefault("predicted", {})
        role_of = getattr(self.world, "role_of", None)
        for a, b in sovs[pid]["forces"]:
            und.add(f"{pid}#{a}", "forces", f"{pid}#{b}", "seen", 1.0)
            for x in (a, b):
                if role_of and role_of(x)[1]:
                    und.__dict__.setdefault("effect_nodes", set()).add(f"{pid}#{x}")
        # a predicted loss (Params.predicted_losses; the user, 2026-11-12, "Yes, as a loss"): the effect is on a region the register holds
        # now, so it is the region leaving the state it is held in. Its prediction SOV keeps its instances and answers as any, but it is
        # never owned and never meets a want (first every prediction was owned: a gain in ownership, as the user ruled potential effects
        # were; a loss reported through that would be owned and wanted). The register says, not the world (my reading)
        row_ = mind.territory.rows.get(self.owner_of(effect), {})
        if row_.get("holder") == "contested" and row_.get("held_states"):   # (contested: a loss only into a state it was never held in; the
            loss = bool(mind.p.predicted_losses) and effect not in row_["held_states"]   # user, 2026-11-13, "three levels": a plan
        else:                                                                             # ended or stopped is a gain, made
            loss = bool(mind.p.predicted_losses) and row_.get("holder") == "mine"          # unstoppable a loss)
        if loss and mind.p.held_losses_by_state:   # (Params.held_losses_by_state: a held region's effect is a loss only out of its held
            r_ = self.owner_of(effect)              #  states; never one the world names a gain)
            now_ = f"{r_}_{self.world.shown.get(r_)}" if self.world.shown.get(r_) is not None else None
            held_ = row_.get("held_states") or ({now_} if now_ else set())
            if effect in held_ or effect == now_ or effect.startswith(tuple(getattr(self.world, "gain_prefixes", ()))):
                loss = False
        ins = dict(sov=pid, effect=effect, made=n0, due=n0 + n, by=by_, outcome=None, loss=loss)
        sovs[pid]["instances"].append(ins)
        open_[(effect, n0 + n)] = ins
        if loss:
            sovs[pid]["loss"] = True
            und.__dict__.setdefault("loss_rels", set()).add(rel)   # (read by anti_update: a predicted loss is what a held_<doing> fears)
            return ins
        self.own_prediction(f"potential:{rel}", held=True)
        if self.goal == f"potential:{rel}":
            if self.stack:
                self.sub_log.append((mind.t, self.goal, "met"))
                self.goal = self.stack.pop()
            else:
                self.reached.append((mind.t, self.goal))
                self.sub_log.append((mind.t, self.goal, "met"))
                self.goal = None
            self.sub_since = mind.t
        return ins

    def record_decision(self, decision, rec, invs, winner=None):
        """Params.decision_paths (the user, 2026-11-11: a 'most-often-used' decision tree, meta-cognitive and observational). A decision
        traced back: the winning thought at the top level it came from (the push's molecule, or a split half of it; for a wait, the top
        level's winners), its bonds at each level (its partner, or the edge it formed, and that partner's own binding), then the SOV
        relations between the winning thought's concept and each partner's concept. Each node and each step back is counted. What gave a
        winner its support isn't recorded by the tournament, so support shows only through the bonds."""
        und = self.mind.understanding
        tree = self.mind.__dict__.setdefault("decision_tree", {"nodes": {}, "steps": {}, "decisions": 0, "failed": {}, "records": []})
        self.decision_tree = tree   # (on the mind, for the meta layer: Params.meta_targets)
        tree["decisions"] += 1
        record = (self.mind.t, decision, set())
        tree["records"].append(record)
        del tree["records"][:-500]
        levels = rec.get("levels") or []
        top = levels[-1]["winners"] if levels else []
        base = decision.split("|")[0]
        if winner is not None:
            thoughts = [winner]
        elif decision == "wait":
            thoughts = list(top)
        else:
            thoughts = [i for i in top if i.split("|")[0] == base] or [decision]
        def count(node, parent):
            record[2].add(node)
            tree["nodes"][node] = tree["nodes"].get(node, 0) + 1
            tree["steps"][(parent, node)] = tree["steps"].get((parent, node), 0) + 1
        count(("decision", decision), None)
        for w in thoughts:
            count(("thought", w), ("decision", decision))
            cw = concept_of(w) or w.split("|")[0]
            for L, lv in enumerate(levels):
                b = lv["res"].get(w)
                if not b or b[0] == "none":
                    continue
                partners = [b[1]] if b[0] == "partner" else list(b[1:])
                for q in partners:
                    count(("bond", f"L{L}:{q}"), ("thought", w))
                    b2 = lv["res"].get(q)
                    if b2 and b2[0] == "partner" and b2[1] != w:
                        count(("bond", f"L{L}:{q}>{b2[1]}"), ("bond", f"L{L}:{q}"))
                    cq = concept_of(q) or q.split("|")[0]
                    for (r, o), e in und.rel.get(cw, {}).items():   # the SOV relations behind the bond, either way
                        if o == cq:
                            count(("sov", f"{cw} {r} {cq}"), ("bond", f"L{L}:{q}"))
                    for (r, o), e in und.rel.get(cq, {}).items():
                        if o == cw:
                            count(("sov", f"{cq} {r} {cw}"), ("bond", f"L{L}:{q}"))
                    mw, mq = self.mind.pool.get(w), self.mind.pool.get(q)
                    for t in (mw.tags if mw else ()):   # a site of the partner the thought filled, e.g. a push's causes:<want> in a want's site
                        if t.startswith("causes:") and mq is not None and t in mq.sites:
                            count(("sov", f"{cw} causes {t[7:]}"), ("bond", f"L{L}:{q}"))

    def decision_view(self, k=12):
        """Params.decision_paths: what the mind's decisions rest on, most used first: decisions, thoughts, bonds, SOV relations."""
        tree = self.__dict__.get("decision_tree", {"nodes": {}, "decisions": 0})
        out = {"decisions": tree["decisions"]}
        for kind in ("decision", "thought", "bond", "sov"):
            nodes = sorted(((n, c) for (kk, n), c in tree["nodes"].items() if kk == kind), key=lambda x: -x[1])
            out[kind] = nodes[:k]
        return out

    def cleanup(self):
        """Params.dormancy (the user, 2026-11-11: "build a cleanup routine for it"): storage, not deletion. Every h0 x log2(1/floor) ticks
        (the time a molecule untouched takes to fade below the floor), each region whose object isn't in the world now and that nothing
        holds (given or tracked, a want, the goal or its stack, the anti-want, a node of the last 500 decision paths) and nothing touched in
        that time (its history, a relation written to its concepts) is stored: its territory row (territory.dormant), its ownership slots and
        its concepts' SOV molecules, candidate wants and questions (out of the pool), its concepts' relations (understanding.dormant_rel).
        Territory.row, Understanding.add and perceive wake it as it was."""
        import math
        import re
        mind, terr, und = self.mind, self.mind.territory, self.mind.understanding
        age = max(1, int(mind.p.h0 * math.log2(1 / mind.p.floor)))
        if mind.t - self.__dict__.get("_cleaned_at", -10 ** 9) < age:
            return
        self._cleaned_at = mind.t
        present = set(self.world.states())
        held = set()
        for x in [self.goal, *self.stack, *(self.__dict__.get("kept", {}) or {})]:
            if x:
                held |= {x, self.owner_of(x)}
        held |= {self.owner_of(x) for x in (mind.__dict__.get("anti_targets") or ())}
        held |= set(terr.wants)
        tree = mind.__dict__.get("decision_tree") or {}
        for _, _, nodes in tree.get("records", []):
            for _, n in nodes:
                for tok in re.findall(r"[A-Za-z0-9_+\-]+", n):
                    held |= {tok, self.owner_of(tok)}
        touched = set()
        for t, _, pair in reversed(und.log):
            if t < mind.t - age:
                break
            if isinstance(pair, tuple):
                for x in pair:
                    if isinstance(x, str):
                        touched |= {x, self.owner_of(x)}
        dormant = terr.__dict__.setdefault("dormant", {})
        stored_rel = und.__dict__.setdefault("dormant_rel", {})
        stored_anti = self.__dict__.get("anti_stored", [])   # set-aside anti-wants fade by acceptance too (the user, 2026-11-11): one that
        quiet_anti = self.__dict__.setdefault("anti_stored_quiet", {})   # hasn't come back for as many passes as the mind's acceptance
        for entry in list(stored_anti):                                   # is let go
            quiet_anti[entry] = quiet_anti.get(entry, 0) + 1
            if mind.p.acceptance is not None and quiet_anti[entry] >= mind.p.acceptance:
                stored_anti.remove(entry)
                del quiet_anti[entry]
                self.__dict__.setdefault("anti_log", []).append((mind.t, entry[0], "let go"))
        for entry in list(quiet_anti):
            if entry not in stored_anti:   # (came back: counting starts again if it is set aside again)
                del quiet_anti[entry]
        going = []
        k = mind.p.acceptance   # grief let go (the user, 2026-11-11: "acceptance"): a lost region whose object is gone, nothing new about it
        for r, row in terr.rows.items():   # for as many passes as the mind's acceptance, is stored even on decision paths (first its lost
            if k is not None and row.get("holder") == "lost" and r not in present and not row.get("tracked"):   # slot paid its concepts for
                news = (len(row["history"]), r in touched)   # good, their SOV molecules won every tick, and kept it on the paths)
                quiet = row.get("_grief_quiet", 0) + 1 if row.get("_grief_seen") == news[0] and not news[1] else 0
                row["_grief_quiet"], row["_grief_seen"] = quiet, news[0]
                if quiet >= k:
                    going.append(r)
                    self.__dict__.setdefault("let_go", []).append((mind.t, r))
                    continue
            if r in present or r in terr.given or row.get("tracked") or r in held or r in touched:
                continue
            last = row["history"][-1][0] if row["history"] else -10 ** 9
            if mind.t - last < age:
                continue
            going.append(r)
        if not going:
            return
        going_set = set(going)
        concepts = [c for c in und.rel if (und.owners.get(c) or self.owner_of(c)) in going_set and c not in held and c not in touched]
        for r in going:
            dormant[r] = terr.rows.pop(r)
        for c in concepts:
            stored_rel[c] = und.rel.pop(c)
        for i in [i for i in mind.pool if i.startswith(("own:", "own:q:")) and i.rsplit(":", 1)[-1] in going_set]:
            del mind.pool[i]
        stored_c = set(concepts)
        for i in [i for i in mind.pool if (i.startswith("sov:") and i[4:] in stored_c) or (i.startswith("subwant:") and i[8:] in stored_c)]:
            del mind.pool[i]
        for q, (c, r_) in list(und.questions.items()):
            if c in stored_c:
                mind.pool.pop(q, None)
                del und.questions[q]
        self.__dict__.setdefault("cleanup_log", []).append((mind.t, len(going), len(concepts)))

    def anti_update(self, invs):
        """Params.anti_wants (the user, 2026-11-11): what the mind doesn't want arises from loss. A region it held going lost makes that
        loss the anti-want held (the latest, one at a time, as a want is). Read relative, from the mind's own two halves (the go session's
        reading, 2026-11-11): what it perceived the region doing as it was lost (its memory of it, last_seen) and that the register held
        it: anti:held_<doing>, "a region I hold, <doing>", so it carries to every region it holds (first anti:<region>, a stone gone for
        good that nothing could threaten again). A prediction it owned is relative already and stays anti:<its region>. What it threatens
        (Mind.anti_targets, read by Mind.support): each held region's <doing>, or the prediction's own concepts. It is dropped only when
        pushes are on offer and none threatens it, by the SOV (prevents one of those, any funding): with nothing on offer,
        nothing has been shown not to (first dropped then too, and between turns in go every anti-want went within a slice).
        Dropped is set aside, not gone (the user, 2026-11-11, "make the fix"; the go session's trace: with go's placements named by what
        they do, the placement that lost the group isn't on offer on the empty board after it, so the anti-want was dropped 300 slices
        before the next endgame and never there when the same placement came round): it is kept (anti_stored), and comes back, held
        again, when a push on offer threatens it, as a settled thought comes back when something needs it. The latest first."""
        terr, und, told = self.mind.territory, self.mind.understanding, self.mind.p.credulity
        if self.mind.p.defense_still:   # the register presses for everything it holds (the balance principle, both sides
            # counting; the user, 2026-11-15): a push's defense counts its losses across ALL held regions, standing, no
            # anti-want needed in rotation. Found at the full hold (trace, s3p1): four destroyer pushes at stacked potential
            # 7.0 bid ~22, rest not at the top at all, and the one-anti defense read None — one rotating anti-want against
            # four armed destroyers. Computed here, read by Mind.support as anti_defense is
            self.defense_now(invs)
        read = self.__dict__.setdefault("_lost_read", {})
        log = self.__dict__.setdefault("anti_log", [])
        seen = self.__dict__.get("last_seen", {})
        lost_now = []
        for r, row in terr.rows.items():
            hist = row["history"]
            if any(ev == "lost" for tt, ev in hist[read.get(r, 0):]):
                lost_now.append(r)
            read[r] = len(hist)
        # read from the object lost, not its parts: of the regions lost together, those whose name no other lost region's extends (a
        # stone, not its sides and bond: the world's own object naming, the prefix owner_of reads). First the last one in the register's
        # order was taken, often a side last seen binding or pressed, and in go most anti-wants were "a region I hold, binding" (the go
        # session's trace, 2026-11-11)
        wholes = [r for r in lost_now if not any(r != o and r.startswith(o + "_") for o in lost_now)]
        lessons = self.mind.p.lived_loss_lessons
        for r in wholes:
            row = terr.rows[r]
            if lessons and self.__dict__.get("anti") is not None:   # (Params.lived_loss_lessons: the one it replaces is set aside, not
                prev = (self.anti, self.__dict__.get("anti_doing"))   # thrown away; first a slice's later losses overwrote its earlier
                stored_ = self.__dict__.setdefault("anti_stored", [])   # ones, and a forked knight's "held, hanging" stood for no slice:
                if prev not in stored_:                                 # trace_sf_loss.py, 2026-11-21)
                    stored_.append(prev)
            if row.get("prediction") or (row.get("tracked") and r.startswith("potential_")):   # an owned prediction: relative already
                self.anti, self.anti_doing = r, None
            else:
                doing = seen.get(r)
                self.anti, self.anti_doing = (f"held_{doing}", doing) if doing else (r, None)
                if lessons and doing:   # the lived loss is a lesson (Params.lived_loss_lessons): its kind, relative to the mind's last move as
                    last = self.__dict__.get("_last_own_push")   # the world names a prediction's, is feared from now on, and that move
                    effect = f"{r}_{doing}"                       # lived causing it (seen); first only a predicted loss's kind was feared
                    rel_of = getattr(self.world, "lived_rel", None)
                    kind = (rel_of(effect, last[1]) if rel_of and last else None) or effect
                    und.__dict__.setdefault("loss_rels", set()).add(kind)
                    # blame only where the move made a difference (the user, 2026-11-21, "DUH"): its own prediction, when it made the move,
                    # touched the region, and some other move on offer was predicted to leave it alone. First every lived loss blamed the
                    # last move, 5-20 a move, most made by the opponent whatever the mind did: every move blamed, none singled out,
                    # nothing to learn (measure_lessons.py)
                    made, regs = self.__dict__.get("_regions_at_move") or (None, {})
                    mine_ = regs.get(made) if made is not None else None
                    blamed_ = bool(last) and mine_ is not None and r in mine_ and any(r not in v for k_, v in regs.items() if k_ != made)
                    if blamed_:
                        # told, not seen: a blame is the mind's own inference about a cause, held until tested (the user, 2026-11-21:
                        # "that's horrible, it can't be lived fact"; first written seen, and a wrong blame became firm fact)
                        und.add(inv_id(last[1]), "causes", f"potential:{kind}", "told", 1.0)
                        und.add(f"potential:{kind}", "caused_by", inv_id(last[1]), "told", 1.0)
                    chain = self.reasons_back() if blamed_ else []   # how it got here, through its own reasons (the user, 2026-11-21, "A, through its reasons")
                    for step in chain:
                        for c_ in {step["move"], step["commit"]} - {None}:
                            und.add(c_, "causes", f"potential:{kind}", "told", 1.0)
                            und.add(f"potential:{kind}", "caused_by", c_, "told", 1.0)
                    self.__dict__.setdefault("lived_lessons", []).append(dict(
                        t=self.mind.t, effect=effect, kind=kind, last=inv_id(last[1]) if last else None, blamed=blamed_,
                        back=[(s["t"], s["move"], s["commit"], s["goal"]) for s in chain]))
                    if not blamed_ and self.mind.p.open_loss_blame:   # its last move made no difference: open, for the moves after
                        self.__dict__.setdefault("_open_losses", []).append(dict(r=r, effect=effect, kind=kind, t=self.mind.t,
                                                                                 left=OPEN_LOSS_MOVES))
            log.append((self.mind.t, self.anti, "set"))
        def targets_of(r, doing):
            if doing:   # every region the register holds or has held, doing that: a loss of "mine", whichever of its regions (the user,
                rows = list(terr.rows.items()) + list(terr.__dict__.get("dormant", {}).items())   # 2026-11-11; first only regions held
                out = {f"{x}_{doing}" for x, row in rows                                           # now, and in go every link from a
                       if not row.get("prediction") and not x.startswith("potential_")             # placement to a stone coming apart
                       and (x in terr.given or row.get("ever") or row.get("holder") in ("mine", "contested"))}   # named a stone long
                # and the predicted losses of that doing, relative (Params.predicted_losses: a push told it causes "potential:opportunity+0_
                # bearing" causes a held region bearing wherever it is; the user, 2026-11-12)
                return out | {f"potential:{rel}" for rel in und.__dict__.get("loss_rels", ()) if rel.endswith(f"_{doing}")}
            return {c for c, o in und.owners.items() if o == r} | {r}                              # gone: none ever counted)

        def threats(doing):
            # which relations threaten: for an owned prediction's anti-want, prevents only (its targets are what it owned: a push that causes
            # it is the way back, not a threat; first causes counted, and a lost prediction's anti-want came back whenever a push that clears
            # the run was on offer and pushed it down: the user, 2026-11-11). For "a region I hold, <doing>", causes too: its target is the
            # state the region was lost in, so a push that causes it causes the loss (the user, 2026-11-12, "Causes = threat"; first prevents
            # only, and in go, where nothing writes prevents, a mind with 383 lived "placement causes my held point bearing" filled its own
            # territory, the anti-want dropped a slice after each loss: go/trace_opp_games.py)
            return ("prevents", "causes") if doing else ("prevents",)

        def threatened(targets, doing=None):
            kinds = threats(doing)
            return any(k in kinds and o in targets and e[0] + e[2] + told * e[1] > 0
                       for c in invs for (k, o), e in und.rel.get(c, {}).items())
        stored = self.__dict__.setdefault("anti_stored", [])   # anti-wants dropped: set aside, latest last
        r = self.__dict__.get("anti")
        if r is None and invs:   # one set aside comes back when a push on offer threatens it
            for back, back_doing in reversed(stored):
                if threatened(targets_of(back, back_doing), back_doing):
                    stored.remove((back, back_doing))
                    self.anti, self.anti_doing, r = back, back_doing, back
                    log.append((self.mind.t, back, "returned"))
                    break
        if r is None:
            self.mind.anti_targets = None
            return
        targets = targets_of(r, self.__dict__.get("anti_doing"))
        self.mind.anti_targets = targets
        self.mind.anti_threats = threats(self.__dict__.get("anti_doing"))   # (read by Mind.support, as anti_targets is)
        if not self.mind.p.defense_still:   # (defense_still computed its all-held defense above; the one-anti defense stands aside)
            self.mind.anti_defense = None
        effects_after = getattr(self.world, "effects_after", None)
        if effects_after is not None and invs and not self.mind.p.defense_still:   # the forces say what each choice loses (the user,
            waiting = len(effects_after(None) & targets)   # 2026-11-11: waiting carries the loss the forces predict, and the anti-want
            if waiting:                                     # pulls toward pushes that prevent it): a push losing fewer held regions than
                                                            # waiting defends; one losing more costs; first only
                self.mind.anti_defense = {c: waiting - len(effects_after(inv) & targets)   # pushes could be pushed down, waiting never was,
                                          for c, inv in invs.items()}                      # and a mind averse to filling rows waited while
                if not any(self.mind.anti_defense.values()):                                # gravity filled them (13 top-outs in 400 slices)
                    self.mind.anti_defense = None
        if invs and not threatened(targets, self.__dict__.get("anti_doing")) and not self.mind.__dict__.get("anti_defense"):
            log.append((self.mind.t, r, "dropped"))
            if (r, self.__dict__.get("anti_doing")) not in stored:
                stored.append((r, self.__dict__.get("anti_doing")))
            self.anti = None
            self.mind.anti_targets = None
            self.mind.pool.pop(f"anti:{r}", None)

    def own_prediction(self, r, held):
        """Params.force_predictions: a certain prediction is owned (the user, 2026-11-10: "a correct prediction is ownership; if you lose
        the prediction by intervening, you've lost what you own"). Its potential effect, read relative to the piece, is given territory:
        held while a prediction of it stands (and held again when one stands again, as a given region back in view), lost when the
        mind's own push broke one. The agent tracks it itself: the world never shows a prediction, so perceive leaves it alone."""
        if self.mind.p.counted_pull and _COUNTED_EFFECT.search(r):   # NO counted change is ownable as a prediction
            return   # (clean code, 2026-11-16, two lessons one day apart: widenings owned became wants to re-make wounds
            # — 48 widening-wants in one run, the worst rate of any variant; then closings owned became wants UNMEETABLE
            # AT THE SOLUTION — a mind that sat on the full hold 149 slices, closing 75 times, dragged off it by the pull
            # of a want for "closing" with nothing left to close (rung2j trace). The grammar law completes: states are
            # held, changes are caused, and neither counted states nor counted changes are territory — only the states
            # the changes serve
        self.mind.understanding.owners[r] = r.replace(":", "_", 1)   # the potential effect is its region's (its slots pay for it)
        r = r.replace(":", "_", 1)   # a region's name holds no ":" (own:<kind>:<region>; first potential:..., and the slots' ids broke)
        self.track_region(r, held)
        self.mind.territory.rows[r]["prediction"] = True   # (relative already: its loss is its own anti-want)

    def unknowns(self, sides, present):
        """Params.unknown_slots (the user, 2026-11-19): a location a seen side's force points at (world.forces: (side, location)) that
        has never been in view is an unknown, an ownership slot of its own kind that pulls (Territory._open_slots); having a location
        in view is a gain of territory: it is held from then on (tracked, as tetris tracks its open rows; out of view isn't gone), and
        an unknown it was is closed. The state an unknown would be seen in is what the side's force says of it (my reading: a side
        pressed meets a mountain, so the location would be seen blocking; a side free meets open ground, seen free), kept as the
        state its slot offers as a want (own_candidates)."""
        terr = self.mind.territory
        locs = getattr(self.world, "locations", None)
        for r in [o for o in present if (locs is None or locs(o))]:
            if terr.rows.get(r, {}).get("unknown"):   # in view now: an unknown no longer, tracked or not (first only an untracked one was
                terr.rows[r].pop("unknown", None)     # cleared, and where the world's own territory reading had tracked it already, it stayed
            if terr.rows.get(r, {}).get("tracked"):   # unknown for good: codecraft's protagonist shuttled among 4 constructs, each still
                continue                              # pulling as unseen, 2026-11-20)
            row = terr.row(r)
            row.pop("unknown", None)
            row.setdefault("seen_states", set()).add(f"{r}_{self.world.states()[r]}")
            self.track_region(r, True)
        reached = getattr(self.world, "held_once_reached", None)   # a region the world says is held for good once reached (zodiac: a city
        if reached:                                               # stood on; the user's territory, "cities reached"), by reading, not claims:
            for o, st in self.world.states().items():             # first the walks on and off a city were its claims, and leaving Aries
                if reached(o, st) and not terr.rows.get(o, {}).get("tracked"):   # read as lost, a want to go back (trace_trip_start.py)
                    self.track_region(o, True)
        shown = self.world.states()
        for a, b in sides:
            if b in self.seen_objs or terr.rows.get(b, {}).get("tracked") or shown.get(a) not in ("pressed", "free"):
                continue   # (only a side perceived now says what is across it: first an unperceived one read as free)
            row = terr.row(b)
            row["unknown"] = True
            us = getattr(self.world, "unknown_state", None)   # (the world says what an unknown would be seen in, where it reads its sides
            row["unknown_states"] = {us(b, a, shown.get(a)) if us else   # its own way: codecraft, 2026-11-20; else zodiac's reading)
                                     f"{b}_{'blocking' if shown.get(a) == 'pressed' else 'free'}"}

    def count_turns(self):
        """Params.plan_discovery: the changes of the body's travelling gerund the mind notices this trip (a trip starts when the body is
        perceived resting again, set back at the start), and at the root want's arrival, the trip's total as a plan known: the first, or
        a better one (a discovery, as discovered() makes one in imagination)."""
        here = Model.body_at(self.facts_now())
        if "trip_start" not in self.__dict__:   # (the first trip starts where the mind first stands)
            self.trip_start = here
        for e in self.world.diffs:
            if not e.startswith("body: "):
                continue
            to = e.split(" -> ")[-1]
            if to == "resting":
                self.trip_turns, self.trip_start = 0, here
            elif to.startswith("travelling_"):
                self.trip_turns = self.__dict__.get("trip_turns", 0) + 1
        root = self.stack[0] if self.stack else self.goal
        if root is not None:   # the trip's destination, remembered: by the slice the arrival is perceived the want is already met and
            self.trip_want = root   # gone (first the arrival was read off the want held then, and none was: no look back ran)
        root = self.__dict__.get("trip_want")
        if root is not None and root in self.facts_now():
            com = self.__dict__.get("committed")
            if com and com["ins"]["effect"] == root and not com["ins"].get("outcome"):
                com["ins"]["outcome"] = "confirmed"   # the plan committed to came (the world answered: the mind stands at its want)
            if self.__dict__.get("_arrived") != (root, self.__dict__.get("trip_start")):
                self._arrived = (root, self.__dict__.get("trip_start"))
                self.plan_known(root, self.__dict__.get("trip_turns", 0), "walked")
                self.look_back(root, here)

    # Looking back (the user, 2026-11-19: the mind "can 'look back' on its route, and come up with alternatives"), and committing to the
    # best plan (the user, 2026-11-20, "try commitment"). My readings, named: looking back, at the arrival, is imagining over the ground
    # the mind holds (each location it has had in view, each side as it last saw it, the side forces) for the walk from the trip's start
    # to where it stands with the fewest gerund changes, the user's measure, the first found among ties; the plan is the walks' names;
    # offered at the plan's start as a commit (Params.commit), its prediction SOV's forces the side forces along the route, due when the
    # walks are done (a walk and its landing, two slices each, and one to spare).

    def recall_way(self, start, dest):
        """The mind's memory of the way (the user, 2026-11-20: "the mind's memory apparatus, not authored"): over the ground it holds
        (each location had in view, each side as it last saw it, the side forces), the walk from start to dest with the fewest gerund
        changes. -> (turns, walks, the side forces along it) or None."""
        import heapq
        if start is None or dest is None:
            return None
        und, seen = self.mind.understanding, self.__dict__.get("side_seen", {})
        held = {r for r, row in self.mind.territory.rows.items() if row.get("tracked")}
        forced = lambda side: next((o for (r, o), e in und.rel.get(side, {}).items() if r == "forces" and e[0] > 0), None)
        dist, prev, todo, k_ = {(start, None): 0}, {}, [(0, 0, start, None)], 0
        while todo:
            turns, _, here, h0 = heapq.heappop(todo)
            if turns > dist.get((here, h0), 1e9):
                continue
            if here == dest:
                chain, forces, node = [], [], (here, h0)
                while node in prev:
                    node, side, name = prev[node]
                    chain.insert(0, name)
                    forces.insert(0, (side, forced(side)))
                return turns, chain, forces
            for h in ("north", "east", "south", "west"):
                side = f"{here}_{h}"
                n = forced(side) if seen.get(side) == "free" else None
                if n is None or n not in held:
                    continue
                t2 = turns + (h != h0)
                if t2 < dist.get((n, h), 1e9):
                    dist[(n, h)], prev[(n, h)] = t2, ((here, h0), side, f"walk_{h}")
                    k_ += 1
                    heapq.heappush(todo, (t2, k_, n, h))
        return None

    def look_back(self, g, dest):
        start = self.__dict__.get("trip_start")
        got = self.recall_way(start, dest)
        if got is None:
            return
        turns, chain, forces = got
        old = self.__dict__.setdefault("plans", {}).get(g)
        if old is None or turns < old["turns"]:
            self.plans[g] = dict(start=start, dest=dest, chain=chain, turns=turns, forces=forces)
        self.plans[g].setdefault("dest", dest)
        self.plan_known(g, turns, "looked back")

    def plan_sequences(self):
        """The best plan to the root want, offered to commit to where it starts; anywhere else, the way recalled from where the mind
        stands to the plan's destination (the user, 2026-11-20, "yes, build it": first only at the start, and a mind that left it
        without committing broke the want down into "see this cell" sub-wants that flipped at the view's edge for 4,000 slices,
        trace_stall.py on seed 0). commit_offers reads sequence_predicted."""
        import hashlib
        self.sequence_predicted = []
        if self.__dict__.get("committed"):
            return
        root = self.__dict__.get("trip_want") or (self.stack[0] if self.stack else self.goal)
        plan = self.__dict__.get("plans", {}).get(root)
        here = Model.body_at(self.facts_now())
        if plan is None or here is None:
            return
        if here != plan["start"]:
            memo = self.__dict__.setdefault("_recalled", {})
            key = (here, plan.get("dest"), len(self.mind.territory.rows))
            if key not in memo:
                memo.clear()
                memo[key] = self.recall_way(here, plan.get("dest"))
            got = memo[key]
            if got is None or not got[1]:
                return
            plan = dict(plan, start=here, turns=got[0], chain=got[1], forces=got[2])
        if not plan["chain"]:
            return
        sovs = self.mind.understanding.__dict__.setdefault("prediction_sovs", {})
        forces = frozenset(plan["forces"])
        pid = f"prediction:{root}:{hashlib.md5(repr(sorted(forces)).encode()).hexdigest()[:8]}"
        sovs.setdefault(pid, dict(effect=root, forces=forces, instances=[]))
        self.sequence_predicted = [(root, 2 * len(plan["chain"]) + 1, root, pid, list(plan["chain"]))]
        # the commit is told it brings the want itself, as a push known to bring a want is linked to it (first only
        # "potential:<want>", the commit path's own name, which no want of the mind's is: nothing tied the plan to Leo, and the commit lost
        # to every walk at Aries, trace_commit_offer.py)
        und, cid = self.mind.understanding, inv_id(("commit", f"potential_{root}", "+".join(plan["chain"])))
        if ("causes", root) not in und.rel.get(cid, {}):
            und.add(cid, "causes", root, "told", 1.0)
            und.add(root, "caused_by", cid, "told", 1.0)

    def discovered(self, model):
        """Params.plan_discovery: the plans this planning imagined to the want, and the fewest changes among them; fewer than the best
        known is a discovery."""
        root = self.stack[0] if self.stack else self.goal
        for g, total in (model.__dict__.get("found") or {}).items():
            if g == root:   # (a plan is the route to the root want, the destination; a sub-want's line is a step on the way)
                self.plan_known(g, total, "imagined")

    def plan_known(self, g, total, how):
        best = self.__dict__.setdefault("route_best", {})
        if g in best and best[g] <= total:
            return
        best[g] = total
        self.__dict__.setdefault("discoveries", []).append((self.mind.t, g, total, how))
        self.track_region(f"plan_{g}_{total}turns", True)   # a gain of territory: the better plan held from now on (the user)

    def remember_sides(self):
        """Params.force_walks: each side's state as last perceived (a side is an object with three underscores: pos_x_y_<heading>),
        so a plan can walk the forces of ground seen and now out of view (out of view isn't gone)."""
        seen = self.__dict__.setdefault("side_seen", {})
        for o, st in self.world.states().items():
            if o.startswith("pos_") and o.count("_") == 3:
                seen[o] = st

    def open_loss_blame(self, made):
        """Params.open_loss_blame, at each move the mind makes: every open lived loss (a region lost that its last move made no difference
        to) is read against this move's decision. The region no longer lost, or this move predicted to bring it back: closed. Another move
        on offer predicted to bring it back (SovAgent.defense_now's regains), this one not: this move is blamed, told, as a lived lesson's
        blame is, a new lesson filed (late=True) so the blame's challenge (world.blame_read) tests it; closed. Otherwise it stays open,
        up to OPEN_LOSS_MOVES of the mind's moves."""
        terr, und = self.mind.territory, self.mind.understanding
        regains = self.__dict__.get("_decision_regains") or {}
        keep = []
        for ol in self.__dict__.get("_open_losses") or []:
            r = ol["r"]
            if (terr.rows.get(r) or {}).get("holder") not in ("lost", "contested") or r in regains.get(made, ()):
                continue   # brought back, or this move brings it back
            if any(r in v for k_, v in regains.items() if k_ != made):   # another move would have: this one is blamed
                pot = f"potential:{ol['kind']}"
                und.add(made, "causes", pot, "told", 1.0)
                und.add(pot, "caused_by", made, "told", 1.0)
                self.__dict__.setdefault("lived_lessons", []).append(dict(
                    t=self.mind.t, effect=ol["effect"], kind=ol["kind"], last=made, blamed=True, back=[], late=True, opened=ol["t"]))
                continue
            ol["left"] -= 1
            if ol["left"] > 0:
                keep.append(ol)
        self._open_losses = keep

    def reasons_back(self):
        """How the mind got here, through its own reasons (Params.lived_loss_lessons; the user, 2026-11-21, "A, through its reasons"):
        from its last move back, the moves of this episode made for the same plan — a step of the same commitment, or made for the same
        want — stopping where the reason changes. Each its record as it made it (reason_log): move, commitment, want. -> newest first."""
        rl = self.__dict__.get("reason_log") or []
        if not rl:
            return []
        out = [rl[-1]]
        for r in reversed(rl[:-1]):
            if r["episode"] != out[-1]["episode"]:
                break
            prev = out[-1]
            same_commit = r["commit"] is not None and r["commit"] == prev["commit"] and r.get("commit_since") == prev.get("commit_since")
            # the same want, set once and pursued: one pursuit (2026-11-21: first any move for the same want counted, and a standing
            # relative want, "potential:plan_square+1_none", set again and again, strung 11 moves over 64 slices into one plan, the blame
            # for a fork spread over the game; the move that allowed it, the last, no more than the rest: lived_q seed 1 game 1)
            # the want in hand, the same one, set at the same moment (2026-11-21, the user: "fix 1"): first a shared root sufficed, and
            # a root held all game ("end a plan of theirs to win an outpost 4 squares from where it lands", set at move 3) strung Qe5,
            # h4, h5 and Ke8, made for four different wants under it, into one pursuit; a lost pawn was blamed on all four
            same_want = (r["goal"] is not None and r["goal"] == prev["goal"]
                         and r.get("goal_since") is not None and r.get("goal_since") == prev.get("goal_since"))
            if not (same_commit or same_want):
                break
            out.append(r)
        return out

    def track_region(self, r, held, contested=False):
        """A region the agent tracks itself, held or lost by what it is now rather than by claims (an owned prediction; in tetris a row
        of open space, held while it is empty: the user, 2026-11-11): given territory, held while `held`, lost when not, held again
        when it is again; and, held, contested while `contested` (a threat the mind can still answer: warpchess's opponent plan it can
        stop; the user, 2026-11-13, "three levels"). Perceive leaves it alone (row["tracked"])."""
        terr = self.mind.territory
        row = terr.row(r)
        row["tracked"], row["ever"] = True, True
        terr.given.add(r)
        if not held and self.mind.p.no_loss_wants:   # (the states it is told are lost, for the want gate: a region contested from the
            st_ = getattr(self.world, "shown", {}).get(r)   # start has no held state to read them against; 2026-11-21)
            if st_ is not None:
                row.setdefault("lost_states", set()).add(f"{r}_{st_}")
        if row.get("gone") != (not held) or bool(row.get("threatened")) != bool(contested and held):
            row["gone"] = not held
            row["threatened"] = bool(contested and held)
            terr.update([r])

    def situations_remember(self):
        """Params.own_wants: a sub-want met co-occurs with the news perceived while it was held; one dropped co-occurs with not:<that news>
        (the user: situations remember the sub-wants they co-occur with). Lived receipts: the agent held the sub-want and perceived the news."""
        log = self.__dict__.setdefault("news_log", [])
        log.append((self.mind.t, frozenset(effect_id(e) for e in self.world.diffs)))
        seen = self.__dict__.get("_sub_log_read", 0)
        new = self.sub_log[seen:]
        self._sub_log_read = len(self.sub_log)
        und = self.mind.understanding
        for t, g, kind in new:
            if kind not in ("met", "dropped"):
                continue
            start = max((tt for tt, gg, k in self.sub_log if gg == g and k == "set" and tt <= t), default=None)
            if start is None:
                continue
            news = set().union(*(n for tt, n in log if start <= tt <= t)) - {g}
            for e in news:
                und.add(g, "co_occurs", e if kind == "met" else f"not:{e}", "seen")

    def own_states(self):
        """Each region's state now (world.states), and as records: every state each region has been seen in, and the facts in
        which regions became the mind's (a claim taking: a Black piece captured)."""
        terr = self.mind.territory
        states = {r: f"{r}_{g.replace(' ', '_')}" for r, g in self.world.states().items() if g is not None}
        claims = terr.__dict__.setdefault("claim_facts", set())
        skip = terr.__dict__.get("unclaimable")
        for r, f in states.items():
            if skip and r.startswith(skip):   # (no one's to claim: no region to offer states to; first a row was made for every cell)
                continue
            terr.row(r).setdefault("seen_states", set()).add(f)
        for r, row in terr.rows.items():
            mine = row.get("holder") == "mine"
            if mine and not row.get("was_mine") and r not in terr.given and r in states:
                claims.add(states[r])
            if mine and r in states and row.get("_held_seen") == states[r]:   # the states the register has held it in (Params.held_state_
                row.setdefault("held_states", set()).add(states[r])           # wants: what a lost slot wants back), in a state it was in
                kind_ = next((p for p in (terr.__dict__.get("read_held") or ()) if r.startswith(p)), None)   # last reading too (first
                if kind_:   # any: when a go board was set back, every held opportunity read "breathing" for the slice before the register
                    # let it go, and "breathing" became a held doing every control slot offered: go/trace_wants_all.py). And, for a region
                    # held by reading, the doing it was held in, kept for its kind across regions and games
                    terr.__dict__.setdefault("held_doings", {}).setdefault(kind_, set()).add(states[r][len(r) + 1:])
            row["_held_seen"] = states.get(r) if mine else None
            row["was_mine"] = mine
        return states

    def leads(self, f, targets, depth=2):
        """Whether the mind's funded relations connect fact f to one of the targets: f causes it (lived or worked out, told at
        credulity; imagined funds nothing), directly or through what f causes, up to depth steps."""
        und, told = self.mind.understanding, self.mind.p.credulity
        frontier, seen = {f}, {f}
        for _ in range(depth):
            nxt = set()
            for x in frontier:
                for (r, e), w in und.rel.get(x, {}).items():
                    if r == "causes" and w[0] + w[2] + told * w[1] > 0 and e not in seen:
                        if e in targets:
                            return True
                        nxt.add(e)
            seen |= nxt
            frontier = nxt
        return False

    # ---- improvement is territory (Params.improvement_territory; the user, 2026-11-20: "point territory at the problem"; "instead of
    # 'err less and less', it's 'gain territory more and more, better, faster, and cheaper'"; design in cognitivechess_v2/PLAN.md) ----
    #
    # A way: one stretch from a start to an end, with its costs. The mind's own plans: a want set -> met (ended well) or dropped, stepped
    # aside or cleared (ended badly), from sub_log. The opponent's plans, and any threat: a region of the register going from mine to
    # contested -> mine again (ended well) or lost (ended badly), from the register's history. Each way is filed under its kind (the
    # world's kind_of where it has one; else the name with its places taken out: my reading, `_kind`). Per kind the best way so far on
    # each measure is the ghost; the kind's regions better / faster / cheaper are tracked by the agent (given territory): beating the
    # best is a claim that takes (held, the new best, and a for-good record); matching holds; worse contests; ending badly is a loss.
    # Cheaper: moves made + thinking slices (slices with no move) + territory lost on the way (the user chose all three; summed with
    # weight 1 each: my reading). One level up, `improving`: held while the kinds whose best improved this episode are at least the last
    # episode's; contested when fewer. An episode: a game of the world's (world.games) where it keeps them, else 200 slices.

    _PLACE = None

    @staticmethod
    def _kind(world, name):
        kind_of = getattr(world, "kind_of", None)
        if kind_of is not None:
            return kind_of(name)
        import re
        if SovAgent._PLACE is None:
            SovAgent._PLACE = re.compile(r"(?<![a-z])([a-h][1-8]|\d+)(?![a-z0-9])")
        return SovAgent._PLACE.sub("n", name).replace(":", "_")

    def improvement_update(self):
        mind, terr = self.mind, self.mind.territory
        st = self.__dict__.setdefault("_improve", dict(sub_read=0, hist_read={}, open={}, best={}, lost=0, thinking=0, moves_seen=0,
                                                      episode=0, ep_new=0, last_ep_new=None, records=0, log=[]))
        t = mind.t
        moves = self.__dict__.get("_moves_made", 0)
        if moves == st["moves_seen"]:   # a slice with no move made: a thinking slice
            st["thinking"] += 1
        st["moves_seen"] = moves
        now = lambda: (t, moves, st["thinking"], st["lost"])

        def close(key, kind, good):
            t0, m0, k0, l0 = st["open"].pop(key)
            slices, cost = t - t0, (moves - m0) + (st["thinking"] - k0) + (st["lost"] - l0)
            st["log"].append((t, kind, good, slices, cost))
            chain = [c for tt, c in self.__dict__.get("_moves_log", ()) if t0 <= tt <= t]   # the moves this way took
            if good and chain and (kind not in st.setdefault("best_chain", {}) or cost < st["best_chain"][kind][0]):
                st["best_chain"][kind] = (cost, chain)   # recalled as an option for the next way of this kind (improvement_options)
            for measure, value in (("better", 0 if good else 1), ("faster", slices), ("cheaper", cost)):
                r = f"pace_{measure}__{kind}"
                if not good:
                    self.track_region(r, False)   # ended badly: a loss
                    continue
                best = st["best"].get((measure, kind))
                if best is None or value < best:   # beats the best (the first way sets it): a claim that takes, a for-good record
                    st["best"][(measure, kind)] = value
                    self.track_region(r, True)
                    st["records"] += 1
                    rec = f"pace_record_{st['records']}"
                    self.track_region(rec, True)
                    terr.rows[rec]["for_good"] = True
                    st["ep_new"] += 1
                else:
                    self.track_region(r, True, contested=value > best)   # matched: held; worse: contested

        # the mind's own plans: wants set, met or ended
        for _, g, ev in self.sub_log[st["sub_read"]:]:
            if g is None:
                continue
            key = ("want", g)
            if ev == "set":
                st["open"][key] = now()
            elif key in st["open"] and ev in ("met", "dropped", "stepped_aside", "cleared"):
                close(key, "want_" + self._kind(self.world, str(g)), ev == "met")
        st["sub_read"] = len(self.sub_log)
        # threats: regions mine -> contested -> mine again or lost; and territory lost on the way (cheaper's third cost)
        for r, row in list(terr.rows.items()):   # (a snapshot: closing a way adds pace regions to the register)
            if r.startswith("pace_"):
                continue
            hist = row.get("history", ())
            k = st["hist_read"].get(r, 0)
            for _, ev in hist[k:]:
                key = ("threat", r)
                if ev == "lost":
                    st["lost"] += 1
                if (ev == "contested" or (ev == "re-tested" and (mind.p.improvement_contests or mind.p.improvement_retested)
                                          and row.get("holder") == "contested")) and \
                        key not in st["open"]:   # (re-tested: the register's name for lost -> contested as for lost -> held; under
                    st["open"][key] = now()          # Params.improvement_contests a lost region threatened again opens a way: first
                    continue                         # zodiac's roads, once lost, never opened one again, 2026-11-21; trace_road_hist.py)
                elif key in st["open"] and ev in ("mine", "claimed", "re-tested", "lost"):
                    close(key, "threat_" + self._kind(self.world, r), ev != "lost")
            st["hist_read"][r] = len(hist)
        # one level up: improving, episode by episode
        games = getattr(self.world, "games", None)
        ep = len(games) if games is not None else t // 200
        if ep != st["episode"]:
            if st["last_ep_new"] is not None:
                self.track_region("pace_improving", True, contested=st["ep_new"] < st["last_ep_new"])
            st["last_ep_new"], st["ep_new"], st["episode"] = st["ep_new"], 0, ep

    def improvement_gains(self, invs):
        """The options weighed against the meta-territory (the user, 2026-11-20: "the mind creates various 'options' that would improve
        the meta-territory"): for each option on offer — a push, with the effects the forces predict for it (push_predicted), or a
        commitment, with its sequence's effect and length (sequence_predicted) — the open ways it would end well (a held want met; a
        threatened region brought back to a state it was held in), and what each way would cost ended so: faster, its slices so far
        plus the option's slices; cheaper, its moves, thinking slices and losses so far plus the option's moves. Each measure on which
        that beats the best known for the way's kind is a predicted gain of 1 (a region's worth, as defense_now counts a region; better
        is not predicted: it is settled when the way ends). -> {option id: gain}"""
        st = self.__dict__.get("_improve")
        if not st or not st["open"]:
            return {}
        terr = self.mind.territory
        t, moves, thinking, lost = self.mind.t, self.__dict__.get("_moves_made", 0), st["thinking"], st["lost"]
        effects = {}   # option id -> [(absolute effect, slices until it lands, moves it takes)]
        for eff, n, rel, pid, cc in self.__dict__.get("push_predicted", []) or []:
            effects.setdefault(cc, []).append((eff, n, 1))
        for eff, n, rel, pid, chain in self.__dict__.get("sequence_predicted", []) or []:
            c = inv_id(("commit", f"potential_{rel}", "+".join(chain)))
            effects.setdefault(c, []).append((eff, n, max(1, len(chain))))
        if self.mind.p.improvement_options:   # options the mind made itself (recalled and imagined lines: the world's imagine_options,
            for c, lines in (self.__dict__.get("imagined_options") or {}).items():   # set this slice): each the effect it would bring,
                for eff, n, m in lines:                                               # in how many slices, in how many moves
                    effects.setdefault(c, []).append((eff, n, m))
        out = {}
        contests = self.mind.p.improvement_contests
        lines_ = {}   # option -> {(measure, kind): its value} (Params.improvement_contests reads them all before judging any)
        for c in invs:
            beaten = set()   # (measure, kind): each meta-region is one region, a gain of 1 however many ways of its kind the option ends
            for eff, n, m in effects.get(c, ()):
                for key in (("want", eff), ("threat", self.owner_of(eff))):
                    if key not in st["open"]:
                        continue
                    if key[0] == "threat":
                        row = terr.rows.get(key[1], {})
                        kind_ = next((p_ for p_ in (terr.__dict__.get("read_held") or ()) if key[1].startswith(p_)), None) if contests else None
                        doing_ = eff[len(key[1]) + 1:] if eff.startswith(key[1] + "_") else None
                        if eff not in (row.get("held_states") or ()) and not (   # (Params.improvement_contests: or a doing regions of
                                kind_ and doing_ in terr.__dict__.get("held_doings", {}).get(kind_, ())):   # its kind, held by reading,
                            continue   # (not back to a state it was held in: no way ended well)              # are held in: zodiac's
                            # roads, a sign never beaten has no state of its own to come back to, 2026-11-21)
                    t0, m0, k0, l0 = st["open"][key]
                    kind = ("want_" if key[0] == "want" else "threat_") + self._kind(self.world, str(key[1]))
                    for measure, value in (("faster", t - t0 + n), ("cheaper", (moves - m0) + m + (thinking - k0) + (lost - l0))):
                        best = st["best"].get((measure, kind))
                        if contests:
                            v_ = lines_.setdefault(c, {})
                            v_[(measure, kind)] = min(value, v_.get((measure, kind), value))
                        if best is not None and value < best:
                            beaten.add((measure, kind))
            if beaten:
                out[c] = len(beaten)
                if self.mind.p.anneal_rate:   # the old best way's lived funding fades when a better way is imagined (Params.anneal_rate)
                    for measure, kind in beaten:
                        chain = (st.get("best_chain") or {}).get(kind, (None, []))[1]
                        if chain and chain[0] != c:
                            annealed = st.setdefault("_annealed", set())
                            if (t, kind) in annealed:
                                continue
                            annealed.add((t, kind))
                            und = self.mind.understanding
                            for mv in chain:
                                for (rel, o), e in und.rel.get(mv, {}).items():
                                    if rel == "causes" and e[0] > 0:
                                        e[0] *= 1.0 - self.mind.p.anneal_rate
                                        und.changed(mv)
                            st.setdefault("anneal_log", []).append((t, kind, len(chain)))
        if contests and lines_:   # Params.improvement_contests (the user, 2026-11-21, "Slower contests"): an option whose imagined line
            bar = {}              # would end a way slower or dearer than the best known for its kind contests that pace region, a
            for v_ in lines_.values():   # predicted loss of 1, as a worse way lived contests it (improvement_update); for a kind with no
                for k_, val in v_.items():   # best yet, the fastest (cheapest) line imagined this slice is the bar. First only gains were
                    b_ = st["best"].get(k_)   # predicted: a slower option tied with a faster one, and in zodiac's battles faithful_choice's
                    bar[k_] = b_ if b_ is not None else min(val, bar.get(k_, val))   # tie-break cycled the mind through switches
            for c, v_ in lines_.items():
                worse = sum(1 for k_, val in v_.items() if val > bar[k_])
                if worse:
                    out[c] = out.get(c, 0) - worse
        if contests and self.mind.p.improvement_options:   # a line the mind imagined ending its way badly (the world's imagine_options
            for c, regions in (self.__dict__.get("imagined_bad") or {}).items():   # names them: zodiac's battles, the mind out first;
                if c not in invs:                                                  # the user, 2026-11-21, "Imagine both sides") is a
                    continue                                                       # predicted loss of the way's three pace regions, as a
                bad = sum(3 for r in regions if ("threat", r) in st["open"] or ("want", r) in st["open"])   # way lived ending badly
                if bad:                                                            # loses them (improvement_update)
                    out[c] = out.get(c, 0) - bad
        for c, inv in invs.items():   # a commitment starting with a move carries that move's meta gain (2026-11-20: the mind chooses largely
            if inv[0] == "commit" and inv[2] != "standing" and c not in out:   # through commitments; first only the bare move got it, and 164
                first = str(inv[2]).split("+", 1)[0]                           # imagined options that beat the best changed no move)
                if first in out:
                    out[c] = out[first]
        if out and st.get("_gains_logged") != t:   # (logged once a slice)
            st["_gains_logged"] = t
            st.setdefault("option_gains", []).append((t, len(out), len(invs), max(out.values())))
        return out

    def want_conditions_holding(self):
        """Params.control_spares_want: the regions of conditions the mind has learned for the wants it holds, that hold now -> {region}.
        A condition of a want: a split's tag on a push it knows causes the want (Meta.differentiate writes `conditioned_by` from the push
        to the tag, and the split itself), for the want in hand and every want on the stack."""
        mind, und = self.mind, self.mind.understanding
        wants = {w for w in (self.goal, *self.stack) if w}
        if not wants or und is None:
            return set()
        facts = self.facts_now()
        ways = {c for c, rels in und.rel.items() if any(rel == "causes" and o in wants and e[0] + e[1] + e[2] > 0
                                                        for (rel, o), e in rels.items())}
        conds = {o for c in ways for (rel, o), e in und.rel.get(c, {}).items() if rel == "conditioned_by" and not o.startswith("not:")}
        conds |= {sp["tag"] for x, sp in mind.meta.splits.items() if x.split("|")[0] in ways}
        return {und.owners.get(f) or f.rsplit("_", 1)[0] for f in conds if f in facts}

    def own_candidates(self):
        """The candidate sub-wants an open ownership slot's site takes: every state its region has been perceived in, but the one it
        is in now (a sub-want that holds is met as it is set). Which one is wanted is the tournament's to decide, as for any thought:
        binding, support, tension. (Before, I filtered them by rules of mine: states while the mind's, a claim's word matched across
        regions, then what the mind's relations connect to its wants. The user: "why are you making rules at all???")"""
        mind, terr = self.mind, self.mind.territory
        if not mind.p.territory:   # (ablation, Params.territory: no ownership, so no want offered for being its own)
            return []
        if mind.p.slot_bound_wants:   # a candidate offered by a slot that has since closed leaves with it (Params.slot_bound_wants)
            open_ = terr.open_slots()
            for i in [i for i in mind.pool if i.startswith("subwant:")]:
                slot = next(((k, r) for t in mind.pool[i].tags if "?" in t
                             for k, r in [t.split("?", 1)] if k in ("lost", "control", "unclaimed", "contested", "unknown")), None)
                if slot is not None and slot not in open_:
                    mind.pool.pop(i, None)
        now = self.own_states()
        holds = set(now.values())
        out = []
        needs = self.want_conditions_holding() if mind.p.control_spares_want else set()
        for i in list(mind.pool):
            if not i.startswith(("own:lost:", "own:control:", "own:unclaimed:", "own:contested:", "own:unknown:")):
                continue
            kind, r = i.split(":", 2)[1:]   # (a region name can hold ":": a whole want's, all:a&b)
            row = terr.rows.get(r, {})   # perceived states, and with Params.dreams the states dreams showed it (dreams shape wants, the user)
            seen = row.get("seen_states", set()) | (row.get("dreamed_states", set()) if mind.p.dreams else set())
            if kind == "unknown":   # never seen: the state its seen side's force says it would be seen in (Params.unknown_slots)
                seen = set(row.get("unknown_states", ()))
            if mind.p.held_state_wants and kind in ("lost", "contested") and row.get("held_states"):
                # a lost or contested slot asks for the region back: the states the register held it in (the user, 2026-11-13, "Held
                # states"; first every state it had been seen in, and in go the mind wanted a held point's opportunity filled or alive,
                # its own loss, go/trace_want.py). A slot on a region never held (control, unclaimed) offers every state, as before
                seen = row["held_states"]
            kind_ = next((p for p in (terr.__dict__.get("read_held") or ()) if r.startswith(p)), None)
            if mind.p.held_state_wants and kind in ("control", "unclaimed") and kind_:
                # a region held only by reading, never held: the doings the register has held regions of its kind in (the user,
                # 2026-11-13, "The held doings"; relative, as the anti-want is). First every state it had been seen in, and in go a
                # control slot on a point where the mind's own stone stood offered "White's opportunity there alive" as the root want
                # that filled its eyes (go/trace_wants_all.py)
                seen = {f"{r}_{d}" for d in terr.__dict__.get("held_doings", {}).get(kind_, ())}
            for f in sorted(seen - holds):
                if f in (self.goal, *self.stack) or f in self.failed_subs:
                    continue
                if kind == "control" and r in needs:   # (Params.control_spares_want: a probe that would undo a condition of the want in
                    continue                          #  hand waits until the want is met)
                out.append(clause(f"subwant:{f}", tags=(f"{kind}?{r}", "subwant", f"region:{r}")))
        # an owned prediction offers its potential effect while no prediction of it stands (the user, 2026-11-12, "yes, try it": a correct
        # prediction is ownership, so the mind can want one back; first an owned prediction became a want only when lost, and a prediction
        # has no state in the world to want, so a push told it brings a clear was tagged so and nothing took hold of it)
        standing = {sovs_["effect"] for sovs_ in [mind.understanding.__dict__.get("prediction_sovs", {}).get(ins["sov"], {})
                                                   for ins in self.__dict__.get("predicted", {}).values()] if sovs_}
        for r, row in terr.rows.items():
            if not row.get("prediction") or not r.startswith("potential_"):
                continue
            rel = r[len("potential_"):]
            f = f"potential:{rel}"
            if rel in standing or f in (self.goal, *self.stack) or f in self.failed_subs:
                continue
            if not any(f in v for v in (self.__dict__.get("push_leads") or {}).values()):   # only while a push on offer leads to it from here
                continue   # (as a sub-want is offered only if a known push can make it; first wanted with nothing in reach, and the want held
                           # the top for slices while nothing it pulled could act)
            out.append(clause(f"subwant:{f}", tags=(f"{row.get('holder')}?{r}", "subwant", f"region:{r}")))
        if mind.p.condition_subwants and self.goal is not None:   # the planner's backward step (README: "what conditions
            # does the known way need? Each becomes a nearer want"): a way to the held want whose KNOWN condition does not
            # hold now offers that condition as a sub-want — wanted as a means while the root stands, never a standing
            # claim (the wound law holds: the tally stays unclaimable. Balance 4t, 2026-11-16: the number line was
            # understood but not WANTABLE — sub_log empty in every run of two domains — and the blind walk stopped at the
            # plateau because the mind's known ways were conditioned on counts it had no way to want)
            und_, told_ = mind.understanding, mind.p.credulity
            now_ = set(self.facts_now())
            ways = sorted(((sum(e[0] + e[2] + told_ * e[1] for (rr, oo), e in und_.rel.get(c, {}).items()
                                if rr == "causes" and oo == self.goal), c)
                           for c in und_.rel if "_push:" in c and ("causes", self.goal) in und_.rel.get(c, {})),
                          reverse=True)
            for fund_, way in ways[:3]:
                if fund_ <= 0:
                    continue
                conds = sorted((e[0] + e[2] + told_ * e[1], o) for (rr, o), e in und_.rel.get(way, {}).items()
                               if rr == "conditioned_by" and not o.startswith("not:") and o not in now_)
                for seg in way.split("|")[1:]:   # a split half IS a way, its condition written in its own name
                    # ("attaching|tally_counting_1": the way, when the count is one) — the split read from its positive
                    # side. Found at x=2 (balance 4t): the lived conditions came out as no-halves (exclusions make no
                    # goals), while the yes-half stood in the web, a way with its needed state in its name, unread
                    if not seg.startswith("not_") and seg not in now_:
                        conds.append((fund_, seg))
                for cf, f in list(reversed(conds))[:2]:
                    if cf <= 0 or f in (self.goal, *self.stack) or f in self.failed_subs or not self.can_be(f):
                        continue
                    row_ = terr.rows.get(self.owner_of(f))
                    if row_ is None and mind.p.no_loss_wants and str(self.owner_of(f)).startswith(tuple(terr.__dict__.get("unclaimable") or ())):
                        continue   # (Params.no_loss_wants: a region no one's to claim, let go and holding no state now, is never a
                        # means in a state it isn't held in: zodiac's standing, let go between battles, offered standing_down, being
                        # behind, as a way's condition; 2026-11-21, trace_idle.py)
                    if row_ is not None and f not in (row_.get("held_states") or ()):   # a loss state of a held region is
                        continue   # never a means: the first run set subwant:post_0_giving_way_right — the cure's lived
                        # context — and the mind planned to RECREATE the problem to apply the known cure (break the
                        # balance to see the sign that says how to fix it). You do not wound yourself to use your healing
                    out.append(clause(f"subwant:{f}", tags=("condition", "subwant", f"region:{self.owner_of(f)}")))
        return out

    def own_subwant(self, rec):
        """A candidate that won the top level is set as a want: with no want held, it is the want (REORG step 4: goals arise from
        open slot instances, none placed; the user: humans map a game onto their own territorial motivations and play it through
        them); with one held, it is a sub-want, and the want it serves goes on the stack (as subwant() sets one)."""
        if self.watching or len(self.stack) >= 4:
            return
        now = self.facts_now()
        if self.mind.p.tie_superposition:   # tied top candidates: none set, both held as candidates until something separates them
            lv, m = rec["levels"][-1], self.mind
            L = len(rec["levels"]) - 1
            rank = lambda i: (round(lv["bids"].get(i, 0.0), 9), round(m.surprise(L, i, lv["res"].get(i)), 9), m.waited(i))
            cands = [i for i in lv["winners"] if i.startswith("subwant:")]
            cands = [i for i in cands if i[len("subwant:"):] not in now and i[len("subwant:"):] not in self.failed_subs
                     and i[len("subwant:"):] != self.goal and i[len("subwant:"):] not in self.stack]
            if len(cands) > 1:
                best = max(rank(i) for i in cands)
                if sum(rank(i) == best for i in cands) > 1:
                    self.__dict__.setdefault("tied_subs", []).append((m.t, sorted(i for i in cands if rank(i) == best)))
                    return
        for i in rec["levels"][-1]["winners"]:
            if i.startswith("subwant:"):
                f = i[len("subwant:"):]
                if f != self.goal and f not in self.stack and f not in now and f not in self.failed_subs:
                    if self.mind.p.no_loss_wants:   # never want your own loss (Params.no_loss_wants; the user's rule): a state of a region
                        row_ = self.mind.territory.rows.get(self.owner_of(f))   # that it was never held in isn't set as a want here,
                        if row_ is not None and ((row_.get("held_states") and f not in row_["held_states"])   # as the condition
                                                 or f in (row_.get("lost_states") or ())):
                            continue   # path's guard has it (first, the mind as Black set "plan_square_a2_unstoppable", their plan
                            #            made unstoppable, as its want: own_subwant's winners were never checked; 2026-11-21)
                    if self.goal is not None:
                        self.stack.append(self.goal)
                    self.goal, self.sub_since = f, self.mind.t
                    self.sub_log.append((self.mind.t, f, "set"))
                    if self.mind.p.decision_paths:
                        self.record_decision(f"want:{f}", rec, None, winner=i)
                    self.mind.pool.pop(i, None)
                    return

    def can_be(self, fact):
        """Whether a fact's object can hold it again: in the world now, or out of view and able to come back (world.returns). Only for
        worlds that say what returns; for the rest, as before (always). A need about an object gone for good is no want: no push can make it
        (the user, 2026-11-11; first a go mind's sub-wants were the sides of stones from a game long over, 13 of 18, none ever met)."""
        returns = getattr(self.world, "returns", None)
        if returns is None:
            return True
        obj = self.owner_of(fact)
        if obj not in self.seen_objs:   # never an object of the world (the mind's own doings): not this check's to judge
            return True
        return obj in self.world.states() or obj in returns

    def owner_of(self, fact):
        """The object a fact is about: the longest object name it starts with (the world's objects), else its stem."""
        objs = getattr(self.world, "objs", {}) or {}
        if getattr(self.world, "t", None) is None:   # a world with no slice count: nothing tells when its objects change
            return max((o for o in objs if fact.startswith(o + "_")), key=len, default=fact.rsplit("_", 1)[0])
        memo = self.__dict__.get("_owner_memo")   # remembered while the world's objects can't have changed: within one of its slices
        stamp = (self.world.t, id(objs), len(objs))   # (first every call scanned every object: 584,000 calls in 100 late slices; the count
        # too, and cleared after renew, for worlds that change their objects without moving the counter: a well or board set back)
        if memo is None or memo[0] != stamp:
            memo = self._owner_memo = (stamp, {})
        if fact not in memo[1]:
            memo[1][fact] = max((o for o in objs if fact.startswith(o + "_")), key=len, default=fact.rsplit("_", 1)[0])
        return memo[1][fact]

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

    def loses(self, fact):
        """With Params.no_loss_means: a fact that would be a loss of what the mind holds, so no means to anything (the user, 2026-11-13,
        "No loss as a means"): its region is one the register holds now, and the fact is another state of it. Read from the register, as
        the anti-want is. (First nothing checked: in go, with affords_chain, a way's needs were the whole board as it stood when the way
        last worked, and the mind set "a held point's opportunity alive" as a sub-want and filled its own eyes for it: go/trace_want.py.)"""
        if not self.mind.p.no_loss_means:
            return False
        r = self.owner_of(fact)
        if self.mind.territory.rows.get(r, {}).get("holder") != "mine":
            return False
        now = self.world.states().get(r)
        return now is not None and fact != f"{r}_{str(now).replace(' ', '_')}"

    def costly(self, inv, fact, root):
        """With Params.sub_cost: a push that, where it brought `fact` about, also moved the root want's object to a state
        other than the root want (it undoes what the means are for)."""
        if not self.mind.p.sub_cost or root is None:
            return False
        obj = self.owner_of(root)
        return any(any(self.owner_of(e) == obj and e != root for e in names)   # (the push's own rows, by the exact index: the same
                   for _f, names in self._by_inv(self.pushed, "_pushed_by_inv").get(inv, ()) if fact in names)   # answers)

    def undoes(self, inv, fact, keep):
        """With Params.sub_cost: a push that, where it brought `fact` about, also changed something the way it would serve
        needs and has (`keep`) to another state: it undoes the way. (First only the root want's object counted, and a
        mind wanting "e8 held" for the mate Rxe8 met it with Re8, the bishop taking the rook that was to mate: 201
        rooks; cognitive chess 1e.)"""
        if not self.mind.p.sub_cost or not keep:
            return False
        objs = {self.owner_of(k): k for k in keep}
        return any(any(self.owner_of(e) in objs and e != objs[self.owner_of(e)] for e in names)   # (the push's own rows, by the exact
                   for _f, names in self._by_inv(self.pushed, "_pushed_by_inv").get(inv, ()) if fact in names)   # index: first every push
        # ever was scanned per candidate and per maker, and a tetris slice at luck 0 ran over five hours in it, 2026-11-20)

    def _by_fact(self, rows, key):
        """fact -> {invitation: times} beside an append-only register — an exact index, same answers as the scan it replaces
        (2026-11-16: makers scanned pushed AND dreamed per call, and the planner calls it per candidate; with a grown imagination
        register one cleancode slice spun 3.5 hours in it, cleancode/rung2m/s8_hang_stack.txt, and warpchess waking slices paid it
        every tick at 125k rows). Extended from where it stands; rebuilt if the register shrank or was replaced."""
        ix = self.__dict__.get(key)
        if ix is None or ix[0] > len(rows):
            ix = self.__dict__[key] = [0, {}]
        n, by = ix
        for inv, _, names in rows[n:]:
            for f in names:
                d = by.setdefault(f, {})
                d[inv] = d.get(inv, 0) + 1
        ix[0] = len(rows)
        return by

    def _by_inv(self, rows, key):
        """invitation -> its rows' (facts, effects), in order, beside an append-only register (the same exact-index pattern)."""
        ix = self.__dict__.get(key)
        if ix is None or ix[0] > len(rows):
            ix = self.__dict__[key] = [0, {}]
        n, by = ix
        for inv, f, names in rows[n:]:
            by.setdefault(inv, []).append((f, names))
        ix[0] = len(rows)
        return by

    def defense_now(self, invs):
        """Params.defense_still: each push on offer's defense, the held regions waiting would lose less those the push would (the
        forces' world.effects_after), set on the mind as anti_defense for Mind.support (None where nothing differs)."""
        effects_after = getattr(self.world, "effects_after", None)
        self.mind.anti_defense = None
        if effects_after is not None and invs:
            terr = self.mind.territory
            held = {r for r, row in terr.rows.items() if row.get("holder") == "mine"}
            weigh = self.region_weigher()
            lose = lambda es: sum(weigh(r) for r in {self.owner_of(e) for e in es} & held)
            if self.mind.p.held_state_no_loss:   # a held region predicted to a state it is held in has lost nothing (Params.held_state_no_
                rows_h = terr.rows                # loss; 2026-11-22: the register a reading behind the world — "their plan via g2" held
                lose = lambda es: sum(weigh(r) for r in {self.owner_of(e) for e in es   # while the world read it stoppable — and every
                                                         if e not in (rows_h.get(self.owner_of(e), {}).get("held_states") or ())}
                                      & held)   # queen move that ended it, "plan_via_g2_none", felt as losing the region, 24 each)
            if self.mind.p.contested_losses:   # a contested region taken to a state it was never held in is lost too (Params.contested_
                rows_ = terr.rows               # losses; 2026-11-21: first only held regions counted, and Black's stalemate plan,
                held_lose = lose                # contested whenever a move of mine could make it, cost nothing when made: 61. Nxc7
                shown_ = getattr(self.world, "shown", None) or {}
                now_state = lambda e: f"{self.owner_of(e)}_{shown_.get(self.owner_of(e))}"   # (the region's state as the world shows it now)
                only = getattr(self.world, "contested_loss_regions", None)   # (the world may name which: chess, its draws, the game
                lose = lambda es: held_lose(es) + sum(weigh(r) for r in {self.owner_of(e) for e in es   # stalemated at +17)
                                                                         if rows_.get(self.owner_of(e), {}).get("holder") == "contested"
                                                                         and (only is None or self.owner_of(e) in only)
                                                                         and e not in (rows_[self.owner_of(e)].get("held_states") or ())
                                                                         and not (self.mind.p.held_state_no_loss and e == now_state(e))})
                # (Params.held_state_no_loss too: a contested region predicted to the state it is in now loses nothing; 2026-11-22: 24. c4
                #  read as leaving "their plan via g2" stoppable, as it already was, and felt as losing it, -24)
                # (2026-11-21: for every contested region, the opening's stoppable square plans made central moves feel like losses and
                #  the mind played 1...a5 2...g6 3...Ra7 for 1...e5 2...Qf6 3...Nc6; the user: "before ... it was taking the center")
            if self.mind.p.defense_gains:   # both sides count (Params.defense_gains): a lost or contested region brought back to a
                rows = terr.rows             # state it was held in is a gain against waiting
                regain = lambda es: sum(weigh(r) for r in {self.owner_of(e) for e in es
                                                           if rows.get(self.owner_of(e), {}).get("holder") in ("lost", "contested")
                                                           and e in (rows[self.owner_of(e)].get("held_states") or ())})
            else:
                regain = lambda es: 0
            gain_ = getattr(self.world, "is_gain", None) if self.mind.p.new_region_gains else None
            if gain_ is not None:   # (Params.new_region_gains: a predicted state the world names a gain, in a region not held now, is
                rows_g, regain_old = terr.rows, regain   # gained: first only a region held before could be brought back, and a new
                regain = lambda es: regain_old(es) + sum(weigh(r) for r in {self.owner_of(e) for e in es if gain_(e)}   # plan of the mind's
                                                         if rows_g.get(r, {}).get("holder") != "mine")   # own counted for nothing; 2026-11-21)
            w_ = effects_after(None)
            waiting = lose(w_) - regain(w_)
            defense = {}
            regions_ = {}   # (each push's predicted regions, kept for the move made: a lived loss blames it only where it made a difference)
            regains_ = {}   # (and the lost or contested regions each would bring back to a held state: Params.open_loss_blame)
            for c, inv in invs.items():
                e_ = effects_after(inv)
                defense[c] = waiting - (lose(e_) - regain(e_))
                if inv[0] not in ("commit", "ask"):
                    regions_[c] = frozenset(self.owner_of(x) for x in e_)
                    regains_[c] = frozenset(self.owner_of(x) for x in e_
                                            if terr.rows.get(self.owner_of(x), {}).get("holder") in ("lost", "contested")
                                            and x in (terr.rows[self.owner_of(x)].get("held_states") or ()))
            self._decision_regions = regions_
            self._decision_regains = regains_
            if self.mind.p.challenge_assumptions or self.mind.p.open_mindedness is not None:   # an assumption the tool tested: a told
                for c, gain in (self.__dict__.get("assumption_breaks") or {}).items():   # gain or loss, at credulity (Params.
                    # challenge_assumptions, Params.open_mindedness)
                    if c in invs:
                        defense[c] = defense.get(c, 0) + self.mind.p.credulity * gain
            if self.mind.p.improvement_territory:   # the meta-territory (Params.improvement_territory): an option that would end a way
                for c, gain in self.improvement_gains(invs).items():   # better than the best known is a predicted gain of it
                    defense[c] = defense.get(c, 0) + gain
                if self.mind.p.improvement_contests and self.mind.p.improvement_options:   # a line the mind imagined ending its way
                    for c, regions in (self.__dict__.get("imagined_bad") or {}).items():    # badly is also a predicted loss of the
                        if c in invs:                                                       # region itself, held or contested, at its
                            defense[c] = defense.get(c, 0) - sum(                           # weight (the user, 2026-11-21, "Loss of the
                                weigh(r) for r in regions                                   # road": zodiac's approved loss, "losing a
                                if terr.rows.get(r, {}).get("holder") in ("mine", "contested"))   # battle"; first only its pace regions, -3,
                                                                                            # against -2 for winning slowly)
                    if self.mind.p.imagined_regions:   # regions the mind's own imagined lines say an option keeps or loses (Params.
                        rows_ = terr.rows                 # imagined_regions; zodiac's wild_plan, the user, 2026-11-21: "Chess's three levels")
                        for c, preds in (self.__dict__.get("imagined_regions") or {}).items():
                            if c not in invs:
                                continue
                            for r, held_after in preds:
                                h_ = rows_.get(r, {}).get("holder")
                                if not held_after and h_ in ("mine", "contested"):
                                    defense[c] = defense.get(c, 0) - weigh(r)   # a stoppable plan made unstoppable: a loss
                                elif held_after and h_ == "lost":
                                    defense[c] = defense.get(c, 0) + weigh(r)   # an unstoppable one made stoppable: a gain
                    for c, (gained, lost_) in (self.__dict__.get("imagined_round") or {}).items():   # and the territory a line gains
                        if c in invs:                                    # and loses on the way, as the world's producer imagines it from
                            defense[c] = defense.get(c, 0) + gained - lost_   # the mind's record, in regions (expected counts; the
                            # user, 2026-11-21, "Weak points on the way": zodiac's weak points broken over the next round; first, with every
                            # line ending the same, the options tied and faithful_choice's tie-break brought up the switch every ~10 rounds)
            if any(defense.values()):
                self.mind.anti_defense = defense

    def region_weigher(self):
        """Params.region_weights: what a region weighs where the register sums what a push loses or brings back, as the world says
        (world.region_weight; the user, 2026-11-17, "include what it can reach": a piece's bearing weighs what the piece can reach); 1
        each otherwise, as before."""
        rw = getattr(self.world, "region_weight", None) if self.mind.p.region_weights else None
        return rw if rw is not None else (lambda r: 1)

    def stakes(self, invs):
        """Params.experimentation: what each push on offer would do to the register, as the forces predict it (world.effects_after):
        -1 for each held region it takes out of its held state, +1 for each lost or contested region it brings back to a state it was
        held in. -> {push id: net} (memoized per slice), or None where the world doesn't say what a push does."""
        ea = getattr(self.world, "effects_after", None)
        if ea is None or not invs:
            return None
        memo = self.__dict__.get("_stakes")
        if memo is not None and memo[0] == self.mind.t:
            return memo[1]
        rows = self.mind.territory.rows
        weigh = self.region_weigher()
        out = {}
        for c, inv in invs.items():
            net = 0
            for e in ea(inv):
                row = rows.get(self.owner_of(e))
                if not row:
                    continue
                held = row.get("held_states") or ()
                if row.get("holder") == "mine" and e not in held:
                    net -= weigh(self.owner_of(e))
                elif row.get("holder") in ("lost", "contested") and e in held:
                    net += weigh(self.owner_of(e))
            out[c] = net
        self._stakes = (self.mind.t, out)
        return out

    def yields(self, step, invs):
        """Params.experimentation: whether an experiment's step yields to what is at stake: the best push on offer better than the step
        (a push id, or "wait": nothing changes) by more than the mind's experimentation."""
        st = self.stakes(invs)
        if not st:
            return False
        if step != "wait" and "_push:" in step:   # a commitment's step: the stakes of the push it commits to (a commitment is on
            import re                              # offer itself and reads 0, changing nothing on the board: first read so, and an
            m_ = re.search(r"(\d+ [^_]+_push:.*)$", step)   # experiment committing to a move that left a knight hanging went ahead)
            step = m_.group(1) if m_ and m_.group(1) in st else step
        mine = 0 if step == "wait" else st.get(step, 0)
        return max(st.values()) - mine > self.mind.p.experimentation

    def within_reach(self, want):
        """Params.patience_reach: whether a push on offer leads to a want from here (read off the last slice's readings): a potential
        want, as own_candidates reads it (the forces' push_leads); a whole want, any of its parts; any other, a push on offer predicted
        to bring it (push_predicted), or one the record knows brings it (makers) that is on offer."""
        if want.startswith("all:"):
            return any(self.within_reach(x) for x in want[4:].split("&"))
        leads = self.__dict__.get("push_leads") or {}
        if want.startswith("potential:"):
            return any(want in v for v in leads.values())
        # (a region want: in reach only by a way the planner can take, a known maker on offer; first a push the forces predicted to
        # bring it counted too, and a want no lived way reached was held 400 slices, in reach by that reading, never stepping aside,
        # never planned for: the play app's stuck mind, trace_stuck_mind.py)
        offered ={inv_id(i) for i in self.world.invitations()} if hasattr(self.world, "invitations") else set(leads)
        return any(inv_id(i) in offered for i in self.makers(want))

    def explained(self, inv, want):
        """Params.explained_needs: the facts the mind's own record explains as needed for a push to bring a want: each held every
        time the push brought it, and was absent at least one time the push was made and the want didn't come (the contrast that
        separates a need from what merely held alongside). With one success and no contrast, nothing is explained: the rest is a
        conflation of what happened to hold, and stays unexplained until lived. -> frozenset (memoized by the record's length)."""
        rows = self._by_inv(self.pushed, "_pushed_by_inv").get(inv, [])
        memo = self.__dict__.setdefault("_explained_memo", {})
        key = (inv_id(inv), want)
        got = memo.get(key)
        if got is not None and got[0] == len(rows):
            return got[1]
        yes = [f for f, names in rows if want in names]
        no = [f for f, names in rows if want not in names]
        out = frozenset()
        if yes and no:
            both = frozenset.intersection(*(frozenset(f) for f in yes))
            out = frozenset(f for f in both if any(f not in g for g in no))
        memo[key] = (len(rows), out)
        return out

    def makers(self, fact):
        """The pushes that have brought a fact about, most often first: invitation -> times. With Params.dreams, after those lived,
        the ones that brought it in dreams (a way known only from a dream can give a sub-want; acted on, it becomes lived)."""
        out = dict(self._by_fact(self.pushed, "_pushed_by_fact").get(fact, {}))
        lived = sorted(out, key=lambda i: (-out[i], i))
        if not self.mind.p.dreams:
            return lived
        dreamt = {i: c for i, c in self._by_fact(self.dreamed, "_dreamed_by_fact").get(fact, {}).items() if i not in out}
        return lived + sorted(dreamt, key=lambda i: (-dreamt[i], i))

    def dreamed_modes(self, inv, facts):
        """Params.dreams: what the push did in dreams in the same reading as this situation (the imagination register).
        (Dropping the reading filter was tried for Params.dream_reach and measured a no-op — the planner's queried invs
        already passed it; 1,119 dream-answered steps, 0 rewarded, with and without. Reverted the same day; the switch
        lives in subwant instead: warpchess/PLAN.md, the dream's reach, 2026-11-16.)"""
        rows = self._by_inv(self.dreamed, "_dreamed_by_inv").get(inv, ())
        meta = self.mind.meta
        c = inv_id(inv)
        x = meta.reading_in(c, facts) if meta else c
        return [names for f, names in rows if (meta.reading_in(c, f) if meta else c) == x]

    def needs(self, inv, want):
        """What a push needs to bring a want: its configuration, and the conditions of the splits on it down to a half
        whose outcomes brought the want (yes halves only: a condition that must not hold is no want; with
        Params.polarity, it prevents the push, and its object as it stood where the want came is wanted)."""
        out = [f"{inv[1]}_{inv[2].replace(' ', '_')}"]
        if self.mind.p.affords_chain:   # and what enables it, on one way in: the nearest (fewest of its enablers not holding now), then
            by = self.__dict__.get("offered_ways", {}).get(inv_id(inv), {})   # the one lived most (Params.affords_chain)
            if by:
                now = self.facts_now()
                held, _ = min(by.values(), key=lambda w_: (len(w_[0] - now), -w_[1]))
                add = sorted(f for f in held if f not in out)
                if self.mind.p.explained_needs:   # only what the mind's own record explains (Params.explained_needs)
                    ex = self.explained(inv, want)
                    add = [f for f in add if f in ex]
                out += add
        meta, x = self.mind.meta, inv_id(inv)
        while x in meta.splits:
            sp = meta.splits[x]
            if sp.get("cands"):   # (Params.split_superposition) a condition still in superposition is not yet known to matter
                break
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

    @staticmethod
    def held(g, facts):
        """Whether a want holds in these facts: a want of a way whole (Params.ways_whole, "all:<a>&<b>") holds when every part does."""
        if g is None:
            return False
        parts = g[4:].split("&") if g.startswith("all:") else [g]
        return all(x in facts for x in parts)

    def subwant(self, facts, invs=None):
        """The nearer want for the current one (see above), or None; or ("try", invitation) when the situation never
        tried is the one that holds now: the push is made in it rather than another sub-want set (first, a combination
        made by sub-wants was skipped once it held, the next one set at once, and the push it was made for never came:
        the civilization ladder P7, one mind re-making its jar's states 55 times and never launching)."""
        goal = self.goal
        taken = set(self.stack) | {goal} | self.failed_subs
        root = self.stack[0] if self.stack else goal   # the want the sub-wants serve
        makeable = lambda f, keep=(): f not in taken and self.can_be(f) and not self.loses(f) and any(
            self.known.get(inv_id(i)) and not self.costly(i, f, root) and not self.undoes(i, f, keep)
            for i in self.makers(f))
        if goal is not None and goal.startswith("all:"):   # (Params.ways_whole) no line to the whole: a part, the one no push on offer
            parts = [x for x in goal[4:].split("&") if x not in facts and makeable(x)]   # here makes first (met here, it would be
            here = set(invs or ())                                                        # undone on the way to the others)
            parts.sort(key=lambda x: (any(inv_id(i) in here for i in self.makers(x)), x))
            return parts[0] if parts else None
        for inv in self.makers(goal):   # 1. a way known
            needs = self.needs(inv, goal)
            keep = [f for f in needs if f in facts]   # what the way needs and has now: a means must not undo it
            need = [f for f in needs if f not in facts]
            need = [f for f in need if makeable(f, keep)]
            need = list(dict.fromkeys(need))   # each need once (a push's configuration, its enablers and its splits' conditions can name
                                               # the same fact: first a tetris whole listed cell_2_17_carrying twice, and one need named
                                               # twice counted as two toward a whole)
            if need and self.mind.p.ways_whole and len(need) >= 2:   # the way's needs together: one want (Params.ways_whole)
                whole = "all:" + "&".join(sorted(need))
                if whole not in taken:
                    self.serving[whole] = keep
                    return whole
            if need:
                self.serving[need[0]] = keep
                return need[0]
            if (self.mind.p.dream_reach and not need
                    and inv not in self._by_inv(self.pushed, "_pushed_by_inv")):
                # Params.dream_reach (the user, 2026-11-16: "the dreams should be utilized effectively"): a way only
                # dreams know, standing with nothing left to need, is tried now — so it becomes lived (this method's
                # own intent: "a way known only from a dream can give a sub-want"). Before, it fell through silently:
                # nothing to sub-want, no funding to bid (the firewall), no root in the planner — 0 dream-rewarded
                # steps of 1,119 (warpchess/trace_dream_reach.py). Once pushed it is lived and never re-tried here.
                cur = next((v for v in (invs or {}).values() if inv_id(v) == inv_id(inv)), None)
                if cur is not None:
                    return ("try", cur)
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
        # the untried combination needing the fewest changes, each makeable (least key (len(need), need)), searched level by level:
        # combinations changing k objects, k = 1, 2, ..., stopping at the first level with an answer. The same answer as the product over
        # every combination it replaces (competency_rooms/checks/least_need.py: 0 mismatches in 20,000 random cases), which grew
        # exponentially in the objects: a tetris slice at luck 0 ran over five hours in it (2026-11-20)
        from itertools import combinations, product
        seen = {o: list(self.states_seen(o)) for o in objs}
        memo = {}
        ok = lambda f: memo[f] if f in memo else memo.setdefault(f, makeable(f))
        cur = {o: next((x for x in seen[o] if x in facts), None) for o in objs}
        alt = {o: [x for x in seen[o] if x not in facts and ok(x)] for o in objs}   # a changed object's state is needed, so makeable
        must = [o for o in objs if cur[o] is None]   # (first every state was tried, and with no answer anywhere every level was walked,
        if any(not alt[o] for o in must):            #  as exponential as the product: the same tetris slice stuck again, 2026-11-20)
            return None
        free = [o for o in objs if o not in must and alt[o]]
        for k in range(max(1, len(must)), len(must) + len(free) + 1):
            best = None
            for extra in combinations(free, k - len(must)):
                change = set(must) | set(extra)
                choices = [(alt[o] if o in change else [cur[o]]) for o in objs]
                for combo in product(*choices):
                    if frozenset(combo) in tried:
                        continue
                    need = [f for f in combo if f not in facts]
                    key = (len(need), need)
                    if best is None or key < best[0]:
                        best = (key, need)
            if best is not None:
                return best[1][0]
        return None

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
            if self.mind.p.dreams:   # nothing lived here: what it did in dreams, if anything
                modes = self.dreamed_modes(inv, frozenset(facts))
                return max(set(modes), key=lambda m: (modes.count(m), sorted(m))) if modes else None
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


def imagined_lines(model, s, roots, horizon=3, gamma=1.0):
    """Params.imagined_tournament (the user, 2026-11-06): planning as a train of thought over the agent's own model. Each
    move that won the top level now is imagined forward; at each imagined position the moves that win the mind's
    tournament there (Model.actions -> Model.attended) are each imagined in turn ("each winner"), to the horizon. The
    model is deterministic, so each line is imagined once; there is nothing to sample. -> (the first move of the line
    worth most, that line's worth), worth summed as mcts sums it (the reward at each step, discounted by gamma); ties
    go to the first root in bid order. (None, 0.0) if no move won the top level."""
    memo = {}   # (state, depth) -> worth: the model is deterministic within a plan, so each is worked out once (exact; 2026-11-19,
                # for Params.force_walks' horizon of the whole view, 4^12 lines otherwise)

    def worth(state, depth):
        if depth >= horizon:
            return 0.0
        if (state, depth) in memo:
            return memo[(state, depth)]
        best = 0.0
        for a in model.actions(state):
            nxt, r, _ = model.step(state, a)
            best = max(best, gamma ** depth * r + worth(nxt, depth + 1))
        memo[(state, depth)] = best
        return best
    out = (None, 0.0)
    idle = lambda nxt, r: r == 0 and frozenset(x for x in nxt if not x.startswith(("made:", "line:"))) ==         frozenset(x for x in s if not x.startswith(("made:", "line:")))
    for a in roots:
        nxt, r, _ = model.step(s, a)
        if model.agent.mind.p.lines_need_change and idle(nxt, r):   # it changes nothing and brings nothing: no line of its own
            continue
        v = r + worth(nxt, 1)
        if out[0] is None or v > out[1]:
            out = (a, v)
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

    # ---- Params.force_walks (the user, 2026-11-19): imagined walks along the side forces of ground seen -------------------------
    # The body stands where a location bears it (pos_x_y_bearing). Each side of that location the mind last perceived free has a force
    # on the location across it (the side_forces links): imagining the walk that way carries the body there. A want on a location is
    # met in imagination standing on it, or (seen free or blocking) standing where one of its sides' forces is on it: beside it, so in
    # view; a want on a city, standing on the location the city's force is on. My readings, named: the walk's push is named as the
    # world names it (walk_<heading>_push:<location>_free); these imagined walks are not filtered by the imagined tournament (a
    # walk never made has no reading to enter it with).

    @staticmethod
    def body_at(s):
        return next((x[:-len("_bearing")] for x in s if x.startswith("pos_") and x.endswith("_bearing") and x.count("_") == 3), None)

    def side_state(self, s, side):
        for st in ("free", "pressed"):
            if f"{side}_{st}" in s:
                return st
        return self.agent.__dict__.get("side_seen", {}).get(side)

    def forced(self, a):
        """The location a side's (or a city's) force is on, from the SOV's seen forces links."""
        return next((o for (r, o), e in self.agent.mind.understanding.rel.get(a, {}).items() if r == "forces" and e[0] > 0), None)

    def force_walk_actions(self, s):
        here, out = self.body_at(s), []
        for h in ("north", "east", "south", "west"):
            side = f"{here}_{h}"
            n = self.forced(side) if self.side_state(s, side) == "free" else None
            if n is not None and self.in_view(n):
                out.append(f"walk_{h}_push:{n}_free")
        return out

    def in_view(self, n):
        """The user, 2026-11-19 ("B"): the view bounds where the mind imagines walking, not how many steps: a location perceived now."""
        root = self.root[0] if self.root is not None else self.agent.facts_now()
        return any(f"{n}_{st}" in root for st in ("free", "bearing", "pressed"))

    def force_walk_reached(self, n):
        g = self.goal
        if g is None or g.startswith("all:"):
            return False
        o, st = g.rsplit("_", 1)
        if o.startswith("city_"):
            return self.forced(o) == n
        if not (o.startswith("pos_") and o.count("_") == 2):
            return False
        if st == "bearing":
            return n == o
        return n == o or any(self.forced(f"{n}_{h}") == o for h in ("north", "east", "south", "west"))

    def force_walk(self, s, a):
        here = self.body_at(s)
        h = a.split("_push:")[0][len("walk_"):]
        n = a.split("_push:", 1)[1].rsplit("_", 1)[0]
        side = f"{here}_{h}"
        if self.side_state(s, side) != "free" or self.forced(side) != n:
            return frozenset(x for x in s if not x.startswith("made:")), 0.0, None
        # the imagined state carries only what a walk changes: where the body stands, its travelling gerund, the turns so far (sides
        # are read from what was last perceived, side_seen, and where it may walk from the view, in_view). First the whole perceived
        # state, about a thousand facts, was copied at every imagined step: 5-9 s a planning slice (2026-11-20; exact: the same lines)
        body = next((x for x in s if x.startswith("body_")), None)
        turns = next((x for x in s if x.startswith("turns:")), None)
        nxt = {f"{n}_bearing", f"made:{a}"} | ({body} if body else set()) | ({turns} if turns else set())
        reached = self.goal in nxt or self.force_walk_reached(n)
        if not self.agent.mind.p.plan_discovery:
            return frozenset(nxt), (1.0 if reached else 0.0), None
        # Params.plan_discovery: the body's travelling gerund along the line, and how many times it changed (turns:<k>)
        g = f"body_travelling_{h}"
        k = next((int(x[6:]) for x in nxt if x.startswith("turns:")), 0)
        if g not in nxt:
            nxt = {x for x in nxt if not x.startswith(("body_", "turns:"))} | {g, f"turns:{k + 1}"}
            k += 1
        if not reached:
            return frozenset(nxt), 0.0, None
        total = self.agent.__dict__.get("trip_turns", 0) + k
        found = self.__dict__.setdefault("found", {})
        found[self.goal] = min(found.get(self.goal, total), total)
        best = self.agent.__dict__.get("route_best", {}).get(self.goal)
        return frozenset(nxt), 1.0 + (best - total if best is not None and total < best else 0.0), None

    def actions(self, s):
        if self.root is not None and s == self.root[0]:
            return sorted(c for c in self.root[1] if c in self.agent.known)
        if self.agent.mind.p.force_walks and self.body_at(s) is not None:
            return self.force_walk_actions(s)
        acts = self.candidates(s)
        if self.agent.mind.p.imagined_tournament:
            return self.attended(s, acts)
        return acts

    def candidates(self, s):
        """The moves that fit an imagined state: every known push whose configuration holds there."""
        return sorted(c for c, inv in self.agent.known.items() if f"{inv[1]}_{inv[2].replace(' ', '_')}" in s)

    def attended(self, s, acts):
        """Params.imagined_tournament: of the moves that fit an imagined state, those whose reading wins the top level of the
        mind's own tournament there (Mind.imagined_winners). The pool is the mind's as it stands, its want, questions and
        attention, with the moves on offer now taken out (they are offered in the present, not there) and these moves put
        in, each as the half of its splits the imagined facts select (as perceive() presents the half the present selects).
        A move already in the pool keeps its activation; one that isn't enters at 1.0, as perceive() presents an offer:
        its potential force is read off the board (potential.py), and an imagined position has no board. What is
        perceived there is these moves. Read once per state in a plan."""
        cache = self.__dict__.setdefault("_attended", {})
        facts = frozenset(x for x in s if not x.startswith(("made:", "line:")))
        if facts not in cache:
            mind, known, meta = self.agent.mind, self.agent.known, self.agent.mind.meta
            pool = {i: m for i, m in mind.pool.items() if "invitation" not in m.tags}
            reading = {}   # move -> the reading it enters as
            for c in acts:
                x = meta.reading_in(c, facts) if meta else c
                reading[c] = x
                if x in mind.pool:
                    pool[x] = mind.pool[x]
                else:
                    half = next((mol for sp in (meta.splits.values() if meta else ()) for mol in sp["mols"] if mol.id == x), None)
                    pool[x] = replace(half, act=1.0) if half is not None else clause(c, tags=("invitation", known[c][1]))
            won = set(mind.imagined_winners(pool, set(acts)))
            cache[facts] = [c for c in acts if reading[c] in won]   # in the model's order, as actions() gives it
        return cache[facts]

    def step(self, s, a):
        if self.costly(s, a):   # no means to a sub-want if it undoes the want the sub-want serves
            return frozenset(x for x in s if not x.startswith("made:")), 0.0, None
        if self.agent.mind.p.force_walks and a.startswith("walk_") and "_push:" in a and self.body_at(s) is not None:
            return self.force_walk(s, a)
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
        und = self.agent.mind.understanding
        # not understood: imagined from the board. With Params.dreams, a move whose conditions a dream has given structure counts as
        # understood (Understanding.open_structure) and is read from the mind's records and dreams instead: the mind's own understanding
        # answers where it can (README: understanding makes search unnecessary); the board answers only at the edge (the user, 2026-11-07)
        open_ = (und.funding(a, "conditions") < 1.0) if (p.plan_asks_world or not p.dreams) else ("conditions" in und.open_structure(a))
        # (Params.plan_asks_world, 2026-11-16: a dream's closure answers the dream's question, never the plan's — imagined
        #  structure closing this gate skipped 1,600 of 6,587 world questions per 60 slices and lost a third of the
        #  oracle's goal-findings; the D>C>A arm ordering's mechanism, warpchess/PLAN.md)
        if open_:
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

    def split(self, s):
        """A state's marks of what was made (made:<push>) and the state without them, each once per state (an exact speed-up, 2026-11-13:
        first both were rebuilt at every imagined step, up to five times in one, and in a Warp chess game, ~480 facts a state, 71% of a
        slice went to the imagined lines' steps, most of it here; py-spy, warpchess/rung4p.py)."""
        if not isinstance(s, frozenset):
            return {x[5:] for x in s if x.startswith("made:")}, frozenset(x for x in s if not x.startswith("made:"))
        memo = self.__dict__.setdefault("_split_memo", {})
        got = memo.get(s)
        if got is None:
            got = memo[s] = (frozenset(x[5:] for x in s if x.startswith("made:")), frozenset(x for x in s if not x.startswith("made:")))
        return got

    def recorded(self, s, a):
        inv = self.agent.known[a]
        und = self.agent.mind.understanding
        made, base_s = self.split(s)
        if any(("conditioned_by", f"not:{m}") in und.rel.get(a, {}) for m in made):
            # a preparation ruled out for this push (the state it made is not the one that works)
            return base_s, 0.0, None
        mode = self.agent.predict(inv, base_s)
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
                base = base_s
                if self.agent.mind.p.told_effects:   # nothing known of what it does, but that it was made (a told
                    return base | {f"made:{a}"}, r, None   # line can be read on from it)
                return base, r, None
        owners = und.owners
        objs = {o for o in owners.values()}
        nxt = set(base_s)
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
        hist = meta.modes.get(meta.reading_in(inv_id(inv), base_s), [])
        r = sum(1 for h in hist if self.goal in h[2]) / len(hist) if hist else (1.0 if self.goal in mode else 0.0)
        if hist and self.agent.mind.p.acted_on_conditions:   # a success counts where the conditions it was made under hold now
            here = base_s
            conds = {o for (rel, o), e in und.rel.get(inv_id(inv), {}).items() if rel == "conditioned_by" and e[0] > 0}
            r = sum(1 for h in hist if self.goal in h[2] and (conds & h[1]) <= here) / len(hist)
        if not hist and self.agent.mind.p.dreams:   # known only from dreams: believed at credulity, as imagined outcomes are
            dreamt = self.agent.dreamed_modes(inv, base_s)
            if dreamt:
                r = self.agent.mind.p.credulity * sum(1 for d in dreamt if self.goal in d) / len(dreamt)
        if told_r is not None:   # a told outcome is believed as far as the mind believes what it is told
            r = told_r
        if self.goal is not None and self.goal.startswith("all:"):   # (Params.ways_whole) the whole want: every part holding after
            r = 1.0 if self.agent.held(self.goal, nxt) else 0.0
        return frozenset(nxt), r, None

    def states_of(self, owner):
        """The gerunds an object has been perceived in (from the agent's perception log). Kept as the log grows, read
        on from where it was last read (first rescanned whole on every planner step: in a chess world a third of the
        run's time; the answer is the same)."""
        ix = self.agent.__dict__.setdefault("_states_ix", {"upto": 0, "seen": set(), "by": {}})   # every name prefix of every fact perceived
        hist = self.agent.history                                                             # -> its states, extended as the log grows
        if ix["upto"] < len(hist):   # (first each object scanned the whole log the first time it was asked about: 84 calls, 2.2 s, in one
            seen, by = ix["seen"], ix["by"]   # late tetris slice; a fact is an object's exactly when the object's name is one of its
            for facts, _ in hist[ix["upto"]:]:   # underscore prefixes, so the same answers)
                for x in facts:
                    if x in seen:
                        continue
                    seen.add(x)
                    k = x.find("_")
                    while k != -1:
                        by.setdefault(x[:k], set()).add(x[k + 1:])
                        k = x.find("_", k + 1)
            ix["upto"] = len(hist)
        return set(ix["by"].get(owner, ()))

    def expected(self, s, a):
        return self.step(s, a)[1]
