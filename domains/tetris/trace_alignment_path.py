"""Replay a window of clean5 from a checkpoint and follow every change of piece_alignment: which path the agent read it through (idle ->
territory.moved, which can contest the region; a watch -> claimed as the push's own, or moved if the world says another did it), and
what opened each contested slot and each alignment want. Nothing is saved; Gerundelle is wrapped on the loaded objects only.
python -u -X utf8 trace_alignment_path.py checkpoints/clean5_<slice>.pkl <slices>"""
import collections
import sys

import checkpoint
import run

sys.stdout.reconfigure(encoding="utf-8")
R = "piece_alignment"
a, w, start = checkpoint.load(sys.argv[1])
for k, v in run.SWITCHES.items():   # (as trace_decisions.py resumes)
    setattr(a.mind.p, k, v)
N = int(sys.argv[2])
terr = a.mind.territory
now = {"mode": None, "events": []}

orig_idle, orig_watch = a.idle, a.watch
def idle(hold=False):
    now["mode"] = "idle"
    diffs = orig_idle(hold=hold)
    for e in diffs:
        if e.startswith(R + ":"):
            now["events"].append(("idle", e))
    return diffs
def watch(diffs, rec):
    now["mode"] = "watch"
    others = set(getattr(w, "others", None) or ())
    for e in diffs:
        if e.startswith(R + ":"):
            now["events"].append(("watch:others" if R in others else "watch:claimed", e))
    return orig_watch(diffs, rec)
a.idle, a.watch = idle, watch
orig_moved, orig_unexp, orig_claimed = terr.moved, terr.unexplained, terr.claimed
def moved(changed, effects=(), context=None):
    if R in set(changed):
        now["events"].append(("register:moved", None))
    return orig_moved(changed, effects, context)
def unexplained(r, e, context=None):
    if r == R:
        now["events"].append(("register:unexplained", e))
    return orig_unexp(r, e, context)
def claimed(c, region, watched, *rest, **kw):
    hit = R in set(watched or ()) or region == R
    out = orig_claimed(c, region, watched, *rest, **kw)
    if hit:
        now["events"].append(("register:claimed", (c, region, bool(terr.rows.get(R, {}).get("failed")))))
    return out
terr.moved, terr.unexplained, terr.claimed = moved, unexplained, claimed

modes = collections.Counter()
paths = collections.Counter()
contests, wants, sub_seen = [], [], len(a.sub_log)
hist_seen = len(terr.rows[R]["history"])
for t in range(start, N):
    row = terr.rows[R]
    before = (row["holder"], row["other_since"], row.get("failed"), row.get("other_last"))
    now["mode"], now["events"] = None, []
    a.mind.potentials = w.potentials()
    a.tick()
    run.after_tick(a, w)
    mode = now["mode"] or ("commit-wait" if a.__dict__.get("committed") else "none")
    modes[mode] += 1
    if any(k in ("idle", "watch:claimed", "watch:others") for k, _ in now["events"]):
        paths[tuple(sorted({k for k, _ in now["events"]}))] += 1
    row = terr.rows[R]
    if row["holder"] != before[0] and row["holder"] == "contested":
        contests.append((t + 1, mode, now["events"], "other_since %s->%s" % (before[1], row["other_since"]), "failed %s->%s" % (before[2], row.get("failed"))))
    for e in a.sub_log[sub_seen:]:
        if e[1].startswith(R):
            wants.append((e, terr.rows[R]["holder"]))
    sub_seen = len(a.sub_log)
    if (t + 1) % 200 == 0:
        print(f"slice {t + 1}: pieces cleared this game {w.pieces_cleared}, rows {w.lines}", flush=True)
print(f"\nwindow {start}..{N}: the agent's slices by mode: {dict(modes)}")
print("slices where piece_alignment changed, by the paths that read it:")
for k, c in paths.most_common():
    print(f"  {c:4d}  {k}")
print(f"\ncontested openings ({len(contests)}):")
for c in contests:
    print("  ", c)
print(f"\nalignment wants in the sub-want log ({len(wants)}):")
for x in wants:
    print("  ", x)
print("\nholder history in the window (to compare with the run's own):", terr.rows[R]["history"][hist_seen:])
print("sub_log in the window:", [e for e in a.sub_log[sub_seen - 0:] if False] or [e for e in a.sub_log if start < e[0] <= N])
