"""Rung 1b (chess-sov-plan.md): counterfactual lookahead. Rung 1's world and mind (polarity and sub-wants on), with
Gerundelle's Params.imagine: the planner's model imagines a push whose conditions question is still open, from the board
now, the other side's reply from a source: none (no imagination, rung 1), 'rules' (Black passes: the naive line), or
'stockfish' (Stockfish 15.1 at depth 6: its word, told). Imagined outcomes only score plans; nothing imagined is
written in the register.

Measured: exchanges lost (all, and before the first defended win), the first defended win (episode), defended and
hanging wins, positions imagined per White move.

Run: python -X utf8 rung1b.py [--seeds 10] [--ticks 800] [--sources none,rules,stockfish]
"""
import argparse
import statistics
import sys
import time
from collections import Counter

import rung1


def summary(w, m, log):
    r = rung1.measure(w, m, log)
    first = r["first_defended_win"]
    lost_before = sum(1 for ep, cfg, mv, ev in log if cfg == 0 and (first is None or ep < first)
                      and any(e.startswith("material:") and e.endswith("-> down") for e in ev))
    moves = sum(1 for _, _, mv, _ in log if mv)
    return dict(r, lost_before=lost_before, imagined=w.imagined, moves=moves)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=800)
    ap.add_argument("--sources", default="none,rules,stockfish")
    ap.add_argument("--arm", default="both")
    args = ap.parse_args()
    for src in args.sources.split(","):
        t0, rows = time.time(), []
        for k in range(args.seeds):
            t1 = time.time()
            r = summary(*rung1.run(k, args.arm, args.ticks, None if src == "none" else src))
            rows.append(r)
            print(f"  {src} seed {k}: defended won {r['won'].get(0, 0)} lost {r['lost'].get(0, 0)} "
                  f"(before first win {r['lost_before']}), first defended win ep {r['first_defended_win']}, "
                  f"hanging won {r['won'].get(1, 0)}, imagined {r['imagined']} over {r['moves']} moves  "
                  f"{time.time() - t1:.0f}s", flush=True)
        firsts = [r["first_defended_win"] for r in rows if r["first_defended_win"] is not None]
        print(f"{src:9} defended won {sum(r['won'].get(0, 0) for r in rows)}, lost {sum(r['lost'].get(0, 0) for r in rows)} "
              f"(before the first defended win {sum(r['lost_before'] for r in rows)}); first defended win, median episode "
              f"{statistics.median(firsts) if firsts else '-'} ({len(firsts)}/{len(rows)}); hanging won "
              f"{sum(r['won'].get(1, 0) for r in rows)}; imagined per move "
              f"{sum(r['imagined'] for r in rows) / max(1, sum(r['moves'] for r in rows)):.1f}  {time.time() - t0:.0f}s",
              flush=True)


if __name__ == "__main__":
    main()
