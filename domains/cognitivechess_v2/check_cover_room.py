"""The walk-in room (PLAN.md, coverage, expectations E1-E3 written before the run). 6rk/6pp/8/8/8/5Q2/2n5/R5K1 w: Black's knight on c2
attacks White's rook on a1; White's queen on f3 can't take the knight; some White moves walk into a fork (the queen to a square the
knight attacks, with the rook still attacked): which ones, the covers-on world's own reading says (sets a move on offer would uncover).
Black's king is boxed in by its rook and pawns: White has no check. Fresh minds (rung 4p's switches, v2's want-dreams), one per seed,
covers on and off; each mind looks at the room once (give) and then has slices until it moves.
  E1 (covers on): at the mind's first slice the fork sets are held regions, and each walk-in move's prediction of its set is a loss.
  E2: walk-in moves chosen less often with covers on than off.
(First the room had the queen on d2 guarding c2: every mind, both arms, took the knight in its first slice, so nothing was tested; and
E1 was then counted met with no slice to read, an empty all(): fixed.)
python -u -X utf8 check_cover_room.py [seeds]"""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
import mate_oracle
import rung4p
from chessduel import configure
from plansworld import COVER, give, read_mate_passed

FEN = "6rk/6pp/8/8/8/5Q2/2n5/R5K1 w - - 0 1"
seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 10
chosen = {True: Counter(), False: Counter()}
e1 = []
walk = None
for on in (True, False):
    for seed in range(seeds):
        w, a = rung4p.build(seed, FEN, dreams=True, half_moves=4)
        configure(a)
        w.covers_read = on
        w.shown = w.read()
        if on and walk is None:   # the walk-in moves, by the world's reading: the sets each move on offer would uncover
            sets = {o for o, s in w.shown.items() if o.startswith(COVER)}
            preds = [p for p in w.push_predictions() if p[0].startswith(COVER) and p[0].endswith("_uncovered")]
            walk = {}
            for p in preds:
                walk.setdefault(p[4][0].split("_push")[0].split(" ", 1)[1], set()).add(p[0].rsplit("_", 1)[0])
            print(f"sets named on reading the room: {len(sets)}; walk-in moves: {sorted(walk)}", flush=True)
            w.shown = w.read()
        give(a, w)   # (the mind looks at the room once before its first slice: its territory as the room stands)
        move, t = None, 0
        for t in range(40):
            moved0 = w.moved
            choice, _ = a.tick()
            read_mate_passed(a, choice)
            if on and t == 0:   # E1, at the first slice
                rows = a.mind.territory.rows
                want_sets = set().union(*walk.values()) if walk else set()
                held = {s for s in want_sets if rows.get(s, {}).get("holder") == "mine"}
                losses = {ins["effect"].rsplit("_", 1)[0] for ins in a.__dict__.get("predicted", {}).values()
                          if ins["effect"].startswith(COVER) and ins.get("loss")}
                e1.append((seed, len(want_sets), held, losses & want_sets))
            give(a, w)
            if w.moved > moved0:
                move = next(x[1] for x in reversed(w.log) if x[2]).split(" ", 1)[1]
                break
        chosen[on][move] += 1
        print(f"covers {'on ' if on else 'off'} seed {seed}: moved {move} after {t + 1} slices"
              f"{' (walks into a fork)' if walk and move in walk else ''}", flush=True)
print()
for seed, n, held, losses in e1:
    print(f"E1 seed {seed}: fork sets held {len(held)}/{n}, their walk-ins predicted as losses {len(losses)}/{n}")
e1_ok = bool(e1) and all(n > 0 and len(h) == n and len(l) == n for _, n, h, l in e1)
walk_off, walk_on = (sum(chosen[x][m] for m in (walk or {})) for x in (False, True))
print(f"E1: {'met' if e1_ok else 'NOT met'}")
print(f"E2: walk-in moves chosen, covers off {walk_off}/{seeds}, on {walk_on}/{seeds}: {'met' if walk_on < walk_off else 'NOT met'}")
print("moves, off:", dict(chosen[False]), "| on:", dict(chosen[True]))
mate_oracle.close()
