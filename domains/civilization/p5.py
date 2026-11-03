"""Rung P5 (PHYSICS.md, the rest of the physics): unmaking, fusing, and travel between two worlds, on the moon's own
field.

Ada is on the moon after P3's voyage, her skiff moored there, and wants to sail home. The moon's pool is nearly dry; an
old husk unmade gives it potential; the flask draws from it; the basin forms a lantern from it; the lantern fused onto
the skiff lights it; and only a lit skiff with a brimming flask beats the moon's binding. The world is
moon_world.MoonWorld. The mind is Gerundelle, unchanged, run two ways: fresh (a mind that has never been anywhere), and
carried (her mind from P3's steady run, which learned the hill's jar and its brim: does any of it transfer?).

Measures: the want reached (the skiff returning home); conservation at every slice, across the moon and home; which of
the new powers were used (unmade, formed, fused, launched; hops that fell back); the conditions learned; the story.

Run: python -X utf8 p5.py [--ticks 1200] [--tempers steady,...] [--no-story] [--beats]
Writes results/p5_<fresh|carried>_<temper>.json.
"""
import argparse
import dataclasses
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

from moon_world import MoonWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402
import p0  # noqa: E402

ACTOR, PRONOUN, WANT = "Ada", "she", "skiff_returning"
EXPLAINING = p0.LEXICON["conditions"][("skiff", "jar", "charged")][1]

LEXICON = {
    "frame": "The moon was silent and grey.",
    "nouns": {"pool": ("a shallow pool", "the pool"), "flask": ("a glass flask", "the flask"),
              "basin": ("a round basin", "the basin"), "husk": ("an old husk", "the husk"),
              "skiff": ("the skiff", "the skiff"), "lantern": ("a small lantern", "the lantern")},
    "states": {},
    "states_obj": {("pool", "dry"): "lay dry", ("pool", "glimmering"): "glimmered",
                   ("flask", "empty"): "stood empty beside it", ("basin", "shaping"): "lay open in the dust",
                   ("husk", "resting"): "lay in the dust", ("skiff", "moored"): "was moored at the edge of the pool"},
    "flips": {("resting", "unmaking"): "crumbled into light", ("dry", "glimmering"): "began to glimmer",
              ("glimmering", "dry"): "ran dry", ("empty", "charged"): "began to glow",
              ("charged", "brimming"): "brimmed with light", ("brimming", "charged"): "dimmed",
              ("charged", "empty"): "went dark", ("brimming", "empty"): "went dark",
              ("unformed", "resting"): "took shape in the basin", ("resting", "fusing"): "melted into the skiff",
              ("moored", "lit"): "began to shine", ("propelling", "hopping"): "hopped",
              ("hopping", "moored"): "fell back to its mooring", ("propelling", "escaping"): "climbed past the stars",
              ("escaping", "drifting"): "drifted through the dark",
              ("drifting", "returning"): "came down on the hillside at home"},
    "flips_obj": {("basin", "shaping", "forming"): "began to glow", ("basin", "cradling", "shaping"): "lay empty again"},
    "skip": {("unmaking", "gone"), ("forming", "cradling"), ("fusing", "gone"), ("moored", "propelling"),
             ("lit", "propelling"), ("returning", "beached")},
    "push": {"light": "touched {N}", "hard": "pushed {N} hard"},
    "push_obj": {("light", "flask"): "dipped {N} into the pool", ("hard", "flask"): "shook {N}"},
    "want": {WANT: "wanted to sail home"},
    "slots": {"causes": "what {N} did", "conditions": "what {N} needed", "role": "what {N} had to do with it",
              "co_occurs": "what came with {N}", "caused_by": "what moved {N}"},
    "conditions": {("skiff", "flask", "brimming"): ("{N} went home only when {C} was full", EXPLAINING),
                   ("flask", "pool", "glimmering"): ("{N} filled only when {C} glimmered", EXPLAINING),
                   ("pool", "husk", "gone"): ("{N} glimmered only when {C} was gone", EXPLAINING)},
    "waits": {},
}


def run(ticks, temper="steady", carried=False, settle=8):
    from temperament import PROFILES
    past = None
    if carried:   # her mind from P3: the hill, the jar, the brim, the voyage out
        import p3
        _, past = p3.run(800, "steady")
    world = MoonWorld()
    kw = PROFILES[temper].gerundelle()
    mind = GerundelleMind(ACTOR, world, want=WANT, mind=past.agent.mind if past else None, **kw)
    guard(mind.agent)
    if past:   # what she learned on the hill is her past, not news: not realized again on the moon
        mind.splits_seen |= set(past.agent.mind.meta.splits)
    mind.run(ticks, settle=settle)
    return world, mind


STAGES = ("pool_glimmering", "skiff_lit", WANT)


def guard(agent):
    """Gerundelle's planner crashes when a rollout reaches a state with no known action (molecules.mcts, pick:
    `best[1]` with best None, molecules.py:3716; met with a carried mind on the moon). Not patched in Gerundelle here
    (its own backup-and-suite discipline): a crash is read as no plan, as plan_step returns when no path reaches the
    want, and the mind explores. Counted in agent.plan_crashes."""
    plan = agent.plan_step
    agent.plan_crashes = 0

    def guarded(invs, **kw):
        try:
            return plan(invs, **kw)
        except TypeError:
            agent.plan_crashes += 1
            return None
    agent.plan_step = guarded
    return agent


