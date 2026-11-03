"""Rung 1c: constraint convergence (embodied/CONSTRAINT_DISCOVERY.md, JustOne), on a back rank.

Eight configurations drawn per episode, three independent facts: a black knight on b7 guarding d8, a black bishop on b5
guarding e8 (and so able to interpose on e8 against a check from d8), the h-pawn on h6 (the king's flight to h7) or on
h7. Relations are perceived as objects of their own: `d8` and `e8` (guarded or open), `flight` (open or none); the black
king is safe, checked or mated. Black answers a check (takes the checker, else steps out, else interposes), and
otherwise recaptures. Rd8 mates only with d8 and e8 open and no flight; Re8 only with e8 open and no flight. In one
configuration (the knight there, no bishop, no flight) exactly one move mates: Re8.

The mind is Gerundelle wanting the black king mated, again and again (polarity and sub-wants on, as rung 1 left it).

Measured: mates in the two configurations that have one; in the JustOne configuration, Re8 (the mate) against Rd8 (taken
by the knight) as the move tried; the conditions learned on Rd8 and Re8; rooks lost.

Run: python -X utf8 rung1c.py [--seeds 10] [--ticks 800] [--arms baseline]
"""
import argparse
import os
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

from chessworld import RUNG1C, RUNG1C_RELATIONS, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402  (fiction's; puts Gerundelle on the path)

WANT = "black_king_g8_safety_mated"
ONE = 2    # the configuration where only Re8 mates
BOTH = 6   # both mate
ARMS = {"baseline": dict(polarity=True, subwants=True), "cost": dict(polarity=True, subwants=True, sub_cost=True),
        "converge": dict(polarity=True, subwants=True, converge=True),
        "converge_cost": dict(polarity=True, subwants=True, converge=True, sub_cost=True),
        "full": dict(polarity=True, subwants=True, converge=True, sub_cost=True, sub_yield=True, sub_tested=True),
        "bridge": dict(polarity=True, subwants=True, converge=True, sub_cost=True, sub_yield=True, sub_tested=True, bridge=True)}


def run(seed, arm, ticks=800, relations=RUNG1C_RELATIONS, clean=False):
    """clean: the want is a mate without losing material (the world's `game` read whole: mate, or costly_mate)."""
    # two of White's moves an episode: a sub-want and the move it was set for (first one: a mind that made its
    # sub-want's fact used up the episode, and the move it was made for never came; seed 5, 326 times)
    w = ChessWorld(RUNG1C, order=seed, seed=seed, reply="answer", moves=2,
                   relations=relations + (("game",) if clean else ()), clean=clean)
    m = GerundelleMind("White", w, want="game_mate" if clean else WANT, want_count=10 ** 6)
    for k, v in ARMS[arm].items():
        setattr(m.agent.mind.p, k, v)
    log, act = [], w.act

    def logged(inv=None, hold=False):
        ep, cfg = len(w.episodes), w.config
        ev = act(inv, hold)
        log.append((ep, cfg, inv[0].split(" ", 1)[-1] if inv else None, ev))
        return ev
    w.act = logged
    try:
        m.run(ticks)
    finally:
        w.close()
    return w, m, log


def measure(w, m, log):
    eps = Counter(w.episodes[:-1])
    mated = Counter(cfg for _, cfg, _, ev in log if any(e.startswith("black_king_g8_safety:") and "-> mated" in e for e in ev))
    first = {}   # configuration -> first move of each episode in it
    for ep, cfg, mv, ev in log:
        if mv and ep not in first:
            first[ep] = (cfg, mv)
    one = Counter(mv for cfg, mv in first.values() if cfg == ONE)
    lost = sum(1 for _, _, _, ev in log if any(e.startswith("white_rook") and "-> captured" in e for e in ev))
    clean, down = Counter(), set()   # mates in an episode where no material was lost before or with the mate
    for ep, cfg, mv, ev in log:
        if any(e.startswith("material:") and e.endswith("-> down") for e in ev):
            down.add(ep)
        if any(e.startswith("black_king_g8_safety:") and "-> mated" in e for e in ev) and ep not in down:
            clean[cfg] += 1
    conds = {}
    for x, sp in m.agent.mind.meta.splits.items():
        for mv in ("Rd8", "Re8"):
            if f" {mv}_push" in x or x.startswith(f"{mv}_push"):
                conds.setdefault(mv, []).append(sp["tag"])
    return dict(episodes=dict(eps), mated=dict(mated), clean=dict(clean), one_first=dict(one), rooks_lost=lost,
                conds=conds,
                pushes=len(m.agent.tried), subs=Counter(k for _, _, k in m.agent.sub_log))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=800)
    ap.add_argument("--arms", default="baseline")
    ap.add_argument("--reply", action="store_true", help="Black's reply perceived as an object of its own (rung 1e)")
    ap.add_argument("--clean", action="store_true", help="the want: a mate without losing material")
    args = ap.parse_args()
    for arm in args.arms.split(","):
        t0, rows = time.time(), []
        for k in range(args.seeds):
            t1 = time.time()
            r = measure(*run(k, arm, args.ticks, RUNG1C_RELATIONS + (("reply",) if args.reply else ()), args.clean))
            rows.append(r)
            print(f"  {arm} seed {k}: mated {r['mated']} of episodes {r['episodes'].get(ONE, 0)} (JustOne) / "
                  f"{r['episodes'].get(BOTH, 0)} (both); JustOne first moves {r['one_first']}; rooks lost "
                  f"{r['rooks_lost']}; conditions {r['conds']}; subs {dict(r['subs'])}  {time.time() - t1:.0f}s",
                  flush=True)
        one_eps = sum(r["episodes"].get(ONE, 0) for r in rows)
        print(f"{arm}: JustOne configuration mated {sum(r['mated'].get(ONE, 0) for r in rows)} of {one_eps} episodes; "
              f"both-mate configuration {sum(r['mated'].get(BOTH, 0) for r in rows)} of "
              f"{sum(r['episodes'].get(BOTH, 0) for r in rows)}; rooks lost {sum(r['rooks_lost'] for r in rows)}; "
              f"mates with no material lost: JustOne {sum(r['clean'].get(ONE, 0) for r in rows)}, both "
              f"{sum(r['clean'].get(BOTH, 0) for r in rows)}  {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
