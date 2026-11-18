"""Where the want standing_white_up comes from (read from a checkpoint; nothing run): the register's row for standing_white (holder,
history, claims, the states it was seen and held in), the ownership slots on it in the pool, and the sub-want log's entries for it.
python -X utf8 trace_standing_want.py checkpoints/rung4p_full_s0_g<n>.pkl"""
import collections
import sys

import rung4p

sys.stdout.reconfigure(encoding="utf-8")
a, w, b, s = rung4p.load_run(sys.argv[1])
terr = a.mind.territory
row = terr.rows.get("standing_white", {})
print("row standing_white:")
for k in ("holder", "ever", "tracked", "gone", "other", "other_since", "seen_states", "held_states", "claims"):
    v = row.get(k)
    if isinstance(v, dict) and k == "claims":
        v = dict(sorted(v.items(), key=lambda x: -x[1][0])[:6])
    print(f"   {k}: {v}")
print("   history (first 8, last 8):", row.get("history", [])[:8], "...", row.get("history", [])[-8:])
print("   holder changes by kind:", collections.Counter(e for _, e in row.get("history", [])))
print("unclaimable:", getattr(w, "unclaimable", None), "| read_held:", getattr(w, "read_held", None))
print("slots on it in the pool:", [(i, round(m.act, 3)) for i, m in a.mind.pool.items() if i.startswith("own:") and i.endswith(":standing_white")])
print("open slots on it:", [x for x in terr.open_slots() if x[1] == "standing_white"])
sets = [(t, g, k) for t, g, k in a.sub_log if g.startswith("standing_white")]
print(f"sub-want log entries about it: {len(sets)}; kinds {collections.Counter(k for _, _, k in sets)}; first {sets[:4]}; last {sets[-4:]}")
print("held now? goal:", a.goal, "| stack:", a.stack)
