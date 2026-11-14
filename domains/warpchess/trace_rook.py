"""Rung 1d: when the rook can take the knight, what happens in its own mind, and in the main mind? Run: python -X utf8 trace_rook.py [seed]"""
import collections
import sys

from rung0 import WANT  # (puts Gerundelle on the path)
from molecules import is_exp, is_meta, is_own, is_phase, is_sov
from pieceminds import MainMind
from warpworld import RUNG1_TWO, WarpWorld


def track(i):
    return "meta" if is_meta(i) else "sov" if is_sov(i) else "exp" if is_exp(i) else "own" if is_own(i) else "phase" if is_phase(i) else "thought"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    w = WarpWorld(RUNG1_TWO, seed=seed, moves=2, forces=True)
    a = MainMind(w, pieces=True)
    rook = next(pm for p, pm in a.pieces.items() if "rook" in p)
    windows, agg, shown = 0, collections.Counter(), 0
    for t in range(1000):
        if a.goal is None:
            a.goal = WANT
        target = w.where["black_knight_Rd4"]
        caps = {l: m for l, m in w.offers().items() if w.moved == 1 and target is not None and m.final_square == target and w.ids_at(m.from_square) == rook.piece}
        if not caps:
            a.tick()
            continue
        label = next(iter(caps))
        cid = f"{label}_push:{rook.piece}_present"
        state = (list(a.queue), a.running)
        offered_before = len(a.offered)
        choice, rec = a.tick()
        windows += 1
        rr = rook.last_rec
        r_top = rr["levels"][-1]["winners"]
        r_lv0 = rr["levels"][0]
        put = [c for _, p, c in a.offered[offered_before:] if p == rook.piece]
        agg["rook: capture in its pool" if cid in rook.mind.pool else "rook: capture NOT in its pool"] += 1
        agg["rook: capture won its top level" if cid in r_top else "rook: capture didn't win its top"] += 1
        agg["rook: put the capture forward" if cid in put else "rook: put other moves forward"] += 1
        agg["main: queue busy" if state[0] or state[1] else "main: queue free"] += 1
        agg["main: played the capture" if choice and choice[0] == label else "main: played something else" if choice else "main: no move"] += 1
        if shown < 6:
            shown += 1
            print(f"t{t}: capture {label}; rook goal {rook.goal}, rook plan {rook.plan_step(rook.perceive()[1], 500, 3)}")
            print(f"   rook: capture in pool {cid in rook.mind.pool}, level-0 bid {r_lv0['bids'].get(cid, float('nan')):.2f}, reached {rr['reached'].get(cid)}; "
                  f"its top {[i[:42] for i in r_top][:5]}")
            print(f"   rook level-0 thoughts: {[i[:34] for i in r_lv0['winners'] if track(i) == 'thought'][:6]}; experiments {rr['experiments'][:2]}")
            print(f"   rook put forward {[c.split('_push')[0] for c in put]}; main queue {state[0][:1]} running {str(state[1])[:60]}; main played {choice and choice[0]}")
    print(f"\nseed {seed}: ticks with the rook able to take the knight: {windows}")
    for k, v in sorted(agg.items()):
        print(f"  {k}: {v}")
    print(f"  the rook's want: {rook.goal}; met {len(rook.reached)}; what it learned about the capture: "
          f"{[(r, o) for c, rels in rook.mind.understanding.rel.items() if 'Rd4' in c for (r, o), e in rels.items() if r == 'causes'][:4]}")


if __name__ == "__main__":
    main()
