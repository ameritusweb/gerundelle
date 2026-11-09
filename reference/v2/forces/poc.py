"""Force gerunds: external and internal forces, and how they map from the gerund AST
(world-model POC; NEWTONIAN_WORLD_MODEL.md sections 2, 4, 6, 9; the vocabulary is
FORCE_VOCABULARY.md, every gerund of which is registered in GERUNDS below).

A scene is a gerund AST: every node is a doing (supporting, resting, pressing),
and its doer is a slot (ambiguity-as-abstraction). As in poc3, the skeleton is
valid if there EXISTS a filling of every slot under which the configuration
persists when stepped; its valid fillings are its readings.

Where each force kind lives, which is the mapping this POC exists to show:

- EXTERNAL forces ARE the edges of the AST. A doing borne by another doing is
  its kid, and the force on a node is the sum of its kids' outputs: resting(roof)
  under supporting(beam) is the roof's weight as an external force on the beam.
  A gerund declares which channels its output acts on (load, push, strike,
  squeeze, heat, flow, pressure, wear; for agents evidence, drive, oppose;
  an agent's persuasion is a push). There is no separate force table; force_map() reads the external
  forces off the parent-kid relation.

- INTERNAL forces live in the object filling the slot, as reserves: capacity,
  tensile, cohesion, grip, base, buoyancy, seal, volume, heat points; for
  agents resolve, conviction, retention, goal. They enter the AST in exactly
  one place: as the thresholds of the node's phase-change kids, filled at
  wiring time. Which reserves a node watches is a fact about its gerund.

- A PHASE CHANGE is a first-class node (changing_phase), a kid of the doing it
  watches, with a threshold slot (unfilled in the skeleton). When the watched
  quantity crosses the threshold the parent's gerund is rewritten and what it
  bore is re-read: supporting becomes breaking, resting becomes falling, a
  wall becomes bricks. The slots are the same; the gerund changed.

Time is slices and diffs (section 6): step() maps a slice to the next, all
thresholds read against the incoming slice at once, and the events it returns
are the diffs, each one a gerund. There is no velocity or acceleration: motion
is a gerund (falling is weight with nothing opposing it), and a change of
force is a discrete event between slices.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import permutations

INF = float("inf")


@dataclass(frozen=True)
class Obj:
    """An object: the external force it sources (weight) and its internal
    forces, the reserves whose balance decides whether it persists as this
    node. A reserve left at INF adds no phase-change node."""
    name: str
    weight: float
    capacity: float = INF   # load its doing can bear before breaking
    cohesion: float = INF   # load through it before it is its parts
    tensile: float = 0.0    # load it can carry hanging before snapping
    parts: tuple = ()       # what it is re-read as when cohesion fails
    grip: float = INF       # push it holds against before sliding
    base: float = INF       # side push it holds against before tipping
    buoyancy: float = INF   # weight it floats before sinking
    seal: float = INF       # pressure its walls hold before leaking
    volume: float = INF     # contents it holds before overflowing
    stiffness: float = INF  # side push a compressed member takes before buckling
    bend: float = INF       # load before a permanent bend
    crack: float = INF      # load before a crack (a reserve drops)
    shatter: float = INF    # strike before shattering (brittle)
    tear: float = INF       # pull before tearing
    erode: float = INF      # flow before it starts wearing away
    jam: float = INF        # load through a redirector before it jams
    melt: float = INF       # heat above which a solid melts; below which a liquid freezes
    boil: float = INF       # heat above which a liquid boils
    ignite: float = INF     # heat above which it burns
    heat: float = 20.0      # its own heat before anything heats or cools it
    solvency: float = 0.0   # a liquid's pull on what rests in it
    round: bool = False     # rolls rather than slides
    elastic: bool = False   # rebounds rather than rests after striking
    resolve: float = INF    # agent: opposition or persuasion it holds against
    conviction: float = INF # agent: contrary evidence a belief holds against
    retention: float = INF  # agent: interference a memory holds against
    goal: float = INF       # agent: progress at which a pursuit is reached


@dataclass
class Node:
    kind: str                 # a force gerund, or changing_phase
    kids: list = field(default_factory=list)
    doer: str = None          # the object doing it; None = an unfilled slot
    watch: tuple = None       # changing_phase: (quantity, new gerund, op, reserve)
    threshold: float = None   # changing_phase: the threshold slot (None = unfilled)
    amount: float = None      # a doing's own quantity: a push's size, a flow's rate,
                              # a pool's mass, a lever's ratio, a purpose's drive
    against: str = None       # a second participant named, not borne (leaning, siphoning)
    progress: float = 0.0     # what has accumulated in this node: wear, a pursuit's progress


# ---- the vocabulary ----------------------------------------------------------------
#
# Each gerund: its group in FORCE_VOCABULARY.md, the channels its output acts on
# (on its bearer, the parent), and the reserves it watches, each a phase-change
# node (quantity, reserve, new gerund, op, factor). Output channels:
#   load      the doer's weight plus the load it bears, handed down (what BORNE was)
#   push, strike, squeeze, flow, wear, evidence, drive, oppose:  its amount
#   heat / cold  +amount / -amount of heat;  pressure  a boiling liquid's push outward
#   pass      every incoming channel but load, passed on unchanged
#   passflow  incoming flow passed on;  pushload  an incoming push passed down as load
#   swap      weight plus incoming push as load, incoming load as push (redirecting)
#   gain      every incoming channel times its amount (attending)

@dataclass(frozen=True)
class G:
    group: str
    out: tuple = ()
    watches: tuple = ()


def w(qty, reserve, to, op=">", factor=1.0):
    return (qty, reserve, to, op, factor)


SHATTER = (w("strike", "shatter", "shattering"),)
BREAK = (w("load", "capacity", "breaking"), w("through", "cohesion", "coming apart"))
HANGS = (w("load", "tensile", "snapping"), w("through", "cohesion", "coming apart"))
MATTER = (w("push", "tear", "tearing"), w("heat", "melt", "melting"), w("heat", "ignite", "burning"))
DAMAGE = (w("load", "crack", "cracking"), w("load", "bend", "bending"))
LIQUID = (w("heat", "melt", "freezing", "<"), w("heat", "boil", "boiling"))
SHIFT = (w("push", "base", "tipping"), w("push", "grip", "sliding"))


def solid(*own, holds=BREAK):
    """A solid doing's watches: shattering, its failure reserves, tearing,
    melting, burning, then its own, then damage that leaves the gerund."""
    return SHATTER + holds + MATTER + own + DAMAGE


CONTAINS = (w("pressure", "capacity", "bursting"), w("pressure", "seal", "leaking"),
            w("load", "volume", "overflowing"))
GOAL = (w("oppose", "resolve", "giving up"), w("progress", "goal", "reaching", ">="))
BELIEF = (w("evidence", "conviction", "changing one's mind"),
          w("evidence", "conviction", "doubting", ">", 0.5))

GERUNDS = {
    # bearing
    "anchoring": G("bearing", ("load",)),
    # a loaded support can still be pushed over (added 2026-10-23 for the agent's force world:
    # with no tipping watch, a press could never knock out a prop holding a boulder)
    "supporting": G("bearing", ("load",), solid(w("push", "base", "tipping"))),
    "standing": G("bearing", ("load",), solid(w("push", "base", "tipping"))),
    "resting": G("bearing", ("load",), solid(*SHIFT)),
    "pressing": G("bearing", ("load",), solid()),
    "hanging": G("bearing", ("load",), solid(holds=HANGS)),
    "piling": G("bearing", ("load",), solid(w("push", "grip", "sliding"))),
    "leaning": G("bearing", ("load",), solid(w("push", "grip", "sliding"))),
    "bracing": G("bearing", ("load", "pushload"),
                 solid(w("push", "capacity", "breaking"), w("push", "stiffness", "buckling"))),
    "spanning": G("bearing", ("load",), solid(w("load", "capacity", "sagging", ">", 0.8))),
    "wedging": G("bearing", ("load",), solid(w("load", "grip", "slipping"))),
    "cantilevering": G("bearing", ("load",), solid()),
    # losing balance
    "falling": G("losing balance"),
    "tipping": G("losing balance"),
    "sliding": G("losing balance", ("load",), solid()),
    "rolling": G("losing balance", ("load",), solid()),
    "swinging": G("losing balance", ("load",), solid(holds=HANGS)),
    "sinking": G("losing balance"),
    "floating": G("losing balance", ("load",), solid(w("through", "buoyancy", "sinking"))),
    "drifting": G("losing balance", ("load",), solid(w("through", "buoyancy", "sinking"))),
    # contact
    "pushing": G("contact", ("push",)),
    "pulling": G("contact", ("push",), (w("amount", "tensile", "snapping"),)),
    "striking": G("contact", ("strike",)),
    "squeezing": G("contact", ("squeeze",)),
    "blocking": G("contact", ("load",), solid(w("push", "capacity", "breaking"))),
    "catching": G("contact", ("load",), solid()),
    "gripping": G("contact", ("load",), solid(w("push", "grip", "slipping"))),
    "slipping": G("contact", ("load",)),
    "rebounding": G("contact"),
    # transmitting
    "pivoting": G("transmitting", ("load",), solid()),
    "levering": G("transmitting", ("load",), solid(w("push", "grip", "slipping"))),
    "redirecting": G("transmitting", ("swap",), solid(w("through", "jam", "jamming"))),
    "transmitting": G("transmitting", ("load", "pass"), solid()),
    "coupling": G("transmitting", ("load", "pass"), solid()),
    "jamming": G("transmitting", ("load",),
                 solid(w("push", "capacity", "breaking"), w("push", "grip", "slipping"))),
    # holding together
    "cohering": G("holding together", ("load",), solid()),
    "binding": G("holding together", ("load",), solid()),
    "tying": G("holding together", ("load",), solid(w("push", "grip", "slipping"), holds=HANGS)),
    "fastening": G("holding together", ("load",), solid(w("push", "grip", "slipping"))),
    "locking": G("holding together", ("load",), solid(w("push", "grip", "releasing"))),
    # storing and releasing
    "stretching": G("storing", ("load",), (w("amount", "tensile", "snapping"),)),
    "compressing": G("storing", ("load",), (w("amount", "capacity", "buckling"),)),
    "loading": G("storing", ("load",), solid()),
    "releasing": G("storing"),
    "launching": G("storing"),
    "flying": G("storing"),
    # containing and flowing
    "containing": G("containing", ("load",), SHATTER + CONTAINS),
    "filling": G("containing", ("load",), SHATTER + CONTAINS),
    "overflowing": G("containing", ("load",), SHATTER + CONTAINS[:2]),
    "leaking": G("containing", ("load",), SHATTER + CONTAINS[:1]),
    "bursting": G("containing"),
    "flowing": G("containing", ("flow",), LIQUID[:1]),
    "pouring": G("containing", ("flow",), LIQUID[:1]),
    "pooling": G("containing", ("load",), LIQUID),
    "damming": G("containing", ("load",), solid(w("load", "volume", "overflowing"))),
    "channeling": G("containing", ("load", "passflow"),
                    solid(w("flow", "volume", "overflowing"), w("flow", "erode", "eroding"))),
    "siphoning": G("containing", ("load",)),
    "draining": G("containing", ("load",), SHATTER + CONTAINS[:1]),
    "eroding": G("containing", ("load", "passflow"), solid()),
    # a valve (added 2026-10-23 for the curriculum's button, calculator and power worlds): a seal
    # held shut by its reserve; a push over the seal opens it and the flow behind it passes, and
    # the reserve recloses it when the push lets up
    "sealing": G("containing", ("load",), solid(w("push", "seal", "opening"))),
    "opening": G("containing", ("load", "passflow"), solid()),
    # a plug (same date, for the power world): seated in its socket by its grip it passes what
    # flows through it; a push over the grip unseats it, and another push over the grip seats it
    "connecting": G("transmitting", ("load", "pass"), solid(w("push", "grip", "parting"))),
    "parting": G("transmitting", ("load",), solid(w("push", "grip", "connecting"))),
    # feedback (added 2026-10-23 for the curriculum's stage 4): a float valve, open (metering) while
    # its bearer's contents are under its seal, closed (shutting) from there until they fall to its
    # amount (a lower mark: between the two it keeps whichever it was, hysteresis); and a pump
    # (feeding) that passes the flow behind it plus its amount times the contents it stands in
    # (the more it holds, the more comes in: positive feedback)
    "metering": G("containing", ("load", "passflow"), solid()),
    "shutting": G("containing", ("load",), solid()),
    "feeding": G("containing", ("load", "feed"), solid()),
    # phase changes (the gerund a crossing produces; most last one slice)
    "breaking": G("phase change"),
    "snapping": G("phase change"),
    "coming apart": G("phase change"),
    "crumbling": G("phase change"),
    "shattering": G("phase change"),
    "cracking": G("phase change"),
    "bending": G("phase change"),
    "buckling": G("phase change"),
    "sagging": G("phase change", ("load",), solid()),
    "tearing": G("phase change"),
    "melting": G("phase change"),
    "freezing": G("phase change"),
    "boiling": G("phase change", ("pressure",), (w("heat", "boil", "pooling", "<"),)),
    "burning": G("phase change", ("load", "heat")),
    "dissolving": G("phase change"),
    "wearing": G("phase change", ("wear",)),
    "heating": G("heat", ("heat",)),
    "cooling": G("heat", ("cold",)),
    # agents: the same balances, abstract
    "pursuing": G("agents", (), GOAL),
    "avoiding": G("agents", (), (w("oppose", "resolve", "pursuing"),)),
    "perceiving": G("agents", ("evidence",)),
    "believing": G("agents", (), BELIEF),
    "doubting": G("agents", (), BELIEF[:1] + (w("evidence", "conviction", "believing", "<=", 0.5),)),
    "changing one's mind": G("agents"),
    "remembering": G("agents", (), (w("evidence", "retention", "gone"),)),
    "recalling": G("agents"),
    "attending": G("agents", ("gain",)),
    "wanting": G("agents"),
    "resisting": G("agents", (), (w("push", "resolve", "yielding"),)),
    "yielding": G("agents"),
    "committing": G("agents", (), GOAL[:1]),
    "hesitating": G("agents"),
    "giving up": G("agents"),
    "reaching": G("agents"),
    "helping": G("agents", ("drive",)),
    "opposing": G("agents", ("oppose",)),
}

# Doings whose output presses on (or pulls at) their bearer. falling and
# breaking are not borne: their force reaches nothing until they settle.
# (standing is borne: an unburdened post still presses the ground - found by
# the reader, which saw the post's contact vanish and read a phantom break.)
BORNE = {k for k, g in GERUNDS.items() if "load" in g.out}
STUFF = {"pooling", "flowing", "pouring", "boiling"}          # mass is the node's amount
CONTAINERS = {"containing", "filling", "overflowing", "leaking", "draining", "damming"}
SOLIDS = BORNE - STUFF - CONTAINERS - {"anchoring"}
# What leaves a bearer that has failed: its borne kids fall, its liquid flows.
FAILS = {"breaking", "snapping", "buckling", "tipping", "shattering", "crumbling",
         "tearing", "melting", "burning", "bursting"}


def doing(kind, doer=None, *borne, amount=None, against=None):
    return Node(kind, list(borne), doer, amount=amount, against=against)


def anchoring(doer, *borne): return doing("anchoring", doer, *borne)
def supporting(doer, *borne): return doing("supporting", doer, *borne)
def resting(doer, *borne): return doing("resting", doer, *borne)
def pressing(doer): return doing("pressing", doer)
def hanging(doer, *borne): return doing("hanging", doer, *borne)


def changing_phase(watch, threshold=None):
    return Node("changing_phase", watch=watch, threshold=threshold)


def slot(kind, *borne):
    """A doing whose doer is a slot, carrying its phase-change nodes for the
    reserves every doer has (capacity or tensile, and cohesion) with the
    threshold slots unfilled: the skeleton states that the doing can break and
    can come apart before knowing what fills it."""
    ws = [changing_phase((q, to, op, r)) for q, r, to, op, f in GERUNDS[kind].watches
          if r in ("capacity", "tensile", "cohesion") and to in ("breaking", "snapping", "coming apart")]
    return Node(kind, [*ws, *borne])


def doings(n):
    return [k for k in n.kids if k.kind != "changing_phase"]


def watches(n):
    return [k for k in n.kids if k.kind == "changing_phase"]


def slots(n):
    """How many doer slots the skeleton has (filled in tree order)."""
    return int(n.doer is None) + sum(slots(k) for k in doings(n))


def like(n, kind=None, kids=None):
    """n with its kind or kids replaced, keeping its doer and its quantities."""
    return Node(kind or n.kind, n.kids if kids is None else kids, n.doer,
                amount=n.amount, against=n.against, progress=n.progress)


# ---- the mapping: gerund AST -> forces -----------------------------------------

def weight(n, objs):
    """A doer's weight; for stuff (a pool, a flow) the node's own amount."""
    if n.kind in STUFF and n.amount is not None:
        return n.amount
    return objs[n.doer].weight


def outputs(n, objs):
    """The force a doing hands to its bearer, by channel."""
    d = defaultdict(float)
    amt = n.amount or 0.0
    for ch in GERUNDS[n.kind].out:
        if ch == "load":
            d["load"] += output(n, objs)
        elif ch == "cold":
            d["heat"] -= amt
        elif ch == "heat":
            d["heat"] += amt if n.kind != "burning" else 50 * weight(n, objs)
        elif ch == "pressure":
            d["pressure"] += 10 * weight(n, objs)
        elif ch == "feed":   # what it pumps: the flow behind it, plus what its bearer's level drew
            d["flow"] += incoming(n, objs)["flow"] + n.progress
        elif ch in ("pass", "passflow", "pushload", "swap", "gain"):
            inc = incoming(n, objs)
            if ch == "pass":
                for c, v in inc.items():
                    if c != "load":
                        d[c] += v
            elif ch == "passflow":
                d["flow"] += inc["flow"]
            elif ch == "pushload":
                d["load"] += inc["push"]
            elif ch == "swap":
                d["load"] += weight(n, objs) + inc["push"]
                d["push"] += inc["load"]
            else:
                for c, v in inc.items():
                    d[c] += v * amt
        else:
            d[ch] += amt
    return d


def incoming(n, objs):
    """Every external force on a doing, by channel: the sum of its kids' outputs."""
    d = defaultdict(float)
    for k in doings(n):
        for c, v in outputs(k, objs).items():
            d[c] += v
    return d


