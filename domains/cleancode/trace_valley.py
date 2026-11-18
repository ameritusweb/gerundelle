"""Why a conditioned understanding does not reach the decision (LADDER.md rung 2, "the planner's step through the valley is the
open organ"): run one orbiting problem and, at every slice where the mind stands one turn from a fully-held setting, name the
closing push and its anatomy — its bid at the top (split variants included), whether it won, what won instead, the anti-want
pressing it, its potential — plus who rules the tournament over the run (what kind of molecule wins the top), whether the
planner ever engages (the sub-want stack), and the commits made.

Run: PYTHONHASHSEED=0 python -u -X utf8 trace_valley.py [--seed 2] [--slices 300] [--from 40]
"""
import collections
import itertools
import sys

import graph as g
import run

sys.stdout.reconfigure(encoding="utf-8")
SEED = int(next((x.split("=")[1] for x in sys.argv if x.startswith("--seed=")), "2"))
N = int(next((x.split("=")[1] for x in sys.argv if x.startswith("--slices=")), "300"))
FROM = int(next((x.split("=")[1] for x in sys.argv if x.startswith("--from=")), "40"))

a, w = run.build("2", SEED, dream=True)
und, mind, told = a.mind.understanding, a.mind, a.mind.p.credulity
sizes = [len(g.wheel(k)) for k in w.p.shape.kinds]
full = [pos for pos in itertools.product(*(range(n) for n in sizes))
        if all(g.territory(w.p.reading(list(pos))).values())]
print(f"seed {SEED} problem 1: fully-held {full}, start {w.p.start}, correct {w.p.correct}")

kinds = collections.Counter()
stack_seen = commits = 0
for t in range(N):
    a.mind.potentials = w.potentials()
    choice, rec = a.tick()
    run.give(a, w)
    if w.solved:
        print(f"solved at slice {t + 1}: settled {w.solved[0]['settled']}")
        break
    lv = rec["levels"][-1] if rec.get("levels") else {"bids": {}, "winners": []}
    for i in lv["winners"][:1]:
        kinds[i.split(":")[0]] += 1
    stack_seen += bool(a.__dict__.get("stack"))
    commits = len(a.__dict__.get("commit_log", []))
    pos = [x % n for x, n in zip(w.pos, sizes)]
    d, h = min(((sum(min((x - y) % n, (y - x) % n) for x, y, n in zip(pos, hh, sizes)), hh) for hh in full),
               key=lambda z: z[0])
    if t + 1 < FROM or d > 1 or w.unread:
        continue
    c = next(i for i in range(3) if pos[i] != h[i])
    fwd = (h[c] - pos[c]) % sizes[c] == 1
    iid = f"{'turning_forward' if fwd else 'turning_back'}_push:conn_{c}_{w.shown[f'conn_{c}']}"
    bid = max((v for i, v in lv["bids"].items() if i.split("|")[0] == iid), default=None)
    won = any(i.split("|")[0] == iid for i in lv["winners"])
    targets = set(mind.__dict__.get("anti_targets") or ())
    rel = und.rel.get(iid, {})
    threat = [(o, round(e[0] + e[2] + told * e[1], 2)) for (k, o), e in rel.items()
              if k in ("causes", "prevents") and o in targets and e[0] + e[2] + told * e[1] > 0]
    splits = [i for i in lv["bids"] if i.startswith(iid + "|")]
    print(f"s{t + 1} AT d1 ({pos} -> {list(h)}): closer {iid}")
    print(f"    potential {mind.potentials.get(iid)}, bid {bid and round(bid, 2)}, won {won}, split-variants {splits[:2]}")
    print(f"    threatens anti targets {threat[:3]}; chose {choice[0] if choice else None}; "
          f"top winners {lv['winners'][:4]}; stack {len(a.__dict__.get('stack') or ())}")
print(f"\ntop-winner kinds over the run: {kinds.most_common(8)}")
print(f"slices with a sub-want stack: {stack_seen}; commits logged: {commits}")
