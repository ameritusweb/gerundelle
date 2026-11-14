"""Find a rung-2 start where neither side can capture on its first move: RUNG2 with Black's king and bishop moved as little as possible."""
from warpworld import WarpWorld, WHITE, BLACK, rehash, square_name

FILES = "abcdefgh"
def fen(bsq, ksq):
    rows = []
    for rank in range(7, 0, -1):
        row = ["."] * 8
        if rank == 4: row[3] = "n"
        for sq, ch in ((bsq, "b"), (ksq, "k")):
            if sq and int(sq[1]) == rank: row[FILES.index(sq[0])] = ch
        s, n = "", 0
        for c in row:
            if c == ".": n += 1
            else: s += (str(n) if n else "") + c; n = 0
        rows.append(s + (str(n) if n else ""))
    return "8/8/8/8/3R4/5PPP/2K5|||" + "/".join(rows) + " w - - 0 1"

def captures(w, colour):
    b = w.board.copy(); b.turn = colour; rehash(b)
    out = []
    for m in b.legal_moves:
        t = w.board.copy(); t.turn = colour; rehash(t)
        before = sum(1 for s in range(len(t.pieces)) if t.pieces[s] and t.colors[s] != colour)
        t.push(m)
        if sum(1 for s in range(len(t.pieces)) if t.pieces[s] and t.colors[s] != colour) < before: out.append(m.uci())
    return out

dist = lambda a, b: abs(FILES.index(a[0]) - FILES.index(b[0])) + abs(int(a[1]) - int(b[1]))
cands = []
for b in [f + r for f in FILES for r in "1234567"]:
    for k in [f + r for f in FILES for r in "1234567"]:
        if b == k or "d4" in (b, k): continue
        try: w = WarpWorld(fen(b, k), seed=0)
        except Exception: continue
        if not captures(w, WHITE) and not captures(w, BLACK):
            cands.append((dist(b, "a6") + dist(k, "e1"), b, k))
cands.sort()
print(cands[:10])
