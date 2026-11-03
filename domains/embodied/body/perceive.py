"""What the mind perceives of the wanted mug before it reaches, read from the octree's things and the marks of
step 3 (never the answer key): which way its handle points, on which side its rim carries a distinctive mark,
and on which sides something stands close. Sides are as the body sees them: left, right, near, far.

The relational constraints read these: "not from a side where something stands close", "the handle only from
the side it faces", "not the rim on the side of its mark".
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "perception"))
from samples import DATA, name_of  # noqa: E402
import distinct as D  # noqa: E402

CLOSE = 0.06   # something stands close when less than a hand's width lies between it and the mug
HOME_HAND = (0.32, 0.16, 0.42)   # where the hand rests: the body knows where its own hand is


# what each raw quantity can range over, as a measurement (its instrument's scale, not a category): cosines over 2,
# shares of the mug's height over 1, of its radius over 1.6 (a handle stands out to about 1.6), lightness over 1,
# texture spread over 60 (sRGB), distinctiveness over 200 (it is capped there), what lies in the way over 50 cm2,
# what is touched over 30 cm2, the area of a mark over 500 cm2 (a mug's body)
SCALE = {"height": 1.0, "out_from_axis": 1.6, "faces_out": 2.0, "faces_up": 2.0, "lightness": 1.0, "spread": 60.0,
         "distinct": 200.0, "came_to_touch": 2.0, "came_to_mark": 2.0, "in_way": 50.0, "touched": 3000.0,
         "mark_area": 500.0}


def scale_of(f):
    """The scale of a raw quantity (height_mean, faces_out_max, ...: the quantity before its _mean/_max/_min)."""
    return SCALE.get(f) or SCALE.get(f.rsplit("_", 1)[0], 1.0)


def side_of(v):
    """The side a direction (x, z) points, as the body sees it."""
    if abs(v[0]) >= abs(v[1]):
        return "left" if v[0] < 0 else "right"
    return "near" if v[1] > 0 else "far"


class Percept:
    def __init__(self, data, wanted_at):
        """data: the scene; wanted_at: where the wanted thing stands (x, z): the task says which mug is wanted,
        as a voice says what to fetch; what it is like is the mind's to see."""
        name = name_of(data)
        t = dict(np.load(os.path.join(DATA, f"octree_{name}.npz")))
        self.t = t
        self.sc = sc = D.Scene(t, D.neighbours(t))
        fam = sc.families()
        self.d = D.distinctiveness(sc, fam)
        self.marks = D.marks(sc, self.d)
        self.k = min(range(sc.n), key=lambda k: np.linalg.norm(sc.frames[k]["axis"] - np.asarray(wanted_at)))
        f = sc.frames[self.k]
        idx, F = sc.features(self.k)
        self.axis, self.H = f["axis"], f["H"]
        h, r, up, out = F[:, 0], F[:, 1], F[:, 2], F[:, 3]
        body = (out > 0.5) & (h > 0.3 * f["H"]) & (h < 0.7 * f["H"])
        self.R = float(np.median(r[body])) if body.any() else f["reach"]
        # the handle: what stands out beyond the body, at mid height
        out_cells = idx[(r > self.R * 1.25) & (h > 0.15 * f["H"]) & (h < 0.9 * f["H"])]
        self.handle_side = None
        if len(out_cells):
            v = (t["mean_pos"][out_cells][:, [0, 2]] - self.axis).mean(0)
            self.handle_side = side_of(v)
        # the rim's distinctive mark: a mark of this thing at the rim
        self.mark_side = None
        rim = [m for m in self.marks if m["thing"] == self.k and m["height"] > 0.88]
        if rim:
            m = max(rim, key=lambda m: m["strength"] if np.isfinite(m["strength"]) else 0)
            v = (t["mean_pos"][m["cells"]][:, [0, 2]] - self.axis).mean(0)
            self.mark_side = side_of(v)
            self.mark_cells = set(m["cells"].tolist())
        else:
            self.mark_cells = set()
        self.mark_area = {}   # cell -> the area (cm2) of the mark it belongs to, for this thing's marks
        for m in self.marks:
            if m["thing"] == self.k:
                for c in m["cells"]:
                    self.mark_area[int(c)] = m["area"] * 1e4
        # what stands close, and on which side
        self.close_sides = set()
        for j in range(sc.n):
            if j == self.k or sc.frames[j]["reach"] > 0.3:   # not itself; not the table
                continue
            fj = sc.frames[j]
            v = fj["axis"] - self.axis
            gap = np.linalg.norm(v) - self.R - min(fj["reach"], 0.06)
            if gap < CLOSE:
                self.close_sides.add(side_of(v))

    def approach(self, side):
        """Where the hand would come down beside the mug from a side, as the mind sees the mug (its axis and
        height): 9 cm out, above the rim."""
        d = {"left": (-1, 0), "right": (1, 0), "near": (0, 1), "far": (0, -1)}[side]
        return np.array([self.axis[0] + 0.09 * d[0], self.H + 0.03, self.axis[1] + 0.09 * d[1]])

    def in_the_way(self, start, goal, corridor=0.04):
        """Whether some thing other than the wanted one lies between the hand and where it reaches: its cells in
        the corridor along the way (the field's regions between), below the height the hand travels at."""
        t, p = self.t, self.t["mean_pos"]
        a, b = np.asarray(start, float), np.asarray(goal, float)
        ab = b - a
        L2 = float(ab @ ab) or 1.0
        others = (self.sc.thing >= 0) & (self.sc.thing != self.k)
        others &= np.array([self.sc.frames[k]["reach"] <= 0.3 if k >= 0 else False for k in self.sc.thing])   # not the table
        q = p[others]
        s = np.clip(((q - a) @ ab) / L2, 0, 1)
        nearest = a + s[:, None] * ab
        d = np.linalg.norm((q - nearest)[:, [0, 2]], axis=1)
        return bool(((d < corridor) & (q[:, 1] > nearest[:, 1] - 0.03)).any())   # reaches up into the hand's way

    # ---- an attempt, as perceived: tags read from the octree, not from rules -----------------------------

    SIDE = {"left": (-1.0, 0.0), "right": (1.0, 0.0), "near": (0.0, 1.0), "far": (0.0, -1.0)}
    REACH = {"hook": 0.03, "pinch": 0.02, "wrap": 0.04}   # how far round the fingers' contact spreads (the
                                                          # same hand the world has: world.REACH)

    def out_dir(self):
        """Which way the part that stands out beyond the body points (the handle, as seen)."""
        if not hasattr(self, "_out"):
            idx, F = self.sc.features(self.k)
            sel = idx[(F[:, 1] > self.R * 1.25) & (F[:, 0] > 0.15 * self.H) & (F[:, 0] < 0.9 * self.H)]
            v = (self.t["mean_pos"][sel][:, [0, 2]] - self.axis).mean(0) if len(sel) else np.zeros(2)
            self._out = v / (np.linalg.norm(v) + 1e-9) if len(sel) else None
        return self._out

    def mark_dir(self):
        if not hasattr(self, "_mark"):
            self._mark = None
            if self.mark_cells:
                v = (self.t["mean_pos"][sorted(self.mark_cells)][:, [0, 2]] - self.axis).mean(0)
                self._mark = v / (np.linalg.norm(v) + 1e-9)
        return self._mark

    def plan(self, side, part):
        """Where the mind would put its fingers to take the mug from a side by a part, as it sees the mug: the
        out-standing part, where it stands out; the rim or the body, on that side."""
        d = np.array(self.SIDE[side])
        if part == "handle" and self.out_dir() is not None:
            xz = self.axis + self.out_dir() * (self.R + 0.035)
            return np.array([xz[0], 0.55 * self.H, xz[1]])
        if part == "rim":
            xz = self.axis + d * self.R
            return np.array([xz[0], self.H, xz[1]])
        xz = self.axis + d * (self.R + 0.008)
        return np.array([xz[0], 0.45 * self.H, xz[1]])

    def touch_tags(self, at, grip):
        """What the fingers meet at `at`: the mug's cells under them, each where it sits on the mug (rim, upper,
        middle, lower), how it faces (outside, inside, up), whether it stands out beyond the body, and whether
        one of the mug's distinctive marks is among them."""
        idx, F = self.sc.features(self.k)
        p = self.t["mean_pos"][idx]
        near = np.linalg.norm(p - np.asarray(at, float), axis=1) < self.REACH[grip]
        tags, held = set(), {}
        area = self.t["count"][idx[near]]
        for (h, r, up, out), c, a in zip(F[near], idx[near], area):
            s = h / max(self.H, 1e-9)
            tags.add("touch:" + ("rim" if s > 0.88 else "upper" if s > 0.6 else "middle" if s > 0.3 else "lower"))
            tags.add("touch:" + ("outside" if out > 0.4 else "inside" if out < -0.4 else "up" if up > 0.6 else "edge"))
            where = "stands-out" if r > self.R * 1.25 else "rim" if s > 0.88 else "body"
            tags.add("touch:" + where)
            held[where] = held.get(where, 0) + a
            if int(c) in self.mark_cells:
                tags.add("touch:mark")
        if held:   # what the hand mostly holds: where most of the contact is (first only what it touched at all, and
            tags.add("holds:" + max(held, key=held.get))   # a hook through the handle, brushing the body where the
        return tags or {"touch:nothing"}                   # handle joins, could not be told from a hand on the body

    def way_tags(self, side):
        return {"way:crosses" if self.in_the_way(HOME_HAND, self.approach(side)) else "way:clear"}

    def came_tags(self, side):
        """How the approach lay to what the mug shows: along the way its out-standing part faces, across it,
        against it; toward its mark or not."""
        d = np.array(self.SIDE[side])
        tags = set()
        for name, v in (("out", self.out_dir()), ("mark", self.mark_dir())):
            if v is None:
                continue
            c = float(d @ v)
            tags.add(f"came:{'with' if c > 0.5 else 'against' if c < -0.5 else 'across'}-{name}")
        return tags

    def predict(self, attempt):
        """The tags an untried attempt would carry, as the mind imagines it on the mug it sees."""
        side, part, grip = attempt
        return (self.touch_tags(self.plan(side, part), grip) | self.way_tags(side) | self.came_tags(side)
                | {f"grip:{grip}"})

    # ---- an attempt as raw perception: quantities, no categories (tags are minted from these by need) -----

    def marks_dirs(self):
        """The directions (from the mug's axis) of each of its distinctive marks."""
        if not hasattr(self, "_mdirs"):
            self._mdirs = []
            for m in self.marks:
                if m["thing"] == self.k:
                    v = (self.t["mean_pos"][m["cells"]][:, [0, 2]] - self.axis).mean(0)
                    if np.linalg.norm(v) > 1e-6:
                        self._mdirs.append(v / np.linalg.norm(v))
        return self._mdirs

    def imagined_path(self, side, step=0.02):
        """The way the mind expects its hand to go to a side: as its reach moves, a step at a time along the longest
        part of the gap first (first a straight line, and on the stoneware mug the line passed clear of the bottle
        while the hand's real path clipped it: seventeen knocks, none perceived as "something in the way")."""
        pos, goal, pts = np.array(HOME_HAND, float), self.approach(side), []
        for _ in range(200):
            gap = goal - pos
            if np.linalg.norm(gap) <= 0.75 * step:
                break
            ax = int(np.argmax(np.abs(gap)))
            pos = pos.copy()
            pos[ax] += step * np.sign(gap[ax])
            pts.append(pos)
        return pts

    def raw(self, side, at, grip, touched=True, path=None):
        """What the mind perceives of an attempt, as quantities: of the cells under the fingers (area-weighted
        mean, and the extreme), their height on the mug and distance from its axis (as shares of the mug's),
        which way they face, their lightness, texture spread and distinctiveness, and how much was touched; how
        the approach lay to where the fingers went and to the mug's marks (cosines); how much of other things
        lay in the way. A reach stopped before it touched has no touch quantities."""
        f = {}
        d = np.array(self.SIDE[side])
        way = self.way_along(path if path is not None else self.imagined_path(side))
        f["in_way"] = way
        dirs = self.marks_dirs()
        f["came_to_mark"] = max((float(d @ m) for m in dirs), default=np.nan)
        if not touched:
            return f
        idx, F = self.sc.features(self.k)
        p = self.t["mean_pos"][idx]
        near = np.linalg.norm(p - np.asarray(at, float), axis=1) < self.REACH[grip]
        if not near.any():
            f["touched"] = 0.0
            return f
        w = self.t["count"][idx[near]].astype(float)
        G = F[near]
        q = {"height": G[:, 0] / max(self.H, 1e-9), "out_from_axis": G[:, 1] / max(self.R, 1e-9),
             "faces_out": G[:, 3], "faces_up": G[:, 2],
             "lightness": self.t["colour"][idx[near]].mean(1) / 255, "spread": self.t["spread"][idx[near]],
             "distinct": np.nan_to_num(self.d[idx[near]], nan=0.0, posinf=200.0)}
        for name, v in q.items():
            f[f"{name}_mean"] = float((v * w).sum() / w.sum())
            f[f"{name}_max"] = float(v.max())
            f[f"{name}_min"] = float(v.min())
        f["touched"] = float(w.sum())
        # (tried: the area of the smallest mark under the fingers, so a chip, a speck, is told from a mug
        # distinctive all over: worse on the new mugs, 4.35 attempts against 3.62; removed)
        c = (p[near][:, [0, 2]] * w[:, None]).sum(0) / w.sum() - self.axis
        f["came_to_touch"] = float(d @ (c / (np.linalg.norm(c) + 1e-9)))
        return f

    def way_along(self, pts, reach=0.035):
        """How much of other things lay along a path (cm2): their cells within the hand's reach of a point of it,
        up where the hand passes; for an attempt made, the path the hand took."""
        if not len(pts):
            return 0.0
        p = self.t["mean_pos"]
        others = (self.sc.thing >= 0) & (self.sc.thing != self.k)
        others &= np.array([self.sc.frames[k]["reach"] <= 0.3 if k >= 0 else False for k in self.sc.thing])
        idx = np.where(others)[0]
        q = p[idx]
        hit = np.zeros(len(idx), bool)
        for pt in np.asarray(pts, float):
            hit |= (np.linalg.norm(q[:, [0, 2]] - pt[[0, 2]], axis=1) < reach) & (q[:, 1] > pt[1] - 0.03)
        return float(self.t["count"][idx[hit]].sum()) / 100.0

    def way_amount(self, start, goal, corridor=0.04):
        """How much of other things lies between the hand and where it reaches (their cells' area in the corridor,
        up where the hand passes), in cm2."""
        p = self.t["mean_pos"]
        a, b = np.asarray(start, float), np.asarray(goal, float)
        ab = b - a
        others = (self.sc.thing >= 0) & (self.sc.thing != self.k)
        others &= np.array([self.sc.frames[k]["reach"] <= 0.3 if k >= 0 else False for k in self.sc.thing])
        q = p[others]
        s = np.clip(((q - a) @ ab) / (float(ab @ ab) or 1.0), 0, 1)
        nearest = a + s[:, None] * ab
        hit = (np.linalg.norm((q - nearest)[:, [0, 2]], axis=1) < corridor) & (q[:, 1] > nearest[:, 1] - 0.03)
        return float(self.t["count"][np.where(others)[0][hit]].sum()) / 100.0

    def around(self, idx, p, at, grip):
        """The usual distinctiveness of the thing's cells just around a touch (a ring out to twice the contact)."""
        d = np.linalg.norm(p - np.asarray(at, float), axis=1)
        ring = (d >= self.REACH[grip]) & (d < 2 * self.REACH[grip])
        if not ring.any():
            return self.usual_distinct()
        return float(np.median(np.nan_to_num(self.d[idx[ring]], nan=0.0, posinf=200.0)))

    def usual_distinct(self):
        """The thing's own usual distinctiveness (the median over its cells)."""
        if not hasattr(self, "_usual"):
            idx, _ = self.sc.features(self.k)
            self._usual = float(np.median(np.nan_to_num(self.d[idx], nan=0.0, posinf=200.0)))
        return self._usual

    def predict_raw(self, attempt):
        side, part, grip = attempt
        return self.raw(side, self.plan(side, part), grip)

    def mark_under(self, at, reach=0.015):
        """Whether one of the mug's distinctive rim marks lies under the fingers at `at` (the octree's cells there)."""
        if not self.mark_cells:
            return False
        p = self.t["mean_pos"]
        near = np.where((self.sc.thing == self.k) & (np.linalg.norm(p - np.asarray(at), axis=1) < reach))[0]
        return any(int(c) in self.mark_cells for c in near)

    def __repr__(self):
        return (f"handle toward the {self.handle_side}; rim mark on the {self.mark_side}; "
                f"something close on the {sorted(self.close_sides) or 'no side'}")
