"""Rung 1e: after its first win, why doesn't the mind keep winning? Records each episode: both moves, where each came from, and what the planner held. Run: python -X utf8 trace_settle.py [seed] [pieces|control]"""
import collections
import sys

from rung0 import WANT  # (puts Gerundelle on the path)
from pieceminds import MainMind
from sov_agent import inv_id
from warpworld import RUNG1_TWO, WarpWorld


class Traced(MainMind):
    def planned(self, invs):
        g = self.goal
        step = super().planned(invs)
        self.trace_plan = (g, step, list(self.stack))
        return step

    def tick(self, force=None):
        self.trace_plan = None
        q, run_ = list(self.queue), self.running
        out = super().tick(force)
        self.trace_before = (q, run_)
        return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    arm = sys.argv[2] if len(sys.argv) > 2 else "control"
    w = WarpWorld(RUNG1_TWO, seed=seed, moves=2, forces=True)
    a = Traced(w, pieces=arm == "pieces", forces=True)
    episodes, ep, first = [], [], None
    for t in range(1000):
        if a.goal is None:
            a.goal = WANT
        n = len(w.log)
        choice, rec = a.tick()
        if len(w.log) > n and w.log[-1][2]:
            q, run_ = a.trace_before
            plan = a.trace_plan
            src = "plan" if plan and plan[1] == choice else "experiment" if (q or run_ or rec["experiments"]) else "attention"
            ep.append(dict(t=t, move=w.log[-1][1].split(" ")[1], src=src, goal=plan[0] if plan else a.goal, stack=plan[2] if plan else list(a.stack),
                           running=str(run_ or "")[:70], material=w.log[-1][3]))
            if first is None and w.log[-1][3] == "up":
                first = len(episodes)
        if w.moved == 0 and ep:
            episodes.append(ep)
            ep = []
    if first is None:
        print(f"seed {seed} {arm}: never won")
        return
    after = episodes[first:]
    won = [any(m["material"] == "up" for m in e) for e in after]
    print(f"seed {seed} {arm}: first win in episode {first}; episodes after: {len(after)}, won {sum(won)}")
    pair = collections.Counter((e[0]["src"], e[1]["src"] if len(e) > 1 else "-") for e in after)
    print(f"  sources of (first move, second move) after the first win: {dict(pair)}")
    firsts = collections.Counter(e[0]["move"] for e in after)
    print(f"  first moves after the first win: {firsts.most_common(6)}")
    print(f"  goals when choosing: {collections.Counter(str(m['goal']) for e in after for m in e).most_common(4)}; sub-wants seen {sum(1 for e in after for m in e if m['stack'])}")
    wins = [e for e in after if any(m["material"] == "up" for m in e)]
    print(f"  the winning episodes: {[(e[0]['move'], e[0]['src'], e[1]['move'] if len(e) > 1 else '-', e[1]['src'] if len(e) > 1 else '-') for e in wins[:6]]}")
    _, invs = a.perceive()
    w2 = WarpWorld(RUNG1_TWO, seed=seed, moves=2, forces=True)
    a.world = w2
    _, invs = a.perceive()
    step, value = None, None
    from sov_agent import Model
    from molecules import mcts
    model = Model(a, WANT, root=(a.facts_now(), set(invs)))
    if model.actions(a.facts_now()):
        act, value = mcts(model, a.facts_now(), {}, budget=500, horizon=3, value=True)
        step = act
    print(f"  at the start, after the run: the planner's best first move {step} with value {value}")
    winner = next((m for e in wins for m in e if m["material"] == "up"), None)
    if winner:
        print(f"  the model of the winning second move from the first move's situation: {[(c[:30], round(r, 2)) for c, r in []]}")
    for e in after[:5]:
        print(f"  episode: " + " | ".join(f"{m['move']} by {m['src']}{' ('+m['running']+')' if m['src']=='experiment' else ''} -> {m['material']}" for m in e))


if __name__ == "__main__":
    main()
