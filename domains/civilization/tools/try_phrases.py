"""Read candidate sentences back with fiction's reader: python -X utf8 tools/try_phrases.py <file of 'text<TAB>shape'>."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "fiction"))
from measure import round_trip  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
rows = [line.rstrip("\n").split("\t") for line in open(sys.argv[1], encoding="utf-8") if line.strip()]
for r in round_trip([(i, t, s) for i, (t, s) in enumerate(rows)]):
    print("ok  " if r["ok"] else "MISS", r["text"], "->", r["reading"] or r["why"])
