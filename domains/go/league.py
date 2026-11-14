"""A league of temperament profiles playing Go, ranked by Elo (the user, 2026-11-13: "have multiple minds; keep ELO rankings for
different temperament profiles; have them compete; do a study to find which temperament profiles shine at Go").

Decided by the user (2026-11-13):
- Lifelong minds: one mind per profile and colour plays the whole league and keeps learning; Elo follows it as it changes.
- Two minds per profile, a Black one and a White one, each keeping its colour for life (stones and readings are named by real colour,
  the 2026-11-11 ruling); colours alternate between profiles: Black-of-A meets White-of-B and Black-of-B meets White-of-A.
- Area scoring, no komi; equal area is a draw.
- Profiles: fiction/temperament.py's that have a home in Gerundelle's Params (stubbornness has none yet, left out), plus aversion and
  acceptance halved and doubled.

My choices (each can change; stated in the log's header):
- Elo: everyone starts at 1500, K = 24, a profile's rating pooled over both its minds' games.
- Interleaved rounds (lifelong minds learn from every game, so a pair's games aren't played in one block): each round is 10 sub-rounds;
  in sub-round k, the Black mind of profile i meets the White mind of profile i + k (mod 11), so every mind plays once per sub-round, the
  11 games in parallel processes, and over a round every ordered pair of profiles meets once.
- A game is called after CAP_SLICES duel slices if it hasn't ended (the world's own cap of 98 stones ends nearly all of them first).
- Each mind is saved after every game (league/minds/<profile>_<colour>.pkl, tetris/checkpoint.py), so the league resumes where it stopped.

Run: PYTHONHASHSEED=0 python -u -X utf8 league.py [--rounds 3] [--workers 11]
"""
import argparse
import json
import math
import multiprocessing as mp
import os
import sys
import time

HERE = __import__("paths").domain('go')
DIR = f"{HERE}/league"   # (--dir: another folder, e.g. for a trial that mustn't touch the league's lifelong minds)
CAP_SLICES = 1500
K, START = 24.0, 1500.0

PROFILES = {   # Gerundelle Params per profile (fiction/temperament.py's names; acceptance 6 is the Go mind's own, run.py)
    "steady": {},
    "impatient": dict(patience=2),
    "patient": dict(patience=6),
    "restless": dict(persistence=0.25, curiosity=2.0),
    "dogged": dict(persistence=4.0, curiosity=0.5),
    "trusting": dict(credulity=0.9),
    "skeptical": dict(credulity=0.1),
    "averse": dict(aversion=2.0),
    "unflinching": dict(aversion=0.5),
    "accepting": dict(acceptance=3),
    "grieving": dict(acceptance=12),
}
NAMES = list(PROFILES)


def path(profile, colour, folder=None):
    return f"{folder or DIR}/minds/{profile}_{colour}.pkl"


def create(folder):
    """Every profile's two minds, each on its own seat, saved before their first game."""
    import run  # noqa: F401  (first: it puts Gerundelle, warpchess and tetris on the path)
    import checkpoint
    import duel_run
    from goduel import GoSeat
    os.makedirs(f"{folder}/minds", exist_ok=True)
    for name, over in PROFILES.items():
        for colour in ("black", "white"):
            if os.path.exists(path(name, colour, folder)):
                continue
            seat = GoSeat(None, colour)
            agent = duel_run.mind(seat, over)
            checkpoint.save(agent, seat, 0, path(name, colour, folder))


