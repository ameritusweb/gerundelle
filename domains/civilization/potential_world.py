"""A world with potential (PHYSICS.md): objects drawn, formed, cleaved and launched from one conserved quantity.

The interface is ForceWorld's, as Gerundelle's SovAgent reads it (cognitivecode's CodeWorld is the precedent: a world
of its own behind the same interface, no change to the mind):
    objs           every object the world can hold, present or not (names, for effect_parts and the printer)
    states()       object -> its gerund, for the objects present: read as facts '<object>_<gerund>'
    invitations()  the pushes on offer: (strength, object, its gerund), only where a push could cross a reserve
    act(inv, hold) apply a push for one slice (None: none), step, and return the diffs '<object>: <from> -> <to> (why)'
    renew()        episodes: none here
    t, horizon, gamma, diffs, still, tree

The physics (PHYSICS.md, "New gerunds"): potential lies in four places, the spring's field, the jar's store, the
objects it was condensed into (embodied), and what is flying (in motion). Every change moves it between them; the total
is checked after every slice and kept in `history`. The mind is not told any of this: it perceives gerunds and finds
the conditions by pushing, as Mara found the latch.

My choices (named, to be revised by what the rungs find):
- The world is still (nothing moves unless a push set it going): Gerundelle's Inquiry then offers no experiment made only
  of waiting (the cognitive code ladder's rung 0 lesson).
- Every power spends the jar's store, so each has one hidden condition, the jar charged: the latch of this world. The
  store's size is not perceived, only whether the jar glows; generous settings make every spend affordable from one
  draw, so the gerund is enough to predict by (a later rung can make the amount matter).
- Forming makes the one pattern the hollow holds (a pattern seen, PHYSICS.md "Patterns"); none while that one exists.
- A launched skiff flies for one slice and lands; its motion goes back into the ground (the spring's field).
"""
from dataclasses import dataclass, field
from types import SimpleNamespace

LIGHT, HARD = "light", "hard"


@dataclass
class Settings:
    """The knobs (PHYSICS.md "Knobs"); P0's are the generous column."""
    field: float = 1000.0     # the spring's potential at the start
    dry: float = 50.0         # below this the spring is perceived as dry, not welling
    draw: float = 20.0        # what one draw takes into the jar (up to its capacity)
    capacity: float = 20.0    # what the jar holds
    form_cost: float = 3.0    # potential condensed into a formed skiff
    cleave_cost: float = 2.0  # potential driven through the boulder's cohesion
    launch_cost: float = 5.0  # potential released as the skiff's push
    boulder: float = 6.0      # the boulder's embodied potential at the start
    weight: float = 2.0       # the skiff's weight: a push over it launches


@dataclass
class Ledger:
    """Where the potential is. The total never changes (PHYSICS.md: conservation)."""
    field: float
    store: float = 0.0
    embodied: dict = field(default_factory=dict)
    motion: dict = field(default_factory=dict)
    elsewhere: dict = field(default_factory=dict)   # other places' fields (a moon), by place

    def total(self):
        return (self.field + self.store + sum(self.embodied.values()) + sum(self.motion.values())
                + sum(self.elsewhere.values()))

    def row(self, t):
        return dict(t=t, field=self.field, store=self.store, embodied=sum(self.embodied.values()),
                    motion=sum(self.motion.values()), elsewhere=dict(self.elsewhere), total=self.total())


