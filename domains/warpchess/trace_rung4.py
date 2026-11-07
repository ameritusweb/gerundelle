"""Trace (LADDER.md, rung 4): why does White end games up on material less often late than early? One run, a line per game: White's captures
and losses (by kind), how White's moves were chosen, and how many distinct moves it made. Run: python -X utf8 trace_rung4.py ROOM SEED"""
import collections
import sys

import rung4
from gameworld import GameWorld, RandomSide, opening_rooms
from warpworld import NAMES, PIECE_VALUES

sys.stdout.reconfigure(encoding="utf-8")
ROOM, SEED = sys.argv[1], int(sys.argv[2])
mind = rung4.learned(SEED, 1000, True)
fen = None if ROOM == "chevron" else dict(opening_rooms())[ROOM]
w = GameWorld(seed=SEED, fen=fen)
w.actor = "White"
white = rung4.Player(w, "game", mind=mind)
rung4.switch(white.mind, True)
black = RandomSide(w, SEED)
how = {"v": None}
planned, winner, did = white.planned, white.winner, white.mind.inquiry.did
def p(invs):
    s = planned(invs)
    if s is not None: how["v"] = "plan"
    return s
def wn(rec, invs):
    s = winner(rec, invs)
    if s is not None: how["v"] = "attention"
    return s
def d(eid):
    how["v"] = "experiment"
    return did(eid)
white.planned, white.winner, white.mind.inquiry.did = p, wn, d
game = dict(took=collections.Counter(), lost=collections.Counter(), how=collections.Counter(), moves=set(), refused=0)
orig_play = w.play
def play(move):
    side = "White" if w.board.turn else "Black"
    kinds = {sq: (w.board.pieces[sq], w.board.colors[sq]) for sq in range(len(w.board.pieces)) if w.board.pieces[sq]}
    mover = orig_play(move)
    after = {sq: (w.board.pieces[sq], w.board.colors[sq]) for sq in range(len(w.board.pieces)) if w.board.pieces[sq]}
    gone = collections.Counter(kinds.values()) - collections.Counter(after.values())
    for (pc, col), n in gone.items():
        name = NAMES[pc]
        if col != (side == "White"):
            (game["took"] if side == "White" else game["lost"])[name] += n
        else:
            game["lost" if side == "White" else "took"][name + "(own move)"] += n
    return mover
w.play = play
n_games = 0
for r in range(2000):
    if w.board.turn == 1:
        w.actor = "White"
        for _ in range(rung4.TURN_STEPS):
            if white.goal is None:
                white.goal = rung4.GOAL
            n = len([x for x in w.log if x[2]])
            how["v"] = None
            white.tick()
            if len([x for x in w.log if x[2]]) > n:
                game["how"][how["v"]] += 1
                game["moves"].add(w.log[-1][1])
                break
            elif w.log and w.log[-1][2] is False:
                game["refused"] += 1
    else:
        black.tick()
        w.actor = "White"
        white.tick()
    if len(w.games) > n_games:
        g = w.games[-1]
        n_games = len(w.games)
        val = lambda c: sum(PIECE_VALUES[[k for k, v in NAMES.items() if v == nm.split("(")[0]][0]] * n for nm, n in c.items())
        print(f"game {n_games}: {g[0]}, balance {g[1]}, half-moves {g[2]} | White took {dict(game['took'])} ({val(game['took'])}); lost {dict(game['lost'])} ({val(game['lost'])}) | "
              f"moves by {dict(game['how'])}, distinct {len(game['moves'])}, refused {game['refused']}", flush=True)
        game = dict(took=collections.Counter(), lost=collections.Counter(), how=collections.Counter(), moves=set(), refused=0)
