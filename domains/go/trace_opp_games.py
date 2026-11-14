"""Why the mind still loses ~48 stones in some games now that its territory is White's dead opportunity forces (opp_seed0.log, seed 0:
games 1, 2, 4 kept every stone and the whole board; games 3 and 5 lost 48 and 49). Replays the run from slice 0 (PYTHONHASHSEED=0, the
switches as run.py reads them) and, for every turn of the mind's, sorts what was on offer and what it did:
  held   a placement on a point whose opportunity the mind holds (dead, "mine"): filling its own territory
  inner  a placement on a free point with only its own stones or the edge beside it (its own breath), not held
  other  any other placement;  pass;  wait (on offer, nothing chosen).
Per game: the counts; how it ended; boards every 10 of the mind's stones (X black, O white, + an opportunity held, - one lost, . free);
the last turns before the loss in detail (on offer by kind, the choice, the anti-want, the want, the top level's winners by kind, what
the forces predicted for the choice, the register's event on the point it filled); and what the mind's SOV holds about placements on held
points. Run: PYTHONHASHSEED=0 python -u -X utf8 trace_opp_games.py [slices, default 1470]"""
import collections
import sys

import run
from world import BLACK, DEAD, WHITE, opportunity

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 1470
a, w = run.build(0, 0.7)
und, terr = a.mind.understanding, a.mind.territory
read = 0
G = collections.defaultdict(lambda: dict(turns=0, did=collections.Counter(), offer=collections.Counter(), only=collections.Counter(),
                                          log=[], boards=[], lost_regions=[], fills_held=[]))


def holder(c):
    return terr.rows.get(opportunity(c), {}).get("holder")


def kind_of(c, board):
    if holder(c) == "mine":
        return "held"
    if all(board.get(n) == BLACK for n in w.beside(c)):
        return "inner"
    return "other"


def picture():
    rows = []
    for y in range(w.size):
        s = ""
        for x in range(w.size):
            c = (x, y)
            if c in w.at:
                s += "X" if w.colour[w.at[c]] == BLACK else "O"
            else:
                h = holder(c)
                s += "+" if h == "mine" else "-" if h == "lost" else "."
        rows.append(s)
    return rows


def kinds_of(ids, offered):
    out = collections.Counter()
    for i in ids:
        base = i.split("|")[0]
        out[offered.get(base, "not a push")] += 1
    return dict(out)


shown_at = None
for t in range(N):
    game = len(w.games)
    g = G[game]
    a.mind.potentials = w.potentials()
    invs = w.invitations()
    board = w.board()
    offered = {}
    for inv in invs:
        iid = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
        offered[iid] = "pass" if inv[0] == "pass" else kind_of(w.target(inv), board)
    preds = w.push_predictions() if invs else []
    anti_before = a.__dict__.get("anti")
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    if not invs:
        continue
    g["turns"] += 1
    kinds = collections.Counter(offered.values())
    for k in kinds:
        g["offer"][k] += 1
    if set(kinds) <= {"held", "inner", "pass"}:
        g["only"]["no 'other' on offer"] += 1
    if choice is None:
        did = "wait"
    elif choice[0] == "commit":
        did = "commit"
    else:
        did = offered.get(f"{choice[0]}_push:{choice[1]}_{choice[2]}", "?")
    if a.__dict__.get("committed") and choice is not None and choice[0] != "commit":
        did += " (committed)"
    g["did"][did] += 1
    lv = rec["levels"][-1] if rec.get("levels") else None
    winners = kinds_of(lv["winners"], offered) if lv else {}
    pred = []
    if choice is not None and choice[0] == "place":
        iid = f"place_push:{choice[1]}_{choice[2]}"
        pred = sorted({rel for e, n, f, rel, ch in preds if ch == (iid,)})
        c = w.target(choice)
        if did.startswith("held"):
            g["fills_held"].append((t, c))
    g["log"].append((t, w.black_placed, dict(kinds), did, choice[1] if choice is not None and choice[0] != "pass" else (choice[0] if choice else None),
                     anti_before, a.goal, winners, pred, w.took[WHITE]))
    if w.black_placed % 10 == 0 and w.black_placed and (game, w.black_placed) != shown_at:
        shown_at = (game, w.black_placed)
        g["boards"].append((t, w.black_placed, w.took[BLACK], w.took[WHITE], picture()))

events = collections.defaultdict(list)   # the register's events on opportunity regions, by game (the history is kept on the row)
print("games:", [(i + 1, x["stones"], x["black_took"], x["white_took"], x["black_area"], x["white_area"]) for i, x in enumerate(w.games)])
for k in sorted(G):
    g = G[k]
    res = w.games[k] if k < len(w.games) else None
    print(f"\n=== game {k + 1}: " + (f"lost {res['white_took']}, took {res['black_took']}, {res['stones']} stones, area {res['black_area']}-{res['white_area']}" if res else "(unfinished)"))
    print(f"  the mind's turns {g['turns']}; turns with each kind on offer {dict(g['offer'])}; {dict(g['only'])}")
    print(f"  what it did: {dict(g['did'])}")
    print(f"  placements on held points (filling its own territory): {len(g['fills_held'])}: {[c for _, c in g['fills_held']][:30]}")
    for t, n, bt, wt, pic in g["boards"]:
        print(f"  slice {t}, the mind's stone {n}: taken by the mind {bt}, by the other {wt}")
        for row in pic:
            print("      " + row)
    loss_at = next((i for i, row in enumerate(g["log"]) if row[9] >= 10), None)
    tail = g["log"][max(0, (loss_at if loss_at is not None else len(g["log"])) - 14):(loss_at + 2 if loss_at is not None else len(g["log"]))]
    print("  turns before the big loss (slice, its stone, on offer by kind, did, push, anti-want held, want, top-level winners by kind, predicted for it, lost so far):")
    for row in tail:
        print("     ", row[0], row[1], row[2], row[3], row[4], "| anti", row[5], "| want", str(row[6])[:50], "| winners", row[7], "| pred", row[8], "| lost", row[9])

print("\nSOV: relations on placements whose name or effect concerns an opportunity being lost (a held point filled reads 'bearing'):")
rel = collections.Counter()
for c, rels in und.rel.items():
    for (r, o), e in rels.items():
        if o.startswith("opportunity_") or o.startswith("potential:opportunity"):
            rel[(c.split(":")[0], r, o.rsplit("_", 1)[-1] if o.startswith("opportunity_") else o)] += 1
for row, n in rel.most_common(20):
    print("   ", row, n)
print("anti-wants:", collections.Counter(k for _, _, k in a.__dict__.get("anti_log", [])).most_common(),
      "| on opportunity regions:", collections.Counter(k for _, r, k in a.__dict__.get("anti_log", []) if "opportunity" in str(r)).most_common(),
      "| examples:", [x for x in a.__dict__.get("anti_log", []) if "opportunity" in str(x[1])][:6])
print("opportunity regions by holder now:", collections.Counter(row["holder"] for r, row in terr.rows.items() if r.startswith("opportunity_")))
print("commits:", a.__dict__.get("commit_log", []))