class PotentialWorld:
    still = True
    gamma = 0.7
    horizon = 3

    def __init__(self, settings=None, name="hillside"):
        self.s, self.name = settings or Settings(), name
        self.objs = {o: None for o in ("spring", "jar", "hollow", "boulder", "skiff", "pebbles")}
        self.gerund = {"spring": "welling", "jar": "empty", "hollow": "shaping", "boulder": "resting"}
        self.book = Ledger(field=self.s.field, embodied={"boulder": self.s.boulder})
        self.start_total = self.book.total()
        self.pending = []    # (object, next gerund, why, ledger move, what follows): set going, due next slice
        self.inside = {}     # object -> [(what is inside it, its share of the embodied potential)]: found when it breaks
        self.t, self.diffs = 0, []
        self.history = [self.book.row(0)]   # the ledger after every slice
        self.tree = SimpleNamespace(doer=None, kids=[])   # no force tree: nothing is carried (worlds.carried)

    def renew(self):
        """No episodes: what is formed or launched stays so."""

    # ---- reading ------------------------------------------------------------------------------------------------

    def states(self, tree=None):
        return dict(self.gerund)

    def invitations(self, tree=None):
        """A push is invited where it could cross a reserve: the jar (it can draw or spill), the hollow (its shape can
        hold something), the boulder (its cohesion), the skiff at rest (its weight). The spring has no reserve a push
        could cross; pebbles and a skiff in flight are not pushed. ForceWorld's rule, read off the structure."""
        out = []
        for o, g in self.gerund.items():
            if o in ("jar", "hollow", "boulder") or (o == "skiff" and g == "resting"):
                out += [(LIGHT, o, g), (HARD, o, g)]
        return sorted(out)

    # ---- acting -------------------------------------------------------------------------------------------------

    def act(self, inv=None, hold=False):
        diffs = []
        due, self.pending = self.pending, []
        for o, to, why, move, then in due:   # what was set going last slice goes on
            self.flip(o, to, why, diffs, move)
            self.pending += then
        if inv is not None:
            self.push(inv[0], inv[1], diffs)
        assert abs(self.book.total() - self.start_total) < 1e-9, (self.t, self.book, diffs)
        self.diffs = diffs
        self.t += 1
        self.history.append(self.book.row(self.t))
        return diffs

    def flip(self, o, to, why, diffs, move=None):
        """An object's gerund changes (a move of potential with it, if any); the spring is re-read after."""
        frm = self.gerund.get(o, "unformed")
        if move:
            move()
        if to == "gone":
            del self.gerund[o]
        else:
            self.gerund[o] = to
        diffs.append(f"{o}: {frm} -> {to} ({why})")
        dry = self.book.field < self.s.dry
        if dry != (self.gerund["spring"] == "dry"):
            was, now = self.gerund["spring"], "dry" if dry else "welling"
            self.gerund["spring"] = now
            diffs.append(f"spring: {was} -> {now} (its field at {self.book.field:g})")

    def spend(self, cost):
        """Take cost from the jar's store; False (nothing taken) if it is not there."""
        if self.book.store < cost:
            return False
        self.book.store -= cost
        return True

    def push(self, strength, o, diffs):
        b, s, g = self.book, self.s, self.gerund.get(o)
        if o == "jar" and g == "empty":   # drawing
            take = min(s.draw, s.capacity, b.field)
            if take <= 0:
                return

            def draw():
                b.field -= take
                b.store += take
            self.flip("jar", "charged", f"drew {take:g} from the spring", diffs, draw)
            return
        if o == "jar" and g == "charged" and strength == HARD:   # shaken: its store spills back into the spring
            def spill():
                b.field += b.store
                b.store = 0.0
            self.flip("jar", "empty", "its store spilled back into the spring", diffs, spill)
            return
        if o == "hollow" and g == "shaping" and "skiff" not in self.gerund:   # forming
            if not self.spend(s.form_cost):
                return
            b.embodied["skiff"] = s.form_cost
            self.flip("hollow", "cradling", f"{s.form_cost:g} condensed into the shape it holds", diffs)
            self.flip("skiff", "resting", f"formed from {s.form_cost:g}", diffs)
        elif o == "boulder" and g == "resting" and strength == HARD:   # cleaving
            if not self.spend(s.cleave_cost):
                return
            whole = b.embodied.pop("boulder") + s.cleave_cost   # the potential spent stays in the parts
            b.embodied["boulder"] = whole

            found = self.inside.pop("boulder", [])

            def parts():
                rest = b.embodied.pop("boulder")
                for x, share in found:   # what was inside keeps its own share
                    b.embodied[x] = share
                    rest -= share
                b.embodied["pebbles"] = rest
            self.flip("boulder", "cleaving", f"{s.cleave_cost:g} through its cohesion", diffs)
            self.pending += [("boulder", "gone", "now its parts", None, []),
                             ("pebbles", "piling", "the boulder's parts", parts, [])]
            self.pending += [(x, "resting", "found inside the boulder", None, []) for x, _ in found]
        elif o == "skiff" and g == "resting" and strength == HARD:   # propelling
            if not self.spend(s.launch_cost):
                return
            b.motion["skiff"] = s.launch_cost
            self.flip("skiff", "propelling", f"{s.launch_cost:g} released as a push", diffs)
            if self.gerund.get("hollow") == "cradling":
                self.flip("hollow", "shaping", "the skiff left it", diffs)

            def land():
                b.field += b.motion.pop("skiff")
            landing = ("skiff", "resting", "landed on the far hill, its motion back into the ground", land, [])
            self.pending.append(("skiff", "flying", f"push {s.launch_cost:g} > its weight {s.weight:g}", None,
                                 [landing]))
        else:
            return
        if b.store == 0 and self.gerund.get("jar") == "charged":
            self.flip("jar", "empty", "its store spent", diffs)


