"""The adaptive octree: resolution spent only where the scene is not uniform.

    python -X utf8 perception/octree.py [name]     (reads data/samples_<name>.*, writes data/octree_<name>.npz)

It starts with one cell around the whole scene and splits a cell into eight only when its contents are not
uniform. Plain glaze and plain wood stay as big cells; detail pools at the chip, the print, the stain line,
the worn corner. What "uniform" means is my choice, each part to keep resolution off what is merely
regular:

  gerund     a cell holding two nodes of the gerund field (a mug resting on the supporting table, a book on a
             book) judges each node's surfaces on its own; it is a boundary if one of them is not uniform there
  shape      within each sheet of surface, the normals follow position smoothly (an affine fit leaves
             little over), so flat and gently curved surfaces are uniform; edges, rims and chips are not
  colour     within each sheet, the sub-cells look alike: no sub-cell's mean colour stands out from the
  texture    sheet's, and none has a different amount of colour variation. Stationary texture (wood grain,
             speckle) is uniform at a coarse scale; a letter, a stain line, a chip stand out from their siblings
  sheets     a cell can hold both sides of a thin wall (a mug's inside and outside); its surfaces are
             separated by which way they face and judged one by one, so a plain thin wall stays coarse

A cell stops splitting when it is uniform, holds too few samples to judge, or reaches the finest size.
Coordinates are the designer's side of the line: the octree reads them, the mind will read its cells.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from samples import load, name_of, DATA  # noqa: E402

REASONS = ("uniform", "few", "finest", "gerund", "shape", "colour", "texture")


class Octree:
    def __init__(self, s, tau_shape=0.08, tau_colour=14.0, texture_ratio=1.6, texture_floor=4.0,
                 min_points=12, judge_points=8, finest=0.001):
        self.s = s
        self.tau_shape, self.tau_colour = tau_shape, tau_colour
        self.texture_ratio, self.texture_floor = texture_ratio, texture_floor
        self.min_points, self.judge_points, self.finest = min_points, judge_points, finest
        self.col = s.col.astype(np.float32)

    # ---- judging one cell ----------------------------------------------------------------------

    def sheets(self, idx):
        """The cell's surfaces, told apart by which way they face: the sign of each normal along the
        normals' principal direction. One sheet if they all face within a right angle of it."""
        N = self.s.nrm[idx]
        w, v = np.linalg.eigh(N.T @ N)
        side = N @ v[:, -1] >= 0
        if side.all() or not side.any():
            return [idx]
        return [idx[side], idx[~side]]

    def shape_residual(self, idx):
        """How much of the normals an affine function of position does not predict (RMS, unit vectors)."""
        P = self.s.pos[idx].astype(np.float64)
        X = np.c_[P - P.mean(0), np.ones(len(P))]
        N = self.s.nrm[idx].astype(np.float64)
        coef, *_ = np.linalg.lstsq(X, N, rcond=None)
        return float(np.sqrt(((N - X @ coef) ** 2).sum(1).mean()))

    def judge(self, idx, center):
        """Why a cell must split, or None if it is uniform. Each gerund region in the cell is judged on its
        own surfaces (first a cell holding two regions always split, and two uniform surfaces pressed
        together, a book on a book, the oil inside its glass, split down to the finest cells along the whole
        contact). A region's surfaces in a cell where another region's are too are a "gerund" split only if
        one of them is not uniform there."""
        g = self.s.node[idx]   # the gerund field's nodes (first the gerund label alone, and the stacked books,
                               # all "supporting", merged with the supporting table)
        regions = [idx] if g.min() == g.max() else [idx[g == k] for k in np.unique(g)]
        for region in regions:
            why = self.judge_region(region, center)
            if why is not None:
                return "gerund" if len(regions) > 1 and why == "shape" else why
        return None

    def judge_region(self, idx, center):
        """Shape, colour and texture within one gerund region's surfaces. The colour and texture tests allow
        for sampling: a sub-cell's mean is held to stand out only beyond what its few samples could give by
        chance (3 standard errors), and its spread is judged only with enough samples to estimate it (first
        exact, and sub-cells of 8 samples split on noise: thousands of splits in cells under 60 samples)."""
        for sheet in self.sheets(idx):
            if len(sheet) < self.judge_points:
                continue
            if len(sheet) >= 6 and self.shape_residual(sheet) > self.tau_shape:
                return "shape"
            P, C = self.s.pos[sheet], self.col[sheet]
            code = (P[:, 0] > center[0]) + 2 * (P[:, 1] > center[1]) + 4 * (P[:, 2] > center[2])
            mu, sd = C.mean(0), C.std(0).mean()
            for k in np.unique(code):
                Ck = C[code == k]
                nk = len(Ck)
                if nk < self.judge_points:
                    continue
                sdk = Ck.std(0).mean()
                if np.linalg.norm(Ck.mean(0) - mu) > self.tau_colour + 3 * max(sd, sdk) / np.sqrt(nk):
                    return "colour"
                if nk >= 3 * self.judge_points and max(sdk, sd) > self.texture_floor and \
                        max(max(sdk, self.texture_floor) / max(sd, self.texture_floor),
                            max(sd, self.texture_floor) / max(sdk, self.texture_floor)) > self.texture_ratio:
                    return "texture"
        return None

    # ---- building ----------------------------------------------------------------------------------

    def build(self):
        P = self.s.pos
        lo, hi = P.min(0), P.max(0)
        half = float((hi - lo).max()) / 2 * 1.001
        stack = [(np.arange(len(P)), (lo + hi) / 2, half, 0)]
        leaves, splits = [], {r: 0 for r in REASONS}
        while stack:
            idx, center, half, depth = stack.pop()
            if len(idx) < self.min_points:
                reason = "few"
            elif 2 * half <= self.finest:
                reason = "finest"
            else:
                why = self.judge(idx, center)
                if why is not None:
                    splits[why] += 1
                    p = P[idx]
                    code = (p[:, 0] > center[0]) + 2 * (p[:, 1] > center[1]) + 4 * (p[:, 2] > center[2])
                    order = np.argsort(code, kind="stable")
                    bounds = np.searchsorted(code[order], np.arange(9))
                    for k in range(8):
                        sub = idx[order[bounds[k]:bounds[k + 1]]]
                        if len(sub):
                            off = np.array([(k & 1) * 2 - 1, (k >> 1 & 1) * 2 - 1, (k >> 2 & 1) * 2 - 1]) * half / 2
                            stack.append((sub, center + off, half / 2, depth + 1))
                    continue
                reason = "uniform"
            leaves.append((idx, center, half, depth, reason))
        self.splits = splits
        return self.pack(leaves)

    def pack(self, leaves):
        """Each leaf: its cell, how many samples, their mean colour and normal, colour spread, the gerund,
        why it stopped, and (the answer key, for checking only) the object most of its samples came from."""
        s = self.s
        n = len(leaves)
        out = dict(center=np.zeros((n, 3), np.float32), mean_pos=np.zeros((n, 3), np.float32),
                   size=np.zeros(n, np.float32), depth=np.zeros(n, np.uint8),
                   count=np.zeros(n, np.int32), colour=np.zeros((n, 3), np.float32), spread=np.zeros(n, np.float32),
                   normal=np.zeros((n, 3), np.float32), gerund=np.zeros(n, np.uint8), node=np.zeros(n, np.uint8),
                   reason=np.zeros(n, np.uint8),
                   key_object=np.zeros(n, np.uint8))
        point_leaf = np.zeros(len(s.pos), np.int32)
        for i, (idx, center, half, depth, reason) in enumerate(leaves):
            out["center"][i], out["size"][i], out["depth"][i], out["count"][i] = center, 2 * half, depth, len(idx)
            C = self.col[idx]
            out["colour"][i], out["spread"][i] = C.mean(0), C.std(0).mean()
            out["mean_pos"][i] = s.pos[idx].mean(0)
            nm = s.nrm[idx].mean(0)
            out["normal"][i] = nm / (np.linalg.norm(nm) + 1e-9)
            out["gerund"][i] = np.bincount(s.ger[idx]).argmax()
            out["node"][i] = np.bincount(s.node[idx]).argmax()
            out["reason"][i] = REASONS.index(reason)
            out["key_object"][i] = np.bincount(s.obj[idx]).argmax()
            point_leaf[idx] = i
        out["point_leaf"] = point_leaf
        return out


