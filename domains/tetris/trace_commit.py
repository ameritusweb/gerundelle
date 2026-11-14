"""The commit push tried from a checkpoint (Params.commit; the user, 2026-11-12: "there would be a new action called 'commit'. It would
be forced to 'watch' until the potential effect is expected. Where it either does or does not occur"). The checkpoint's mind goes on
with commit switched on: how often a commit was on offer, how often it was made and how each came out, how long each watch was, what
the mind holds about commit afterwards, and the predictions confirmed and rejected in the same slices, with and without a commit.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_commit.py [checkpoint] [slices] [--off]     (--off: the same slices with commit off)"""
import collections
import sys
import time

import run  # noqa: F401
import checkpoint

sys.stdout.reconfigure(encoding="utf-8")
args = [x for x in sys.argv[1:] if not x.startswith("--")]
path = args[0] if args else "checkpoints/clean3_13000.pkl"
N = int(args[1]) if len(args) > 1 else 300
a, w, start = checkpoint.load(path)
a.mind.p.commit = "--off" not in sys.argv
und, mind = a.mind.understanding, a.mind
t_first = mind.t
offered = made = turns = 0
choices = collections.Counter()
games0, pieces0, lines0 = len(w.games), w.__dict__.get("pieces_cleared", 0), w.lines
cleared_total = 0
t0 = time.time()
for k in range(N):
    before_pc = w.__dict__.get("pieces_cleared", 0)
    mind.potentials = w.potentials()
    busy = bool(a.watching or a.__dict__.get("committed"))
    choice, rec = a.tick()
    run.after_tick(a, w, ground="--ground" in sys.argv)   # (first only luck was earned here: the rows and clears weren't kept up)
    cleared_total += max(0, w.__dict__.get("pieces_cleared", 0) - before_pc)
    on_offer = [c for c in a.known if c.startswith("commit_push:") and c in mind.inquiry.actions]
    if not busy and mind.inquiry.actions:
        turns += 1
        offered += bool(on_offer)
        choices["commit" if choice is not None and choice[0] == "commit" else "a push on the piece" if choice is not None else "waited"] += 1
    if (k + 1) % 50 == 0:
        print(f"    slice {start + k + 1} ({time.time() - t0:.0f}s): games {len(w.games)}, commits {len([x for x in a.__dict__.get('commit_log', []) if x[2] == 'made'])}", flush=True)
log = a.__dict__.get("commit_log", [])
print(f"from {path}, {N} slices, commit {'on' if mind.p.commit else 'off'}: the mind's turns {turns}; a commit on offer in {offered}; it chose {dict(choices)}")
print("commits:", dict(collections.Counter(x[2] for x in log)), "| slices watched, each:", [x[3] for x in log if x[2] != "made"])
ins = [i for s in und.__dict__.get("prediction_sovs", {}).values() for i in s["instances"] if i["made"] >= t_first and i["outcome"]]
print("predictions answered:", dict(collections.Counter(i["outcome"] for i in ins)),
      "| committed to:", dict(collections.Counter(i["outcome"] for i in ins if i.get("committed"))),
      "| not committed to:", dict(collections.Counter(i["outcome"] for i in ins if not i.get("committed"))))
for c in sorted(x for x in und.rel if x.startswith("commit_push:")):
    rels = {f"{r} {o}": [round(v, 2) for v in e] for (r, o), e in und.rel[c].items() if r in ("causes", "prevents")}
    print(f"what it holds of {c} (seen, told, worked): {rels}")
print(f"games ended {len(w.games) - games0}; rows cleared {w.lines - lines0}; pieces cleared by runs {cleared_total}; luck {w.luck}")
print("pushes made:", collections.Counter(i[0] for i, _, _ in a.pushed[-(sum(choices.values())):]).most_common())
seqs = [dict(q, rel=p.split(":")[1]) for p, s in und.__dict__.get("prediction_sovs", {}).items() for q in s.get("sequences", [])]
print(f"sequences saved in prediction SOVs: {len(seqs)}; by answer {dict(collections.Counter(q['outcome'] for q in seqs))}")
kinds = collections.Counter(("+".join(x for x in q["steps"] if x != "wait") or "watched only", q["outcome"]) for q in seqs)
print("    by the pushes in the sequence:", kinds.most_common(10))
for q in seqs[:6]:
    print(f"    {q['rel']}: made {q['made']}, due {q['due']}, {q['outcome']}: {q['steps'][:14]}{' ...' if len(q['steps']) > 14 else ''}")
