"""The code mind: fiction's lean mind (fiction/lean.py) with one capability added for the courtship rung.

Asking the way to a condition (Pose, the causes question). A told condition can be on something the mind cannot push:
the pattern answers "the spec passes only if my left read is filled", and a role is not a slot. Fiction's subgoal
(LeanMind.subgoal) acts on the condition's own object, and with nothing to push there the mind waits, in a world
where nothing changes by itself. So, stuck on a condition it holds and cannot bring about by any push it has tried,
the mind asks someone present which push gives it. The teller answers from its own lived tries (a push whose watched
effects included the condition: Attest from receipts, as LeanMind.answer does for conditions); the answer enters told,
funded at half and scaled by the teller's record, and the mind acts on it. A push is said in shared words, the value
it fills with ('v2[v4]'), not by the teller's own ordering of its pushes.

A told way the world contradicts (the push made, the condition it was said to give not among its effects) is
retracted as LeanMind.act retracts a told way to the want: a retract receipt, the teller's record marked (reliability
falls), a surprise, anger anchored on the teller (Gerundelle's Phases: blame for a blocked want, grounded on the word
that failed; the phase does not know the teller's motive). A told way borne out confirms the teller.

In a still world (CodeWorld.still) a condition the mind cannot bring about by a push on its own object is searched
for, not waited for: fiction's subgoal waits for a condition something else moves (the wind's flag), and in a world
where nothing moves unless the mind acts, waiting never ends. The mind tries its best-valued push off the wanted object
instead, watching for the condition.

Credit to slots (OWNERSHIP_SOV.md sec. 5, integration step 4: credit goes to the (slot, action) pair). In code a claim
on a slot is made for the want, and the run is its test: when a run fails, the fill made just before it (the last
edit since the previous run, the one that changed the slot; fiction's "already moving is not mine") did not take,
whatever it changed: its hole gets a lived receipt that the spec still failed, and its region a failure. A fill's
claim is pending until a run: it does not take when it is made, only when a run passes with it in place. Fills
replaced before any run were never tested, and are neither credited nor failed. (First a fill took when made, and only
the one before a failed run was taken back: the untested ones piled up as held, credit then brought the slot's
strength to the base rate, and the slot read as lost, pulling at 1 + all it had held: 9, 11, 13 and rising, so the
mind searched the slot forever and never ran the answer it had put there; two of ten patterns' pasts never reached.) First any change to a slot counted
as a claim taking, and with the abstract value in the slot's state nearly every fill changed it: the slot was held at
once and the mind ran a failing spec hundreds of times (the rerun after rung 3's fix). A run that passes confirms the
fill. In a still world a run on a program unchanged since the last run is not offered: it can only repeat itself.

My choice, ported from the shape of LeanMind.consult (Pose carries the question's shape only; Attest only what is held
lived or worked out; what was only told is not passed on as one's own).
"""
import codeworld  # noqa: F401  (puts poc2 and fiction on the path)
from beats import Beat, effect_parts  # noqa: E402
import lean  # noqa: E402


def said(inv):
    """A push in shared words: its value, without a world's ordering prefix ('042 v2[v4]' -> 'v2[v4]')."""
    s = inv[0]
    return s.split(" ", 1)[1] if s[:3].isdigit() and " " in s else s


