"""Run a rung of the ladder on one or both arms, print the scene, and write it to the corpus.

Run: python run_ladder.py [--rung 0] [--arm lean|gerundelle|both] [--ticks 60]
Writes results/rung<k>_<arm>.json (beats, plans, sentences with their readings, measures).
"""
import argparse
import dataclasses
import json
import os
import sys

from measure import evaluate
from printer import Printer
from beats import effect_parts
from story import tell
import worlds

HERE = os.path.dirname(os.path.abspath(__file__))
RUNGS = {0: {"world": worlds.jack_in_the_box, "lexicon": "jack_in_the_box", "actor": "Mara", "pronoun": "she",
             "want": "lid_releasing"},
         1: {"world": worlds.crate_in_the_wind, "lexicon": "crate_in_the_wind", "actor": "Tom", "pronoun": "he",
             "want": "crate_sliding", "want_count": 3},
         2: {"world": worlds.jack_in_the_box, "lexicon": "jack_with_ben", "actor": "Mara", "pronoun": "she",
             "want": "lid_releasing", "company": ["Ben"]},
         3: {"world": worlds.jack_in_the_box, "lexicon": "jack_with_leo", "actor": "Mara", "pronoun": "she",
             "want": "lid_releasing", "company": ["Leo"], "rivals": ["Leo"]},
         4: {"world": worlds.jack_in_the_box, "lexicon": "jack_tug", "actor": "Mara", "pronoun": "she",
             "want": "lid_releasing", "company": ["Leo"], "rivals": ["Leo"],
             "acting": {"Leo": {"want": "latch_connecting", "resolve": 2.0, "past": worlds.jack_latch_undone}},
             "resolve": 2.0, "stubbornness": 2},
         5: {"world": worlds.toy_box, "lexicon": "toy_story", "actor": "Mara", "pronoun": "she",
             "want": "lid_releasing", "company": ["Leo"], "hold": 4, "gap": 10, "time": True},
         6: {"world": worlds.jack_in_the_box, "then": worlds.cupboard, "lexicon": "two_scenes", "actor": "Mara",
             "pronoun": "she", "want": "lid_releasing", "then_want": "door_releasing", "company": ["Ben"],
             "gap": 10, "scenes": True},
         # new worlds (Gerundelle's curriculum): a locked shed with a wrong key; a lamp with two plugs (an AND)
         8: {"world": worlds.lock_scene, "lexicon": "shed", "actor": "Mara", "pronoun": "she", "want": "door_releasing"},
         9: {"world": worlds.lamp_scene, "lexicon": "lamp", "actor": "Mara", "pronoun": "she", "want": "lamp_filling"},
         # corpus run 2: more of the curriculum, and dressings of the box's structure
         10: {"world": worlds.boulder_scene, "lexicon": "boulder", "actor": "Tom", "pronoun": "he", "want": "stone_flying"},
         11: {"world": worlds.cannon_scene, "lexicon": "cannon", "actor": "Mara", "pronoun": "she", "want": "ball_flying"},
         12: {"world": worlds.catapult_scene, "lexicon": "catapult", "actor": "Tom", "pronoun": "he", "want": "stone_flying"},
         13: {"world": worlds.doorbell_scene, "lexicon": "doorbell", "actor": "Mara", "pronoun": "she", "want": "lamp_filling"},
         14: {"world": worlds.chime_scene, "lexicon": "chime", "actor": "Mara", "pronoun": "she", "want": "chime_swinging"},
         15: {"world": worlds.domino_scene, "lexicon": "domino", "actor": "Mara", "pronoun": "she", "want": "bead_falling"},
         16: {"world": worlds.chest_scene, "lexicon": "chest", "actor": "Mara", "pronoun": "she", "want": "top_releasing"},
         17: {"world": worlds.tin_scene, "lexicon": "tin", "actor": "Tom", "pronoun": "he", "want": "cap_releasing"},
         # corpus run 3: dressings (the same physics, other objects and words)
         18: {"world": worlds.music_box_scene, "lexicon": "music_box", "actor": "Mara", "pronoun": "she", "want": "lid_releasing"},
         19: {"world": worlds.gate_scene, "lexicon": "gate", "actor": "Tom", "pronoun": "he", "want": "gate_releasing"},
         20: {"world": worlds.diary_scene, "lexicon": "diary", "actor": "Mara", "pronoun": "she", "want": "cover_releasing"},
         21: {"world": worlds.log_scene, "lexicon": "log", "actor": "Tom", "pronoun": "he", "want": "log_flying"},
         22: {"world": worlds.pinball_scene, "lexicon": "pinball", "actor": "Tom", "pronoun": "he", "want": "marble_flying"},
         23: {"world": worlds.radio_scene, "lexicon": "radio", "actor": "Mara", "pronoun": "she", "want": "radio_filling"},
         24: {"world": worlds.bike_bell_scene, "lexicon": "bike_bell", "actor": "Tom", "pronoun": "he", "want": "bell_swinging"},
         # rung 6 with the bolt's id sorting last: the fair test of transfer (no alphabetical luck)
         61: {"world": worlds.jack_in_the_box, "then": worlds.cupboard_rod, "lexicon": "two_scenes", "actor": "Mara",
              "pronoun": "she", "want": "lid_releasing", "then_want": "door_releasing", "company": ["Ben"],
              "gap": 10, "scenes": True}}