def external(n, objs):
    """The external load on a doing: the sum of its borne kids' outputs.
    The edges of the AST are the external forces; nothing else carries one."""
    return incoming(n, objs)["load"]


def output(n, objs):
    """The load a doing hands to its bearer: its doer's weight plus what it
    transmits. Also the load through the node, the quantity cohesion answers."""
    return weight(n, objs) + external(n, objs)


def quantities(n, objs):
    """What the node's watches and rules read, from the incoming slice."""
    inc = incoming(n, objs)
    return {
        "load": inc["load"] + inc["squeeze"] + inc["strike"],
        "through": output(n, objs),
        "push": inc["push"] + inc["strike"],
        "strike": inc["strike"],
        "squeeze": inc["squeeze"],
        "pressure": inc["load"] + inc["pressure"] + inc["squeeze"],
        "heat": objs[n.doer].heat + inc["heat"],
        "flow": inc["flow"],
        "wear": inc["wear"],
        "evidence": inc["evidence"],
        "drive": (n.amount or 0.0) + inc["drive"],
        "oppose": inc["oppose"],
        "amount": n.amount or 0.0,
        "progress": n.progress,
    }


def force_map(tree, objs):
    """Both force kinds read off the AST: edges (each borne kid's output as an
    external force on its bearer) and rows (per doing: the load on it, the load
    through it, and its doer's internal reserves)."""
    edges, rows = [], []

    def go(n):
        o = objs[n.doer]
        rows.append((label(n), external(n, objs), output(n, objs), o.capacity, o.cohesion))
        for k in doings(n):
            if k.kind in BORNE:
                edges.append((label(k), output(k, objs), label(n)))
            go(k)
    go(tree)
    return edges, rows


