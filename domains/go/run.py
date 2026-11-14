"""Run a Gerundelle mind in the Go force world (README.md). Run: python -u -X utf8 run.py [--seed 0] [--slices 2000] [--luck 0.7]

The mind is tetris's (tetris/run.py), which is the mystery maze's: SovAgent with ForceMind (its pushes enter with the potential force
they would exert, world.potentials()), every Params switch the user decided on, read from tetris/run.py itself so the two can't drift
apart. No goal is placed: wants form through ownership (Params.own_wants). The dream (--dream; dream_go.py; the user, 2026-11-11):
between games the mind dreams over the game just played, one stone added or taken away at a time, with Params.dreams on.

Territory (the user, 2026-11-12, go/go-design.md: "Territory in Go isn't what you hold. It's what the opponent can't do"): each point
where White's opportunity force is dead (a white stone couldn't hold there, or would hang) is the mind's, held while dead, lost when it
lives again (give()). It replaced the stones, the captures and black_breath as given territory (2026-11-11 to 2026-11-12; backup
run.py.before_opportunity). The placements that would kill an opportunity are reported as potential effects (world.push_predictions),
so the prediction SOVs, wants and commit (Params.commit, on in tetris/run.py's switch set) reach them.

Checkpoints (the user, 2026-11-11: "so we can analyze at later learning stages"; tetris/checkpoint.py, used as it is): the agent and
the world saved together every --checkpoint slices to checkpoints/seed<seed>_<slice>.pkl; --resume <file> goes on from one. Load and run
with the PYTHONHASHSEED the run was saved with. resume(path) -> (agent, world, slice), for traces.

Reported: each game (stones placed, stones each side took, each side's area: counts for this report, never shown to the mind), the
wants set, the territory register by kind of region, the ownership slots open at the end, the questions let go.
"""
import argparse
import ast
import collections
import sys
import time

sys.path.insert(0, __import__("paths").GERUNDELLE)
sys.path.insert(0, __import__("paths").domain('warpchess'))
from molecules import Params  # noqa: E402
from sov_agent import SovAgent  # noqa: E402
from potential import ForceMind  # noqa: E402  (warpchess: pushes enter with the force they would exert)

from world import BLACK, DEAD, GoWorld  # noqa: E402

sys.path.append(__import__("paths").domain('tetris'))   # (last: only checkpoint.py is taken from there)
import checkpoint  # noqa: E402

HERE = __import__("paths").domain('go')


def resume(path):
    """A saved run (checkpoint.load): the agent, the world, the slice it was saved at."""
    return checkpoint.load(path)

TETRIS_RUN = __import__("paths").domain('tetris', 'run.py')


