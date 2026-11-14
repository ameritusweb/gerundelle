"""The boards of the mind's first two games (trace_games.py: game 1 lost 1 stone, game 2 lost 48), shown every 10 of its stones, with
the stones it placed since (point, potential force, how the placement touched its own stones), the anti-want held, and the holders the
territory register gives the points. Run: python -u -X utf8 trace_boards.py [slices]"""
import collections
import sys

import run
from world import BLACK, WHITE

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 600
a, w = run.build(0, 0.7)
read, since, shown_at = 0, [], (0, 0)


def board():
    return ["".join("X" if w.colour.get(w.at.get((x, y))) == BLACK else "O" if (x, y) in w.at else "." for x in range(w.size)) for y in range(w.size)]


for t in range(N):
    pots = w.potentials()
    a.mind.potentials = pots
    game = len(w.games)
    before = w.board()
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    if choice is not None:
        c = w.target(choice)
        own = sum(1 for n in w.beside(c) if before.get(n) == BLACK)
        theirs = sum(1 for n in w.beside(c) if before.get(n) == WHITE)
        since.append(f"({c[0]},{c[1]}) f{pots.get(f'place_push:{choice[1]}_free', 0):.0f} own{own} theirs{theirs}")
        if w.black_placed % 10 == 0 and (game, w.black_placed) != shown_at:
            shown_at = (game, w.black_placed)
            terr = a.mind.territory
            holders = collections.Counter(row["holder"] for r, row in terr.rows.items() if r.startswith("point_"))
            print(f"game {game + 1}, the mind's stone {w.black_placed} (slice {t}): taken so far by the mind {w.took[BLACK]}, by the other {w.took[WHITE]}; "
                  f"anti-want {a.__dict__.get('anti')}; goal {a.goal}; points held as {dict(holders)}")
            for row in board():
                print("    " + row)
            print("    placed since:", "; ".join(since))
            since = []
print("anti-wants:", collections.Counter(k for _, _, k in a.__dict__.get("anti_log", [])).most_common(), "| last few:", a.__dict__.get("anti_log", [])[-4:])
