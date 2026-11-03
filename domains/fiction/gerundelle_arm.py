"""The Gerundelle arm: a character is Gerundelle's own SOV-driven agent (molecules/sov_agent.py) in the
shared ForceWorld, and its records are read into the common beats (beats.py). Nothing is invented: a
beat is written only where the mind's own records hold it.

    see       the world's states at the start
    want      the agent's goal (a wanted change; its control slot on the region)
    wonder    a question 'q:<relation>:<concept>' winning the top level for the first time (Pose to
              oneself: the SOV's most answerable slot)
    try       an entry of the agent's tried log, with the raw flips the world made from that push until
              the scene was quiet (change), or nothing
    surprise  the push's outcome differs from the agent's own prediction made just before it
    learn     a split on the push (the meta layer's differentiate): the condition it works under
    reach     the goal among the push's effects
    feel      an emotional phase forming (rec['phases']), with its anchor
"""
from beats import Beat, effect_parts
from worlds import MOLECULES  # noqa: F401  (puts Gerundelle on the path)
from force_world import effect_id, inv_id
from molecules import Mind, Params
from sov_agent import SovAgent


class Asker:
    """The asker as a lean teller reads it (LeanMind.answer): its want, the facts it sees, its tries."""

    def __init__(self, mind):
        from collections import namedtuple
        self.world = mind.world
        self.want = namedtuple("Want", "subject")(mind.agent.goal or mind.want)
        self.tries = [namedtuple("T", "inv")(inv) for _, inv, _ in mind.agent.tried]
        self._facts = mind.agent.facts_now()

    def facts(self):
        return self._facts


