"""Debug (the user, 2026-11-11: from 18000 in watch_mind, "a row coming apart was an anti-want instead of a want"): run from a checkpoint
as watch_mind does (the well set back, its game forgotten) and log each anti-want as it is set, with the regions lost that slice, their
last history event and what the mind last saw them doing. Run: python -X utf8 trace_anti_rows.py [checkpoint slice] [slices]"""
import sys

sys.argv = [sys.argv[0]] + sys.argv[1:]
import watch_mind as wm   # noqa: E402  (its window only opens when run as a script)
import checkpoint  # noqa: E402
import run  # noqa: E402

START = sys.argv[1] if len(sys.argv) > 1 else "18000"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 400
a, w, t = checkpoint.load(f"checkpoints/decisions_{START}.pkl")
wm.amnesia(a, w)
terr = a.mind.territory
read = len(a.__dict__.get("anti_log", []))
seen_hist = {r: len(row["history"]) for r, row in terr.rows.items()}
for k in range(N):
    a.mind.potentials = w.potentials()
    a.tick()
    run.earn_luck(a, w)
    log = a.__dict__.get("anti_log", [])
    if len(log) > read:
        lost = [(r, terr.rows[r]["history"][seen_hist.get(r, 0):], a.__dict__.get("last_seen", {}).get(r))
                for r in terr.rows if any(ev == "lost" for _, ev in terr.rows[r]["history"][seen_hist.get(r, 0):])]
        for e in log[read:]:
            print(f"slice {t + k + 1}: {e} | lost this slice: {lost[:5]} | held: {a.__dict__.get('anti')}, doing {a.__dict__.get('anti_doing')}", flush=True)
    read = len(log)
    seen_hist = {r: len(row["history"]) for r, row in terr.rows.items()}
print("tracked rows:", sorted((r, row["holder"]) for r, row in terr.rows.items() if r.startswith("row_") and row.get("tracked")))