import social  # noqa: E402  (people, lies and loss in the new worlds)
SOCIAL = social.specs()


class Helper:
    """A person whose pushes here are authored (Ben opening the box for her), made in the world and watched:
    their effects are real, and the watcher learns from them as from its own."""
    helps = True

    def __init__(self, name):
        self.name, self.tries = name, []

    def push(self, world, inv, beats, watch=6):
        from beats import Beat
        from lean import Try
        facts = frozenset(f"{d}_{g}" for d, g in world.states().items())
        tb = len(beats)
        beats.append(Beat(world.t, "try", self.name, obj=inv[1], detail={"strength": inv[0], "gerund": inv[2]}))
        names, diffs, k = [], world.act(inv), 0
        while k < watch:
            for e in diffs:
                obj, rest = e.split(": ", 1)
                if " -> " in rest:
                    frm, to = rest.split(" (")[0].split(" -> ")
                    names.append(f"{obj}_{to}")
                    beats.append(Beat(world.t, "change", self.name, obj=obj, detail={"from": frm, "to": to, "slice": k},
                                      refs=(tb,)))
            k += 1
            if not diffs and k >= world.horizon:
                break
            diffs = world.act(None)
        self.tries.append(Try(world.t, inv, facts, tuple(names), frozenset(f"{d}_{g}" for d, g in world.states().items())))


def run_scenes(spec, kw, ticks):
    """Rung 6: scene A (Mara cannot open the box; Ben opens it, watched), time passing, scene B (a cupboard of
    the same shape, alone)."""
    from lean import LeanMind
    gap = kw.pop("_gap", spec["gap"])
    for k in ("_plant", "_company", "_withhold", "_rival_resolve"):
        kw.pop(k, None)
    wa = spec["world"]()
    ben = Helper("Ben")
    mara = LeanMind(spec["actor"], wa, want=spec["want"], others=[ben], carry_on=True, **kw)
    mara.tick()                                    # she tries, and fails
    for inv in spec.get("help", (("hard", "latch", "connecting"), ("hard", "lid", "locking"))):
        if wa.states().get(inv[1]) != inv[2]:      # he reads the box as it is (a fastening already undone is
            continue                               # left alone)
        ben.push(wa, inv, mara.beats)              # he opens it; she watches
    mara.perceive()                                # what she saw, and the want met by his help
    mara.end_scene()
    mara.pass_time(gap)
    wb = spec["then"]()
    wb.t = wa.t
    mara.others = []
    mara.enter(wb)
    mara.open_want(spec["then_want"])
    mara.done = False
    for _ in range(ticks):
        mara.tick()
        if mara.want.closed is not None:
            break
    return mara.beats, wb


class Taker:
    """A person whose acts here are authored events (taking the toy away, bringing it back): possession is not
    a force yet. Visible to the mind as a mover; not a mind, so not asked anything."""

    def __init__(self, name):
        self.name, self.tries = name, []


