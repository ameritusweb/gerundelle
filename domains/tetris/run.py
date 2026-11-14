"""Run a Gerundelle mind in the tetris force world (README.md). Run: python -X utf8 run.py [--seed 0] [--slices 2000] [--acceptance 6]

The mind is the mystery maze's (mysterymaze/run.py): SovAgent with ForceMind (its pushes enter with the potential force they would exert,
world.potentials()), every Params switch the user decided on. No goal is placed: wants form through ownership (the user, 2026-11-09;
Params.own_wants: an open ownership slot offers the states its region was seen in, and the one that wins the top level is wanted).
The dream is off: mysterymaze/dream_maze.py manipulates the maze's objects, and which forces a tetris dream manipulates isn't decided.

Reported: each game (pieces placed, rows cleared, slices), the wants set, the territory register by kind of region, the ownership slots
open at the end, the pushes made, the questions let go.
"""
import argparse
import collections
import sys
import time

sys.path.insert(0, __import__("paths").GERUNDELLE)
sys.path.insert(0, __import__("paths").domain('warpchess'))
from molecules import Params  # noqa: E402
from sov_agent import SovAgent  # noqa: E402
from potential import ForceMind  # noqa: E402  (warpchess: pushes enter with the force they would exert)

from world import TetrisWorld  # noqa: E402

SWITCHES = dict(inquiry=True, phases=True, winner_acts=True, subwants=True, sub_yield=True, imagined_tournament=True, want_site=True,
                setup_support=True, own_wants=True, want_split=True, mental_energy=0.2, rest=3.0, tie_lru=True, want_holds_pushes=True,
                meta_binds=True, own_doings=True, surprise_gated=True, arrival_by_presence=True, news_in_structure=True, stuck_earns=True,
                split_superposition=True, tie_superposition=True, reread_whole=True, setup_unmet=True, wants_not_arrivals=True,
                predecessor_evidence=True, confound_experiments=True, stack_supports=True, lines_need_change=True, self_noticed=True,
                held_wants_only=True, force_reach_claims=True, affords_chain=True, loop_spares_looping=True, setup_for_wants=True,
                ways_whole=True, held_evidence=False, concept_abstracts=True, force_predictions=True, anti_wants=True, decision_paths=True, meta_targets=True, dormancy=True,
                commit=True)   # (the user, 2026-11-12: commit "should default to on") the maze's set: every switch the user decided on


def own_open_rows(agent, world):
    """The open space is the mind's territory (the user): each row is held while it is open (reads free), lost when the stack reaches it
    (holding), and held again when a clear opens it; the top row going is the last loss. A row that has been cleared is the mind's for
    good (own_clears) and isn't read here."""
    terr = agent.mind.territory
    for y in range(world.height):
        if terr.rows.get(f"row_{y}", {}).get("cleared"):
            continue
        agent.track_region(f"row_{y}", world.shown.get(f"row_{y}") == "free")


def own_clears(agent, world):
    """Cleared blocks and rows are territory (the user, 2026-11-11: "cleared blocks and rows ARE TERRITORY", as a capture in warpchess):
    each block a clear takes out of the well, and each row a clear takes, is the mind's for good, held in view or not. Blocks still in the
    well are no one's to claim (world.unclaimable), so stacking them isn't gaining. (First unclaimable dropped cleared blocks too.)"""
    log = world.__dict__.get("cleared_log", [])
    seen = agent.__dict__.get("_clears_read", 0)
    terr = agent.mind.territory
    for t, rows, blocks in log[seen:]:
        for r in sorted(rows) + sorted(blocks):
            agent.track_region(r, True)
            terr.rows[r]["cleared"] = True
    agent._clears_read = len(log)


def own_ground(agent, world):
    """A piece that touches ground level is the mind's territory (the user, 2026-11-12: "a piece that touches ground level should count
    as territory of the mind"): each settled block of a piece that has a block on the well's floor is held, from the slice the piece
    touches it. Blocks otherwise are no one's to claim (world.unclaimable); these are tracked by the agent itself, as the open rows
    are. My readings, for the user to change: once held, a block stays held while it is in the well, though a clear later lifts its
    piece off the floor; a clear makes it the mind's for good (own_clears); and when the well is set back its leaving is not a loss,
    as the user ruled for every block (2026-11-11: what is lost then is the open space, row by row)."""
    floor = world.height - 1
    grounded = {world.piece_of.get(b) for c, b in world.block_at.items() if c[1] == floor}
    held = agent.__dict__.setdefault("ground_held", set())
    for b in world.block_at.values():
        if b not in held and world.piece_of.get(b) in grounded:
            agent.track_region(b, True)
            held.add(b)


