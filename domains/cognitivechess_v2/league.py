"""A league of temperament profiles playing chess, ranked by Elo (the user, 2026-11-17: "can you set up a league like we did with Go?
With different temperaments"). After go/league.py.

Decided by the user (2026-11-17):
- Mind vs mind: two lifelong minds per profile, a White one and a Black one, each keeping its seat for life (chessduel.py).
- Go's 11 profiles (go/league.py's PROFILES).
- Endings: the rules (checkmate, stalemate, insufficient material, threefold repetition, the fifty-move rule), seventh-heaven chess for
  either side (a side resigns at its opponent's 7th new forced mate in the game), and the 300 half-move cap as a draw. For now the 3rd
  (RESIGN_AFTER, --resign-after; the user, 2026-11-17: "temporarily set it to the 3rd forced mate at first to see how it goes").

Carried over from Go's league (my choices there, kept here; each can change):
- Elo: everyone starts at 1500, K = 24, a profile's rating pooled over both its minds' games.
- Interleaved rounds: each round is 10 sub-rounds; in sub-round k the White mind of profile i meets the Black mind of profile i + k
  (mod 11), so every mind plays once per sub-round, and over a round every ordered pair meets once. A sub-round's games run in batches
  of WORKERS (3) in parallel processes (Go ran all 11 at once); Elo, results.jsonl and state.json are updated after each batch.
- Each mind is saved after every game (league/minds/<profile>_<colour>.pkl, rung4p.save_run), so the league resumes where it stopped.
- Every mind as rung 4p --dreams (want-dreams on the quiet register), seeded by its place in the list (White 2i, Black 2i + 1).

Run: set PYTHONHASHSEED=0; python -u -X utf8 league.py [--rounds 3] [--workers 11] [--dir league] [--subrounds N]
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

HERE = __import__("paths").domain('cognitivechess_v2')
DIR = f"{HERE}/league"
HALF_MOVES = 300
CAP_SLICES = 20000   # (the duel's own safety cap; the half-move cap ends every game first)
RESIGN_AFTER = 3     # temporarily the 3rd new forced mate, not seventh-heaven's 7th (the user, 2026-11-17: "temporarily set it to the 3rd
                     # forced mate at first to see how it goes"); --resign-after 7 for seventh-heaven chess
K, START = 24.0, 1500.0
WORKERS = 3   # a sub-round's 11 games run 3 at a time (the user, 2026-11-17: "why not run the league games in batches of 2 or 3"; Go ran
              # all 11 at once, but chess minds grow to GBs: 22 loaded at once would strain memory, and would compete with other runs)

PROFILES = {   # go/league.py's
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
    "accepting_patient": dict(acceptance=3, patience=6),   # (the user, 2026-11-17: "a temperament that is both 'accepting' AND 'patient'")
    "scientific": dict(experimentation=3),   # (the user, 2026-11-17: "another temperament similar to experimentation or scientific
    #   curiosity"): goes on experimenting through up to 3 regions at stake; the others yield at any (chessduel.configure: 0)
}
NAMES = list(PROFILES)
COLOURS = (("white", True), ("black", False))


def path(profile, colour, folder=None):
    return f"{folder or DIR}/minds/{profile}_{colour}.pkl"


PROFILE_KEYS = sorted({k for over in PROFILES.values() for k in over})


def seat_copy(agent, world, side, seed, half_moves):
    """`agent` (a loaded mind, its world `world`) on a fresh seat for `side` at the start position (chessduel.fresh_seat)."""
    from chessduel import fresh_seat
    w = fresh_seat(agent, side, old=world, half_moves=half_moves)
    w.seed = seed
    return w


def create(folder, half_moves, source=None):
    """Every profile's two minds, each on its own seat, saved before their first game. Fresh, or (source) each a copy of one checkpoint's
    mind with the profile's Params (the user, 2026-11-17: "start from the latest checkpoint"; "All 22 from g12": the Black minds too,
    re-seated, their territory learned from White's seat)."""
    import rung4p
    from chessduel import configure, new_mind
    os.makedirs(f"{folder}/minds", exist_ok=True)
    todo = [(i, j, name, over, colour, side) for i, (name, over) in enumerate(PROFILES.items()) for j, (colour, side) in enumerate(COLOURS)
            if not os.path.exists(path(name, colour, folder))]
    if not todo:
        return
    if source is None:
        for i, j, name, over, colour, side in todo:
            agent, world = new_mind(side, over, seed=2 * i + j, half_moves=half_moves)
            rung4p.save_run(path(name, colour, folder), agent, world, None, {"profile": name, "colour": colour})
        return
    for colour, side in COLOURS:   # (loaded once per colour: each copy is saved before the next profile's Params are set)
        mine = [t for t in todo if t[5] == side]
        if not mine:
            continue
        agent, world, _, _ = rung4p.load_run(source)
        base = {k: getattr(agent.mind.p, k) for k in PROFILE_KEYS}
        w = seat_copy(agent, world, side, seed=0, half_moves=half_moves)
        for i, j, name, over, colour_, side_ in mine:
            for k, v in base.items():
                setattr(agent.mind.p, k, v)
            configure(agent, over)
            w.seed = 2 * i + j
            rung4p.save_run(path(name, colour, folder), agent, w, None, {"profile": name, "colour": colour, "from": source})
            print(f"   {name} {colour}: from {source}", flush=True)


