"""Rung P8: a keeper's sub-want. Does a mind that keeps the state it made for its want defend it when another undoes it?

P7 found no defending: a mind with sub-wants in P4's commons does not guard its jar, it acts sooner in the situation it
wanted. Defending needs a state wanted to last. Gerundelle's `Params.keep_subs` (P8; off by default, needs subwants): a
sub-want met is kept for the want it serves; if it is gone before that want's push uses it, and the mind's own last push
did not change it, something else undid it, and the mind restores it (sets it again as its current want). Here P7's
populations run with sub-wants on and keeping off (P7's numbers) against keeping on.

PREDICTION, written before the first run: restores happen (a kept jar undone by another's curiosity, filled again);
anger rises (Gerundelle reads another's undoing of a held region as anger at the one who moved it); wants met rise or
hold; and the mind that restores holds its own station more (own-station share up).

Measures: P7's (wants met, own-station share, changes on others' stations, sub-wants set/met/tried), and per mind kept,
restored, used (spent by its own push, as a launch spends the jar), released (the want it served no longer held); anger.

Run: python -X utf8 p8.py [--ticks 2000] [--tempers steady,steady,steady,steady] [--only off,on]
Writes results/p8_<tempers>_<keep|nokeep>.json.
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
import p7  # noqa: E402


def keep_measures(minds):
    out = {}
    for m in minds:
        c = Counter(h for _, _, h in getattr(m.agent, "sub_log", []))
        restored = Counter(g for _, g, h in m.agent.sub_log if h == "restored")
        out[m.name] = dict(kept=c["kept"], restored=c["restored"], used=c["used"], released=c["released"],
                           set=c["set"], met=c["met"], tried=c["tried"], dropped=c["dropped"],
                           restored_what=restored.most_common(3))
    return out


def thief_run(temper, keep, thefts=2, ticks=1500, settle=8):
    """The controlled test (authored events, named: fiction's take/give are the precedent). In P3's VoyageWorld, one
    mind with sub-wants on; each time it keeps "the jar brimming" (a sub-want met), a thief spills the jar before the
    mind's next turn, up to `thefts` times. The world's act is stepped by the thief as another actor, so the mind sees
    it as another's doing (fiction's look()). Returns (world, mind, thefts done, reached)."""
    from temperament import PROFILES
    from molecules import Mind, Params
    from potential_world import VoyageWorld
    import p3
    import p6
    world = VoyageWorld()
    kw = PROFILES[temper].gerundelle()
    params = {x: v for x, v in kw.items() if x in Params.__dataclass_fields__}
    mind = Mind(Params(inquiry=True, phases=True, subwants=True, keep_subs=keep, **params))
    m = p6.Planning("Ada", world, want=p3.WANT, mind=mind, **kw)
    done, seen_log, tries = 0, 0, 0
    for _ in range(ticks):
        world.actor = "Ada"
        tries = m.step(tries)
        log = m.agent.sub_log
        new, seen_log = log[seen_log:], len(log)
        made = any(g == "jar_brimming" and h == "met" for _, g, h in new)
        if made and done < thefts and world.gerund.get("jar") == "brimming" and not m.pending:
            world.actor = "Thief"
            world.act(("hard", "jar", "brimming"))
            done += 1
            world.actor = "Ada"
        if m.pending:
            for _ in range(settle):
                tries = m.step(tries)
            m.write_try(*m.pending, reach=True)
            break
        if m.agent.gave_up:
            break
    reached = any(b.kind == "reach" and b.detail.get("change") == p3.WANT for b in m.beats)
    return world, m, done, reached


def thief_main(tempers, ticks):
    print("== the thief: P3's voyage, one mind, sub-wants on; the jar spilled after each 'jar_brimming' met (up to 2)")
    print(f"{'temper':9} {'keeping':>7} {'thefts':>6} {'reached':>8} {'ticks':>5}  sub-log (after the first theft)")
    for temper in tempers:
        for keep in (False, True):
            world, m, done, reached = thief_run(temper, keep, ticks=ticks)
            log = m.agent.sub_log
            first = next((i for i, (_, g, h) in enumerate(log) if g == "jar_brimming" and h == "met"), 0)
            tail = " | ".join(f"t{t} {h} {g}" for t, g, h in log[first:first + 7])
            print(f"{temper:9} {'on' if keep else 'off':>7} {done:>6} {'yes' if reached else 'no':>8} {world.t:>5}  {tail}")
            with open(os.path.join(HERE, "results", f"p8_thief_{temper}_{'keep' if keep else 'nokeep'}.json"), "w",
                      encoding="utf-8") as f:
                json.dump(dict(temper=temper, keep=keep, thefts=done, reached=reached, ticks=world.t, sub_log=log,
                               beats=[dataclasses.asdict(b) for b in m.beats]), f, indent=1, default=str)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=2000)
    ap.add_argument("--tempers", default="steady,steady,steady,steady")
    ap.add_argument("--only", default="off,on")
    ap.add_argument("--thief", action="store_true", help="the controlled test (thief_run) instead of the populations")
    args = ap.parse_args()
    tempers = args.tempers.split(",")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    if args.thief:
        thief_main(tempers, args.ticks)
        return
    for mode in args.only.split(","):
        keep = mode == "on"
        world, minds, shared = p4.run(tempers, args.ticks, subwants=True, kind=p7.Planning, extra={"keep_subs": keep})
        rows, shared_regions, conserved = p4.measure(world, minds, shared)
        ks = keep_measures(minds)
        met = sum(r["reached"] for r in rows)
        anger = sum(r["phases"].get("anger", 0) for r in rows)
        print(f"== keeping {mode}: population {tempers}; wants met {met} of {len(rows)}; anger {anger}; slices {world.t}; "
              f"conservation {'HOLDS' if conserved else 'BROKEN'}")
        print(f"{'mind':5} {'temper':9} {'reached':>8} {'gave up':>7} {'pushes':>6} {'own':>5} {'changed':>7}  "
              f"{'set/met/tried':>13} {'kept':>4} {'restored':>8} {'used':>4} {'released':>8}  phases")
        for r in rows:
            k = ks[r["name"]]
            print(f"{r['name']:5} {r['temper']:9} {str(r['reached_at']) if r['reached'] else 'no':>8} "
                  f"{'yes' if r['gave_up'] else 'no':>7} {r['pushes']:6d} {r['own_share']:5.2f} {r['changed_others']:7d}  "
                  f"{k['set']:>7}/{k['met']}/{k['tried']:<3} {k['kept']:>4} {k['restored']:>8} {k['used']:>4} "
                  f"{k['released']:>8}  {r['phases']}")
        for name, k in ks.items():
            if k["restored_what"]:
                print(f"   {name} restored {k['restored_what']}")
        print(f"   reached: {[(b.t, b.actor, b.obj, b.detail.get('by', 'own push')) for b in shared if b.kind == 'reach']}")
        with open(os.path.join(HERE, "results", f"p8_{'-'.join(tempers)}_{'keep' if keep else 'nokeep'}.json"), "w",
                  encoding="utf-8") as f:
            json.dump(dict(tempers=tempers, keep=keep, slices=world.t, conservation=conserved, minds=rows, keeping=ks,
                           beats=[dataclasses.asdict(b) for b in shared]), f, indent=1, default=str)
        print()


if __name__ == "__main__":
    main()
