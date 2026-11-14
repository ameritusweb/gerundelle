"""Why a seed's games don't get better (the long runs: seed 1 had no game with fewer stones lost than the one before). Per game: stones
lost and how it ended; the points the anti-want threatens at the game's end (placements the SOV links to a held region doing what the
anti-want is on); and on the slices where only breath-filling placements were on offer: how many were on offer, how many threatened,
and whether each fill the mind made was a threatened one. Then the last such slices of each game.
Run: python -u -X utf8 trace_seed.py <seed> [slices]"""
import collections
import sys
import time

import run
from force_world import inv_id
from world import BLACK

sys.stdout.reconfigure(encoding="utf-8")
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
N = int(sys.argv[2]) if len(sys.argv) > 2 else 1100
a, w = run.build(seed, 0.7)
und, mind = a.mind.understanding, a.mind
read, t0 = 0, time.time()
rows = collections.defaultdict(list)
ends, threat_at_end, last_game = {}, {}, 0


def threatened_of(ids):
    targets = mind.__dict__.get("anti_targets") or set()
    told = mind.p.credulity
    return {c for c in ids if any(k in ("prevents", "causes") and o in targets and e[0] + e[2] + told * e[1] > 0
                                  for (k, o), e in und.rel.get(c, {}).items())}


inner = lambda board, i: i[0] == "place" and all(board.get(n) == BLACK for n in w.beside(w.target(i)))
for t in range(N):
    game = len(w.games)
    if game != last_game:
        last_game = game
    pots = w.potentials()
    mind.potentials = pots
    board = w.board()
    fills = {inv_id(i) for i in w.invitations() if inner(board, i)} if pots else set()
    passes, placed = w.passes, w.placed
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    if (t + 1) % 200 == 0:   # progress (first nothing was printed until the end)
        print(f"    slice {t + 1} ({time.time() - t0:.0f}s): games {len(w.games)}, lost by game {[x['white_took'] for x in w.games]}, luck {w.luck}, "
              f"regions {len(mind.territory.rows)}, anti-want {a.__dict__.get('anti')}", flush=True)
    if w.full and game not in ends:
        ends[game] = "both passed" if w.passes >= 2 else "the cap"
        known = [c for c in a.known if c.startswith("place_push:")]
        th_end = threatened_of(known)
        threat_at_end[game] = (f"{len(th_end)} of {len(known)} placements known, at {len({c.split(':')[1].split('_free')[0] for c in th_end})} points",
                               a.__dict__.get("anti"), len(mind.__dict__.get("anti_targets") or ()))
    places = {c for c in pots if c.startswith("place_push:")}
    if not places or len(fills) != len(places):
        continue
    th = threatened_of(fills)
    cid = inv_id(choice) if choice is not None else None
    lv = rec["levels"][-1]
    top = collections.Counter("threatened fill" if i.split("|")[0] in th else "fill" if i.split("|")[0] in fills else "pass" if i.startswith("pass_push") else i.split(":")[0] for i in lv["winners"])
    rows[game].append((t, len(fills), len(th), "nothing" if cid is None else "passed" if choice[0] == "pass" else "threatened fill" if cid in th else "fill", dict(top), a.__dict__.get("anti"),
                       a.goal if a.goal is None or len(a.goal) < 40 else a.goal[:40]))
for g in sorted(set(rows) | set(ends)):
    r = rows.get(g, [])
    game = w.games[g] if g < len(w.games) else None
    did = collections.Counter(x[3] for x in r)
    print(f"game {g + 1}: " + (f"lost {game['white_took']}, took {game['black_took']}, area {game['black_area']} to {game['white_area']}, ended by {ends.get(g)}; " if game else "unfinished; ")
          + f"threatened at its end: {threat_at_end.get(g, ('-',))[0]} (anti-want {threat_at_end.get(g, ('', None))[1]}, on {threat_at_end.get(g, ('', '', 0))[2]} targets)")
    if r:
        print(f"    slices with only breath-filling on offer {len(r)}: {dict(did)}; threatened among those on offer: "
              f"none in {sum(1 for x in r if x[2] == 0)}, some in {sum(1 for x in r if 0 < x[2] < x[1])}, all in {sum(1 for x in r if x[2] == x[1])}")
        for x in r[-9:]:
            print("       ", x)
