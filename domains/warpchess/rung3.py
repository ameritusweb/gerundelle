"""Rung 3 (LADDER.md): does what it learned carry to new positions? Pairs and the aha. Run: python -X utf8 rung3.py [--seeds 6] [--learn 1000] [--ticks 600]"""
import argparse
import statistics
import sys

from pairs3 import PairMind
from rooms3 import LEARN, LOOSE, SAME
from rung0 import WANT
from warpworld import WarpWorld


def live(fen, room, ticks, seed, mind=None, sealed=None, aha=False):
    w = WarpWorld(fen, seed=seed, moves=2, forces=True)
    a = PairMind(w, room, mind=mind, sealed=sealed, aha=aha)
    for _ in range(ticks):
        if a.goal is None:
            a.goal = WANT
        a.tick()
    a.update()
    made = [x for x in w.log if x[2]]
    half = made[len(made) // 2:]
    a.late = sum(x[3] == "up" for x in half) / max(1, len(half))
    return a


def med(xs):
    return statistics.median(xs) if xs else float("nan")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--learn", type=int, default=1000)
    ap.add_argument("--ticks", type=int, default=600)
    ap.add_argument("--only", type=int, default=None)
    args = ap.parse_args()
    rows = {"same": [], "loose": []}
    for s in ([args.only] if args.only is not None else range(args.seeds)):
        for arm, fen in (("same", SAME), ("loose", LOOSE)):
            first = live(LEARN, "learn", args.learn, s)   # lived again for each arm: the same seed, the same mind
            caps = sum(1 for n, rs in first.pairs.items() if any(r[3] == "captured" for r in rs))
            b = live(fen, arm, args.ticks, s, mind=first.mind, sealed=first.pairs, aha=True)
            xs = list(b.ahas.values())
            multi = [x for x in xs if x["entities"] >= 2]
            capx = [x for x in xs if x["capture"]]
            r = dict(learn_late=first.late, learn_pairs=len(first.pairs), learn_capture_pairs=caps, late=b.late, met=len(b.reached), pairs=len(b.pairs),
                     ahas=len(xs), multi=len(multi), multi_top=sum(x["top"] > 0 for x in multi), multi_score=med([x["first_score"] for x in multi]),
                     capture=len(capx), capture_top=sum(x["top"] > 0 for x in capx), capture_score=max([x["capture_score"] for x in capx], default=0.0),
                     capture_first=min([x["capture_t"] for x in capx], default=None), best=sorted(capx, key=lambda x: -x["capture_score"])[:3])
            rows[arm].append(r)
            print(f"seed {s} {arm}: learn room late {r['learn_late']:.2f}, pairs {r['learn_pairs']} ({caps} with a capture) | new room: late {r['late']:.2f}, wants met {r['met']}, pairs {r['pairs']}; "
                  f"ahas {r['ahas']}, of 2+ pieces {r['multi']} (reached the top {r['multi_top']}, median score {r['multi_score']:.2f}); "
                  f"capture ~ capture {r['capture']} (top {r['capture_top']}, best score {r['capture_score']:.2f}, first at slice {r['capture_first']})", flush=True)
            for x in r["best"]:
                print(f"     {x['capture_score']:.2f} top {x['top']}: {x['a']}  ~  {x['b']}", flush=True)
    for arm, rs in rows.items():
        print(f"{arm}: ahas median {med([r['ahas'] for r in rs])}, of 2+ pieces {med([r['multi'] for r in rs])}, capture ~ capture {med([r['capture'] for r in rs])} "
              f"(seeds with one {sum(r['capture'] > 0 for r in rs)}, reaching the top in {sum(r['capture_top'] > 0 for r in rs)}), best capture score median {med([r['capture_score'] for r in rs]):.2f}")


if __name__ == "__main__":
    main()
