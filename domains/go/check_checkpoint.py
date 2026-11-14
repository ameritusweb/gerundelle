"""A checkpoint goes on as the run it was saved from would have: 260 slices straight, against 200 saved, loaded and 60 more, compared
slice by slice (what the world shows, the mind's want and stack, its pushes, its pool). Run: PYTHONHASHSEED=0 python -X utf8 check_checkpoint.py"""
import hashlib

import run


def sig(a, w):
    return hashlib.md5(repr((sorted(w.shown.items()), a.goal, tuple(a.stack), len(a.pushed), sorted((i, x.act) for i, x in a.mind.pool.items()),
                             w.luck)).encode()).hexdigest()[:10]


def go(a, w, read, n):
    out = []
    for _ in range(n):
        a.mind.potentials = w.potentials()
        a.tick()
        read, _ = run.give(a, w, read)
        out.append(sig(a, w))
    return out, read


a, w = run.build(0, 0.7)
first, read = go(a, w, 0, 200)
run.checkpoint.save(a, w, 200, f"{run.HERE}/checkpoints/check_200.pkl")
straight, _ = go(a, w, read, 60)
a2, w2, t = run.resume(f"{run.HERE}/checkpoints/check_200.pkl")
resumed, _ = go(a2, w2, len(a2.pushed), 60)
same = sum(1 for x, y in zip(straight, resumed) if x == y)
print(f"resumed at slice {t}: {same} of 60 slices the same as the straight run", "ok" if same == 60 else "DIFFERENT from slice %d" % (200 + next(i for i, (x, y) in enumerate(zip(straight, resumed)) if x != y)))
