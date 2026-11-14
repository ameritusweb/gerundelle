"""Probe: is rung 4 making progress? One run, a line every 10 rounds, a stack dump every 120 s."""
import faulthandler
import sys
import time

import rung4
from gameworld import GameWorld, RandomSide

faulthandler.dump_traceback_later(120, repeat=True, file=sys.stderr)
mind = rung4.learned(0, 1000)
print("learned", time.strftime("%H:%M:%S"), flush=True)
w = GameWorld(seed=0)
w.actor = "White"
white = rung4.Player(w, "game", mind=mind)
black = RandomSide(w, 0)
t0 = time.time()
for r in range(2000):
    t = time.time()
    if w.board.turn == 1:
        w.actor = "White"
        for _ in range(rung4.TURN_STEPS):
            if white.goal is None:
                white.goal = rung4.GOAL
            n = len([x for x in w.log if x[2]])
            white.tick()
            if len([x for x in w.log if x[2]]) > n:
                break
    else:
        black.tick()
        w.actor = "White"
        white.tick()
    dt = time.time() - t
    if r % 10 == 0 or dt > 30:
        print(f"round {r} took {dt:.1f}s, total {time.time() - t0:.0f}s, games {len(w.games)}, moved {w.moved}, known pushes {len(white.known)}, lived {len(white.pushed)}", flush=True)
