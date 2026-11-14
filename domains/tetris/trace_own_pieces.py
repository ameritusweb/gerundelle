"""Why the mind's own pieces rarely clear (the user, 2026-11-12): from a checkpoint of the clean run, for each piece luck didn't place: when it
formed, whether a clear was within reach (some column and rotation from the top lands it completing a row or run: TetrisWorld.places,
worth), and whether it would clear falling straight down; then how many pushes the mind gave it, whether it cleared where it came to rest,
and how far that was from the nearest place that would have cleared. Run: python -u -X utf8 trace_own_pieces.py [checkpoint] [slices]"""
import collections
import sys

sys.path.insert(0, ".")
import checkpoint  # noqa: E402
import run  # noqa: E402

PATH = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/clean_3000.pkl"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 600
a, w, t = checkpoint.load(PATH)
pieces, cur = [], None
for k in range(N):
    if w.piece is not None and w.piece_blocks and (cur is None or cur["blocks"] != w.piece_blocks):
        shape = w.piece[0]
        places = w.places(shape, w.piece[3])
        clearing = [p for wk, p in places if wk[0] > 0]
        cur = dict(blocks=list(w.piece_blocks), lucky=w.__dict__.get("lucky_piece"), shape=shape, reach=bool(clearing),
                   free=w.completes(w.parts(w.landing(w.piece))) > 0, clear_cols=sorted({p[2] for p in clearing}), pushes=0, start=w.t)
        pieces.append(cur)
    if w.piece is not None and w.doing == "resting" and cur is not None and "rest" not in cur:
        cur["rest"] = w.piece
        cur["cleared"] = w.completes(w.parts(w.piece)) > 0
    a.mind.potentials = w.potentials()
    choice, rec = a.tick()
    run.earn_luck(a, w)
    run.own_clears(a, w)
    run.own_open_rows(a, w)
    if choice is not None and cur is not None and choice[0] in ("shift_left", "shift_right", "rotate", "drop"):
        cur["pushes"] += 1
own = [p for p in pieces if not p["lucky"] and "rest" in p]
print(f"{len(pieces)} pieces formed in {N} slices; luck {w.luck} ({w.earned} earned); the mind's own (not lucky): {len(own)}")
print("wants on predictions: set", sum(1 for _, g, k in a.sub_log if k == "set" and g.startswith("potential:")), "met", sum(1 for _, g, k in a.sub_log if k == "met" and str(g).startswith("potential:")))
c = collections.Counter((("clear in reach" if p["reach"] else "no clear in reach"),
                         ("falls into it" if p["free"] else "doesn't fall into it"),
                         ("pushed" if p["pushes"] else "not pushed"),
                         ("cleared" if p["cleared"] else "no clear")) for p in own)
for key, n in sorted(c.items(), key=lambda x: -x[1]):
    print(f"  {n:3d}  {', '.join(key)}")
missed = [p for p in own if p["reach"] and not p["cleared"]]
for p in missed[:8]:
    print(f"  missed: {p['shape']} formed slice {p['start']}, pushes {p['pushes']}, rested at column {p['rest'][2]} rotation {p['rest'][1]}; "
          f"would have cleared from columns {p['clear_cols']}")
