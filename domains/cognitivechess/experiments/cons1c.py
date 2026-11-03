"""Rung 1c, converge, one seed: the failure kinds and constraints held, and in the both-mate configuration what the
mating moves would meet and which constraint each runs into."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1c  # noqa: E402
from sov_agent import constraints_from  # noqa: E402
import chess  # noqa: E402
from chessworld import RUNG1C  # noqa: E402

w, m, log = rung1c.run(int(sys.argv[1]), "converge", 800)
a = m.agent
print("kinds:", collections.Counter(k[:50] for _, k in a.trials).most_common(8))
cons = constraints_from(a.trials)
print("constraints:", {e[:40]: [" ".join(sorted(h)) for h in hs] for e, hs in cons.items()})
w.board = chess.Board(RUNG1C[rung1c.BOTH])
for san in ("Rd8", "Re8"):
    meet = w.relations_of((san, None, None))
    hits = [(e[:30], " ".join(sorted(h))) for e, hs in cons.items() for h in hs if h <= meet]
    print(san, "meets", " ".join(sorted(meet)), "\n   runs into", hits)