class CodeMind(lean.LeanMind):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.ways = {}   # condition -> (push, teller): a way to it, told
        self.held_way = None   # a keeper's way: the push in place when its past want was reached
        self.code_episodes = []   # scenes past: a condition learned on the run, with the shape of the way to it
        self.recalled = {}        # condition -> the episode it was recalled from

    def way(self):
        """A keeper's way is what held when its past want was reached, not the latest push that brought the kept
        state about (LeanMind.way): in a code world two fills can give one state, and only one of them passed (rung
        3: the item's past went through v5[v4:v4] to v5, the state unchanged by the second; the keeper fought with
        the junk)."""
        if self.held_way and self.want and self.want.closed is None:
            live = next((i for i in self.world.invitations() if (said(i), i[1]) == self.held_way), None)
            if live is not None:
                return live
        return super().way()

    def way_to(self, cond):
        """Attest: a push this mind made whose watched effects included cond (lived), as (said, object), or None."""
        hits = [x.inv for x in self.tries if cond in x.effects]
        return (said(hits[-1]), hits[-1][1]) if hits else None

    def ask_way(self, cond):
        askable = [o for o in self.others if hasattr(o, "way_to")]
        if not askable or (cond, "way") in self.asked:
            return
        self.asked.add((cond, "way"))
        other = askable[0]
        obj = effect_parts(cond, self.world.objs)[0]
        ab = self.beat("ask", obj=obj, detail={"to": other.name, "slot": "way", "condition": cond})
        got = other.way_to(cond)
        push = None
        if got is not None:
            push = next((i for i in self.world.invitations() if (said(i), i[1]) == got), None)
        if push is None:   # ignorant, or no such push here: its ignorance said with the question's shape
            self.beats.append(Beat(self.world.t, "tell", other.name, obj=obj,
                                   detail={"to": self.name, "condition": None, "way_to": cond}, prov="told", refs=(ab,)))
            return
        ok, n = self.trust.get(other.name, (0, 0))
        self.trust[other.name] = (ok, n + 1)
        h = self.effect_hole(push)
        self.beats.append(Beat(self.world.t, "tell", other.name, hole=h.id, obj=push[1],
                               detail={"to": self.name, "way_to": cond, "inv": push}, prov="told", refs=(ab,)))
        self.receipt(h.id, "causes", cond, "told", 2.0 * self.reliability(other.name))
        self.tellers[len(self.ledger) - 1] = other.name
        self.ways[cond] = (push, other.name)

    def subgoal(self, cond):
        known = [i for i in self.world.invitations() if any(cond in x.effects for x in self.tried(i))]
        if known:
            return known[-1]
        if cond not in self.ways:
            self.ask_way(cond)
        if cond in self.ways:
            push = self.ways[cond][0]
            live = next((i for i in self.world.invitations() if (said(i), i[1]) == (said(push), push[1])), None)
            if live is not None:
                self.trying_way = (cond, live)
                return live
        if cond in self.recalled:   # the way recalled by shape: values of that shape here, untried ones first
            shape = self.recalled[cond]["shape"]
            fits = [i for i in self.world.invitations() if i[1] != self.wanted() and self.shape_of(i) == shape
                    and not self.tried(i)]
            if fits:
                return max(fits, key=lambda i: (round(self.value(i), 9), i))
        sub = super().subgoal(cond)
        if sub is None and getattr(self.world, "still", False):   # search for it: nothing will bring it about but me
            wanted = effect_parts(self.want.subject, self.world.objs)[0] if self.want else None
            edits = [i for i in self.world.invitations() if i[1] != wanted]
            sub = max(edits, key=lambda i: (round(self.value(i), 9), -len(self.tried(i)), i)) if edits else None
        return sub

    # ---- episodes and recall by shape (fiction rung 6, LeanMind.end_scene / recall, in code's terms) ----------

    def shape_of(self, inv):
        return self.world.shape(inv[1], self.world._fills[inv[1]][inv[0]])

    def keep_episode(self):
        """At a scene's end: each condition learned on the run (lived or worked), kept by structure: the shape of the
        fill that brought it about (the value without its names, CodeWorld.shape), and what the condition was in
        structural terms, that this fill made its slot play a part in the pattern (its state names roles). Not the
        role's name: that belongs to the pattern of this scene (rung 5b: carried by name, the condition could never
        be met under another theory's pattern, and the code put the answer in place and never ran it)."""
        run = next(i for i in self.world.invitations() if i[1] == self.wanted())
        for cond, prov, _ in self.conditions(run, provs=("lived", "worked")):
            way = self.way_to(cond)
            if not way:
                continue
            label = next(lab for lab in self.world._fills[way[1]] if said((lab,)) == way[0])
            self.code_episodes.append(dict(cond=cond, shape=self.shape_of((label, way[1])), way=way[0],
                                           stored=self.world.t))

    @staticmethod
    def plays(state):
        """Whether a slot's state names roles in the pattern perceived ('none=...' and 'empty' do not)."""
        return not state.startswith(("none", "empty"))

    def recall(self, inv):
        """Stuck on the run, nothing held about what it needs: a warm episode (memory's h_site and cold, as fiction's)
        is found. What carries over is its way's shape, and that the way made its slot play a part in the pattern.
        The condition is mapped onto this scene by structure when it is seen (fiction rung 6 mapped the latch's
        condition onto the object now in the latch's gerund): a value of that shape tried here, making a slot play a
        part in whatever pattern this scene is perceived through, gives the condition in this scene's terms, held as
        recalled (funded at half: a hypothesis to test)."""
        from memory import COLD, H_SITE
        for ep in reversed(self.code_episodes):
            warmth = 0.5 ** ((self.world.t - ep["stored"]) / H_SITE)
            if warmth < COLD:
                continue
            self.mapping = dict(ep, run=inv)
            self.beat("recall", hole=self.effect_hole(inv).id, obj=inv[1],
                      detail={"condition": "the slot plays a part", "shape": ep["shape"], "from": ep["way"],
                              "warmth": round(warmth, 2)}, prov="recalled")
            return True
        return False

    def follow_recall(self):
        """With a recalled way not yet mapped: if the last push was a value of its shape and made its slot play a part,
        the condition is mapped (that slot's state, here); else the next untried value of the shape. None when the
        shape has nothing left to try (the recall gave out)."""
        ep = getattr(self, "mapping", None)
        if not ep:
            return None
        last = self.tries[-1] if self.tries else None
        if last is not None and last.inv[1] != self.wanted() and self.shape_of(last.inv) == ep["shape"]:
            state = self.world.states()[last.inv[1]]
            if self.plays(state):
                cond = f"{last.inv[1]}_{state}"
                h = self.effect_hole(ep["run"])
                self.receipt(h.id, "conditions", cond, "recalled", lean.M0)
                self.recalled[cond] = ep
                self.mapping = None
                self.beat("recall", hole=h.id, obj=ep["run"][1], detail={"condition": cond, "mapped": True},
                          prov="recalled")
                return None
        fits = [i for i in self.world.invitations() if i[1] != self.wanted() and self.shape_of(i) == ep["shape"]
                and not self.tried(i)]
        if not fits:
            self.mapping = None
            return None
        return max(fits, key=lambda i: (round(self.value(i), 9), i))

    # ---- a learned condition contradicted: Reopen ------------------------------------------------------------

    def conditions(self, inv, provs=("lived", "worked", "told", "recalled")):
        """LeanMind.conditions, without those retracted (a retract receipt on the same hole names them)."""
        h = self.holes.get(f"effect:{inv[0]}:{inv[1]}")
        gone = {self.ledger[i].value[len("retract:cond:"):] for i in (h.receipts if h else ())
                if self.ledger[i].slot == "conditions" and str(self.ledger[i].value).startswith("retract:cond:")}
        return [c for c in super().conditions(inv, provs)
                if c[0] not in gone and not str(c[0]).startswith("retract:")]

    def contradicts(self, x):
        """A run (own or seen) that failed with its learned condition met contradicts the condition: it is retracted,
        logged not erased, with a surprise (SOV_ALGEBRA.md, Reopen: the world contradicting a stored closure). Fiction
        never needed it: nothing there contradicted a learned condition. Here the spec changes (rung 4): the held fill
        fails with every lockstep role filled, and "the spec passes only if the roles are filled" kept the mind from
        ever running the new answer, which fills none (it put v2[v4:] in the slot and searched on)."""
        if x.inv[1] != self.wanted() or not self.want or self.want.subject in x.after:
            return   # not a run, or the spec passes after it (a passing use changes nothing: its effects are empty)
        for cond, prov, _ in self.conditions(x.inv, provs=("lived", "worked", "told", "recalled")):
            if cond in x.facts:
                h = self.effect_hole(x.inv)
                self.receipt(h.id, "conditions", f"retract:cond:{cond}", "lived", 0.0)
                self.beat("surprise", hole=h.id, obj=x.inv[1], detail={"expected": [self.want.subject],
                                                                     "got": list(x.effects), "belief": True,
                                                                     "condition": cond})

    # ---- inquiry, in a still world -------------------------------------------------------------------------

    def value(self, inv):
        """LeanMind.value, with inquiry suppressed for a push already tried under the facts as they stand, in a
        still world: "try it at another moment" assumes the moment can differ, and in a world where nothing changes
        unless the mind acts it cannot (rung 0, finding 3: about half the lone scanner's edits were such repeats).
        The work term is kept: a repeat is still valued by what it did and how much is unknown about it."""
        v = super().value(inv)
        if not getattr(self.world, "still", False):
            return v
        done = self.tried(inv)
        if not done or not any(x.facts == self.facts() for x in done):
            return v
        h = self.effect_hole(inv)
        probing = self.contested(inv[1])
        if not (self.ownership and (probing or "conditions" in self.terr.serve().get(inv, (0.0, ()))[1])):
            return v
        open_c = 1.0 if probing else 1.0 - min(1.0, self.funding(h, "conditions") / lean.M0)
        fresh = 1.0 - 0.5 ** ((self.world.t - done[-1].t) / lean.H0)
        same = sum(1 for x in done if x.facts == self.facts())
        q = lean.KAPPA * self.persistence
        inquiry = self.stakes(h) * open_c * fresh * lean.INQUIRY * q / (q + same)
        on_want = (self.want is not None and self.want.closed is None and (self.serves(h) or self.ownership)
                   and inv[1] == effect_parts(self.want.subject, self.world.objs)[0])
        return v - inquiry * (2.0 if on_want else 1.0)

    # ---- runs: the test of what is held ------------------------------------------------------------------

    def wanted(self):
        return effect_parts(self.want.subject, self.world.objs)[0] if self.want else None

    def stale(self, inv):
        """A run on a program unchanged since the last run, in a still world: it can only repeat itself."""
        if inv is None or inv[1] != self.wanted() or not getattr(self.world, "still", False):
            return False
        last = next((x for x in reversed(self.tries) if x.inv[1] == inv[1]), None)
        return last is not None and last.facts == self.facts()

    def plan(self):
        follow = self.follow_recall()
        if follow is not None:
            return follow
        p = super().plan()
        cond = self.learned(p) if p is not None else None
        if self.stale(p) and not (cond and cond not in self.facts()):
            return None   # a run with its condition unmet is not run (act turns to the condition): not stale
            # (rung 5: a failed run made the next look stale, plan gave nothing, and an unguided edit came first)
        return p

    def choose(self):
        """LeanMind.choose without stale runs. With test_pending, a fill in place and not yet tested is run before any
        other fill (a claim takes when it is tested, rung 4): in rung 6's space every program passes and every fill
        changes the body's roles, so each fill looked like work and the run, which only tests, was outbid; the codes
        swapped programs and almost never ran one. Off by default: rungs 0-5 were measured without it."""
        st = self.world.states()
        if (getattr(self, "test_pending", False) and self.tries and self.tries[-1].inv[1] != self.wanted()
                and st.get("match") != "taken" and not any(st.get(s) == "empty" for s in self.world.slots)):
            # nor while a slot is still empty: an unfilled program cannot pass, and forced runs on one spent the
            # code's patience before it was told the way it lacked (rung 7: the zip codes)
            # not when the code can see the flow is another's: then a run is a contest, chosen by value or not at all
            # (first it was forced, and identical codes fought over one flow until 19 of 20 had resigned)
            run = next((i for i in self.world.invitations() if i[1] == self.wanted()), None)
            if run is not None and not self.stale(run):
                return run
        invs = [i for i in self.world.invitations() if not self.stale(i)]
        if not invs:
            return None
        return max(invs, key=lambda i: (round(self.value(i), 9), -len(self.tried(i)), i))

    def register(self):
        """The territory register's claim record, as it stands (to put back after a fill)."""
        return {r: (dict((k, list(v)) for k, v in row["claims"].items()), row["fails"], row["failed"], row["ever"])
                for r, row in self.terr.rows.items()}

    def unclaim(self, before):
        """After a fill: its claims undone. A fill makes no claim on the register; only a run tests one (the user,
        2026-10-27: a slot is not tried until a run tests it, as it is not held until a run confirms it). The
        register was built for objects with two or three pushes; a slot has as many as its type has values, and
        counting every search fill as a tried claim diluted the confirmed ones (rung 4, reading B: strength 0.03-0.07
        against a base rate of 0.15 after five confirmed uses; the slot was never mine, so it could not be lost)."""
        for r, row in self.terr.rows.items():
            if r in before:
                row["claims"] = {k: list(v) for k, v in before[r][0].items()}
                row["fails"], row["failed"], row["ever"] = before[r][1], before[r][2], before[r][3]
            else:
                row["claims"], row["fails"], row["failed"], row["ever"] = {p: [0, 0] for p in row["claims"]}, 0, False, False
        self.terr.took_now.clear()
        self.terr.update()

    def credit(self):
        """After a run: the fill just before it (since the previous run) takes if the run passed, fails if not."""
        run = self.tries[-1]
        wanted = self.wanted()
        prev = self.tries[-2] if len(self.tries) > 1 else None
        if prev is None or prev.inv[1] == wanted:
            return   # nothing filled since the previous run
        row = self.terr.row(prev.inv[1])
        c = row["claims"].setdefault(prev.inv, [0, 0])
        c[0] += 1   # tried: a run tested it
        if self.want and self.want.subject in run.effects:
            c[1] += 1   # it took: the run passed with it in place
            row["fails"] = 0
            self.terr.took_now.add(prev.inv[1])
        else:
            row["fails"] += 1
            if row["ever"]:
                row["failed"] = True
            self.receipt(self.effect_hole(prev.inv).id, "causes", f"{self.want.subject}:not", "lived")
        self.terr.update()

    def act(self, max_watch=12):
        self.trying_way = None
        n = len(self.tries)
        before = self.register()
        out = super().act(max_watch)
        if len(self.tries) > n and self.tries[-1].inv[1] == self.wanted():
            self.contradicts(self.tries[-1])
            self.credit()
        elif len(self.tries) > n and self.want and self.want.closed is None:
            self.unclaim(before)   # a keeper's fills too (rung 4: skipped for keepers, its fills took when made,
            # held grew with every search fill, and grief's pull rose 5, 6, ... 21)
        if self.trying_way and len(self.tries) > n and self.tries[-1].inv == self.trying_way[1]:
            cond, inv = self.trying_way
            push, teller = self.ways[cond]
            names = self.tries[-1].effects
            h = self.effect_hole(inv)
            ok, n_told = self.trust.get(teller, (0, 0))
            tb = max(i for i, b in enumerate(self.beats) if b.kind == "try" and b.actor == self.name)
            if cond in names:   # borne out: the teller confirmed
                self.trust[teller] = (ok + 1, n_told)
            else:               # contradicted: retracted, logged not erased; the teller's record marked
                del self.ways[cond]
                self.receipt(h.id, "causes", f"retract:told:{teller}", "lived", 0.0)
                self.beat("surprise", hole=h.id, obj=inv[1], detail={"expected": [cond], "got": list(names),
                                                                     "belief": False, "told": teller}, refs=(tb,))
                if self.phases and f"other:{teller}" not in self.angry:
                    self.angry.add(f"other:{teller}")
                    self.beat("feel", hole=f"other:{teller}", obj=teller,
                              detail={"phase": "anger", "unexpected": []}, refs=(tb,))
        return out
