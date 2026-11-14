"""Two Gerundelle minds playing Go against each other (goduel.py). Each is built as run.build builds the mind alone (the switch set read from
tetris/run.py, plus run.GO_SWITCHES), on its own seat, with its territory from its own seat (run.give: where the other colour's
opportunities are dead). Params overrides per colour come from --black / --white as key=value pairs (temperament, for the league).
Reports each game: stones, each colour's area, who won, stones taken; and that the seats stayed one game every slice.
Run: PYTHONHASHSEED=0 python -u -X utf8 duel_run.py [--slices 600] [--seed 0] [--black aversion=2] [--white acceptance=3]"""
import argparse
import ast
import sys
import time

import run
from goduel import Duel
from molecules import Params
from potential import ForceMind
from sov_agent import SovAgent
from world import BLACK, WHITE


def mind(seat, overrides=None, acceptance=6):
    p = Params(**{**run.SWITCHES, **run.GO_SWITCHES, **(overrides or {})})
    a = SovAgent(seat, ForceMind(p))
    if "acceptance" not in (overrides or {}):
        a.mind.p.acceptance = acceptance
    return a


def parse(pairs):
    out = {}
    for kv in pairs or ():
        k, v = kv.split("=", 1)
        out[k] = ast.literal_eval(v)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--slices", type=int, default=600)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--black", nargs="*")
    ap.add_argument("--white", nargs="*")
    args = ap.parse_args()
    d = Duel(seed=args.seed)
    agents = {BLACK: mind(d.seats[BLACK], parse(args.black)), WHITE: mind(d.seats[WHITE], parse(args.white))}
    read = {BLACK: 0, WHITE: 0}

    def after(colour, agent, seat):
        read[colour], _ = run.give(agent, seat, read[colour])

    t0, shown = time.time(), 0
    for t in range(args.slices):
        d.step(agents, after)
        while shown < len(d.results):
            r = d.results[shown]
            shown += 1
            print(f"  game {shown}: {r['stones']} stones in {r['slices']} slices; area black {r['black_area']}, white {r['white_area']}: "
                  f"{r['winner']}; taken by black {r['black_took']}, by white {r['white_took']}", flush=True)
        if (t + 1) % 100 == 0:
            held = {c: sum(1 for r_, row in agents[c].mind.territory.rows.items() if r_.startswith("opportunity_") and row.get("holder") == "mine")
                    for c in agents}
            print(f"    slice {t + 1} ({time.time() - t0:.0f}s): stones this game {d.seats[BLACK].placed}; opportunities held: black {held[BLACK]}, "
                  f"white {held[WHITE]}; wants: black {str(agents[BLACK].goal)[:40]}, white {str(agents[WHITE].goal)[:40]}", flush=True)
    print(f"games {len(d.results)}: winners {[r['winner'] for r in d.results]}; the seats stayed one game for {args.slices} slices")


if __name__ == "__main__":
    main()
