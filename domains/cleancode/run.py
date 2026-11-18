"""Run a Gerundelle mind in the clean code world (world.py, PLAN.md). Run: python -u -X utf8 run.py --rung 0 [--seed 0] [--slices 600]

The mind is Go's (go/run.py), which is tetris's: SovAgent with ForceMind (its pushes enter with the potential force they would exert,
world.potentials()), every Params switch the user decided on: tetris/run.py's SWITCHES and go/run.py's GO_SWITCHES, read from those
files so they can't drift apart (as warpchess/rung1d.py reads them). No goal is placed: wants form through ownership.

Territory (the user, 2026-11-14: "lint rules off and compiler errors off and clean code and tests passing would be its territory";
PLAN.md): each territory gerund (graph.TERRITORY: tests, range checks, signs, divisors, overflows, lint, clean) is the mind's while it
holds, lost when it stops holding, held again when it holds again, tracked by the agent as Go's dead opportunities are
(SovAgent.track_region). As Go's: a gerund never held isn't the mind's to lose; when a problem is closed and the next opened, its
regions are let go, held or lost, with no loss (nothing made it so).

Time territory (the user, 2026-11-14): each tick the program is correct (everything held), a tick gained (world.py), the mind's for good.
"""
import argparse
import ast
import collections
import os
import sys
import time

sys.path.insert(0, __import__("paths").GERUNDELLE)
sys.path.insert(0, __import__("paths").domain('warpchess'))
from molecules import Params  # noqa: E402
from sov_agent import SovAgent  # noqa: E402
from potential import ForceMind  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import graph as g  # noqa: E402
import rooms  # noqa: E402
from world import CodeWorld  # noqa: E402

TETRIS_RUN = __import__("paths").domain('tetris', 'run.py')
GO_RUN = __import__("paths").domain('go', 'run.py')


def read_switches(path, name):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return {k.arg: ast.literal_eval(k.value) for k in node.value.keywords}
    raise ValueError(f"no {name} in {path}")


SWITCHES = {**read_switches(TETRIS_RUN, "SWITCHES"), **read_switches(GO_RUN, "GO_SWITCHES")}
CODE_SWITCHES = dict(anti_unbinds=True,   # the user, 2026-11-14 ("yes, build it"): on here, as GO_SWITCHES are on in go
                     dreamed_conditions=True,   # the user, 2026-11-15 ("build it, following the Gerundelle way"): a dreamed
                                                # condition becomes the hypothesis its experiment tests (LADDER.md, rung 2)
                     faithful_choice=True,   # the user, 2026-11-15 ("yes you should try it"; temperament upstream only): the
                                             # bids decide among the top's winners; the sticky wheel and the familiarity
                                             # discount no longer override the tournament (trace_valley.py)
                     defense_still=True,   # the balance principle on both sides (the user, 2026-11-15): losses stack against
                                           # a push as its flips stack for it, in this still world too (world.effects_after)
                     counted_pull=True,   # the user, 2026-11-15 ("do it"): the want's pull reads the counted structure —
                                          # closings pull, widenings press, n/(n+kappa) each at the wants' scale (Mind.support)
                     held_edges=True,
                     abstract_grows=True,   # the transfer trace's second fix (2026-11-16): joining is membership, not the end of analogizing
                     undo_loops=True,   # a loop of successes is perceived (balance rung 2's churn, 2026-11-16)
                     condition_subwants=True,   # the planner's backward step: a known way's unmet condition becomes a sub-want (balance 4t)
                     loop_unbinds=True,   # a perceived loop forfeits its bond (the bedrock's coalition broken by perception)   # balance rung 3's trace (2026-11-16): edges about held regions enter analogy by
                                        # what they are about — success starves the danger edges transfer needs
                     # the user's switches from cognitivechess_v2, 2026-11-17 (every user-decided switch on, in every domain):
                     defense_gains=True,    # both sides felt: a lost region brought back is a gain against waiting
                     plan_as_pull=True,     # a want's planned step pulls in the tournament, not an override
                     push_slots=(3, 2, 2),  # the pushes on offer in a lane of their own (no move crowded out by thoughts)
                     experimentation=0,     # temperament: an experiment yields to anything at stake on the board
                     patience_reach=True,   # patience also counts slices a held want is out of reach
                     explained_needs=True,  # a need is explained by the mind's own record, never a conflation of what held
                     ask_once_here=True,    # a question answered in a situation is not asked again there
                     region_weights=True)   # regions summed by the world's weights (none here: one each)
SWITCHES = {**SWITCHES, **CODE_SWITCHES}