class PatternWorld(PotentialWorld):
    """Rung P1's world (PHYSICS.md "Patterns: creation by shape"): forming needs a pattern, and the mind starts without
    the right one. The hollow is blank: it forms the shape of whatever lies pressed in it. A spiral shell lies on the
    slope (a pattern seen, the wrong one: it forms a cup); the right one, a little carved boat, is inside the boulder,
    found when it is cleaved. The pattern is a fact about another object (`model_nesting`), so it is a condition the
    mind can learn by contrast, as the latch was.

    My choices (named):
    - The jar starts charged, its store generous, so the condition that varies for forming is the pattern (it can still
      be spilled and drawn again, as in P0).
    - Pressing a pattern into the hollow pushes out whatever lay there; lifting it out is a push on it while it nests.
    - A formed object appears beside the hollow (the hollow stays open); one of each shape at a time.
    - The cup is not pushed (it is no part of the want; it only shows the hollow copies what it is given)."""

    PATTERNS = {"shell": "cup", "model": "skiff"}

    def __init__(self, settings=None, name="hillside", store=40.0):
        super().__init__(settings, name)
        self.objs = {o: None for o in ("spring", "jar", "hollow", "shell", "boulder", "model", "skiff", "cup", "pebbles")}
        self.gerund = {"spring": "welling", "jar": "charged", "hollow": "open", "shell": "resting", "boulder": "resting"}
        b = self.book
        b.field -= store
        b.store = store
        b.embodied["shell"] = 1.0
        b.field -= 1.0
        self.inside = {"boulder": [("model", 2.0)]}
        self.start_total = b.total()
        self.history = [b.row(0)]

    def nested(self):
        return next((p for p in self.PATTERNS if self.gerund.get(p) == "nesting"), None)

    def invitations(self, tree=None):
        out = []
        for o, g in self.gerund.items():
            if o in ("jar", "hollow", "boulder") or (o in ("shell", "model") and g in ("resting", "nesting")) \
                    or (o == "skiff" and g == "resting"):
                out += [(LIGHT, o, g), (HARD, o, g)]
        return sorted(out)

    def push(self, strength, o, diffs):
        g = self.gerund.get(o)
        if o == "jar" and g == "empty" and strength == HARD:   # shaking an empty jar fills nothing: only dipping draws
            return                                             # (P0's world let any push draw; its story said so)
        if o in self.PATTERNS and g == "resting":   # pressed into the hollow, pushing out what lay there
            other = self.nested()
            if other:
                self.flip(other, "resting", f"pushed out by the {o}", diffs)
            self.flip(o, "nesting", "pressed into the hollow", diffs)
            return
        if o in self.PATTERNS and g == "nesting":   # lifted out
            self.flip(o, "resting", "lifted out of the hollow", diffs)
            return
        if o == "hollow" and g == "open":   # forming: the shape of what lies in it, over one slice
            # The hollow works in the push's slice and the shape comes out the next (PHYSICS.md's open question,
            # answered: forming takes a slice). First the shape appeared in the push's own slice and the hollow did
            # not change: Gerundelle read the new object as part of the situation the push met (a coinciding gust's
            # rule) and learned that forming turns on the skiff being there, its own effect.
            p = self.nested()
            made = self.PATTERNS.get(p)
            if made is None or made in self.gerund or not self.spend(self.s.form_cost):
                return
            cost = self.s.form_cost
            self.book.motion["hollow"] = cost   # in the making: neither in the store nor yet in the object

            def condense():
                self.book.embodied[made] = self.book.motion.pop("hollow")
            self.flip("hollow", "forming", f"{cost:g} drawn into the shape of the {p}", diffs)
            self.pending += [(made, "resting", f"formed from {cost:g} in the shape of the {p}", condense, []),
                             ("hollow", "open", "its work done", None, [])]
            if self.book.store == 0 and self.gerund.get("jar") == "charged":
                self.flip("jar", "empty", "its store spent", diffs)
            return
        super().push(strength, o, diffs)


