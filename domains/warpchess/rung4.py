"""Rung 4 (LADDER.md): full games, against a random player first. Run: python -X utf8 rung4.py [--seeds 6] [--rounds 2000] [--learn 1000] [--arm carried|fresh] [--only SEED]"""
import argparse
import statistics
import sys

from gameworld import GameWorld, RandomSide, opening_rooms
from pairs3 import PairMind
from rooms3 import LEARN
from rung0 import WANT
from warpworld import WarpWorld

TURN_STEPS = 5   # as rung 2
GOAL = "outcome_white_won"   # to win the game (my choice, as the Nim mind's outcome_won)


SWITCHES = ("imagined_tournament", "want_site", "setup_support")
OWN = ("own_wants",)   # with --own: ownership slots set sub-wants on the existing stack (not Params.subwants, the planner's own), pieces given


class Player(PairMind):
    """Rung 1f's main mind (potential forces, offer memory, winner_acts); its pairs aren't read here."""

    def update(self):
        pass


def switch(mind, on):
    for k in SWITCHES:
        setattr(mind.p, k, on)


def learned(seed, ticks, on=False):
    """A mind that has lived rung 1's two-move room (as rung 3's learn room)."""
    w = WarpWorld(LEARN, seed=seed, moves=2, forces=True)
    a = Player(w, "learn")
    switch(a.mind, on)
    for _ in range(ticks):
        if a.goal is None:
            a.goal = WANT
        a.tick()
    return a.mind


def play(seed, rounds, mind=None, patience=None, fen=None, on=False, label="", own=False):
    w = GameWorld(seed=seed, fen=fen)
    w.owned = own
    w.actor = "White"
    white = Player(w, "game", mind=mind)
    white.mind.p.patience = patience
    switch(white.mind, on)
    if own:
        for k in OWN:
            setattr(white.mind.p, k, True)
        terr = white.mind.territory
        terr.given = w.white_pieces()
        for r in terr.given:
            terr.row(r)
        terr.update(terr.given)
    black = RandomSide(w, seed)
    for r in range(rounds):
        if r % 100 == 0 and r:
            g = w.games
            print(f"  {label} round {r}: games {len(g)}, won {sum(x[0] == '1-0' for x in g)}, lost {sum(x[0] == '0-1' for x in g)}, "
                  f"White up at the end {sum(x[1] > 0 for x in g)}, down {sum(x[1] < 0 for x in g)}; wants met {len(white.reached)}", flush=True)
        if w.board.turn == 1:
            w.actor = "White"
            for _ in range(TURN_STEPS):
                if white.goal is None:
                    white.goal = GOAL
                n = len([x for x in w.log if x[2]])
                white.tick()
                if len([x for x in w.log if x[2]]) > n:
                    break
        else:
            black.tick()
            w.actor = "White"
            white.tick()   # it sees the answer
    return w, white


def summary(games):
    n = len(games)
    up = sum(g[1] > 0 for g in games) / max(1, n)
    down = sum(g[1] < 0 for g in games) / max(1, n)
    won = sum(g[0] == "1-0" for g in games)
    lost = sum(g[0] == "0-1" for g in games)
    bal = statistics.median([g[1] for g in games]) if games else float("nan")
    return dict(n=n, up=up, down=down, won=won, lost=lost, balance=bal)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--rounds", type=int, default=2000)
    ap.add_argument("--learn", type=int, default=1000)
    ap.add_argument("--arm", default="carried")
    ap.add_argument("--patience", type=int, default=None)
    ap.add_argument("--only", type=int, default=None)
    ap.add_argument("--switches", action="store_true", help="rung 1g's switches on: " + ", ".join(SWITCHES))
    ap.add_argument("--own", action="store_true", help="Params.own_wants and subwants, White's pieces given territory")
    ap.add_argument("--room", default="chevron", help="chevron (the rulebook start) or an iteration of the user's openings, e.g. iter_286")
    args = ap.parse_args()
    for s in ([args.only] if args.only is not None else range(args.seeds)):
        mind = learned(s, args.learn, args.switches) if args.arm == "carried" else None
        fen = None if args.room == "chevron" else dict(opening_rooms())[args.room]
        w, white = play(s, args.rounds, mind, args.patience, fen, args.switches, f"{args.room} {args.arm} seed {s}", args.own)
        g = w.games
        early, late = summary(g[: len(g) // 2]), summary(g[len(g) // 2:])
        print(f"{args.room} {args.arm} patience {args.patience} seed {s}: games {len(g)}; early: up {early['up']:.2f} down {early['down']:.2f} won {early['won']} lost {early['lost']} median balance {early['balance']}; "
              f"late: up {late['up']:.2f} down {late['down']:.2f} won {late['won']} lost {late['lost']} median balance {late['balance']}; wants met {len(white.reached)}, gave up {len(white.gave_up)}", flush=True)
        print("   results:", [(r, b, m) for r, b, m in g][-8:], flush=True)


if __name__ == "__main__":
    main()