def report(s, t):
    """Where the resolution went, by object; and at the answer key's marks against plain surface."""
    size_mm = t["size"] * 1000
    print(f"\n{len(t['size']):,} cells (leaves);  why they stopped: " +
          ", ".join(f"{r} {(t['reason'] == k).sum():,}" for k, r in enumerate(REASONS) if (t['reason'] == k).any()))
    bands = {"<3": (0, 3), "3-11": (3, 11), "11-41": (11, 41), "41+": (41, 1e9)}
    each = size_mm[t["point_leaf"]]   # the cell each sample sits in: resolution by surface area, not by cell count
    print(f"\n{'object':12} {'samples':>9} {'cells':>7}   share of its surface in cells of (mm): "
          + "  ".join(f"{b:>6}" for b in bands))
    for k, key in enumerate(s.key):
        m = t["key_object"] == k
        on = s.obj == k
        print(f"{key['name']:12} {on.sum():9,} {m.sum():7,}   {'':38}"
              + "  ".join(f"{((each[on] >= lo) & (each[on] < hi)).mean():6.0%}" for lo, hi in bands.values()))
    print("\nresolution at the answer key's marks, against the same mug's plain surface (cell size each sample sits in):")
    leaf = t["point_leaf"]
    for key in [x for x in s.key if x["name"].startswith("mug_")]:
        name, tr = key["name"], key["truth"]
        m, p, phi, r = s.local(name)
        cell = size_mm[leaf[m]]
        H, R = tr["H"], tr["R"]
        d = lambda a: np.abs((phi - a + np.pi) % (2 * np.pi) - np.pi)
        outer = (r > R * 0.9) & (p[:, 1] > 0.02) & (p[:, 1] < H - 0.01)
        line = f"  {name:6} plain outer wall: median cell {np.median(cell[outer]):5.1f} mm"
        for mk in tr["marks"]:
            if mk["what"] == "chip":
                sel = (p[:, 1] > H - 1.5 * mk["size"]) & (d(mk["angle"]) < mk["size"] / R)
                opp = (p[:, 1] > H - 1.5 * mk["size"]) & (d(mk["angle"] + np.pi) < mk["size"] / R)
                line += f" | chip {np.median(cell[sel]):4.1f} mm (the rim opposite {np.median(cell[opp]):4.1f})"
            if mk["what"] == "print":
                band = (np.abs(p[:, 1] - mk["at"]["height"]) < 0.008) & (r > R * 0.9)
                sel, opp = band & (d(mk["at"]["angle"]) < 0.5), band & (d(mk["at"]["angle"] + np.pi) < 0.5)
                line += f" | print {np.median(cell[sel]):4.1f} mm (half way round {np.median(cell[opp]):4.1f})"
            if mk["what"] == "stain":
                inner = r < R * 0.9
                sel = inner & (np.abs(p[:, 1] - mk["level"]) < 0.003)
                ctl = inner & (p[:, 1] > mk["level"] + 0.008) & (p[:, 1] < H - 0.006)
                line += f" | stain line {np.median(cell[sel]):4.1f} mm (inside above it {np.median(cell[ctl]):4.1f})"
        print(line)


if __name__ == "__main__":
    seed = name_of(sys.argv[1] if len(sys.argv) > 1 else "seed7")
    s = load(seed)
    t0 = time.time()
    tree = Octree(s)
    t = tree.build()
    print(f"built in {time.time() - t0:.0f}s from {len(s):,} samples; splits by reason: {tree.splits}")
    report(s, t)
    np.savez_compressed(os.path.join(DATA, f"octree_{seed}.npz"), **t, reasons=np.array(REASONS),
                        gerunds=np.array(s.gerunds))
    # for the scene's viewer: each cell as a surfel (mean position, normal, size, mean colour), f32 x 10
    np.c_[t["mean_pos"], t["normal"], t["size"], t["colour"] / 255].astype(np.float32).tofile(
        os.path.join(DATA, f"cells_{seed}.bin"))