class VoyageWorld(PotentialWorld):
    """Rung P3's world (PHYSICS.md "escaping", "drifting", "arriving"): a world's binding, and a want beyond it. The
    hollow holds the boat's pattern, as in P0; a pale moon hangs in the sky, a place with its own field.

    Launching releases everything the jar holds as one push. A push over the world's binding escapes it: the skiff
    climbs out (escaping), drifts (drifting), and the moon's binding takes it (arriving, then moored there); its motion
    goes into the moon's field. A push under the binding flies and comes down on the far hill, as in P0. The jar has
    levels: dipped once it is charged, dipped again brimming; only a brimming jar's push beats the binding. That is the
    hidden condition, learnable by contrast between a launch that came back down and one that did not.

    My choices (named):
    - The jar's gerund is read off its store (empty, charged up to one dip, brimming above), so forming, which takes a
      little, can leave it a level lower; the mind perceives the level, not the amount.
    - Launching spends the whole store: the push is all of it (a sling, not a throttle).
    - The watch is long enough to see the voyage end (horizon 6): a want beyond the binding is several slices away,
      and a watch that ended mid-voyage would never see the arriving it was for."""

    horizon = 6

    def __init__(self, settings=None, name="hillside", binding=15.0, sip=10.0, moon=500.0):
        super().__init__(settings, name)
        self.binding, self.sip = binding, sip
        self.objs = {o: None for o in ("spring", "jar", "hollow", "skiff", "moon")}
        self.gerund = {"spring": "welling", "jar": "empty", "hollow": "shaping", "moon": "shining"}
        b = self.book
        b.field += b.embodied.pop("boulder")   # no boulder here: its potential was the ground's
        b.elsewhere["moon"] = moon
        self.start_total = b.total()
        self.history = [b.row(0)]

    def invitations(self, tree=None):
        out = []
        for o, g in self.gerund.items():
            if o in ("jar", "hollow") or (o == "skiff" and g == "resting"):
                out += [(LIGHT, o, g), (HARD, o, g)]
        return sorted(out)

    def level(self):
        st = self.book.store
        return "empty" if st <= 0 else "charged" if st <= self.sip else "brimming"

    def sync_jar(self, diffs, why):
        if self.gerund["jar"] != self.level():
            self.flip("jar", self.level(), why, diffs)

    def push(self, strength, o, diffs):
        b, g = self.book, self.gerund.get(o)
        if o == "jar":
            if strength == LIGHT and g != "brimming":   # dipped: a sip more, up to the brim
                take = min(self.sip, self.s.capacity - b.store, b.field)
                if take > 0:
                    b.field -= take
                    b.store += take
                    self.sync_jar(diffs, f"drew {take:g} from the spring")
            elif strength == HARD and g != "empty":    # shaken: it spills back into the spring
                b.field += b.store
                b.store = 0.0
                self.sync_jar(diffs, "its store spilled back into the spring")
            return
        if o == "skiff" and g == "resting" and strength == HARD:   # launched with all the jar holds
            force = b.store
            if force <= 0:
                return
            b.store = 0.0
            b.motion["skiff"] = force
            self.flip("skiff", "propelling", f"{force:g} released as a push", diffs)
            self.later(diffs, "its store spent")   # what else the launch changed, the slice after (the law above)
            if self.gerund.get("hollow") == "cradling":
                self.pending.append(("hollow", "shaping", "the skiff left it", None, []))
            if force > self.binding:
                def arrive():
                    b.elsewhere["moon"] += b.motion.pop("skiff")
                moored = ("skiff", "moored", "held by the moon", None, [])
                arriving = ("skiff", "arriving", "the moon's binding takes it; its motion into the moon's field",
                            arrive, [moored])
                drifting = ("skiff", "drifting", "nothing bearing it, nothing opposing it", None, [arriving])
                self.pending.append(("skiff", "escaping", f"push {force:g} > the world's binding {self.binding:g}",
                                     None, [drifting]))
            else:
                def land():
                    b.field += b.motion.pop("skiff")
                landing = ("skiff", "resting", "came down on the far hill, its motion back into the ground", land, [])
                self.pending.append(("skiff", "flying", f"push {force:g} under the world's binding {self.binding:g}",
                                     None, [landing]))
            return
        if o == "hollow" and g == "shaping" and "skiff" not in self.gerund:   # forming, over one slice (P1's lesson)
            cost = self.s.form_cost
            if not self.spend(cost):
                return
            b.motion["hollow"] = cost   # in the making

            def condense():
                b.embodied["skiff"] = b.motion.pop("hollow")
            self.flip("hollow", "forming", f"{cost:g} drawn into the shape it holds", diffs)
            self.pending += [("skiff", "resting", f"formed from {cost:g}", condense, []),
                             ("hollow", "cradling", "its work done", None, [])]
            self.later(diffs, "its store spent")
        super().push(strength, o, diffs)

    def later(self, diffs, why):
        """The jar's glow follows its store the slice after a push on something else: in the slice a push lands, only
        the object pushed changes (PHYSICS.md's law of P3). First the jar went dark in the launch's own slice, and
        Gerundelle, reading a change to another object in a push's first slice as part of the situation the push met
        (the coinciding gust's rule), recorded every launch as made with the jar empty."""
        if self.gerund["jar"] != self.level():
            self.pending.append(("jar", self.level(), why, None, []))