def run_time(spec, kw, ticks):
    """Rung 5's scene, in four movements: the want and then holding the toy (hold plays); the toy taken; time
    passing (gap ticks); the toy brought back, and held again."""
    from lean import LeanMind, Try
    from beats import Beat
    world = spec["world"]()
    hold, gap = kw.pop("_hold", spec["hold"]), kw.pop("_gap", spec["gap"])
    storage = not kw.pop("_nostore", False)
    leo = Taker("Leo")
    prize = spec.get("prize", "toy")   # what is held, taken and brought back
    mara = LeanMind(spec["actor"], world, want=spec["want"], others=[leo], storage=storage, carry_on=True, **kw)

    def plays():
        return sum(1 for x in mara.tries if x.inv[1] == prize and x.effects)

    def event(kind, obj):
        f = mara.facts()
        world.take(obj) if kind == "take" else world.give(obj)
        leo.tries.append(Try(world.t, (kind, obj, ""), f, (f"{obj}_{'gone' if kind == 'take' else 'back'}",), mara.facts()))
        mara.beats.append(Beat(world.t, "try", leo.name, obj=obj, detail={"strength": kind, "gerund": ""}))
        world.t += 1
    for _ in range(ticks):
        mara.tick()
        if mara.want.closed is not None and plays() >= hold:
            break
    event("take", prize)
    mara.tick()          # the loss, seen
    mara.pass_time(gap)
    event("give", prize)
    start = plays()
    for _ in range(ticks):
        mara.tick()
        if plays() > start:
            break
    return mara.beats, world


def run_scenes_gerundelle(spec, kw, ticks, settle=8):
    """Rung 6 on the Gerundelle arm: scene A (Mara fails at the box; Ben opens it, his pushes watched whole and
    set against her own tries); time passing; scene B (the cupboard), her Mind carried in."""
    from gerundelle_arm import GerundelleMind
    from beats import Beat
    from force_world import effect_id
    gap = kw.pop("_gap", spec["gap"])
    kw = {k: v for k, v in kw.items() if not k.startswith("_")}
    wa = spec["world"]()
    mara = GerundelleMind(spec["actor"], wa, want=spec["want"], **kw)
    obj = spec["want"].rsplit("_", 1)[0]
    seen = 0
    alone = False
    for _ in range(ticks):   # she tries, until a push on the wanted object has failed (or she opens it herself)
        seen = mara.step(seen)
        if mara.pending:   # she met the want on her own: told, and nothing for Ben to do
            for _ in range(8):
                seen = mara.step(seen)
            mara.write_try(*mara.pending, reach=True)
            mara.pending, alone = None, True
            break
        if any(inv[1] == obj and not any(n.startswith(obj + "_") for n in names) for _, inv, names in mara.agent.tried):
            break
    while (mara.agent.watching or mara.agent.queue) and not mara.done:   # (a mind done takes no more turns:
        mara.agent.queue = []                                            # first this waited on it forever)
        seen = mara.step(seen)
    mara.done = False   # the scene goes on for her (Ben, time, the next scene)
    ben = Helper("Ben")
    for inv in spec.get("help", (("hard", "latch", "connecting"), ("hard", "lid", "locking"))):   # he opens it
        if alone or wa.states().get(inv[1]) != inv[2]:   # read as it is: a fastening already undone is left alone
            continue
        facts, n0 = mara.agent.facts_now(), len(mara.seen)
        wa.actor = "Ben"
        ben.push(wa, inv, mara.beats)
        effects = {}
        for k, (_, _, _, ev, _) in enumerate(mara.seen[n0:]):
            for e in ev:
                effects.setdefault(effect_id(e), k)
        mara.agent.observe_other(inv, facts, effects, by="Ben")
    wa.actor = mara.name
    for _ in range(2):   # what she saw, and her want met by his help
        mara.agent.queue = ["wait"]
        seen = mara.step(seen)
    mara.beat("time", detail={"ticks": gap})
    for _ in range(gap):
        mara.agent.queue = ["wait"]
        seen = mara.step(seen)
    wb = spec["then"]()
    wb.t = wa.t
    mara.beats.append(Beat(wb.t, "scene", mara.name, detail={"world": wb.name}))
    m2 = GerundelleMind(spec["actor"], wb, want=spec["then_want"], mind=mara.agent.mind, beats=mara.beats, **kw)
    m2.splits_seen = set(mara.splits_seen)   # what she already realized is not realized again
    m2.agent.pushed, m2.agent.recalled = list(mara.agent.pushed), []   # her history of pushes, carried
    m2.phases_seen, m2.log_upto = set(mara.phases_seen), mara.log_upto
    seen = 0
    for _ in range(ticks):
        seen = m2.step(seen)
        if m2.pending:
            for _ in range(settle):
                seen = m2.step(seen)
            m2.write_try(*m2.pending, reach=True)
            break
        if m2.done:
            break
    return mara.beats, wb


