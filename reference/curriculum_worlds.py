"""The first slice of the curriculum (CURRICULUM_EXPANDED.md, "Recommended first implementation
slice"): five interactive worlds, every one of them forces and potential forces (the user: "Everything
needs to be designed as forces or potential forces. No excuses. Anything can be converted").

Each world: a scene in the force simulator (forces/poc.py), whose invitations are the agent's
actions (a push over a reserve it could cross); one misleading correlate; a held-out variant with
the same structure in different objects. The answer key is ForceWorld.truth(), computed by the
simulator against the no-push slices, never shown to the agent.

    movable block   grip holds a block against a push; a heavier block's grip is larger; a fastened
                    block's is larger still. Correlate: a gust both slides the block and swings a
                    flag hanging beside it (a hidden common driver).
    marble run      a prop holds a marble; the lever leans on the marble, the gate on the lever, the
                    bead on the gate: knocking the prop drops each in turn, one slice apart. Pushing
                    the lever off its lean first breaks the chain. Correlate: a flag that also
                    leans on the lever falls with the gate, a sibling effect and no cause.
    powered button  power is a flow held behind the button's seal; a push opens it and the flow
                    reaches the lamp through the cable's plug, which a hard push unseats or seats
                    again. Correlate: a gust presses the button and swings a flag.
    calculator      each key is a seal on a source of a different size; the register's contents are
                    the display; the reset key opens onto a draw that pulls them out; past the
                    register's volume the excess spills. Correlate: a gust presses key 1 and
                    swings a flag.
    spring / clamp  a clamp's grip holds a compressed spring with a ball on it; a push over the grip
                    releases it, the spring launches the ball. Its pair: a raised weight held by a
                    catch (loading for compressing). Correlate: a gust releases it and swings a flag.
"""
from force_world import poc  # the simulator, on the path force_world sets
from poc import INF, Obj
import copy

from force_world import AMOUNTS, ForceAgent, ForceWorld, effect_id, inv_id, walk
from molecules import Mind, Params


def n(objs, kind, doer, *kids, amount=None, against=None):
    return poc.Node(kind, poc.watches_for(kind, objs[doer]) + list(kids), doer, amount=amount, against=against)


def table(*objs):
    return {o.name: o for o in objs}


FLAG = Obj("flag", 0.2, tear=50.0)        # swings under any push; nothing tears it


# ---- S0-W01 the movable block ------------------------------------------------------------------

def block_world(block="block", grip=3.0, fastened=False, gust=4.0, episode=None):
    O = table(Obj("ground", 0.0), Obj(block, 2.0, grip=grip, base=8.0), FLAG)
    held = "fastening" if fastened else "resting"
    scene = n(O, "anchoring", "ground", n(O, held, block), n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(8, 2, [(block, gust), ("flag", 1.0)])] if gust else [], episode=episode,
                      name=f"block:{block}")


def null_world(movable=False, names=("stone_a", "stone_b", "stone_c", "stone_d")):
    """The null world (OWNERSHIP_SOV.md sec. 10, test B; REORG.md step 8): stones resting on the
    ground, each with a grip of 50 that no push of the agent's (at most 5) crosses. Each invites a
    push (its reserve is finite) and none ever takes: nothing claimable. No gusts and no flag (a flag
    is claimable). movable=True, the ablation: the first stone's grip is 3, one claimable region."""
    O = table(Obj("ground", 0.0), *[Obj(s, 2.0, grip=(3.0 if movable and i == 0 else 50.0), base=8.0)
                                    for i, s in enumerate(names)])
    scene = n(O, "anchoring", "ground", *[n(O, "resting", s) for s in names])
    return ForceWorld(scene, O, gusts=[], episode=None, name="null" + (":movable" if movable else ""))


class NeighbourWorld(ForceWorld):
    """S6-W01 an autonomous neighbouring agent (REORG.md, Stage 6): a world with a second actor whose
    pushes arrive exactly like a gust's, with no doer in what the agent perceives (the user,
    2026-10-25: the agent infers another actor from the pattern, it is not told one exists). Unlike a
    gust, the neighbour pushes toward something: when its object has been out of the state it keeps
    for `delay` ticks, it pushes it back (`amount`), and it does nothing while the state holds."""

    def setup(self, obj, keeps, delay=4, amount=5.0):
        self.keep_obj, self.keeps, self.delay, self.keep_amount, self.away = obj, keeps, delay, amount, 0
        return self

    def gusting(self, t=None):
        out = list(super().gusting(t))
        if t is None or t == self.t:   # the acting tick (not a look ahead): the neighbour's turn
            keeps = self.keeps(self.states()) if callable(self.keeps) else self.keeps
            if self.states().get(self.keep_obj) != keeps:
                self.away += 1
            else:
                self.away = 0
            if self.away >= self.delay:
                out.append((self.keep_obj, self.keep_amount))
                self.away = 0
        return out


def goals_catch(marked=True):
    """S6-W02 same action, different goal (REORG.md Stage 6): the catch with a neighbour whose goal
    depends on the scene. Scene A has a sign standing and the neighbour keeps the latch seated (the
    lid shut); scene B has a post instead and it keeps the latch unseated. marked=False, the
    ambiguous contrast: both scenes have the sign, so nothing the agent perceives tells the goals
    apart. Returns (world, scene A, scene B): the test alternates the scenes."""
    scenes = []
    for marker in ("sign", "post" if marked else "sign"):
        lid, toy, latch, stop = "lid", "toy", "latch", "stop"
        O = table(Obj("ground", 0.0), Obj(lid, 0.5, grip=2.0), Obj("spring", 0.5), Obj(toy, 1.0),
                  Obj(latch, 0.2, grip=-8.0), Obj(stop, 0.0), Obj("sign", 1.0, grip=50.0, base=8.0),
                  Obj("post", 1.0, grip=50.0, base=8.0), FLAG)
        inside = n(O, "compressing", "spring", n(O, "resting", toy), amount=4.0)
        scene = n(O, "anchoring", "ground",
                  n(O, "locking", lid, inside, n(O, "connecting", latch, poc.Node("pushing", [], stop, amount=-10.0))),
                  n(O, "resting", marker), n(O, "hanging", "flag"))
        scenes.append((scene, O))
    (a, O), (b, _) = scenes
    w = NeighbourWorld(a, O, gusts=[(9, 4, [("flag", 1.0)])], episode=None, name="catch:goals")
    keep_b = (lambda st: "parting" if "post" in st else "connecting") if marked else None
    w.setup("latch", keep_b or "connecting")
    if not marked:   # ambiguous: the goal alternates with the scene, the marker does not
        w.scene_goal = {"A": "connecting", "B": "parting"}
        w.current = "A"
        w.keeps = lambda st: w.scene_goal[w.current]
    return w, a, b


