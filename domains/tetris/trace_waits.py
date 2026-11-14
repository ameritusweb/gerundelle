"""Trace, from a checkpoint (default the slice-14,000 one): (1) the block SOV molecules most often behind decisions, where their block is and
why they win; (2) the waits: the anti-want held, what won the top level instead of a push, and how much the anti-want lowered each push on
offer. Run: python -u -X utf8 trace_waits.py [checkpoint] [slices]"""
import collections
import sys

import checkpoint
import run  # noqa: I001  (sets up the path to Gerundelle first)
import molecules

sys.stdout.reconfigure(encoding="utf-8")
path = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/decisions_14000.pkl"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 150
a, w, t0 = checkpoint.load(path)
for k, v in run.SWITCHES.items():
    setattr(a.mind.p, k, v)
m, u, terr = a.mind, a.mind.understanding, a.mind.territory

# (1) the block SOV molecules behind decisions
tree = m.__dict__.get("decision_tree", {"nodes": {}})
top_sov = sorted(((n, c) for (k, n), c in tree["nodes"].items() if k == "thought" and n.startswith("sov:block_")), key=lambda x: -x[1])[:3]
present = set(w.states())
print(f"at slice {t0}:")
for n, c in top_sov:
    c_ = n[4:]
    b = c_.rsplit("_", 1)[0]
    row = terr.rows.get(b)
    print(f"  {n}: behind {c} decisions; block {b} in the world now: {b in present}; kept (left by a clear): {b in getattr(w, 'kept', ())}; "
          f"territory: {'row ' + str(row['holder']) if row else ('stored' if b in terr.__dict__.get('dormant', {}) else 'none')}; "
          f"in the pool: {n in m.pool}{' act %.2f' % m.pool[n].act if n in m.pool else ''}; SOV relations {len(u.rel.get(c_, {}))}, "
          f"open {u.open_slots(c_) if c_ in u.rel else '-'}; on the last 500 decision paths: "
          f"{sum(1 for _, _, nodes in tree.get('records', []) if any(n in x[1] for x in nodes))}")

# (2) the waits: record the anti-want's push-down on each push
anti_down = {}
plain_support = molecules.Mind.support_all
def support(self, res, comps):
    base = plain_support(self, res, comps)
    out = molecules.Mind.__dict__["_traced_support"](self, res, comps)
    for i in out:
        if "invitation" in getattr(m.pool.get(i), "tags", ()) or "_push:" in i:
            anti_down[i] = out.get(i, 0.0) - base.get(i, 0.0)
    return out
molecules.Mind._traced_support = molecules.Mind.support
molecules.Mind.support = support

waits, pushes, why, held, downs = 0, 0, collections.Counter(), collections.Counter(), []
winners_at_wait = collections.Counter()
block_wins = collections.Counter()
for t in range(N):
    anti_down.clear()
    m.potentials = w.potentials()
    invs = w.invitations()
    watching = bool(a.watching)
    choice, rec = a.tick()
    run.earn_luck(a, w)
    top = rec["levels"][-1]["winners"]
    for i in top:
        if i.startswith("sov:block_"):
            block_wins[i] += 1
    if invs and not watching:
        if choice is None:
            waits += 1
            held[a.__dict__.get("anti")] += 1
            pushes_top = [i for i in top if "_push:" in i]
            why["a push won the top but none was acted on" if pushes_top else "no push won the top level"] += 1
            for i in top:
                winners_at_wait[i.split(":")[0] if ":" in i else i] += 1
            downs.append(sorted((round(v, 2), k.split("_push")[0]) for k, v in anti_down.items() if v)[:4])
        else:
            pushes += 1
print(f"over {N} slices: offered and decided {waits + pushes}: waits {waits}, pushes {pushes}")
print("  at the waits:", dict(why), "| anti-want held:", held.most_common(3))
print("  what held the top level at the waits (by kind):", winners_at_wait.most_common(8))
print("  the anti-want's push-down on pushes at the waits (first 6):", downs[:6])
print("  block SOV molecules winning the top level:", block_wins.most_common(4))
print("  anti-want targets now:", len(m.__dict__.get("anti_targets") or ()), "| luck", w.luck)
