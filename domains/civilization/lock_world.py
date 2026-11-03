"""Rung P9's world: StationsWorld with locks (possession as physics; FORCE_VOCABULARY.md's `locking`: holds against a
push until released).

Each station's jar has a lid (`lid1`). A push on an open lid shuts it, and the lid takes the hand that shut it: shut, it
opens only to that hand's push; anyone else's push on it does nothing. A shut jar cannot be dipped or spilled by anyone,
its keeper included (the keeper opens it first); it still feeds its hollow and its skiff through the lid (those are the
station's mechanism, not a hand).

My choice (named): the lock is bound to the actor who set it, read off the runner's `world.actor`, as StationsWorld
already keeps who set each motion going. To a mind this is perceived as it should be: a shut lid that does not open for
me; a jar that fills only when its lid is open (a condition its keeper can learn by contrast).

PHYSICS.md principle 0 holds: in the slice a push lands, only the object pushed changes. Conservation is untouched:
a lid holds no potential.
"""
from potential_world import HARD, LIGHT, StationsWorld


class LockWorld(StationsWorld):
    """marks (P10): a shut lid shows whose hand shut it (`shut by Ben`), so a mind can perceive a lock as someone's."""

    def __init__(self, stations=4, marks=False, **kw):
        super().__init__(stations, **kw)
        self.marks = marks
        ids = [str(i + 1) for i in range(stations)]
        for i in ids:
            self.objs[f"lid{i}"] = None
            self.gerund[f"lid{i}"] = "open"
        self.keyholder = {}   # lid -> the mind whose hand shut it
        self.blocked = []     # (tick, actor, object pushed, keyholder): pushes a lock stopped
        self.shuts = []       # (tick, actor, lid): every lid shut, and by whom

    def invitations(self, tree=None):
        out = super().invitations(tree)
        out += [(s, o, g) for o, g in self.gerund.items() if o.startswith("lid") for s in (LIGHT, HARD)]
        return sorted(out)

    def push(self, strength, o, diffs):
        actor = getattr(self, "actor", None)
        g = self.gerund.get(o)
        if o.startswith("lid"):
            if g == "open":
                self.keyholder[o] = actor
                self.shuts.append((self.t, actor, o))
                self.flip(o, f"shut by {actor}" if self.marks else "shut", "closed over the jar", diffs)
            elif self.keyholder.get(o) == actor:
                self.keyholder.pop(o, None)
                self.flip(o, "open", "opened by the hand that shut it", diffs)
            else:
                self.blocked.append((self.t, actor, o, self.keyholder.get(o)))
            return
        if o.startswith("jar") and self.gerund.get(f"lid{self.station(o)}", "").startswith("shut"):
            self.blocked.append((self.t, actor, o, self.keyholder.get(f"lid{self.station(o)}")))
            return
        super().push(strength, o, diffs)


SEAL = "seal"


class SealWorld(StationsWorld):
    """Rung P11's world: the lock as a state of the jar itself, so that sealing a jar changes the jar.

    A third push on a jar, `seal`, seals it, and the seal shows the hand: `jar1: charged sealed by Ben`. Sealed, the jar
    cannot be dipped or spilled by anyone; only the sealing hand's seal push unseals it; it still feeds its hollow and
    skiff (its level shows through the seal: `empty sealed by Ben` after a launch). The difference from P10's lid: there
    the lock was another object, so a mind that held its jar (its dips took) saw nothing of its jar change when another
    locked it; here another's seal is a change, by another, to a region the mind may hold (Gerundelle's territory register
    reads that as its own: contested, lost, and the phases on it).

    My choice (named): the seal is bound to the actor who set it (`world.actor`), as P9's lid was."""

    def __init__(self, stations=4, **kw):
        super().__init__(stations, **kw)
        self.seal = {}        # jar -> the hand that sealed it
        self.blocked = []     # (tick, actor, jar, keyholder)
        self.shuts = []       # (tick, actor, jar): every seal set

    @property
    def keyholder(self):   # P9's measures read lids' keyholders; here the jars'
        return dict(self.seal)

    def jar_g(self, i):
        o, level = f"jar{i}", self.level(i)
        return f"{level} sealed by {self.seal[o]}" if o in self.seal else level

    def later(self, i, why):
        if self.gerund[f"jar{i}"] != self.jar_g(i):
            self.pending.append((f"jar{i}", self.jar_g(i), why, None, []))

    def invitations(self, tree=None):
        out = super().invitations(tree)
        out += [(SEAL, o, g) for o, g in self.gerund.items() if o.startswith("jar")]
        return sorted(out)

    def push(self, strength, o, diffs):
        actor = getattr(self, "actor", None)
        if o.startswith("jar"):
            i, holder = self.station(o), self.seal.get(o)
            if strength == SEAL:
                if holder is None:
                    self.seal[o] = actor
                    self.shuts.append((self.t, actor, o))
                    self.flip(o, self.jar_g(i), "sealed", diffs)
                elif holder == actor:
                    del self.seal[o]
                    self.flip(o, self.jar_g(i), "unsealed by the hand that sealed it", diffs)
                else:
                    self.blocked.append((self.t, actor, o, holder))
                return
            if holder is not None:
                self.blocked.append((self.t, actor, o, holder))
                return
        super().push(strength, o, diffs)
