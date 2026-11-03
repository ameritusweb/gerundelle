"""Rung P4 (PHYSICS.md): what does a population do with no scarcity?

Several Gerundelle minds in one StationsWorld, acting in turns (fiction's rung 4 way: each mind's step is a slice of
the shared world, and each sees what the others' slices changed). One station per mind and a spring with a field to
spare: nothing is short. Mind k wants skiff k on the moon, but nothing assigns a station to a mind, and any mind can
push any object. They can ask each other (p2.Asking: a conditions question that wins is put to the others; each
answers from its own splits).

PREDICTION, written before the first run (README: "write predictions down before the run so a surprise counts as a
surprise"; cognitivecode lesson 9, scarcity drives variety): little specialization, little conflict, little exchange.
Each mind works mostly its own station; pushes on another's station are curiosity, not contest; anger at a person is
rare; asks are few, as no mind needs another's knowledge to reach its want. This is the baseline the scarcity rungs
are measured against.

Measures, per mind: reached (and when), gave up, pushes; the share of its pushes on its own station (specialization by
want), pushes on others' stations and how many changed something there (interference); anger and the other phases;
asks and tells. For the population: conservation at every slice; regions more than one mind ever claimed.

Run: python -X utf8 p4.py [--ticks 1200] [--tempers steady,steady,steady,steady] [--story]
Writes results/p4_<tempers>.json.
"""
import argparse
import dataclasses
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

from potential_world import StationsWorld  # noqa: E402
from p2 import Asking  # noqa: E402

NAMES = ["Ada", "Ben", "Cal", "Dee", "Eli", "Fay", "Gus", "Hal"]


def run(tempers, ticks, settle=8, subwants=False, kind=Asking, extra=None, world_cls=StationsWorld, order=0):
    """subwants: Gerundelle's Params.subwants for every mind (P7); kind: the GerundelleMind class (P7 tells sub-wants);
    extra: further Params for every mind (P8: keep_subs); world_cls: the world (P9: LockWorld); order: the turn order,
    rotated by this many (P14: the minds are deterministic, so the order is where a range comes from)."""
    from temperament import PROFILES
    from molecules import Mind, Params
    world = world_cls(len(tempers))
    shared = []
    minds = []
    for k, temper in enumerate(tempers):
        kw = PROFILES[temper].gerundelle()
        params = {x: v for x, v in kw.items() if x in Params.__dataclass_fields__}
        own = extra[k] if isinstance(extra, (list, tuple)) else extra   # (P12: a trait per mind)
        mind = Mind(Params(inquiry=True, phases=True, subwants=subwants, **params, **(own or {})))
        m = kind(NAMES[k], world, want=f"skiff{k + 1}_arriving", beats=shared, see=(k == 0), mind=mind, **kw)
        m.station, m.temper = str(k + 1), temper
        minds.append(m)
    for m in minds:
        m.others = [o for o in minds if o is not m]
    seen = {m.name: 0 for m in minds}
    left = {}   # mind -> settling steps left after its want was met
    turns = minds[order % len(minds):] + minds[:order % len(minds)]
    for _ in range(ticks):
        for m in turns:
            if m.done:
                continue
            world.actor = m.name
            seen[m.name] = m.step(seen[m.name])
            if m.agent.gave_up:
                m.done = True
            if m.pending:
                left[m.name] = left.get(m.name, settle) - 1
                if left[m.name] <= 0:
                    m.write_try(*m.pending, reach=True)
        if all(m.done for m in minds):
            break
    for m in minds:   # what each saw of the end
        world.actor = m.name
        m.look()
    return world, minds, shared


def measure(world, minds, shared):
    rows = []
    claimed_by = {}
    for m in minds:
        a = m.agent
        own = sum(1 for _, inv, _ in a.tried if world.station(inv[1]) == m.station)
        theirs = [(inv, n) for _, inv, n in a.tried if world.station(inv[1]) not in ("", m.station)]
        moved = sum(1 for _, n in theirs if n != ["no_change"])
        phases = Counter(p.split(":")[1] for p in m.phases_seen)
        reach = next((b.t for b in shared if b.kind == "reach" and b.actor == m.name), None)
        for r, row in a.mind.territory.rows.items():
            if any(h == "claimed" for _, h in row.get("history", [])):
                claimed_by.setdefault(r, set()).add(m.name)
        rows.append(dict(name=m.name, temper=m.temper, station=m.station, reached=reach is not None, reached_at=reach,
                         gave_up=bool(a.gave_up), pushes=len(a.tried), own_share=own / len(a.tried) if a.tried else 0.0,
                         on_others=len(theirs), changed_others=moved, phases=dict(phases),
                         asks=sum(1 for b in shared if b.kind == "ask" and b.actor == m.name),
                         answered=sum(1 for b in shared if b.kind == "tell" and b.actor == m.name and b.detail.get("condition"))))
    shared_regions = {r: sorted(ns) for r, ns in claimed_by.items() if len(ns) > 1}
    totals = {round(r["total"], 9) for r in world.history}
    return rows, shared_regions, len(totals) == 1


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=1200, help="rounds (each mind steps once per round)")
    ap.add_argument("--tempers", default="steady,steady,steady,steady")
    args = ap.parse_args()
    tempers = args.tempers.split(",")
    world, minds, shared = run(tempers, args.ticks)
    rows, shared_regions, conserved = measure(world, minds, shared)
    print(f"population {tempers}; world slices {world.t}; conservation {'HOLDS' if conserved else 'BROKEN'}; "
          f"moon's field {world.book.elsewhere['moon']:g}")
    print(f"{'mind':5} {'temper':9} {'reached':>8} {'gave up':>7} {'pushes':>6} {'own':>5} {'others':>6} {'changed':>7} "
          f"{'asks':>4} {'told':>4}  phases")
    for r in rows:
        print(f"{r['name']:5} {r['temper']:9} {str(r['reached_at']) if r['reached'] else 'no':>8} "
              f"{'yes' if r['gave_up'] else 'no':>7} {r['pushes']:6d} {r['own_share']:5.2f} {r['on_others']:6d} "
              f"{r['changed_others']:7d} {r['asks']:4d} {r['answered']:4d}  {r['phases']}")
    print(f"regions more than one mind claimed: {shared_regions or 'none'}")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", f"p4_{'-'.join(tempers)}.json"), "w", encoding="utf-8") as f:
        json.dump(dict(tempers=tempers, slices=world.t, conservation=conserved, minds=rows, shared_regions=shared_regions,
                       ledger=world.history, beats=[dataclasses.asdict(b) for b in shared]), f, indent=1, default=str)


if __name__ == "__main__":
    main()
