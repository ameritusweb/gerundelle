"""Rung 1d (LADDER.md): a mind for each piece, on the two-move position. Run: python -X utf8 rung1d.py [--seeds 6] [--ticks 1000] [--arm pieces|control]"""
import argparse
import collections
import statistics
import sys

from rung0 import WANT  # (puts Gerundelle on the path)
from pieceminds import MainMind, OfferedMainMind
from warpworld import RUNG1_TWO, WarpWorld


FORCES = False
OFFERED = False
IMAGINED = False
WANT_SITE = False
SETUP = False


def run(seed, ticks, pieces):
    w = WarpWorld(RUNG1_TWO, seed=seed, moves=2, forces=True)
    a = (OfferedMainMind if OFFERED else MainMind)(w, pieces=pieces, forces=FORCES)
    for ag in [a] + list(a.pieces.values()):
        ag.mind.p.imagined_tournament = IMAGINED
        ag.mind.p.want_site = WANT_SITE
        ag.mind.p.setup_support = SETUP
    first = None
    for _ in range(ticks):
        if a.goal is None:
            a.goal = WANT
        a.tick()
        if first is None and a.reached:
            first = len(a.pushed)
    made = [x for x in w.log if x[2]]
    half = made[len(made) // 2:]
    rook = next((pm for p, pm in a.pieces.items() if "rook" in p), None)
    capture_offered = sum(1 for _, p, c in a.offered if "rook" in p and "Rd4" in c.split("_push")[0])
    return dict(first=first, tries=len(made), late=sum(x[3] == "up" for x in half) / max(1, len(half)), met=len(a.reached),
                rook_alone=len(rook.reached) if rook else None, capture_offered=capture_offered,
                offered=collections.Counter(p.split("_")[1] for _, p, _ in a.offered))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--ticks", type=int, default=1000)
    ap.add_argument("--arm", default="pieces")
    ap.add_argument("--potential", action="store_true")
    ap.add_argument("--offered", action="store_true")
    ap.add_argument("--imagined", action="store_true", help="Params.imagined_tournament in the main mind and the piece minds")
    ap.add_argument("--only", type=int, default=None)
    ap.add_argument("--want-site", action="store_true", help="Params.want_site in every mind")
    ap.add_argument("--setup-support", action="store_true", help="Params.setup_support in every mind")
    args = ap.parse_args()
    global FORCES, OFFERED, IMAGINED, WANT_SITE, SETUP
    FORCES, OFFERED, IMAGINED, WANT_SITE, SETUP = args.potential, args.offered, args.imagined, args.want_site, args.setup_support
    rows = []
    for s in ([args.only] if args.only is not None else range(args.seeds)):
        r = run(s, args.ticks, args.arm == "pieces")
        rows.append(r)
        print(f"{args.arm} seed {s}: first want at try {r['first']}, tries {r['tries']}, wants met {r['met']}, winning share late {r['late']:.2f}, "
              f"rook reached 'owns' {r['rook_alone']}, the rook put the knight capture forward {r['capture_offered']} times, ideas by piece {dict(r['offered'])}", flush=True)
    ok = [r["first"] for r in rows if r["first"]]
    med = statistics.median
    print(f"{args.arm}: found in {len(ok)}/{len(rows)}; first want at try median {med(ok) if ok else '-'}; winning share late median {med(r['late'] for r in rows):.2f}")


if __name__ == "__main__":
    main()
