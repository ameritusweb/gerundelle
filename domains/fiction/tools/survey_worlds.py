"""Survey Gerundelle's curriculum worlds: states, pushes, and every change a curious lean mind (no want) makes."""
import inspect
import os
import sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import worlds  # noqa: E402
from lean import LeanMind  # noqa: E402
C = worlds.C
names = [n for n, f in inspect.getmembers(C, inspect.isfunction) if n.endswith("_world") and n not in ("renamed",)]
for n in sorted(names):
    f = getattr(C, n)
    try:
        kw = {"episode": None} if "episode" in inspect.signature(f).parameters else {}
        w = f(**kw)
        st = {k: v for k, v in w.states().items() if k not in ("ground",)}
        m = LeanMind("X", w)
        flips = Counter()
        for _ in range(120):
            m.tick()
        for b in m.beats:
            if b.kind in ("change", "other") and b.obj != "flag":
                flips[f"{b.obj}:{b.detail['from']}>{b.detail['to']}"] += 1
        print(f"{n}: {st}")
        print(f"    pushes {sorted({(i[0][0], i[1]) for i in w.invitations()})}")
        print(f"    flips {dict(flips)}")
    except Exception as ex:
        print(f"{n}: ERROR {type(ex).__name__} {ex}")