# ---- wiring: objects into doer slots, reserves into threshold slots -------------

def watches_for(kind, o, keep=()):
    """The phase-change nodes a doing of this kind has with this doer: one per
    watched reserve the doer has (a boundless reserve adds no node). A watch
    the node already had on the same quantity and reserve keeps its threshold,
    so a crack or a bend survives a change of gerund. A round doer rolls where
    others slide."""
    old = {(k.watch[0], k.watch[3]): k.threshold for k in keep}
    out = []
    for q, r, to, op, f in GERUNDS[kind].watches:
        lim = r if isinstance(r, (int, float)) else getattr(o, r)
        if lim == INF:
            continue
        if to == "sliding" and o.round:
            to = "rolling"
        thr = old.get((q, r), lim * f) if f == 1.0 else lim * f
        out.append(changing_phase((q, to, op, r), thr))
    return out


def wire(skel, picks, objs):
    """The skeleton with its doer slots filled in tree order, and every doing
    given phase-change nodes whose threshold slots are filled from the doer's
    reserves (capacity for load borne, tensile for load hung, cohesion for
    through, and whatever else the gerund watches). Which reserve the load
    reads is a fact about the gerund, not the object: the same rope consults
    tensile when hanging, capacity when posted. This is the whole entry of
    internal forces into the AST; a boundless reserve adds no node."""
    it = iter(picks)

    def go(n):
        doer = n.doer if n.doer is not None else next(it)
        m = Node(n.kind, [], doer, amount=n.amount, against=n.against, progress=n.progress)
        m.kids = watches_for(n.kind, objs[doer]) + [go(k) for k in doings(n)]
        return m
    return go(skel)


