"""Do the potential-effect wants cover for the missing aligning want? Replay a window of clean5 from a checkpoint (nothing saved) and, for
each piece, record: whether a clear was in reach (a push on offer the forces predict a clear from: SovAgent.push_leads), whether the
alignment read aligning, which wants the mind held, which state the alignment was left in by the mind's own pushes, and whether the
piece cleared. python -u -X utf8 trace_clear_wants.py checkpoints/clean5_<slice>.pkl <slices>"""
import collections
import sys

import checkpoint
import run

sys.stdout.reconfigure(encoding="utf-8")
a, w, start = checkpoint.load(sys.argv[1])
for k, v in run.SWITCHES.items():
    setattr(a.mind.p, k, v)
N = int(sys.argv[2])
CLEAR = ("potential:row+", "potential:run+")
is_clear_want = lambda g: bool(g) and (g.startswith(CLEAR) or g == "piece_alignment_aligning")

orig_watch = a.watch
pushed_off = []
def watch(diffs, rec):
    for e in diffs:
        if e == "piece_alignment: aligning -> straying" and a.watching:
            pushed_off.append(a.mind.t)
    return orig_watch(diffs, rec)
a.watch = watch

pieces = []
cur = None
def new_piece():
    return dict(start=a.mind.t, slices=0, reach=0, aligned=0, want_clear=0, want_clear_reach=0, want_straying=0, wants=collections.Counter(),
                pushed_off=0, cleared=False, decisions=0)
cur = new_piece()
placed, lines, nclr = w.placed, w.lines, len(w.__dict__.get("cleared_log", []))
dec = a.__dict__.get("decision_tree", {}).get("decisions", 0)
for t in range(start, N):
    a.mind.potentials = w.potentials()
    n_off = len(pushed_off)
    a.tick()
    run.after_tick(a, w)
    here = a.__dict__.get("push_leads") or {}
    reachset = {str(e) for v in here.values() for e in v if str(e).startswith(CLEAR)}
    reach = bool(reachset)
    held = [g for g in (a.goal, *a.stack) if g]
    match = any(g in reachset for g in held)
    cur["want_match"] = cur.get("want_match", 0) + match
    cur.setdefault("reach_kinds", collections.Counter()).update(reachset)
    cur["slices"] += 1
    cur["reach"] += reach
    cur["aligned"] += w.shown.get("piece_alignment") == "aligning"
    wc = any(is_clear_want(g) for g in held)
    cur["want_clear"] += wc
    cur["want_clear_reach"] += wc and reach
    cur["want_straying"] += "piece_alignment_straying" in held
    for g in held:
        cur["wants"][g.split("&")[0][:40]] += 1
    cur["pushed_off"] += len(pushed_off) - n_off
    d = a.__dict__.get("decision_tree", {}).get("decisions", 0)
    cur["decisions"] += d - dec
    dec = d
    c = len(w.__dict__.get("cleared_log", []))
    if c > nclr:
        cur["cleared"] = True
        nclr = c
    if w.placed != placed:   # the piece came to rest (or the well was set back)
        pieces.append(cur)
        cur = new_piece()
        placed = w.placed
    if (t + 1) % 200 == 0:
        print(f"slice {t + 1}: pieces {len(pieces)}, cleared so far {sum(p['cleared'] for p in pieces)}", flush=True)

def summary(ps, label):
    n = len(ps)
    if not n:
        print(f"  {label}: none")
        return
    cl = sum(p["cleared"] for p in ps)
    print(f"  {label}: {n} pieces, {cl} cleared ({cl / n:.0%})")

print(f"\nwindow {start}..{N}: {len(pieces)} pieces at rest, {sum(p['cleared'] for p in pieces)} with a clear")
reach = [p for p in pieces if p["reach"]]
print(f"clear in reach at some slice: {len(reach)}; aligning at some slice: {sum(1 for p in pieces if p['aligned'])}")
summary([p for p in reach if p.get("want_match")], "reach, the clear in reach was the want held")
summary([p for p in reach if not p.get("want_match") and p["want_clear_reach"]], "reach, a different clear want held (not the one in reach)")
summary([p for p in reach if not p["want_clear_reach"]], "reach, no clear want held while in reach")
print("clears in reach (slices):", sum((p.get("reach_kinds", collections.Counter()) for p in pieces), collections.Counter()).most_common(6))
summary([p for p in pieces if not p["reach"]], "no clear in reach")
summary([p for p in pieces if p["want_straying"]], "a straying want held at some slice")
summary([p for p in pieces if p["pushed_off"]], "a push of the mind's own took the alignment off aligning")
print(f"slices with a clear in reach: {sum(p['reach'] for p in pieces)}; of them with a clear want held: {sum(p['want_clear_reach'] for p in pieces)}")
print("wants held (slices), all pieces:", sum((p["wants"] for p in pieces), collections.Counter()).most_common(10))
print("\nsub_log in the window (to compare with the run's own):", [e for e in a.sub_log if start < e[0] <= N])
print("\nper piece (start, slices, reach slices, aligned slices, clear-want slices, straying-want slices, pushed off, decisions, cleared):")
for p in pieces:
    print(f"  {p['start']:6d} {p['slices']:4d} reach {p['reach']:3d} aligned {p['aligned']:3d} want {p['want_clear']:3d} stray {p['want_straying']:3d} "
          f"match {p.get('want_match', 0):3d} off {p['pushed_off']} dec {p['decisions']:3d} {'CLEARED' if p['cleared'] else ''}  {p['wants'].most_common(2)}")
