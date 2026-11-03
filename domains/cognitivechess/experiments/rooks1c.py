"""Rung 1c, converge, the clean want, Black's reply perceived: every rook lost, by the path that chose the move, the
configuration, the move, and the sub-want served (if any)."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1c  # noqa: E402
from chessworld import RUNG1C, RUNG1C_RELATIONS, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

seeds = int(sys.argv[1])
arm = sys.argv[2] if len(sys.argv) > 2 else "converge"
by_path, by_move, by_goal, eps_cfg = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
for seed in range(seeds):
    w = ChessWorld(RUNG1C, order=seed, seed=seed, reply="answer", moves=2,
                   relations=RUNG1C_RELATIONS + ("reply", "game"), clean=True)
    m = GerundelleMind("White", w, want="game_mate", want_count=10 ** 6)
    for k, v in rung1c.ARMS[arm].items():
        setattr(m.agent.mind.p, k, v)
    a, src = m.agent, {}
    op, on = a.plan_step, a.notice

    def plan_step(invs, **kw):
        s = op(invs, **kw)
        if s is not None:
            src[a.mind.t] = "planner, for a sub-want" if a.stack else "planner"
        return s

    def notice(invs):
        s = on(invs)
        if s is not None:
            src[a.mind.t] = "noticed"
        return s

    a.plan_step, a.notice = plan_step, notice
    act = w.act

    def logged(inv=None, hold=False):
        t, cfg, goal = a.mind.t, w.config, a.goal
        path = src.get(t, "experiment" if a.queue or a.running else "sub-want 'try' / other")
        ev = act(inv, hold)
        if inv is not None:
            pending = getattr(w, "pending", {})
            lost = any(x.startswith("white_rook") and "-> captured" in x for x in ev) or any(
                o.startswith("white_rook") and not o.endswith("_safety") and st == "captured" for o, st in pending.items())
            if lost:
                by_path[(path, "no mate here" if cfg not in (rung1c.ONE, rung1c.BOTH) else f"config {cfg}")] += 1
                by_move[inv[0].split(" ", 1)[-1]] += 1
                if path == "planner, for a sub-want":
                    by_goal[goal] += 1
        return ev
    w.act = logged
    m.run(800)
    eps_cfg.update(w.episodes[:-1])
    print(f"seed {seed} done", flush=True)
print("rooks lost by path and where:", by_path.most_common())
print("by move:", by_move.most_common(8))
print("sub-wants served when a rook was lost:", by_goal.most_common(6))
print("episodes by configuration:", dict(sorted(eps_cfg.items())))
