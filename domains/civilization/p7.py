"""Rung P7: sub-wants in a population. Does a mind that sets itself "my jar to the brim" defend that state?

P4 found that a population with no scarcity of potential reaches few wants (1-2 of 4) because the jars are a commons:
curiosity empties and spills each other's jars, and a stable state, not matter, is what is scarce. P6 gave Gerundelle
sub-wants (Params.subwants): a mind that finds no way to its want sets itself a nearer one. Here the same population, in
the same StationsWorld, runs with sub-wants on, against P4's numbers (sub-wants off, the same runner).

PREDICTION, written before the first run: sub-wants raise the wants met above P4's 1-2 of 4, and minds re-make states
others undid (a sub-want set again for a fact it had already met: defending by remaking), with more anger, as an undone
sub-want is a claim that failed by another's hand. Pushes on others' stations do not fall much: curiosity is unchanged.

Measures: P4's (p4.measure: wants met, own-station share, changes on others' stations, asks, phases, give-ups), and per
mind: sub-wants set, met, dropped; sub-wants on its own station's objects; and re-makes (a sub-want set for a fact the
mind had met as a sub-want before: the state was lost between).

Run: python -X utf8 p7.py [--ticks 2000] [--tempers steady,steady,steady,steady]
Writes results/p7_<tempers>_<on|off>.json.
"""
import argparse
import dataclasses
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

import p4  # noqa: E402
from p2 import Asking  # noqa: E402
from beats import effect_parts  # noqa: E402


class Planning(Asking):
    """p2.Asking (asks the others) that also tells the sub-wants it sets itself, as want beats."""

    def step(self, tries_seen):
        before = self.agent.goal
        out = super().step(tries_seen)
        goal = self.agent.goal
        if goal is not None and goal != before and goal != self.want and self.agent.stack:
            self.beat("want", hole=f"own:control:{effect_parts(goal, self.world.objs)[0]}",
                      obj=effect_parts(goal, self.world.objs)[0], detail={"change": goal, "sub": True})
        return out


def sub_measures(world, minds):
    out = {}
    for m in minds:
        log = getattr(m.agent, "sub_log", [])
        sets = [g for _, g, h in log if h == "set"]
        met_before, remakes = set(), 0
        for _, g, h in log:
            if h == "set" and g in met_before:
                remakes += 1
            if h == "met":
                met_before.add(g)
        own = sum(1 for g in sets if world.station(effect_parts(g, world.objs)[0]) == m.station)
        out[m.name] = dict(set=len(sets), met=sum(1 for _, _, h in log if h == "met"),
                           tried=sum(1 for _, _, h in log if h == "tried"),
                           dropped=sum(1 for _, _, h in log if h == "dropped"), own=own, remakes=remakes,
                           which=Counter(sets).most_common(4))
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=2000)
    ap.add_argument("--tempers", default="steady,steady,steady,steady")
    ap.add_argument("--only", default="off,on")
    args = ap.parse_args()
    tempers = args.tempers.split(",")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    for mode in args.only.split(","):
        on = mode == "on"
        world, minds, shared = p4.run(tempers, args.ticks, subwants=on, kind=Planning)
        rows, shared_regions, conserved = p4.measure(world, minds, shared)
        subs = sub_measures(world, minds)
        met = sum(r["reached"] for r in rows)
        print(f"== sub-wants {mode}: population {tempers}; wants met {met} of {len(rows)}; slices {world.t}; "
              f"conservation {'HOLDS' if conserved else 'BROKEN'}; moon's field {world.book.elsewhere['moon']:g}")
        print(f"{'mind':5} {'temper':9} {'reached':>8} {'gave up':>7} {'pushes':>6} {'own':>5} {'changed':>7} {'asks':>4}  "
              f"{'subs set/met/drop/tried':>23} {'own':>4} {'remake':>6}  phases")
        for r in rows:
            s = subs[r["name"]]
            print(f"{r['name']:5} {r['temper']:9} {str(r['reached_at']) if r['reached'] else 'no':>8} "
                  f"{'yes' if r['gave_up'] else 'no':>7} {r['pushes']:6d} {r['own_share']:5.2f} {r['changed_others']:7d} "
                  f"{r['asks']:4d}  {s['set']:>9}/{s['met']}/{s['dropped']}/{s['tried']:<5} {s['own']:>9} {s['remakes']:>6}  {r['phases']}")
        for name, s in subs.items():
            if s["which"]:
                print(f"   {name}'s sub-wants: {s['which']}")
        reach = [(b.t, b.actor, b.obj, b.detail.get("by", "own push")) for b in shared if b.kind == "reach"]
        print(f"   reached: {reach}")
        with open(os.path.join(HERE, "results", f"p7_{'-'.join(tempers)}_{mode}.json"), "w", encoding="utf-8") as f:
            json.dump(dict(tempers=tempers, subwants=on, slices=world.t, conservation=conserved, minds=rows, subs=subs,
                           shared_regions=shared_regions, beats=[dataclasses.asdict(b) for b in shared]),
                      f, indent=1, default=str)
        print()


if __name__ == "__main__":
    main()