def run_time_gerundelle(spec, kw, ticks, settle=8):
    """Rung 5 on the Gerundelle arm: the want, then playing (the mind goes on after its want is met); the toy
    taken (an authored event, the taker seen); time passing (idle ticks: Gerundelle's own half-lives decide what
    fades and what is stored open); the toy brought back, and played with again."""
    from gerundelle_arm import GerundelleMind
    from beats import Beat
    world = spec["world"]()
    hold, gap = kw.pop("_hold", spec["hold"]), kw.pop("_gap", spec["gap"])
    kw = {k: v for k, v in kw.items() if not k.startswith("_")}
    mara = GerundelleMind(spec["actor"], world, want=spec["want"], **kw)
    prize = spec.get("prize", "toy")
    seen = 0

    def plays():
        return sum(1 for _, inv, names in mara.agent.tried if inv[1] == prize and any(n.startswith(prize + "_") for n in names))

    def turn():
        nonlocal seen
        seen = mara.step(seen)
        if mara.pending:   # the want met: the scene settles, the reach is told, and she goes on
            for _ in range(settle):
                seen = mara.step(seen)
            mara.write_try(*mara.pending, reach=True)
            mara.pending, mara.done = None, False

    def idle(n):
        nonlocal seen
        for _ in range(n):
            mara.agent.queue = ["wait"]
            seen = mara.step(seen)

    def event(kind):
        terr = mara.agent.mind.territory
        mara.beats.append(Beat(world.t, "try", "Leo", obj=prize, detail={"strength": kind, "gerund": ""}))
        if kind == "take":
            world.take(prize)
            terr.row(prize)["taken_by"] = "Leo"   # seen taken: the mover is visible
        else:
            world.give(prize)
    for _ in range(ticks):
        turn()
        if mara.agent.reached and plays() >= hold:
            break
    event("take")
    idle(2)            # the loss, seen
    mara.beat("time", detail={"ticks": gap})
    idle(gap)          # time passing
    event("give")
    start = plays()
    for _ in range(ticks):
        turn()
        if plays() > start:
            break
    idle(2)
    return mara.beats, world


def prologue(name, spec, ticks):
    """A companion's past: the same scene lived through once, on its own copy of the world, before the
    story begins. Its ledger (holes, receipts, tries) is kept as history; its beats are not told."""
    from lean import LeanMind
    mind = LeanMind(name, spec["world"](), want=spec["want"], want_count=spec.get("want_count", 1))
    for _ in range(ticks):
        mind.tick()
        if mind.done:
            break
    return mind


