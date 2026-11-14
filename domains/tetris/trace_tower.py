"""Debug the tower (the user, 2026-11-11: "it somehow is trying to create the tallest tower"): from the repaired checkpoint at luck 0, the
well set back as watch_mind does, each slice where pushes are on offer and the mind isn't watching a push: did it push or wait, and when it
waited, what held the top of its tournament; which pushes it chose; and the column each piece came to rest in.
Run: python -u -X utf8 trace_tower.py [slices]"""
import collections
import sys

N = int(sys.argv[1]) if len(sys.argv) > 1 else 250
sys.argv = sys.argv[:1]   # (watch_mind reads its own arguments on import)
sys.path.insert(0, ".")
import checkpoint  # noqa: E402
import run  # noqa: E402
import watch_mind as wm  # noqa: E402

a, w, t = checkpoint.load("checkpoints/decisions_18000_repaired.pkl")
wm.amnesia(a, w)
choices, wait_tops, rest_cols, top_kinds = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
examples = []
for k in range(N):
    offers = w.invitations()
    watching = bool(a.watching)
    piece, doing = w.piece, w.doing
    a.mind.potentials = w.potentials()
    choice, rec = a.tick()
    run.earn_luck(a, w)
    run.own_clears(a, w)
    run.own_open_rows(a, w)
    t += 1
    if piece is not None and doing == "resting" and w.doing != "resting":   # it settled this slice
        rest_cols[min(c[0] for c in w.parts(piece) or [(0, 0)])] += 1
    if offers and not watching:
        top = rec["levels"][-1]["winners"]
        pushes_top = [i for i in top if "_push:" in i]
        if choice is not None:
            choices[choice[0]] += 1
        else:
            choices["wait"] += 1
            wait_tops["a push held the top" if pushes_top else "no push held the top"] += 1
            for i in top:
                top_kinds[i.split(":")[0] if ":" in i else i.split("_")[0]] += 1
            if len(examples) < 4:
                bids = rec["levels"][-1]["bids"]
                examples.append((t, [(i[:45], round(bids.get(i, 0), 2)) for i in top][:8], a.goal))
print(f"slices with pushes on offer, not watching: {sum(choices.values())}; chosen: {dict(choices)}")
print("when it waited:", dict(wait_tops), "| what held the top then:", top_kinds.most_common(8))
for ex in examples:
    print("  example wait at", ex[0], "top:", ex[1], "| want:", ex[2])
print("pieces came to rest by leftmost column:", sorted(rest_cols.items()))
terr = a.mind.territory
print("territory:", {k: dict(collections.Counter(row["holder"] for r, row in terr.rows.items() if r.startswith(k))) for k in ("row_", "cell_", "block_", "potential_")}, "| cleared and the mind's for good:", sum(1 for r, row in terr.rows.items() if row.get("cleared")))
print("wants set:", collections.Counter(g for _, g, kk in a.sub_log if kk == "set").most_common(6), "| want now:", a.goal)
print("games", len(w.games), "| blocks now", len(w.settled), "| pieces cleared", w.pieces_cleared, "rows", w.lines)