def readings(skel, inventory, objs):
    """Every filling of the slots with distinct objects from the inventory
    under which the configuration persists (step finds no diff): existential
    validity over force assignments. Returns [(picks, diffs)] for all fillings."""
    out = []
    for picks in permutations(inventory, slots(skel)):
        _, events = step(wire(skel, picks, objs), objs)
        out.append((picks, events))
    return out


# ---- time: a slice to the next slice; the diffs are gerunds ----------------------

def crossed(q, op, thr):
    return {">": q > thr, "<": q < thr, ">=": q >= thr, "<=": q <= thr}[op]


def contents(n, objs):
    return sum(weight(k, objs) for k in doings(n) if k.kind == "pooling")


def scan(tree, objs):
    """What a step needs to know about the whole incoming slice: which doers
    are present and holding, and the level of every container."""
    present, levels = set(), {}

    def go(n):
        if n.kind not in FAILS and n.kind not in ("falling", "flying", "sinking"):
            present.add(n.doer)
        if n.kind in CONTAINERS:
            levels[n.doer] = contents(n, objs)
        for k in doings(n):
            go(k)
    go(tree)
    return present, levels


def step(tree, objs):
    """One slice to the next, pure. Every threshold is read against the
    incoming slice (a slice is simultaneous), then the crossings are applied:
    a doing whose load crosses its capacity becomes breaking and what it bore
    is re-read as falling; a doing whose through-load crosses its cohesion
    stops being one node and its parts pile; what was falling or breaking
    settles onto the ground as piling; a supporter left bearing nothing is
    re-read as standing (context changes the node). Every other gerund of the
    vocabulary flips the same way, by its watches (reserves crossed), its
    mechanics (what it does to its contents or kids each slice) and its rules
    (conditions on the forces that need no reserve). Returns (next slice,
    diffs); each diff is a gerund, the unit of meaning."""
    moved, events, transfers = [], [], defaultdict(float)
    present, levels = scan(tree, objs)

    def say(n, to, why):
        events.append(f"{n.doer}: {n.kind} -> {to} ({why})")

    def make(kind, doer, amount=None):
        return Node(kind, watches_for(kind, objs[doer]), doer, amount=amount)

    def fall(k):
        if k.kind in STUFF:
            say(k, "flowing", "its container failed")
            moved.append(make("flowing", k.doer, weight(k, objs)))
            return None
        events.append(f"{k.doer}: {k.kind} -> falling (its bearer failed)")
        return Node("falling", k.kids, k.doer, amount=k.amount)

    def become(n, to, why=None):
        """n re-read under a new gerund. A failed bearer drops what it bore."""
        if why:
            say(n, to, why)
        kids = doings(n)
        if to in FAILS:
            kids = [r for r in (fall(k) if k.kind in BORNE else k for k in kids) if r is not None]
        return Node(to, watches_for(to, objs[n.doer], watches(n)) + kids, n.doer,
                    amount=n.amount, against=n.against, progress=n.progress)

    def to_parts(n, kind_of_change):
        ps = objs[n.doer].parts or (n.doer,)
        events.append(f"{n.doer}: {kind_of_change} -> its parts, {len(ps)} piling")
        moved.extend(Node("piling", [], p) for p in ps)
        return [r for r in (fall(k) for k in doings(n) if k.kind in BORNE) if r is not None]

    def add_stuff(n, stuff, delta):
        """Change a container's contents by delta of stuff (its pooling kid)."""
        pool = next((k for k in n.kids if k.kind == "pooling"), None)
        if pool is None:
            if delta > 0:
                n.kids.append(make("pooling", stuff, delta))
            return
        pool.amount = max(0.0, weight(pool, objs) + delta)
        if pool.amount == 0:
            n.kids.remove(pool)

    def grounded(parent):
        return parent is None or parent.kind == "anchoring"

    # ---- settling: one-slice gerunds become what follows them

    def settle(n, parent):
        k, o = n.kind, objs[n.doer]
        if k == "falling" and parent is not None and parent.kind == "catching":
            return n
        if k in ("falling", "breaking", "snapping", "buckling"):
            events.append(f"{n.doer}: {k} -> piling (on the ground)")
            moved.append(Node("piling", doings(n), n.doer))
            return None
        if k in ("shattering", "crumbling", "tearing"):
            return to_parts(n, k)
        if k == "burning":
            events.append(f"{n.doer}: burning -> its parts, ash piling")
            moved.extend(Node("piling", [], p) for p in (o.parts or ("ash",)))
            return [r for r in (fall(x) for x in doings(n) if x.kind in BORNE) if r is not None]
        if k == "bursting":
            return to_parts(n, "bursting")
        if k in ("tipping", "slipping", "rebounding"):
            if not grounded(parent):
                return become(n, "falling", "off its bearer")
            nxt = {"tipping": "resting", "slipping": "sliding"}.get(k, "rolling" if o.round else "resting")
            return become(n, nxt, "settles")
        if k == "striking":
            return become(n, "rebounding" if o.elastic else "resting", "the strike is spent")
        if k in ("sinking", "freezing"):
            return become(n, "resting", "settles")
        if k == "melting":
            return become(n, "flowing", "now liquid")
        if k == "releasing":
            return become(n, "launching", "stored force let go")
        if k == "launching":
            out = []
            for x in doings(n):
                if x.kind in BORNE and output(x, objs) < (n.amount or 0.0):
                    say(x, "flying", f"launched by {n.amount:g} > its weight {output(x, objs):g}")
                    moved.append(like(x, "flying"))
                else:
                    out.append(x)
            return become(like(n, kids=watches(n) + out), "resting", "its force is handed on")
        if k == "flying":
            return become(n, "falling", "weight unopposed")
        if k == "changing one's mind":
            return become(like(n, kids=[x for x in n.kids if x.kind != "perceiving"]),
                          "believing", "the new position")
        if k == "recalling":
            return become(n, "remembering", "the past position is back in play")
        if k in ("giving up", "reaching"):
            return become(n, "resting", "no purpose acting")
        if k == "dissolving":
            events.append(f"{n.doer}: dissolving -> gone (now part of the liquid)")
            return []
        return n

    SETTLE = {"falling", "breaking", "snapping", "buckling", "shattering", "crumbling", "tearing",
              "burning", "bursting", "tipping", "slipping", "rebounding", "striking", "sinking",
              "freezing", "melting", "releasing", "launching", "flying", "changing one's mind",
              "recalling", "giving up", "reaching", "dissolving"}

    # ---- a watch crossed: the phase-change node fires

    def phase(n, wn, Q):
        q, to, op, r = wn.watch
        why = f"{q} {Q[q]:g} {op} reserve {wn.threshold:g}"
        if to == "coming apart":
            if n.progress > 0:
                return become(n, "crumbling", why + ", worn")
            ps = objs[n.doer].parts or (n.doer,)
            events.append(f"{n.doer}: {n.kind} -> coming apart, {len(ps)} parts piling"
                          f" (through {Q['through']:g} > cohesion {wn.threshold:g})")
            moved.extend(Node("piling", [], p) for p in ps)
            return [r for r in (fall(k) for k in doings(n) if k.kind in BORNE) if r is not None]
        if to in ("cracking", "bending", "sagging"):
            keep = [x for x in watches(n) if x is not wn]
            cut = {"cracking": 0.5, "bending": 0.75, "sagging": 0.9}[to]
            for x in keep:
                if x.watch[3] == "capacity" and x.watch[1] == "breaking":
                    x.threshold *= cut
            n2 = like(n, kids=keep + doings(n))
            if to == "sagging":
                return become(n2, "sagging", why)
            events.append(f"{n.doer}: {n.kind}, {to} ({why}; capacity now x{cut:g})")
            return n2
        if to == "gone":
            events.append(f"{n.doer}: {n.kind} -> gone ({why})")
            return []
        if to == "releasing":
            kids = [become(k, "releasing", "its lock let go")
                    if k.kind in ("stretching", "compressing", "loading") else k for k in doings(n)]
            return become(like(n, kids=watches(n) + kids), "releasing", why)
        return become(n, to, why)

    # ---- mechanics: what a doing does to its contents or kids each slice

    def mechanics(n, Q, parent):
        k, o = n.kind, objs[n.doer]
        if Q["wear"] > 0:
            for x in watches(n):
                if x.watch[1] in ("breaking", "coming apart", "snapping"):
                    x.threshold = max(0.0, x.threshold - Q["wear"])
            n.progress += Q["wear"]
            events.append(f"{n.doer}: {k}, wearing (reserves -{Q['wear']:g})")
        # a container takes in the flow the slice it arrives (2026-10-23: from the second slice
        # only, so a one-slice flow, a valve pressed once, added nothing)
        if k in ("containing", "filling", "damming", "overflowing") and Q["flow"] > 0:
            src = next((x.doer for x in doings(n) if x.kind in STUFF), "water")
            add_stuff(n, src, Q["flow"])
            events.append(f"{n.doer}: {k} (+{Q['flow']:g}, holds {contents(n, objs):g})")
        if k == "overflowing" and Q["load"] > o.volume:
            ex = Q["load"] - o.volume
            pool = next((x for x in n.kids if x.kind == "pooling"), None)
            if pool is not None:
                add_stuff(n, pool.doer, -ex)
                moved.append(make("flowing", pool.doer, ex))
                events.append(f"{n.doer}: overflowing (excess {ex:g} flows out)")
        if k == "leaking":
            pool = next((x for x in n.kids if x.kind == "pooling"), None)
            lk = min(contents(n, objs), max(1.0, Q["pressure"] - o.seal)) if pool else 0.0
            if lk > 0:
                add_stuff(n, pool.doer, -lk)
                moved.append(make("flowing", pool.doer, lk))
                events.append(f"{n.doer}: leaking ({lk:g} escapes)")
        if k in ("containing", "filling") and Q["flow"] < 0:
            # a draw (a flow toward a lower pressure, added 2026-10-23): the contents it pulls out
            # leave the scene that slice, up to what there is
            d = min(contents(n, objs), -Q["flow"])
            if d > 0:
                pool = next(x for x in n.kids if x.kind == "pooling")
                add_stuff(n, pool.doer, -d)
                events.append(f"{n.doer}: {k}, draining (-{d:g}, holds {contents(n, objs):g})")
        if k == "feeding":   # read the bearer's contents for the next slice's pumping
            n.progress = (n.amount or 1.0) * levels.get(parent.doer, 0.0) if parent is not None else 0.0
        if k == "draining":
            pool = next((x for x in n.kids if x.kind == "pooling"), None)
            if pool is None:
                return become(n, "containing", "empty")
            d = min(weight(pool, objs), n.amount or 1.0)
            add_stuff(n, pool.doer, -d)
            moved.append(make("flowing", pool.doer, d))
            events.append(f"{n.doer}: draining ({d:g} leaves)")
        if k == "eroding" and Q["flow"] > 0:
            for x in watches(n):
                if x.watch[1] == "breaking":
                    x.threshold = max(0.0, x.threshold - Q["flow"])
            events.append(f"{n.doer}: eroding (capacity -{Q['flow']:g})")
        if k == "catching":
            falls = [x for x in doings(n) if x.kind == "falling"]
            if falls:
                c = sum(output(x, objs) for x in falls)
                if c > o.capacity:
                    return become(n, "breaking", f"caught {c:g} > reserve {o.capacity:g}")
                kids = [like(x, "resting") if x.kind == "falling" else x for x in doings(n)]
                for x in falls:
                    say(x, "resting", f"caught by {n.doer}")
                return become(like(n, kids=watches(n) + kids), "supporting", "bears what it caught")
        if k == "levering":
            lift = Q["push"] * (n.amount or 1.0)
            keep = []
            for x in doings(n):
                if x.kind in ("resting", "pressing", "piling") and lift > output(x, objs):
                    say(x, "flying", f"levered {lift:g} > its weight {output(x, objs):g}")
                    moved.append(like(x, "flying"))
                else:
                    keep.append(x)
            n.kids = watches(n) + keep
        if k == "siphoning" and parent is not None:
            src, dst = levels.get(parent.doer, 0.0), levels.get(n.against, 0.0)
            if src <= dst:
                return become(n, "standing", "levels match, nothing flows")
            mv = min(n.amount or 1.0, (src - dst) / 2)
            transfers[parent.doer] -= mv
            transfers[n.against] += mv
            events.append(f"{n.doer}: siphoning ({mv:g} from {parent.doer} to {n.against})")
        if k in ("pooling", "flowing"):
            kids = []
            for x in doings(n):
                if x.kind in SOLIDS and objs[x.doer].cohesion < o.solvency:
                    n.amount = weight(n, objs) + output(x, objs)
                    x = become(x, "dissolving", f"{n.doer}'s pull {o.solvency:g} > cohesion "
                                                f"{objs[x.doer].cohesion:g}")
                kids.append(x)
            n.kids = watches(n) + kids
        if k == "pursuing" and Q["drive"] > Q["oppose"]:
            n.progress += Q["drive"] - Q["oppose"]
            events.append(f"{n.doer}: pursuing (progress {n.progress:g})")
        if k == "hesitating":
            pulls = sorted(((x.amount or 0.0) + incoming(x, objs)["drive"], i)
                           for i, x in enumerate(doings(n)) if x.kind in ("wanting", "pursuing"))
            if len(pulls) >= 2 and pulls[-1][0] - pulls[-2][0] > (n.amount or 1.0):
                win = doings(n)[pulls[-1][1]]
                return become(like(n, kids=watches(n) + [win]), "committing",
                              f"{win.doer} outpulls the rest")
        return None

    # ---- rules: conditions on the forces that need no reserve

    def rules(n, Q, parent):
        k, o = n.kind, objs[n.doer]
        loaded = any(x.kind in BORNE for x in n.kids)
        liquid = parent is not None and (parent.kind in STUFF or parent.kind in CONTAINERS)
        return {
            "supporting": [(not loaded, "standing", "nothing borne")],
            "standing": [(loaded, "supporting", "something placed on it")],
            "hanging": [(Q["push"] > 0, "swinging", f"pushed {Q['push']:g}")],
            "swinging": [(Q["push"] == 0, "hanging", "no push, settles")],
            "leaning": [(n.against not in present, "falling", f"{n.against} is gone")],
            "sliding": [(Q["push"] <= o.grip, "resting", "grip recovers"),
                        (not grounded(parent), "falling", "off the edge")],
            "rolling": [(Q["push"] == 0, "resting", "nothing pushing"),
                        (not grounded(parent), "falling", "off the edge")],
            "floating": [(Q["push"] > 0, "drifting", f"pushed {Q['push']:g}"),
                         (not liquid, "resting", "no water under it")],
            "drifting": [(not liquid, "resting", "grounded"),
                         (Q["push"] == 0, "floating", "the current stops")],
            "blocking": [(Q["flow"] > 0, "damming", f"a flow of {Q['flow']:g} held back")],
            "containing": [(Q["flow"] > 0, "filling", f"a flow of {Q['flow']:g} arrives")],
            "filling": [(Q["flow"] == 0, "containing", "the flow stops")],
            "overflowing": [(Q["flow"] == 0, "containing", "the flow stops")],
            "leaking": [(Q["pressure"] <= o.seal, "containing", "pressure under the seal")],
            "flowing": [(grounded(parent) and parent is not None, "pooling", "comes to rest low")],
            "pouring": [(grounded(parent) and parent is not None, "pooling", "comes to rest low")],
            "boiling": [(not (parent is not None and parent.kind in CONTAINERS), "gone",
                         "escapes as vapour")],
            "wanting": [(Q["drive"] > Q["oppose"], "pursuing", "unopposed")],
            "pursuing": [(Q["oppose"] >= Q["drive"], "wanting", "blocked")],
            "yielding": [(Q["push"] == 0, "resisting", "the push lets up")],
            "opening": [(Q["push"] == 0, "sealing", "the push lets up, the seal recloses")],
            "metering": [(parent is not None and levels.get(parent.doer, 0.0) >= o.seal, "shutting",
                          f"the level {levels.get(parent.doer, 0.0) if parent is not None else 0:g} reaches its seal {o.seal:g}")],
            "shutting": [(parent is not None and levels.get(parent.doer, 0.0) <= (n.amount if n.amount is not None else o.seal),
                          "metering", f"the level {levels.get(parent.doer, 0.0) if parent is not None else 0:g} falls to its mark")],
        }.get(k, [])

    def go(n, parent):
        if n.kind == "changing_phase":
            return changing_phase(n.watch, n.threshold)   # a copy: damage must not reach the last slice
        kids = []
        for k in n.kids:
            r = go(k, n)
            if r is None:
                continue
            kids.extend(r if isinstance(r, list) else [r])
        n2 = like(n, kids=kids)
        if n.kind in SETTLE:
            return settle(n2, parent)
        Q = quantities(n, objs)
        for wn in watches(n2):
            if wn.threshold is not None and crossed(Q[wn.watch[0]], wn.watch[2], wn.threshold):
                return phase(n2, wn, Q)
        r = mechanics(n2, Q, parent)
        if r is not None:
            return r
        for cond, to, why in rules(n, Q, parent):
            if cond:
                if to == "gone":
                    events.append(f"{n.doer}: {n.kind} -> gone ({why})")
                    return []
                return become(n2, to, why)
        return n2

    root = go(tree, None)
    root = Node(root.kind, root.kids + moved, root.doer, amount=root.amount)
    if transfers:
        def apply(n):
            if n.kind in CONTAINERS and transfers.get(n.doer):
                pool = next((k for k in n.kids if k.kind == "pooling"), None)
                add_stuff(n, pool.doer if pool else "water", transfers[n.doer])
            for k in doings(n):
                apply(k)
        apply(root)
    return root, events