class SharedTaskWorld(ForceWorld):
    """S6-W03 a shared task (REORG.md Stage 6). The safety catch, no episodes, whose latch springs back:
    unseated and not held, it is seated again the next slice (a restoring force: it acts whatever
    else is happening). Alone, the agent never opens the lid: the latch is back before its lid push.
    partner="responsive": after the agent's push on the lid fails, a partner holds the latch unseated
    for `hold` slices (the spring overcome), then lets go: its doing is conditioned on the agent's
    need (the user, 2026-10-25: a relation, not just a force). partner="timed": the same hold at
    irregular times, from the world's own seeded source, whatever the agent does. partner=None: the
    spring alone. No doer is perceived in any of these pushes."""

    def setup(self, partner="responsive", hold=4, p=0.15, seed=0, answers=1.0):
        import random
        self.partner, self.hold, self.p, self.answers = partner, hold, p, answers   # answers: the share of
                                                                                   # failed tries it comes for
        self.holding, self.last_inv, self.lid_tried_at = 0, None, None
        self.rng = random.Random(seed)
        return self

    def act(self, inv=None, hold=False):
        self.last_inv = inv
        return super().act(inv, hold)

    def gusting(self, t=None):
        out = list(super().gusting(t))
        if t is not None and t != self.t:   # a look ahead, not the acting slice
            return out
        st = self.states()
        if self.holding:   # the partner is holding the latch unseated
            self.holding -= 1
            if st.get("latch") == "connecting":
                out.append(("latch", 5.0))
            return out
        start = False
        if self.partner == "responsive" and self.lid_tried_at is not None and self.t - self.lid_tried_at == 2 \
                and st.get("lid") == "locking":   # the agent's lid push did not take: the partner comes
            start = self.rng.random() < self.answers   # (sometimes not: then "will they be there?" is a question)
        if self.partner == "timed" and self.rng.random() < self.p:
            start = True
        if self.last_inv is not None and self.last_inv[1] == "lid":
            self.lid_tried_at = self.t
        if start:
            self.holding = self.hold
            if st.get("latch") == "connecting":
                out.append(("latch", 5.0))
        elif st.get("latch") == "parting":   # the spring: not held, it seats the latch again
            out.append(("latch", 5.0))
        return out


def shared_catch(partner="responsive", seed=0, answers=1.0):
    """The catch with a springing latch and a partner (SharedTaskWorld)."""
    w = catch_world(episode=None)
    sw = SharedTaskWorld.__new__(SharedTaskWorld)
    sw.__dict__.update(copy.deepcopy(w.__dict__))
    sw.name = f"catch:shared:{partner}"
    sw.episode = 16   # the lid closes again for another round (the scene set back between pushes)
    return sw.setup(partner, seed=seed, answers=answers)


def neighbour_catch(neighbour=True):
    """The safety catch, no episodes. neighbour=True: a neighbour keeps the latch seated (the lid shut);
    False, the contrast: a gust hits the latch on a timer, moving it both ways (no purpose)."""
    w = catch_world(episode=None)
    nw = NeighbourWorld.__new__(NeighbourWorld)
    nw.__dict__.update(copy.deepcopy(w.__dict__))
    if neighbour:
        nw.setup("latch", "connecting")
    else:
        nw.gusts = list(nw.gusts) + [(7, 3, [("latch", 5.0)])]
        nw.setup("latch", "connecting", delay=10 ** 9)   # never acts
    nw.name = "catch:neighbour" if neighbour else "catch:latch-gust"
    return nw


def block_variants():
    return {"block": block_world(), "heavier": block_world("crate", grip=8.0),
            "fastened": block_world("bolted", grip=50.0, fastened=True)}


def block_heldout():
    return block_world("brick", grip=4.0)


# ---- S1-W03 the three-step marble run ----------------------------------------------------------

def marble_world(names=("prop", "marble", "lever", "gate", "bead"), episode=12, fork=False):
    """fork: the gate leans on the marble, not on the lever (S5-W04: the same objects in the same
    gerunds, a fork for a chain; pushing the lever off its lean no longer saves the bead)."""
    p, m, l, g, b = names
    O = table(Obj("ground", 0.0), Obj(p, 1.0, base=1.5), Obj(m, 1.0), Obj(l, 2.0, grip=4.0),
              Obj(g, 2.0, grip=4.0), Obj(b, 0.5), Obj("flag", 0.3, grip=2.0))
    scene = n(O, "anchoring", "ground",
              n(O, "supporting", p, n(O, "resting", m)),
              n(O, "leaning", l, against=m),
              n(O, "leaning", g, against=m if fork else l),
              n(O, "leaning", b, against=g),
              n(O, "leaning", "flag", against=l))
    return ForceWorld(scene, O, horizon=5, episode=episode, name=f"marble:{p}")


def marble_heldout():
    return marble_world(("stake", "stone", "arm", "door", "pebble"))


# ---- S2-W01 the powered button -----------------------------------------------------------------

def button_world(names=("lamp", "cable", "button", "power"), connected=True, episode=None, gusts=True):
    lamp, cable, button, power = names
    O = table(Obj("ground", 0.0), Obj(lamp, 0.5), Obj(cable, 0.2, grip=3.0),
              Obj(button, 0.2, seal=0.5), Obj(power, 0.0), Obj("water", 0.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "containing", lamp,
                n(O, "connecting" if connected else "parting", cable,
                  n(O, "sealing", button, n(O, "flowing", power, amount=1.0)))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(11, 3, [(button, 1.0), ("flag", 1.0)])] if gusts else [], episode=episode,
                      name=f"button:{button}")


def button_heldout(connected=False):
    """A different apparatus, same structure: a tap on a tank's outflow, through a hose, into a
    bucket."""
    return button_world(("bucket", "hose", "tap", "tank"), connected=connected)


# ---- S3-W02 the unfamiliar calculator ----------------------------------------------------------

def calculator_world(names=("register", "key1", "key2", "reset"), sizes=(1.0, 2.0), volume=5.0,
                     episode=None):
    reg, k1, k2, rs = names
    O = table(Obj("ground", 0.0), Obj(reg, 0.5, volume=volume), Obj(k1, 0.0, seal=0.5),
              Obj(k2, 0.0, seal=0.5), Obj(rs, 0.0, seal=0.5), Obj("src1", 0.0), Obj("src2", 0.0),
              Obj("drain", 0.0), Obj("water", 0.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "containing", reg,
                n(O, "sealing", k1, n(O, "flowing", "src1", amount=sizes[0])),
                n(O, "sealing", k2, n(O, "flowing", "src2", amount=sizes[1])),
                n(O, "sealing", rs, n(O, "flowing", "drain", amount=-100.0))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(11, 4, [(k1, 1.0), ("flag", 1.0)])], episode=episode,
                      gauges=(reg,), name=f"calculator:{reg}")


def calculator_heldout():
    """A differently shaped device: a barrel with a small tap, a large tap and a bung."""
    return calculator_world(("barrel", "small_tap", "large_tap", "bung"), sizes=(1.0, 3.0), volume=6.0)


# ---- S3 spring / clamp, and the raised weight --------------------------------------------------

def spring_world(store="compressing", names=("clamp", "spring", "ball"), episode=12):
    c, s, b = names
    O = table(Obj("ground", 0.0), Obj(c, 0.5, grip=2.0), Obj(s, 0.5), Obj(b, 1.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "locking", c, n(O, store, s, n(O, "resting", b), amount=4.0)),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(13, 7, [(c, 3.0), ("flag", 1.0)])], episode=episode,
                      name=f"store:{s}")


def weight_world():
    """The raised weight: a catch holds a weight that is loading (stored by being raised)."""
    return spring_world("loading", ("catch", "weight", "stone"))


