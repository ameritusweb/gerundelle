"""The time coverage adds to a slice's readings (read and push_predictions) on positions from a league game, off and on."""
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
import chess

import rung0  # noqa: F401
from plansgame import PlansGame
from plansworld import COVER

tag = sys.argv[1] if len(sys.argv) > 1 else "r0_k1_steady_vs_impatient"
b = chess.Board()
fens = []
for line in open(f"league/logs/{tag}.log", encoding="utf-8"):
    if "game over" in line:
        break
    m = re.search(r"(?:White|Black)\s+[\d.]+s: .*?moved \d+ ([a-h][1-8][a-h][1-8][qrbn]?)", line)
    if m:
        b.push_uci(m.group(1))
        if b.turn and 10 <= len(b.move_stack) <= 80 and len(b.move_stack) % 10 == 0:
            fens.append(b.fen())
for on in (False, True):
    t, sets = 0.0, 0
    for fen in fens:
        w = PlansGame(seed=0, fen=fen)
        w.covers_read = on
        t0 = time.time()
        r = w.read()
        w.shown = r
        w.push_predictions()
        t += time.time() - t0
        sets += sum(1 for o, s in r.items() if o.startswith(COVER) and s == "uncovered")
    print(f"covers {'on ' if on else 'off'}: {len(fens)} positions, {t / len(fens):.2f}s each (read + predictions); uncovered sets {sets}")