# ---- printing --------------------------------------------------------------------

def label(n):
    return f"{n.kind}[{n.doer or '<slot>'}]"


def show(n, depth=0, out=None):
    out = [] if out is None else out
    ann = "; ".join(f"-> {w.watch[1]} when {w.watch[0]} {w.watch[2]} "
                    f"{'?' if w.threshold is None else f'{w.threshold:g}'}" for w in watches(n))
    out.append("  " * depth + label(n) + (f"   ({ann})" if ann else ""))
    for k in doings(n):
        show(k, depth + 1, out)
    return out


def fmt(x):
    return "-" if x == INF else f"{x:g}"


def print_force_map(tree, objs):
    edges, rows = force_map(tree, objs)
    print("  external (the edges of the AST):")
    for a, f, b in edges:
        print(f"    {a} --{f:g}--> {b}")
    print("  internal (the doer's reserves, against the loads on and through it):")
    print(f"    {'doing':28}{'load':>7}{'through':>9}{'capacity':>10}{'cohesion':>10}")
    for lbl, ext, out, cap, coh in rows:
        print(f"    {lbl:28}{ext:>7g}{out:>9g}{fmt(cap):>10}{fmt(coh):>10}")


def run(tree, objs):
    """Step until the slice is quiet, printing each diff and slice."""
    i = 0
    while True:
        tree, events = step(tree, objs)
        if not events:
            print(f"\n  slice {i + 1} == slice {i}: the configuration persists (equilibrium).")
            return tree
        i += 1
        print(f"\n  diff -> slice {i} (each line a gerund):")
        for e in events:
            print(f"    {e}")
        print()
        print("\n".join(show(tree, depth=1)))


