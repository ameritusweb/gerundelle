"""Rung 3: why a defending Black (wanting holding_black_kept) takes back only a third of the time.

At each Black move made right after a White capture, it records:
  source   what in Black's agent chose the move: 'planned' (SovAgent.planned found a way: plan_step, a sub-want's, or
           a noticed push), 'experiment' (the next step of an experiment, or one starting), or 'forced' (a scripted
           call; none here)
  goal     Black's current want, and the sub-wants above it
  the take-back push on offer (a capture on the square White just took on): its reading in the situation Black is in
  (through the meta layer's splits), how often that reading was tried, what came of it (the want or not), and what
  Black's model predicts for it now
Counts are per configuration (0 defended, 1 hanging), over the run.

Run: PYTHONHASHSEED=0 python -X utf8 experiments/why3.py [--seeds 0,1,2] [--rounds 800] [--arm base] [--black-want kept]
     [--show 6]
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
from force_world import inv_id  # noqa: E402


def run(seed, arm, rounds, black_want, show):
    w, minds = make(seed, "mind", arm, black_want)
    black = minds[1].agent
    want = minds[1].want
    st = dict(took=None, planned=None)   # took: the square White just captured on, while Black has not answered
    rows = []

    planned = black.planned

    def traced_planned(invs):
        out = planned(invs)
        st["planned"] = out
        return out
    black.planned = traced_planned
    tick = black.tick

    def traced_tick(force=None):
        if w.actor != "Black" or st["took"] is None or w.board.turn != chess.BLACK:
            return tick(force)
        before = dict(goal=black.goal, stack=list(black.stack), queue=list(black.queue), running=black.running,
                      watching=bool(black.watching))
        facts = black.facts_now()
        offered = {i[0].split(" ", 1)[-1]: i for i in w.invitations()}
        sq = st["took"]
        back = [i for san, i in offered.items()
                if w.board.parse_san(san).to_square == sq]
        info = []
        for inv in back:
            c = inv_id(inv)
            x = black.mind.meta.reading_in(c, facts)
            hist = black.mind.meta.modes.get(x, [])
            info.append(dict(push=inv[0].split(" ", 1)[-1], reading=x.split("|", 1)[1] if "|" in x else "-",
                             tried=len(hist), wanted=sum(1 for h in hist if want in h[2]),
                             predict=sorted(black.predict(inv, facts) or ["never tried here"])[:4],
                             splits=black.conditions_of(inv)[:3]))
        st["planned"] = None
        choice, rec = tick(force)
        if choice is None:
            return choice, rec
        san = choice[0].split(" ", 1)[-1]
        took_back = any(choice == i for i in back)
        if st["planned"] is not None and choice == st["planned"]:
            source = "planned"
        elif before["queue"] or black.running:
            source = "experiment"
        else:
            source = "other"
        rows.append(dict(cfg=w.config, t=black.mind.t, move=san, took_back=took_back, source=source,
                         goal=before["goal"], stack=before["stack"], back=info,
                         exp=black.running or (rec["experiments"][0] if rec.get("experiments") else None)))
        st["took"] = None
        return choice, rec
    black.tick = traced_tick
    act = w.act

    def logged(inv=None, hold=False):
        if inv is not None and inv[0] != "pass":
            move = w.board.parse_san(inv[0].split(" ", 1)[-1])
            cap = w.board.is_capture(move)
            if w.actor == "White":
                st["took"] = move.to_square if cap else None
        return act(inv, hold)
    w.act = logged
    reset = w.reset

    def counted_reset():
        st["took"] = None
        reset()
    w.reset = counted_reset
    play(w, minds, rounds, "turns")
    w.close()
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--rounds", type=int, default=800)
    ap.add_argument("--arm", default="base")
    ap.add_argument("--black-want", default="kept", choices=("up", "kept"))
    ap.add_argument("--show", type=int, default=6, help="example decisions printed per seed (late in the run)")
    a = ap.parse_args()
    tot = Counter()
    for s in (int(x) for x in a.seeds.split(",")):
        rows = run(s, a.arm, a.rounds, a.black_want, a.show)
        c = Counter((r["cfg"], r["took_back"], r["source"]) for r in rows)
        tot.update(c)
        avail = Counter((r["cfg"], bool(r["back"])) for r in rows)
        print(f"seed {s}: Black's moves right after a White capture: {len(rows)}; "
              f"(cfg, took back, source) {dict(sorted(c.items()))}; take-back on offer {dict(sorted(avail.items()))}")
        goals = Counter((r["goal"] or "none") + (" [sub of " + r["stack"][0] + "]" if r["stack"] else "") for r in rows
                        if not r["took_back"])
        print(f"  goal when not taking back: {goals.most_common(5)}")
        exps = Counter((r["exp"] or "-").split(":")[1] if r["exp"] else "-" for r in rows if not r["took_back"])
        print(f"  experiment kinds when not taking back: {dict(exps.most_common())}")
        tb = [b for r in rows if not r["took_back"] for b in r["back"]]
        print(f"  the take-back, when not taken: never tried in this reading {sum(1 for b in tb if b['tried'] == 0)}, "
              f"tried and never brought the want {sum(1 for b in tb if b['tried'] and not b['wanted'])}, "
              f"brought it before {sum(1 for b in tb if b['wanted'])} (of {len(tb)})")
        for r in [r for r in rows if not r["took_back"] and r["back"]][-a.show:]:
            print(f"    t={r['t']} cfg {r['cfg']}: played {r['move']} by {r['source']} (exp {r['exp']}); goal {r['goal']} "
                  f"stack {r['stack']}; take-back {r['back']}")
        print(flush=True)
    print(f"TOTAL (cfg, took back, source): {dict(sorted(tot.items()))}")


if __name__ == "__main__":
    main()
