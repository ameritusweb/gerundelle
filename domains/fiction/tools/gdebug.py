"""Trace the Gerundelle arm tick by tick on a rung: the top, the experiment chosen, the push, splits, phases.
python tools/gdebug.py RUNG [ticks]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import run_ladder  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
rung = int(sys.argv[1])
ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 120
spec = run_ladder.RUNGS[rung]
world = spec["world"]()
others = [run_ladder.prologue(n, spec, 300) for n in spec.get("company", ())]
m = GerundelleMind(spec["actor"], world, want=spec["want"], want_count=spec.get("want_count", 1), others=others)
ag = m.agent
_tick = ag.tick
_plan = ag.plan_step
log = {}


def plan_step(invs, **kw):
    out = _plan(invs, **kw)
    log["plan"] = out
    return out


ag.plan_step = plan_step


def tick(force=None):
    log.clear()
    q0, run0 = list(ag.queue), ag.running
    choice, rec = _tick(force)
    log["choice"], log["src"] = choice, ("plan" if log.get("plan") else "queue" if q0 else "exp" if choice else "")
    log["running"] = ag.running or run0
    return choice, rec


ag.tick = tick
seen_splits = set()
m.predictions, tries_seen = {}, 0
for k in range(ticks):
    n_tried = len(ag.tried)
    tries_seen = m.step(tries_seen)
    rec = ag.last_rec
    top = [q for q in ag.mind.top(rec)][:4]
    new = ag.tried[n_tried:]
    sp = {x: s["tag"] for x, s in ag.mind.meta.splits.items() if x not in seen_splits}
    seen_splits |= set(sp)
    ph = [p for p in rec.get("phases", []) if p.startswith("phase:")]
    fl = sorted(f for f in ag.facts_now() if f.startswith("flag"))
    print(f"t{world.t:3d} {fl} goal={ag.goal} plan={log.get('plan')} watching={bool(ag.watching)} top={top} exp={rec['experiments'][:1]} "
          f"{('PUSH ' + str(log['choice'][:2]) + ' via ' + log['src'] + ' ' + str(log['running'])) if log.get('choice') else ''} "
          f"{'DONE ' + str([(i[0], i[1], tuple(n)) for _, i, n in new]) if new else ''} "
          f"{'SPLIT ' + str(sp) if sp else ''} {'PH ' + str(ph) if ph else ''}")
    if m.pending:
        break
print("splits:", {x: s["tag"] for x, s in ag.mind.meta.splits.items()})
terr = ag.mind.territory
print("live before settle:", sorted(terr.live()), "rows lid:", {k: v for k, v in terr.rows.get("lid", {}).items() if k != "claims"})
for k in range(8):
    tries_seen = m.step(tries_seen)
    rec = ag.last_rec
    ph = [p for p in rec.get("phases", []) if p.startswith("phase:")]
    print(f"settle t{world.t} live={sorted(terr.live())} phases={ph} took={getattr(terr, 'took_now', None)}")
print("phase log tail:", ag.mind.phases.log[-6:])