# ---- the rest of stages 1-2 (built 2026-10-23, after the first slice) ---------------------------

def lights_world(episode=None):
    """S1-W01 paired lights: two lamps, each behind its own plug and valve; a hidden driver (a gust
    on a timer) opens valve A, and the next slice valve B, so lamp A lights and then lamp B, every
    time. The valves' seals (50) are past any push of the agent's; it can unseat either plug. The
    trap: A lights before B, reliably, so A seems to cause B; unseating A's plug leaves B lighting
    on time. An unrelated bell swings on its own timer."""
    O = table(Obj("ground", 0.0), Obj("lamp_a", 0.5), Obj("lamp_b", 0.5), Obj("plug_a", 0.2, grip=3.0),
              Obj("plug_b", 0.2, grip=3.0), Obj("valve_a", 0.0, seal=50.0), Obj("valve_b", 0.0, seal=50.0),
              Obj("src_a", 0.0), Obj("src_b", 0.0), Obj("water", 0.0), Obj("bell", 0.2, tear=50.0))
    scene = n(O, "anchoring", "ground",
              n(O, "containing", "lamp_a", n(O, "connecting", "plug_a", n(O, "sealing", "valve_a",
                                                                          n(O, "flowing", "src_a", amount=1.0)))),
              n(O, "containing", "lamp_b", n(O, "connecting", "plug_b", n(O, "sealing", "valve_b",
                                                                          n(O, "flowing", "src_b", amount=1.0)))),
              n(O, "hanging", "bell"))
    # timers of 6 (DRIFT.md: once changed to 7 to keep a timer out of step with the earlier agent's
    # rhythm, tuning the world to the agent; the SOV-driven agent varies its moments itself)
    return ForceWorld(scene, O, gusts=[(6, 1, [("valve_a", 60.0)]), (6, 2, [("valve_b", 60.0)]),
                                       (7, 5, [("bell", 1.0)])], episode=episode, name="lights")


