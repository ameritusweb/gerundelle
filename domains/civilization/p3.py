"""Rung P3 (PHYSICS.md): does a mind reach space?

The world is VoyageWorld: the hollow holds the boat's pattern (as in P0), a pale moon hangs in the sky, and the world
has a binding. Launching releases all the jar holds as one push; only a brimming jar (dipped twice) beats the binding,
and the skiff then climbs out, drifts, and lands on the moon. A charged jar's push flies and comes down on the far hill.
One want, beyond the binding: the skiff arriving. The mind is Gerundelle, unchanged; the story is fiction's pipeline.

Measures: the want reached; conservation at every slice (now across two places: the moon's field takes the voyage's
motion); the condition learned on launching (a split on the skiff's push), and whether it is the brim; how many launches
came back down first; the story's round-trip.

Run: python -X utf8 p3.py [--ticks 800] [--tempers steady,restless,...] [--beats] [--no-story]
Writes results/p3_<temper>.json.
"""
import argparse
import dataclasses
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

from potential_world import VoyageWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402
import p0  # noqa: E402

ACTOR, PRONOUN, WANT = "Ada", "she", "skiff_arriving"
EXPLAINING = p0.LEXICON["conditions"][("skiff", "jar", "charged")][1]

LEXICON = dict(p0.LEXICON, **{
    "frame": "There was a spring of light at the foot of a hill.",
    "nouns": dict(p0.LEXICON["nouns"], moon=("a pale moon", "the moon")),
    "states_obj": {("spring", "welling"): "glowed softly", ("jar", "empty"): "stood empty beside it",
                   ("hollow", "shaping"): "lay open in the rock", ("moon", "shining"): "hung in the sky"},
    "flips": {**p0.LEXICON["flips"], **{
        ("charged", "brimming"): "brimmed with light", ("brimming", "empty"): "went dark",
        ("propelling", "escaping"): "climbed past the clouds", ("escaping", "drifting"): "drifted among the stars",
        ("drifting", "arriving"): "landed on the moon"}},
    "flips_obj": {("hollow", "shaping", "forming"): "began to glow", ("hollow", "cradling", "shaping"): "lay empty again"},
    "skip": {("resting", "propelling"), ("arriving", "moored"), ("forming", "cradling")},
    "want": {WANT: "wanted to send a boat to the moon"},
    "conditions": {("skiff", "jar", "brimming"): ("{N} reached the moon only when {C} was full", EXPLAINING),
                   ("skiff", "jar", "charged"): ("{N} flew only when {C} glowed", EXPLAINING)},
})


def run(ticks, temper="steady", settle=8):
    from temperament import PROFILES
    world = VoyageWorld()
    mind = GerundelleMind(ACTOR, world, want=WANT, **PROFILES[temper].gerundelle())
    mind.run(ticks, settle=settle)
    return world, mind


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=800)
    ap.add_argument("--tempers", default="steady")
    ap.add_argument("--beats", action="store_true")
    ap.add_argument("--no-story", action="store_true")
    args = ap.parse_args()
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    rows = []
    for temper in args.tempers.split(","):
        world, mind = run(args.ticks, temper)
        agent = mind.agent
        totals = {round(r["total"], 9) for r in world.history}
        launched = [n for _, (s, o, _), n in agent.tried if o == "skiff" and s == "hard"]
        fell = sum(1 for n in launched if "skiff_flying" in n)
        arrived = sum(1 for n in launched if "skiff_arriving" in n)
        splits = {x: sp["tag"] for x, sp in agent.mind.meta.splits.items()}
        brim = any(t == "jar_brimming" for x, t in splits.items() if "_push:skiff" in x)
        print(f"[{temper}] reached {bool(agent.reached)}; ticks {world.t}; pushes {len(agent.tried)}; launches "
              f"{len(launched)} (came back down {fell}, reached the moon {arrived}); conservation "
              f"{'HOLDS' if len(totals) == 1 else 'BROKEN'}; moon's field {world.book.elsewhere['moon']:g}")
        print(f"  splits {splits}  (the brim learned: {'yes' if brim else 'no'})")
        print("  pushes:", Counter(f"{s} {o}" for _, (s, o, _), _ in agent.tried).most_common())
        for b in mind.beats:
            if args.beats or b.kind in ("learn", "surprise", "reach"):
                print(f"    t{b.t:<4} {b.kind:8} {b.obj:8} {b.detail}")
        out = dict(temper=temper, reached=bool(agent.reached), ticks=world.t, pushes=len(agent.tried),
                   launches=len(launched), fell=fell, arrived=arrived, conservation=len(totals) == 1,
                   splits=splits, brim_learned=brim)
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
        with open(os.path.join(HERE, "results", f"p3_{temper}.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=str)
        rows.append(out)
        print()
    print(f"{'temper':10} {'reached':>7} {'pushes':>6} {'ticks':>5} {'launches':>8} {'fell':>4}  brim learned")
    for r in rows:
        print(f"{r['temper']:10} {'yes' if r['reached'] else 'no':>7} {r['pushes']:6d} {r['ticks']:5d} {r['launches']:8d} "
              f"{r['fell']:4d}  {'yes' if r['brim_learned'] else 'no'}")


if __name__ == "__main__":
    main()
