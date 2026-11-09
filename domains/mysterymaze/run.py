"""Run a Gerundelle mind in the mystery maze (README.md). It wants the cheese; between trips it dreams (dream_maze.py).

    python -X utf8 run.py --seed 0 --slices 2000 --dreams --acceptance 6

The mind: SovAgent on Gerundelle reference/v2, a ForceMind (each push enters with the force it would exert), with every switch the
user decided on and the ones the maze's traces led to (LESSONS_LEARNED.md, section 2). Temperament: --acceptance, how many experiments
on a question may bring nothing new before the mind lets it go (released from attention, not forgotten); 6 did best over five mazes.
Reported: each trip to the cheese (slices taken), the words found to open walls, the questions released.
"""
import argparse
import collections
import sys

from gerundelle_path import ForceMind  # puts reference/v2 on the path
from molecules import Params  # noqa: E402
from sov_agent import SovAgent  # noqa: E402

import dream_maze  # noqa: E402
from maze import Maze  # noqa: E402

WANT = "cheese_borne"

SWITCHES = dict(
    # the user's, from the other domains
    inquiry=True, phases=True, winner_acts=True, subwants=True, sub_yield=True, imagined_tournament=True, want_site=True,
    setup_support=True, own_wants=True, want_split=True, mental_energy=0.2, rest=3.0, tie_lru=True, want_holds_pushes=True,
    meta_binds=True, own_doings=True, surprise_gated=True, arrival_by_presence=True, news_in_structure=True, stuck_earns=True,
    # the maze's (LESSONS_LEARNED.md, section 2)
    split_superposition=True, tie_superposition=True, reread_whole=True, setup_unmet=True, wants_not_arrivals=True,
    predecessor_evidence=True, confound_experiments=True, stack_supports=True, lines_need_change=True, self_noticed=True,
    held_wants_only=True, force_reach_claims=True, affords_chain=True, loop_spares_looping=True, setup_for_wants=True,
    ways_whole=True)


class DreamingMaze(dream_maze.RemembersTrips, Maze):
    """The maze, remembering each trip's configurations for the dream."""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--slices", type=int, default=2000)
    ap.add_argument("--dreams", action="store_true", help="the dream planner between trips (dream_maze.py; Params.dreams)")
    ap.add_argument("--acceptance", type=int, default=None, help="temperament: experiments bringing nothing new before a question is let go")
    ap.add_argument("--off", default="", help="switches to turn off, for a comparison, comma-separated")
    args = ap.parse_args()
    w = DreamingMaze(seed=args.seed) if args.dreams else Maze(seed=args.seed)
    a = SovAgent(w, ForceMind(Params(**SWITCHES)))
    for k in filter(None, args.off.split(",")):
        setattr(a.mind.p, k, False)
    a.mind.p.dreams = args.dreams
    a.mind.p.acceptance = args.acceptance
    print(f"maze seed {args.seed}: {len(w.walls)} walls, the words that open them {w.opens}")
    shown = 0
    for t in range(args.slices):
        if a.goal is None:
            a.goal = WANT
        a.mind.potentials = w.potentials()   # each push's force, read from what it would reach
        a.tick()
        while shown < len(w.episodes):
            got, n = w.episodes[shown]
            shown += 1
            print(f"  trip {shown}: {'cheese' if got else 'no cheese'} in {n} slices", flush=True)
            if args.dreams:   # between trips: the dream
                trials, edges = dream_maze.dream(a)
                print(f"    dream: {trials} trials, {edges} at the edge", flush=True)
    und = a.mind.understanding
    opened = sorted({c.split("_push")[0] for c, rels in und.rel.items()
                     if c.startswith("say_") and any(r == "causes" and o.endswith("_yielding") for (r, o) in rels)})
    print("words found to open walls:", opened)
    print("pushes:", dict(collections.Counter(i[0].split("_")[0] for i, _, _ in a.pushed)))
    print("questions released from attention:", len(getattr(und, "released", {})))
    print("trips:", len(w.episodes), "| cheese:", sum(g for g, _ in w.episodes))


if __name__ == "__main__":
    main()
