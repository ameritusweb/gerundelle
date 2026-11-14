"""Go on from a checkpoint with the commit push on (Params.commit; the user, 2026-11-12), saving checkpoints as it goes.
Run: PYTHONHASHSEED=0 python -u -X utf8 run_commit.py <checkpoint> <to slice> [name, default commit]
Every 200 slices: games ended, pieces cleared by runs and rows cleared since the start, predictions confirmed and rejected since the
start, commits made and how they came out. Every 1000: checkpoints/<name>_<slice>.pkl."""
import collections
import sys
import time

import run  # noqa: F401
import checkpoint

sys.stdout.reconfigure(encoding="utf-8")
args = [x for x in sys.argv[1:] if not x.startswith("--")]
path, to = args[0], int(args[1])
name = args[2] if len(args) > 2 else "commit"
a, w, start = checkpoint.load(path)
a.mind.p.commit = "--no-commit" not in sys.argv
und = a.mind.understanding
t_first, games0, lines0 = a.mind.t, len(w.games), w.lines
cleared, t0 = 0, time.time()
print(f"from {path} at slice {start}, commit {'on' if a.mind.p.commit else 'off'}, ground pieces {'held' if '--no-ground' not in sys.argv else 'not held'}, to slice {to}", flush=True)
for t in range(start, to):
    before = w.__dict__.get("pieces_cleared", 0)
    a.mind.potentials = w.potentials()
    a.tick()
    run.after_tick(a, w, ground="--no-ground" not in sys.argv)   # (first only luck was earned here: the rows and clears weren't kept up)
    cleared += max(0, w.__dict__.get("pieces_cleared", 0) - before)
    if (t + 1) % 200 == 0:
        ins = [i for s in und.__dict__.get("prediction_sovs", {}).values() for i in s["instances"] if i["made"] >= t_first and i["outcome"]]
        c = collections.Counter(i["outcome"] for i in ins)
        log = collections.Counter(x[2] for x in a.__dict__.get("commit_log", []))
        print(f"slice {t + 1} ({time.time() - t0:.0f}s): games ended {len(w.games) - games0}, pieces cleared {cleared}, rows {w.lines - lines0}; "
              f"predictions confirmed {c['confirmed']}, rejected {c['rejected']}; commits made {log['made']}, came {log['came']}, "
              f"did not come {log['did not come']}, dissolved {log['dissolved']}; ground blocks held {len(a.__dict__.get('ground_held', ()))}; anti-want {a.__dict__.get('anti')}", flush=True)
    if (t + 1) % 1000 == 0:
        checkpoint.save(a, w, t + 1, f"checkpoints/{name}_{t + 1}.pkl")
