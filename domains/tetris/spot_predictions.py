"""Spot check the prediction SOVs in a checkpoint, with no slices run (the user, 2026-11-12: "Why can't you just spot check the
prediction SOVs?"). Every prediction instance the mind holds and how the world answered it, by when it was made; for the late ones,
how far ahead they were, the push before them, what was predicted; and, within the mind's own memory of its pushes (its last 64), what
it pushed between a prediction and its due slice.
Run: PYTHONHASHSEED=0 python -X utf8 spot_predictions.py [checkpoint]"""
import collections
import sys

import run  # noqa: F401  (the paths to Gerundelle)
import checkpoint

sys.stdout.reconfigure(encoding="utf-8")
path = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/clean3_13000.pkl"
a, w, t = checkpoint.load(path)
und, mind = a.mind.understanding, a.mind
sovs = und.__dict__.get("prediction_sovs", {})
ins = [dict(i, rel=p.split(":")[1]) for p, s in sovs.items() for i in s["instances"] if i["outcome"]]
print(f"{path}: the mind's tick {mind.t}; prediction SOVs {len(sovs)}; instances answered {len(ins)} {dict(collections.Counter(i['outcome'] for i in ins))}")
edges = [0, 2000, 4000, 6000, 8000, 10000, 11000, 12000, 12500, mind.t + 1]
for lo, hi in zip(edges, edges[1:]):
    part = [i for i in ins if lo <= i["made"] < hi]
    c = collections.Counter(i["outcome"] for i in part)
    after_push = collections.Counter(i["outcome"] for i in part if i["by"] != "wait")
    print(f"  made in ticks {lo:>5}-{hi:<5}: confirmed {c['confirmed']:>4}, rejected {c['rejected']:>4}"
          f" | of those made just after a push of its own: confirmed {after_push['confirmed']}, rejected {after_push['rejected']}")
late = [i for i in ins if i["made"] >= 12000]
ahead = lambda o: sorted(collections.Counter(i["due"] - i["made"] for i in late if i["outcome"] == o).items())
print("from tick 12000, how far ahead (slices: count): confirmed", ahead("confirmed"))
print("from tick 12000, how far ahead (slices: count): rejected ", ahead("rejected"))
print("from tick 12000, rejected: the push before it:", collections.Counter(i["by"].split("|")[0] for i in late if i["outcome"] == "rejected").most_common(6))
print("from tick 12000, what was predicted: rejected", collections.Counter(i["rel"] for i in late if i["outcome"] == "rejected").most_common(5),
      "| confirmed", collections.Counter(i["rel"] for i in late if i["outcome"] == "confirmed").most_common(5))
did = a.__dict__.get("did_log", [])
if did:
    between = lambda i: [inv[0] for tt, inv in did if i["made"] < tt < i["due"]]
    rej = [i for i in ins if i["made"] >= did[0][0] and i["outcome"] == "rejected"]
    conf = [i for i in ins if i["made"] >= did[0][0] and i["outcome"] == "confirmed"]
    print(f"within its memory of its own pushes (its last {len(did)}, ticks {did[0][0]} to {did[-1][0]}):")
    print(f"    rejected {len(rej)}: it pushed between the prediction and its due slice in {sum(1 for i in rej if between(i))}; "
          f"pushes: {collections.Counter(p for i in rej for p in between(i)).most_common()}")
    print(f"    confirmed {len(conf)}: it pushed in between in {sum(1 for i in conf if between(i))}")
    for i in rej[-8:]:
        print(f"      {i['rel']}: made {i['made']}, due {i['due']}, after {i['by'].split('|')[0][:30]}; pushed in between: {between(i)}")
prevents = collections.Counter(c.split("|")[0] for c, rels in und.rel.items() for (r, o), e in rels.items()
                               if r == "prevents" and o.startswith("potential:") and e[1] > 0)
print("pushes it has told itself prevent a predicted effect (links held):", prevents.most_common(6))
print("times it took back its own telling (belied):", len(und.__dict__.get("belied", [])), "| anti-want now:", a.__dict__.get("anti"),
      "| luck", w.luck, "| games", len(w.games))