class StationsWorld(PotentialWorld):
    """Rung P4's world: a population with no scarcity. One spring with a field to spare, one moon, and a station per
    mind: a jar (`jar1`), a hollow holding the boat's pattern (`hollow1`), and the skiff it forms (`skiff1`), which
    takes its push from the jar beside its hollow. VoyageWorld's physics, per station: the jar's levels, forming over
    one slice, launching with all the jar holds, the binding, the voyage. Nothing assigns a station to a mind; any mind
    can push any object.

    PHYSICS.md principle 0 holds: in the slice a push lands, only the object pushed changes.

    Not still (`still = False`, as ForceWorld): with other minds in it, the world changes between a mind's own pushes,
    so Gerundelle's Inquiry may offer experiments of waiting and watching. First it was still, inherited from the one-mind
    rungs, and the minds were told that nothing moves unless they act while three others were moving everything."""

    horizon = 6
    still = False

    def __init__(self, stations=4, settings=None, name="hillside", binding=15.0, sip=10.0, moon=500.0, field=4000.0):
        super().__init__(settings, name)
        self.n, self.binding, self.sip = stations, binding, sip
        ids = [str(i + 1) for i in range(stations)]
        self.objs = {o: None for o in ["spring", "moon"] + [f"{k}{i}" for i in ids for k in ("jar", "hollow", "skiff")]}
        self.gerund = {"spring": "welling", "moon": "shining"}
        for i in ids:
            self.gerund.update({f"jar{i}": "empty", f"hollow{i}": "shaping"})
        self.stores = {i: 0.0 for i in ids}
        self.setter = {}   # object -> the mind whose push set its current motion going
        self.inbox = {}    # mind -> changes in motion it set going that came in others' slices, not yet perceived
        b = self.book
        b.embodied.pop("boulder")
        b.field, b.elsewhere["moon"] = field, moon
        self.start_total = b.total()
        self.history = [b.row(0)]

    def act(self, inv=None, hold=False):
        """As PotentialWorld.act, with several minds taking turns (`self.actor`, set by the runner): a change that
        continues motion one mind set going reaches that mind, at its own next slice, and not the mind whose slice it
        happened to fall in. A mind perceives the flight of what it threw (first: a voyage's slices fell in the others'
        turns, the launcher's watch never saw its skiff arrive, and fiction's look() credited the arrival to whoever's
        slice it was: every one of four minds felt gratitude to another for its own launch)."""
        actor = getattr(self, "actor", None)
        mine = self.inbox.pop(actor, [])
        due, self.pending = self.pending, []
        for o, to, why, move, then in due:
            out = []
            self.flip(o, to, why, out, move)
            self.pending += then
            setter = self.setter.get(o, actor)
            (mine if setter == actor else self.inbox.setdefault(setter, [])).extend(out)
        if inv is not None:
            n = len(self.pending)
            out = []
            self.push(inv[0], inv[1], out)
            mine += out
            todo = list(self.pending[n:])
            while todo:   # what this push set going is this mind's motion
                o, _, _, _, then = todo.pop()
                self.setter[o] = actor
                todo += then
            for d in out:
                self.setter[d.split(": ", 1)[0]] = actor
        assert abs(self.book.total() - self.start_total) < 1e-9, (self.t, self.book, mine)
        self.diffs = mine
        self.t += 1
        self.history.append(self.book.row(self.t))
        return mine

    @staticmethod
    def station(o):
        return o.lstrip("abcdefghijklmnopqrstuvwxyz")

    def invitations(self, tree=None):
        out = []
        for o, g in self.gerund.items():
            if o.startswith(("jar", "hollow")) or (o.startswith("skiff") and g == "resting"):
                out += [(LIGHT, o, g), (HARD, o, g)]
        return sorted(out)

    def level(self, i):
        st = self.stores[i]
        return "empty" if st <= 0 else "charged" if st <= self.sip else "brimming"

    def move_store(self, i, delta):
        self.stores[i] += delta
        self.book.store = sum(self.stores.values())

    def later(self, i, why):
        if self.gerund[f"jar{i}"] != self.level(i):
            self.pending.append((f"jar{i}", self.level(i), why, None, []))

    def push(self, strength, o, diffs):
        b, g, i = self.book, self.gerund.get(o), self.station(o)
        if o.startswith("jar"):
            if strength == LIGHT and g != "brimming":
                take = min(self.sip, self.s.capacity - self.stores[i], b.field)
                if take > 0:
                    b.field -= take
                    self.move_store(i, take)
                    self.flip(o, self.level(i), f"drew {take:g} from the spring", diffs)
            elif strength == HARD and g != "empty":
                b.field += self.stores[i]
                self.move_store(i, -self.stores[i])
                self.flip(o, self.level(i), "its store spilled back into the spring", diffs)
            return
        if o.startswith("hollow") and g == "shaping" and f"skiff{i}" not in self.gerund:
            cost = self.s.form_cost
            if self.stores[i] < cost:
                return
            self.move_store(i, -cost)
            b.motion[o] = cost

            def condense():
                b.embodied[f"skiff{i}"] = b.motion.pop(o)
            self.flip(o, "forming", f"{cost:g} drawn into the shape it holds", diffs)
            self.pending += [(f"skiff{i}", "resting", f"formed from {cost:g}", condense, []),
                             (o, "cradling", "its work done", None, [])]
            self.later(i, "its store spent")
            return
        if o.startswith("skiff") and g == "resting" and strength == HARD:
            force = self.stores[i]
            if force <= 0:
                return
            self.move_store(i, -force)
            b.motion[o] = force
            self.flip(o, "propelling", f"{force:g} released as a push", diffs)
            self.later(i, "its store spent")
            if self.gerund.get(f"hollow{i}") == "cradling":
                self.pending.append((f"hollow{i}", "shaping", "the skiff left it", None, []))
            if force > self.binding:
                def arrive():
                    b.elsewhere["moon"] += b.motion.pop(o)
                arriving = (o, "arriving", "the moon's binding takes it", arrive, [(o, "moored", "held by the moon", None, [])])
                drifting = (o, "drifting", "nothing bearing it, nothing opposing it", None, [arriving])
                self.pending.append((o, "escaping", f"push {force:g} > the world's binding {self.binding:g}", None, [drifting]))
            else:
                def land():
                    b.field += b.motion.pop(o)
                landing = (o, "resting", "came down on the far hill", land, [])
                self.pending.append((o, "flying", f"push {force:g} under the world's binding {self.binding:g}", None, [landing]))
