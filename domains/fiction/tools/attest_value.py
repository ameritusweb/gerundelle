"""What being told is worth: tries and ticks to the want, alone, with a companion who knows (a past lived
through on his own copy of the world), and with one who does not. The behavioural test of Attest.

Run: python tools/attest_value.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lean import LeanMind  # noqa: E402
import worlds  # noqa: E402
from worlds import C  # noqa: E402


def lock():
    w = C.lock_world(episode=None)
    w.gusts = []
    return w


SCENES = {"jack-in-the-box": (worlds.jack_in_the_box, "lid_releasing"), "lock and two keys": (lock, "door_releasing")}


def live(name, world, want, others=(), ticks=200):
    m = LeanMind(name, world, want=want, others=others)
    for _ in range(ticks):
        m.tick()
        if m.done:
            break
    return m


def live_gerundelle(name, world, want, others=(), ticks=300):
    from gerundelle_arm import GerundelleMind
    m = GerundelleMind(name, world, want=want, others=others)
    m.run(ticks)
    return m


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{'arm':10} {'scene':20} {'company':10} {'reached':>7} {'tries':>5} {'ticks':>5}  pushes")
    for scene, (make, want) in SCENES.items():
        ben = live("Ben", make(), want)   # his past: the same scene, lived through once
        for company, others in (("alone", ()), ("knows", (ben,)), ("ignorant", (LeanMind("Ben", make()),))):
            m = live("Mara", make(), want, others)
            pushes = ", ".join(f"{x.inv[0]} {x.inv[1]}" for x in m.tries)
            print(f"{'lean':10} {scene:20} {company:10} {str(m.done):>7} {len(m.tries):5d} {m.world.t:5d}  {pushes}")
            g = live_gerundelle("Mara", make(), want, others)
            pushes = ", ".join(f"{inv[0]} {inv[1]}" for _, inv, _ in g.agent.tried)
            print(f"{'gerundelle':10} {scene:20} {company:10} {str(g.done):>7} {len(g.agent.tried):5d} "
                  f"{g.world.t:5d}  {pushes}")


if __name__ == "__main__":
    main()
