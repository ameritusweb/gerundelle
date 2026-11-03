"""Step 4: do the distinctiveness signatures recognize? Seen once (scene A), each thing's marks are stored as a
profile in the copied Gerundelle mind's storage: a box whose keys are its marks. Seen again elsewhere (scene
B: the same objects, the mugs swapped between places and turned, fresh samples, fresh octree, shuffled thing
ids), the mind attends to one thing at a time, presents its marks, and the stored profiles resonate or not.

    python -X utf8 perception/recognize.py [scene A] [scene B ...]      (default: seed7 seed7_layout3 seed7_layout5)

Resonance is Gerundelle's own rule (Mind.reopen): a box reopens when at least half its keys are filled by
the tick's winners. A key is what a mark looks like and where it sits (colour, place, face: my choice of
the tags that should survive being seen again; size and grain shift with the octree's cells). The share of
keys filled is reported too. The answer key says which object each thing is, for the check only.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from samples import load, name_of, DATA  # noqa: E402
import distinct as D  # noqa: E402
import to_molecules as TM  # noqa: E402
from molecules import Mind, Params, clause  # noqa: E402  (the copy in embodied/gerundelle)

CORE = ("colour:", "place:", "face:")


def core(tags):
    return frozenset(t for t in tags if t.startswith(CORE))


def perceive(name, soft=True):
    """A scene's things with families, each with its mark molecules; and the answer key's object per thing."""
    name = name_of(name)
    s = load(name)
    t = dict(np.load(os.path.join(DATA, f"octree_{name}.npz")))
    sc = D.Scene(t, D.neighbours(t))
    fam = sc.families()
    ms = D.marks(sc, D.distinctiveness(sc, fam))
    mols = TM.molecules(ms, soft=soft)       # what is presented: every reading within the margins
    firm = TM.molecules(ms, soft=False)      # what is stored: each mark's one best reading
    names = [k["name"] for k in s.key]
    things = {}
    for k in range(sc.n):
        if not fam[k]:
            continue
        m = sc.thing == k
        who = names[np.bincount(t["key_object"][m], weights=t["count"][m]).argmax()]
        mine = [(mol, act) for (mol, act), mk in zip(mols, ms) if mk["thing"] == k]
        keys = {core(mol.tags) for (mol, _), mk in zip(firm, ms) if mk["thing"] == k}
        f = sc.frames[k]
        things[k] = dict(who=who, marks=mine, keys=keys, family=fam[k], axis=f["axis"],
                         place=np.array([f["axis"][0], f["base"], f["axis"][1]]),   # where it stands, base height too
                         form=(f["H"], f["reach"], f["area"]))
    for k, th in things.items():   # a profile keeps what tells it apart: keys no other member of its family has
        others = [mol.tags for j in th["family"] if j in things for mol, _ in things[j]["marks"]]
        th["compressed"] = {key for key in th["keys"] if not any(key <= o for o in others)}
    return things


def funded(names, keep=0.75, reach=0.05):
    """Profiles funded over several encounters (receipts): the first scene and encounters in which each thing
    turned where it stood, watched turning, so which thing is which carries over by place in the field (the
    thing whose axis stands within `reach` of where it stood). Each key earns a receipt in every encounter
    that shows it on that thing; a profile keeps the keys with receipts in at least `keep` of the encounters
    (three of four: at half, keys seen twice stayed, and a book whose test views showed one mark of its
    three keys never resonated; 25/30 at half, 28/30 at three of four, the diner mugs 12/12 both).
    What recurs is kept; what was seen once (crazing, texture noise read as a mark) fades."""
    first = perceive(names[0])
    receipts = {k: {key: 1 for key in th["keys"]} for k, th in first.items()}
    for name in names[1:]:
        now = perceive(name)
        for k, th in first.items():
            # the thing standing where it stood: its axis and its base (first the axis alone, and stacked
            # books, one axis, took each other's receipts)
            near = sorted((np.linalg.norm(x["place"] - th["place"]), j) for j, x in now.items())
            if not near or near[0][0] >= reach:
                continue
            for key in now[near[0][1]]["keys"]:
                receipts[k][key] = receipts[k].get(key, 0) + 1
    n = len(names)
    for k, th in first.items():
        th["receipts"] = receipts[k]
        th["funded"] = {key for key, c in receipts[k].items() if c >= keep * n}
    return first


def recognize(profiles, marks, ticks=3):
    """A fresh mind with the stored profiles; one thing's marks presented for a few ticks. Returns the profiles
    that reopened by resonance, and every profile's share of keys filled at its best tick."""
    mind = Mind(Params(sov=False, meta=False))
    for pid, keys in profiles.items():
        if keys:
            mind.box(clause(pid, tags=("profile",)), keys)
    reopened, share = [], {pid: 0.0 for pid in profiles}
    for _ in range(ticks):
        for m, act in marks:
            mind.present(m, act)
        rec = mind.think()
        reopened += [i for i, why in rec["reopened"] if i in profiles and i not in reopened]
        won = [mind.pool[i].tags if i in mind.pool else frozenset() for i in rec["reached"]]
        for pid, keys in profiles.items():
            if keys:
                share[pid] = max(share[pid], sum(any(k <= w for w in won) for k in keys) / len(keys))
    return reopened, share


