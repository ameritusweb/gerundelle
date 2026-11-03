"""Rung P6: minds that make their own sub-wants (P5's finding 1), and Gerundelle's planner fixed in Gerundelle.

P5 found that no mind reaches a far want down a seven-step chain (the moon's way home), and that an authored curriculum
of three wants carries three minds home. Here the mind makes its own: Gerundelle's `Params.subwants` (sov_agent.py,
`SovAgent.subwant`, off by default, so Gerundelle's own suite is unchanged), measured on P5's single want and on P3's,
fresh minds, sub-wants off against on.

A sub-want is written as a beat of its own (`want`, "Ada set out to ..."), so the story says what she set herself.

Run: python -X utf8 p6.py [--ticks 1500] [--tempers steady,restless,...] [--worlds moon,voyage] [--no-story]
Writes results/p6_<world>_<on|off>_<temper>.json.
"""
import argparse
import dataclasses
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

from gerundelle_arm import GerundelleMind  # noqa: E402
from molecules import Mind, Params  # noqa: E402  (Gerundelle's, on the path fiction set)
from beats import effect_parts  # noqa: E402
import p0  # noqa: E402

ACTOR, PRONOUN = "Ada", "she"


class Planning(GerundelleMind):
    """GerundelleMind that tells the sub-wants its mind sets itself: each new one is a want beat."""

    def step(self, tries_seen):
        before = self.agent.goal
        out = super().step(tries_seen)
        goal = self.agent.goal
        if goal is not None and goal != before and goal != self.want and getattr(self.agent, "stack", None):
            self.beat("want", hole=f"own:control:{effect_parts(goal, self.world.objs)[0]}",
                      obj=effect_parts(goal, self.world.objs)[0], detail={"change": goal, "sub": True})
        return out


def worlds():
    import p3
    import p5
    from moon_world import MoonWorld
    from potential_world import VoyageWorld
    sub_moon = {"pool_glimmering": "set out to fill the pool with light", "flask_charged": "set out to fill the flask",
                "flask_brimming": "set out to fill the flask to the brim", "skiff_lit": "set out to light the skiff",
                "lantern_resting": "set out to make a lantern", "husk_gone": "set out to break the husk"}
    sub_voyage = {"jar_charged": "set out to fill the jar", "jar_brimming": "set out to fill the jar to the brim",
                  "skiff_resting": "set out to make a boat", "hollow_cradling": "set out to make a boat"}
    return {"moon": (MoonWorld, p5.WANT, dict(p5.LEXICON, want={**p5.LEXICON["want"], **sub_moon})),
            "voyage": (VoyageWorld, p3.WANT, dict(p3.LEXICON, want={**p3.LEXICON["want"], **sub_voyage}))}


def run(world_name, ticks, temper="steady", subwants=True, settle=8):
    from temperament import PROFILES
    make, want, _ = worlds()[world_name]
    world = make()
    temper_kw = PROFILES[temper].gerundelle()
    params = {k: v for k, v in temper_kw.items() if k in Params.__dataclass_fields__}
    mind = Mind(Params(inquiry=True, phases=True, subwants=subwants, **params))
    m = Planning(ACTOR, world, want=want, mind=mind, **temper_kw)
    m.run(ticks, settle=settle)
    return world, m


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=1500)
    ap.add_argument("--tempers", default="steady,restless,dogged,impatient,patient")
    ap.add_argument("--worlds", default="moon,voyage")
    ap.add_argument("--no-story", action="store_true")
    args = ap.parse_args()
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    rows = []
    for wn in args.worlds.split(","):
        _, want, lexicon = worlds()[wn]
        for temper in args.tempers.split(","):
            for on in (False, True):
                world, m = run(wn, args.ticks, temper, on)
                a = m.agent
                reached = any(b.kind == "reach" and b.detail.get("change") == want for b in m.beats)
                totals = {round(r["total"], 9) for r in world.history}
                subs = [(t, g, how) for t, g, how in getattr(a, "sub_log", [])]
                row = dict(world=wn, temper=temper, subwants=on, reached=reached, ticks=world.t, pushes=len(a.tried),
                           gave_up=bool(a.gave_up), conservation=len(totals) == 1, subs=subs,
                           made=sum(1 for _, _, h in subs if h == "set"), met=sum(1 for _, _, h in subs if h == "met"),
                           dropped=sum(1 for _, _, h in subs if h == "dropped"))
                label = f"{wn}_{'on' if on else 'off'}_{temper}"
                print(f"[{label}] reached {reached}; ticks {world.t}; pushes {len(a.tried)}; gave up {row['gave_up']}; "
                      f"sub-wants set {row['made']}, met {row['met']}, dropped {row['dropped']}; conservation "
                      f"{'HOLDS' if row['conservation'] else 'BROKEN'}")
                if subs:
                    print("   ", " | ".join(f"t{t} {h} {g}" for t, g, h in subs[:14]))
                if not args.no_story and reached:
                    scene, sentences, ms = p0.story(world, m, lexicon)
                    row.update(sentences=[t for _, t, _ in sentences], round_trip=ms["round_trip"])
                    misses = [r["text"] for r in ms["rows"] if not r["ok"]]
                    print(f"    story: {len(sentences)} sentences, round-trip {ms['round_trip']:.2f}"
                          + (f"; misses {misses}" if misses else ""))
                row.update(beats=[dataclasses.asdict(b) for b in m.beats])
                with open(os.path.join(HERE, "results", f"p6_{label}.json"), "w", encoding="utf-8") as f:
                    json.dump(row, f, indent=1, default=str)
                rows.append(row)
    print(f"\n{'world':7} {'temper':9} {'off':>14} {'on':>14}  sub-wants (set/met/dropped)")
    for wn in args.worlds.split(","):
        for temper in args.tempers.split(","):
            off = next(r for r in rows if r["world"] == wn and r["temper"] == temper and not r["subwants"])
            on = next(r for r in rows if r["world"] == wn and r["temper"] == temper and r["subwants"])
            f = lambda r: f"{'yes' if r['reached'] else ('gave up' if r['gave_up'] else 'no')} {r['ticks']}t"
            print(f"{wn:7} {temper:9} {f(off):>14} {f(on):>14}  {on['made']}/{on['met']}/{on['dropped']}")


if __name__ == "__main__":
    main()
