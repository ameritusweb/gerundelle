"""Stress test (MAKING_RUNGS.md): full games from the standard position, the mind as it stands after rung 3.

Not a rung: nothing is built to pass it. Two Gerundelle minds (base arm, given territory, Black a keeper of what it holds,
the turns schedule) play games of up to --half-moves half-moves from the starting position. Per game: how it ended (mate,
a draw by the rules, the half-move cap, or idling), the material then, captures by side, how each side's moves were
chosen (planner / experiment / other), and the time it took. At the end: each side's phases and sub-wants, and the size
of its records. The failures are candidate residue for the next rungs.

Run: PYTHONHASHSEED=0 python -X utf8 experiments/fullgame.py [--seed 0] [--steps 4000] [--half-moves 120] [--winner-acts] [--imagined-lane] [--news-in-structure]
     [--curiosity 1.0] [--persistence 1.0] [--patience N]
"""
import argparse
import os
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "fiction"))

import chess  # noqa: E402
from rung3 import make, play  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--steps", type=int, default=4000, help="mind-steps in all (2 x rounds)")
    ap.add_argument("--half-moves", type=int, default=120)
    ap.add_argument("--winner-acts", action="store_true", help="Params.winner_acts: the push that won the top is made")
    ap.add_argument("--imagined-lane", action="store_true", help="Params.imagined_lane: pushes not offered now are imagined")
    ap.add_argument("--news-in-structure", action="store_true", help="Params.news_in_structure: news perceived, not presented")
    ap.add_argument("--stuck-earns", action="store_true", help="Params.stuck_earns: a stuck molecule must win to be refreshed")
    ap.add_argument("--curiosity", type=float, default=1.0)
    ap.add_argument("--persistence", type=float, default=1.0)
    ap.add_argument("--patience", type=int, default=None)
    a = ap.parse_args()
    w, minds = make(a.seed, "mind", "base", "keeper", given=True, fen=chess.STARTING_FEN, half_moves=a.half_moves)
    for m in minds:   # both minds, one temperament
        m.agent.mind.p.winner_acts = a.winner_acts
        m.agent.mind.p.imagined_lane = a.imagined_lane
        m.agent.mind.p.news_in_structure = a.news_in_structure
        m.agent.mind.p.stuck_earns = a.stuck_earns
        m.agent.mind.p.curiosity, m.agent.mind.p.persistence, m.agent.mind.p.patience = a.curiosity, a.persistence, a.patience
    print(f"winner_acts={a.winner_acts} imagined_lane={a.imagined_lane} news_in_structure={a.news_in_structure} curiosity={a.curiosity} persistence={a.persistence} patience={a.patience}", flush=True)
    agents = {m.name: m.agent for m in minds}
    src = {"White": Counter(), "Black": Counter()}
    last_plan = {"White": None, "Black": None}
    for name, ag in agents.items():
        planned = ag.planned

        def traced(invs, _n=name, _p=planned):
            last_plan[_n] = _p(invs)
            return last_plan[_n]
        ag.planned = traced
        tick = ag.tick

        def ticked(force=None, _n=name, _t=tick, _ag=ag):
            queue, last_plan[_n] = list(_ag.queue), None
            choice, rec = _t(force)
            if choice is not None:
                src[_n]["planned" if choice == last_plan[_n] else "experiment" if (queue or _ag.running) else "winner"] += 1
            return choice, rec
        ag.tick = ticked
    game = dict(n=0, t0=time.time(), caps=Counter(), half=0)
    act, reset = w.act, w.reset

    def logged(inv=None, hold=False):
        if inv is not None and inv[0] != "pass":
            mv = w.board.parse_san(inv[0].split(" ", 1)[-1])
            if w.board.is_capture(mv):
                game["caps"][w.actor] += 1
            game["half"] += 1
        return act(inv, hold)
    w.act = logged

    def counted_reset():
        if hasattr(w, "standing"):
            b = w.board
            why = ("mate" if b.is_checkmate() else "draw (rules)" if b.is_game_over() else
                   "half-move cap" if w.moved >= w.moves else "idle")
            game["n"] += 1
            s = {n: dict(src[n]) for n in src}
            print(f"game {game['n']}: {game['half']} half-moves, ended by {why}; White's balance {w.balance('White')} "
                  f"({w.material() - w.start_material:+d}); captures {dict(game['caps'])}; moves chosen {s}; "
                  f"{time.time() - game['t0']:.0f}s", flush=True)
            for n in src:
                src[n].clear()
            game.update(t0=time.time(), caps=Counter(), half=0)
        reset()
    w.reset = counted_reset
    t0 = time.time()
    play(w, minds, a.steps // 2, "turns")
    w.close()
    print(f"--- {a.steps} mind-steps in {time.time() - t0:.0f}s; games finished {game['n']}; the game under way had "
          f"{game['half']} half-moves")
    for m in minds:
        ag = m.agent
        ph = Counter(p.split(":")[1] for p in ag.mind.phases.info)
        subs = Counter(g for _, g, k in ag.sub_log if k == "set")
        print(f"{m.name}: phases {dict(ph.most_common())}; sub-wants set {subs.most_common(5)}; pushes {len(ag.tried)}; "
              f"meta readings {len(ag.mind.meta.modes)}, splits {len(ag.mind.meta.splits)}; territory rows "
              f"{len(ag.mind.territory.rows)}; reached {len(ag.reached)}")


if __name__ == "__main__":
    main()
