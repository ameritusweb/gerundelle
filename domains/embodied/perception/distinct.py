"""Step 3: what is distinctive among the octree's cells, relative to context; the marks that become thought
molecules.

    python -X utf8 perception/distinct.py [name]

Nothing the scene does not give is handed over. Which mug is which is never given:
  things     the nodes of the gerund field (each doing a region: object boundaries are force boundaries;
             node ids are shuffled, so they say which surfaces belong together, not which object it is)
  family     things of a similar coarse form (height, reach, surface): the context, the genre
  distinct   a cell is distinctive when no other member of its family has a cell like it at the
             corresponding place (the same height on the thing, the same distance from its axis, facing
             the same way). Height and radius, not angle: no one tells the mind how each thing is turned
  marks      adjacent distinctive cells, grouped: what the thing has that its family does not
The answer key (which object each cell came from, and what was put into it) is used only in check().
"""
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from samples import load, name_of, DATA  # noqa: E402

DENSITY = 1e6   # samples per m2 (scene/sampler.js): a cell's sample count is its area


class UnionFind:
    def __init__(self, n):
        self.p = np.arange(n)

    def find(self, i):
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[max(a, b)] = min(a, b)

    def labels(self):
        return np.array([self.find(i) for i in range(len(self.p))])


def neighbours(t, gap=0.003):
    """Cells that touch: same node of the field, mean positions within half their sizes of each other
    (plus a small gap). Pairs (i, j), i < j."""
    pos, size, ger = t["mean_pos"], t["size"], t["node"]
    tree = cKDTree(pos)
    out = []
    for i in range(len(pos)):
        for j in tree.query_ball_point(pos[i], 0.75 * size[i] + gap + 0.75 * 0.02):
            if j > i and ger[i] == ger[j] and np.linalg.norm(pos[i] - pos[j]) < 0.75 * (size[i] + size[j]) + gap:
                out.append((i, j))
    return out


class Scene:
    """The things the field holds, each in its own upright frame (up is the way the table supports)."""

    def __init__(self, t, pairs, min_area=2e-4):
        self.t, self.pairs = t, pairs
        lab = t["node"].astype(int)   # a thing is a node of the field (first connected cells within a
                                      # gerund label: books merged with the table, the table fell apart)
        area = np.bincount(lab, weights=t["count"]) / DENSITY
        roots = [r for r in np.unique(lab) if area[r] >= min_area]
        self.thing = np.full(len(lab), -1)
        for k, r in enumerate(roots):
            self.thing[lab == r] = k
        self.n = len(roots)
        self.frames = [self.frame(k) for k in range(self.n)]

    def frame(self, k):
        t, m = self.t, self.thing == k
        w = t["count"][m].astype(float)
        p = t["mean_pos"][m]
        axis = (p[:, [0, 2]] * w[:, None]).sum(0) / w.sum()
        base, top = p[:, 1].min(), p[:, 1].max()
        r = np.hypot(p[:, 0] - axis[0], p[:, 2] - axis[1])
        return dict(axis=axis, base=base, H=top - base, reach=np.percentile(r, 95), area=w.sum() / DENSITY)

    def features(self, k):
        """Each of thing k's cells where it sits on the thing: height above its base, distance from its
        axis, and how it faces (up, and out from the axis)."""
        t, f = self.t, self.frames[k]
        idx = np.where(self.thing == k)[0]
        p, nrm = t["mean_pos"][idx], t["normal"][idx]
        dx, dz = p[:, 0] - f["axis"][0], p[:, 2] - f["axis"][1]
        r = np.hypot(dx, dz)
        radial = np.c_[dx, dz] / np.maximum(r, 1e-9)[:, None]
        n_out = nrm[:, 0] * radial[:, 0] + nrm[:, 2] * radial[:, 1]
        return idx, np.c_[p[:, 1] - f["base"], r, nrm[:, 1], n_out]

    def families(self, tol=0.3):
        """Things of a similar coarse form: height, reach and surface each within tol of each other."""
        F = self.frames
        fam = []
        for a in range(self.n):
            near = [b for b in range(self.n) if b != a and all(
                abs(F[a][q] - F[b][q]) <= tol * max(F[a][q], F[b][q]) for q in ("H", "reach", "area"))]
            fam.append(near)
        return fam


def distinctiveness(sc, fam, tol_place=0.004, tol_face=0.5):
    """For every cell of a thing with a family: how unlike it is the most alike cell at the corresponding
    place on any other member (colour distance plus spread distance). Large: nothing in its family has it."""
    t = sc.t
    col, spread = t["colour"], t["spread"]
    d = np.full(len(t["size"]), np.nan)
    feats = {k: sc.features(k) for k in range(sc.n) if fam[k]}
    trees = {k: cKDTree(np.c_[f[1][:, :2], f[1][:, 2:] * (tol_place / tol_face)]) for k, f in feats.items()}
    for k, (idx, F) in feats.items():
        q = np.c_[F[:, :2], F[:, 2:] * (tol_place / tol_face)]
        best = np.full(len(idx), np.inf)
        for o in fam[k]:
            oidx, _ = feats[o]
            for a, near in enumerate(trees[o].query_ball_point(q, tol_place * 1.5)):
                if near:
                    j = oidx[near]
                    app = np.linalg.norm(col[j] - col[idx[a]], axis=1) + np.abs(spread[j] - spread[idx[a]])
                    best[a] = min(best[a], app.min())
        d[idx] = best   # inf: no member has anything at that place (a difference of form)
    return d


