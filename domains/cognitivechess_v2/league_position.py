"""The current (or final) position of a league game, replayed from its log's moves, drawn as a PNG.
python -X utf8 league_position.py <tag> [out.png]   (tag: the log's name, e.g. r0_k1_accepting_vs_grieving)"""
import re
import subprocess
import sys

import chess

HERE = __import__("paths").domain('cognitivechess_v2')
tag = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else f"{HERE}/{tag}.png"
b = chess.Board()
last = None
for line in open(f"{HERE}/league/logs/{tag}.log", encoding="utf-8"):
    if "game over" in line:   # (moves after the game's end belong to the next game)
        break
    m = re.search(r"(White|Black)\s+[\d.]+s: .*?moved \d+ ([a-h][1-8][a-h][1-8][qrbn]?)", line)
    if m:
        last = m.group(2)
        b.push_uci(last)
print("half-moves", len(b.move_stack), "| FEN", b.fen())
print(b.unicode(borders=True, empty_square="·"))
title = f"{tag.split('_', 2)[2].replace('_vs_', ' (W) vs ').replace('_', ' ')} (B): half-move {len(b.move_stack)}"
subprocess.run([sys.executable, "-X", "utf8", f"{HERE}/board_png.py", b.fen(), out, title] + ([last] if last else []), check=True)
