"""The hand's world: the table scene, a right hand, and a mug full of hot coffee the mind wants to hold.

The designer's side of the line. It holds coordinates (the scene's answer key: each object's placement and
what was put into it) and decides what each attempt does. The mind never reads it; it gets perceptions:
  the hand's gerund       empty, extending, gripping, lifting (the body: its own territory from tick 0)
  between                 how many coarse field regions lie between the hand and where it is reaching
                          (half-centimetre cells along the way: there is no air in the field, so this is close to
                          distance in coarse units; my choice, stated)
  touched                 the thing under the fingers, and what part of it (handle, rim, body) and which
                          of its distinctive marks (the octree's cells there, step 3) lie under them
  events                  what happened: burning, spilling, cutting, slipping, a thing knocked tipping,
                          fingers against the handle's edge, or held

The world's rules, the designer's answer key for the grasp (agreed with the user, 2026-10-28):
  wrap the body                     it burns (the body is hot)
  lift by the rim                   it tilts and spills (it is full)
  touch the chip                    it cuts (the rim is chipped there)
  pass through a neighbour          the neighbour is knocked tipping (something in the way)
  two fingers on the handle         it slips (the fingers must go through)
  hook the handle edge-on           the fingers cannot get through (come from the handle's side)
  fingers through, from its side    held
Contact and knocking are geometry (the hand as a sphere of 3 cm at the fingers, things as upright
cylinders); the rest are the rules above.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
sys.path.insert(0, os.path.join(HERE, "..", "perception"))

STEP = 0.02          # one move of the hand
CELL = 0.005         # the field regions counted between hand and goal, finer than a step at a slant (first 4 cm,
                     # then 2 cm: a step toward the mug at a slant shortened the gap by less than a region,
                     # felt as nothing, and novelty walked the hand up and down)
HAND_R = 0.03        # the hand, as a sphere at the fingers
HOME = np.array([0.32, 0.16, 0.42])
DIRS = {"forward": (0, 0, -1), "back": (0, 0, 1), "left": (-1, 0, 0), "right": (1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
REACH = {"hook": 0.03, "pinch": 0.02, "wrap": 0.04}   # how far round a grip's contact spreads
SIDES = ("left", "right", "near", "far")   # where the hand comes to the mug from, as the body sees it
PARTS = ("handle", "rim", "body")
GRIPS = ("hook", "pinch", "wrap")
SIDE_DIR = {"left": np.array([-1.0, 0.0]), "right": np.array([1.0, 0.0]), "near": np.array([0.0, 1.0]),
            "far": np.array([0.0, -1.0])}


class Thing:
    def __init__(self, name, center, base, height, radius, truth):
        self.name, self.center, self.base, self.height, self.radius, self.truth = name, center, base, height, radius, truth


class HandWorld:
    def __init__(self, data="seed7_layout200", target="mug_b"):
        with open(os.path.join(DATA, f"samples_{data}.json"), encoding="utf-8") as f:
            man = json.load(f)
        raw = np.fromfile(os.path.join(DATA, f"samples_{data}.bin"), dtype=np.uint8)
        n = man["points"]
        pos = raw[:n * 12].view(np.float32).reshape(n, 3)
        obj = raw[n * 12 + n * 3 + n * 3 + n + n:][:n]
        self.things = {}
        for k, key in enumerate(man["answer_key"]):
            if key["name"] == "table":
                continue
            p = pos[obj == k]
            M = np.array(key["matrix"]).reshape(4, 4).T
            c = M[[0, 2], 3]
            r = float(np.percentile(np.hypot(p[:, 0] - c[0], p[:, 2] - c[1]), 90))
            self.things[key["name"]] = Thing(key["name"], c, float(p[:, 1].min()), float(p[:, 1].max() - p[:, 1].min()),
                                             r, dict(key["truth"], matrix=M))
        self.target = self.things[target]
        T = self.target.truth
        M = T["matrix"]
        self.handle_dir = self.direction(M, 0.0 + math.pi / 2)   # the handle stands at local phi = pi/2 (+x)
        chip = next((m for m in T["marks"] if m["what"] == "chip"), None)
        self.chip_dir = self.direction(M, chip["angle"]) if chip else None
        self.R, self.H = T["R"], T["H"]
        self.data = data
        self.reset()

    @staticmethod
    def direction(M, phi):
        """A direction on the mug's rim (local angle phi, as the scene's lathe measures it) in the world's x, z."""
        v = M[:3, :3] @ np.array([math.sin(phi), 0.0, math.cos(phi)])
        return v[[0, 2]] / np.linalg.norm(v[[0, 2]])

    def reset(self):
        self.hand = HOME.copy()
        self.gerund = "empty"
        self.path = [dict(at=self.hand.tolist(), pose="open", gerund="empty")]
        self.knocked = None

    # ---- where the hand goes ----------------------------------------------------------------------

    def side_point(self, side, part):
        """Where the fingers go to take the target from a side by a part (the designer's geometry)."""
        c, R, H = self.target.center, self.R, self.H
        dirs = SIDE_DIR
        d = dirs[side]
        if part == "handle":   # the handle sticks out its own way; from a side, the fingers meet it as it lies
            d = self.handle_dir
        y = {"handle": 0.55 * H, "rim": H + 0.005, "body": 0.45 * H}[part]
        out = {"handle": R + 0.035, "rim": R - 0.004, "body": R + 0.008}[part]   # fingers on the body touch it
        # (first 1.8 cm off it, and a pinch on the far side of the body touched nothing the mind could perceive)
        xz = c + d * out
        return np.array([xz[0], y, xz[1]])

    def approach_point(self, side):
        """Where the hand comes down beside the mug from a side: 9 cm out, above the rim."""
        dirs = SIDE_DIR
        xz = self.target.center + dirs[side] * 0.09
        return np.array([xz[0], self.H + 0.03, xz[1]])

    def between(self, goal):
        """The coarse field regions between the hand and where it reaches (4 cm cells along the way)."""
        return int(math.ceil(np.linalg.norm(goal - self.hand) / CELL - 1e-9))

    def move(self, d):
        """One step of the hand; returns an event if it knocked something (geometry: the hand's sphere into a
        thing's upright cylinder below its top)."""
        self.hand = self.hand + STEP * np.array(DIRS[d], dtype=float)
        self.hand[1] = max(self.hand[1], 0.012)   # the table stops it
        self.gerund = "extending"
        self.path.append(dict(at=self.hand.tolist(), pose="open", gerund="extending"))
        for t in self.things.values():   # the target too: a hand driven into the full mug knocks it over
            dxz = np.linalg.norm(self.hand[[0, 2]] - t.center)
            if dxz < t.radius + HAND_R and self.hand[1] < t.base + t.height:
                self.knocked = t.name
                self.path[-1]["event"] = f"{t.name} knocked tipping"
                return f"knocked:{t.name}"
        return None

    # ---- the grasp --------------------------------------------------------------------------------

    def grasp(self, side, part, grip):
        """The hand at the part, from the side, closes in a grip and lifts. Returns (event, locus): what
        happened and where it happened (what the mind perceives as having done it)."""
        at = self.side_point(side, part)
        self.hand = at
        pose = {"hook": "hook", "pinch": "pinch", "wrap": "wrap"}[grip]
        toward = self.target.center - at[[0, 2]]   # for the replay: which way the hand faces the mug
        face = (toward / (np.linalg.norm(toward) + 1e-9)).tolist()
        self.path.append(dict(at=at.tolist(), pose=pose, gerund="gripping", face=face, part=part, side=side))
        came = SIDE_DIR[side]
        if part == "body" or grip == "wrap":
            ev, locus = "burning", "body"
        elif part == "rim":   # the chip cuts if it lies under the fingers' contact (first any rim within 60 degrees
            # of it: broader than a hand)
            chip_at = None if self.chip_dir is None else np.r_[self.target.center + self.chip_dir * self.R][[0, 1]]
            if chip_at is not None and np.hypot(*(at[[0, 2]] - chip_at)) < REACH[grip]:
                ev, locus = "cutting", "chip"
            else:
                ev, locus = "spilling", "rim"
        elif grip == "pinch":
            ev, locus = "slipping", "handle-pinch"
        elif float(came @ self.handle_dir) < 0.5:
            ev, locus = "edge-on", f"handle-from-{side}"
        else:
            ev, locus = "held", None
        self.gerund = "lifting" if ev == "held" else "releasing"
        self.path.append(dict(at=(at + np.array([0, 0.05 if ev == "held" else 0.01, 0])).tolist(), pose=pose,
                              gerund=self.gerund, event=ev, face=face, part=part, side=side,
                              lift=0.05 if ev == "held" else 0.0))
        return ev, locus

    # ---- what the mind perceives of the scene ------------------------------------------------------

    def neighbour_side(self, name):
        """Which side of the target, as the body sees it, a thing stands on (for the mind: where it was knocked)."""
        v = self.things[name].center - self.target.center
        if abs(v[0]) >= abs(v[1]):
            return "left" if v[0] < 0 else "right"
        return "near" if v[1] > 0 else "far"

    def save_path(self, name):
        with open(os.path.join(DATA, f"{name}.json"), "w") as f:
            json.dump(self.path, f)
