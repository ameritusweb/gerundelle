"""From trace_aligning_28000.log: the alignment wants set and met per game (game ends read off clean5_run.log's game counter)."""
import ast
import collections
import re

text = open("trace_aligning_28000.log", encoding="utf-8").read().splitlines()
i = text.index("sub_log after 13000 (every entry):")
late = [ast.literal_eval(l.strip()) for l in text[i + 1:] if l.startswith("   (")]
j = next(k for k, l in enumerate(text) if l.startswith("sub_log for piece_alignment_aligning"))
early = []
for l in text[j + 1:]:
    if not l.startswith("   ("):
        break
    early.append(ast.literal_eval(l.strip()))
ends, last = [], 0
for l in open("clean5_run.log", encoding="utf-8"):
    m = re.match(r"slice (\d+) .*games (\d+),", l)
    if m and int(m.group(2)) > last:
        ends.append(int(m.group(1)))
        last = int(m.group(2))
game = lambda t: sum(t > e for e in ends)
print("game ends (by slice, within 200):", ends)
c = collections.Counter()
for t, g, k in late:
    if g.startswith("piece_alignment") and k in ("set", "met", "dropped"):
        c[(game(t), g[len("piece_alignment_"):], k)] += 1
for t, g, k in early:
    if t <= 13000 and k in ("set", "met", "dropped"):
        c[(game(t), "aligning", k)] += 1
for gm in sorted({k[0] for k in c}):
    print(f"  game {gm}: " + ", ".join(f"{s} {k} {c[(gm, s, k)]}" for s in ("aligning", "straying") for k in ("set", "met", "dropped") if c[(gm, s, k)]))
print("straying wants after 13000:", [(t, k) for t, g, k in late if g == "piece_alignment_straying"])
