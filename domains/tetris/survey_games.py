"""Why game 3 of clean5 was short (86 pieces, 3 rows; game 2: 263 pieces, 18 rows): the well and the mind at every 1,000-slice
checkpoint of games 2-4, read from the checkpoints (no replay): pieces placed this game, pieces cleared this game, holes (open cells
with a block above them), the stack's highest column and summed column heights, the root want and stack, the anti-want, and the wants
set since the checkpoint before. Run: python -u -X utf8 survey_games.py [from] [to]"""
import collections
import sys

import run  # noqa: F401  (puts Gerundelle and warpchess on the path)
import checkpoint

sys.stdout.reconfigure(encoding="utf-8")
lo, hi = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (14000, 28000)
prev_sub = 0
for s in range(lo, hi + 1, 1000):
    a, w, t = checkpoint.load(f"checkpoints/clean5_{s}.pkl")
    cols = collections.defaultdict(list)
    for x, y in w.settled:
        cols[x].append(y)
    holes = sum(sum(1 for y in range(min(ys) + 1, w.height) if (x, y) not in w.settled) for x, ys in cols.items())
    heights = [w.height - min(cols[x]) if cols[x] else 0 for x in range(w.width)]
    new = [x for x in a.sub_log if x[0] > s - 1000 and x[2] == "set"]
    kinds = collections.Counter(g.split("_")[0] if not g.startswith("potential:") else g.split("_")[0] for _, g, _ in new)
    print(f"slice {s}: game {len(w.games)}; pieces placed {w.placed}, cleared this game {w.__dict__.get('pieces_cleared')}; holes {holes}, "
          f"highest {max(heights)}, summed heights {sum(heights)}, cells {len(w.settled)}; goal {str(a.goal)[:45]}; stack {[str(x)[:30] for x in a.stack]}; "
          f"anti {a.__dict__.get('anti')}; wants set in the last 1000: {dict(kinds.most_common(6))}", flush=True)