def accounts(keys, marks):
    """How much of what is seen a profile accounts for: the salience-weighted share of the thing's marks that
    carry one of its keys."""
    total = sum(act for _, act in marks)
    return sum(act for m, act in marks if any(k <= m.tags for k in keys)) / total if total else 0.0


def run(A, field, tests, soft, verbose=True):
    """Of the profiles that reopened by resonance, the thing is recognized as the one that scores highest on
    both counts: the share of its keys found, times the share of what is seen it accounts for (first on the
    share of keys alone, and a one-key profile, one hit, scored 1.00 against a chipped mug's own 0.86).
    A: the stored things; field: which of their key sets is the profile (keys, compressed, funded)."""
    profiles = {f"profile:{k}": th[field] for k, th in A.items()}
    who_A = {f"profile:{k}": th["who"] for k, th in A.items()}
    form_A = {f"profile:{k}": th["form"] for k, th in A.items()}
    if verbose:
        print(f"profiles stored ({field})")
        for pid, keys in profiles.items():
            print(f"  {pid:11} [{who_A[pid]:10}] {len(keys)} keys: " +
                  "; ".join(" ".join(sorted(x.split(':')[1] for x in k)) for k in sorted(keys, key=sorted))[:150])
    summary = []
    for b in tests:
        B = perceive(b, soft=soft)
        if verbose:
            print(f"\nscene {b}: each thing attended to in turn")
        right, outcome = 0, {}
        for k, th in B.items():
            # recognition in context: only the profiles of things of a like form (first every profile, and a book
            # with a yellowish cover was taken for the stoneware mug)
            alike = {p: keys for p, keys in profiles.items() if all(
                abs(a - b) <= 0.3 * max(a, b) for a, b in zip(form_A[p], th["form"]))}
            reopened, share = recognize(alike, th["marks"])
            share = {p: share.get(p, 0.0) for p in profiles}
            score = {p: share[p] * accounts(profiles[p], th["marks"]) for p in profiles}
            got = max(reopened, key=score.get) if reopened else None
            ok = got is not None and who_A[got] == th["who"]
            right += ok
            outcome[th["who"]] = "RIGHT" if ok else f"as {who_A[got]}" if got else "none"
            if verbose:
                ranked = sorted(((p, score[p]) for p in reopened), key=lambda x: -x[1])[:3]
                print(f"  thing {k:2} [{th['who']:10}] {len(th['marks']):2} marks, {len(reopened)} reopened -> "
                      f"{'RIGHT' if ok else 'wrong' if got else '-----'}   best: " +
                      ", ".join(f"{who_A[p]} {v:.2f} (keys {share[p]:.2f})" for p, v in ranked))
        if verbose:
            print(f"  recognized {right} of {len(B)}")
        summary.append((b, right, len(B), outcome))
    return summary


LEARN = ["seed7", "seed7_layout101", "seed7_layout102", "seed7_layout103"]
TESTS = ["seed7_layout3", "seed7_layout5", "seed7_layout7", "seed7_layout9"]

if __name__ == "__main__":
    single = perceive(LEARN[0])
    many = funded(LEARN)
    print("receipts over the learning encounters (the diner mugs):")
    for k, th in many.items():
        if th["who"] in ("mug_a", "mug_b", "mug_c"):
            print(f"  {th['who']}: kept {len(th['funded'])} of {len(th['receipts'])} keys seen;  " + "; ".join(
                f"{' '.join(sorted(x.split(':')[1] for x in key))} x{c}"
                for key, c in sorted(th["receipts"].items(), key=lambda x: -x[1])))
    rows = []
    for soft in (False, True):
        for label, A, field in (("one look", single, "keys"), ("funded over 4 encounters", many, "funded")):
            name = f"{label}, {'soft' if soft else 'hard'} readings"
            print(f"\n################ {name}")
            rows.append((name, run(A, field, TESTS, soft)))
    print("\n################ summary (the diner mugs: mug_a new, mug_b chipped, mug_c printed)")
    for name, summ in rows:
        total = sum(r for _, r, _, _ in summ), sum(n for _, _, n, _ in summ)
        diner = sum(o.get(m) == "RIGHT" for _, _, _, o in summ for m in ("mug_a", "mug_b", "mug_c"))
        print(f"  {name:40} all {total[0]}/{total[1]}, diner mugs {diner}/{3 * len(summ)}:  " + "  ".join(
            f"{b.split('layout')[-1]}: a {o.get('mug_a', '-')[:8]}, b {o.get('mug_b', '-')[:8]}, c {o.get('mug_c', '-')[:8]}"
            for b, r, n, o in summ))
