"""Why the aligning want went away in clean5: read a checkpoint's own records (no slices run). python -u -X utf8 trace_aligning.py checkpoints/clean5_<slice>.pkl"""
import collections
import sys

import checkpoint
import run  # noqa: F401  (sets the Gerundelle path)

sys.stdout.reconfigure(encoding="utf-8")
a, w, t = checkpoint.load(sys.argv[1])
KEY = "piece_alignment_aligning"
print(f"checkpoint at slice {t}; mind.t {a.mind.t}")
print("games (pieces placed, rows cleared):", w.games, "| this game: placed", w.placed, "lines", w.lines)
print("failed_subs:", sorted(a.failed_subs))
print("goal", a.goal, "| stack", a.stack)
print(f"\nsub_log for {KEY}:")
for e in a.sub_log:
    if KEY in str(e[1]):
        print("  ", e)
print("\nsub_log kinds per 2000 slices, every want:")
by = collections.defaultdict(collections.Counter)
for tt, g, k in a.sub_log:
    by[tt // 2000 * 2000][k] += 1
for b in sorted(by):
    print(f"  {b:6d}: {dict(by[b])}")
print("\nwants set, per 2000 slices (top 4):")
setby = collections.defaultdict(collections.Counter)
for tt, g, k in a.sub_log:
    if k == "set":
        setby[tt // 2000 * 2000][g] += 1
for b in sorted(setby):
    print(f"  {b:6d}: {setby[b].most_common(4)}")
print("\ndropped after 13000:")
for tt, g, k in a.sub_log:
    if k == "dropped" and tt > 13000:
        print(f"  {tt}: {g}")
print("\nsub_log after 13000 (every entry):")
for e in a.sub_log:
    if e[0] > 13000:
        print("  ", e)
terr = a.mind.territory
row = terr.rows.get("piece_alignment")
print("\nterritory row piece_alignment:", None if row is None else {k: v for k, v in row.items()})
print("dormant:", "piece_alignment" in terr.__dict__.get("dormant", {}))
print("slots in the pool on piece_alignment:", [(i, round(m.act, 3)) for i, m in a.mind.pool.items() if i.startswith("own:") and i.endswith(":piece_alignment")])
print("open slots on piece_alignment:", [s for s in terr.open_slots() if s[1] == "piece_alignment"])
print("world state of piece_alignment:", w.states().get("piece_alignment"))
rel = [x for x in a.mind.meta.log if KEY in str(x[2]) and "relevant" in str(x[2])]
print(f"\nmeta relevant entries about {KEY}: {len(rel)}, first {rel[:1]}, last {rel[-3:]}")
