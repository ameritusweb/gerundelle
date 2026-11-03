"""Rung 1c: the both-mate configuration (6), with and without converge. For each episode there, the first move, which
path chose it, and whether the episode mated."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1c  # noqa: E402
from chessworld import RUNG1C, RUNG1C_RELATIONS, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

arm, seeds = sys.argv[1], int(sys.argv[2])
tot, lost = collections.Counter(), collections.Counter()
for seed in range(seeds):
    clean = "clean" in sys.argv[3:]
    extra = tuple(r for r in sys.argv[3:] if r != "clean") + (("game",) if clean else ())
    w = ChessWorld(RUNG1C, order=seed, seed=seed, reply="answer", moves=2, relations=RUNG1C_RELATIONS + extra,
                   clean=clean)
    m = GerundelleMind("White", w, want="game_mate" if clean else rung1c.WANT, want_count=10 ** 6)
    for k, v in rung1c.ARMS[arm].items():
        setattr(m.agent.mind.p, k, v)
    a = m.agent
    src = {}
    op = a.plan_step
    a.plan_step = lambda invs, **kw: (lambda s: (src.__setitem__(a.mind.t, "planner(sub)" if a.stack else "planner") if s else None, s)[1])(op(invs, **kw))
    if hasattr(a, "notice"):
        on = a.notice
        a.notice = lambda invs: (lambda s: (src.__setitem__(a.mind.t, "noticed") if s else None, s)[1])(on(invs))
    act, eps = w.act, {}

    def logged(inv=None, hold=False):
        ep, cfg = len(w.episodes), w.config
        ev = act(inv, hold)
        if cfg in (rung1c.BOTH, rung1c.ONE):
            e = eps.setdefault(ep, {"moves": [], "mated": False, "cfg": cfg})
            if inv is not None:
                e["moves"].append((inv[0].split(" ", 1)[-1], src.get(a.mind.t, "experiment" if a.queue or a.running else "sub-want try/other")))
            if any("-> mated" in x for x in ev):
                e["mated"] = True
        if inv is not None and any(x.startswith("white_rook") and "-> captured" in x for x in ev + w.diffs):
            lost[(src.get(a.mind.t, "experiment" if a.queue or a.running else "sub-want try/other"), cfg)] += 1
        return ev
    w.act = logged
    m.run(800)
    for e in eps.values():
        if e["moves"]:
            mv, how = e["moves"][0]
            key = (e["cfg"], how, mv if mv in ("Rd8", "Re8") else "other")
            tot[key + (("mated" if e["mated"] else "not"),)] += 1
    print(f"seed {seed}: episodes {len(eps)}, mated {sum(e['mated'] for e in eps.values())}", flush=True)
print(arm, "rooks lost by path and configuration:", lost.most_common(8))
print(arm, "first move in the both-mate configuration (path, move, outcome):")
for k, v in sorted(tot.items(), key=lambda x: -x[1]):
    print(f"  {v:4}  {k}")