anti = a.__dict__.get("anti_log", [])
print("anti-wants:", collections.Counter((r, k) for _, r, k in anti).most_common(6))
print("passes made:", sum(1 for i, _, _ in a.pushed if i[0] == "pass"), "of", len(a.pushed), "pushes")
print("cleanups (slice, regions stored, concepts stored):", a.__dict__.get("cleanup_log", [])[:4], "...", len(a.__dict__.get("cleanup_log", [])), "in all")

# the third part (the user: let the SOV generalize): what there is to generalize from, and whether Abstract has
told = mind.p.credulity
funded = lambda e: e[0] + e[2] + told * e[1]
by_sit = collections.defaultdict(lambda: [set(), set(), set()])
for c, rels in und.rel.items():
    if not c.startswith("place_push:"):
        continue
    pt, sit = c.split(":")[1].split("_free", 1)
    by_sit[sit][0].add(pt)
    for (r, o), e in rels.items():
        if r == "causes" and funded(e) > 0:
            if o.startswith("black_") and o.endswith("_coming_apart"):
                by_sit[sit][1].add(pt)
            if o == "potential:group+black_coming_apart":
                by_sit[sit][2].add(pt)
print("placements by what the stone meets: points known; points where it was followed by a stone of the mind's coming apart; points linked to the predicted effect 'a black group coming apart'")
for sit, (known, lost, pred) in sorted(by_sit.items(), key=lambda kv: -len(kv[1][1]))[:10]:
    print(f"    free{sit}: {len(known)}; {len(lost)}; {len(pred)}")
cabs = und.__dict__.get("concept_abstracts", [])
with_place = [x for x in cabs if any(str(v).startswith("place_push:") for m in x["members"] for v in m.values())]
print(f"concept abstracts {len(cabs)}, with a placement among their members {len(with_place)}; abstracts {len(und.abstracts)}, "
      f"with a placement {sum(1 for x in und.abstracts if any(str(v).startswith('place_push:') for m in x['members'] for v in m.values()))}")
for x in with_place[:4]:
    print("    ", x["id"], sorted(x["pattern"])[:4], "| centers:", sorted({m[x["center"]] for m in x["members"]})[:5], f"({len(x['members'])} members)")

# the colour's breath (black_breath, white_breath): what the mind has linked to its own breath hanging and coming apart
for eff in ("black_breath_hanging", "black_breath_coming_apart", "white_breath_hanging", "white_breath_coming_apart"):
    causes = [(c, funded(e)) for c, rels in und.rel.items() if c.startswith("place_push:") for (r, o), e in rels.items() if r == "causes" and o == eff and funded(e) > 0]
    by_doing = collections.Counter(c.rsplit("_", 1)[-1] for c, _ in causes)
    print(f"placements linked to {eff}: {len(causes)} ({dict(by_doing)} by what the stone would be doing), funded {sum(f for _, f in causes):.1f} in all, "
          f"at {len({c.split(':')[1].split('_free')[0] for c, _ in causes})} points")
for c in ("black_breath_hanging", "black_breath_coming_apart"):
    rels = sorted(((r, o, round(funded(e), 2)) for (r, o), e in und.rel.get(c, {}).items() if funded(e) >= 1.0 and not o.startswith("place_push:")), key=lambda x: -x[2])
    print(f"{c}: {len(und.rel.get(c, {}))} relations; funded 1 or more, not to placements: {rels[:8]}")
row = mind.territory.rows.get("black_breath", {})
print("black_breath in the register:", row.get("holder"), "| history", row.get("history", [])[-6:], "| moved by another", row.get("other"))
known = [c for c in a.known if c.startswith("place_push:")]
th = threatened_of(known)
print("placements threatened now, by what the stone would be doing:", dict(collections.Counter(c.rsplit("_", 1)[-1] for c in th)), "of known",
      dict(collections.Counter(c.rsplit("_", 1)[-1] for c in known)))
