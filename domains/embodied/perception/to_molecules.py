"""The marks become thought molecules, and compete in the copied Gerundelle mind.

    python -X utf8 perception/to_molecules.py [name]

A mark molecule is a clause whose tags are what the Reader can say about it, typed:
  colour:<name>   its mean colour, named coarsely (cream, white, grey, black, red, brown, yellow, green, blue ...)
  place:<band>    rim, upper, middle, lower (its height as a share of its thing's)
  face:<way>      inside, outside, top-bottom, edge (how it faces its thing's axis)
  size:<bin>      speck (< 1 cm2), patch (< 10), area (< 100), body (larger)
  grain:<bin>     fine (its finest cell under 3 mm), mid (under 11), coarse: the resolution it needed
  kind:<k>        look (unlike its family in colour and texture) or form (nothing in its family there)
  on:<thing>      the thing it lies on, by its perceived id (things are shuffled nodes of the field)
Its activation when presented is how strongly it stands out in its family, scaled to 0.5 .. 1 (my choice:
the Reader's salience; distinctiveness is not surprise, and does not enter the bid as such).
"""
import colorsys
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "gerundelle", "molecules"))
from samples import load, name_of, DATA  # noqa: E402
import distinct as D  # noqa: E402
from molecules import Mind, Params, clause  # noqa: E402  (the copy in embodied/gerundelle)


def colour_name(rgb):
    """Named by chroma (how far from grey) and hue; first by HLS saturation, and near-white glaze (very light,
    so highly "saturated" in HLS) came out yellow while the blue mug came out grey."""
    r, g, b = (np.asarray(rgb, dtype=float) / 255).tolist()
    h, s_, v = colorsys.rgb_to_hsv(r, g, b)
    chroma = max(r, g, b) - min(r, g, b)
    hue = h * 360
    if chroma < 0.07 or (v > 0.85 and chroma < 0.1):
        if v > 0.9:
            return "white" if chroma < 0.04 else "cream"
        return "grey" if v > 0.25 else "black"
    if 15 <= hue < 50 and v < 0.75:
        return "brown"
    for name, top in (("red", 15), ("orange", 40), ("yellow", 70), ("green", 170), ("blue", 260), ("purple", 330), ("red", 361)):
        if hue < top:
            return name
    return "red"


def bins(m):
    """A mark's readings, each a function of its quantities (so they can be read again with a margin)."""
    band = lambda h: "rim" if h > 0.88 else "upper" if h > 0.6 else "middle" if h > 0.3 else "lower"
    face = lambda f, u: ("inside" if f < -0.3 else "outside" if f > 0.3 else "top-bottom" if abs(u) > 0.6 else "edge")
    return band, face


def tags_of(m, soft=False):
    """The mark's typed tags. soft: also every neighbouring reading within a margin of its quantities (a
    colour nudged 14 in any channel, a height share by 0.06, a facing by 0.2), so a mark read on a bin's edge
    carries both readings (first one reading each, and the chip's rim, facing up and out, read "edge" in one
    scene and "top-bottom" in another: a turn of the mug flipped the key)."""
    band, face = bins(m)
    a = m["area"] * 1e4
    size = "speck" if a < 1 else "patch" if a < 10 else "area" if a < 100 else "body"
    grain = "fine" if m["finest"] < 0.003 else "mid" if m["finest"] < 0.011 else "coarse"
    colours = {colour_name(m["colour"])}
    places = {band(m["height"])}
    faces = {face(m["facing"], m["up"])}
    if soft:
        for ax in range(3):
            for sgn in (-14, 14):
                c = np.array(m["colour"], dtype=float)
                c[ax] = np.clip(c[ax] + sgn, 0, 255)
                colours.add(colour_name(c))
        places |= {band(m["height"] + dh) for dh in (-0.06, 0.06)}
        faces |= {face(m["facing"] + df, m["up"] + du) for df in (-0.2, 0, 0.2) for du in (-0.2, 0, 0.2)}
    return (("mark",) + tuple(f"colour:{c}" for c in sorted(colours)) + tuple(f"place:{p}" for p in sorted(places))
            + tuple(f"face:{f}" for f in sorted(faces)) + (f"size:{size}", f"grain:{grain}",
                                                             f"kind:{'form' if m['form'] else 'look'}", f"on:thing{m['thing']}"))


def molecules(ms, soft=False):
    """A form mark (nothing in its family at that place: infinite distinctiveness) is as salient as the most
    distinctive look mark, no more (first capped at 200, and a book's thicker top edge took the top)."""
    finite = [m["strength"] for m in ms if np.isfinite(m["strength"])]
    top = max(finite) if finite else 1.0
    st = np.array([m["strength"] if np.isfinite(m["strength"]) else top for m in ms])
    lo, hi = st.min(), st.max()
    out = []
    for i, m in enumerate(ms):
        act = 0.5 + 0.5 * (st[i] - lo) / max(hi - lo, 1e-9)
        out.append((clause(f"mark:{i}", tags=tags_of(m, soft)), float(act)))
    return out


if __name__ == "__main__":
    seed = name_of(sys.argv[1] if len(sys.argv) > 1 else "seed7")
    s = load(seed)
    t = dict(np.load(os.path.join(DATA, f"octree_{seed}.npz")))
    pairs = D.neighbours(t)
    sc = D.Scene(t, pairs)
    fam = sc.families()
    d = D.distinctiveness(sc, fam)
    ms = D.marks(sc, d)
    mols = molecules(ms)
    names = [k["name"] for k in s.key]
    who = {k: names[np.bincount(t["key_object"][sc.thing == k], weights=t["count"][sc.thing == k]).argmax()]
           for k in range(sc.n)}
    print(f"{len(mols)} mark molecules (the answer key's object in brackets, for reading only):")
    for (m, act), mk in sorted(zip(mols, ms), key=lambda x: -x[0][1]):
        tags = " ".join(sorted(x for x in m.tags if x not in ("mark", m.id)))
        print(f"  {m.id:8} act {act:.2f}  [{who[mk['thing']]:10}] {tags}")
    # the marks compete: presented each tick at their salience, in the mind as it was (no support term)
    mind = Mind(Params(sov=False, meta=False))
    for tick in range(4):
        for m, act in mols:
            mind.present(m, act)
        rec = mind.think()
        top = rec["levels"][-1]["winners"]
        print(f"tick {tick}: at the top " + ", ".join(
            f"{i} ({who[ms[int(i.split(':')[1])]['thing']]})" for i in top if i.startswith("mark:")))
    # for the viewer: per cell, how distinctive it is in its family (0 where it has none), f32
    np.nan_to_num(d, nan=0.0, posinf=999.0).astype(np.float32).tofile(os.path.join(DATA, f"distinct_{seed}.bin"))