def switches(path=TETRIS_RUN):
    """The switch set as tetris/run.py writes it (SWITCHES = dict(...)): every switch the user decided on."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "SWITCHES" for t in node.targets):
            return {k.arg: ast.literal_eval(k.value) for k in node.value.keywords}
    raise ValueError(f"no SWITCHES in {path}")


SWITCHES = switches()
GO_SWITCHES = dict(reach_relations=True, transfer_tells=True, reach_claims=True, predicted_losses=True, commit_told=True, situational_told=True, no_loss_means=True, held_state_wants=True, affords_relation=True)   # the user, 2026-11-12 ("Reach as a relation", "Transfer tells a relation", reach_claims "yes, build it"):
# on here, not yet in tetris/run.py's set

def give(agent, world, read):
    """The mind's territory: where White's opportunity forces are dead (go/go-design.md; the user, 2026-11-12: "Territory in Go isn't
    what you hold. It's what the opponent can't do"; dead = a white stone couldn't hold there or would hang, world.DEAD). Each point's
    opportunity is held from the slice it reads dead, lost when it lives again, and held again when it dies again, tracked by the agent
    itself as tetris's open rows are (SovAgent.track_region). This replaces the stones, the captures and black_breath as given territory
    (the user, 2026-11-12: "Replace it"). My reading, for the user to change: when the board is set back between games, every
    opportunity lives again but nothing made it so, so it is no loss: the opportunity regions are let go, held or lost, and the next
    game's are claimed afresh. -> (how far the mind's pushes have been read, [] : nothing is given as taken now)."""
    terr = agent.mind.territory
    tracked = agent.__dict__.setdefault("opp_tracked", set())
    games = len(world.games)
    if agent.__dict__.get("opp_games", games) != games:   # the board was set back: the opportunity regions let go, no loss
        for r in tracked:
            terr.given.discard(r)
            terr.rows.pop(r, None)
        tracked.clear()
    agent.opp_games = games
    for o, doing in world.shown.items():
        if not o.startswith("opportunity_"):
            continue
        dead = doing in DEAD
        if dead or o in tracked:   # (a point never dead isn't the mind's to lose)
            agent.track_region(o, dead)
            tracked.add(o)
    return len(agent.pushed), []


def kind(r):
    head = r.split("_", 1)[0]
    if r.endswith("_breath"):
        return "breath"
    if r.startswith("opportunity_"):
        return "opportunity"
    return head if head == "point" or r.count("_") == 1 else head + "_side"


def build(seed=0, luck=0.7, acceptance=6, dream=False):
    if dream:
        import dream_go
        w = dream_go.DreamingGo(seed=seed, luck=luck)
    else:
        w = GoWorld(seed=seed, luck=luck)
    a = SovAgent(w, ForceMind(Params(**{**SWITCHES, "dreams": bool(dream) or SWITCHES.get("dreams", False), **GO_SWITCHES})))
    a.mind.p.acceptance = acceptance
    return a, w


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--slices", type=int, default=2000)
    ap.add_argument("--acceptance", type=int, default=6, help="temperament: experiments bringing nothing new before a question is let go")
    ap.add_argument("--luck", type=float, default=0.7, help="the dial (tetris's 0.7): the chance the other's reply is the one best for the mind")
    ap.add_argument("--checkpoint", type=int, default=1000, help="save the agent and the world every this many slices (0: never)")
    ap.add_argument("--resume", default=None, help="a checkpoint file to go on from")
    ap.add_argument("--dream", action="store_true", help="the dream planner between games (dream_go.py; Params.dreams)")
    args = ap.parse_args()
    import os
    os.makedirs(f"{HERE}/checkpoints", exist_ok=True)
    if args.resume:
        a, w, start = resume(args.resume)
        print(f"go seed {w.seed}: resumed from {args.resume} at slice {start}, luck {w.luck}", flush=True)
    else:
        a, w = build(args.seed, args.luck, args.acceptance, args.dream)
        start = 0
        print(f"go seed {args.seed}: a {w.size} x {w.size} board, {len(w.objs)} objects perceived at the start, luck {w.luck}", flush=True)
    shown, t0, read, taken = len(w.games), time.time(), len(a.pushed), 0
    for t in range(start, args.slices):
        a.mind.potentials = w.potentials()   # (as the maze's and tetris's)
        a.tick()
        read, took = give(a, w, read)
        taken += len(took)
        dreamt = shown < len(w.games) and a.mind.p.dreams and not a.watching and not a.queue
        while shown < len(w.games):
            g = w.games[shown]
            shown += 1
            print(f"  game {shown}: {g['stones']} stones placed in {g['slices']} slices; the mind took {g['black_took']}, lost {g['white_took']}; "
                  f"area {g['black_area']} to {g['white_area']}; lucky replies so far {w.lucky}; luck {w.luck} ({w.earned} games kept better)", flush=True)
        if dreamt:   # between games: the dream (dream_go.py)
            import dream_go
            td = time.time()
            trials, edges = dream_go.dream(a)
            print(f"    dream ({time.time() - td:.0f}s): {trials} trials, {edges} at the edge; imagination register {len(a.dreamed)}", flush=True)
        if args.checkpoint and (t + 1) % args.checkpoint == 0:
            checkpoint.save(a, w, t + 1, f"{HERE}/checkpoints/{'dream_' if a.mind.p.dreams else ''}seed{w.seed}_{t + 1}.pkl")
        if (t + 1) % 100 == 0:
            terr = a.mind.territory
            print(f"    slice {t + 1} ({time.time() - t0:.0f}s): goal {a.goal}, stack {a.stack}, stones this game {w.placed} (the mind's {w.black_placed}), "
                  f"regions {len(terr.rows)}, slots open {len(terr.open_slots())}", flush=True)
    terr, und = a.mind.territory, a.mind.understanding
    answers = a.__dict__.get("prediction_answers", [])
    print("the mind's stones placed:", sum(1 for i, _, _ in a.pushed), "| stones given as taken:", taken,
          "| taken over the run: by the mind", w.captures[BLACK], "by the other", w.captures["white"])
    print("predictions answered:", collections.Counter((o, "own push" if by != "wait" else "wait") for _, _, o, by in answers).most_common())
    print("wants set:", collections.Counter(g for _, g, k in a.sub_log if k == "set").most_common(10))
    print("wants met:", collections.Counter(g for _, g, k in a.sub_log if k == "met").most_common(6), "| reached:", collections.Counter(g for _, g in a.reached).most_common(6))
    print("territory:", {k: dict(collections.Counter(row["holder"] for r, row in terr.rows.items() if kind(r) == k)) for k in sorted({kind(r) for r in terr.rows})})
    print("slots open:", collections.Counter((k, kind(r)) for k, r in terr.open_slots()).most_common(10))
    print("commits:", dict(collections.Counter(x[2] for x in a.__dict__.get("commit_log", []))),
          "| committed to:", collections.Counter(x[1] for x in a.__dict__.get("commit_log", []) if x[2] == "made").most_common(5))
    print("anti-wants:", collections.Counter(k for _, _, k in a.__dict__.get("anti_log", [])).most_common())
    print("released (from attention):", len(getattr(und, "released", {})))
    print("games:", len(w.games), "| luck", w.luck, f"({w.earned} games kept better, {w.lucky} lucky replies)")


if __name__ == "__main__":
    main()
