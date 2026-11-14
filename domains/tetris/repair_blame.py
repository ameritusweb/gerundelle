"""Repair a checkpoint of the old blame (the user, 2026-11-11: "make the repaired checkpoint"). Before the fix, when a prediction failed,
every push the mind made between the prediction and its due slice was told it prevents the potential effect, and its decision path was
marked failed; by slice 18,000 all four pushes carried 333 such receipts, and a lost prediction's anti-want pushed every push down,
the clearing ones too. This takes out exactly that output: each push's told `prevents` toward a potential effect, and the failed marks
on the decision paths (written by the same rule). Everything else the mind learned stays. The original checkpoint is left as it is.

Run: python -X utf8 repair_blame.py [slice, default 18000]  ->  checkpoints/decisions_<slice>_repaired.pkl
"""
import sys

sys.path.insert(0, ".")
import run  # noqa: F401,E402  (Gerundelle on the path, as the checkpoints were saved)
import checkpoint  # noqa: E402

START = sys.argv[1] if len(sys.argv) > 1 else "18000"
a, w, t = checkpoint.load(f"checkpoints/decisions_{START}.pkl")
und = a.mind.understanding
removed = 0
for c, rels in und.rel.items():
    if not c.split("|")[0].endswith("_push:piece_falling"):
        continue
    for key in [k for k in rels if k[0] == "prevents" and k[1].startswith("potential:")]:
        removed += 1
        del rels[key]
tree = a.mind.__dict__.get("decision_tree")
failed = sum((tree or {}).get("failed", {}).values())
if tree is not None:
    tree["failed"] = {}
out = f"checkpoints/decisions_{START}_repaired.pkl"
checkpoint.save(a, w, t, out)
print(f"slice {t}: removed {removed} told prevents relations from the pushes and {failed} failed marks on decision paths; saved {out}")
