"""Rung 3: why a Black mind moves its knight off d5 more often when its pieces are its given territory.

For every Black move of the knight from d5, records what in the agent chose it ('planned': SovAgent.planned's way;
'experiment': a step of an experiment, with its kind: probe, conditions, causes, caused_by, co_occurs, await, summon;
'other'), Black's want and sub-wants, and the ownership instances among the top winners that tick (what pays the
experiments: Territory.serve). Also whether White had just captured, and whether the knight stood attacked then.

Run: PYTHONHASHSEED=0 python -X utf8 experiments/flee3.py [--seeds 0,1,2] [--rounds 800] [--given]
"""
import argparse
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "fiction"))

import chess  # noqa: E402
from rung3 import make, play  # noqa: E402  (puts Gerundelle on the path)


def run(seed, rounds, given):
    w, minds = make(seed, "mind", "base", "kept", given)
    black = minds[1].agent
    st = dict(planned=None, white_took=False)
    rows = []
    planned = black.planned

    def traced_planned(invs):
        st["planned"] = planned(invs)
        return st["planned"]
    black.planned = traced_planned
    tick = black.tick

    def traced_tick(force=None):
        if w.actor != "Black" or w.board.turn != chess.BLACK:
            return tick(force)
        queue, goal, stack = list(black.queue), black.goal, list(black.stack)
        knight_state = w.states().get("black_knight_d5_safety")
        on_d5 = w.where.get("black_knight_d5") == chess.D5
        st["planned"] = None
        choice, rec = tick(force)
        if choice is None:
            return choice, rec
        if not (on_d5 and choice[1] == "black_knight_d5"):   # the knight, moved from d5
            st["white_took"] = False
            return choice, rec
        if st["planned"] is not None and choice == st["planned"]:
            source = "planned"
        elif queue or black.running:
            exp = black.running or ""
            source = "experiment:" + (exp.split(":")[1] if exp else "?")
        else:
            source = "other"
        top = rec["levels"][-1]["winners"]
        own = sorted(i for i in top if i.startswith("own:") and not i.startswith("own:q:"))
        rows.append(dict(source=source, exp=black.running, goal=goal, stack=stack, own=own, after_capture=st["white_took"],
                         knight=knight_state))
        st["white_took"] = False
        return choice, rec
    black.tick = traced_tick
    act = w.act

    def logged(inv=None, hold=False):
        if inv is not None and inv[0] != "pass" and w.actor == "White":
            st["white_took"] = w.board.is_capture(w.board.parse_san(inv[0].split(" ", 1)[-1]))
        return act(inv, hold)
    w.act = logged
    play(w, minds, rounds, "turns")
    w.close()
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--rounds", type=int, default=800)
    ap.add_argument("--given", action="store_true")
    a = ap.parse_args()
    tot_src, tot_own, tot_ctx = Counter(), Counter(), Counter()
    for s in (int(x) for x in a.seeds.split(",")):
        rows = run(s, a.rounds, a.given)
        src = Counter(r["source"] for r in rows)
        own = Counter(o.split(":", 1)[1] for r in rows if r["source"].startswith("experiment") for o in r["own"])
        ctx = Counter((r["after_capture"], r["knight"]) for r in rows)
        exps = Counter(r["exp"] for r in rows if r["exp"])
        tot_src.update(src); tot_own.update(own); tot_ctx.update(ctx)
        print(f"seed {s} ({'given' if a.given else 'not given'}): knight moves off d5 {len(rows)}; chosen by {dict(src.most_common())}")
        print(f"  (after a White capture, knight's safety then): {dict(ctx.most_common())}")
        print(f"  ownership instances at the top when an experiment moved it: {own.most_common(6)}")
        print(f"  commonest experiments: {exps.most_common(4)}", flush=True)
    print(f"TOTAL ({'given' if a.given else 'not given'}): chosen by {dict(tot_src.most_common())}; context {dict(tot_ctx.most_common())}; "
          f"own at top {tot_own.most_common(6)}")


if __name__ == "__main__":
    main()
