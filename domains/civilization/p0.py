"""Rung P0 (PHYSICS.md): does one mind draw, form, break and launch, and does a story come out?

One place, a generous field, one pattern already seen (the hollow shaped like a boat), one want: the skiff flying. The
mind is Gerundelle (E:/vscode/analogy/molecules: SovAgent, read into beats by fiction's GerundelleMind), unchanged; the
story is fiction's pipeline (story.tell, Printer, measure.evaluate), unchanged. Only the world and its lexicon are new.

Measures: conservation holds at every slice (the world asserts it; the ledger is reported); the want is reached; the
story round-trips (each sentence read back as the shape it was written with).

Run: python -X utf8 p0.py [--ticks 400] [--beats] [--no-story]
Writes results/p0_gerundelle.json.
"""
import argparse
import dataclasses
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
FICTION = os.path.join(os.path.dirname(HERE), "fiction")
sys.path.insert(0, FICTION)

from potential_world import PotentialWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402  (fiction's; puts Gerundelle on the path)

ACTOR, PRONOUN, WANT = "Ada", "she", "skiff_flying"

# How the hillside is said (fiction's lexicon format: printer.Printer reads it).
LEXICON = {
    "frame": "There was a spring of light at the foot of a hill.",
    "nouns": {"spring": ("the spring", "the spring"), "jar": ("a clay jar", "the jar"),
              "hollow": ("a boat-shaped hollow", "the hollow"), "boulder": ("a boulder", "the boulder"),
              "skiff": ("a small skiff", "the skiff"), "pebbles": ("a heap of pebbles", "the pebbles")},
    "states": {},
    "states_obj": {("spring", "welling"): "glowed softly", ("jar", "empty"): "stood empty beside it",
                   ("hollow", "shaping"): "lay open in the rock", ("boulder", "resting"): "sat on the slope"},
    "flips": {("unformed", "resting"): "took shape in the hollow", ("resting", "propelling"): "surged forward",
              ("propelling", "flying"): "rose into the air", ("flying", "resting"): "came down on the far hill",
              ("resting", "cleaving"): "split apart", ("unformed", "piling"): "lay on the ground",
              ("empty", "charged"): "began to glow", ("charged", "empty"): "went dark",
              ("welling", "dry"): "ran dry", ("dry", "welling"): "glowed again"},
    "flips_obj": {("hollow", "shaping", "cradling"): "held a new shape", ("hollow", "cradling", "shaping"): "lay empty again"},
    "skip": {("cleaving", "gone"), ("resting", "propelling")},   # the flight is told by its rising
    "push": {"light": "touched {N}", "hard": "pushed {N} hard"},
    "push_obj": {("light", "jar"): "dipped {N} into the spring", ("hard", "jar"): "shook {N}"},
    "want": {WANT: "wanted to fly"},
    "slots": {"causes": "what {N} did", "conditions": "what {N} needed", "role": "what {N} had to do with it",
              "co_occurs": "what came with {N}", "caused_by": "what moved {N}"},
    "conditions": {("skiff", "jar", "charged"): ("{N} flew only when {C} glowed",
                                                "explaining(condition=narrating|describing, effect=narrating)")},
    "waits": {},
}


def run(ticks, settle=8):
    world = PotentialWorld()
    mind = GerundelleMind(ACTOR, world, want=WANT)
    mind.run(ticks, settle=settle)
    return world, mind


def story(world, mind, lexicon=None):
    from measure import evaluate
    from printer import Printer
    from story import tell
    scene = tell(mind.beats, set(world.objs), ACTOR)
    sentences = Printer(lexicon or LEXICON, ACTOR, PRONOUN).print_scene(scene)
    return scene, sentences, evaluate(scene, sentences)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--beats", action="store_true")
    ap.add_argument("--no-story", action="store_true")
    args = ap.parse_args()

    world, mind = run(args.ticks)
    agent = mind.agent
    totals = {round(r["total"], 9) for r in world.history}
    print(f"ticks {world.t}; pushes {len(agent.tried)}; reached {bool(agent.reached)}; gave up {bool(agent.gave_up)}")
    print(f"conservation: {len(world.history)} slices, totals seen {sorted(totals)}  "
          f"({'HOLDS' if len(totals) == 1 else 'BROKEN'})")
    print(f"ledger at the end: {world.history[-1]}")
    print("pushes:", Counter(f"{s} {o}" for _, (s, o, _), _ in agent.tried).most_common())
    print("splits (conditions learned):", {x: sp["tag"] for x, sp in agent.mind.meta.splits.items()})
    kinds = Counter(b.kind for b in mind.beats)
    print("beats:", dict(kinds))
    for b in mind.beats:
        if args.beats or b.kind in ("learn", "surprise", "reach", "feel", "wonder"):
            print(f"  t{b.t:<4} {b.kind:8} {b.obj:10} {b.detail}")

    out = {"rung": "P0", "arm": "gerundelle", "ticks": world.t, "reached": bool(agent.reached),
           "ledger": world.history, "tried": [(t, list(i), n) for t, i, n in agent.tried],
           "beats": [dataclasses.asdict(b) for b in mind.beats]}
    if not args.no_story:
        scene, sentences, m = story(world, mind)
        print()
        print(" ".join(t for _, t, _ in sentences))
        print()
        for r in m["rows"]:
            if not r["ok"]:
                print(f"  MISS {r['text']}\n        intended {r['shape']}\n        reading  {r['reading'] or r['why']}")
        print(f"round-trip {m['round_trip']:.2f}; sentences {len(sentences)}; history {m['history']}")
        out.update(sentences=[t for _, t, _ in sentences], round_trip=m["round_trip"], history=m["history"])
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "p0_gerundelle.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=str)


if __name__ == "__main__":
    main()