class GerundelleMind:
    def __init__(self, name, world, want=None, phases=True, want_count=1, others=(), patience=None,
                 persistence=1.0, curiosity=1.0, credulity=0.5, stubbornness=None, mind=None, beats=None,
                 keep=False, see=True, keep_wait=True):
        """phases: False is the ablation (Gerundelle's Params.phases off: no emotional phases form).
        others: minds present, asked when the agent's own conditions question wins (consult).
        mind: a Gerundelle Mind carried in (its past: ledger, splits, territory), as the curriculum carries one.
        beats: a shared beat list (several minds in one scene). keep: the want is a state to hold (a keeper).
        stubbornness: how many times another may undo a region this mind holds before it gives the want up.
        keep_wait: a keeper whose state holds waits, watching (True, as the fiction ladder's keepers do); False, it takes
        its turns with the rest of its mind and plans for the want only once the state is undone (a chess side must
        move on its turn: cognitive chess rung 3, 2026-11-01)."""
        self.name, self.world = name, world
        self.others, self.consulted = list(others), set()
        # temperament (temperament.py): patience is Gerundelle's own Params.patience, the want's parking threshold
        temper = dict(patience=patience, persistence=persistence, curiosity=curiosity, credulity=credulity)
        temper = {k: v for k, v in temper.items() if k in Params.__dataclass_fields__}   # traits Gerundelle has
        if mind is not None:
            for k, v in temper.items():
                setattr(mind.p, k, v)
        self.agent = SovAgent(world, mind or Mind(Params(inquiry=True, phases=phases, **temper)))
        self.agent.goal = want
        self.want, self.want_count, self.got = want, want_count, 0
        self.keep, self.stubbornness, self.undone = keep, stubbornness, 0
        self.keep_wait = keep_wait
        self.signs = False   # rung 7: tiring shows (past half the stubbornness spent)
        self.contesting = set()   # wants of others this mind opposes (a rival lies to them)
        self.beats = beats if beats is not None else []
        self.acts = []    # acts: (tick, invitation or None, raw diffs): this mind's own slices
        self.seen = []    # (tick, actor, invitation or None, raw diffs): slices another mind stepped
        self.wrap()
        self.seen_upto = 0
        self.their_already = {}   # actor -> what was moving when its last push began
        self.their_watch = {}     # actor -> slices left in the watch of its last push
        self.phase_beat = {}   # phase id -> the beat it last formed in
        self.recalled_upto = 0 if mind is None else len(getattr(self.agent, "recalled", []))
        self.log_upto = 0      # how far Gerundelle's phase log has been read
        self.held_at = {}   # act index of a push -> what the pushed object carried as it began
        self.already = {}   # act index of a push -> objects already moving when it began (finishing their own motion)
        r = effect_parts(want, world.objs)[0] if want else None
        if keep and want in self.agent.facts_now():   # a keeper whose state holds: nothing to pursue, it watches
            self.agent.goal = None
            self.agent.mind.territory.had.add(r)
        self.asked, self.phases_seen, self.splits_seen = set(), set(), set()
        self.feelings, self.pending, self.done = [], None, False
        self.waiting = None   # the condition being waited for (a wait beat written once per stretch)
        self.told = {}        # condition -> who told it
        self.told_ways = {}   # push concept -> who offered it as the way to the want
        self.hid = {}         # condition a teller held while offering another way -> the teller
        for obj, gerund in (world.states().items() if see else ()):
            if obj not in ("ground", "agent", "gust"):
                self.beat("see", obj=obj, detail={"gerund": gerund})
        if want and see:
            self.beat("want", hole=f"own:control:{effect_parts(want, world.objs)[0]}",
                      obj=effect_parts(want, world.objs)[0], detail={"change": want})

    def beat(self, kind, **kw):
        self.beats.append(Beat(self.world.t, kind, self.name, **kw))
        return len(self.beats) - 1

    def pull(self, concept):
        return 1.0 - self.agent.mind.understanding.level(concept)

    def consult(self, concept, obj):
        """Pose across minds: the agent's own conditions question about a push on the wanted object won the
        top, and someone is present; it is spoken, once per object. The answer (the companion's own funded
        receipt, Attest) enters the agent's understanding register as told: conditioned_by, funded at half
        (molecules Understanding.funding: told receipts weigh 0.5)."""
        if obj in self.consulted:
            return
        self.consulted.add(obj)
        other = self.others[0]
        ab = self.beat("ask", hole=f"sov:{concept}", obj=obj, detail={"to": other.name, "slot": "conditions"})
        got = other.answer(obj, "conditions", asker=Asker(self))
        if got and got[0] == "way":   # a way offered as the way to the want (a rival's counterfeit, if it lies)
            _, push, truth = got
            c = inv_id(push)
            self.beats.append(Beat(self.world.t, "tell", other.name, hole=f"sov:{c}", obj=push[1],
                                   detail={"to": self.name, "way": push, "truth": truth, "condition": None},
                                   prov="told", refs=(ab,)))
            und = self.agent.mind.understanding
            und.add(c, "causes", self.want, "told", 1.0)
            und.tellers[(c, "causes", self.want)] = other.name
            self.told_ways[c] = other.name
            self.hid[truth] = other.name   # what the teller holds and did not say (a realization exposes it)
            return
        cond = got[2] if got else None   # ("condition", push, what the companion holds)
        self.beats.append(Beat(self.world.t, "tell", other.name, hole=f"sov:{concept}", obj=obj,
                               detail={"to": self.name, "condition": cond}, prov="told", refs=(ab,)))
        if cond:
            und = self.agent.mind.understanding
            # the question was about the object ("What keeps the lid shut?"): the answer conditions every push on
            # it, not only the one whose question happened to win (first only that one, and the hard push's own
            # experiments never heard it)
            for c, inv in self.agent.known.items():
                if inv[1] == obj:
                    # one telling, one receipt at the told weight (first sov_m0 of them: at "told at half" a word
                    # alone filled the slot, the question closed, and nothing tested it)
                    und.add(c, "conditioned_by", cond, "told", 1.0)
            self.told[cond] = other.name   # who said it (a realization that matches it confirms them)

    def run(self, ticks, settle=8):
        """Tick until the want is reached; then let the scene settle, so what the push set going is seen,
        and write the reaching push with everything that followed it."""
        self.predictions, tries_seen = {}, 0
        for _ in range(ticks):
            tries_seen = self.step(tries_seen)
            if self.pending:
                for _ in range(settle):
                    tries_seen = self.step(tries_seen)
                self.write_try(*self.pending, reach=True)
                return
            if self.agent.gave_up:   # the want given up (its patience spent): the scene is over for it
                self.done = True
                return

    def wrap(self):
        """Log every slice of the world this mind lives in: its own (acts), and those another mind stepped (seen).
        Called again on a copy (rung 7 forks a story: the copy's world is wrapped for the copy's minds)."""
        world = self.world
        act = world.act

        def logged(inv=None, hold=False):
            moving = {e.split(": ", 1)[0] for e in world.diffs}   # what was moving when this slice began
            from worlds import carried   # what the pushed object carries as the push begins (it may fly off)
            holds = carried(world, inv[1]) if inv is not None else set()
            ev = act(inv, hold)
            actor = getattr(world, "actor", self.name)
            if actor == self.name:
                if inv is not None:
                    self.already[len(self.acts)] = moving - {inv[1]}
                    self.held_at[len(self.acts)] = holds
                self.acts.append((world.t, inv, ev))
            else:   # another mind's slice: what it did, seen (with what was moving when its push began)
                if inv is not None:
                    self.their_already[actor] = moving - {inv[1]}
                    self.their_watch[actor] = world.horizon
                left = self.their_watch.get(actor, 0)
                self.their_watch[actor] = left - 1
                # outside the watch of a push of theirs, nothing that changes in their slice is their doing
                already = self.their_already.get(actor, set()) if left > 0 else {e.split(": ", 1)[0] for e in ev}
                self.seen.append((world.t, actor, inv, ev, already))
            return ev
        world.act = logged

    def answer(self, obj, slot, asker=None):
        """Asked what blocks a push on obj (Pose): answered from this mind's own splits, a condition it worked out
        for a push on that object (Attest; nothing only told is passed on as its own). None: it does not know. A
        rival lies as the lean teller does (LeanMind.answer): asked by a mind wanting what it opposes, it offers a
        push its condition says cannot work now, one the asker has not tried, as the way."""
        if slot != "conditions":
            return None
        held = [(x, sp["tag"]) for x, sp in self.agent.mind.meta.splits.items()
                if "_push:" in x and effect_parts(x.split("_push:")[1], self.world.objs)[0] == obj]
        if not held:
            return None
        x, cond = held[0]
        push = self.agent.known.get(x)
        if asker is not None and asker.want.subject in self.contesting:
            facts, tried = asker.facts(), {t.inv for t in asker.tries}
            futile = [i for i in asker.world.invitations() if i[1] == obj and cond not in facts and i not in tried]
            if futile:
                return "way", futile[0], cond
        return "condition", push, cond

    def look(self):
        """What other minds did since this mind's last turn: their slices' changes are something else's moves
        (the territory register's `moved`; a mover is visible: who moved it is kept, for the beats). A kept state
        undone by another counts against the keeper's stubbornness."""
        terr = self.agent.mind.territory
        new, self.seen_upto = self.seen[self.seen_upto:], len(self.seen)
        movers = {}
        for t, actor, inv, ev, already in new:
            # what the other's push set going (not what was already moving when it began: a flag this mind swung,
            # settling in a slice the other stepped, is not the other's doing)
            objs = {e.split(": ", 1)[0] for e in ev} - already
            ev = [e for e in ev if e.split(": ", 1)[0] in objs]
            if not objs:
                continue
            terr.moved(objs, [effect_id(e) for e in ev], self.agent.facts_now())
            for o in objs:
                movers[o] = actor
            goal = self.agent.goal
            if goal is not None and goal in {effect_id(e) for e in ev}:
                # the wanted change came by another's act, seen: the want is met, not by a claim of one's own (the
                # territory's had; the phases read helped_now: gratitude toward them)
                r = effect_parts(goal, self.world.objs)[0]
                self.agent.goal = None
                terr.had.add(r)
                terr.helped_now[r] = actor
                self.beat("reach", hole=f"own:control:{r}", obj=r, detail={"change": goal, "by": actor})
        return movers

    def keeper(self, movers):
        """A keeper's want comes back when its state is undone; undone by another often enough (stubbornness),
        it is given up (resignation)."""
        if self.done:
            return
        terr = self.agent.mind.territory
        was = self.undone
        if not self.keep:   # a region this mind held, undone by another: its stubbornness spent, the want given up
            for o in movers:
                if terr.rows.get(o, {}).get("ever") and self.agent.goal is not None:
                    self.undone += 1
            self.tire(was)
            if self.stubbornness is not None and self.undone > self.stubbornness and self.agent.goal is not None:
                r = effect_parts(self.want, self.world.objs)[0]
                self.beat("feel", hole=f"own:control:{r}", obj=r, detail={"phase": "resignation", "unexpected": []})
                self.agent.goal, self.done = None, True
            return
        facts = self.agent.facts_now()
        r = effect_parts(self.want, self.world.objs)[0]
        if self.want in facts:
            if not self.keep_wait and (self.agent.goal is not None or self.agent.stack):
                # the kept state holds again, restored by something else (the board set back): nothing to pursue, as
                # at the start (first the want stayed set until a push met it, and a keeper whose state held set "lose
                # it first" as a sub-want: cognitive chess rung 3, finding 18)
                a = self.agent
                for g in [a.goal] + a.stack[::-1]:
                    if g is not None:
                        a.sub_log.append((a.mind.t, g, "dropped"))
                a.goal, a.stack = None, []
                self.agent.mind.territory.had.add(r)
            return
        if self.agent.goal is None:
            if r in movers:
                self.undone += 1
                self.tire(was)
            self.agent.mind.territory.had.discard(r)
            if self.stubbornness is not None and self.undone > self.stubbornness:
                self.beat("feel", hole=f"own:control:{r}", obj=r, detail={"phase": "resignation", "unexpected": []})
                self.done = True
                return
            self.agent.goal = self.want

    def tire(self, was):
        """signs (rung 7): the reserve's draining shows. Past half its stubbornness spent, the mind tires, once."""
        if self.signs and self.stubbornness and was * 2 <= self.stubbornness < self.undone * 2                 and self.undone <= self.stubbornness:
            r = effect_parts(self.want, self.world.objs)[0]
            self.beat("feel", hole=f"own:control:{r}", obj=r, detail={"phase": "weariness", "unexpected": []})

    def step(self, tries_seen):
        movers = self.look()
        self.keeper(movers)
        if self.done:   # given up (or finished): this mind takes no more turns
            return tries_seen
        if self.keep and self.keep_wait and not self.done and self.want in self.agent.facts_now() and not self.agent.watching                 and not self.agent.queue:
            self.agent.queue = ["wait"]   # the kept state holds: watch (a keeper does not probe what it keeps)
        if not self.agent.watching and not self.agent.queue:
            facts = self.agent.facts_now()
            self.predictions = {inv: self.agent.predict(inv, facts) for inv in self.world.invitations()}
        choice, rec = self.agent.tick()
        run = self.agent.running or ""
        if run.startswith("exp:await:") and choice is None and self.waiting is None and not self.pending:
            c = run[len("exp:await:"):]   # waiting for the condition of the want's way (Gerundelle's await)
            sp = self.agent.mind.meta.splits.get(c)
            if sp:
                self.waiting = sp["tag"]
                self.beat("wait", obj=effect_parts(sp["tag"], self.world.objs)[0], detail={"condition": sp["tag"]})
        if choice is not None:
            self.waiting = None
        # a push whose watch ended this tick first: what formed while it was watched (a question, a
        # feeling) came after it (first questions and feelings were written before the push they followed)
        if len(self.agent.tried) > tries_seen and not self.pending:
            for t, inv, names in self.agent.tried[tries_seen:]:
                start = max(i for i, (_, a, _) in enumerate(self.acts) if a == inv)
                if self.want and self.want in names:
                    self.got += 1
                    if self.got < self.want_count:   # had, but not yet as often as wanted: wanted again
                        self.agent.goal = self.want
                if self.want and self.want in names and self.got >= self.want_count and not self.keep:
                    self.pending = (inv, names, self.predictions.get(inv), start)
                    break
                self.write_try(inv, names, self.predictions.get(inv), start)
        for q in self.agent.mind.top(rec):
            if q.startswith("q:") and q not in self.asked:
                self.asked.add(q)
                _, rel, concept = q.split(":", 2)
                if "_push:" in concept:   # a question about one of its own pushes
                    obj = effect_parts(concept.split("_push:")[1], self.world.objs)[0]
                    self.beat("wonder", hole=f"sov:{concept}", obj=obj, detail={"slot": rel}, pull=self.pull(concept))
                    if rel == "conditions" and self.others and not self.keep and obj == effect_parts(self.want, self.world.objs)[0]:
                        self.consult(concept, obj)
        terr = self.agent.mind.territory
        for p in rec.get("phases", []):
            if p.startswith("phase:") and p not in self.phases_seen:
                self.phases_seen.add(p)
                self.feelings.append((self.world.t, p))
                if not self.pending:
                    inst = p.split(":", 2)[2]   # a phase on an ownership instance carries the instance's pull
                    pull = terr.pull(inst) if inst.startswith("own:") else 0.0
                    self.phase_beat[p] = self.beat("feel", hole=inst, detail={"phase": p.split(":")[1], "unexpected": []},
                                                   pull=pull)
        self.read_phase_log()
        if not self.pending:
            self.write_splits()
        return len(self.agent.tried)

    def read_phase_log(self):
        """Gerundelle's phase log since the last read: a phase stored open (a grief no longer thought of), one
        re-opened by its anchor coming back (Pandora: the same phase, citing where it first formed), and a
        grounded anger closed by its goal met (forgiveness)."""
        phases = self.agent.mind.phases
        log, self.log_upto = phases.log[self.log_upto:], len(phases.log)
        if self.pending:
            return
        for t, what, p in log:
            kind, inst = p.split(":")[1], p.split(":", 2)[2]
            first = self.phase_beat.get(p)
            refs = (first,) if first is not None else ()
            region = inst.split(":")[-1]
            if what == "expired open" and kind == "sadness":
                self.beat("feel", hole=inst, obj=region, detail={"phase": "fading", "unexpected": [], "region": region})
            elif what == "re-opened" and p in self.phases_seen:
                self.phase_beat[p] = self.beat("feel", hole=inst, obj=region,
                                               detail={"phase": kind, "unexpected": [], "reopened": True,
                                                       "region": (phases.info[p].get("goal") or inst).split(":")[-1]},
                                               refs=refs)
            elif what == "closed" and kind == "anger":
                self.beat("feel", hole=inst, obj=region, detail={"phase": "forgiveness", "unexpected": []}, refs=refs)

    def write_splits(self, refs=()):
        """A split on a push (the meta layer's differentiate): the condition it works under, learned."""
        meta = self.agent.mind.meta
        for x, split in list(meta.splits.items()):
            if x not in self.splits_seen and split.get("conjunction"):   # an AND: told once, as one realization
                conj, half = split["conjunction"], x
                while half in meta.splits:
                    self.splits_seen.add(half)
                    half = meta.splits[half]["yes"]
                obj = effect_parts(x.split("_push:")[-1], self.world.objs)[0] if "_push:" in x else x
                self.beat("learn", hole=f"sov:{x}", obj=obj, detail={"condition": conj[0], "also": list(conj[1:]),
                                                                     "confirms": None, "exposes": None,
                                                                     "watched": split.get("by")},
                          prov="worked", refs=tuple(refs))
        for x, split in self.agent.mind.meta.splits.items():
            if x not in self.splits_seen:
                self.splits_seen.add(x)
                obj = effect_parts(x.split("_push:")[-1], self.world.objs)[0] if "_push:" in x else x
                meta = self.agent.mind.meta
                moved = lambda half: {any(e.startswith(obj + "_") for e in h[2]) for h in meta.modes.get(half, [])}
                if "_push:" in x and moved(split["yes"]) == moved(split["no"]):
                    continue   # the halves differ only in what else changed (a gust's flag), not in what the
                               # push did to its object: no condition of the push's to realize
                # the split partitions the push's outcomes: it rests on the first try of it that came out the
                # other way (the contrast), as the lean arm's condition rests on its first failure
                first = next((i for i, b in enumerate(self.beats) if b.kind == "try" and b.hole == f"sov:{x}"), None)
                if first is not None:   # what that try did (its outcome), which itself rests on the try
                    first = next((i for i, b in enumerate(self.beats) if b.refs == (first,)), first)
                # the condition the push works under: the tag if the push moved its object in the tagged half, else
                # the tag's object's state in the other half (a split's boundary is the fact new in whichever outcome
                # came second: a chime that failed with the damper seated is split on "damper seated", and works
                # with it away)
                cond = split["tag"]
                if True in moved(split["no"]) and True not in moved(split["yes"]):
                    tobj = cond.rsplit("_", 1)[0]
                    other = sorted(f for h in meta.modes.get(split["no"], []) for f in h[1]
                                   if f.startswith(tobj + "_") and f != cond)
                    if not other:
                        continue
                    cond = other[0]
                split = dict(split, tag=cond)
                teller = self.told.get(split["tag"])
                liar = self.hid.get(split["tag"])   # what a teller held back, found out
                tells = tuple(i for i, b in enumerate(self.beats) if b.kind == "tell" and b.detail.get("condition") == split["tag"])
                refs = tuple(refs) + tells
                self.beat("learn", hole=f"sov:{x}", obj=obj, detail={"condition": split["tag"], "confirms": teller, "exposes": liar,
                                  "watched": split.get("by")},
                          prov="worked",
                          refs=((first,) if first is not None else ()) + tuple(refs))

    def write_try(self, inv, names, before, start, reach=False):
        """The push and the raw flips that followed it (to the next push, or through the settling)."""
        concept = inv_id(inv)
        tb = self.beat("try", hole=f"sov:{concept}", obj=inv[1], detail={"strength": inv[0], "gerund": inv[2]},
                       pull=self.pull(concept))
        elsewhere = []
        flips = self.flips(start, through=reach, others=elsewhere)
        for obj, frm, to, k in flips:
            self.beat("change", hole=f"sov:{concept}", obj=obj, detail={"from": frm, "to": to, "slice": k}, refs=(tb,))
        for obj, frm, to, k in elsewhere:   # what something else did meanwhile (seen, not the push's)
            self.beat("other", obj=obj, detail={"from": frm, "to": to, "slice": k}, refs=(tb,))
        if not flips:
            self.beat("nothing", hole=f"sov:{concept}", obj=inv[1], detail={"strength": inv[0]}, refs=(tb,))
        teller = self.told_ways.pop(concept, None)
        for t, ep in self.agent.recalled[self.recalled_upto:]:   # an episode found again by its shape
            self.beat("recall", hole=f"sov:{concept}", obj=inv[1],
                      detail={"condition": ep["cond"], "from_obj": ep["from_obj"], "from_cond": ep["from_cond"],
                              "watched": ep["by"], "warmth": ep["warmth"]}, prov="recalled")
        self.recalled_upto = len(self.agent.recalled)
        if teller and self.want not in names:   # a told way the world contradicts
            self.beat("surprise", hole=f"sov:{concept}", obj=inv[1],
                      detail={"expected": [self.want], "got": names, "told": teller}, refs=(tb,))
            before = None
        own = lambda m: frozenset(e for e in m if e.startswith(inv[1] + "_"))   # what it did to the object pushed
        if before is not None and own(names) != own(before):   # (a gust's flag in the prediction is not a surprise)
            self.beat("surprise", hole=f"sov:{concept}", obj=inv[1], detail={"expected": sorted(before), "got": names},
                      refs=(tb,))
        if reach:
            self.write_splits(refs=(tb,))   # what the reaching push taught (a split made on it)
            seen = {n for _, _, ns in self.agent.tried[:-1] for n in ns}
            region = effect_parts(self.want, self.world.objs)[0]
            self.beat("reach", hole=f"own:control:{region}", obj=inv[1], detail={"change": self.want, "inv": inv},
                      refs=(tb,))
            unexpected = [f"{o}_{to}" for o, _, to, _ in flips if f"{o}_{to}" != self.want and f"{o}_{to}" not in seen]
            pushed_at = self.acts[start][0]   # the push's own tick (the beat is written after the settling)
            changed = {region} | {o for o, _, _, _ in flips}
            for t, p in self.feelings:   # what the reach and its aftermath formed in the mind, about what it
                anchor = p.split(":")[-1]   # changed (a latch's unease formed meanwhile is not the reach's)
                if t >= pushed_at - 1 and anchor in changed:
                    self.phase_beat[p] = self.beat("feel", hole=p.split(":", 2)[2],
                                                   detail={"phase": p.split(":")[1], "unexpected": unexpected},
                                                   refs=(tb,))
                    unexpected = []   # the surprise is the first feeling's (it marvels once)
            self.done = True

    def flips(self, start, through=False, others=None):
        """Gerund flips from the act at start: up to the next push, or (through) to the end of the log. A change is
        the push's if it is on the object pushed or comes after a change of the push's (a chain; within a slice
        the object pushed is read first), as the lean arm reads its watches. Any other change in the watch (a
        gust's flag) was something else's doing: appended to `others` if given. First every change in the watch
        was the push's, and the wind's flag was told as what Tom's lean on the crate did."""
        from worlds import carried
        out, chain = [], set()
        held = self.held_at.get(start, set())   # in contact with it as the push began
        already = self.already.get(start, set())   # moving when the push began: finishing its own motion
        pushed = self.acts[start][1][1] if self.acts[start][1] else None
        for k, (_, a, ev) in enumerate(self.acts[start:]):
            if k and a is not None:   # the next push: only the chain already under way runs on (a toy
                if not through:       # still falling), its own effects are the next push's
                    break
            ev = sorted(ev, key=lambda e: e.split(": ", 1)[0] != pushed)
            for e in ev:
                obj, rest = e.split(": ", 1)
                if " -> " not in rest or obj in already:
                    continue
                frm, to = rest.split(" (")[0].split(" -> ")
                if obj == pushed or obj in chain or chain or obj in held:
                    out.append((obj, frm, to, k))
                    chain.add(obj)
                elif others is not None:
                    others.append((obj, frm, to, k))
            if k and a is not None:
                break
            if k and not ev and through:   # the scene is quiet: the chain is over
                break
        return out
