"""Rung P1 (PHYSICS.md): does a mind learn forming's hidden condition when it starts without the right pattern?

The world is PatternWorld: a blank hollow that forms the shape of whatever lies pressed in it, a spiral shell on the
slope (the wrong pattern: it forms a cup), and the right one, a little carved boat, inside the boulder. One want: the
skiff flying. The mind is Gerundelle, unchanged, through fiction's GerundelleMind; the story is fiction's pipeline.

Measures: the want reached; conservation at every slice; the conditions learned on forming (splits on the hollow's push:
which object lying in it it turns on), and whether the right one was learned by contrast; the story's round-trip.
`--tempers` runs fiction's temperament profiles (temperament.py), so the rung reports a range, not one character.

Run: python -X utf8 p1.py [--ticks 600] [--beats] [--no-story] [--tempers steady,restless,dogged,...]
Writes results/p1_<temper>.json.
"""
import argparse
import dataclasses
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

from potential_world import PatternWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402
import p0  # noqa: E402

ACTOR, PRONOUN, WANT = "Ada", "she", "skiff_flying"

LEXICON = {
    "frame": "There was a spring of light at the foot of a hill.",
    "nouns": {"spring": ("the spring", "the spring"), "jar": ("a clay jar", "the jar"),
              "hollow": ("a smooth hollow", "the hollow"), "shell": ("a spiral shell", "the shell"),
              "boulder": ("a boulder", "the boulder"), "model": ("a little carved boat", "the carved boat"),
              "skiff": ("a small skiff", "the skiff"), "cup": ("a shell-shaped cup", "the cup"),
              "pebbles": ("a heap of pebbles", "the pebbles")},
    "states": {},
    "states_obj": {("spring", "welling"): "glowed softly", ("jar", "charged"): "glowed beside it",
                   ("hollow", "open"): "lay open in the rock", ("shell", "resting"): "lay on the slope",
                   ("boulder", "resting"): "sat on the slope"},
    "flips": {("resting", "nesting"): "settled into the hollow", ("nesting", "resting"): "came out of the hollow",
              ("unformed", "resting"): "took shape beside the hollow", ("propelling", "flying"): "rose into the air",
              ("flying", "resting"): "came down on the far hill", ("resting", "cleaving"): "split apart",
              ("unformed", "piling"): "lay on the ground", ("empty", "charged"): "began to glow",
              ("charged", "empty"): "went dark", ("welling", "dry"): "ran dry", ("dry", "welling"): "glowed again"},
    "flips_obj": {("model", "unformed", "resting"): "lay among the pieces"},
    "skip": {("cleaving", "gone"), ("resting", "propelling")},
    "push": {"light": "touched {N}", "hard": "pushed {N} hard"},
    "push_obj": {("light", "jar"): "dipped {N} into the spring", ("hard", "jar"): "shook {N}",
                 ("light", "shell"): "moved {N}", ("hard", "shell"): "moved {N}",
                 ("light", "model"): "moved {N}", ("hard", "model"): "moved {N}"},
    "want": {WANT: "wanted to send a boat into the sky"},
    "slots": {"causes": "what {N} did", "conditions": "what {N} needed", "role": "what {N} had to do with it",
              "co_occurs": "what came with {N}", "caused_by": "what moved {N}"},
    "conditions": {("hollow", "model", "nesting"): ("{N} made a boat only when {C} lay in it", p0.LEXICON["conditions"][
                       ("skiff", "jar", "charged")][1]),
                   ("hollow", "shell", "nesting"): ("{N} made a cup only when {C} lay in it", p0.LEXICON["conditions"][
                       ("skiff", "jar", "charged")][1]),
                   ("skiff", "jar", "charged"): p0.LEXICON["conditions"][("skiff", "jar", "charged")]},
    "waits": {},
}


def run(ticks, temper="steady", settle=8):
    from temperament import PROFILES
    world = PatternWorld()
    mind = GerundelleMind(ACTOR, world, want=WANT, **PROFILES[temper].gerundelle())
    mind.run(ticks, settle=settle)
    return world, mind


def forming_conditions(agent):
    """The splits on the hollow's pushes: the facts forming was found to turn on."""
    return {x: sp["tag"] for x, sp in agent.mind.meta.splits.items() if "_push:hollow" in x.split("|")[0]}


def report(temper, world, mind, show_beats=False):
    agent = mind.agent
    totals = {round(r["total"], 9) for r in world.history}
    conds = forming_conditions(agent)
    right = any(t == "model_nesting" for t in conds.values())
    print(f"[{temper}] ticks {world.t}; pushes {len(agent.tried)}; reached {bool(agent.reached)}; "
          f"gave up {bool(agent.gave_up)}; conservation {'HOLDS' if len(totals) == 1 else 'BROKEN'}")
    print(f"  forming's conditions learned: {conds or 'none'}  (the right pattern: {'yes' if right else 'no'})")
    splits = {x: sp["tag"] for x, sp in agent.mind.meta.splits.items()}
    print(f"  every split: {splits}")
    print("  pushes:", Counter(f"{s} {o}" for _, (s, o, _), _ in agent.tried).most_common())
    print("  made:", sorted(o for o in ("cup", "skiff", "model") if o in world.gerund))
    for b in mind.beats:
        if show_beats or b.kind in ("learn", "surprise", "reach", "feel"):
            print(f"    t{b.t:<4} {b.kind:8} {b.obj:10} {b.detail}")
    return dict(temper=temper, ticks=world.t, pushes=len(agent.tried), reached=bool(agent.reached),
                conservation=len(totals) == 1, forming_conditions=conds, right_pattern=right,
                splits={x: sp["tag"] for x, sp in agent.mind.meta.splits.items()})


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=600)
    ap.add_argument("--beats", action="store_true")
    ap.add_argument("--no-story", action="store_true")
    ap.add_argument("--tempers", default="steady")
    args = ap.parse_args()
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    for temper in args.tempers.split(","):
        world, mind = run(args.ticks, temper)
        out = report(temper, world, mind, args.beats)
        if not args.no_story:
            scene, sentences, m = p0.story(world, mind, LEXICON)
            print()
            print(" ".join(t for _, t, _ in sentences))
            for r in m["rows"]:
                if not r["ok"]:
                    print(f"  MISS {r['text']}\n        intended {r['shape']}\n        reading  {r['reading'] or r['why']}")
            print(f"  round-trip {m['round_trip']:.2f}; sentences {len(sentences)}; history {m['history']}")
            out.update(sentences=[t for _, t, _ in sentences], round_trip=m["round_trip"])
        out.update(ledger=world.history, beats=[dataclasses.asdict(b) for b in mind.beats])
        with open(os.path.join(HERE, "results", f"p1_{temper}.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=str)
        print()


if __name__ == "__main__":
    main()
