"""While the mind holds a want for an owned prediction (potential:...), does the push the forces predict leads there carry the tag, reach the
top level, and win? Each such slice: the want, the pushes on offer with their causes:potential tags this slice, the top-level winners with
bids, the want molecule's site and binding, and what the mind did. Run: python -u -X utf8 trace_want_pull.py [checkpoint] [slices]"""
import sys

sys.path.insert(0, ".")
import checkpoint  # noqa: E402
import run  # noqa: E402

PATH = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/clean_3000.pkl"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 400
a, w, t = checkpoint.load(PATH)
shown = 0
for k in range(N):
    a.mind.potentials = w.potentials()
    choice, rec = a.tick()
    run.earn_luck(a, w)
    run.own_clears(a, w)
    run.own_open_rows(a, w)
    g = a.goal
    if g and str(g).startswith("potential:") and shown < 10:
        lv = rec["levels"][-1]
        L0 = rec["levels"][0]
        sit = {c.split("_push")[0]: sorted(v) for c, v in a.__dict__.get("push_leads", {}).items()}
        tagged = [(i.split("_push")[0], [x for x in m.tags if x.startswith("causes:potential")]) for i, m in a.mind.pool.items() if "invitation" in m.tags]
        want = a.mind.pool.get(g)
        print(f"slice {w.t}: want {g} (in pool: {want is not None}, sites {want.sites if want else None}, act {round(want.act, 2) if want else None}, "
              f"binding L0 {L0['res'].get(g)}, bid L0 {round(L0['bids'].get(g, 0), 2)})", flush=True)
        print(f"   predicted from here: {sit}", flush=True)
        print(f"   pushes in the pool and their tags: {tagged}", flush=True)
        print(f"   top: {[(i[:40], round(lv['bids'].get(i, 0), 2)) for i in lv['winners']][:9]}", flush=True)
        print(f"   push bids at L0: {[(i.split('_push')[0] + ('|' + i.split('|', 1)[1][:20] if '|' in i else ''), round(L0['bids'][i], 2), L0['res'].get(i)) for i in L0['bids'] if '_push:' in i][:6]}", flush=True)
        print(f"   did: {choice[0] if choice else ('watching' if a.watching else 'wait')}", flush=True)
        shown += 1
