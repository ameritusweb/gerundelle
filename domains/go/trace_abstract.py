"""Why Abstract doesn't generalize "a placement on a point I hold makes it bearing" (trace_aversion.py: the anti-want held_bearing
pushes down only the exact placements already linked to a held point bearing; the mind fills with unlinked ones). Params.concept_abstracts
(Understanding.analogize_concepts) compares concepts' own structures; analogize_all compares whole structures (components).
Replays seed 0 to the slice given, wrapping analogize_concepts to record, at each call, what it had to work with:
  - placements linked "causes opportunity_<p>_bearing" (funded) at all, and how many of them are attended (sov:<c> in the pool: the
    only concepts analogize_concepts reads);
  - of those, how many have a core (the relations around them cut to the best-funded, CORE 12) still holding the bearing link;
  - the concept abstracts formed and what their centers are;
then at the end: the whole-structure components (is everything one component?), the abstracts holding placements, the expectations
written on placements, and one fill placement's relations and core in full.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_abstract.py [slice, default 760]"""
import collections
import sys

import run
from molecules import Understanding

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 760
a, w = run.build(0, 0.7)
und, mind = a.mind.understanding, a.mind
told = mind.p.credulity
OWN = ("subwant:", "all:", "own:", "q:", "exp:", "meta:", "phase:", "sov:")
calls = []
DETAIL = []


def bearing_links(c):
    return [o for (r, o), e in und.rel.get(c, {}).items() if r == "causes" and o.startswith("opportunity_") and o.endswith("_bearing")
            and e[0] + e[2] + 0.5 * e[1] >= 1.0]


orig = Understanding.analogize_concepts


def wrapped(self, rec):
    if self is und and mind.t - self.__dict__.get("concepts_analogized_at", -99) >= 10:
        linked = [c for c in und.rel if c.startswith("place_push:") and bearing_links(c)]
        attended = [c for c in linked if f"sov:{c}" in mind.pool]
        edges = {e for e in (self.__dict__.get("_edges_now") or self.edges()) if not e[1].startswith(OWN) and not e[2].startswith(OWN)}
        by = collections.defaultdict(set)
        for e in edges:
            by[e[1]].add(e)
            by[e[2]].add(e)
        held_ix = self.__dict__.get("_funding_ix")
        if held_ix is None:
            self._funding_ix = self.funding_index()
        with_core = [c for c in attended if any(r == "causes" and x.endswith("_bearing") for r, _, x in self.core(by[c]))]
        if held_ix is None:
            self._funding_ix = None
        detail = []
        for c in sorted(i[4:] for i in mind.pool if i.startswith("sov:place_push:")):
            if held_ix is None:
                self._funding_ix = self.funding_index()
            core = self.core(by[c]) if len(by.get(c, ())) >= 2 else frozenset()
            if held_ix is None:
                self._funding_ix = None
            reach_op = sorted(x for r, p, x in core if r == "reaches" and x.startswith("opportunity_"))
            bearing = sorted(x for r, p, x in core if r == "causes" and x.startswith("opportunity_") and x.endswith("_bearing"))
            detail.append((c.split(":", 1)[1][:40], len(by.get(c, ())), len(core), reach_op, bearing))
        DETAIL.append((mind.t, detail))
        n_before = len(self.__dict__.get("concept_abstracts", []))
        orig(self, rec)
        new = self.__dict__.get("concept_abstracts", [])[n_before:]
        calls.append((mind.t, len(linked), len(attended), len(with_core),
                      sum(1 for i in mind.pool if i.startswith("sov:")), [(x["id"], x["members"][0][x["center"]], len(x["pattern"])) for x in new]))
        return
    return orig(self, rec)


Understanding.analogize_concepts = wrapped
read = 0
for t in range(N):
    a.mind.potentials = w.potentials()
    a.tick()
    read, _ = run.give(a, w, read)

print(f"analogize_concepts calls: {len(calls)}")
print("  (slice, placements linked to a held point bearing, of them attended, of those with the link in their core, SOV molecules in "
      "the pool, concept abstracts formed this call)")
for row in calls[::max(1, len(calls) // 25)]:
    print("   ", row)
print("  most attended at once:", max((c[2] for c in calls), default=0), "| most with the link in the core:", max((c[3] for c in calls), default=0))
cabs = und.__dict__.get("concept_abstracts", [])
print(f"\nconcept abstracts: {len(cabs)}; their centers by kind:",
      collections.Counter(x["members"][0][x["center"]].split(":")[0].split("_")[0] for x in cabs))
for x in cabs[:12]:
    m0 = x["members"][0]
    print(f"   {x['id']} center {m0[x['center']][:60]}; {len(x['members'])} members; pattern {sorted(x['pattern'])[:6]}; "
          f"roles {sorted((r, v[:40]) for r, v in m0.items())[:6]}")
edges = und.edges()
comps = und.components(edges)
print(f"\nwhole structures: {len(edges)} edges in {len(comps)} components; largest {max((len(g) for g, _ in comps), default=0)} nodes")
abs_ = und.abstracts
print(f"abstracts (whole structures): {len(abs_)}; holding a placement: {sum(1 for x in abs_ if any(v.startswith('place_push:') for m in x['members'] for v in m.values()))}")
exp = [(k, v) for k, v in und.expect.items() if str(k[0]).startswith("place_push:")]
print(f"expectations on placements: {len(exp)}", exp[:6])
fills = [c for c in und.rel if c.startswith("place_push:") and bearing_links(c)]
print(f"\nplacements linked (funded >= 1) to a held point bearing: {len(fills)}")
if fills:
    c = sorted(fills)[0]
    print(f"one of them, {c}:")
    for (r, o), e in sorted(und.rel[c].items(), key=lambda kv: -(kv[1][0] + kv[1][2] + 0.5 * kv[1][1]))[:16]:
        print(f"    {r} {o} {[round(x, 2) for x in e]}")
    by = [e for e in edges if c in (e[1], e[2])]
    und._funding_ix = und.funding_index()
    print(f"  its edges as Abstract sees them: {len(by)}; its core: {sorted(und.core(set(by)))}")
    und._funding_ix = None
told = [x for x in und.log if x[1] == "transfer told"]
print(f"\ntransfer told (Params.transfer_tells): {len(told)}", told[:10])
reach = sum(1 for c, rels in und.rel.items() for (r, o) in rels if r == "reaches")
print(f"reaches relations: {reach}; placements reaching an opportunity: {sum(1 for c, rels in und.rel.items() if c.startswith('place_push:') and any(r == 'reaches' and o.startswith('opportunity_') for (r, o) in rels))}")
print("concept abstracts with a reaches link:", [(x["id"], x["members"][0][x["center"]][:50], sorted(x["pattern"]), len(x["members"])) for x in cabs if any(r == "reaches" for r, _, _ in x["pattern"])][:6])

print()
print("attended placements at each Abstract pass (slice: [(placement, its links, its core's links, core reaches an opportunity, core causes an opportunity bearing)]):")
for t, d in DETAIL:
    if d:
        print("   ", t, d[:4])
log = [x for x in und.log if x[1] in ("concept analogy", "joined")]
print("concept analogies and joins:", log[:12])
