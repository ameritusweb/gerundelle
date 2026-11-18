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
PLANS = False   # (PLAN.md step 2: plansworld.PlansWorld, the opponent's plans as territory)
SHARED = False   # (PLAN.md step 1: the shared switch set, tetris/run.py's SWITCHES, every user-decided switch, plus affords_relation)
TETRIS_RUN = __import__("paths").domain('tetris', 'run.py')


def _here(path):
    """The same file under WSL (/mnt/e/...) when the Windows drive path isn't there (2026-11-16, the fork measurements)."""
    import os
    return path if os.path.exists(path) else path.replace("E:/", "/mnt/e/")


def shared_switches(path=TETRIS_RUN):
    """The switch set as tetris/run.py writes it (as go/run.py reads it), plus Params.affords_relation (2026-11-13)."""
    import ast
    tree = ast.parse(open(_here(path), encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "SWITCHES" for t in node.targets):
            return {**{k.arg: ast.literal_eval(k.value) for k in node.value.keywords}, "affords_relation": True}
    raise ValueError(f"no SWITCHES in {path}")


def go_switches(path=__import__("paths").domain('go', 'run.py')):
    """go/run.py's GO_SWITCHES (the switches the user ruled on for Go's territory)."""
    import ast
    tree = ast.parse(open(_here(path), encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "GO_SWITCHES" for t in node.targets):
            return {k.arg: ast.literal_eval(k.value) for k in node.value.keywords}
    raise ValueError(f"no GO_SWITCHES in {path}")


def run(seed, ticks, pieces):
    if PLANS:
        from plansworld import PlansWorld
        w = PlansWorld(RUNG1_TWO, seed=seed, moves=2)
    else:
        w = WarpWorld(RUNG1_TWO, seed=seed, moves=2, forces=True)
    a = (OfferedMainMind if OFFERED else MainMind)(w, pieces=pieces, forces=FORCES)
    for ag in [a] + list(a.pieces.values()):
        ag.mind.p.imagined_tournament = IMAGINED
        ag.mind.p.want_site = WANT_SITE
        ag.mind.p.setup_support = SETUP
        if SHARED:
            for k, v in shared_switches().items():
                setattr(ag.mind.p, k, v)
        if PLANS:   # (and Go's territory switches, the user's rulings of 2026-11-12/13: go/run.py GO_SWITCHES)
            for k, v in go_switches().items():
                setattr(ag.mind.p, k, v)
    first = None
    for _ in range(ticks):
        if a.goal is None:
            a.goal = WANT
        a.tick()
        if PLANS:
            import plansworld
            plansworld.give(a, w)
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
    ap.add_argument("--shared", action="store_true", help="PLAN.md step 1: tetris/run.py's SWITCHES and affords_relation in every mind")
    ap.add_argument("--plans", action="store_true", help="PLAN.md step 2: the opponent's plans as the mind's territory (plansworld.py)")
    args = ap.parse_args()
    global FORCES, OFFERED, IMAGINED, WANT_SITE, SETUP, SHARED, PLANS
    FORCES, OFFERED, IMAGINED, WANT_SITE, SETUP = args.potential, args.offered, args.imagined, args.want_site, args.setup_support
    SHARED, PLANS = args.shared, args.plans
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
