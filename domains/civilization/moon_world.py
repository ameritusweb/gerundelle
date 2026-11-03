"""Rung P5's world (PHYSICS.md: unmaking, fusing, travel between two worlds): the moon, after P3's voyage.

The skiff lies moored on the moon; the moon is a place of its own, with its own field, sparse: its pool is nearly dry.
The rest of PHYSICS.md's gerunds, each moving potential between the places the ledger keeps:
- unmaking: an old husk, pushed hard, goes back whole into the moon's field (`husk: resting -> unmaking -> gone`), and
  the pool glimmers again. The only way to potential here.
- drawing (the flask from the pool, in levels, as the jar on the hill) and forming (the basin holds a lantern's pattern;
  the lantern is made from the moon's own field, through the flask).
- fusing: the lantern pushed hard onto the skiff joins it (`lantern: resting -> fusing -> gone`, `skiff: moored -> lit`):
  the lantern's potential and what the joining took from the flask become the skiff's own (embodied as `skiff_fused`).
- travel home: the skiff launched releases the flask's store as its push; the lantern fused into it lifts it (the
  binding on a lit skiff is the moon's less its fused store) and is not burned. Over the binding it escapes, drifts,
  and the home world takes it (`returning`, then `beached`), its motion into the home field; under it, it hops and
  falls back to its mooring (still lit, if it was), its motion into the moon's field.
The hidden condition of the way home is an AND: the skiff lit and the flask brimming (10 > 12 - 5; lit with the flask
only charged, 5, is not; unlit with it brimming, 10 against 12, is not).

PHYSICS.md principle 0 holds: in the slice a push lands, only the object pushed changes.
"""
from potential_world import HARD, LIGHT, PotentialWorld