def give(agent, world):
    """The mind's territory: each territory gerund held while it holds (PLAN.md). Regions of a closed problem are let go."""
    terr = agent.mind.territory
    tracked = agent.__dict__.setdefault("code_tracked", set())
    if agent.__dict__.get("code_problem", world.problems) != world.problems:   # the next problem: the last one's regions let go, no loss
        for r in tracked:
            terr.given.discard(r)
            terr.rows.pop(r, None)
        tracked.clear()
    agent.code_problem = world.problems
    for o in world.shown:   # time territory (the user, 2026-11-14): each tick gained is the mind's for good, across problems
        if o.startswith("tick_"):
            agent.track_region(o, True)
    for o, held in g.territory(world.shown).items():
        if held or o in tracked:   # (a gerund never held isn't the mind's to lose)
            agent.track_region(o, held)
            tracked.add(o)


def kind(r):
    return r.split("_", 1)[0]


AVERSION = 2.0   # this domain's temperament (the user, 2026-11-14: "make 2 the default"; LADDER.md, rung 0's table)


def build(rung, seed=0, acceptance=6, dream=False, aversion=AVERSION):
    """dream: in-problem dreaming when stuck (the user, 2026-11-14, as Warp chess: Params.dreams and Params.dream_when_stuck, with
    dream_code.dreamer)."""
    if dream:
        import dream_code
        w = dream_code.DreamingCode(rooms.ROOMS[rung], seed=seed)
    else:
        w = CodeWorld(rooms.ROOMS[rung], seed=seed)
    a = SovAgent(w, ForceMind(Params(**SWITCHES)))
    a.mind.p.acceptance = acceptance
    if aversion is not None:   # temperament: how strongly an anti-want pushes down what threatens it (Params.aversion, 1.0)
        a.mind.p.aversion = aversion
    if dream:
        a.mind.p.dreams = True
        a.mind.p.dream_when_stuck = True
        a.dreamer = dream_code.dreamer
    return a, w


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--rung", default="0")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--slices", type=int, default=600)
    ap.add_argument("--acceptance", type=int, default=6)
    ap.add_argument("--quiet", action="store_true", help="no line per slice")
    ap.add_argument("--dream", action="store_true", help="dream in the problem when stuck (dream_code.py)")
    ap.add_argument("--aversion", type=float, default=AVERSION, help="temperament: Params.aversion (this domain's default 2.0)")
    args = ap.parse_args()
    a, w = build(args.rung, args.seed, args.acceptance, args.dream, args.aversion)
    print(f"clean code rung {args.rung} seed {args.seed}: {len(w.objs)} objects, problem {w.p.name}: tests {w.p.tests}, "
          f"start {[w.p.shape.doing(c, x) for c, x in enumerate(w.p.start)]}", flush=True)
    t0, shown = time.time(), 0
    for t in range(args.slices):
        a.mind.potentials = w.potentials()
        ts = time.time()
        a.tick()
        give(a, w)
        if not args.quiet:
            turn = w.log[-1] if w.log and w.log[-1][0] == w.t - 1 else None
            held = g.territory(w.shown)
            print(f"  s{t + 1} {time.time() - ts:5.1f}s: {f'{turn[1]} {turn[2]}' if turn else '-'}; held {sum(held.values())}/{len(held)}; "
                  f"wheels {[w.p.shape.doing(c, x) for c, x in enumerate(w.pos)]}", flush=True)
        while shown < len(w.solved):
            s = w.solved[shown]
            shown += 1
            print(f"  problem {shown} ({s['name']}): {'settled' if s['settled'] else 'not settled'} in {s['slices']} slices, "
                  f"{s['turns']} turns; start {s['start']} end {s['end']} correct {s['correct']}", flush=True)
            if not args.quiet and w.problems > shown:
                print(f"  problem {w.problems} ({w.p.name}): tests {w.p.tests}, start {[w.p.shape.doing(c, x) for c, x in enumerate(w.p.start)]}",
                      flush=True)
    terr = a.mind.territory
    print(f"slices {args.slices}, {(time.time() - t0) / args.slices:.2f}s a slice; problems {len(w.solved)} closed, "
          f"{sum(s['settled'] for s in w.solved)} settled")
    print("wants set:", collections.Counter(x for _, x, k in a.sub_log if k == "set").most_common(10))
    print("wants met:", collections.Counter(x for _, x, k in a.sub_log if k == "met").most_common(6))
    print("territory:", {k: dict(collections.Counter(row["holder"] for r, row in terr.rows.items() if kind(r) == k))
                         for k in sorted({kind(r) for r in terr.rows})})
    print("slots open:", collections.Counter((k, kind(r)) for k, r in terr.open_slots()).most_common(10))
    print("commits:", dict(collections.Counter(x[2] for x in a.__dict__.get("commit_log", []))))
    print("ticks gained (time territory):", w.gained)
    done = a.__dict__.get("dreams_done", [])
    print("dreams:", len(done), "| trials", sum(x[2] for x in done), "| not run", len(a.__dict__.get("dreams_not_run", [])))


if __name__ == "__main__":
    main()
