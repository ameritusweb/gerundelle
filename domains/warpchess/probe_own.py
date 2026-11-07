"""Probe Params.own_wants in a full game: sub-wants set from ownership slots, what they were, met or dropped, and the register."""
import collections
import sys

import rung4
from gameworld import RandomSide

sys.stdout.reconfigure(encoding="utf-8")
NOGOAL = "nogoal" in sys.argv
SEED, ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 1, int(sys.argv[2]) if len(sys.argv) > 2 else 600
mind = rung4.learned(SEED, 1000, True)
import gameworld
from imagine import Imagines
IMAGINE = "imagine" in sys.argv


class ImaginingGame(Imagines, gameworld.GameWorld):
    pass


w = (ImaginingGame if IMAGINE else gameworld.GameWorld)(seed=SEED)
w.owned = True
w.actor = "White"
white = rung4.Player(w, "game", mind=mind)
rung4.switch(white.mind, True)
white.mind.p.own_wants = True
for k in ("subwants", "sub_yield"):   # Gerundelle's sub-wants (README), and sub_yield: a trace showed its problem here (5 of 8 sub-wants came about and weren't counted met)
    setattr(white.mind.p, k, True)
white.mind.p.imagine = IMAGINE
terr = white.mind.territory
terr.given = w.white_pieces()
for r in terr.given:
    terr.row(r)
terr.update(terr.given)
black = RandomSide(w, SEED)
subs, prev = [], None
for r in range(ROUNDS):
    if w.board.turn == 1:
        w.actor = "White"
        for _ in range(rung4.TURN_STEPS):
            if white.goal is None and not NOGOAL:   # nogoal: no want placed; wants arise from the ownership slots
                white.goal = rung4.GOAL
            n = len([x for x in w.log if x[2]])
            white.tick()
            if len([x for x in w.log if x[2]]) > n:
                break
    else:
        black.tick()
        w.actor = "White"
        white.tick()
    cur = (white.goal, tuple(white.stack))
    if cur != prev:
        subs.append((white.mind.t, white.goal, len(white.stack)))
        prev = cur
    if r % 100 == 0 and r:
        print(f"round {r}: games {len(w.games)} {[g[:2] for g in w.games][-4:]}, wants met {len(white.reached)}, goal {white.goal}, stack {white.stack}", flush=True)
print("goal changes (slice, goal, stack depth):", subs[:30])
print("sub-wants set:", collections.Counter(g for _, g, d in subs if d > 0).most_common(10))
print("reached:", collections.Counter(g for _, g in white.reached).most_common(10))
print("dropped (failed):", sorted(white.failed_subs)[:10])
hold = collections.Counter((("given" if r in terr.given else "other"), row.get("holder")) for r, row in terr.rows.items())
print("register:", sorted(hold.items(), key=str))
