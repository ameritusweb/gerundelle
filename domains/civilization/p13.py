"""Rung P13: acting on grievance (retaliation), and whether it becomes conflict.

P12 gave Gerundelle grievance: a mind that grieves feels anger at the one seen moving a thing it held. But the anger was
felt, not acted on: nothing let a mind act because of another mind. Here an avenger (a trait, per mind) answers its
anger's "blame?" with an act: a want to undo something the blamed one did. Of the objects whose last change it saw was
the blamed mind's move, not ones it holds itself, it wants one back in another state a push it knows can make (the jar
the other filled, spilled). The want is held on the mind's stack, as a sub-want is: Gerundelle's planner pursues it,
its sub-want budget drops it if it stalls, and the mind's own want comes back when it is met. Once per anger.

My choice (named): retaliation is the arm's (`Avenging`), not Gerundelle's, because who moved what is the arm's
perception (fiction's look(), made visible at P11); Gerundelle is unchanged. The world is P11's SealWorld, the minds
grieve (P12's Params.grievance), sub-wants off.

PREDICTION, written before the first run: retaliation lands on the one blamed, who is often not the encloser (P12 finding
2); a target that grieves too is angered back, and pairs fall into feuds (mutual anger, retaliation both ways); wants met
fall below P12's.

Measures: per mind its traits (grieves, avenges), wants met, the retaliations set, met and dropped and at whom; anger and
at whom; feuds (pairs angry at each other, and pairs that retaliated against each other); seals.

Run: python -X utf8 p13.py [--ticks 2000] [--tempers steady,...] [--grieve 1,1,1,1] [--avenge 1,1,1,1]
Writes results/p13_<tempers>_<grieve>_<avenge>.json.
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
import p12  # noqa: E402
from beats import effect_parts  # noqa: E402
from lock_world import SealWorld  # noqa: E402

AVENGE = {}   # mind name -> avenges (set by the runner before the minds are made)


class Avenging(p11.Grieving):
    """P11's Grieving (the mover visible) that, if it avenges, acts on its anger: a want to undo something the blamed did."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.avenges = AVENGE.get(self.name, False)
        self.last_mover = {}    # object -> (the mind whose move last changed it, the state it left)
        self.answered = set()   # anger phases already answered
        self.revenge = []       # (tick, at whom, the state wanted, 'set' | 'met' | 'dropped')
        self.pending_revenge = None

    def look(self):
        movers = super().look()
        for o, actor in movers.items():
            if actor != self.name and o in self.world.gerund:
                self.last_mover[o] = (actor, self.world.gerund[o])
        return movers

    def step(self, tries_seen):
        a = self.agent
        if self.pending_revenge and self.pending_revenge not in [a.goal] + a.stack:   # met or dropped since
            met = any(g == self.pending_revenge and h == "met" for _, g, h in a.sub_log)
            who = next(w for _, w, g, h in reversed(self.revenge) if g == self.pending_revenge and h == "set")
            self.revenge.append((self.world.t, who, self.pending_revenge, "met" if met else "dropped"))
            self.pending_revenge = None
        if self.avenges and self.pending_revenge is None and not a.watching and not a.queue and not self.done:
            self.avenge()
        return super().step(tries_seen)

    def avenge(self):
        a, ph = self.agent, self.agent.mind.phases
        terr = a.mind.territory
        for p in sorted(ph.live()):
            inf = ph.info.get(p, {})
            if inf.get("kind") != "anger" or not str(inf.get("anchor", "")).startswith("other:") or p in self.answered:
                continue
            who = inf["anchor"][len("other:"):]
            facts = a.facts_now()
            for o, (actor, left) in sorted(self.last_mover.items()):
                if actor != who or terr.rows.get(o, {}).get("holder") == "mine" or o not in self.world.gerund:
                    continue
                for s in a.states_seen(o):
                    if s in facts or s == f"{o}_{left.replace(' ', '_')}" or not a.makers(s):
                        continue
                    self.answered.add(p)
                    a.stack.append(a.goal)
                    a.goal, a.sub_since = s, a.mind.t
                    a.sub_log.append((a.mind.t, s, "set"))
                    self.pending_revenge = s
                    self.revenge.append((self.world.t, who, s, "set"))
                    self.beat("want", hole=f"own:control:{effect_parts(s, self.world.objs)[0]}",
                              obj=effect_parts(s, self.world.objs)[0], detail={"change": s, "revenge": who})
                    return


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=2000)
    ap.add_argument("--tempers", default="steady,steady,steady,steady")
    ap.add_argument("--grieve", default="1,1,1,1")
    ap.add_argument("--avenge", default="1,1,1,1")
    args = ap.parse_args()
    tempers = args.tempers.split(",")
    grieve = [g == "1" for g in args.grieve.split(",")]
    avenge = [g == "1" for g in args.avenge.split(",")]
    AVENGE.clear()
    AVENGE.update({p4.NAMES[k]: v for k, v in enumerate(avenge)})
    world, minds, shared = p4.run(tempers, args.ticks, subwants=False, kind=Avenging, world_cls=SealWorld,
                                  extra=[{"grievance": g} for g in grieve])
    rows, _, conserved = p4.measure(world, minds, shared)
    locks, end = p9.lock_measures(world, minds)
    feel = {m.name: p12.feelings(m, shared) for m in minds}
    met = sum(r["reached"] for r in rows)
    print(f"== retaliation (grieve {args.grieve}, avenge {args.avenge}): population {tempers}; wants met {met} of "
          f"{len(rows)}; slices {world.t}; conservation {'HOLDS' if conserved else 'BROKEN'}")
    at = {}
    for r, m, g, v in zip(rows, minds, grieve, avenge):
        k, f = locks[r["name"]], feel[r["name"]]
        sets = [(w, s) for _, w, s, h in m.revenge if h == "set"]
        done = Counter(h for _, _, _, h in m.revenge if h != "set")
        at[m.name] = Counter(w for w, _ in sets)
        print(f"{r['name']:5} {r['temper']:9} {'grieves' if g else 'concedes':8} {'avenges' if v else 'forgives':8} "
              f"reached {str(r['reached_at']) if r['reached'] else 'no':>5}; sealed others {k['shut_others']}; "
              f"anger at {f['anger_at'] or '-'}; retaliated at {dict(at[m.name]) or '-'} ({dict(done) or '-'})")
        for w, s in sets[:4]:
            print(f"      wanted {s} (against {w})")
    names = [m.name for m in minds]
    feuds_anger = sorted({tuple(sorted((x, y))) for x in names for y in names if x != y
                          and feel[x]["anger_at"].get(y) and feel[y]["anger_at"].get(x)})
    feuds_acts = sorted({tuple(sorted((x, y))) for x in names for y in names if x != y and at[x].get(y) and at[y].get(x)})
    print(f"   feuds (angry at each other): {feuds_anger or 'none'}; (retaliated against each other): {feuds_acts or 'none'}")
    print(f"   reached: {[(b.t, b.actor, b.obj) for b in shared if b.kind == 'reach']}")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    name = f"p13_{'-'.join(tempers)}_{args.grieve.replace(',', '')}_{args.avenge.replace(',', '')}.json"
    with open(os.path.join(HERE, "results", name), "w", encoding="utf-8") as fh:
        json.dump(dict(tempers=tempers, grieve=grieve, avenge=avenge, slices=world.t, conservation=conserved, minds=rows,
                       locks=locks, feelings=feel, revenge={m.name: m.revenge for m in minds}, feuds_anger=feuds_anger,
                       feuds_acts=feuds_acts, beats=[dataclasses.asdict(b) for b in shared]), fh, indent=1, default=str)


if __name__ == "__main__":
    main()
