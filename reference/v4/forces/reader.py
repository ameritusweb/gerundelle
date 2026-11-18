"""A reader from simulator slices back into force skeletons (world-model POC;
the gap's first item, NEWTONIAN_WORLD_MODEL.md sections 9, 10, 12).

The simulator's state is the gerund AST, so the sensor comes first: observe()
forgets everything the doc calls unobservable. A Snap holds weights and
contacts only; gerunds, reserves and thresholds are not in it. The reader then
works from Snaps alone, never from the AST it came from, which is held back as
the hidden truth the reading is scored against.

Three readers, matching section 6's diff table:
- read_slice: a describing. Structure comes from the contacts; each node gets a
  gerund CANDIDATE SET from rules (ambiguity-as-abstraction on the gerund
  itself). A single slice cannot tell resting from piling (how it got there is
  a diff), nor falling from breaking, and the reader says so rather than guess.
- read_diff: a narrating/explaining. Between two slices: a thing that left a
  bearer that held, broke; a thing whose bearer gave way, fell; a thing that
  vanished as parts appeared, came apart; a thing that gained the ground,
  landed. Each line is a gerund, read from observations alone, and the demo
  prints it beside the simulator's own event to compare.
- the Bounds table: internal forces, inferred from what each thing survives
  (section 10). A survived load is a lower bound on the reserve the gerund
  consulted; a failure is an upper bound. The reader ends holding intervals
  like capacity(oak-beam) in [5, 13) against a hidden truth of 12.
"""
from dataclasses import dataclass

from poc import BORNE, INF, Node, Obj, anchoring, doing, doings, pressing, show, slot, step, wire
from theories import MATERIALS

GROUND = "ground"

OBJS = {**MATERIALS,
        "snow": Obj("snow", 8.0),
        "heavy-roof": Obj("heavy-roof", 9.0, capacity=25.0, cohesion=35.0, tensile=3.0),
        "brick": Obj("brick", 2.5, capacity=20.0, cohesion=50.0),
        "mortared-wall": Obj("mortared-wall", 10.0, capacity=40.0, cohesion=15.0,
                             parts=("brick", "brick", "brick", "brick"))}


# ---- the sensor -------------------------------------------------------------------

@dataclass(frozen=True)
class Snap:
    """A slice as sensed: weights and contacts only."""
    weights: tuple    # ((uid, weight), ...) in traversal order
    on: frozenset     # (a, b): a presses on b from above
    hangs: frozenset  # (a, b): a hangs below b

    def present(self):
        return [u for u, _ in self.weights]

    def weight(self, u):
        return dict(self.weights)[u]

    def bearer(self, u):
        return next((b for a, b in self.on | self.hangs if a == u), None)

    def deps(self, u):
        return sorted(a for a, b in self.on | self.hangs if b == u)


def _walk(scene):
    """(uid, node, parent uid) in traversal order; duplicate names numbered, the
    same way each slice, so an object keeps its uid across a trajectory."""
    counts, out = {}, []

    def go(n, parent):
        counts[n.doer] = counts.get(n.doer, 0) + 1
        u = n.doer if counts[n.doer] == 1 else f"{n.doer}#{counts[n.doer]}"
        out.append((u, n, parent))
        for k in doings(n):
            go(k, u)
    go(scene, None)
    return out


def observe(scene, objs):
    """What a slice shows. A borne doing is a contact with its bearer (on for
    compression, hangs for tension); a falling or breaking thing touches
    nothing. Weight is measurable; nothing else of the object is."""
    ws, on, hangs = [], set(), set()
    for u, n, p in _walk(scene):
        ws.append((u, objs[n.doer].weight))
        if p is not None and n.kind in BORNE:
            (hangs if n.kind == "hanging" else on).add((u, p))
    return Snap(tuple(ws), frozenset(on), frozenset(hangs))


def truth(scene):
    """uid -> gerund, for scoring a reading. The reader never sees this."""
    return {u: n.kind for u, n, _ in _walk(scene)}


def load(u, snap):
    """The external force on u, computed from the snapshot: the weights of
    everything transitively in contact above (or below, hanging). Observable
    because weights are."""
    return sum(snap.weight(a) + load(a, snap) for a in snap.deps(u))


def through(u, snap):
    return snap.weight(u) + load(u, snap)