def after_tick(agent, world, ground=True):
    """What run.py does after each of the mind's ticks, for anything that goes on from a checkpoint as the run would: luck earned, cleared
    blocks and rows the mind's for good, the open rows held or lost, and the pieces on the ground held."""
    earn_luck(agent, world)
    own_clears(agent, world)
    own_open_rows(agent, world)
    if ground:
        own_ground(agent, world)


def earn_luck(agent, world):
    """Luck falls a step for each clear the mind both made and predicted (the user, 2026-11-11: luck falls in-game as the mind gets
    better, by "clears it predicted"): a prediction of its own, confirmed, linked to one of its pushes (not "wait"), whose effect was a
    clear its pushes made (world.made_clears: the piece falling straight down with no push would not have cleared). Each answer is read
    once."""
    answers = agent.__dict__.get("prediction_answers", [])
    seen = agent.__dict__.get("_luck_read", 0)
    events = world.__dict__.get("made_events", [])
    done = world.__dict__.setdefault("earned_events", set())   # each clear earns one step, however many of its predictions came true (the user's
    for t, effect, outcome, by in answers[seen:]:               # "clears it predicted"; first one clear with a row and a run predicted earned two)
        if outcome != "confirmed" or by == "wait":
            continue
        k = next((i for i in range(len(events) - 1, -1, -1) if effect in events[i]), None)
        if k is not None and k not in done:
            done.add(k)
            world.earn()
    agent._luck_read = len(answers)


def kind(r):
    return r.split("_", 1)[0] if not r.startswith("block_") else ("block_" + r.rsplit("_", 1)[1] if r.count("_") > 1 else "block")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--slices", type=int, default=2000)
    ap.add_argument("--acceptance", type=int, default=6, help="temperament: experiments bringing nothing new before a question is let go")
    ap.add_argument("--luck", type=float, default=0.7, help="the dial (0.7: the user, 2026-11-09): the chance a new piece forms where falling straight down lands it best")
    args = ap.parse_args()
    w = TetrisWorld(seed=args.seed, luck=args.luck)
    a = SovAgent(w, ForceMind(Params(**SWITCHES)))
    a.mind.p.acceptance = args.acceptance
    print(f"tetris seed {args.seed}: a {w.width} x {w.height} well, {len(w.objs)} objects perceived at the start", flush=True)
    shown, t0, start, read, owed = 0, time.time(), 0, 0, set()
    terr = a.mind.territory
    for t in range(args.slices):
        a.mind.potentials = w.potentials()   # (as the maze's)
        a.tick()
        after_tick(a, w)
        read = len(a.pushed)   # (the cells a cleared piece left were made the mind's here; cells are no one's now: own_clears)
        while shown < len(w.games):
            placed, lines = w.games[shown]
            shown += 1
            print(f"  game {shown}: {placed} pieces placed, {lines} rows cleared, {t - start} slices; lucky pieces so far {w.lucky}; luck {w.luck} ({w.earned} earned)", flush=True)
            start = t
        if (t + 1) % 100 == 0:
            terr = a.mind.territory
            print(f"    slice {t + 1} ({time.time() - t0:.0f}s): goal {a.goal}, stack {a.stack}, pieces this game {w.placed}, "
                  f"regions {len(terr.rows)}, slots open {len(terr.open_slots())}", flush=True)
    terr, und = a.mind.territory, a.mind.understanding
    print("wants set:", collections.Counter(g for _, g, k in a.sub_log if k == "set").most_common(10))
    print("wants met:", collections.Counter(g for _, g, k in a.sub_log if k == "met").most_common(6), "| reached:", collections.Counter(g for _, g in a.reached).most_common(6))
    print("territory:", {k: dict(collections.Counter(row["holder"] for r, row in terr.rows.items() if kind(r) == k)) for k in sorted({kind(r) for r in terr.rows})})
    print("slots open:", collections.Counter((k, kind(r)) for k, r in terr.open_slots()).most_common(10))
    print("pushes:", collections.Counter(i[0] for i, _, _ in a.pushed))
    print("released (from attention):", len(getattr(und, "released", {})))
    print("games:", len(w.games), "| rows cleared:", w.lines)


if __name__ == "__main__":
    main()
