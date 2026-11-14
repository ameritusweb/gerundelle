"""From trace_aligning_28000.log's sub_log after 13000: how long each potential:* want was held, and how it ended."""
import ast

text = open("trace_aligning_28000.log", encoding="utf-8").read().splitlines()
i = text.index("sub_log after 13000 (every entry):")
ents = [ast.literal_eval(l.strip()) for l in text[i + 1:] if l.startswith("   (")]
open_ = {}
for t, g, k in ents:
    if not g.startswith("potential:"):
        continue
    if k == "set":
        open_[g] = t
    elif g in open_:
        print(f"  {g}: set {open_[g]}, {k} {t}  (held {t - open_.pop(g)} slices)")
for g, t in open_.items():
    print(f"  {g}: set {t}, still held at the checkpoint (28000): {28000 - t} slices")
print("every ending kind seen for potential wants:", sorted({k for t, g, k in ents if g.startswith("potential:") and k != "set"}))