def catch_world(spring=True, names=("lid", "toy", "latch", "stop"), episode=12):
    """S2-W02 safety catch: a lid held by its grip (2) over a compressed spring with a toy on it; a
    push over the grip releases the lid and the spring launches the toy. The latch, seated, passes
    its stop's counter-push (-10) to the lid, so no push of the agent's crosses the grip: it
    prevents the transition rather than opposing a movement in progress. A hard push unseats or
    seats the latch. spring=False: the nonfunctional lid (released, nothing launches)."""
    lid, toy, latch, stop = names
    O = table(Obj("ground", 0.0), Obj(lid, 0.5, grip=2.0), Obj("spring", 0.5), Obj(toy, 1.0),
              Obj(latch, 0.2, grip=-8.0), Obj(stop, 0.0), FLAG)   # the latch feels its own stop's
    # -10 too: its grip, net of that, is -8, so a push over 2 unseats it, or seats it again
    inside = n(O, "compressing", "spring", n(O, "resting", toy), amount=4.0) if spring else n(O, "resting", toy)
    scene = n(O, "anchoring", "ground",
              n(O, "locking", lid, inside, n(O, "connecting", latch, poc.Node("pushing", [], stop, amount=-10.0))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, name=f"catch:{lid}")


def and_world(names=("lamp", "plug_a", "plug_b", "button", "power"), episode=None, seated=(False, False), gusts=True):
    """S2-W03 AND: the flow behind the button reaches the lamp only through two plugs in series; a
    press lights it only when both are seated (an AND of two conditions, each set by a hard push)."""
    lamp, pa, pb, button, power = names
    O = table(Obj("ground", 0.0), Obj(lamp, 0.5), Obj(pa, 0.2, grip=3.0), Obj(pb, 0.2, grip=3.0),
              Obj("hose", 0.1), Obj(button, 0.0, seal=0.5), Obj(power, 0.0), Obj("water", 0.0), FLAG)
    g = lambda s: "connecting" if s else "parting"
    # a hose between the plugs passes the flow and not a push (a plug passes both: first, pushing
    # plug B toggled plug A too)
    scene = n(O, "anchoring", "ground",
              n(O, "containing", lamp, n(O, g(seated[0]), pa, n(O, "channeling", "hose", n(O, g(seated[1]), pb,
                                                                 n(O, "sealing", button, n(O, "flowing", power, amount=1.0)))))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(10, 6, [("flag", 1.0)])] if gusts else [], episode=episode, name="and")


def renamed(world, names):
    """The same world with objects renamed (old -> new): its scene, objects, gusts and gauges. Each
    world's flag is its own object; under one name, a mind that lives in several worlds joins
    their understanding through it into one structure (found: no analogy between two worlds ever
    formed, the flags' swinging bridged them)."""
    import dataclasses
    r = lambda d: names.get(d, d)

    def go(n):
        return poc.Node(n.kind, [go(k) for k in n.kids], r(n.doer), watch=n.watch, threshold=n.threshold,
                        amount=n.amount, against=r(n.against) if n.against else None, progress=n.progress)
    objs = {r(k): dataclasses.replace(o, name=r(k)) for k, o in world.objs.items()}
    gusts = [(p, off, [(r(d), a) for d, a in pushes]) for p, off, pushes in world.gusts]
    w = ForceWorld(go(world.start), objs, horizon=world.horizon, gamma=world.gamma, gusts=gusts,
                   episode=world.episode, gauges={r(g) for g in world.gauges},
                   sensors={r(s) for s in world.sensors}, name=world.name)
    w.phase = world.phase
    return w


# ---- stage 5: same structure, different stuff; and a false analogy (built 2026-10-23) ----------

def guard_world(names=("file", "guard", "rule"), guarded=False, episode=None):
    """S5-W01's third enabling system, permission / command / file, in the agents' gerunds: a file
    resisting (resolve 2) a command, which is the agent's push; a guard, seated, passes its rule's
    counter-push (-10) to the file, so no command gets through; a hard push lifts the guard or seats
    it again (its grip, net of the rule's -10, is -8, as the safety catch's latch). guarded: the
    guard starts seated."""
    f, gd, rule = names
    O = table(Obj("ground", 0.0), Obj(f, 0.0, resolve=2.0), Obj(gd, 0.0, grip=-8.0), Obj(rule, 0.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "resisting", f, n(O, "connecting" if guarded else "parting", gd,
                                     poc.Node("pushing", [], rule, amount=-10.0))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, name=f"guard:{f}")


# ---- the rest of stages 1-2 (built 2026-10-23, second round) -----------------------------------

def chime_world(episode=None):
    """S1-W02 striker and chime: a chime hangs; a striker against it passes a push to it, and the chime
    swings (it sounds). A damper, seated against the chime, passes its stop's -10, so a strike is a
    silent near miss; a hard push seats or unseats the damper (its grip net of the stop, -8). Contact
    is the condition, as the damper's absence. (First: the striker on a seated arm, but an arm on
    the push's path is itself pushed, and the strike unseated it.)"""
    O = table(Obj("ground", 0.0), Obj("chime", 0.5, tear=50.0, tensile=10.0), Obj("damper", 0.1, grip=-8.0), Obj("stop", 0.0),
              Obj("striker", 0.1, tear=50.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "hanging", "chime", n(O, "transmitting", "striker"),
                n(O, "connecting", "damper", poc.Node("pushing", [], "stop", amount=-10.0))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, name="chime")


def source_world(episode=12):
    """S1-W04 one source, two effects: two stones rest on one lever (ratio 6); a push on the lever
    launches both in the same slice. Neither stone's flight is the other's cause."""
    O = table(Obj("ground", 0.0), Obj("lever", 1.0, grip=20.0), Obj("stone_a", 2.0, grip=8.0, base=20.0),
              Obj("stone_b", 2.0, grip=8.0, base=20.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "levering", "lever", n(O, "resting", "stone_a"), n(O, "resting", "stone_b"), amount=6.0),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, name="source")


def paths_world(episode=None):
    """S1-W05 two paths to the same bell: one lamp, two lines into it, each a button behind its own
    plug. Unseating one plug stops that button lighting the lamp, not the other."""
    O = table(Obj("ground", 0.0), Obj("lamp", 0.5), Obj("plug_a", 0.2, grip=3.0), Obj("plug_b", 0.2, grip=3.0),
              Obj("button_a", 0.0, seal=0.5), Obj("button_b", 0.0, seal=0.5), Obj("src_a", 0.0),
              Obj("src_b", 0.0), Obj("water", 0.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "containing", "lamp",
                n(O, "connecting", "plug_a", n(O, "sealing", "button_a", n(O, "flowing", "src_a", amount=1.0))),
                n(O, "connecting", "plug_b", n(O, "sealing", "button_b", n(O, "flowing", "src_b", amount=1.0)))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, name="paths")


def sequence_world(episode=None):
    """S1-W06 sequence versus causation: a ticking lamp and an automatic door (a lamp standing for
    it), each opened by its own timer, the tick one slice before the door, every time. The agent can
    unseat the tick's plug; the door keeps its time. (The force structure of S1-W01, renamed.)"""
    return renamed(lights_world(episode), {"lamp_a": "tick", "plug_a": "tick_plug", "valve_a": "tick_valve",
                                           "lamp_b": "door", "plug_b": "door_plug", "valve_b": "door_valve"})


def redundant_world(episode=None):
    """S2-W04 redundant mechanisms (OR): one button, two sources behind it, each through its own plug;
    a press lights the lamp when either plug is seated."""
    O = table(Obj("ground", 0.0), Obj("lamp", 0.5), Obj("button", 0.0, seal=0.5), Obj("plug_a", 0.2, grip=3.0),
              Obj("plug_b", 0.2, grip=3.0), Obj("hose_a", 0.1), Obj("hose_b", 0.1), Obj("src_a", 0.0),
              Obj("src_b", 0.0), Obj("water", 0.0), FLAG)
    # hoses between the plugs and the button pass the flow and not a push (a plug passes both)
    scene = n(O, "anchoring", "ground",
              n(O, "containing", "lamp",
                n(O, "sealing", "button",
                  n(O, "channeling", "hose_a", n(O, "connecting", "plug_a", n(O, "flowing", "src_a", amount=1.0))),
                  n(O, "channeling", "hose_b", n(O, "parting", "plug_b", n(O, "flowing", "src_b", amount=1.0))))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, name="redundant")


def reversal_world(episode=None):
    """S2-W05 context reversal: one button, two lines behind it: a fill line (+1) and a drain line (a
    draw of 3), each through its own plug. The same press fills the register or drains it, by which
    line is seated. The register starts holding 3 and its level is displayed."""
    O = table(Obj("ground", 0.0), Obj("register", 0.5), Obj("button", 0.0, seal=0.5), Obj("fill", 0.2, grip=3.0),
              Obj("drain", 0.2, grip=3.0), Obj("hose_f", 0.1), Obj("hose_d", 0.1), Obj("src", 0.0), Obj("sink", 0.0),
              Obj("water", 0.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "containing", "register", n(O, "pooling", "water", amount=3.0),
                n(O, "sealing", "button",
                  n(O, "channeling", "hose_f", n(O, "connecting", "fill", n(O, "flowing", "src", amount=1.0))),
                  n(O, "channeling", "hose_d", n(O, "parting", "drain", n(O, "flowing", "sink", amount=-3.0))))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, gauges=("register",),
                      name="reversal")


def enabler_world(episode=None):
    """S2-W06 false enabler: the powered button, and beside it a blue indicator whose plug a slow
    timer seats and unseats (every 13 ticks); it lights nothing the button needs. Early on its state
    can line up with the cable's by chance."""
    O = table(Obj("ground", 0.0), Obj("lamp", 0.5), Obj("cable", 0.2, grip=3.0), Obj("button", 0.2, seal=0.5),
              Obj("power", 0.0), Obj("water", 0.0), Obj("indicator", 0.2, grip=50.0))
    scene = n(O, "anchoring", "ground",
              n(O, "containing", "lamp", n(O, "connecting", "cable",
                                           n(O, "sealing", "button", n(O, "flowing", "power", amount=1.0)))),
              n(O, "connecting", "indicator"))
    return ForceWorld(scene, O, gusts=[(13, 6, [("indicator", 60.0)])], episode=episode, name="enabler")


# ---- stage 3: making things happen (built 2026-10-23) ------------------------------------------

def control_world(episode=None):
    """S3-W01 controllable versus uncontrollable: lamp A behind the agent's button (seal 0.5); lamp
    B behind a valve whose seal (50) no push of the agent's crosses, opened by a timer. Both light
    often; only one is the agent's to light."""
    O = table(Obj("ground", 0.0), Obj("lamp_a", 0.5), Obj("lamp_b", 0.5), Obj("button", 0.0, seal=0.5),
              Obj("valve", 0.0, seal=50.0), Obj("src_a", 0.0), Obj("src_b", 0.0), Obj("water", 0.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "containing", "lamp_a", n(O, "sealing", "button", n(O, "flowing", "src_a", amount=1.0))),
              n(O, "containing", "lamp_b", n(O, "sealing", "valve", n(O, "flowing", "src_b", amount=1.0))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(6, 2, [("valve", 60.0)]), (9, 5, [("flag", 1.0)])], episode=episode,
                      name="control")   # timer 6 again (DRIFT.md; it was 7 for the earlier agent's rhythm)


def lock_world(episode=12):
    """S3-W03 a key, a lock and a door: the door is held by its grip (2), and a lock, seated, passes
    its stop's counter-push (-10) to it. The right key sits in the lock and passes a push to it: a
    hard push on the key unseats the lock (its grip net of the stop is -8), or seats it again. The
    wrong key rests beside it (grip 1) and moves under any push, to no effect on the door. The door,
    unlocked and pushed, releases (opens)."""
    O = table(Obj("ground", 0.0), Obj("door", 0.5, grip=2.0), Obj("lock", 0.0, grip=-8.0), Obj("stop", 0.0),
              Obj("key", 0.1, tear=50.0), Obj("wrong_key", 0.1, grip=1.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "locking", "door", n(O, "connecting", "lock", poc.Node("pushing", [], "stop", amount=-10.0),
                                        n(O, "transmitting", "key"))),
              n(O, "resting", "wrong_key"),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, name="lock")


def lever_world(episode=12):
    """S3-W04, as a lever (the ramp's job, a small force doing what a large one cannot, in the
    vocabulary there is): a stone (5) whose grip (8) no push of the agent's crosses rests on a lever
    of ratio 6; a light push (1) on the lever lifts 6 and launches it."""
    O = table(Obj("ground", 0.0), Obj("lever", 1.0, grip=20.0), Obj("stone", 5.0, grip=8.0, base=20.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "levering", "lever", n(O, "resting", "stone"), amount=6.0),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, name="lever")


# ---- stage 4: systems (built 2026-10-23) --------------------------------------------------------

def parts_world(episode=None):
    """S4-W01 remove one part: the button's flow reaches the lamp through three plugs in series
    (hoses between them pass the flow, not a push); a fourth plug on a dead line beside it carries
    nothing. Every plug of the three is needed, the fourth is not."""
    O = table(Obj("ground", 0.0), Obj("lamp", 0.5), Obj("button", 0.0, seal=0.5), Obj("power", 0.0),
              Obj("water", 0.0), *[Obj(f"plug_{i}", 0.2, grip=3.0) for i in (1, 2, 3, 4)],
              *[Obj(f"hose_{i}", 0.1) for i in (1, 2, 3)], FLAG)
    line = n(O, "sealing", "button", n(O, "flowing", "power", amount=1.0))
    for i in (3, 2, 1):
        line = n(O, "connecting", f"plug_{i}", n(O, "channeling", f"hose_{i}", line))
    scene = n(O, "anchoring", "ground", n(O, "containing", "lamp", line), n(O, "connecting", "plug_4"),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, name="parts")


def regulator_world(high=4.0, low=3.0, episode=None, name="regulator"):
    """S4-W02 negative feedback: a tank fed through a float valve (open under its seal, `high`;
    closed until the level falls to its mark, `low`) and drawn on steadily (0.5 a slice). The level
    settles in the band. A drain button (a draw of 3) lowers it; the float reopens and refills it."""
    O = table(Obj("ground", 0.0), Obj("tank", 0.5, volume=20.0), Obj("float", 0.1, seal=high), Obj("src", 0.0),
              Obj("use", 0.0), Obj("drain_button", 0.0, seal=0.5), Obj("drain", 0.0), Obj("water", 0.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "containing", "tank",
                n(O, "metering", "float", n(O, "flowing", "src", amount=1.0), amount=low),
                n(O, "flowing", "use", amount=-0.5),
                n(O, "sealing", "drain_button", n(O, "flowing", "drain", amount=-3.0))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, horizon=6, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, gauges=("tank",),
                      name=name)


def runaway_world(episode=16):
    """S4-W03 positive feedback: a pump stands in a tank and passes the flow behind its primer plus
    the tank's level: a press of the primer (+1) starts it, and each slice brings in more than the
    last until the tank bursts (capacity 20). A small push, a delayed failure."""
    O = table(Obj("ground", 0.0), Obj("tank", 0.5, capacity=20.0, volume=30.0, parts=("staves",)), Obj("staves", 0.5),
              Obj("pump", 0.1), Obj("primer", 0.0, seal=0.5), Obj("src", 0.0), Obj("water", 0.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "containing", "tank",
                n(O, "feeding", "pump", n(O, "sealing", "primer", n(O, "flowing", "src", amount=1.0)), amount=2.0)),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, horizon=9, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, gauges=("tank",),
                      name="runaway")


def threshold_world(episode=24):
    """S4-W04 the threshold container: a bucket hangs from a rope (tensile 4); a key adds 1 to it per
    press. Three presses change nothing but the level; the fourth snaps the rope."""
    O = table(Obj("ground", 0.0), Obj("rope", 0.1, tensile=4.0), Obj("bucket", 0.5), Obj("key", 0.0, seal=0.5),
              Obj("src", 0.0), Obj("water", 0.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "hanging", "rope", n(O, "containing", "bucket", n(O, "sealing", "key", n(O, "flowing", "src", amount=1.0)))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, gauges=("bucket",), name="threshold")


def opposing_world(episode=None):
    """S4-W05 opposing forces: a block (grip 3) braced by a stop pressing back (-5) through a brace; a
    hard push on the block is balanced and nothing moves, but the block is pressed harder (a sensor
    reads it). Unbraced (a hard push on the brace, whose grip net of its stop is -1), the same push
    slides the block."""
    O = table(Obj("ground", 0.0), Obj("block", 2.0, grip=3.0, base=20.0), Obj("brace", 0.1, grip=-1.0),
              Obj("stop", 0.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "resting", "block", n(O, "connecting", "brace", poc.Node("pushing", [], "stop", amount=-5.0))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, sensors=("block",), name="opposing")


def hysteresis_world(episode=None):
    """S4-W06 hysteresis: the regulator with a wide band (closes at 6, reopens only at 2) and no
    steady draw. Full and drained once, the level stands at 3 with the float closed and stays there;
    rising from empty through 3, the float is open and it fills on. The same level, two futures."""
    w = regulator_world(high=6.0, low=2.0, name="hysteresis")
    for x in walk(w.start):
        if x.doer == "use":
            x.amount = 0.0
    w.reset()   # the scene in play is a copy of the start (first: edited after it was taken)
    return w


def cascade_world(episode=None):
    """S4-W07 failure cascades: a pond on a shelf (capacity 7) fed 1 a slice and emptied 1 a slice
    through a gate. Unseat the gate and the pond fills; past 6.5 the shelf breaks and the pond falls.
    Seat the gate again early and the level holds where it got to; late, and nothing is left to save."""
    O = table(Obj("ground", 0.0), Obj("shelf", 0.5, capacity=7.0), Obj("pond", 0.5, volume=30.0), Obj("src", 0.0),
              Obj("gate", 0.2, grip=3.0), Obj("outlet", 0.0), Obj("water", 0.0), FLAG)
    scene = n(O, "anchoring", "ground",
              n(O, "supporting", "shelf",
                n(O, "containing", "pond", n(O, "flowing", "src", amount=1.0),
                  n(O, "connecting", "gate", n(O, "flowing", "outlet", amount=-1.0)))),
              n(O, "hanging", "flag"))
    return ForceWorld(scene, O, horizon=10, gusts=[(9, 4, [("flag", 1.0)])], episode=episode, gauges=("pond",),
                      name="cascade")


def worlds():
    """The slice, in curriculum order: name -> (discovery world, held-out world)."""
    return {"block": (block_world(), block_heldout()),
            "marble": (marble_world(), marble_heldout()),
            "button": (button_world(), button_heldout()),
            "calculator": (calculator_world(), calculator_heldout()),
            "spring": (spring_world(), weight_world())}


# ---- running and reading out -------------------------------------------------------------------

PROBES = {   # configurations the readout asks about: pushes made from the start, each let settle
    "block": [[]],
    "marble": [[], [("hard", 2)]],                     # the lever pushed off its lean first
    "button": [[], [("hard", 1)]],                     # the plug unseated
    "calculator": [[], [("light", 1)], [("light", 2), ("light", 2)]],   # at 0, 1 and 4
    "spring": [[]],
    "lights": [[], [("hard", 1)]],                                   # plug A unseated
    "catch": [[], [("hard", 3)]],                                    # the latch unseated
    "and": [[], [("hard", 1)], [("hard", 3)], [("hard", 1), ("hard", 3)]],   # none, A, B, both
    "chime": [[], [("hard", 2)]],                                    # the damper off
    "source": [[]],
    "paths": [[], [("hard", 1)], [("hard", 3)]],                     # plug A out, plug B out
    "redundant": [[], [("hard", 3)], [("hard", 5)], [("hard", 3), ("hard", 5)]],   # A, none, both, B
    "reversal": [[], [("hard", 3), ("hard", 5)]],                    # fill seated; drain seated
    "enabler": [[], [("hard", 1)]],                                  # the cable out
}


def after(world, pushes):
    """The scene after pushes from the start, each let settle for the world's horizon. A push names
    its object by its place among the scene's objects (so the same probe fits a held-out world)."""
    tree = copy.deepcopy(world.start)
    names = [d for d in world.states(tree) if d in world.objs and d != "ground" and "flag" not in d]
    for strength, i in pushes:
        tree = world._apply(tree, names[i], AMOUNTS[strength])
        for k in range(world.horizon):
            tree, _ = poc.step(tree, world.objs)
            if k == 0:
                tree = world._unpush(tree)
    return tree


AGENT = None   # the agent class the harness builds (None: the SOV-driven agent, sov_agent.SovAgent)


def make(world, mind=None):
    """An agent for a world (DRIFT.md, the repair: the SOV-driven agent by default; ForceAgent is the
    earlier one, kept as a baseline where a readout measures one of its own mechanisms)."""
    if AGENT is not None:
        return AGENT(world, mind)
    from sov_agent import SovAgent
    return SovAgent(world, mind)


def run(world, ticks, mind=None):
    agent = make(world, mind)
    for _ in range(ticks):
        agent.tick()
    return agent


def conds(agent):
    """The conditions an agent has read, per push: {invitation: [condition, ...]}, a condition a list of
    facts (an AND; several are alternatives). The SOV-driven agent's are the meta layer's splits."""
    if isinstance(agent, ForceAgent):
        return {i: [list(x) for x in v] for i, v in agent.conds.items() if v}
    return {i: [[t] for t in agent.conditions_of(i)] for i in agent.known.values() if agent.conditions_of(i)}


def outcomes_of(agent, inv):
    """What each try of a push did, in order: [frozenset of effects]."""
    if isinstance(agent, ForceAgent):
        return [es for _, es in agent.seen.get(inv, [])]
    return [frozenset(names) for _, i, names in agent.tried if i == inv]


def readout(agent, world, probes):
    """Per probed configuration and invitation: what the push really does (truth, all slices) and
    what the agent predicts there. Returns rows (probe, invitation, truth, prediction) and the
    shares tried and right (among tried)."""
    rows = []
    for p in probes:
        tree = after(world, p)
        facts = agent.facts_now(tree)
        for inv, got in world.truth(tree).items():
            true = frozenset(set().union(*got.values())) if got else frozenset({"no_change"})
            rows.append((tuple(p), inv, true, agent.predict(inv, facts, tree)))
    tried = [r for r in rows if r[3] is not None]
    right = [r for r in tried if r[3] == r[2]]
    return rows, len(tried) / len(rows), (len(right) / len(tried) if tried else 0.0)


def right_all(rows):
    """Share of all probed rows predicted exactly (no prediction counts as wrong)."""
    return sum(1 for r in rows if r[3] is not None and r[3] == r[2]) / len(rows)


def transfer(name, ticks=150, later=15):
    """Held-out prediction with and without transfer: the discovery agent's tries carried to the
    held-out world, read out before any push there and after `later` ticks there (each arm with its
    own copy of the discovery mind). Returns {arm: (right_all at 0, right_all after later)}.
    The earlier agent's mechanism (transfer by configuration; DRIFT.md: its home is analogy), so a
    baseline readout: it runs on ForceAgent."""
    w, h = worlds()[name]
    a = ForceAgent(w)
    for _ in range(ticks):
        a.tick()
    out = {}
    for arm in (False, True):
        b = ForceAgent(copy.deepcopy(h), copy.deepcopy(a.mind), experience=a, analogy=arm)
        r0 = right_all(readout(b, b.world, PROBES[name])[0])
        for _ in range(later):
            b.tick()
        out["analogy" if arm else "no analogy"] = (round(r0, 2), round(right_all(readout(b, b.world, PROBES[name])[0]), 2))
    return out


def overlap(rows):
    """Mean Jaccard overlap of predicted and true effects over the tried rows (partial credit)."""
    tried = [(t, p) for _, _, t, p in rows if p is not None]
    return sum(len(t & p) / len(t | p) for t, p in tried) / len(tried) if tried else 0.0


def beliefs(agent):
    """The agent's worked-out causal links between effects (not its own pushes): (cause, effect,
    funding)."""
    und = agent.mind.understanding
    out = []
    for c, rels in und.rel.items():
        if c.startswith(("light_push", "hard_push", "q:", "sov:")):
            continue
        for (r, o), e in rels.items():
            if r == "causes" and e[2] > 0:
                out.append((c, o, round(e[2], 2)))
    return sorted(out)


def enabling(ticks=150, later=100):
    """S5-W01: one mind through the powered button, then the safety catch, then the guarded file
    (guard lifted at the start; 100 ticks there, first 40, too few to find its condition once the
    agent rests between tries). Returns the abstract structures formed and, for each abstract
    whose pattern holds a condition on an action, which domains' pushes fill that action's role
    (same structure, different stuff: the press, the lid push, the command)."""
    a = run(renamed(button_world(), {"flag": "flag_1"}), ticks)
    b = make(renamed(catch_world(), {"flag": "flag_2"}), a.mind)
    for _ in range(ticks):
        b.tick()
    und = a.mind.understanding
    g = make(renamed(guard_world(), {"flag": "flag_3"}), a.mind)
    for _ in range(later):
        g.tick()
    out = {"abstracts": [(x["id"], sorted(x["pattern"]), x["members"]) for x in und.abstracts]}
    # the enabling correspondence: an abstract whose pattern holds a condition on an action, and
    # which of the three domains' pushes fill that action's role
    pushes = {"button": "push:button", "catch": "push:lid", "guard": "push:file"}
    out["enabling"] = []
    for x in und.abstracts:
        acts = [(r, rel) for rel, p, r in x["pattern"] if rel in ("conditions", "enables", "prevents")]
        for r, rel in acts:
            fill = {m.get(r) for m in x["members"]}
            out["enabling"].append((x["id"], rel, sorted(d for d, p in pushes.items() if any(p in (v or "") for v in fill))))
    return out


def reach(edges, root):
    """The causal edges reachable forward from a node: what a push sets going."""
    out, todo, seen = set(), [root], {root}
    while todo:
        x = todo.pop()
        for e in edges:
            if e[0] == "causes" and e[1] == x:
                out.add(e)
                if e[2] not in seen:
                    seen.add(e[2])
                    todo.append(e[2])
    return frozenset(out)


def false_analogy(ticks=150, later=60):
    """S5-W04: a mind trained on the chain marble run, carried to a renamed chain and to a renamed
    fork (the door leans on the stone, not on the arm). Before any push there, surface transfer
    (same gerunds) predicts that a stake push after the arm was pushed off its lean leaves the
    pebble standing: right in the chain, wrong in the fork. After `later` ticks of its own pushes,
    its own prediction, and which link to the door's fall its understanding holds: from the arm
    (a chain) or from the stone (a fork). The surface transfer is the earlier agent's mechanism
    (ForceAgent, a baseline); exploring the renamed worlds and the links read are the default agent's,
    its mind carried from the chain."""
    base = ForceAgent(marble_world())
    for _ in range(ticks):
        base.tick()
    a = run(marble_world(), ticks)
    names = ("stake", "stone", "arm", "door", "pebble")
    out = {}
    push = ("hard", "stake", "supporting")
    for kind, w in (("chain", renamed(marble_world(names), {"flag": "flag_2"})),
                    ("fork", renamed(marble_world(names, fork=True), {"flag": "flag_2"}))):
        t = after(w, [("hard", 2)])
        got = w.truth(t)[push]
        true = "pebble_falling" in set().union(*got.values())
        sb = ForceAgent(copy.deepcopy(w), copy.deepcopy(base.mind), experience=base)
        before = sb.predict(push, sb.facts_now(t), t)
        b = make(w, copy.deepcopy(a.mind))
        for _ in range(later):
            b.tick()
        own = b.predict(push, b.facts_now(t), t)
        edges = b.mind.understanding.edges()
        out[kind] = dict(pebble_really_falls=true,
                         surface_predicts=("pebble_falling" in (before or ())),
                         own_predicts=("pebble_falling" in own) if own else None,
                         arm_to_door=("causes", "arm_falling", "door_falling") in edges,
                         stone_to_door=("causes", "stone_falling", "door_falling") in edges)
    return out


def pursue(agent, world, start, goal, ticks=40, want=True):
    """Set the world to `start` (no gusts) and count the agent's pushes until the goal effect happens
    (None: not within `ticks`); want=False: the goal is not given to the agent (curiosity only).
    Returns (pushes, the pushes made)."""
    w = copy.deepcopy(world)
    w.gusts, w.episode = [], None
    w.tree, w.diffs = copy.deepcopy(start), []
    agent.world, agent.goal, agent.watching = w, goal if want else None, None
    made = []
    for _ in range(ticks):
        choice, _ = agent.tick()
        if choice is not None:
            made.append(choice)
        if any(effect_id(e) == goal for e in w.diffs):
            return len(made), made
    return None, made


def stage3(explore=150):
    """S3: per world, an agent explores (curiosity, gusts on), then is set a goal from a set-up start.
    Pushes to the goal with its plan, against the same explored agent not given the goal (curiosity
    only), and a fresh agent given the goal (nothing learned yet, so no plan at first)."""
    cases = {
        "button": (button_world(), [("hard", 1)], "lamp_filling"),           # the cable unseated
        "lock": (lock_world(), [], "door_releasing"),                        # locked
        "lever": (lever_world(), [], "stone_flying"),
        "assembly": (and_world(), [], "lamp_filling"),                       # S3-W06: both plugs out
        "control A": (control_world(), [], "lamp_a_filling"),
        "control B": (control_world(), [], "lamp_b_filling"),                # not the agent's to light
    }
    out = {}
    for name, (w, setup, goal) in cases.items():
        a = run(copy.deepcopy(w), explore)
        start = after(w, setup)
        p = copy.deepcopy(a)
        pushes = pursue(p, w, start, goal)[0]
        out[name] = dict(plan=a.plan(goal, w.states(start)), pushes=dict(
            plan=pushes,
            curiosity=pursue(copy.deepcopy(a), w, start, goal, want=False)[0],
            fresh=pursue(make(copy.deepcopy(w)), w, start, goal)[0]),
            plan_after=p.plan(goal, w.states(start)))   # what it plans once it has pursued
    return out


def stage12(ticks=150):
    """The second round of stages 1-2, each world explored for `ticks` (gusts on): exact share of
    probes, the conditions read on the pushes that matter, and the links that would be traps."""
    out = {}
    for name, w in (("chime", chime_world()), ("source", source_world()), ("paths", paths_world()),
                    ("redundant", redundant_world()), ("reversal", reversal_world()), ("enabler", enabler_world())):
        a = run(w, ticks)
        rows = readout(a, w, PROBES[name])[0]
        conds_ = {f"{i[0]} {i[1]}": v for i, v in conds(a).items() if i[1] != "flag"}
        out[name] = dict(right_all=round(right_all(rows), 2), conditions=conds_)
        if name == "source":
            e = a.mind.understanding.edges()
            out[name]["stone_links"] = sorted(x for x in e if "stone_a" in x[1] and "stone_b" in x[2]
                                              or "stone_b" in x[1] and "stone_a" in x[2])
    w = sequence_world()
    a = run(w, ticks)
    e = a.mind.understanding.edges()
    out["sequence"] = dict(tick_to_door=sorted(x for x in e if x[0] == "causes" and x[1].startswith("tick")
                                               and x[2].startswith("door")),
                           door_with_tick_unseated=sum("door_filling" in arr for fs, arr in a.history
                                                       if "tick_plug_parting" in fs),
                           refuted=sorted((x, y) for x, r, y in a.mind.understanding.refuted
                                          if r == "causes" and x.startswith("tick") and y.startswith("door")))
    return out


def library():
    """The worlds built so far that have probes, for the curriculum's selection."""
    return {"block": block_world(), "marble": marble_world(), "button": button_world(),
            "calculator": calculator_world(), "spring": spring_world(), "catch": catch_world(),
            "and": and_world(), "chime": chime_world(), "paths": paths_world(),
            "redundant": redundant_world(), "reversal": reversal_world(), "enabler": enabler_world()}


def interest(agent):
    """The agent's own reading of how much a world still has to teach it: the mean gap over the
    pushes it invites now (how much of what they do is not understood), never the answer key. An
    unseen world is fully open. (First: the largest pull, estimated work x gap; a visited world's
    estimates of work dwarfed an unseen world's prior, and the agent kept to four worlds of twelve.)"""
    invs = agent.world.invitations()
    return sum(agent.gap(i) for i in invs) / len(invs) if invs else 0.0


def milestone_e(rounds=24, ticks=10, rotation=0):
    """Milestone E: the agent's understanding chooses the next world against a fixed order (round
    robin). The choice: learning progress, how much its own gap (interest()) fell over its last
    visit there, unseen worlds first (first: the world most open now; a world whose pushes the agent
    never tries stays open forever, and it spent ten of 24 visits in one); the same budget (rounds x ticks), one
    mind across the worlds, an agent per world keeping its tries. Scored by the mean exact share of
    every world's probes at the end. rotation: where round robin starts (a different order)."""
    out = {}
    for arm in ("adaptive", "round robin"):
        lib = library()
        names = list(lib)
        names = names[rotation:] + names[:rotation]
        mind = Mind(Params())
        agents = {n: make(lib[n], mind) for n in names}
        visits, progress = [], {n: float("inf") for n in names}   # unseen: first
        for r in range(rounds):
            if arm == "adaptive":
                pick = max(names, key=lambda n: (progress[n], -names.index(n)))
            else:
                pick = names[r % len(names)]
            visits.append(pick)
            before = interest(agents[pick])
            for _ in range(ticks):
                agents[pick].tick()
            while agents[pick].watching:   # a watch is not left half done
                agents[pick].tick()
            # (tried 2026-10-23: the summed gap, then the summed gap at the starting scene; neither
            # helped, see milestone_ceiling.py: here even the best allocation gains 0.019)
            progress[pick] = before - interest(agents[pick])
        scores = {n: right_all(readout(agents[n], lib[n], PROBES[n])[0]) for n in names}
        out[arm] = dict(mean=round(sum(scores.values()) / len(scores), 3),
                        scores={n: round(v, 2) for n, v in scores.items()},
                        visits={n: visits.count(n) for n in names})
    return out


def stage4(ticks=150):
    """Stage 4, per world: the answer key's point (known answers from the simulator) and what the
    agent makes of it, by its own exploration (`ticks`, gusts on) or by scripted pushes where the
    point needs a particular sequence."""
    out = {}

    def script(w, pushes):
        w = copy.deepcopy(w)
        w.gusts = []
        a = make(w)
        for inv in pushes:
            a.tick(force=inv)
            while a.watching:
                a.tick()
        return a

    # S4-W01: the press needs plugs 1-3, not 4
    press = ("light", "button", "sealing")
    seq = [press]
    for i in (1, 2, 3, 4):
        seq += [("hard", f"plug_{i}", "connecting"), press, ("hard", f"plug_{i}", "parting")]
    a = script(parts_world(), seq)
    out["parts"] = dict(conditions=conds(a).get(press, []))

    # S4-W02: the drain lowers the level, the float reopens and refills it
    w = regulator_world()
    a = run(w, ticks)
    drain = ("hard", "drain_button", "sealing")
    steady = copy.deepcopy(w)
    steady.reset()
    steady.gusts = []
    while not (steady.states()["float"] == "shutting" and float(steady.states()["tank_level"]) >= 4):
        steady.act(None)   # the level at the top of its band, the float just closed
    p = a.predict(drain, a.facts_now(steady.tree), steady.tree)
    out["regulator"] = dict(steady=(steady.states()["tank_level"], steady.states()["float"]),
                            drain_predicts=sorted(p or []),
                            truth=sorted(set().union(*w.truth(steady.tree)[drain].values())))

    # S4-W03: a light press, and the tank bursts slices later
    w = runaway_world()
    a = run(w, ticks)
    p = a.predict(("light", "primer", "sealing"), a.facts_now(w.start), w.start)
    t = w.truth()[("light", "primer", "sealing")]
    out["runaway"] = dict(predicts_burst="tank_bursting" in (p or ()),
                          burst_at_slice=min((k for k, v in t.items() if "tank_bursting" in v), default=None))

    # S4-W04: four presses; only the fourth snaps the rope
    key = ("light", "key", "sealing")
    a = script(threshold_world(), [key] * 6)
    out["threshold"] = dict(snapped_on=[k + 1 for k, es in enumerate(outcomes_of(a, key)) if "rope_snapping" in es],
                            conditions=conds(a).get(key, []))

    # S4-W05: braced, a push moves nothing but presses the block; unbraced, it slides it
    w = opposing_world()
    a = run(w, ticks)
    hard = ("hard", "block", "resting")
    braced, unbraced = w.start, after(w, [("hard", 1)])
    out["opposing"] = dict(braced=sorted(a.predict(hard, a.facts_now(braced), braced) or []),
                           unbraced=sorted(a.predict(hard, a.facts_now(unbraced), unbraced) or []),
                           conditions=conds(a).get(hard, []))

    # S4-W06: the same level, 4, with the float open (rising) or closed (fallen from full)
    w = hysteresis_world()
    drain = ("hard", "drain_button", "sealing")
    rising, falling = copy.deepcopy(w), copy.deepcopy(w)
    rising.gusts = falling.gusts = []
    for _ in range(4):   # from empty up to 4, the float open
        rising.act(None)
    for _ in range(13):  # full (7, the float closed at 6), then drained by 3, down to 4
        falling.act(None)
    falling.act(drain)
    falling.act(None)
    st = lambda x: (x.states()["tank_level"], x.states()["float"])
    later = lambda x: [x.act(None) for _ in range(8)] and x.states()["tank_level"]
    out["hysteresis"] = dict(rising=st(rising), falling=st(falling),
                             eight_slices_later=(later(copy.deepcopy(rising)), later(copy.deepcopy(falling))))

    # S4-W07: unseat the gate; reseat it early or late
    w = cascade_world()
    gate_off, gate_on = ("hard", "gate", "connecting"), ("hard", "gate", "parting")
    res = {}
    for when in (3, 9):
        x = copy.deepcopy(w)
        x.gusts = []
        for t in range(14):
            x.act(gate_off if t == 0 else gate_on if t == when else None)
        res["early" if when == 3 else "late"] = x.states().get("shelf")
    a = run(w, ticks)
    p = a.predict(gate_off, a.facts_now(w.start), w.start)
    out["cascade"] = dict(shelf_after=res, agent_predicts_shelf_breaking="shelf_breaking" in (p or ()))
    return out


def report(ticks=150, held=60):
    """The slice: each world's discovery run and readout, its held-out world for a fresh agent and
    for one carrying the discovery mind, and the spring / raised-weight analogy (one mind through
    both). Prints as it goes."""
    out = {}
    for name, (w, h) in worlds().items():
        a = run(w, ticks)
        rows, tried, right = readout(a, w, PROBES[name])
        fresh = run(h, held)
        carried = run(h, held, a.mind)
        hr = [readout(x, h, PROBES[name]) for x in (fresh, carried)]
        out[name] = dict(tried=tried, right=right, overlap=overlap(rows),
                         conds=conds(a),
                         held=[(t, r, overlap(rs)) for rs, t, r in hr], rows=rows, agent=a)
        print(f"{name:10s} discovery {ticks}: tried {tried:.2f} right {right:.2f} overlap {overlap(rows):.2f}"
              f" | held-out {held}: fresh right {hr[0][2]:.2f}, carried right {hr[1][2]:.2f}", flush=True)
        for inv, cs in out[name]["conds"].items():
            print(f"{'':12s}conditions {inv}: {cs}")
        for p, inv, true, pred in rows:
            if pred != true:
                print(f"{'':12s}wrong {p} {inv}: predicted {sorted(pred) if pred else None}, true {sorted(true)}")
    sw = make(spring_world())
    for _ in range(ticks):
        sw.tick()
    ww = make(weight_world(), sw.mind)
    for _ in range(ticks):
        ww.tick()
    und = sw.mind.understanding
    out["analogy"] = [a for a in und.abstracts]
    print(f"analogy: {len(und.abstracts)} abstract(s)")
    for a in und.abstracts:
        print(f"  {a['id']} pattern {sorted(a['pattern'])}")
        for m in a["members"]:
            print(f"    member {dict(sorted(m.items()))}")
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    if "--key" in sys.argv:
        for name, (w, h) in worlds().items():
            for x in (w, h):
                print(f"== {x.name}: states {x.states()}")
                for inv, got in x.truth().items():
                    print(f"   {inv}: {got or 'no change'}")
    else:
        report()
