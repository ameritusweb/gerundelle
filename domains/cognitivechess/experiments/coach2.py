"""Rung 2, one seed, a coach: what was told and refuted, the phases about the coach, and what the mind did after."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung2  # noqa: E402

seed, ck = int(sys.argv[1]), sys.argv[2]
w, want = rung2.world_for("1", seed, 20)
m = rung2.GerundelleMind("White", w, want=want, want_count=10 ** 6)
for k, v in rung2.FULL.items():
    setattr(m.agent.mind.p, k, v)
coach, told = [rung2.Coach(ck, seed) if ck != "none" else None], []
rung2.coached(m, coach, told)
a = m.agent
pushes_by = collections.Counter()
act = w.act


def logged(inv=None, hold=False):
    if inv is not None:
        pushes_by[a.mind.t // 100] += 1
    return act(inv, hold)


w.act = logged
for _ in range(800):
    m.step(len(a.tried))
if coach[0]:
    coach[0].close()
und = a.mind.understanding
print("told:", told[:12])
print("refuted:", sorted(und.refuted)[:8])
print("pushes per 100 ticks:", [pushes_by[i] for i in range(8)])
print("sub_log kinds:", collections.Counter((g, k) for _, g, k in a.sub_log).most_common(6))
print("noticed:", len(a.noticed), "contradicted:", sum(1 for _, x in a.noticed if isinstance(x, tuple) and x[0] == "contradicted"))
ph = collections.Counter(p.split(":")[1] for p in a.mind.phases.info) if hasattr(a.mind.phases, "info") else {}
print("phases formed:", dict(ph))
print("splits on Rxd5:", {x.split(" ", 1)[-1][:40]: s["tag"] for x, s in a.mind.meta.splits.items() if "Rxd5" in x})