# the configurations compared: an arm and its settings (the ablations of the inventory)
CONFIGS = {
    "lean": ("lean", {}),                                      # effect holes, want, ownership slots, phases
    "lean-nophase": ("lean", {"phases": False}),               # ownership stakes, no feelings
    "lean-rules": ("lean", {"ownership": False}),              # the first cut: the want alone pays, feelings by rule
    "lean-noretract": ("lean", {"retract_phase": False}),      # no phase when a belief is contradicted
    "lean-alone": ("lean", {"_company": "none"}),              # rung 2 without the companion
    "lean-ignorant": ("lean", {"_company": "ignorant"}),       # the companion present, with no past
    "lean-withhold": ("lean", {"_withhold": True}),            # the narrator does not reveal the liar's truth
    "lean-stubborn": ("lean", {"_rival_resolve": 4.0}),        # the rival's reserve doubled
    "lean-briefly": ("lean", {"_hold": 1}),                    # rung 5: the toy held once before it is taken
    "lean-years": ("lean", {"_gap": 120}),                     # rung 5: a long time before it comes back
    "lean-nostore": ("lean", {"_nostore": True}),              # rung 5: phases neither fade nor are stored
    "plant-none": ("lean", {"_plant": "none"}),                # rung 6: Ben's way with the latch not told
    "plant-emphasized": ("lean", {"_plant": "emphasized"}),    # rung 6: and her lesson from it told outright
    "plant-years": ("lean", {"_gap": 120}),                    # rung 6: the cupboard found long after
    # temperaments (temperament.py PROFILES): the same mind, a different character
    "lean-impatient": ("lean", {"_temper": "impatient"}),
    "lean-patient": ("lean", {"_temper": "patient"}),
    "gerundelle-impatient": ("gerundelle", {"_temper": "impatient"}),
    "gerundelle-patient": ("gerundelle", {"_temper": "patient"}),
    "lean-restless": ("lean", {"_temper": "restless"}),
    "lean-dogged": ("lean", {"_temper": "dogged"}),
    "gerundelle-restless": ("gerundelle", {"_temper": "restless"}),
    "gerundelle-dogged": ("gerundelle", {"_temper": "dogged"}),
    "lean-trusting": ("lean", {"_temper": "trusting"}),
    "lean-skeptical": ("lean", {"_temper": "skeptical"}),
    "gerundelle-trusting": ("gerundelle", {"_temper": "trusting"}),
    "gerundelle-skeptical": ("gerundelle", {"_temper": "skeptical"}),
    "gerundelle-stubborn": ("gerundelle", {"_rival_stub": 4}),
    "lean-yielding": ("lean", {"_temper": "yielding"}),
    "lean-obstinate": ("lean", {"_temper": "obstinate"}),
    "gerundelle-yielding": ("gerundelle", {"_temper": "yielding"}),
    "gerundelle-obstinate": ("gerundelle", {"_temper": "obstinate"}),   # rung 4: the rival's stubbornness doubled
    "gerundelle-briefly": ("gerundelle", {"_hold": 1}),        # rung 5: the toy held once before it is taken
    "gerundelle-years": ("gerundelle", {"_gap": 120}),         # rung 5: a long time before it comes back
    "gerundelle-weeks": ("gerundelle", {"_gap": 40}),
    "gerundelle": ("gerundelle", {}),
    "gerundelle-nophase": ("gerundelle", {"phases": False}),
    "gerundelle-alone": ("gerundelle", {"_company": "none"}),
}


def run_acting_gerundelle(spec, kw, ticks, settle=8):
    """Rung 4 on the Gerundelle arm: several Gerundelle minds in one world, in turns, on one beat list. A keeper's
    past is its Mind, carried in (the curriculum's way: a mind lived through the scene on another copy). Each
    mind sees what the others' slices changed (moved by something else); a mind's stubbornness is how often
    another may undo what it holds before it gives the want up."""
    from gerundelle_arm import GerundelleMind
    world = spec["world"]()
    shared = []
    actors = []
    for n, a in spec["acting"].items():
        past = GerundelleMind(n, a["past"](), want=a["want"])
        past.run(ticks)
        stub = kw.get("stubbornness") if kw.get("_rival_stub") is None else kw["_rival_stub"]
        actors.append(GerundelleMind(n, world, want=a["want"], mind=past.agent.mind, beats=shared, keep=True,
                                     see=False, stubbornness=a.get("stubbornness", 2) if stub is None else stub))
    kw = {k: v for k, v in kw.items() if not k.startswith("_")}
    kw.setdefault("stubbornness", spec.get("stubbornness"))
    mara = GerundelleMind(spec["actor"], world, want=spec["want"], beats=shared, others=actors, **kw)
    for a in actors:
        a.others = [mara]
        a.contesting.add(spec["want"])   # it opposes the want
    seen = {m.name: 0 for m in [mara] + actors}
    for _ in range(ticks):
        world.actor = mara.name
        seen[mara.name] = mara.step(seen[mara.name])
        if mara.pending:
            for _ in range(settle):
                seen[mara.name] = mara.step(seen[mara.name])
            mara.write_try(*mara.pending, reach=True)
            break
        if mara.done:
            break
        for a in actors:
            if not a.done:
                world.actor = a.name
                seen[a.name] = a.step(seen[a.name])
    for a in actors:   # what the others saw of the end
        world.actor = a.name
        a.look()
    return shared, world


