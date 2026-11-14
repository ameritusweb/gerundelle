"""What differs between the mind's first game and its second (trace_first.py with luck held: game 1 lost 1 stone, games 2 and 3 lost 48
each). Per game: the mind's stones by the potential force of the placement and how many were later taken; whether a want was held when
it placed, and of what kind; whether the placement was one its want named (a point it wanted bearing); the turns it let pass; the
anti-want held; the top-level winners that were placements. Run: python -u -X utf8 trace_games.py [slices]"""
import collections
import sys

import run
from world import BLACK

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 650
a, w = run.build(0, 0.7)
read = 0
games = collections.defaultdict(lambda: dict(stones=[], held=collections.Counter(), passes=0, anti=collections.Counter(), offered=0,
                                             won=collections.Counter(), slices=0))
on_board, lost, where = set(), set(), {}
for t in range(N):
    g = games[len(w.games)]
    pots = w.potentials()
    a.mind.potentials = pots
    goal, stack, anti, passes = a.goal, list(a.stack), a.__dict__.get("anti"), w.passes
    turn_before = w.turn
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    g["slices"] += 1
    if pots:
        g["offered"] += 1
        top = rec["levels"][-1]["winners"] if rec.get("levels") else []
        g["won"]["a placement at the top" if any(i.split("|")[0] in pots for i in top) else "no placement at the top"] += 1
    if turn_before == BLACK and w.turn != BLACK and choice is None:
        g["passes"] += 1
    if choice is not None:
        want = "none" if goal is None else ("all" if goal.startswith("all:") else goal.rsplit("_", 1)[-1] + " on a " + run.kind(goal.rsplit("_", 1)[0]))
        named = goal == f"{choice[1]}_bearing" or f"{choice[1]}_bearing" in (goal or "")
        g["held"][(want, "the point it wanted bearing" if named else "another point")] += 1
        g["anti"]["held" if anti else "none"] += 1
        s = w.at.get(w.target(choice))
        g["stones"].append((s, pots.get(f"place_push:{choice[1]}_free")))
    now = {s for s, col in w.colour.items() if col == BLACK}
    on_board |= now
    lost |= {s for s in on_board if s not in w.colour and s not in w.kept}
for k in sorted(games):
    g = games[k]
    print(f"game {k + 1}: {g['slices']} slices; on offer in {g['offered']}; stones placed {len(g['stones'])}, later taken "
          f"{sum(1 for s, _ in g['stones'] if s in lost)}; turns let pass {g['passes']}")
    for f in (3.0, 2.0, 1.0):
        sub = [s for s, ff in g["stones"] if ff == f]
        if sub:
            print(f"    force {f:.0f}: {len(sub)} placed, {sum(1 for s in sub if s in lost)} later taken")
    print("    slices on offer:", dict(g["won"]))
    print("    the want held when it placed:", g["held"].most_common(8))
    print("    an anti-want when it placed:", dict(g["anti"]))
print("wants by game (set, met, dropped):")
bounds = [0] + [sum(x["slices"] for x in w.games[:i + 1]) for i in range(len(w.games))] + [10 ** 9]
for k in range(len(bounds) - 1):
    c = collections.Counter(kind for tt, _, kind in a.sub_log if bounds[k] <= tt < bounds[k + 1])
    print(f"    game {k + 1}: {dict(c)}")
