"""What survives when imagination is taken away (chess-sov-plan.md: "what survives when the coach is removed is the mind's
own"). Rung 1's world and mind (both), imagining with a source for the first half of the ticks, then the same mind with
Params.imagine off for the second half. Defended wins and lost exchanges in each half, and the condition held.

Run: python -X utf8 withdraw1b.py SOURCE SEEDS [TICKS]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1  # noqa: E402  (first: it puts fiction, and so Gerundelle, on the path)
from chessworld import RUNG1, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

src, seeds = sys.argv[1], int(sys.argv[2])
ticks = int(sys.argv[3]) if len(sys.argv) > 3 else 800
for k in range(seeds):
    w = ChessWorld(RUNG1, order=k, seed=k, reply="recapture", moves=2, imagine=None if src == "none" else src)
    m = GerundelleMind("White", w, want=rung1.WANT, want_count=10 ** 6)
    for a, v in rung1.ARMS["both"].items():
        setattr(m.agent.mind.p, a, v)
    m.agent.mind.p.imagine = src != "none"
    log, act = [], w.act

    def logged(inv=None, hold=False):
        ev = act(inv, hold)
        log.append((len(w.episodes), w.config, inv, ev))
        return ev
    w.act = logged
    halves = []
    try:
        for half in (0, 1):
            if half == 1:
                m.agent.mind.p.imagine, w.imagined_by = False, None
            start = len(log)
            m.run(ticks // 2)
            part = log[start:]
            won = sum(1 for _, c, _, ev in part if c == 0 and "material: even -> up" in ev)
            lost = sum(1 for _, c, _, ev in part if c == 0 and any(e.startswith("material:") and e.endswith("-> down") for e in ev))
            eps = len({e for e, c, _, _ in part if c == 0})
            halves.append(f"{won:3} won / {lost:2} lost of {eps:2} defended episodes")
    finally:
        w.close()
    splits = sorted({s["tag"] for x, s in m.agent.mind.meta.splits.items() if "Rxd5" in x})
    print(f"{src} seed {k}: imagining {halves[0]} | after, alone {halves[1]} | Rxd5 split {splits}", flush=True)
