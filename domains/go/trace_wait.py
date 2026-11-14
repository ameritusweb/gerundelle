"""Why the mind placed nothing for six slices at the end of game 3 (trace_eyes.py on the relative anti-wants: games 1 and 2 lost 49
and 48 stones, game 3 lost none and ended with both passing), where in games 1 and 2 it waited one or two slices and then filled. On
each slice where only breath-filling placements were on offer: what it did; the anti-want held and how many of the placements on offer
it threatens (the SOV links them to one of its targets); the top-level bids of the threatened and the other placements; what won the top
level; the mind's energy. The last 14 such slices of each game. Run: python -u -X utf8 trace_wait.py [slices]"""
import collections
import sys

import run
from world import BLACK

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 920
a, w = run.build(0, 0.7)
und, mind = a.mind.understanding, a.mind
read = 0
rows = collections.defaultdict(list)
for t in range(N):
    game = len(w.games)
    pots = w.potentials()
    mind.potentials = pots
    board = w.board()
    fills = {f"place_push:point_{c[0]}_{c[1]}_free" for c in w.legal(BLACK) if all(board.get(n) == BLACK for n in w.beside(c))} if pots else set()
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    if not pots or len(fills) != len(pots):
        continue
    targets = mind.__dict__.get("anti_targets") or set()
    told = mind.p.credulity
    threatened = {c for c in fills if any(k in ("prevents", "causes") and o in targets and e[0] + e[2] + told * e[1] > 0
                                          for (k, o), e in und.rel.get(c, {}).items())}
    lv = rec["levels"][-1]
    bids = {i.split("|")[0]: v for i, v in lv["bids"].items() if i.split("|")[0] in fills}
    top = collections.Counter("threatened fill" if i.split("|")[0] in threatened else "fill" if i.split("|")[0] in fills else i.split(":")[0]
                              for i in lv["winners"])
    best = lambda ids: round(max((bids[i] for i in ids if i in bids), default=float("nan")), 2)
    rows[game].append((t, "filled" if choice is not None else "nothing", len(fills), len(threatened), best(threatened), best(fills - threatened),
                       dict(top), round(getattr(mind, "energy", 1.0), 2), a.__dict__.get("anti"), a.quiet))
for g in sorted(rows):
    r = rows[g]
    print(f"game {g + 1}: {len(r)} slices with only breath-filling on offer; filled in {sum(1 for x in r if x[1] == 'filled')}; "
          f"with an anti-want held {sum(1 for x in r if x[8])}; with a threatened placement on offer {sum(1 for x in r if x[3])}")
    print("    slice, did, on offer, threatened, best bid threatened, best bid other, top-level winners, energy, anti-want, slices quiet")
    for x in r[-14:]:
        print("   ", x)