def play(job):
    """One game: Black-of-b against White-of-w, both loaded, played to the end, both saved. -> the result."""
    b, w, tag, folder = job
    sys.stdout = open(f"{folder}/logs/{tag}.log", "w", encoding="utf-8")
    import run
    import checkpoint
    from goduel import Duel
    agents, seats = {}, {}
    for name, colour in ((b, "black"), (w, "white")):
        agent, seat, _ = checkpoint.load(path(name, colour, folder))
        agents[colour], seats[colour] = agent, seat
    d = Duel(seats=(seats["black"], seats["white"]))

    def after(colour, agent, seat):
        agent._league_read, _ = run.give(agent, seat, agent.__dict__.get("_league_read", 0))

    t0 = time.time()
    while not d.results and d.clock < CAP_SLICES:
        d.step(agents, after)
    if not d.results:   # called: the board as it stands is the result (my choice; see the header)
        area = seats["black"].area()
        r = dict(black_area=area["black"], white_area=area["white"], stones=seats["black"].placed, slices=d.clock, called=True,
                 black_took=seats["black"].took["black"], white_took=seats["black"].took["white"])
        r["winner"] = "draw" if area["black"] == area["white"] else ("black" if area["black"] > area["white"] else "white")
    else:
        r = dict(d.results[0])
    for colour, name in (("black", b), ("white", w)):
        seats[colour].duel = None
        checkpoint.save(agents[colour], seats[colour], 0, path(name, colour, folder))
    r.update(black=b, white=w, tag=tag, seconds=round(time.time() - t0))
    print(json.dumps(r), flush=True)
    return r


def expected(ra, rb):
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def main():
    global NAMES   # (--names replaces the profiles played)
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=len(NAMES))
    ap.add_argument("--dir", default=DIR)
    ap.add_argument("--subrounds", type=int, default=None, help="stop after this many sub-rounds this run (a trial)")
    ap.add_argument("--names", nargs="*", default=None,
                    help="the profiles to play, their minds already in <dir>/minds (evo_make.py); default: PROFILES, made if missing")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    folder = args.dir
    os.makedirs(f"{folder}/logs", exist_ok=True)
    if args.names:
        NAMES = list(args.names)
        missing = [p for n_ in NAMES for p in (path(n_, "black", folder), path(n_, "white", folder)) if not os.path.exists(p)]
        assert not missing, missing
    else:
        create(folder)
    state_path = f"{folder}/state.json"
    state = json.load(open(state_path)) if os.path.exists(state_path) else dict(done=[], elo={n: START for n in NAMES}, games={n: 0 for n in NAMES})
    print(f"league: {len(NAMES)} profiles x 2 minds; Elo start {START}, K {K}; rounds {args.rounds}; {len(state['done'])} sub-rounds done before", flush=True)
    n, played = len(NAMES), 0
    with mp.get_context("spawn").Pool(args.workers) as pool:
        for rnd in range(args.rounds):
            for k in range(1, n):
                key = f"{rnd}:{k}"
                if key in state["done"]:
                    continue
                if args.subrounds is not None and played >= args.subrounds:
                    return
                played += 1
                jobs = [(NAMES[i], NAMES[(i + k) % n], f"r{rnd}_k{k}_{NAMES[i]}_vs_{NAMES[(i + k) % n]}", folder) for i in range(n)]
                t0 = time.time()
                results = pool.map(play, jobs)
                for r in results:   # Elo, in the fixed order of the jobs (the profile's rating pooled over its two minds)
                    s = 1.0 if r["winner"] == "black" else 0.0 if r["winner"] == "white" else 0.5
                    eb = expected(state["elo"][r["black"]], state["elo"][r["white"]])
                    state["elo"][r["black"]] += K * (s - eb)
                    state["elo"][r["white"]] += K * ((1 - s) - (1 - eb))
                    state["games"][r["black"]] += 1
                    state["games"][r["white"]] += 1
                    with open(f"{folder}/results.jsonl", "a", encoding="utf-8") as f:
                        f.write(json.dumps(dict(r, round=rnd, k=k)) + "\n")
                state["done"].append(key)
                json.dump(state, open(state_path, "w"), indent=1)
                wins = {"black": sum(r["winner"] == "black" for r in results), "white": sum(r["winner"] == "white" for r in results),
                        "draw": sum(r["winner"] == "draw" for r in results)}
                table = sorted(state["elo"].items(), key=lambda x: -x[1])
                print(f"round {rnd + 1}, sub-round {k} ({time.time() - t0:.0f}s): {wins}; Elo "
                      + ", ".join(f"{name} {e:.0f}" for name, e in table), flush=True)


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
