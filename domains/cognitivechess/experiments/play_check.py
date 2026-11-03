"""Checks play.py's engine without a window: self-play N games, then a game against random legal 'human' moves, on each side;
a new game; and the force button. Prints what the panel would show.

Run: python -X utf8 experiments/play_check.py [--n 1] [--half 40] [--side both]
"""
import argparse
import os
import queue
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import chess  # noqa: E402
from play import Engine  # noqa: E402


def drain(e, wait=120.0, until=None):
    """Latest snapshot, once the engine has settled (`until` holds, or nothing comes for a moment)."""
    last, t0, quiet = None, time.time(), time.time()
    while time.time() - t0 < wait:
        try:
            s = e.out.get(timeout=0.2)
            if "error" in s:
                raise SystemExit("ENGINE ERROR:\n" + s["error"])
            last, quiet = s, time.time()
            if until and until(s):
                return s
        except queue.Empty:
            if last and not until and time.time() - quiet > 1.0:
                return last
    raise SystemExit(f"timed out; last status: {last and last['status']}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1); ap.add_argument("--half", type=int, default=40); ap.add_argument("--side", default="both")
    a = ap.parse_args()
    rng = random.Random(0)
    for side in (("white", "black") if a.side == "both" else (a.side,)):
        e = Engine(games=a.n, side=side, seed=1)
        e.start()
        ready = lambda s: s["playing"] and (s["status"] == "Your move." or s["stalled"] or "win" in s["status"] or "mates" in s["status"] or "Draw" in s["status"])
        s = drain(e, 600, ready)
        forced = 0
        while len(s["log"]) < a.half:
            if s["stalled"]:
                forced += 1
                e.send("force")
                s = drain(e, 120, ready)
                continue
            b = chess.Board(s["fen"])
            if b.is_game_over() or s["status"] != "Your move.":
                break
            m = rng.choice(list(b.legal_moves))
            n = len(s["log"])
            e.send("move", m.from_square, m.to_square)
            s = drain(e, 300, lambda x: ready(x) and len(x["log"]) >= n + 1 and (x["stalled"] or len(x["log"]) >= n + 2 or x["status"] != "Your move." or True) and x["status"] != "The mind is thinking…")
        print(f"=== you play {side}: {len(s['log'])} half-moves; forced {forced}; status: {s['status']}")
        print("  moves:", " ".join(f"{san}[{why}]" for _, san, why in s["log"][:14]))
        print("  want:", s["want"], "| stack:", s["stack"])
        print("  why:", s["why"]); print("  expected:", s["expected"])
        print("  attention:", {k: v[:2] for k, v in s["attention"].items()})
        print("  feelings:", s["feelings"][:3]); print("  holds:", s["holders"], "lost", s["lost"][:3], "slots", s["slots"])
        print("  learned:", s["learned"][-3:]); print("  size:", s["size"])
        e.send("new")
        s2 = drain(e, 120, ready)
        print(f"  new game: board reset {s2['fen'].split()[0] == chess.STARTING_FEN.split()[0] or len(s2['log']) <= 1}; log {len(s2['log'])}; status {s2['status']}")
        e.send("stop")
    print("OK")


if __name__ == "__main__":
    main()
