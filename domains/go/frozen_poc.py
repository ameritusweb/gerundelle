"""Frozen play, a first proof of concept (FROZEN_PLAY.md; the user, 2026-11-13: "we can use that to create a frozen play POC to see what
happens"). The league's minds as zipped mid-league (frozen_poc/minds/, copies: the league's own files are never touched) play the same
pairing twice from identical copies: once as in the league (learning), once frozen. Nothing is saved back.

Frozen, in this first cut (my reading of FROZEN_PLAY.md's table, the narrowest freeze):
- Understanding.add (every relation written into the SOV: receipts, lived or told) queues instead of writing;
- Understanding.analogize (Abstract, and the concept abstracts it runs) is skipped.
Everything else stays live: perception, the territory register, wants and anti-wants, the tournament, commits, questions and experiments,
the meta layer. The wrappers are on the classes in this process only (no Gerundelle file changes).

Reported per game: seconds, slices, seconds per slice, stones, area and winner, the mind's relations before and after (learning) or the
queue's size (frozen), and each side's placements in order, so where the two games' moves part can be read.
Run: PYTHONHASHSEED=0 python -u -X utf8 frozen_poc.py [--pairs trusting:unflinching patient:dogged]"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

HERE = __import__("paths").domain('go')
MINDS = f"{HERE}/frozen_poc/minds"
CAP_SLICES = 1500


def relations(agent):
    return sum(len(r) for r in agent.mind.understanding.rel.values())


def play(job):
    black, white, mode = job
    frozen = mode != "learning"
    sys.path.insert(0, HERE)
    import run  # noqa: F401  (first: Gerundelle, warpchess and tetris on the path)
    import checkpoint
    import molecules
    from goduel import Duel
    queue = []
    if frozen:   # the learning half of a slice, frozen (this process only)
        add, analogize = molecules.Understanding.add, molecules.Understanding.analogize

        def frozen_add(self, c, rel, other, how, w=1.0):
            if mode == "frozen_told" and how == "told":   # (second cut: what the mind tells itself from the world's predictions is how
                return add(self, c, rel, other, how, w)   # it perceives the forces: acting, not learning, so written as in play)
            if mode == "frozen_enables" and rel == "enables":   # (third cut: what held while a push was on offer, frozen_diverge.py's
                return add(self, c, rel, other, how, w)          # finding; written as in play)
            queue.append((getattr(self.mind, "t", None), c, rel, other, how, w))

        def frozen_analogize(self, rec):
            return None
        molecules.Understanding.add = frozen_add
        if mode != "frozen_live":   # (frozen_live: the real Abstract runs, now cheap where nothing changed: molecules.py's core memo,
            molecules.Understanding.analogize = frozen_analogize   # go/abstract_ref.py; every write still queued)
    agents, seats = {}, {}
    for name, colour in ((black, "black"), (white, "white")):
        agent, seat, _ = checkpoint.load(f"{MINDS}/{name}_{colour}.pkl")
        agents[colour], seats[colour] = agent, seat
    before = {c: relations(a) for c, a in agents.items()}
    d = Duel(seats=(seats["black"], seats["white"]))
    placed = {"black": [], "white": []}

    def after(colour, agent, seat):
        agent._league_read, _ = run.give(agent, seat, agent.__dict__.get("_league_read", 0))
        if seat.log and seat.log[-1][0] == seat.t - 1 and seat.log[-1][2] and seat.log[-1][1] != "hand":
            placed[colour].append(seat.log[-1][1].replace("point_", ""))

    t0 = time.time()
    while not d.results and d.clock < CAP_SLICES:
        d.step(agents, after)
    secs = time.time() - t0
    r = dict(d.results[0]) if d.results else dict(called=True, stones=seats["black"].placed)
    area = seats["black"].area() if not d.results else None
    if area:
        r.update(black_area=area["black"], white_area=area["white"],
                 winner="draw" if area["black"] == area["white"] else ("black" if area["black"] > area["white"] else "white"))
    after_rel = {c: relations(a) for c, a in agents.items()}
    return dict(black=black, white=white, mode=mode, seconds=round(secs), slices=d.clock,
                per_slice=round(secs / max(1, d.clock), 3), stones=r.get("stones"), winner=r.get("winner"),
                area=f"{r.get('black_area')}-{r.get('white_area')}", relations_before=before, relations_after=after_rel,
                queued=len(queue), placed=placed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="*", default=["trusting:unflinching", "patient:dogged"])
    ap.add_argument("--modes", nargs="*", default=["learning", "frozen"],
                    help="learning; frozen (every SOV write queued); frozen_told (told writes pass, the rest queued)")
    ap.add_argument("--out", default="results.json")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    jobs = [(p.split(":")[0], p.split(":")[1], mode) for p in args.pairs for mode in args.modes]
    with mp.get_context("spawn").Pool(len(jobs)) as pool:
        results = pool.map(play, jobs)
    os.makedirs(f"{HERE}/frozen_poc", exist_ok=True)
    with open(f"{HERE}/frozen_poc/{args.out}", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    earlier = []   # (the other runs' games, from the same copies of the minds: shown beside these)
    for old in ("results.json", "results_told.json", "results_enables.json", "results_live.json"):
        if old != args.out:
            try:
                earlier += json.load(open(f"{HERE}/frozen_poc/{old}", encoding="utf-8"))
            except (OSError, ValueError):
                pass
    for p in args.pairs:
        b, w = p.split(":")
        pair = {r["mode"]: r for r in results + earlier if r["black"] == b and r["white"] == w}
        print(f"\n{b} (Black) vs {w} (White)")
        for mode in [m for m in ("learning", "frozen", "frozen_told", "frozen_enables", "frozen_live") if m in pair]:
            r = pair[mode]
            grew = {c: r["relations_after"][c] - r["relations_before"][c] for c in r["relations_before"]}
            print(f"  {mode:8s}: {r['seconds']:5d}s, {r['slices']} slices ({r['per_slice']}s each), {r['stones']} stones, {r['winner']} {r['area']}; "
                  f"relations written {grew}, queued {r['queued']}")
        for other in [m for m in ("frozen", "frozen_told", "frozen_enables", "frozen_live") if m in pair and "learning" in pair]:
            for colour in ("black", "white"):
                a_, b_ = pair["learning"]["placed"][colour], pair[other]["placed"][colour]
                k = next((i for i, (x, y) in enumerate(zip(a_, b_)) if x != y), min(len(a_), len(b_)))
                print(f"  {colour}'s placements, learning vs {other}: the same for the first {k} (learning {len(a_)}, {other} {len(b_)})")


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
