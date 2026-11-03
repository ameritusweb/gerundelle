"""Rung 9: recombination within a statement, and the comparison with POC3.

A fifth seed (POC3's flow 9, positions + insert: `for v4 in range(len(v1)): v3.insert(v4, (v1[v4], v2[v4]))`) is one more
way the patterns can tell; wiring alone sets it under a positions or enumerate loop (rung 9's check: no conjunction
learner needed). The known answers: flows 10 and 11, the insert verb with the enumerate seed's pair,
`v3.insert(v4, (v5, v2[v4]))` under enumerate(v1), and with that pair varied (rung 8), `v3.insert(v4, (v1[v4], v5))`
under enumerate(v2). Neither is a wiring or a variation of one way: they join parts of two.

The capability (new in the mind): recombining two held ways. A value operation of one (the host) is replaced by a value
operation of the same type from another (the donor, as held: varied too, if it was), wired in scope like any way
(StmtWorld.recombine; typed by poc2's grammar in the seeds: untyped splicing would be noise; names are left to the
wiring). The trigger (the user's): only after every whole way and every variation is exhausted: nothing untried,
nothing left for the patterns to tell, every held way varied. Pairs with ways seen to work first.

The comparison with POC3 (52 skeletons, 12 flows; 9 of them not churn: flows 0, 2 and 3 wrap and pop, rung 8) is run
over several orders in which the patterns tell their ways, and the range reported: what a scarce population holds
depends on the order of telling.

Run: python -X utf8 rung9.py [--orders 6] [--ticks 800]
"""
import argparse
import random
import sys

import rung8
import rung7
import rung6
import stmtworld as S
import grammar as G  # noqa: E402
import references as R  # noqa: E402

S.SEEDS["insert"] = lambda: R.color_line_with(G.iterating_over_positions(G.name("v4"), G.name("v1"), G.block(
    G.inserting(G.name("v3"), G.name("v4"), G.pairing(G.indexing(G.name("v1"), G.name("v4")),
                                                      G.indexing(G.name("v2"), G.name("v4")))))))
CHURN = {"flow00", "flow02", "flow03"}
ALL12 = {f"flow{k:02d}" for k in range(12)}


class RecombineMind(rung8.VaryMind):
    def choose(self):
        w = self.world
        done = {(x.inv[0], x.inv[1]) for x in self.tries}
        untried = [i for i in w.invitations() if i[1] != self.wanted() and (i[0], i[1]) not in done]
        run = next(i for i in w.invitations() if i[1] == self.wanted())
        held = [s for slot, s in w.known if slot == "growth"]
        varied = {s for slot, s in getattr(w, "varied", set()) if slot == "growth"}
        told_out = all(p.tell(w.known) is None for p in self.patterns)
        if (not untried and told_out and set(held) <= varied and self.stale(run)
                and w.spec_state != "passing"):
            worked = getattr(self, "worked", set())
            order = list(S.SEEDS)
            pairs = sorted(((h, d) for h in held for d in held if h != d
                            and (h, d) not in getattr(w, "recombined", set())),
                           key=lambda p: (p[1] not in worked, p[0] not in worked, order.index(p[0]),
                                          order.index(p[1])))
            if pairs:   # everything whole and varied exhausted: recombine two held ways
                w.recombine(*pairs[0])
                self.beat("wonder", obj="growth", detail={"recombine": pairs[0]})
        return super().choose()


def population(scarce, ticks, patience, order):
    reg = rung6.Registry(scarce)
    patterns = (rung7.Pattern("Growth", "growth"), rung7.Pattern("Header", "header"))
    for p in patterns:
        p.seeds = list(order)   # the order this population is told the seeds' ways in
    codes = []
    for header in ("positions", "zip", "enumerate"):
        for recalled in (None, "positions", "accumulate", "enumerate"):
            c = rung7.Code(f"{header[:3]}-{recalled or 'court'}", header, recalled, reg, patterns)
            c.mind.__class__ = RecombineMind
            c.mind.patience = patience
            codes.append(c)
    for _ in range(ticks):
        for c in codes:
            m = c.mind
            if c.resigned:
                continue
            if m.want and m.want.closed is not None and not m.done:
                m.keep, m.want.closed, m.done = True, None, False
            if not m.done:
                m.tick()
    held = set()
    for c in codes:
        f = c.holds() if scarce else (c.world.flow() if c.world.spec_state == "passing" else None)
        if f:
            held.add(f)
    how = {c.holds(): [b.detail.get("recombine") or b.detail.get("vary") for b in c.mind.beats
                       if b.kind == "wonder" and ("recombine" in b.detail or "vary" in b.detail)][-1:]
           for c in codes if scarce and c.holds()}
    return held, how


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--orders", type=int, default=6)
    ap.add_argument("--ticks", type=int, default=800)
    args = ap.parse_args()
    rung7.NAMES = rung7.flow_names()
    seeds = list(S.SEEDS)
    orders = [seeds] + [random.Random(k).sample(seeds, len(seeds)) for k in range(1, args.orders)]
    print(f"{'scarcity':8} {'patience':>8} {'telling order':48} {'of 12':>5} {'of 9':>4} {'new':>3}  flows")
    rows = []
    for scarce, patience in ((True, 24), (True, 48)):
        for order in orders:
            held, how = population(scarce, args.ticks, patience, order)
            ours = held & ALL12
            r = (len(ours), len(ours - CHURN), len(held - ALL12))
            rows.append((patience, r, ours))
            print(f"{str(scarce):8} {patience:>8} {' > '.join(order):48} {r[0]:>5} {r[1]:>4} {r[2]:>3}  "
                  f"{sorted(ours)} {'(10, 11 by ' + str([how.get(f) for f in ('flow10', 'flow11')]) + ')' if {'flow10', 'flow11'} & ours else ''}",
                  flush=True)
    held, _ = population(False, args.ticks, 24, orders[0])
    print(f"{'False':8} {24:>8} {' > '.join(orders[0]):48} {len(held & ALL12):>5} {len((held & ALL12) - CHURN):>4} "
          f"{len(held - ALL12):>3}  {sorted(held & ALL12)}")
    for p in (24, 48):
        rs = [r for pp, r, _ in rows if pp == p]
        union = set().union(*[o for pp, _, o in rows if pp == p])
        print(f"patience {p}: of 12 {min(r[0] for r in rs)}-{max(r[0] for r in rs)}, of 9 {min(r[1] for r in rs)}-"
              f"{max(r[1] for r in rs)}, new {min(r[2] for r in rs)}-{max(r[2] for r in rs)}; over all orders "
              f"{len(union)} of 12, {len(union - CHURN)} of 9: {sorted(union)}")


if __name__ == "__main__":
    main()
