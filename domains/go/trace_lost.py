"""Why the mind loses more stones than a random player (the first run: 49, 56, 49 a game against 45, 41, 40). Each stone the mind
places, by the potential force its placement had (3 takes a group, 2 presses a stone of the other's, 1 reaches none): how many, the
breath its group had once it landed, and how many were later taken. The same for a player placing random legal stones in the same
world. Run: python -u -X utf8 trace_lost.py [slices]"""
import random
import sys

import run
from world import BLACK, GoWorld

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 650


def breath(w, c):
    group, around = w.group_of(w.board(), c, w.beside)
    return sum(1 for n in around if n not in w.at)


def table(name, rows, lost, offers):
    print(f"{name}: {len(rows)} stones placed, {sum(1 for s, *_ in rows if s in lost)} later taken")
    for f in (3.0, 2.0, 1.0):
        sub = [r for r in rows if r[1] == f]
        on = sum(1 for o in offers if f in o)
        share = sum(sum(1 for x in o if x == f) / len(o) for o in offers) / max(len(offers), 1)
        if sub:
            print(f"  force {f:.0f}: {len(sub)} stones ({len(sub) / len(rows):.0%}; on offer in {on} of {len(offers)} turns, {share:.0%} of the placements on offer); "
                  f"breath once landed: mean {sum(r[2] for r in sub) / len(sub):.2f}, one or none {sum(1 for r in sub if r[2] <= 1)}; "
                  f"later taken {sum(1 for r in sub if r[0] in lost)} ({sum(1 for r in sub if r[0] in lost) / len(sub):.0%})")


def play(w, choose, after=lambda: None):
    rows, offers, on_board = [], [], set()
    lost = set()
    for t in range(N):
        pots = w.potentials()
        inv = choose(pots)
        mine = {s for s, col in w.colour.items() if col == BLACK}
        if inv is not None and pots:
            offers.append(list(pots.values()))
            c = w.target(inv)
            if w.at.get(c) and w.colour[w.at[c]] == BLACK and w.at[c] not in on_board:
                pass
        after()
        now = {s for s, col in w.colour.items() if col == BLACK}
        for s in now - on_board:   # a stone of the mind's landed this slice
            c = next(k for k, v in w.at.items() if v == s)
            rows.append([s, w.__dict__.pop("_force", None), breath(w, c)])
        on_board |= now
        lost |= {s for s in on_board if s not in w.colour and s not in w.kept}   # off the board and not kept: taken by the other
    return rows, lost, offers


# the mind
a, w = run.build(0, 0.7)
read = [0]


def mind_choose(pots):
    a.mind.potentials = pots
    choice, rec = a.tick()
    read[0], _ = run.give(a, w, read[0])
    if choice is not None:
        w._force = pots.get(f"place_push:{choice[1]}_free")
    return choice


rows, lost, offers = play(w, mind_choose)
table("the mind", [r for r in rows if r[1] is not None], lost, offers)

# a random player, the same world
w2 = GoWorld(seed=0, luck=0.7)
w2.earn = lambda: None
rng = random.Random(1)


def random_choose(pots):
    w2.renew()
    invs = w2.invitations()
    inv = rng.choice(invs) if invs else None
    if inv is not None:
        w2._force = pots.get(f"place_push:{inv[1]}_free")
    w2.act(inv)
    return inv


rows2, lost2, offers2 = play(w2, random_choose)
table("a random player", [r for r in rows2 if r[1] is not None], lost2, offers2)
