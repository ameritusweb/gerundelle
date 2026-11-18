"""Rung 3's rooms (LADDER.md): the learning room, the same structure elsewhere, and a loose room. Each is checked here against the engine, not assumed.

A room is set up as fiction sets up a scene: pieces placed. What the mind makes of it is its own.
"""
from warpworld import BLACK, RUNG1_TWO, WHITE, WarpWorld, rehash

FILES = "abcdefgh"


def shift(fen, df):
    """The same position, every piece df files over (on both boards)."""
    boards, rest = fen.split(" ", 1)
    out = []
    for board in boards.split("|||"):
        rows = []
        for row in board.split("/"):
            cells = []
            for ch in row:
                cells += ["."] * int(ch) if ch.isdigit() else [ch]
            moved = ["."] * 8
            for f, ch in enumerate(cells):
                if ch != ".":
                    moved[f + df] = ch   # IndexError if it falls off: such a shift isn't a room
            s, n = "", 0
            for ch in moved:
                if ch == ".":
                    n += 1
                else:
                    s += (str(n) if n else "") + ch
                    n = 0
            rows.append(s + (str(n) if n else ""))
        out.append("/".join(rows))
    return "|||".join(out) + " " + rest


def first_capture(fen, target_char="n", depth=2):
    """With Black passing: the fewest White moves that take Black's piece of that kind, and the lines that do (move uci strings)."""
    w = WarpWorld(fen)
    def count(b):
        return sum(1 for s in range(len(b.pieces)) if b.pieces[s] and not b.colors[s] and b.pieces[s] == KIND[target_char])
    lines, frontier = {}, [((), w.board.copy())]
    for d in range(1, depth + 1):
        nxt = []
        for line, b in frontier:
            for m in b.legal_moves:
                c = b.copy()
                c.push(m)
                if count(c) < count(b):
                    lines.setdefault(d, []).append(line + (m.uci(),))
                elif c._king_sq[BLACK] >= 0 and c._king_sq[WHITE] >= 0:
                    c.turn = WHITE
                    rehash(c)
                    nxt.append((line + (m.uci(),), c))
        if d in lines:
            return d, lines[d]
        frontier = nxt
    return None, []


KIND = {"p": 1, "n": 2, "b": 3, "r": 4, "q": 5, "k": 6}

LEARN = RUNG1_TWO                      # the rung-1 room: the knight is two White moves away
SAME = shift(RUNG1_TWO, -2)            # the same room two files over: every piece has another square, and another name
LOOSE = shift("8/8/8/8/3R4/5PPP/2K5|||8/8/8/4n3/8/8/4k3 w - - 0 1", -2)   # as SAME, the knight one square over (e4 before the shift): out of two White moves' reach

if __name__ == "__main__":
    for name, fen in (("learn", LEARN), ("same", SAME), ("loose", LOOSE)):
        d, lines = first_capture(fen, depth=3)
        print(name, fen, "knight taken in", d, "moves;", len(lines), "lines, e.g.", lines[:6])
