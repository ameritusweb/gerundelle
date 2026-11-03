"""Does a mind that imagines still learn the defender's condition from lived play? The split on Rxd5, per seed."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1  # noqa: E402

src = sys.argv[1]
for k in range(int(sys.argv[2])):
    w, m, log = rung1.run(k, "both", 800, src)
    r = rung1.measure(w, m, log)
    rx = sum(1 for _, inv, _ in m.agent.tried if "Rxd5" in inv[0])
    print(f"{src} seed {k}: Rxd5 splits {sorted(set(r['splits'].values()))}  polarity {r['polar']}  Rxd5 pushed {rx}", flush=True)