def play(job):
    """One game: White-of-w against Black-of-b, both loaded, played to the end, both saved. -> the result."""
    w, b, tag, folder, resign_after = job
    sys.path.insert(0, HERE)
    log = open(f"{folder}/logs/{tag}.log", "w", encoding="utf-8")
    import rung4p
    from chessduel import BLACK, WHITE, ChessDuel
    agents, worlds, states = {}, {}, {}
    for name, (colour, side) in ((w, COLOURS[0]), (b, COLOURS[1])):
        agents[side], worlds[side], _, states[side] = rung4p.load_run(path(name, colour, folder))
        worlds[side].RESIGN_AFTER_NEW_MATES = resign_after   # (--resign-after; set every game, so a change takes effect at once)
    before = {s: (len(worlds[s].__dict__.get("forced_mate_log", [])), len(agents[s].__dict__.get("mates_passed", [])),
                  len(agents[s].__dict__.get("want_dreams_done", []))) for s in (WHITE, BLACK)}
    d = ChessDuel(agents, worlds, log=lambda s: print(s, file=log, flush=True))
    d.why_path = f"{folder}/logs/{tag}.why.jsonl"   # each move's explanation (why.py), read by watch_league.py
    open(d.why_path, "w").close()
    d.profiles = {WHITE: w, BLACK: b}
    print(f"{tag}: White {w} vs Black {b}", file=log, flush=True)
    t0 = time.time()
    result, balance, half_moves = d.play_game(cap_slices=CAP_SLICES)
    rb = worlds[BLACK].games[-1]
    if rb[0] != result:
        raise RuntimeError(f"the seats recorded different results: {result} vs {rb[0]}")
    winner = "white" if result.startswith("1-0") else "black" if result.startswith("0-1") else "draw"
    r = dict(white=w, black=b, tag=tag, result=result, winner=winner, white_balance=balance, half_moves=half_moves, slices=d.clock,
             seconds=round(time.time() - t0))
    for s, key in ((WHITE, "white"), (BLACK, "black")):
        fm, mp_, wd = before[s]
        r[f"{key}_new_forced_mates"] = len(worlds[s].__dict__.get("forced_mate_log", [])) - fm
        r[f"{key}_mates_passed"] = len(agents[s].__dict__.get("mates_passed", [])) - mp_
        r[f"{key}_want_dreams"] = len(agents[s].__dict__.get("want_dreams_done", [])) - wd
    for name, (colour, side) in ((w, COLOURS[0]), (b, COLOURS[1])):
        st = dict(states[side] or {})
        st["games"] = st.get("games", 0) + 1
        rung4p.save_run(path(name, colour, folder), agents[side], worlds[side], None, st)
    print(json.dumps(r), file=log, flush=True)
    log.close()
    import mate_oracle   # (Stockfish closed: its reader thread kept the worker from exiting, and the pool, one game per worker, never
    mate_oracle.close()  #  got a worker for the next batch; the first batched trial hung after its first batch)
    return r


