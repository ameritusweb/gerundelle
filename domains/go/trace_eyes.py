"""Whether the mind stopped filling its own breath in game 2 (trace_boards.py with the watch at 6: game 1 lost 49 stones, game 2 lost 3
and ended with two separate free points), or the game ended first. A placement into its own breath: a free point with only the mind's
stones or the edge beside it. Per game: the turns one was on offer, the turns the mind placed one, the turns it placed elsewhere or
let pass; how the game ended; and what the mind holds about such placements: the relations its SOV has from a placement to one of its
own stones coming apart, the anti-wants held, and the bids of breath-filling placements against the others at the top level.
Run: python -u -X utf8 trace_eyes.py [slices]"""
import collections
import sys

import run
from world import BLACK, WHITE

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 760
a, w = run.build(0, 0.7)
und = a.mind.understanding
read = 0
G = collections.defaultdict(lambda: dict(offer=0, filled=0, elsewhere=0, waited=0, only=0, only_filled=0, bids=[], anti=0, turns=0, last=[]))
ends = []


def inner(board, c):
    return all(board.get(n) == BLACK for n in w.beside(c))


for t in range(N):
    g = G[len(w.games)]
    pots = w.potentials()
    a.mind.potentials = pots
    board = w.board()
    fills = {f"place_push:point_{c[0]}_{c[1]}_free" for c in w.legal(BLACK) if inner(board, c)} if pots else set()
    state = (w.passes, w.placed, len(w.games))
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    if len(w.games) != state[2] or w.full:
        if not ends or ends[-1][0] != len(w.games) + (1 if w.full else 0):
            ends.append((len(w.games) + (1 if w.full else 0), t, "both passed" if w.passes >= 2 else f"{w.placed} stones placed (the cap)"))
    if not pots:
        continue
    g["turns"] += 1
    g["anti"] += bool(a.__dict__.get("anti"))
    if fills:
        g["offer"] += 1
        only = len(fills) == len(pots)
        g["only"] += only
        cid = f"place_push:{choice[1]}_free" if choice is not None else None
        if cid in fills:
            g["filled"] += 1
            g["only_filled"] += only
        elif choice is not None:
            g["elsewhere"] += 1
        else:
            g["waited"] += 1
        lv = rec["levels"][-1] if rec.get("levels") else None
        if lv:
            bid = lambda ids: [round(v, 2) for i, v in lv["bids"].items() if i.split("|")[0] in ids]
            fb, ob = bid(fills), bid(set(pots) - fills)
            if fb:
                g["bids"].append((max(fb), max(ob) if ob else None, sum(1 for i in lv["winners"] if i.split("|")[0] in fills),
                                  sum(1 for i in lv["winners"] if i.split("|")[0] in set(pots) - fills)))
        g["last"].append((t, len(fills), len(pots), "filled" if cid in fills else "elsewhere" if choice is not None else "waited", a.goal))
for k in sorted(G):
    g = G[k]
    print(f"game {k + 1}: the mind's turns {g['turns']}; a breath-filling placement on offer in {g['offer']} (the only kind on offer in {g['only']}): "
          f"it filled in {g['filled']} ({g['only_filled']} when nothing else was on offer), placed elsewhere in {g['elsewhere']}, placed nothing in {g['waited']}; "
          f"turns with an anti-want held {g['anti']}")
    if g["bids"]:
        n = len(g["bids"])
        both = [(f, o) for f, o, _, _ in g["bids"] if o is not None]
        print(f"    top-level bids on those turns: best breath-filling {sum(f for f, *_ in g['bids']) / n:.2f} on average"
              + (f"; with another kind also on offer ({len(both)} turns): breath-filling {sum(f for f, _ in both) / len(both):.2f}, the other {sum(o for _, o in both) / len(both):.2f}" if both else "")
              + f"; breath-filling placements among the top winners {sum(x[2] for x in g['bids'])}, others {sum(x[3] for x in g['bids'])}")
    print("    its last turns with one on offer (slice, breath-filling on offer, all on offer, what it did, want held):")
    for row in g["last"][-8:]:
        print("       ", row[:4], str(row[4])[:60])
print("how the games ended:", ends)
print("games:", [(x["stones"], x["black_took"], x["white_took"], x["black_area"], x["white_area"], x["slices"]) for x in w.games])
own_loss = [(c, o, [round(x, 2) for x in e]) for c, rels in und.rel.items() if c.startswith("place_push:")
            for (r, o), e in rels.items() if r in ("causes", "prevents") and o.startswith("black_") and o.endswith("_coming_apart")]
print(f"SOV relations from a placement to one of the mind's own stones coming apart: {len(own_loss)}")
for row in own_loss[:6]:
    print("   ", row)
anti = a.__dict__.get("anti_log", [])
print("anti-wants:", collections.Counter(k for _, _, k in anti).most_common(), "| held now:", a.__dict__.get("anti"))
held = collections.Counter()
last = {}
for tt, r, k in anti:
    if k == "set":
        last[r] = tt
    elif r in last:
        held[min(tt - last[r], 5)] += 1
print("    slices an anti-want was held before it was dropped (5 = five or more):", dict(held))
