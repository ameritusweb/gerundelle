"""Rung P12: grievance as a switch and as a trait.

P11 found no grievance in SealWorld because of Gerundelle's theory of possession: a held thing another has moved, still in
view, becomes "another's" (concession); grief, and anger at the taker, need it gone. Gerundelle's `Params.grievance`
(off by default, settable per mind: a trait): a mind that grieves reads its held thing, taken in view, as lost. Here
P11's SealWorld, with the mover visible (p11.Grieving), runs with no mind grieving (P11), every mind grieving, and half
grieving: grievers beside conceders.

PREDICTION, written before the first run: grieving minds feel sadness and anger at the sealers of jars they held, the
sealer named; conceders beside them do not. Anger changes little of what minds do: Gerundelle's anger is a phase whose
sites ask "blame?" of the taker, and nothing in this world lets a mind act on a person (only on things), so grievance is
felt, not acted on. Wants met stay near P11's (0 of 4 steady, 3 of 4 mixed).

Measures: per mind its trait (grieves or concedes), wants met, seals own/others', the sadness and anger formed (in
Gerundelle's phase register, whether or not they won attention) and at whom, and the feel beats that reached the story.

Run: python -X utf8 p12.py [--ticks 2000] [--tempers steady,steady,steady,steady] [--grieve 1,1,1,1]
Writes results/p12_<tempers>_<grieve>.json.
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
import p9  # noqa: E402
import p11  # noqa: E402
from lock_world import SealWorld  # noqa: E402


def feelings(m, shared):
    ph = m.agent.mind.phases
    formed = [(t, p) for t, what, p in ph.log if what in ("formed", "re-opened")]
    anger = Counter(p.split(":")[-1] for _, p in formed if ":anger:" in p)
    sad = Counter(p.split(":")[-1] for _, p in formed if ":sadness:" in p)
    told = Counter(b.detail.get("phase") for b in shared if b.kind == "feel" and b.actor == m.name)
    return dict(anger_at=dict(anger), sadness_over=dict(sad), told=dict(told))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=2000)
    ap.add_argument("--tempers", default="steady,steady,steady,steady")
    ap.add_argument("--grieve", default="1,1,1,1", help="per mind: 1 grieves, 0 concedes")
    args = ap.parse_args()
    tempers = args.tempers.split(",")
    grieve = [g == "1" for g in args.grieve.split(",")]
    world, minds, shared = p4.run(tempers, args.ticks, subwants=False, kind=p11.Grieving, world_cls=SealWorld,
                                  extra=[{"grievance": g} for g in grieve])
    rows, _, conserved = p4.measure(world, minds, shared)
    locks, end = p9.lock_measures(world, minds)
    met = sum(r["reached"] for r in rows)
    feel = {m.name: feelings(m, shared) for m in minds}
    print(f"== grievance {args.grieve}: population {tempers}; wants met {met} of {len(rows)}; slices {world.t}; "
          f"conservation {'HOLDS' if conserved else 'BROKEN'}")
    for r, g in zip(rows, grieve):
        k, f = locks[r["name"]], feel[r["name"]]
        print(f"{r['name']:5} {r['temper']:9} {'grieves' if g else 'concedes':8} reached {str(r['reached_at']) if r['reached'] else 'no':>5}; "
              f"sealed own/others {k['shut_own']}/{k['shut_others']}; locked out {k['blocked_by_others']}; "
              f"anger at {f['anger_at'] or '-'}; sadness over {f['sadness_over'] or '-'}; told {f['told']}")
    print(f"   jars sealed at the end: {end}")
    print(f"   reached: {[(b.t, b.actor, b.obj) for b in shared if b.kind == 'reach']}")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    name = f"p12_{'-'.join(tempers)}_{args.grieve.replace(',', '')}.json"
    with open(os.path.join(HERE, "results", name), "w", encoding="utf-8") as fh:
        json.dump(dict(tempers=tempers, grieve=grieve, slices=world.t, conservation=conserved, minds=rows, locks=locks,
                       feelings=feel, sealed_at_end=end, beats=[dataclasses.asdict(b) for b in shared]),
                  fh, indent=1, default=str)


if __name__ == "__main__":
    main()
