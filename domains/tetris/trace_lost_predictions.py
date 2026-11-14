"""Why the mind keeps losing its predictions (the user, 2026-11-12, watching checkpoints/clean3_13000.pkl: "it keeps saying lost
prediction and sadness; what's causing all the bad predictions?"). From a checkpoint, slice by slice: each prediction the world's
forces gave the mind (potential_effects: what follows if nothing pushes), how far ahead it was, whether it was confirmed or rejected,
and for the rejected ones what happened between its making and its due slice: the pushes the mind made itself, by name, or none.
And on each of the mind's turns with a prediction standing: whether it pushed or waited, the anti-want held, and how its pushes and
the wait stood at the top level.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_lost_predictions.py [checkpoint] [slices]"""
import collections
import sys
import time

import checkpoint
import run

sys.stdout.reconfigure(encoding="utf-8")
path = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/clean3_13000.pkl"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 250
a, w, start = checkpoint.load(path)
und, mind = a.mind.understanding, a.mind
t_first = mind.t
pushes = []          # (the mind's tick, the push)
turns = collections.Counter()
by_anti = collections.Counter()
top_when_standing = collections.Counter()
t0 = time.time()
for k in range(N):
    standing = len(a.__dict__.get("predicted", {}))
    offers = w.invitations()
    anti = a.__dict__.get("anti")
    mind.potentials = w.potentials()
    tick = mind.t
    choice, rec = a.tick()
    run.earn_luck(a, w)
    if choice is not None:
        pushes.append((tick, choice[0]))
    if offers and not a.watching or choice is not None:
        key = ("a prediction standing" if standing else "none standing", "pushed" if choice is not None else "waited")
        turns[key] += 1
        if standing:
            by_anti[("anti-want held" if anti else "no anti-want", "pushed" if choice is not None else "waited")] += 1
            lv = rec["levels"][-1] if rec.get("levels") else None
            if lv:
                top_when_standing["a push among the top winners" if any("_push:" in i for i in lv["winners"]) else "no push among the top winners"] += 1
    if (k + 1) % 50 == 0:
        print(f"    slice {start + k + 1} ({time.time() - t0:.0f}s): games {len(w.games)}, predictions answered so far "
              f"{len(a.__dict__.get('prediction_answers', []))}", flush=True)
ins = [i for s in und.__dict__.get("prediction_sovs", {}).values() for i in s["instances"] if i["made"] >= t_first and i["outcome"]]
print(f"from {path}, {N} slices: predictions made and answered {len(ins)}: {dict(collections.Counter(i['outcome'] for i in ins))}")
print("how far ahead (slices), confirmed:", sorted(collections.Counter(i["due"] - i["made"] for i in ins if i["outcome"] == "confirmed").items()))
print("how far ahead (slices), rejected: ", sorted(collections.Counter(i["due"] - i["made"] for i in ins if i["outcome"] == "rejected").items()))
between = lambda i: [p for tt, p in pushes if i["made"] < tt < i["due"]]
rej = [i for i in ins if i["outcome"] == "rejected"]
print(f"rejected, by what the mind did between the prediction and its due slice: pushed {sum(1 for i in rej if between(i))}, pushed nothing {sum(1 for i in rej if not between(i))}")
print("    the pushes it made in between (each counted once a prediction):", collections.Counter(p for i in rej for p in set(between(i))).most_common())
print("    how many pushes in between:", sorted(collections.Counter(len(between(i)) for i in rej).items()))
conf = [i for i in ins if i["outcome"] == "confirmed"]
print(f"confirmed: pushed in between {sum(1 for i in conf if between(i))}, pushed nothing {sum(1 for i in conf if not between(i))}")
print("what was predicted (relative effect), rejected:", collections.Counter(i["sov"].split(":")[1] for i in rej).most_common(6))
print("what was predicted (relative effect), confirmed:", collections.Counter(i["sov"].split(":")[1] for i in conf).most_common(6))
print("the mind's turns:", dict(turns))
print("with a prediction standing, by the anti-want:", dict(by_anti))
print("with a prediction standing, the top level:", dict(top_when_standing))
print("the pushes it made:", collections.Counter(p for _, p in pushes).most_common())
none = [i for i in rej if not between(i)]
if none:
    print("rejected with no push of the mind's in between (the first few): ", [(i["sov"].split(":")[1], i["made"], i["due"], i["by"][:40]) for i in none[:5]])
log = a.__dict__.get("anti_log", [])
print("anti-wants in the run so far:", collections.Counter((r[:34], kk) for _, r, kk in log).most_common(6))
phases = collections.Counter(i.split(":")[1] for i in mind.pool if i.startswith("phase:"))
print("phases in the pool now:", dict(phases), "| games:", len(w.games), "| luck", w.luck)