def marks(sc, d, tau=30.0, min_area=1.5e-5):
    """Adjacent distinctive cells of one thing, grouped. Each mark: its thing, cells, area, mean colour,
    where it sits (height and radius as shares of the thing's, which way it faces), how distinctive."""
    t = sc.t
    hot = d > tau
    uf = UnionFind(len(d))
    for i, j in sc.pairs:
        if hot[i] and hot[j] and sc.thing[i] == sc.thing[j]:
            uf.union(i, j)
    lab = uf.labels()
    out = []
    for r in np.unique(lab[hot]):
        cells = np.where((lab == r) & hot)[0]
        k = sc.thing[cells[0]]
        if k < 0:
            continue
        w = t["count"][cells].astype(float)
        area = w.sum() / DENSITY
        if area < min_area:
            continue
        idx, F = sc.features(k)
        pos = {c: i for i, c in enumerate(idx)}
        Fc = F[[pos[c] for c in cells]]
        f = sc.frames[k]
        out.append(dict(thing=k, cells=cells, area=area, colour=(t["colour"][cells] * w[:, None]).sum(0) / w.sum(),
                        height=float((Fc[:, 0] * w).sum() / w.sum() / f["H"]),
                        radius=float((Fc[:, 1] * w).sum() / w.sum() / max(f["reach"], 1e-9)),
                        facing=float((Fc[:, 3] * w).sum() / w.sum()), up=float((Fc[:, 2] * w).sum() / w.sum()),
                        strength=float(np.nanmean(np.where(np.isinf(d[cells]), np.nan, d[cells]))
                                       if np.isfinite(d[cells]).any() else np.inf),
                        form=bool(np.isinf(d[cells]).mean() > 0.5),
                        finest=float(t["size"][cells].min()), coarsest=float(t["size"][cells].max())))
    return out


def describe(m):
    where = ("inside" if m["facing"] < -0.3 else "outside" if m["facing"] > 0.3 else "top/bottom" if abs(m["up"]) > 0.6 else "edge")
    band = "rim" if m["height"] > 0.88 else "upper" if m["height"] > 0.6 else "middle" if m["height"] > 0.3 else "lower"
    kind = "form" if m["form"] else "look"
    return (f"{m['area'] * 1e4:6.2f} cm2  {band:6} {where:9} colour {np.round(m['colour']).astype(int)}  "
            f"{kind}, distinctiveness {m['strength']:.0f}  cells {len(m['cells'])} ({m['finest'] * 1000:.1f}-{m['coarsest'] * 1000:.1f} mm)")


def check(s, t, sc, fam, ms):
    """The answer key, for checking only: what each perceived thing is, and its marks against the key's."""
    names = [k["name"] for k in s.key]
    print(f"\n{sc.n} things perceived (connected cells within a gerund region):")
    for k in range(sc.n):
        m = sc.thing == k
        objs = np.bincount(t["key_object"][m], weights=t["count"][m], minlength=len(names))
        share = objs / objs.sum()
        made_of = ", ".join(f"{names[o]} {share[o]:.0%}" for o in np.argsort(-share) if share[o] > 0.02)
        f = sc.frames[k]
        print(f"  thing {k:2}: {made_of:40} H {f['H'] * 100:5.1f} cm, reach {f['reach'] * 100:4.1f} cm, "
              f"area {f['area'] * 1e4:6.0f} cm2;  family {fam[k]}")
    print("\nmarks: what each thing has that its family does not")
    for k in range(sc.n):
        if not fam[k]:
            continue
        mine = sorted([m for m in ms if m["thing"] == k], key=lambda m: -m["area"])
        m0 = sc.thing == k
        who = names[np.bincount(t["key_object"][m0], weights=t["count"][m0]).argmax()]
        key = next(x for x in s.key if x["name"] == who)["truth"]
        print(f"  thing {k} ({who}; key: {', '.join(x['what'] for x in key.get('marks', [])) or 'no marks'}): "
              f"{len(mine)} marks, {sum(m['area'] for m in mine) * 1e4:.1f} cm2 of {sc.frames[k]['area'] * 1e4:.0f}")
        for m in mine[:8]:
            print("      " + describe(m))
        if len(mine) > 8:
            print(f"      ... and {len(mine) - 8} smaller")


if __name__ == "__main__":
    seed = name_of(sys.argv[1] if len(sys.argv) > 1 else "seed7")
    s = load(seed)
    t = dict(np.load(os.path.join(DATA, f"octree_{seed}.npz")))
    pairs = neighbours(t)
    sc = Scene(t, pairs)
    fam = sc.families()
    d = distinctiveness(sc, fam)
    ms = marks(sc, d)
    check(s, t, sc, fam, ms)
    np.save(os.path.join(DATA, f"distinct_{seed}.npy"), d)
