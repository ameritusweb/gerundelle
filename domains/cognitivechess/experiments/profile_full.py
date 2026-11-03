"""Where a full game's time goes as the minds' records grow (stress test; both minds with winner_acts, the imagined lane
and news in the structure). Plays --warm games unprofiled, then profiles the next --games games.

Run: PYTHONHASHSEED=0 python -X utf8 experiments/profile_full.py [--seed 1] [--warm 12] [--games 1] [--top 30]
"""
import argparse, cProfile, io, os, pstats, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "fiction"))
import chess  # noqa: E402
from rung3 import make, TURN_STEPS  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--warm", type=int, default=12)
    ap.add_argument("--games", type=int, default=1); ap.add_argument("--top", type=int, default=45)
    a = ap.parse_args()
    w, minds = make(a.seed, "mind", "base", "keeper", given=True, fen=chess.STARTING_FEN, half_moves=120)
    for m in minds:
        p = m.agent.mind.p
        p.winner_acts = p.imagined_lane = p.news_in_structure = p.stuck_earns = True
    st = dict(done=0, t=time.time()); reset = w.reset

    def counted():
        st["done"] += 1
        print(f"game {st['done']}: {time.time() - st['t']:.0f}s", flush=True)
        st["t"] = time.time()
        reset()
    w.reset = counted
    by = {m.name: m for m in minds}; seen = {"White": 0, "Black": 0}

    def step(n):
        w.actor = n
        seen[n] = by[n].step(seen[n])

    def play_until(target):
        while st["done"] < target:
            mover = "White" if w.board.turn == chess.WHITE else "Black"
            other = "Black" if mover == "White" else "White"
            before = (w.moved, len(w.episodes))
            for _ in range(TURN_STEPS):
                step(mover)
                if (w.moved, len(w.episodes)) != before:
                    break
            step(other)
    play_until(a.warm)
    for m in minds:
        mi = m.agent.mind
        print(f"{m.name} after {a.warm} games: pool {len(mi.pool)}, boxes {len(mi.boxes)}, meta readings {len(mi.meta.modes)}, "
              f"splits {len(mi.meta.splits)}, understanding concepts {len(mi.understanding.rel)}, plans {len(mi.inquiry.plans)}, "
              f"pushed {len(m.agent.pushed)}, history {len(m.agent.history)}, territory rows {len(mi.territory.rows)}", flush=True)
    pr = cProfile.Profile()
    pr.enable()
    play_until(a.warm + a.games)
    pr.disable()
    for key in ("tottime", "cumulative"):
        out = io.StringIO()
        pstats.Stats(pr, stream=out).sort_stats(key).print_stats(a.top)
        print(f"===== by {key}"); print(out.getvalue())


if __name__ == "__main__":
    main()