class MoonWorld(PotentialWorld):
    horizon = 6

    def __init__(self, settings=None, name="moon", binding=12.0, sip=5.0, capacity=10.0, pool=2.0, husk=30.0,
                 lantern=3.0, fuse=2.0, home=1000.0):
        super().__init__(settings, name)
        self.binding, self.sip, self.cap, self.lantern_cost, self.fuse_cost = binding, sip, capacity, lantern, fuse
        self.objs = {o: None for o in ("pool", "flask", "basin", "husk", "skiff", "lantern")}
        self.gerund = {"pool": "dry" if pool < sip else "glimmering", "flask": "empty", "basin": "shaping",
                       "husk": "resting", "skiff": "moored"}
        b = self.book
        b.embodied = {"husk": husk, "skiff": 3.0}
        b.field, b.store = pool, 0.0      # here the field is the moon's (the pool)
        b.elsewhere = {"home": home}
        self.start_total = b.total()
        self.history = [b.row(0)]

    def flip(self, o, to, why, diffs, move=None):
        """As PotentialWorld.flip, without the hill's spring (the pool is re-read by `pool_later`)."""
        frm = self.gerund.get(o, "unformed")
        if move:
            move()
        if to == "gone":
            del self.gerund[o]
        else:
            self.gerund[o] = to
        diffs.append(f"{o}: {frm} -> {to} ({why})")

    # ---- what follows a push, the slice after (principle 0) ---------------------------------------------------

    def pool_later(self, why):
        now = "glimmering" if self.book.field >= self.sip else "dry"
        if now != self.gerund["pool"]:
            self.pending.append(("pool", now, why, None, []))

    def level(self):
        st = self.book.store
        return "empty" if st <= 0 else "charged" if st <= self.sip else "brimming"

    def flask_later(self, why):
        if self.gerund["flask"] != self.level():
            self.pending.append(("flask", self.level(), why, None, []))

    # ---- reading and acting ------------------------------------------------------------------------------------

    def invitations(self, tree=None):
        out = []
        for o, g in self.gerund.items():
            if o in ("flask", "basin") or (o in ("husk", "lantern") and g == "resting") or \
                    (o == "skiff" and g in ("moored", "lit")):
                out += [(LIGHT, o, g), (HARD, o, g)]
        return sorted(out)

    def push(self, strength, o, diffs):
        b, g = self.book, self.gerund.get(o)
        if o == "flask":
            if strength == LIGHT and g != "brimming":   # dipped in the pool
                take = min(self.sip, self.cap - b.store, b.field)
                if take > 0:
                    b.field -= take
                    b.store += take
                    self.flip("flask", self.level(), f"drew {take:g} from the pool", diffs)
                    self.pool_later("drawn from")
            elif strength == HARD and g != "empty":    # shaken: back into the pool
                b.field += b.store
                b.store = 0.0
                self.flip("flask", "empty", "its store spilled back into the pool", diffs)
                self.pool_later("spilled into")
            return
        if o == "husk" and g == "resting" and strength == HARD:   # unmaking: whole, back into the moon's field
            def unmake():
                b.field += b.embodied.pop("husk")
            self.flip("husk", "unmaking", "its cohesion let go", diffs)
            self.pending.append(("husk", "gone", "returned to the moon's field", unmake, []))
            if self.gerund["pool"] != "glimmering":
                self.pending.append(("pool", "glimmering", "the husk's potential came into it", None, []))
            return
        if o == "basin" and g == "shaping" and "lantern" not in self.gerund:   # forming a lantern from the flask
            if b.store < self.lantern_cost:
                return
            b.store -= self.lantern_cost
            b.motion["basin"] = self.lantern_cost

            def condense():
                b.embodied["lantern"] = b.motion.pop("basin")
            self.flip("basin", "forming", f"{self.lantern_cost:g} drawn into the shape it holds", diffs)
            self.pending += [("lantern", "resting", f"formed from {self.lantern_cost:g}", condense, []),
                             ("basin", "cradling", "its work done", None, [])]
            self.flask_later("its store spent")
            return
        if o == "lantern" and g == "resting" and strength == HARD and self.gerund.get("skiff") in ("moored", "lit"):
            if b.store < self.fuse_cost:   # fusing: the joining is paid from the flask
                return
            b.store -= self.fuse_cost
            b.motion["lantern"] = self.fuse_cost

            def join():   # the skiff's fused store: embodied in it, released at its launch
                add = b.embodied.pop("lantern") + b.motion.pop("lantern")
                b.embodied["skiff_fused"] = b.embodied.get("skiff_fused", 0.0) + add
            self.flip("lantern", "fusing", f"{self.fuse_cost:g} through the joining", diffs)
            self.pending += [("lantern", "gone", "now part of the skiff", join, [])]
            if self.gerund.get("skiff") != "lit":
                self.pending.append(("skiff", "lit", "the lantern fused into it", None, []))
            if self.gerund.get("basin") == "cradling":
                self.pending.append(("basin", "shaping", "the lantern left it", None, []))
            self.flask_later("its store spent")
            return
        if o == "skiff" and g in ("moored", "lit") and strength == HARD:   # launched with the flask's store
            # The fused lantern lifts: a lit skiff's binding is the moon's less what is fused into it, and the lantern
            # is not burned in the push (it stays embodied in the skiff, and goes home with it). First the launch
            # released the fused store with the flask's, so a hop burned the lantern: the first launch any mind made,
            # lit with the flask spent by the fusing, undid the whole preparation, and no mind got home.
            force = b.store
            if force <= 0:
                return
            fused = b.embodied.get("skiff_fused", 0.0)
            bind = self.binding - fused
            b.store = 0.0
            b.motion["skiff"] = force
            self.flip("skiff", "propelling", f"{force:g} released as a push", diffs)
            self.flask_later("its store spent")
            rest = "lit" if fused else "moored"
            if force > bind:
                def home():
                    b.elsewhere["home"] += b.motion.pop("skiff")
                beached = ("skiff", "beached", "on the hillside at home", None, [])
                returning = ("skiff", "returning", "the home world's binding takes it; its motion into the home field",
                             home, [beached])
                drifting = ("skiff", "drifting", "nothing bearing it, nothing opposing it", None, [returning])
                self.pending.append(("skiff", "escaping", f"push {force:g} > the binding on it {bind:g}",
                                     None, [drifting]))
            else:
                def fall():
                    b.field += b.motion.pop("skiff")
                back = ("skiff", rest, "fell back to its mooring, its motion into the moon's field", fall, [])
                self.pending.append(("skiff", "hopping", f"push {force:g} under the binding on it {bind:g}",
                                     None, [back]))
