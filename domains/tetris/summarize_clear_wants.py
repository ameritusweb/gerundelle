"""Re-read trace_clear_wants_<slice>.log with each clear given to the piece that made it. A piece's clear is computed in the slice it comes
to rest (world.py act, the resting branch) and its blocks leave the next slice, which trace_clear_wants.py had already counted under the
next piece: so the CLEARED mark moves back one piece. python -X utf8 summarize_clear_wants.py trace_clear_wants_<slice>.log"""
import re
import sys

lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
pat = re.compile(r"^\s+(\d+)\s+(\d+) reach\s+(\d+) aligned\s+(\d+) want\s+(\d+) stray\s+(\d+) match\s+(\d+) off (\d+) dec\s+(\d+) ?(CLEARED)?\s+(.*)$")
ps = []
for l in lines:
    m = pat.match(l)
    if m:
        ps.append(dict(start=int(m[1]), slices=int(m[2]), reach=int(m[3]), aligned=int(m[4]), want=int(m[5]), stray=int(m[6]),
                       match=int(m[7]), dec=int(m[9]), marked=bool(m[10]), wants=m[11]))
for i, p in enumerate(ps):
    p["cleared"] = ps[i + 1]["marked"] if i + 1 < len(ps) else None   # (the last piece's clear, if any, came after the window)
ps = [p for p in ps if p["cleared"] is not None]
def line(sel, label):
    n = len(sel)
    c = sum(p["cleared"] for p in sel)
    print(f"  {label}: {n} pieces, {c} cleared" + (f" ({c / n:.0%})" if n else ""))
print(f"{sys.argv[1]}: {len(ps)} pieces (the window's last left out: its clear would fall after the window)")
reach = [p for p in ps if p["reach"]]
line(reach, "a clear in reach at some slice")
line([p for p in reach if p["match"]], "  ... and the want held was the clear in reach")
line([p for p in reach if not p["match"]], "  ... and the want held was not the clear in reach")
line([p for p in ps if not p["reach"]], "no clear in reach")
line([p for p in ps if p["stray"]], "a straying want held at some slice")
root = {}
for p in ps:
    k = p["wants"].split("'")[1] if "'" in p["wants"] else "(none)"
    root.setdefault(k, []).append(p)
print("  by the want held longest during the piece:")
for k, sel in sorted(root.items(), key=lambda x: -len(x[1])):
    line(sel, f"    {k}")
