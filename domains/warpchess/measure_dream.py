"""Times the first in-game dream after a checkpoint, with dream trials one at a time or in waves across worker processes (dream.py;
the user, 2026-11-14: "measure it and turn it on"). Loads the checkpoint, plays on as rung4p.py does until the mind has dreamed once,
and prints the dream's trials, seconds and edges, and the slice's time.
Run: PYTHONHASHSEED=0 python -u -X utf8 measure_dream.py <checkpoint> <workers>"""
import sys
import time


def main():
    import rung0  # noqa: F401
    import rung4p
    from plansworld import give
    from rung4 import TURN_STEPS
    path, workers = sys.argv[1], int(sys.argv[2])
    a, w, black, state = rung4p.load_run(path)
    a.dream_workers = workers
    n0, slices = len(a.__dict__.get("dreams_done", [])), 0

    def step():
        t = time.time()
        a.tick()
        give(a, w)
        return time.time() - t

    while len(a.__dict__.get("dreams_done", [])) == n0 and slices < 300:
        if w.board.turn == 1 and not w.over():
            w.actor = "White"
            k = len([x for x in w.log if x[2]])
            for _ in range(TURN_STEPS):
                dt = step()
                slices += 1
                if len([x for x in w.log if x[2]]) > k or len(a.__dict__.get("dreams_done", [])) > n0:
                    break
        elif not w.over():
            black.tick()
            w.actor = "White"
            dt = step()
            slices += 1
        else:
            w.actor = "White"
            w.pend["Black"] = {}
            dt = step()
            slices += 1
    done = a.__dict__.get("dreams_done", [])[n0:]
    print(f"workers {workers}: after {slices} slices; dreams {[(x[1][:60], x[3], x[4], x[5]) for x in done]}; that slice {dt:.1f}s; "
          f"waves {[t['waves'] for t in a.__dict__.get('dream_timing', [])[-len(done):]]}; pool start {[t['pool'] for t in a.__dict__.get('dream_timing', [])[-len(done):]]}")


if __name__ == "__main__":
    main()
