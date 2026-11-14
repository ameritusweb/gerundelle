"""Rung 1h (LADDER.md): why the shared switch set finds rung 1g's crossing as early but wins it far less (late 0.07-0.10 against
0.41-0.50; fewer tries, fewer wants met). Plays one seed both ways, rung 1g's switches and the shared set, as rung1d.py does (main mind
alone), and records every tick: the want held (goal) and the stack under it, whether a move was made, what made it (a want's plan, an
experiment, the tournament's winner), the top level's winners by kind, the mind's energy, the anti-want. Then for each: ticks by what
happened, the wants held and how they were set (sub_log), and where the ticks without a move went.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_1h.py [seed] [ticks]"""
import collections
import sys

import rung1d
import sov_agent
from rung0 import WANT
from pieceminds import OfferedMainMind
from warpworld import RUNG1_TWO, WarpWorld

_args = [x for x in sys.argv[1:] if not x.startswith("--")]
SEED = int(_args[0]) if len(_args) > 0 else 2
TICKS = int(_args[1]) if len(_args) > 1 else 1000


def play(shared, with_plans=False):
    if with_plans:
        from plansworld import PlansWorld
        w = PlansWorld(RUNG1_TWO, seed=SEED, moves=2)
    else:
        w = WarpWorld(RUNG1_TWO, seed=SEED, moves=2, forces=True)
    a = OfferedMainMind(w, pieces=False, forces=True)
    a.mind.p.imagined_tournament = a.mind.p.want_site = a.mind.p.setup_support = True
    if shared:
        for k, v in rung1d.shared_switches().items():
            setattr(a.mind.p, k, v)
    if with_plans:
        for k, v in rung1d.go_switches().items():
            setattr(a.mind.p, k, v)
    if "--tool" in sys.argv:   # (Params.tool_use: the tool's mind side, tool.MindTool)
        from tool import MindTool
        a.tool = MindTool(w)
        a.mind.p.tool_use = True
    tag = {}
    for name in ("planned", "winner"):
        orig = getattr(sov_agent.SovAgent, name)

        def wrap(self, *args, _orig=orig, _name=name, **kw):
            out = _orig(self, *args, **kw)
            if self is a and out is not None and out != "wait":
                tag.setdefault(_name, out)
            return out
        setattr(sov_agent.SovAgent, name, wrap)
    rows = []
    for t in range(TICKS):
        if a.goal is None:
            a.goal = WANT
        tag.clear()
        moves_before = len([x for x in w.log if x[2]])
        q_before = list(a.queue)
        choice, rec = a.tick()
        if with_plans:
            import plansworld
            plansworld.give(a, w)
        moved = len([x for x in w.log if x[2]]) > moves_before
        if choice is None:
            what = "watching" if a.watching else "nothing chosen"
        elif tag.get("planned") == choice:
            what = "a want's plan"
        elif q_before or rec.get("experiments"):
            what = "an experiment"
        elif "winner" in tag:
            what = "the tournament's winner"
        else:
            what = "other"
        lv = rec["levels"][-1]["winners"] if rec.get("levels") else []
        kinds = collections.Counter(i.split(":")[0] if ":" in i.split("|")[0] and not "_push:" in i else ("push" if "_push:" in i else "concept")
                                    for i in lv)
        rows.append(dict(t=t, goal=a.goal, stack=list(a.stack), moved=moved, what=what, kinds=kinds,
                         energy=round(getattr(a.mind, "energy", 1.0), 2), anti=a.__dict__.get("anti")))
    for sw in (sov_agent.SovAgent.planned, sov_agent.SovAgent.winner):
        pass
    return w, a, rows


def report(name, w, a, rows):
    made = [x for x in w.log if x[2]]
    print(f"\n=== {name}: moves {len(made)}, wants met {len(a.reached)}")
    print("  ticks by what happened:", collections.Counter((r["what"], r["moved"]) for r in rows).most_common())
    print("  the want held, ticks:", collections.Counter(str(r["goal"])[:50] for r in rows).most_common(6))
    print("  ticks with the placed want not the goal:", sum(1 for r in rows if r["goal"] != WANT),
          "| with a stack under the goal:", sum(1 for r in rows if r["stack"]))
    sets = collections.Counter((g.split("_")[0] if not g.startswith("all:") else "all:", k) for _, g, k in a.sub_log)
    print("  sub_log (kind, event):", sets.most_common(10))
    print("  examples of wants set:", [g[:60] for _, g, k in a.sub_log if k == "set"][:8])
    low = [r for r in rows if r["energy"] < 0.5]
    print(f"  energy: mean {sum(r['energy'] for r in rows) / len(rows):.2f}, ticks below 0.5: {len(low)}")
    print("  anti-wants held, ticks:", collections.Counter(str(r["anti"]) for r in rows).most_common(4))
    print("  top-level winners by kind (summed):", sum((r["kinds"] for r in rows), collections.Counter()).most_common(8))
    print("  ticks 500-520:")
    for r in rows[500:520]:
        print(f"    {r['t']}: {r['what']:24s} moved {r['moved']!s:5s} goal {str(r['goal'])[:40]:40s} stack {[str(x)[:25] for x in r['stack']]} energy {r['energy']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--plans" in sys.argv:
        w, a, rows = play(True, True)
        report("shared set, plans as territory (rung 1i)", w, a, rows)
        q = [i for i in a.mind.pool if i.startswith("q:")]
        print("  questions in the pool at the end:", q[:10])
        log = a.__dict__.get("tool_log", [])
        print(f"  tool calls: {len(log)}; slices spent waiting: {sum(x[3] for x in log)}; answers with a move: {sum(1 for x in log if x[2])}")
        for x in log[:12]:
            print("    ", x[0], x[1], [r[0][:40] for r in x[2]] if x[2] else "nothing stops it", f"{x[3]} slices")
        told = [(c, o) for c, rels in a.mind.understanding.rel.items() for (r, o), e in rels.items() if r == "causes" and o.startswith("plan_") and o.endswith("_none") and e[1] > 0]
        print(f"  told 'stops the plan' links standing at the end: {len(told)}; of them also lived: "
              f"{sum(1 for c, o in told if a.mind.understanding.rel[c][('causes', o)][0] > 0)}")
        print("  questions about plans posed over the game:", sum(1 for x in a.mind.understanding.log if x[1] == "asked" and "plan_" in str(x[2])) if hasattr(a.mind.understanding, "log") else "?")
    else:
        for shared in (False, True):
            w, a, rows = play(shared)
            report("shared set" if shared else "rung 1g's switches", w, a, rows)