def run_stages(ticks, temper="steady", carried=False, settle=8):
    """The curriculum (my choice, named: authored sub-wants, as a person sets herself steps): the same world and the
    same mind throughout, wanting in turn the pool glimmering, the skiff lit, and the skiff home. Each stage is a new
    GerundelleMind carrying the last one's Mind and beats (fiction's rung 6 way of carrying a mind between scenes).
    First the voyage home was one want, and no temperament, fresh or carried, put the seven steps together (finding 1).
    Returns (world, the last stage's mind, [(stage, reached, ticks it took)])."""
    from temperament import PROFILES
    past = None
    if carried:
        import p3
        _, past = p3.run(800, "steady")
    world = MoonWorld()
    kw = PROFILES[temper].gerundelle()
    mind, beats, log = past.agent.mind if past else None, [], []
    m = None
    for k, want in enumerate(STAGES):
        t0 = world.t
        m = GerundelleMind(ACTOR, world, want=want, mind=mind, beats=beats, see=(k == 0), **kw)
        guard(m.agent)
        if past:
            m.splits_seen |= set(past.agent.mind.meta.splits)
        if k:
            m.splits_seen |= set(mind.meta.splits)   # what the earlier stages taught is not news again
        # no settling between stages: the mind acts while a scene settles, and in the first curriculum it spent the
        # lit skiff in the 8 ticks after lighting it, so the last stage began unlit; the watch of the push that met
        # a stage's want has already seen its chain through
        m.run(ticks, settle=settle if k == len(STAGES) - 1 else 0)
        log.append((want, bool(m.agent.reached), world.t - t0, m.agent.plan_crashes))
        if not m.agent.reached:
            break
        mind = m.agent.mind
    return world, m, log


def used(world, mind):
    """Which powers the mind used, from its own tries (an outcome naming the change)."""
    seen = Counter()
    for _, (s, o, g), names in mind.agent.tried:
        for n in names:
            for key, effect in (("unmade", "husk_unmaking"), ("drew", "flask_charged"), ("brimmed", "flask_brimming"),
                                ("formed", "lantern_resting"), ("fused", "skiff_lit"), ("hopped", "skiff_hopping"),
                                ("went home", "skiff_returning")):
                if n == effect:
                    seen[key] += 1
    return dict(seen)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=1200)
    ap.add_argument("--tempers", default="steady")
    ap.add_argument("--beats", action="store_true")
    ap.add_argument("--no-story", action="store_true")
    args = ap.parse_args()
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    rows = []
    for carried in (False, True):
        for temper in args.tempers.split(","):
            label = f"{'carried' if carried else 'fresh'}_{temper}"
            world, mind = run(args.ticks, temper, carried)
            a = mind.agent
            totals = {round(r["total"], 9) for r in world.history}
            splits = {x: sp["tag"] for x, sp in a.mind.meta.splits.items() if x.split("_push:")[-1].split("_")[0] in world.objs}
            u = used(world, mind)
            print(f"[{label}] reached {bool(a.reached)}; gave up {bool(a.gave_up)}; ticks {world.t}; pushes {len(a.tried)}; "
                  f"conservation {'HOLDS' if len(totals) == 1 else 'BROKEN'}; home field {world.book.elsewhere['home']:g}")
            print(f"  powers used {u}")
            print(f"  conditions learned here {splits}")
            print("  pushes:", Counter(f"{s} {o}" for _, (s, o, _), _ in a.tried).most_common())
            for b in mind.beats:
                if args.beats or b.kind in ("learn", "surprise", "reach", "recall"):
                    print(f"    t{b.t:<4} {b.kind:8} {b.obj:8} {b.detail}")
            out = dict(label=label, reached=bool(a.reached), gave_up=bool(a.gave_up), ticks=world.t, pushes=len(a.tried),
                       conservation=len(totals) == 1, powers=u, splits=splits)
            if not args.no_story:
                scene, sentences, m = p0.story(world, mind, LEXICON)
                print()
                print(" ".join(t for _, t, _ in sentences))
                for r in m["rows"]:
                    if not r["ok"]:
                        print(f"  MISS {r['text']}\n        intended {r['shape']}\n        reading  {r['reading'] or r['why']}")
                print(f"  round-trip {m['round_trip']:.2f}; sentences {len(sentences)}")
                out.update(sentences=[t for _, t, _ in sentences], round_trip=m["round_trip"])
            out.update(ledger=world.history, beats=[dataclasses.asdict(b) for b in mind.beats])
            with open(os.path.join(HERE, "results", f"p5_{label}.json"), "w", encoding="utf-8") as f:
                json.dump(out, f, indent=1, default=str)
            rows.append(out)
            print()
    print(f"{'run':20} {'reached':>7} {'pushes':>6} {'ticks':>5}  powers")
    for r in rows:
        print(f"{r['label']:20} {'yes' if r['reached'] else 'no':>7} {r['pushes']:6d} {r['ticks']:5d}  {r['powers']}")


if __name__ == "__main__":
    main()