# ---- demo ------------------------------------------------------------------------

OBJS = {o.name: o for o in [
    Obj("ground", 0.0),
    Obj("snow", 8.0),
    Obj("thatch-roof", 5.0, capacity=20.0, cohesion=30.0),
    Obj("heavy-roof", 9.0, capacity=25.0, cohesion=35.0),
    Obj("stone-post", 6.0, capacity=30.0, cohesion=40.0),
    Obj("oak-beam", 4.0, capacity=12.0, cohesion=30.0),
    Obj("plank", 1.0, capacity=3.0, cohesion=10.0),
    Obj("rope", 0.5, capacity=2.0, cohesion=6.0),
    Obj("brick", 2.5, capacity=20.0, cohesion=50.0),
    Obj("mortared-wall", 10.0, capacity=40.0, cohesion=15.0,
        parts=("brick", "brick", "brick", "brick")),
]}


def main():
    objs = OBJS

    print("== 1. The skeleton: doings with doer slots; phase changes are nodes"
          " with threshold slots ==\n")
    skel = anchoring("ground", slot("supporting", slot("supporting", resting("thatch-roof"))))
    print("\n".join(show(skel)))

    inventory = ("stone-post", "oak-beam", "plank", "rope")
    print(f"\n== 2. Readings: fillings of the {slots(skel)} slots from"
          f" {{{', '.join(inventory)}}} under which the\n"
          "configuration persists: existential validity over force assignments ==\n")
    for picks, events in readings(skel, inventory, objs):
        tag = "a reading" if not events else "no: " + events[0]
        print(f"  outer<-{picks[0]:<12} inner<-{picks[1]:<12} {tag}")
    print("\n  The stone and the oak swap and both readings hold: a post is whatever")
    print("  bears under these forces, and the same plank is invalid in either slot")
    print("  for two different reasons (its own load differs by context).")

    print("\n== 3. One reading wired: the forces read off the AST ==\n")
    scene = wire(skel, ("stone-post", "oak-beam"), objs)
    print("\n".join(show(scene)))
    print()
    print_force_map(scene, objs)

    print("\n== 4. Snow arrives (a new doing borne by the roof): slices and diffs ==\n")
    skel2 = anchoring("ground", slot("supporting", slot("supporting",
                      resting("thatch-roof", pressing("snow")))))
    t = wire(skel2, ("stone-post", "oak-beam"), objs)
    print("\n".join(show(t, depth=1)))
    run(t, objs)

    print("\n== 5. Cohesion: a wall is a node while its mortar holds; it is bricks"
          " when it doesn't ==\n")
    skel3 = anchoring("ground", slot("supporting", resting("heavy-roof")))
    t = wire(skel3, ("mortared-wall",), objs)
    print("\n".join(show(t, depth=1)))
    print()
    print_force_map(t, objs)
    run(t, objs)


if __name__ == "__main__":
    main()