# ---- reading a slice: a describing -------------------------------------------------

def candidates(u, snap):
    """The gerunds a node might be, from the contacts alone."""
    if u == GROUND:
        return ("anchoring",)
    b = snap.bearer(u)
    if b is None:
        return ("falling", "breaking")
    if (u, b) in snap.hangs:
        return ("hanging",)
    if snap.deps(u):
        return ("supporting",)
    return ("piling", "resting", "standing") if b == GROUND else ("pressing", "resting")


def read_slice(snap):
    """The ambiguous force AST of a slice: a forest (the grounded tree, plus a
    cluster per unattached thing), each node a candidate set. Returns (trees,
    number of readings = the product of the candidate sets)."""
    def build(u):
        return Node("|".join(candidates(u, snap)), [build(a) for a in snap.deps(u)], u)
    n_read = 1
    for u in snap.present():
        n_read *= len(candidates(u, snap))
    roots = [GROUND] + [u for u in snap.present() if u != GROUND and snap.bearer(u) is None]
    return [build(u) for u in roots], n_read


def score(trees, true_kinds):
    """(decided right, ambiguous with truth among candidates, wrong)."""
    d = a = w = 0
    def go(n):
        nonlocal d, a, w
        cands = n.kind.split("|")
        if true_kinds[n.doer] not in cands:
            w += 1
        elif len(cands) == 1:
            d += 1
        else:
            a += 1
        for k in n.kids:
            go(k)
    for t in trees:
        go(t)
    return d, a, w


# ---- internal forces, inferred from what each thing survives ------------------------

class Bounds:
    def __init__(self):
        self.lo, self.hi = 0.0, INF

    def survive(self, x):
        self.lo = max(self.lo, x)

    def fail(self, x):
        self.hi = min(self.hi, x)

    def __str__(self):
        return f"[{self.lo:g}, {'inf' if self.hi == INF else f'{self.hi:g}'})"


def base(u):
    return u.split("#")[0]


def note(table, u, quantity, how, x):
    if table is None:
        return
    b = table.setdefault((base(u), quantity), Bounds())
    b.survive(x) if how == "survive" else b.fail(x)


# ---- reading a diff: a narrating, with its explaining -------------------------------

def read_diff(s0, s1, table=None):
    """The diff between two slices, read from the snapshots alone: a list of
    events, each a dict with a gerund "kind", its parts, and a printed "line".
    A failure or a survival also licenses a bound on an internal reserve,
    noted in the table."""
    ev = []

    def add(kind, line, **data):
        ev.append({"kind": kind, "line": line, **data})

    p0, p1 = set(s0.present()), set(s1.present())
    lost = {u for u in p0 & p1 if s0.bearer(u) is not None and s1.bearer(u) is None}
    vanished, appeared = sorted(p0 - p1), sorted(p1 - p0)
    for u in sorted(lost):
        b = s0.bearer(u)
        if b == GROUND or (b in p1 and s1.bearer(b) is not None):
            q = "tensile" if (u, b) in s0.hangs else "capacity"
            l = load(u, s0)
            add("broke", f"{u}: it broke ({b} held) -> its {q} < {l:g}", obj=u, bearer=b, via=q, load=l)
            note(table, u, q, "fail", l)
        else:
            add("fell", f"{u}: falling ({b} gave way)", obj=u, bearer=b)
    for u in vanished:
        t = through(u, s0)
        parts = ", ".join(appeared) if appeared else "nothing seen"
        add("came_apart", f"{u}: one thing -> parts ({parts}) -> its cohesion < {t:g}",
            obj=u, load=t, parts=appeared)
        note(table, u, "cohesion", "fail", t)
    for u in sorted(p0 & p1):
        if s0.bearer(u) is None and s1.bearer(u) == GROUND:
            add("landed", f"{u}: landed, piling", obj=u)
        elif s0.deps(u) and not s1.deps(u) and s1.bearer(u) is not None and u != GROUND:
            add("unburdened", f"{u}: unburdened, standing", obj=u)
    for u in appeared:
        b = s1.bearer(u)
        if b is not None and not vanished:
            add("arrived", f"{u}: pressing (arrived on {b})", obj=u, bearer=b)
    for u in p0 & p1:
        if u == GROUND or u in lost or s0.bearer(u) is None:
            continue
        l_on = sum(s0.weight(a) + load(a, s0) for a in s0.deps(u) if (a, u) in s0.on)
        l_hang = sum(s0.weight(a) + load(a, s0) for a in s0.deps(u) if (a, u) in s0.hangs)
        if l_on:
            note(table, u, "capacity", "survive", l_on)
        if l_hang:
            note(table, u, "tensile", "survive", l_hang)
        note(table, u, "cohesion", "survive", through(u, s0))
    return ev


