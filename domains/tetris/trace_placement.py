"""Where pieces go, with and without the stuck want: replay a window of clean5 from a checkpoint (nothing saved) and record, for each piece
as it comes to rest, its shape, whether its landing makes a clear (world.coming_apart / clearing in the resting slice), the well after it
(holes: open cells with a block above them in the column; the stack's highest column and summed column heights), the pushes and waits made
while it fell, and the wants held. --drop-goal: the held root want and its stack are taken out at the start (a counterfactual, for
comparison only). python -u -X utf8 trace_placement.py checkpoints/clean5_<slice>.pkl <slices> [--drop-goal]"""
import collections
import sys

import checkpoint
import run

sys.stdout.reconfigure(encoding="utf-8")
a, w, start = checkpoint.load(sys.argv[1])
for k, v in run.SWITCHES.items():
    setattr(a.mind.p, k, v)
N = int(sys.argv[2])
if "--drop-goal" in sys.argv:
    print(f"counterfactual: dropping goal {a.goal} and stack {a.stack}", flush=True)
    for g in [a.goal, *a.stack]:
        a.mind.pool.pop(g, None)
    a.goal, a.stack = None, []


def well():
    cols = collections.defaultdict(list)
    for x, y in w.settled:
        cols[x].append(y)
    holes = sum(sum(1 for y in range(min(ys) + 1, w.height) if (x, y) not in w.settled) for x, ys in cols.items())
    heights = [w.height - min(cols[x]) if cols[x] else 0 for x in range(w.width)]
    return holes, max(heights), sum(heights)


pieces, cur = [], None
placed, games = w.placed, len(w.games)
npushed = len(a.pushed)
def fresh():
    return dict(start=a.mind.t, shape=w.piece[0] if w.piece else None, pushes=collections.Counter(), waits=0, wants=collections.Counter())
cur = fresh()
for t in range(start, N):
    a.mind.potentials = w.potentials()
    if cur["shape"] is None and w.piece:
        cur["shape"] = w.piece[0]
    choice, rec = a.tick()
    run.after_tick(a, w)
    for inv, _, _ in a.pushed[npushed:]:
        cur["pushes"][inv[0]] += 1
    npushed = len(a.pushed)
    if choice is None and not a.watching:
        cur["waits"] += 1
    for g in (a.goal, *a.stack):
        if g:
            cur["wants"][g.split("&")[0][:40]] += 1
    if len(w.games) != games:   # the well was set back: a game ended
        pieces.append(dict(cur, end="GAME OVER"))
        games, placed = len(w.games), w.placed
        cur = fresh()
        continue
    if w.placed != placed:   # the piece came to rest in this slice: its clear (if any) is decided now, and executes next slice
        holes, top, total = well()
        cur.update(clears=bool(w.coming_apart or w.clearing), holes=holes, top=top, total=total, slices=a.mind.t - cur["start"])
        pieces.append(cur)
        placed = w.placed
        cur = fresh()
    if (t + 1) % 200 == 0:
        print(f"slice {t + 1}: pieces {len(pieces)}, clears {sum(1 for p in pieces if p.get('clears'))}, goal {a.goal}", flush=True)

rest = [p for p in pieces if "holes" in p]
print(f"\nwindow {start}..{N}: {len(rest)} pieces at rest, {sum(p['clears'] for p in rest)} made a clear; game overs {sum(1 for p in pieces if p.get('end'))}")
if rest:
    print(f"holes: first {rest[0]['holes']}, last {rest[-1]['holes']}; top: first {rest[0]['top']}, last {rest[-1]['top']}; summed heights: first {rest[0]['total']}, last {rest[-1]['total']}")
print("shapes:", "".join(str(p["shape"])[0] for p in pieces))
print("pushes made:", sum((p["pushes"] for p in pieces), collections.Counter()), "| waits:", sum(p["waits"] for p in pieces))
print("wants held (slices):", sum((p["wants"] for p in pieces), collections.Counter()).most_common(8))
print("goal at the end:", a.goal, "| stack:", a.stack)
print("sub_log in the window:", [e for e in a.sub_log if start < e[0] <= N])
print("\nper piece: start, shape, slices, pushes, waits, clears, holes, top, summed heights, main want")
for p in pieces:
    if "holes" not in p:
        print(f"  {p['start']:6d} {p.get('end')}")
        continue
    print(f"  {p['start']:6d} {str(p['shape']):3s} {p['slices']:3d} {dict(p['pushes'])} waits {p['waits']:3d} {'CLEAR' if p['clears'] else '     '} "
          f"holes {p['holes']:3d} top {p['top']:2d} sum {p['total']:3d} {p['wants'].most_common(1)}")
