"""The surface samples the browser's Reader sent (scene/sampler.js): load them, and check them against
the answer key.

    python -X utf8 perception/samples.py [name]      (reads data/samples_<name>.json and .bin; name: seed7, seed7_layout3)

Each sample: position (m), surface normal, colour (sRGB albedo from the surface's own texture), the
gerund it lies in and the node of the gerund field (one doing; ids shuffled), and the object it came from
(the answer key: for checking, never for the mind).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")


class Samples:
    def __init__(self, manifest, pos, nrm, col, ger, node, obj):
        self.manifest, self.pos, self.nrm, self.col, self.ger, self.obj = manifest, pos, nrm, col, ger, obj
        self.node = node   # the gerund field's node (one doing), ids shuffled: which surfaces belong together
        self.gerunds = manifest["gerunds"]
        self.key = manifest["answer_key"]   # the designer's: object names and what was put into each

    def __len__(self):
        return len(self.pos)

    def of(self, name):
        """The answer key's mask for one object (checking only)."""
        k = next(i for i, t in enumerate(self.key) if t["name"] == name)
        return self.obj == k

    def local(self, name):
        """One object's samples in its own frame, where the designer placed it (checking only): positions,
        and for a lathed thing its angle phi around the axis (as the scene's lathe measures it) and radius."""
        t = next(x for x in self.key if x["name"] == name)
        M = np.array(t["matrix"], dtype=np.float64).reshape(4, 4).T   # three.js stores column-major
        m = self.of(name)
        p = np.c_[self.pos[m], np.ones(m.sum())] @ np.linalg.inv(M).T
        phi = np.arctan2(p[:, 0], p[:, 2]) % (2 * np.pi)
        return m, p[:, :3], phi, np.hypot(p[:, 0], p[:, 2])


def name_of(x="seed7"):
    """A dataset's name: seed7, seed7_layout3 (a bare number is a seed)."""
    return f"seed{x}" if str(x).isdigit() else str(x)


def load(name="seed7"):
    base = os.path.join(DATA, f"samples_{name_of(name)}")
    with open(base + ".json", encoding="utf-8") as f:
        m = json.load(f)
    n = m["points"]
    raw = np.fromfile(base + ".bin", dtype=np.uint8)
    o = 0

    def take(dtype, count):
        nonlocal o
        size = np.dtype(dtype).itemsize * count
        a = raw[o:o + size].view(dtype)
        o += size
        return a
    pos = take(np.float32, n * 3).reshape(n, 3)
    nrm = take(np.int8, n * 3).reshape(n, 3).astype(np.float32) / 127
    col = take(np.uint8, n * 3).reshape(n, 3)
    ger = take(np.uint8, n)
    node = take(np.uint8, n)
    obj = take(np.uint8, n)
    assert o == len(raw), f"read {o} of {len(raw)} bytes"
    return Samples(m, pos, nrm, col, ger, node, obj)


def check(s):
    """What the answer key says was put into the scene, and whether the samples carry it."""
    print(f"{len(s):,} samples; gerund regions {s.gerunds}")
    print(f"{'object':12} {'samples':>9}  gerund      mean colour")
    for t in s.key:
        m = s.of(t["name"])
        g = s.gerunds[np.bincount(s.ger[m]).argmax()]
        print(f"{t['name']:12} {m.sum():9,}  {g:11} {np.round(s.col[m].mean(0)).astype(int)}")
    print("\nthe answer key's marks, looked for where the key says they are (each mug in its own frame):")
    for t in [x for x in s.key if x["name"].startswith("mug_")]:
        name, tr = t["name"], t["truth"]
        m, p, phi, r = s.local(name)
        col = s.col[m].astype(float)
        H, R = tr["H"], tr["R"]
        print(f"  {name} ({tr['model']}, {tr['age']}y): " + (", ".join(x["what"] for x in tr["marks"]) or "no marks"))
        for mk in tr["marks"]:
            if mk["what"] == "chip":   # the chip's arc of rim against the same arc half way round
                w = mk["size"] / R
                d = lambda a: np.abs((phi - a + np.pi) % (2 * np.pi) - np.pi)
                rim = p[:, 1] > H - 1.5 * mk["size"]
                at, away = rim & (d(mk["angle"]) < w), rim & (d(mk["angle"] + np.pi) < w)
                print(f"      chip:  {at.sum()} samples in its arc, mean colour {np.round(col[at].mean(0)).astype(int)}, "
                      f"rim top at {p[at, 1].max() * 1000:.1f} mm;  the opposite arc {np.round(col[away].mean(0)).astype(int)}, "
                      f"rim top at {p[away, 1].max() * 1000:.1f} mm")
            if mk["what"] == "print":   # the print's band against the same band half way round
                a, y = mk["at"]["angle"], mk["at"]["height"]
                d = lambda a0: np.abs((phi - a0 + np.pi) % (2 * np.pi) - np.pi)
                band = (np.abs(p[:, 1] - y) < 0.01) & (r > R * 0.9)
                at, away = band & (d(a) < 0.6), band & (d(a + np.pi) < 0.6)
                dev = lambda sel: np.abs(col[sel] - np.median(col[band], 0)).sum(1)
                print(f"      print '{mk['text']}':  {(dev(at) > 60).mean():.0%} of its band differs from the glaze; "
                      f"half way round {(dev(away) > 60).mean():.0%}")
            if mk["what"] == "stain":   # inside, below the stain line, against inside above it
                inner = r < R * 0.9
                below = inner & (p[:, 1] < mk["level"] - 0.003) & (p[:, 1] > 0.02)
                above = inner & (p[:, 1] > mk["level"] + 0.003)
                print(f"      stain: inside below the line {np.round(col[below].mean(0)).astype(int)}, "
                      f"above it {np.round(col[above].mean(0)).astype(int)}")


if __name__ == "__main__":
    check(load(sys.argv[1] if len(sys.argv) > 1 else "seed7"))
