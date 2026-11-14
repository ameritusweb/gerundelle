"""For each checkpoint: how much told 'prevents' the pushes carry toward potential effects (the old blame: every push made between a
prediction and its failure), how many told 'causes', the anti-wants set so far by kind, and luck. Run: python -u -X utf8 scan_checkpoints.py"""
import collections
import glob
import re
import sys

sys.path.insert(0, ".")
import run  # noqa: F401,E402
import checkpoint  # noqa: E402

for path in sorted(glob.glob("checkpoints/decisions_*.pkl"), key=lambda p: int(re.findall(r"\d+", p)[-1])):
    a, w, t = checkpoint.load(path)
    und = a.mind.understanding
    prev, caus, with_prev = 0.0, 0.0, 0
    for c, rels in und.rel.items():
        if not c.split("|")[0].endswith("_push:piece_falling"):
            continue
        p_ = sum(e[1] for (k, o), e in rels.items() if k == "prevents" and o.startswith("potential:"))
        prev += p_
        caus += sum(e[1] for (k, o), e in rels.items() if k == "causes" and o.startswith("potential:"))
        with_prev += p_ > 0
    anti = collections.Counter(x if x.startswith(("potential", "held_")) else "other" for _, x, k in a.__dict__.get("anti_log", []) if k == "set")
    print(f"{t}: pushes with prevents {with_prev}, told prevents {prev:.0f}, told causes {caus:.0f}; anti-wants set {dict(anti)}; luck {w.luck}",
          flush=True)
