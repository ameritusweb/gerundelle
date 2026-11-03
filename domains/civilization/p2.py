"""Rung P2 (PHYSICS.md): does a told blueprint change what a mind can make?

Two Gerundelle minds. Wen has a past: a P1 run on his own copy of the hillside, in which he learned that the hollow makes
a boat only when the carved boat lies in it (a split on the hollow's push). Ada is new to the hillside, with Wen sitting
by. When Ada's own conditions question about a push wins her top, she asks him (Pose across minds); he answers from his
own splits (Attest, `GerundelleMind.answer`), and the answer enters her register as told: conditioned_by, at the told
weight. Then she acts as before. Measured against P1, the same mind alone (fiction's rung 2 test: does Attest save
search?).

My choice (named): fiction's GerundelleMind asks only about pushes on the wanted object (the lid in the box). Here the
blueprint is about the hollow, which is not the wanted object (the skiff is), so `Asking` asks about any push whose
conditions question wins, once per object. Fiction's code is not changed.

Run: python -X utf8 p2.py [--ticks 800] [--tempers steady,restless,...] [--no-story] [--beats]
Writes results/p2_<temper>.json.
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
from beats import effect_parts  # noqa: E402
import p0  # noqa: E402
import p1  # noqa: E402

ACTOR, TELLER, WANT = "Ada", "Wen", p1.WANT


class Asking(GerundelleMind):
    """GerundelleMind that asks about the conditions of a push on any object, not only on the wanted one."""

    def step(self, tries_seen):
        before = set(self.asked)
        out = super().step(tries_seen)
        for q in sorted(self.asked - before):
            _, rel, concept = q.split(":", 2)
            if rel != "conditions" or "_push:" not in concept or not self.others or self.keep:
                continue
            obj = effect_parts(concept.split("_push:")[1], self.world.objs)[0]
            if obj not in self.consulted:
                self.consult(concept, obj)
        return out


LEXICON = dict(p1.LEXICON, **{
    "people": {TELLER: "Old Wen sat on a stone nearby."},
    # subject questions: the printer embeds the question as it stands for "I don't know ...", and "what does the
    # hollow need" embedded is not English ("I don't know what does the hollow need": the first P2 stories)
    "asks": {(o, "conditions"): f"What {q}?" for o, q in {
        "hollow": "belongs in the hollow", "boulder": "breaks the boulder", "jar": "fills the jar",
        "skiff": "lifts the skiff", "model": "moves the carved boat", "shell": "moves the shell",
        "cup": "moves the cup", "spring": "feeds the spring", "pebbles": "moves the pebbles"}.items()},
    "says": {("hollow", "model", "nesting"): "The carved boat belongs in the hollow",
             ("skiff", "jar", "charged"): "A glowing jar lifts the skiff"},
})


def teller(ticks):
    """Wen and his past: a P1 run on his own copy of the hillside (the steady character), kept whole."""
    wen = GerundelleMind(TELLER, PatternWorld(), want=WANT, see=False)
    wen.run(ticks)
    return wen


def run(ticks, temper="steady", told=True, settle=8):
    from temperament import PROFILES
    world = PatternWorld()
    others = [teller(ticks)] if told else []
    mind = Asking(ACTOR, world, want=WANT, others=others, **PROFILES[temper].gerundelle())
    mind.run(ticks, settle=settle)
    return world, mind, others


def told_used(mind):
    """What the telling did: the conditions told, and whether a later realization confirmed the teller."""
    tells = [b for b in mind.beats if b.kind == "tell"]
    confirms = [b for b in mind.beats if b.kind == "learn" and b.detail.get("confirms")]
    return dict(asked=[b.obj for b in mind.beats if b.kind == "ask"], told_conditions=[b.detail.get("condition") for b in tells],
                confirmed=[b.detail["condition"] for b in confirms])


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
        alone_w, alone, _ = run(args.ticks, temper, told=False)
        world, mind, others = run(args.ticks, temper, told=True)
        agent = mind.agent
        totals = {round(r["total"], 9) for r in world.history}
        used = told_used(mind)
        wen_knows = {x: sp["tag"] for x, sp in others[0].agent.mind.meta.splits.items()}
        print(f"[{temper}] alone: reached {bool(alone.agent.reached)}, ticks {alone_w.t}, pushes {len(alone.agent.tried)}"
              f"  |  told: reached {bool(agent.reached)}, ticks {world.t}, pushes {len(agent.tried)}; "
              f"conservation {'HOLDS' if len(totals) == 1 else 'BROKEN'}")
        print(f"  Wen knows {wen_knows}")
        print(f"  asked about {used['asked']}; told {used['told_conditions']}; confirmed by her own tries {used['confirmed']}")
        print(f"  her forming conditions: {p1.forming_conditions(agent)}")
        print("  pushes:", Counter(f"{s} {o}" for _, (s, o, _), _ in agent.tried).most_common())
        for b in mind.beats:
            if args.beats or b.kind in ("ask", "tell", "learn", "surprise", "reach"):
                print(f"    t{b.t:<4} {b.kind:8} {b.actor:4} {b.obj:10} {b.detail}")
        out = dict(temper=temper, alone=dict(reached=bool(alone.agent.reached), ticks=alone_w.t, pushes=len(alone.agent.tried)),
                   told=dict(reached=bool(agent.reached), ticks=world.t, pushes=len(agent.tried)), conservation=len(totals) == 1,
                   wen_knows=wen_knows, **used, forming_conditions=p1.forming_conditions(agent))
        if not args.no_story:
            from measure import evaluate
            from printer import Printer
            from story import tell
            scene = tell(mind.beats, set(world.objs), ACTOR, people=(TELLER,))
            sentences = Printer(LEXICON, ACTOR, p1.PRONOUN).print_scene(scene)
            m = evaluate(scene, sentences)
            print()
            print(" ".join(t for _, t, _ in sentences))
            for r in m["rows"]:
                if not r["ok"]:
                    print(f"  MISS {r['text']}\n        intended {r['shape']}\n        reading  {r['reading'] or r['why']}")
            print(f"  round-trip {m['round_trip']:.2f}; sentences {len(sentences)}")
            out.update(sentences=[t for _, t, _ in sentences], round_trip=m["round_trip"])
        out.update(beats=[dataclasses.asdict(b) for b in mind.beats])
        with open(os.path.join(HERE, "results", f"p2_{temper}.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=str)
        rows.append(out)
        print()
    print(f"{'temper':10} {'alone':>14} {'told':>14}  confirmed")
    for r in rows:
        a, t = r["alone"], r["told"]
        fmt = lambda x: f"{'yes' if x['reached'] else 'no '} {x['pushes']:3d}p {x['ticks']:4d}t"
        print(f"{r['temper']:10} {fmt(a):>14} {fmt(t):>14}  {r['confirmed']}")


if __name__ == "__main__":
    main()