def run_arm(config, spec, ticks):
    from lean import LeanMind
    from temperament import PROFILES
    arm, kw = CONFIGS[config]
    kw = dict(kw)
    temper = kw.pop("_temper", None)
    if temper:   # a character's temperament, mapped onto the arm's own parameters
        kw.update(PROFILES[temper].lean() if arm == "lean" else PROFILES[temper].gerundelle())
    if arm == "lean" and spec.get("scenes"):   # rung 6: two scenes, the mind's history carried between them
        return run_scenes(spec, dict(kw), ticks)
    if arm == "lean" and spec.get("time"):   # rung 5: one mind, and authored events in time
        return run_time(spec, {k: v for k, v in kw.items() if k not in ("_rival_resolve", "_company", "_withhold")}, ticks)
    world = spec["world"]()
    company = kw.pop("_company", "known")
    kw.pop("_withhold", None)
    rival_resolve = kw.pop("_rival_resolve", None)
    names = () if company == "none" else spec.get("company", ())
    # a companion is a lean mind with a past (or none): the Gerundelle arm's character asks the same Ben
    others = [prologue(n, spec, ticks) if company == "known" else LeanMind(n, spec["world"]()) for n in names]
    for o in others:   # a rival wants, now, what the character wants: a contested want
        if o.name in spec.get("rivals", ()):
            o.contesting.add(spec["want"])
    if arm == "lean" and spec.get("acting"):   # several minds act in one world, in turns, on one beat list
        shared = []
        actors = []
        for n, a in spec["acting"].items():
            # its past: the want lived through once on its own copy of the scene (a keeper: the time it put
            # the state back); the ledger is kept, then the mind is set in the scene to keep that state
            past = LeanMind(n, a["past"](), want=a["want"], **{k: v for k, v in kw.items() if k in ("ownership", "phases")})
            for _ in range(ticks):
                past.tick()
                if past.done:
                    break
            past.world, past.beats, past.keep = world, shared, True
            past.resolve = rival_resolve if rival_resolve is not None else a.get("resolve")
            past.want.closed, past.done, past.last_facts, past.recent = None, False, None, set()
            past.terr.wants[effect_parts(a["want"], world.objs)[0]] = a["want"]
            actors.append(past)
        resolve = kw.pop("resolve", spec.get("resolve"))   # a temperament's stubbornness, else the scene's
        mind = LeanMind(spec["actor"], world, want=spec["want"], beats=shared, resolve=resolve,
                        others=actors, **kw)
        for a in actors:
            a.others = [mind]
            a.contesting.add(spec["want"])   # it opposes the want: a true answer would hand the region over
        for _ in range(ticks):
            mind.tick()
            if mind.done:
                break
            for a in actors:
                a.tick()
        return shared, world
    if arm == "lean":
        mind = LeanMind(spec["actor"], world, want=spec["want"], want_count=spec.get("want_count", 1),
                        others=others, **kw)
        for _ in range(ticks):
            mind.tick()
            if mind.done:
                break
        return mind.beats, world
    from gerundelle_arm import GerundelleMind
    if spec.get("scenes"):   # rung 6: two scenes, the mind carried between them
        return run_scenes_gerundelle(spec, {k: v for k, v in kw.items() if k not in ("_rival_stub",)}, ticks)
    if spec.get("time"):   # rung 5: one mind, and authored events in time
        return run_time_gerundelle(spec, {k: v for k, v in kw.items() if k not in ("_rival_stub",)}, ticks)
    if spec.get("acting"):   # several Gerundelle minds act in one world
        return run_acting_gerundelle(spec, kw, ticks)
    mind = GerundelleMind(spec["actor"], world, want=spec["want"], want_count=spec.get("want_count", 1),
                          others=others, **kw)
    mind.run(ticks)
    return mind.beats, world


def compose(arm, spec, ticks):
    """One configuration of a rung, end to end: the minds act, the scene is told and printed, and measured.
    Returns (beats, scene, sentences, measures)."""
    beats, world = run_arm(arm, spec, ticks)
    company = CONFIGS[arm][1].get("_company", "known")
    objs = set(world.objs) | (set(spec["world"]().objs) if spec.get("scenes") else set())
    scene = tell(beats, objs, spec["actor"], people=() if company == "none" else spec.get("company", ()),
                 plant=CONFIGS[arm][1].get("_plant", "passing"),
                 reveal=not CONFIGS[arm][1].get("_withhold"), rivals=() if company == "none" else spec.get("rivals", ()))
    import zlib   # each story its own place in the phrasings' rotations (deterministic: the scene and the config)
    seed = zlib.crc32(f"{spec['lexicon']}:{arm}".encode()) % 997 if spec.get("vary", True) else 0
    printer = Printer(worlds.LEXICON[spec["lexicon"]], spec["actor"], spec["pronoun"], seed=seed)
    sentences = printer.print_scene(scene)
    m = evaluate(scene, sentences)
    if m["round_trip"] < 1.0:   # generate and test: a sentence the reader cannot read as intended is said again
        sentences = retell(sentences, m["rows"], spec)   # another way (the pronoun as subject), and the reading
        m = evaluate(scene, sentences)                   # taken again: what is kept is what the reader recovers
    return beats, scene, sentences, m


