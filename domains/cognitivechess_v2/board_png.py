"""A chess position as a PNG. python -X utf8 board_png.py "<FEN>" out.png [title] [last-move uci]"""
import sys

import chess
from PIL import Image, ImageDraw, ImageFont

fen, out = sys.argv[1], sys.argv[2]
title = sys.argv[3] if len(sys.argv) > 3 else ""
last = chess.Move.from_uci(sys.argv[4]) if len(sys.argv) > 4 else None
b = chess.Board(fen)
S, M, T = 80, 40, 50 if title else 0
img = Image.new("RGB", (8 * S + 2 * M, 8 * S + 2 * M + T), "white")
d = ImageDraw.Draw(img)
piece_font = ImageFont.truetype("C:/Windows/Fonts/seguisym.ttf", 64)
label_font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
if title:
    d.text((img.width / 2, 25), title, fill="black", font=label_font, anchor="mm")
king = b.king(b.turn) if b.is_check() else None
for sq in chess.SQUARES:
    f, r = chess.square_file(sq), chess.square_rank(sq)
    x, y = M + f * S, T + M + (7 - r) * S
    colour = (240, 217, 181) if (f + r) % 2 else (181, 136, 99)
    if last and sq in (last.from_square, last.to_square):
        colour = (205, 210, 106) if (f + r) % 2 else (170, 162, 58)
    if sq == king:
        colour = (230, 80, 80)
    d.rectangle([x, y, x + S, y + S], fill=colour)
    p = b.piece_at(sq)
    if p:
        glyph = chess.UNICODE_PIECE_SYMBOLS[p.symbol().lower()]   # solid glyph, filled white or black with an outline
        fill, edge = ("white", "black") if p.color else ("black", "black")
        d.text((x + S / 2, y + S / 2 + 2), glyph, font=piece_font, anchor="mm", fill=fill, stroke_width=2, stroke_fill=edge)
for i in range(8):
    d.text((M + i * S + S / 2, T + M + 8 * S + 18), "abcdefgh"[i], fill="black", font=label_font, anchor="mm")
    d.text((M / 2, T + M + i * S + S / 2), str(8 - i), fill="black", font=label_font, anchor="mm")
img.save(out)
print("saved", out)