# ---- demo ---------------------------------------------------------------------------

def print_snap(s):
    print("  present: " + ", ".join(f"{u} ({w:g})" for u, w in s.weights))
    for a, b in sorted(s.on):
        print(f"    {a} on {b}")
    for a, b in sorted(s.hangs):
        print(f"    {a} hangs from {b}")


def narrate(t, objs, table):
    """Run a trajectory to quiet, printing the simulator's own events beside
    what the reader reads from the two snapshots alone."""
    prev = observe(t, objs)
    while True:
        t, events = step(t, objs)
        if not events:
            return
        cur = observe(t, objs)
        print("    simulator:  " + "; ".join(events))
        print("    reader:     " + "; ".join(e["line"] for e in read_diff(prev, cur, table)))
        prev = cur


def main():
    objs = OBJS
    table = {}

    tower = wire(anchoring(GROUND, slot("supporting", slot("supporting",
                 doing("resting", "thatch-roof")))), ("stone-post", "oak-beam"), objs)
    print("== 1. The sensor: what a slice shows (gerunds and reserves withheld) ==\n")
    s = observe(tower, objs)
    print_snap(s)

    print("\n== 2. Reading it back: structure from contacts, gerunds from rules ==\n")
    trees, n = read_slice(s)
    for t in trees:
        print("\n".join(show(t, depth=1)))
    d, a, w = score(trees, truth(tower))
    print(f"\n  against the hidden truth: {d} decided right, {a} ambiguous"
          f" (truth among the candidates), {w} wrong; {n} readings.")
    print("  A slice cannot tell resting from pressing, nor (on the ground)")
    print("  resting from piling from standing: how a thing got there is a diff.")

    chain = wire(anchoring(GROUND, slot("hanging", slot("hanging",
                 doing("hanging", "lantern")))), ("steel-chain", "hemp-rope"), objs)
    sc = observe(chain, objs)
    trees, n = read_slice(sc)
    d, a, w = score(trees, truth(chain))
    print(f"\n  the suspension chain reads back exactly: {d} decided right,"
          f" {a} ambiguous, {w} wrong; {n} reading(s).")
    read_diff(s, s, table)     # a quiet diff: survivals license lower bounds
    read_diff(sc, sc, table)

    print("\n== 3. A trajectory, narrated from observations alone ==\n")
    pre = wire(anchoring(GROUND, slot("supporting", slot("supporting",
               doing("resting", "thatch-roof")))), ("stone-post", "oak-beam"), objs)
    t0 = wire(anchoring(GROUND, slot("supporting", slot("supporting",
              doing("resting", "thatch-roof", pressing("snow"))))), ("stone-post", "oak-beam"), objs)
    print("    simulator:  (snow added between runs; not a step)")
    print("    reader:     " + "; ".join(e["line"] for e in
                                         read_diff(observe(pre, objs), observe(t0, objs), table)))
    narrate(t0, objs, table)

    print("\n== 4. The wall, and a snapped hanger ==\n")
    wall = wire(anchoring(GROUND, slot("supporting", doing("resting", "heavy-roof"))),
                ("mortared-wall",), objs)
    narrate(wall, objs, table)
    hung = wire(anchoring(GROUND, slot("hanging", doing("hanging", "thatch-roof"))),
                ("plank",), objs)
    narrate(hung, objs, table)

    print("\n== 5. Internal forces, inferred from what each thing survived ==\n")
    for (nm, q), b in sorted(table.items()):
        if q == "cohesion" and b.hi == INF:
            continue
        true = getattr(objs[nm], q)
        ok = "consistent" if b.lo <= true < b.hi else "WRONG"
        print(f"  {nm:14} {q:9} reader knows {str(b):12} hidden truth {true:g}  ({ok})")


if __name__ == "__main__":
    main()
