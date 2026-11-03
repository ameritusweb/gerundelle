"""Rung 3 check: where a side's standing outcome goes. After Black answers, White's new standing waits in pend['White'];
it is delivered in White's next slice with no move, or dropped if White moves in that slice. Delivered, it credits White's
push only if it lands inside that push's watch (SovAgent.watching). Also: how many of White's own slices pass between its
move and Black's answer.

Run: python -X utf8 experiments/delivery3.py [--seeds 0,1] [--rounds 800] [--black mind] [--arm base] [--schedule rounds|turns]
"""
import argparse, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "fiction"))
from chessworld import RUNG1, DuelWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402
from rung3 import ARMS, ScriptedBlack  # noqa: E402


def run(seed, black, arm, rounds, schedule="rounds"):
    w = DuelWorld(RUNG1, order=seed, seed=seed)
    minds = []
    for side in ("White", "Black"):
        if side == "Black" and black == "scripted":
            minds.append(ScriptedBlack(w)); continue
        m = GerundelleMind(side, w, want=f"standing_{side.lower()}_up", want_count=10 ** 6)
        for k, v in ARMS[arm].items():
            setattr(m.agent.mind.p, k, v)
        minds.append(m)
    white = minds[0].agent
    fate, delay = Counter(), Counter()
    st = dict(white_slices=None)
    act = w.act

    def logged(inv=None, hold=False):
        who = w.actor
        waiting = w.pend["White"].get("standing_white")
        if who == "White":
            if waiting is not None:
                if inv is not None:
                    fate[f"dropped ({waiting[0]}->{waiting[1]})"] += 1
                else:
                    fate[("in White's watch" if white.watching else "outside any watch") + f" ({waiting[0]}->{waiting[1]})"] += 1
            if st["white_slices"] is not None:
                st["white_slices"] += 1
            if inv is not None:
                st["white_slices"] = 0
        elif inv is not None and st["white_slices"] is not None:
            delay[st["white_slices"]] += 1   # White slices between White's move and Black's answer
            st["white_slices"] = None
        return act(inv, hold)
    w.act = logged
    seen = {m.name: 0 for m in minds}
    by = {m.name: m for m in minds}

    def step(n):
        w.actor = n
        seen[n] = by[n].step(seen[n])
    if schedule == "rounds":
        for _ in range(rounds):
            for m in minds:
                step(m.name)
    else:   # rung3.py's turns schedule
        import chess
        from rung3 import TURN_STEPS
        spent = 0
        while spent < 2 * rounds:
            mover = "White" if w.board.turn == chess.WHITE else "Black"
            other = "Black" if mover == "White" else "White"
            before = (w.moved, len(w.episodes))
            for _ in range(TURN_STEPS):
                step(mover); spent += 1
                if (w.moved, len(w.episodes)) != before or spent >= 2 * rounds:
                    break
            if spent < 2 * rounds:
                step(other); spent += 1
    w.close()
    return fate, delay


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0,1"); ap.add_argument("--rounds", type=int, default=800)
    ap.add_argument("--black", default="mind"); ap.add_argument("--arm", default="base")
    ap.add_argument("--schedule", default="rounds", choices=("rounds", "turns"))
    a = ap.parse_args()
    F, D = Counter(), Counter()
    for s in (int(x) for x in a.seeds.split(",")):
        f, d = run(s, a.black, a.arm, a.rounds, a.schedule)
        F.update(f); D.update(d)
        print(f"seed {s}: standing outcomes {dict(f.most_common())}; Black answers after White slices {dict(sorted(d.items()))}", flush=True)
    print(f"TOTAL ({a.arm}, Black {a.black}, {a.schedule}): {dict(F.most_common())}; delay {dict(sorted(D.items()))}")


if __name__ == "__main__":
    main()
