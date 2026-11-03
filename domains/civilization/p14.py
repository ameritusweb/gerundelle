"""Rung P14: ranges. P4-P13's population configurations, each over several turn orders.

Every population result since P4 is one deterministic run, and from P12 on the directions disagree between populations
and rungs (wants met up in one, down in the other). Gerundelle's minds are deterministic, so a range comes from the order
the minds take their turns (rotated: each mind first in turn) and, for the mixed population, from which temperament has
which station (rotated with the order, so no temperament keeps one station). No new mechanism.

Configurations (each as its rung ran it):
  P4   StationsWorld, sub-wants off          P7   StationsWorld, sub-wants on
  P9   LockWorld (lids)                       P10  LockWorld with marks
  P11  SealWorld, the mover seen              P12  SealWorld, every mind grieves
  P13  SealWorld, every mind grieves and avenges

PREDICTION, written before the first run: the single runs' directions do not all survive. Wants met vary across orders by
at least one want in most configurations; differences between neighbouring rungs smaller than that range are not effects.
What should survive, as structure rather than counts: no specialization (own-station share near chance) in every
configuration; enclosure (seals and lids on others' more than one's own) wherever there are locks; anger only where minds
grieve.

Run: python -X utf8 p14.py [--ticks 2000] [--orders 4] [--procs 6] [--only P4,P7,...]
Writes results/p14_ranges.json and results/p14_ranges.txt.
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIGS = ("P4", "P7", "P9", "P10", "P11", "P12", "P13")
POPS = {"steady": ["steady"] * 4, "mixed": ["steady", "restless", "patient", "dogged"]}


def one(task):
    """One run: (config, population, order) -> its summary. In its own process (Gerundelle's minds are not shared)."""
    config, pop, order, ticks = task
    sys.path.insert(0, HERE)
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))
    import p4
    import p7
    import p9
    import p11
    import p12
    import p13
    from lock_world import LockWorld, SealWorld
    from potential_world import StationsWorld
    tempers = POPS[pop]
    if pop == "mixed":   # which temperament has which station, rotated with the order
        tempers = tempers[order:] + tempers[:order]
    kw = dict(subwants=False, kind=p4.Asking, extra=None, world_cls=StationsWorld)
    if config == "P7":
        kw.update(subwants=True, kind=p7.Planning)
    elif config == "P9":
        kw.update(kind=p7.Planning, world_cls=LockWorld)
    elif config == "P10":
        kw.update(kind=p7.Planning, world_cls=lambda n: LockWorld(n, marks=True))
    elif config == "P11":
        kw.update(kind=p11.Grieving, world_cls=SealWorld)
    elif config == "P12":
        kw.update(kind=p11.Grieving, world_cls=SealWorld, extra=[{"grievance": True}] * 4)
    elif config == "P13":
        p13.AVENGE.clear()
        p13.AVENGE.update({n: True for n in p4.NAMES[:4]})
        kw.update(kind=p13.Avenging, world_cls=SealWorld, extra=[{"grievance": True}] * 4)
    t0 = time.time()
    world, minds, shared = p4.run(tempers, ticks, order=order, **kw)
    rows, _, conserved = p4.measure(world, minds, shared)
    out = dict(config=config, pop=pop, order=order, tempers=tempers, slices=world.t, conservation=conserved,
               met=sum(r["reached"] for r in rows), met_by=[r["temper"] for r in rows if r["reached"]],
               own_share=round(sum(r["own_share"] for r in rows) / len(rows), 3),
               changed_others=sum(r["changed_others"] for r in rows), gave_up=sum(r["gave_up"] for r in rows),
               seconds=round(time.time() - t0))
    if config in ("P9", "P10", "P11", "P12", "P13"):
        locks, _ = p9.lock_measures(world, minds)
        out.update(locked_own=sum(k["shut_own"] for k in locks.values()),
                   locked_others=sum(k["shut_others"] for k in locks.values()),
                   locked_out=sum(k["blocked_by_others"] for k in locks.values()))
    feel = {m.name: p12.feelings(m, shared) for m in minds}
    out["anger"] = sum(sum(f["anger_at"].values()) for f in feel.values())
    names = [m.name for m in minds]
    out["feuds"] = len({tuple(sorted((x, y))) for x in names for y in names if x != y
                        and feel[x]["anger_at"].get(y) and feel[y]["anger_at"].get(x)})
    if config == "P13":
        out["retaliations"] = sum(sum(1 for _, _, _, h in m.revenge if h == "set") for m in minds)
        out["retaliations_met"] = sum(sum(1 for _, _, _, h in m.revenge if h == "met") for m in minds)
    return out


def table(results, orders):
    lines = []
    head = f"{'config':6} {'pop':7} {'wants met per order':>20} {'mean':>5}  {'own':>5} {'changed':>8} {'locked own/others':>17} {'anger':>6} {'feuds':>5}"
    lines.append(head)
    for config in CONFIGS:
        for pop in POPS:
            rs = sorted((r for r in results if r["config"] == config and r["pop"] == pop), key=lambda r: r["order"])
            if not rs:
                continue
            mets = [r["met"] for r in rs]
            mean = lambda k: sum(r.get(k, 0) for r in rs) / len(rs)
            locks = f"{mean('locked_own'):.1f}/{mean('locked_others'):.1f}" if "locked_own" in rs[0] else "-"
            lines.append(f"{config:6} {pop:7} {str(mets):>20} {sum(mets) / len(mets):5.2f}  {mean('own_share'):5.2f} "
                         f"{mean('changed_others'):8.1f} {locks:>17} {mean('anger'):6.1f} {mean('feuds'):5.2f}"
                         + ("" if all(r["conservation"] for r in rs) else "  CONSERVATION BROKEN"))
    return "\n".join(lines)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=2000)
    ap.add_argument("--orders", type=int, default=4)
    ap.add_argument("--procs", type=int, default=6)
    ap.add_argument("--only", default=",".join(CONFIGS))
    args = ap.parse_args()
    tasks = [(c, p, o, args.ticks) for c in args.only.split(",") for p in POPS for o in range(args.orders)]
    results = []
    with Pool(args.procs) as pool:
        for r in pool.imap_unordered(one, tasks):
            results.append(r)
            print(f"[{len(results)}/{len(tasks)}] {r['config']} {r['pop']} order {r['order']}: met {r['met']} "
                  f"({r['met_by']}), anger {r['anger']}, feuds {r['feuds']}, {r['seconds']}s", flush=True)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "p14_ranges.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    t = table(results, args.orders)
    with open(os.path.join(HERE, "results", "p14_ranges.txt"), "w", encoding="utf-8") as f:
        f.write(t + "\n")
    print()
    print(t)


if __name__ == "__main__":
    main()