def finished(folder, tag):
    """A game's result if its log ends with one (play's last line: the game ended and both minds were saved), else None."""
    try:
        with open(f"{folder}/logs/{tag}.log", "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 4000))
            last = f.read().decode("utf-8", "ignore").strip().splitlines()[-1:]
        if last and last[0].startswith("{"):
            r = json.loads(last[0])
            return r if r.get("tag") == tag else None
    except (OSError, ValueError):
        pass
    return None


def expected(ra, rb):
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--dir", default=DIR)
    ap.add_argument("--subrounds", type=int, default=None, help="stop after this many sub-rounds this run (a trial)")
    ap.add_argument("--half-moves", type=int, default=HALF_MOVES, help="the game's cap for new minds (a trial: fewer)")
    ap.add_argument("--from", dest="source", default=None,
                    help="a checkpoint (rung4p.save_run's) every new mind is copied from, White and Black, with its profile's Params")
    ap.add_argument("--resign-after", type=int, default=RESIGN_AFTER,
                    help="a side resigns at its opponent's Nth new forced mate in a game (seventh-heaven chess: 7)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if os.environ.get("PYTHONHASHSEED") != "0":
        sys.exit("set PYTHONHASHSEED=0 (the minds are saved and loaded with it)")
    folder = args.dir
    os.makedirs(f"{folder}/logs", exist_ok=True)
    create(folder, args.half_moves, args.source)
    state_path = f"{folder}/state.json"
    state = (json.load(open(state_path)) if os.path.exists(state_path)
             else dict(done=[], elo={n: START for n in NAMES}, games={n: 0 for n in NAMES}))
    print(f"chess league: {len(NAMES)} profiles x 2 minds; resign at the opponent's new forced mate {args.resign_after}; "
          f"Elo start {START}, K {K}; rounds {args.rounds}; "
          f"{len(state['done'])} sub-rounds done before", flush=True)
    n, played = len(NAMES), 0
    with mp.get_context("spawn").Pool(args.workers, maxtasksperchild=1) as pool:
        for rnd in range(args.rounds):
            for k in range(1, n):
                key = f"{rnd}:{k}"
                if key in state["done"]:
                    continue
                if args.subrounds is not None and played >= args.subrounds:
                    return
                played += 1
                jobs = [(NAMES[i], NAMES[(i + k) % n], f"r{rnd}_k{k}_{NAMES[i]}_vs_{NAMES[(i + k) % n]}", folder, args.resign_after)
                        for i in range(n)]
                t0 = time.time()
                state.setdefault("games_done", [])
                todo = [j for j in jobs if j[2] not in state["games_done"]]   # (a sub-round stopped part-way resumes at its next game)
                for start in range(0, len(todo), args.workers):
                    # a batch of WORKERS games; Elo, results and state after each batch (the user, 2026-11-17: "update after each
                    # batch"; first after the whole sub-round, as Go), in the fixed order of the jobs (a profile's rating pooled
                    # over its two minds)
                    batch = todo[start:start + args.workers]
                    tb = time.time()
                    # a game that finished in a batch that then failed (its minds saved, its result its log's last line) is taken from
                    # its log, not played again (2026-11-17: Stockfish crashed one game of a batch, and the league stopped with two
                    # finished games unrecorded)
                    done_before = {j[2]: finished(folder, j[2]) for j in batch}
                    to_play = [j for j in batch if not done_before[j[2]]]
                    played_now = dict(zip((j[2] for j in to_play), pool.map(play, to_play, chunksize=1))) if to_play else {}
                    results = [done_before[j[2]] or played_now[j[2]] for j in batch]
                    for r in results:
                        if done_before.get(r["tag"]):
                            print(f"   ({r['tag']}: finished before the league stopped; its result taken from its log)", flush=True)
                    for r in results:
                        s = 1.0 if r["winner"] == "white" else 0.0 if r["winner"] == "black" else 0.5
                        ew = expected(state["elo"][r["white"]], state["elo"][r["black"]])
                        state["elo"][r["white"]] += K * (s - ew)
                        state["elo"][r["black"]] += K * ((1 - s) - (1 - ew))
                        state["games"][r["white"]] += 1
                        state["games"][r["black"]] += 1
                        state["games_done"].append(r["tag"])
                        with open(f"{folder}/results.jsonl", "a", encoding="utf-8") as f:
                            f.write(json.dumps(dict(r, round=rnd, k=k)) + "\n")
                        print(f"   {r['white']:>11s} (W) vs {r['black']:<11s} (B): {r['result']}, {r['half_moves']} half-moves, "
                              f"White's balance {r['white_balance']:+d}, new forced mates W {r['white_new_forced_mates']} / "
                              f"B {r['black_new_forced_mates']}, {r['seconds']}s", flush=True)
                    if start + args.workers >= len(todo):
                        state["done"].append(key)
                    json.dump(state, open(state_path, "w"), indent=1)
                    table = sorted(state["elo"].items(), key=lambda x: -x[1])
                    print(f"round {rnd + 1}, sub-round {k}, batch of {len(batch)} ({time.time() - tb:.0f}s): Elo "
                          + ", ".join(f"{name} {e:.0f}" for name, e in table), flush=True)
                print(f"round {rnd + 1}, sub-round {k} done ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
