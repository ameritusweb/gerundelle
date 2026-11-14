"""What the Go mind feels, and what its decisions rest on (the tetris session's view at slice 10,000: frustration at the piece gone, joy
at held space, more waits). The phases (frustration, anger, anxiety, sadness, joy, curiosity, calm, resignation, gratitude), counted by
where in a game they form: `play` (placements of other kinds on offer at the mind's last turn), `endgame` (only breath-filling
placements and the pass on offer), `loss` (the 12 slices after ten or more of the mind's stones leave in one slice); what each is about
(a point, a stone of the mind's or the other's, a side, the hand, a prediction); which phases reach the top level. Then the decision
view (Params.decision_paths), and the meta layer's targets (Params.meta_targets).
Run: python -u -X utf8 trace_feel.py <seed> [slices]"""
import collections
import sys
import time

import run
from force_world import inv_id
from world import BLACK

sys.stdout.reconfigure(encoding="utf-8")
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
N = int(sys.argv[2]) if len(sys.argv) > 2 else 1100
a, w = run.build(seed, 0.7)
mind, und = a.mind, a.mind.understanding
read, t0 = 0, time.time()
label, loss_until = "play", -1
formed = collections.defaultdict(collections.Counter)    # label -> (kind, about) formed
present = collections.defaultdict(collections.Counter)   # label -> kind in the pool, slice by slice
top = collections.defaultdict(collections.Counter)       # label -> kind among the top-level winners
slices = collections.Counter()
decisions = collections.defaultdict(collections.Counter)
moments = []


def about(anchor):
    r = anchor.split(":")[-1] if anchor.startswith("own:") else anchor
    r = r.split("|")[0]
    if "_push:" in r:
        return "a placement" if r.startswith("place") else "the pass"
    head = r.split("_")[0]
    if r.startswith(("black_breath", "white_breath")):
        return "its own breath" if head == "black" else "the other's breath"
    return {"point": "a point", "hand": "the hand", "potential": "a prediction"}.get(head) or (
        ("a side of " if r.count("_") >= 2 and r.split("_")[2] in ("up", "down", "left", "right") else "") + ("its own stone" if head == "black" else "the other's stone" if head == "white" else head))


for t in range(N):
    pots = w.potentials()
    mind.potentials = pots
    board = w.board()
    mine_before = {s for s, col in w.colour.items() if col == BLACK}
    if pots:
        places = [i for i in w.invitations() if i[0] == "place"]
        inner = [i for i in places if all(board.get(n) == BLACK for n in w.beside(w.target(i)))]
        label = "endgame" if places and len(inner) == len(places) else "play"
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    gone = {s for s in mine_before if s not in w.colour and s not in w.kept}
    if len(gone) >= 10:
        loss_until = t + 12
        moments.append((t, len(gone), len(w.games) + 1))
    lab = "loss" if t <= loss_until else label
    slices[lab] += 1
    for p in rec.get("phases", []):
        _, kind, anchor = p.split(":", 2)
        formed[lab][(kind, about(anchor))] += 1
    for i in mind.pool:
        if i.startswith("phase:"):
            present[lab][i.split(":")[1]] += 1
    for i in (rec["levels"][-1]["winners"] if rec.get("levels") else []):
        if i.startswith("phase:"):
            top[lab][i.split(":")[1]] += 1
    if pots:
        decisions[lab]["wait" if choice is None else "pass" if choice[0] == "pass" else "place"] += 1
    if (t + 1) % 200 == 0:
        print(f"    slice {t + 1} ({time.time() - t0:.0f}s): lost by game {[x['white_took'] for x in w.games]}", flush=True)
print(f"seed {seed}, {N} slices; lost by game {[x['white_took'] for x in w.games]}; slices with ten or more stones lost at once: {moments}")
for lab in ("play", "endgame", "loss"):
    n = max(slices[lab], 1)
    print(f"{lab}: {slices[lab]} slices; on its turn it chose {dict(decisions[lab])}")
    print("    phases formed (kind, about):", formed[lab].most_common(9))
    print("    phases in the pool, per 100 slices:", {k: round(100 * v / n, 1) for k, v in present[lab].most_common()})
    print("    phases among the top-level winners, per 100 slices:", {k: round(100 * v / n, 1) for k, v in top[lab].most_common()})
view = a.decision_view(8)
print("decisions:", view["decisions"])
for kind in ("decision", "thought", "bond", "sov"):
    print(f"    most used {kind}s:", "; ".join(f"{n[:58]} x{c}" for n, c in view[kind]))
tree = a.__dict__.get("decision_tree", {"nodes": {}})
fore = sum(c for (k, n), c in tree["nodes"].items() if k in ("bond", "sov") and any(x in n for x in ("prediction:", "potential", "group+")))
allb = sum(c for (k, n), c in tree["nodes"].items() if k in ("bond", "sov"))
print(f"    bonds and SOV links resting on predictions or potential effects: {fore} of {allb}")
mlog = mind.meta.log
rel = [x for x in mlog if "relevant" in str(x[2])]
print(f"meta targets: relevant formed {sum(1 for x in rel if x[1] == 'formed')}, targeted {sum(1 for x in rel if x[1] == 'op:targeted')}, "
      f"confirmed {sum(1 for x in rel if x[1] == 'confirmed')}, refuted {sum(1 for x in rel if x[1] == 'refuted')}; standing on "
      f"{sorted(k[len('meta:relevant:'):] for k in mind.meta.watch if k.startswith('meta:relevant:'))[:6]}")
print("    concepts targeted most:", collections.Counter(str(x[2]).split("relevant:")[-1][:50] for x in rel if x[1] == "formed").most_common(5))
