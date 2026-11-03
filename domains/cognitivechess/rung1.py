"""Rung 1 (chess-sov-plan.md): the defender. A condition learned by contrast, then brought about.

Two configurations drawn per episode, differing in one fact: the knight on d5 defended by the bishop on b7, or hanging
(the bishop on c8). Black recaptures on the square just taken with its least valuable attacker (an authored reply, a
rule of this world). An episode is two of White's moves. Undefended, Rxd5 wins a knight. Defended, Rxd5 loses the
exchange; the combination Bxb7 (Rxb7, even), then Rxd5 wins the knight.

The mind is Gerundelle wanting material up, again and again. Four arms over the same seeds (a seed draws the episodes
and orders the moves): Params.polarity (enable / prevent, the first relation forms) off and on, Params.subwants off and
on.

Measured: the condition learned (the split on Rxd5, its tag, its polarity in the register); losing captures (a move
after which material reads down); wants met in defended episodes (the combination) and in hanging ones; sub-wants set.

Run: python -X utf8 rung1.py [--seeds 10] [--ticks 800] [--arms off,polarity,subwants,both]
"""
import argparse
import os
import statistics
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

from chessworld import RUNG1, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402  (fiction's; puts Gerundelle on the path)

WANT = "material_up"
ARMS = {"off": dict(), "polarity": dict(polarity=True), "subwants": dict(subwants=True),
        "both": dict(polarity=True, subwants=True), "cost": dict(polarity=True, subwants=True, sub_cost=True),
        "converge": dict(polarity=True, subwants=True, converge=True),
        "full": dict(polarity=True, subwants=True, converge=True, sub_cost=True, sub_yield=True, sub_tested=True),
        "bridge": dict(polarity=True, subwants=True, converge=True, sub_cost=True, sub_yield=True, sub_tested=True, bridge=True),
        "c_cost": dict(polarity=True, subwants=True, converge=True, sub_cost=True),
        "c_yield": dict(polarity=True, subwants=True, converge=True, sub_yield=True),
        "c_tested": dict(polarity=True, subwants=True, converge=True, sub_tested=True)}


def run(seed, arm, ticks=800, imagine=None, relations=()):
    """imagine: None, or the source of the other side's reply in imagined lines ('rules', 'stockfish'; rung 1b)."""
    w = ChessWorld(RUNG1, order=seed, seed=seed, reply="recapture", moves=2, imagine=imagine, relations=relations)
    m = GerundelleMind("White", w, want=WANT, want_count=10 ** 6)
    for k, v in ARMS[arm].items():
        setattr(m.agent.mind.p, k, v)
    m.agent.mind.p.imagine = imagine is not None
    log, act = [], w.act   # (episode, configuration, move or None, diffs): every slice

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
    a = m.agent
    eps = Counter(w.episodes[:-1])   # episodes begun and over
    won, lost, combo = Counter(), Counter(), []
    for ep, cfg, mv, ev in log:
        if "material: even -> up" in ev or "material: down -> up" in ev:
            won[cfg] += 1
        if any(e.startswith("material:") and e.endswith("-> down") for e in ev):
            lost[cfg] += 1
    moves = {}
    for ep, cfg, mv, ev in log:
        if mv:
            moves.setdefault(ep, []).append(mv)
    for ep, cfg, mv, ev in log:
        if cfg == 0 and "material: even -> up" in ev:
            combo.append(tuple(moves.get(ep, [])))
    splits = {x.split(" ", 1)[-1].split("_push")[0] + x[x.find("|"):] * ("|" in x): sp["tag"]
              for x, sp in a.mind.meta.splits.items() if "Rxd5" in x}
    und = a.mind.understanding
    polar = sorted((rel, t) for t, rels in und.rel.items() for (rel, c) in rels if rel in ("enables", "prevents")
                   and "Rxd5" in c)
    first = next((ep for ep, cfg, mv, ev in log if cfg == 0 and "material: even -> up" in ev), None)
    return dict(episodes=dict(eps), won=dict(won), lost=dict(lost), combos=Counter(combo), splits=splits, polar=polar,
                subs=Counter(k for _, _, k in a.sub_log), sub_goals=Counter(g for _, g, k in a.sub_log if k == "set"),
                first_defended_win=first, pushes=len(a.tried))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=800)
    ap.add_argument("--arms", default="off,polarity,subwants,both")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--reply", action="store_true", help="Black's reply perceived as an object of its own (rung 1e)")
    args = ap.parse_args()
    for arm in args.arms.split(","):
        t0, rows = time.time(), []
        for k in range(args.seeds):
            r = measure(*run(k, arm, args.ticks, relations=("reply",) if args.reply else ()))
            rows.append(r)
            if args.verbose:
                print(f"  {arm} seed {k}: {r}", flush=True)
        dw = [r["won"].get(0, 0) for r in rows]
        dl = [r["lost"].get(0, 0) for r in rows]
        hw = [r["won"].get(1, 0) for r in rows]
        firsts = [r["first_defended_win"] for r in rows if r["first_defended_win"] is not None]
        learned = Counter(tuple(sorted(set(r["splits"].values()))) for r in rows)
        print(f"{arm:9} defended: won {sum(dw):3} (runs with any {sum(1 for x in dw if x)}/{len(rows)}), "
              f"lost the exchange {sum(dl):3}; hanging: won {sum(hw):3}; first defended win at episode "
              f"{statistics.median(firsts) if firsts else '-'}  {time.time() - t0:.0f}s", flush=True)
        print(f"          Rxd5 split tags {dict(learned)}")
        print(f"          polarity {Counter(tuple(r['polar']) for r in rows).most_common(3)}")
        print(f"          sub-wants {sum((r['subs'] for r in rows), Counter())}  set {sum((r['sub_goals'] for r in rows), Counter()).most_common(4)}")
        print(f"          defended wins by {sum((r['combos'] for r in rows), Counter()).most_common(4)}")


if __name__ == "__main__":
    main()