def retell(sentences, rows, spec):
    """Each sentence whose reading missed its shape, said with the pronoun for the character's name at its
    head ("Tom was delighted with the clasp." misparses where "He was delighted with the clasp." does not), kept
    if that version reads as intended (the parser's quirks are met by trying another wording, not by a table)."""
    from measure import round_trip
    actor, pron = spec["actor"], spec["pronoun"]
    out = list(sentences)
    for k, r in enumerate(rows):
        i, text, shape = out[k]
        if r["ok"] or not text.startswith(actor + " "):
            continue
        alt = pron[0].upper() + pron[1:] + text[len(actor):]
        if round_trip([(i, alt, shape)])[0]["ok"]:
            out[k] = (i, alt, shape)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--rung", default="0", help="a rung number, or a social scene's name (social.py: 'shed:lie')")
    ap.add_argument("--configs", default="lean,gerundelle", help=f"comma-separated, of {list(CONFIGS)}")
    ap.add_argument("--quiet", action="store_true", help="the summary table only")
    ap.add_argument("--ticks", type=int, default=60)
    args = ap.parse_args()
    if args.rung in SOCIAL:   # a generated social scene (social.py), by name
        spec = SOCIAL[args.rung]
    else:
        spec = RUNGS[int(args.rung)]
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    summary = []
    for arm in args.configs.split(","):
        beats, scene, sentences, m = compose(arm, spec, args.ticks)
        roots = {r["reading"].split("(")[0] for r in m["rows"] if r["reading"]}
        summary.append((arm, len(beats), len(sentences), m["round_trip"], m["matched_share"], m["variety"],
                        m["exact_theory"], m["exact_coverage"], m["exact_theories"].get("narrative-arc", 0.0),
                        m["irony"], m["history"]["reach"],
                        len(roots), m["history"]["dependent"], m["history"]["chain"]))
        print(f"== rung {args.rung}, {arm}: {len(beats)} beats, {len(scene.plans)} plans, {len(sentences)} sentences")
        print(" ".join(t for _, t, _ in sentences))
        print()
        for r in ([] if args.quiet else m["rows"]):
            mark = "ok " if r["ok"] else "MISS"
            print(f"  {mark} [{scene.plans[r['plan']].stage:10}] {r['text']}")
            print(f"        intended {r['shape']}")
            print(f"        reading  {r['reading'] or r['readings'] or r['why']}")
        print(f"round-trip {m['round_trip']:.2f}; judge matched share {m['matched_share']:.2f}, variety {m['variety']:.2f}; "
              f"exact theories {m['exact_theories']}; judge-unmatched {m['unmatched']}; history {m['history']}")
        if spec.get("scenes"):
            print(f"reader: {m['reader']}")
        out = {"rung": args.rung, "arm": arm, "beats": [dataclasses.asdict(b) for b in beats],
               "plans": [dataclasses.asdict(p) for p in scene.plans],
               "measures": {k: v for k, v in m.items()}}
        with open(os.path.join(HERE, "results", f"rung{args.rung}_{arm}.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=str)
    print()
    print(f"{'config':20} {'beats':>5} {'sents':>5} {'trip':>5} {'judge':>5} {'var':>5} {'arc':>5} {'irony':>5} "
          f"{'reach':>5} {'roots':>5} {'dep':>5} {'chain':>5}  best exact theory")
    for (arm, nb, ns, trip, judged, var, th, cov, arc, irony, reach, roots, dep, chain) in summary:
        print(f"{arm:20} {nb:5d} {ns:5d} {trip:5.2f} {judged:5.2f} {var:5.2f} {arc:5.2f} {irony:5d} {reach:5d} {roots:5d} "
              f"{dep:5.2f} {chain:5d}  {th} {cov:.2f}")


if __name__ == "__main__":
    main()
