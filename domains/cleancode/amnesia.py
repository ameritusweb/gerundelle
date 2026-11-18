"""The amnesia control (LADDER.md rung 2, the contamination question, 2026-11-15): the same run, but
a fresh mind for every problem — nothing carried. If the settle rate holds flat across positions
where the carrying mind declines, accumulation is the poison (contamination or crowding); if amnesia
does worse, carrying helps net and the late decline is something else. The discriminating control
before any contamination fix is built.

Run: PYTHONHASHSEED=0 python -u -X utf8 amnesia.py --seed 0 --slices 2000
"""
import sys

import run as runmod
from run import AVERSION, SWITCHES

sys.path.insert(0, __import__("paths").GERUNDELLE)
from molecules import Params   # noqa: E402
from sov_agent import SovAgent   # noqa: E402
from potential import ForceMind   # noqa: E402

SEED = int(next((x.split("=")[1] for x in sys.argv if x.startswith("--seed=")), "0"))
N = int(next((x.split("=")[1] for x in sys.argv if x.startswith("--slices=")), "2000"))


def fresh(w):
    a = SovAgent(w, ForceMind(Params(**SWITCHES)))
    a.mind.p.acceptance = 6
    a.mind.p.aversion = AVERSION
    a.mind.p.dreams = True
    a.mind.p.dream_when_stuck = True
    import dream_code
    a.dreamer = dream_code.dreamer
    return a


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    _, w = runmod.build("2", SEED, dream=True)
    a = fresh(w)
    shown, problem = 0, w.problems
    for t in range(N):
        if w.problems != problem:   # a new problem: a new mind (the world goes on; nothing carried)
            a = fresh(w)
            problem = w.problems
        a.mind.potentials = w.potentials()
        a.tick()
        runmod.give(a, w)
        while shown < len(w.solved):
            s = w.solved[shown]
            shown += 1
            print(f"  problem {shown} ({s['name']}): {'settled' if s['settled'] else 'not settled'} in "
                  f"{s['slices']} slices, {s['turns']} turns", flush=True)
    print(f"amnesia seed {SEED}: {len(w.solved)} closed, {sum(s['settled'] for s in w.solved)} settled")


if __name__ == "__main__":
    main()
