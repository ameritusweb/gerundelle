"""Rung 7: the best story per ending, printed and read back (round-trip), with the reader's curve."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung7  # noqa: E402
from measure import evaluate  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
rows = rung7.search(rung7.forest())
best = {}
for r in rows:
    best.setdefault(r["ending"], r)
for e, r in best.items():
    m = evaluate(r["scene"], r["sentences"])
    s = r["state"]
    print(f"== {e}: cast {s.cast} moves {s.moves} value {r['value']} held {r['held']} rise {r['rise']} "
          f"round-trip {m['round_trip']:.2f} judge {m['matched_share']:.2f} variety {m['variety']:.2f} drops {r['drops']}")
    print(" ".join(t for _, t, _ in r["sentences"]))
    for row in m["rows"]:
        if not row["ok"]:
            print(f"   MISS {row['text']}  intended {row['shape']}; read {row['readings'] or row['why']}")
    print()
