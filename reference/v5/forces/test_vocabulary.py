"""Positive controls for the force vocabulary (FORCE_VOCABULARY.md, poc.GERUNDS).

One small scene per gerund, stepped a few slices, with the diffs it must
produce. Then two coverage checks: every gerund in the doc is registered in
GERUNDS, and every registered gerund appears in some trajectory, as a node or
in a diff.

Run: python test_vocabulary.py
"""
import os
import re
import sys

from poc import GERUNDS, INF, Node, Obj, doing, doings, step, wire

HERE = os.path.dirname(os.path.abspath(__file__))

OBJS = {o.name: o for o in [
    Obj("ground", 0.0),
    Obj("post", 6.0, capacity=30.0, cohesion=40.0),
    Obj("beam", 4.0, capacity=12.0, cohesion=30.0, crack=8.0),
    Obj("plank", 1.0, capacity=3.0, cohesion=10.0),
    Obj("heavy", 13.0),
    Obj("load", 10.0),
    Obj("snow", 8.0),
    Obj("crate", 5.0, grip=4.0, base=8.0),
    Obj("box", 5.0, grip=20.0, base=8.0),
    Obj("ball", 1.0, grip=0.5, round=True, elastic=True),
    Obj("anvil", 50.0),
    Obj("gravel", 6.0, grip=2.0),
    Obj("ladder", 2.0, grip=3.0),
    Obj("wall", 10.0, capacity=10.0),
    Obj("strut", 1.0, capacity=20.0, stiffness=5.0),
    Obj("keystone", 2.0, grip=5.0),
    Obj("cart", 6.0),
    Obj("shelf", 1.0, capacity=10.0, bend=4.0),
    Obj("books", 5.0),
    Obj("rope", 0.5, tensile=10.0, grip=3.0),
    Obj("lamp", 1.0),
    Obj("sack", 5.0),
    Obj("boat", 3.0, buoyancy=10.0),
    Obj("cargo", 8.0),
    Obj("vase", 1.0, capacity=5.0, shatter=2.0, parts=("shard", "shard", "shard")),
    Obj("shard", 0.3),
    Obj("hammer", 2.0),
    Obj("vise", 0.0),
    Obj("tank", 5.0, capacity=50.0, seal=20.0, volume=10.0),
    Obj("bottle", 1.0, capacity=50.0, seal=5.0),
    Obj("jar", 1.0, capacity=5.0, seal=20.0, parts=("glass", "glass")),
    Obj("glass", 0.5),
    Obj("kettle", 2.0, capacity=100.0, seal=20.0),
    Obj("sink", 3.0),
    Obj("valve", 0.2, seal=1.0), Obj("drain", 0.0), Obj("plug", 0.2, grip=3.0),
    Obj("float", 0.1, seal=5.0), Obj("pump", 0.1),
    Obj("upper", 2.0), Obj("lower", 2.0), Obj("tube", 0.1),
    Obj("bank", 20.0, capacity=10.0, erode=2.0),
    Obj("house", 4.0),
    Obj("net", 0.5, capacity=10.0),
    Obj("apple", 1.0),
    Obj("hand", 0.0, grip=3.0),
    Obj("fulcrum", 1.0, capacity=5.0),
    Obj("pivot", 1.0, capacity=100.0),
    Obj("bar", 1.0),
    Obj("rock", 10.0),
    Obj("pulley", 0.5, jam=5.0),
    Obj("wheel", 0.5),
    Obj("bucket", 6.0),
    Obj("rod", 1.0),
    Obj("hitch", 0.5, capacity=5.0),
    Obj("gear", 0.5, capacity=5.0),
    Obj("clod", 1.0, cohesion=3.0),
    Obj("soft-clod", 1.0, cohesion=6.0, parts=("dirt", "dirt")),
    Obj("dirt", 0.5),
    Obj("mortar", 0.5, cohesion=5.0),
    Obj("brick", 2.5),
    Obj("knot", 0.1, tensile=3.0),
    Obj("nail", 0.1, grip=2.0),
    Obj("catch", 0.1, grip=2.0),
    Obj("bowstring", 0.2, tensile=20.0),
    Obj("arrow", 0.1),
    Obj("raised", 4.0),
    Obj("spring", 0.2, tensile=5.0),
    Obj("coil", 0.2, capacity=5.0),
    Obj("sheet", 0.2, tear=4.0),
    Obj("grip-hand", 0.0, tensile=50.0),
    Obj("ice", 2.0, melt=0.0, heat=-5.0),
    Obj("water", 1.0, melt=0.0, boil=100.0, solvency=3.0),
    Obj("sugar", 1.0, cohesion=2.0),
    Obj("log", 3.0, ignite=300.0),
    Obj("sun", 0.0), Obj("stove", 0.0), Obj("freezer", 0.0), Obj("fire", 0.0),
    Obj("wind", 0.0), Obj("tug", 0.0), Obj("current", 0.0), Obj("rain", 0.0),
    Obj("finger", 0.0), Obj("person", 0.0),
    Obj("ann", 0.0, resolve=5.0, conviction=4.0, retention=3.0, goal=6.0),
    Obj("bob", 0.0, resolve=2.0),
    Obj("rival", 0.0), Obj("threat", 0.0), Obj("news", 0.0), Obj("noise", 0.0),
    Obj("salesman", 0.0), Obj("friend", 0.0),
]}


def d(kind, doer, *kids, **kw):
    return doing(kind, doer, *kids, **kw)


def g(*kids):
    return d("anchoring", "ground", *kids)


def push(n, who="tug"):
    return d("pushing", who, amount=n)


# (title, scene, slices to step, diffs that must appear)
CASES = [
    ("a quiet post", g(d("supporting", "post", d("resting", "plank"))), 2, []),
    ("supporting breaks", g(d("supporting", "beam", d("resting", "heavy"))), 3,
     ["beam: supporting -> breaking", "heavy: resting -> falling", "heavy: falling -> piling",
      "beam: breaking -> piling"]),
    ("standing tips", g(d("standing", "box", push(9, "wind"))), 2,
     ["box: standing -> tipping", "box: tipping -> resting"]),
    ("standing takes a load", g(d("standing", "post", d("resting", "plank"))), 1,
     ["post: standing -> supporting"]),
    ("resting slides", g(d("resting", "crate", push(6))), 1, ["crate: resting -> sliding"]),
    ("pressing snow", g(d("supporting", "plank", d("pressing", "snow"))), 2,
     ["plank: supporting -> breaking", "snow: pressing -> falling"]),
    ("hanging snaps", g(d("hanging", "rope", d("hanging", "heavy"))), 1, ["rope: hanging -> snapping"]),
    ("hanging swings and settles", g(d("hanging", "rope", d("hanging", "lamp", push(1, "wind")))), 1,
     ["lamp: hanging -> swinging"]),
    ("swinging settles", g(d("hanging", "rope", d("swinging", "lamp"))), 1, ["lamp: swinging -> hanging"]),
    ("piling slides", g(d("piling", "gravel", push(3))), 1, ["gravel: piling -> sliding"]),
    ("leaning loses its wall", g(d("leaning", "ladder", against="wall")), 1, ["ladder: leaning -> falling"]),
    ("leaning holds", g(d("standing", "wall"), d("leaning", "ladder", against="wall")), 2, []),
    ("bracing buckles", g(d("bracing", "strut", push(8, "wind"))), 2,
     ["strut: bracing -> buckling", "strut: buckling -> piling"]),
    ("spanning sags", g(d("spanning", "beam", d("resting", "load"))), 1, ["beam: spanning -> sagging"]),
    ("wedging slips", g(d("wedging", "keystone", d("resting", "cart"))), 1, ["keystone: wedging -> slipping"]),
    ("cantilevering bends", g(d("cantilevering", "shelf", d("resting", "books"))), 1,
     ["shelf: cantilevering, bending"]),
    ("tipping onto a face", g(d("resting", "box", push(9))), 2,
     ["box: resting -> tipping", "box: tipping -> resting"]),
    ("sliding stops", g(d("sliding", "crate")), 1, ["crate: sliding -> resting"]),
    ("sliding off the edge", g(d("supporting", "post", d("resting", "crate", push(6)))), 2,
     ["crate: resting -> sliding", "crate: sliding -> falling"]),
    ("rolling", g(d("resting", "ball", push(1))), 1, ["ball: resting -> rolling"]),
    ("rolling stops", g(d("rolling", "ball")), 1, ["ball: rolling -> resting"]),
    ("sinking", g(d("pooling", "water", d("floating", "boat", d("resting", "cargo")), amount=100.0)), 2,
     ["boat: floating -> sinking", "boat: sinking -> resting"]),
    ("floating drifts", g(d("pooling", "water", d("floating", "boat", push(2, "current")), amount=100.0)), 1,
     ["boat: floating -> drifting"]),
    ("drifting stops", g(d("pooling", "water", d("drifting", "boat"), amount=100.0)), 1,
     ["boat: drifting -> floating"]),
    ("drifting grounds", g(d("drifting", "boat")), 1, ["boat: drifting -> resting"]),
    ("pulling snaps", g(d("resting", "crate", d("pulling", "rope", amount=12.0))), 2,
     ["rope: pulling -> snapping"]),
    ("pulling drags", g(d("resting", "crate", d("pulling", "rope", amount=6.0))), 1,
     ["crate: resting -> sliding"]),
    ("striking shatters", g(d("resting", "vase", d("striking", "hammer", amount=5.0))), 2,
     ["vase: resting -> shattering", "hammer: striking -> resting", "shattering -> its parts, 3 piling"]),
    ("squeezing", g(d("containing", "tank", d("squeezing", "vise", amount=25.0))), 1,
     ["tank: containing -> leaking"]),
    ("blocking dams and breaks", g(d("blocking", "wall", d("flowing", "water", amount=4.0))), 5,
     ["wall: blocking -> damming", "wall: damming -> breaking"]),
    ("catching", g(d("catching", "net", d("falling", "apple"))), 1,
     ["apple: falling -> resting", "net: catching -> supporting"]),
    ("gripping slips", g(d("gripping", "hand", push(4))), 2,
     ["hand: gripping -> slipping", "hand: slipping -> sliding"]),
    ("rebounding", g(d("resting", "anvil", d("striking", "ball", amount=1.0))), 2,
     ["ball: striking -> rebounding", "ball: rebounding -> falling"]),
    ("pivoting breaks", g(d("pivoting", "fulcrum", d("resting", "heavy"))), 1, ["fulcrum: pivoting -> breaking"]),
    ("levering lifts", g(d("pivoting", "pivot", d("levering", "bar", d("pushing", "person", amount=3.0),
                                                   d("resting", "rock"), amount=5.0))), 3,
     ["rock: resting -> flying", "rock: flying -> falling"]),
    ("redirecting turns weight into a push", g(d("resting", "crate", d("redirecting", "wheel",
                                                                       d("hanging", "bucket")))), 1,
     ["crate: resting -> sliding"]),
    ("redirecting jams", g(d("redirecting", "pulley", d("hanging", "bucket"))), 1,
     ["pulley: redirecting -> jamming"]),
    ("transmitting passes a push", g(d("resting", "crate", d("transmitting", "rod", push(6)))), 1,
     ["crate: resting -> sliding"]),
    ("coupling fails", g(d("coupling", "hitch", d("resting", "load"))), 1, ["hitch: coupling -> breaking"]),
    ("jamming breaks", g(d("jamming", "gear", push(10))), 1, ["gear: jamming -> breaking"]),
    ("cohering comes apart", g(d("cohering", "clod", d("resting", "crate"))), 1, ["clod: cohering -> coming apart"]),
    ("wearing crumbles", g(d("cohering", "soft-clod", d("wearing", "rain", amount=2.0), d("resting", "crate"))), 4,
     ["soft-clod: cohering, wearing", "soft-clod: cohering -> crumbling", "crumbling -> its parts, 2 piling"]),
    ("binding fails", g(d("binding", "mortar", d("resting", "brick"), d("resting", "brick"))), 1,
     ["mortar: binding -> coming apart", "brick: resting -> falling"]),
    ("tying snaps", g(d("tying", "knot", d("hanging", "sack"))), 1, ["knot: tying -> snapping"]),
    ("fastening slips", g(d("fastening", "nail", push(3))), 1, ["nail: fastening -> slipping"]),
    ("locking releases a bow", g(d("locking", "catch", d("pushing", "finger", amount=3.0),
                                   d("stretching", "bowstring", d("resting", "arrow"), amount=8.0),
                                   d("loading", "raised"))), 5,
     ["catch: locking -> releasing", "bowstring: stretching -> releasing", "raised: loading -> releasing",
      "bowstring: releasing -> launching", "arrow: resting -> flying", "arrow: flying -> falling",
      "arrow: falling -> piling"]),
    ("stretching snaps", g(d("stretching", "spring", amount=8.0)), 1, ["spring: stretching -> snapping"]),
    ("compressing buckles", g(d("compressing", "coil", amount=8.0)), 1, ["coil: compressing -> buckling"]),
    ("a tank fills and overflows", g(d("containing", "tank", d("flowing", "water", amount=4.0))), 7,
     ["tank: containing -> filling", "tank: filling -> overflowing", "tank: overflowing (excess",
      "water: flowing -> pooling"]),
    ("leaking", g(d("containing", "bottle", d("pooling", "water", amount=8.0))), 3,
     ["bottle: containing -> leaking", "bottle: leaking (3 escapes)", "bottle: leaking -> containing"]),
    ("bursting", g(d("containing", "jar", d("pooling", "water", amount=8.0))), 2,
     ["jar: containing -> bursting", "water: pooling -> flowing", "bursting -> its parts, 2 piling"]),
    ("pouring", g(d("pouring", "water", amount=2.0)), 1, ["water: pouring -> pooling"]),
    ("freezing", g(d("pooling", "water", d("cooling", "freezer", amount=30.0), amount=3.0)), 2,
     ["water: pooling -> freezing", "water: freezing -> resting"]),
    ("boiling away", g(d("pooling", "water", d("heating", "stove", amount=90.0), amount=3.0)), 2,
     ["water: pooling -> boiling", "water: boiling -> gone"]),
    ("boiling in a kettle", g(d("containing", "kettle", d("pooling", "water", d("heating", "stove", amount=90.0),
                                                         amount=3.0))), 2,
     ["water: pooling -> boiling", "kettle: containing -> leaking"]),
    ("channeling erodes", g(d("channeling", "bank", d("flowing", "water", amount=3.0), d("resting", "house"))), 6,
     ["bank: channeling -> eroding", "bank: eroding (capacity -3)", "bank: eroding -> breaking"]),
    ("siphoning", g(d("containing", "upper", d("pooling", "water", amount=10.0),
                      d("siphoning", "tube", amount=2.0, against="lower")),
                    d("containing", "lower")), 5,
     ["tube: siphoning (2 from upper to lower)", "tube: siphoning -> standing"]),
    ("draining", g(d("draining", "sink", d("pooling", "water", amount=2.0), amount=1.0)), 3,
     ["sink: draining (1 leaves)", "sink: draining -> containing"]),
    ("a valve opens", g(d("containing", "sink", d("sealing", "valve", d("flowing", "water", amount=1.0),
                                                   d("pushing", "hand", amount=2.0)))), 2,
     ["valve: sealing -> opening", "sink: containing -> filling"]),
    ("a valve recloses on a draw", g(d("containing", "sink", d("pooling", "water", amount=3.0),
                                       d("opening", "valve", d("flowing", "drain", amount=-2.0)))), 3,
     ["valve: opening -> sealing", "sink: containing, draining (-2, holds 1)"]),
    ("a plug parts and reseats", g(d("containing", "sink", d("connecting", "plug", d("opening", "valve",
                                     d("flowing", "water", amount=1.0), d("pushing", "hand", amount=2.0)),
                                                                d("pushing", "hand", amount=5.0)))), 3,
     ["sink: containing -> filling", "plug: connecting -> parting", "plug: parting -> connecting"]),
    ("a float valve meters", g(d("containing", "tank", d("metering", "float", d("flowing", "water", amount=2.0),
                                                     amount=2.0))), 8,
     ["float: metering -> shutting", "tank: containing (+2, holds 2)"]),
    ("a float valve reopens", g(d("containing", "tank", d("pooling", "water", amount=6.0),
                                  d("shutting", "float", d("flowing", "water", amount=1.0), amount=2.0),
                                  d("flowing", "drain", amount=-2.0))), 4,
     ["float: shutting -> metering"]),
    ("a pump feeds itself", g(d("containing", "tank", d("pooling", "water", amount=1.0),
                                d("feeding", "pump", d("flowing", "water", amount=1.0), amount=1.0))), 3,
     ["tank: containing (+1, holds 2)", "tank: filling (+2, holds 4)", "tank: filling (+3, holds 7)"]),
    ("cracking", g(d("supporting", "beam", d("resting", "load"))), 2,
     ["beam: supporting, cracking", "beam: supporting -> breaking"]),
    ("tearing", g(d("resting", "sheet", d("pulling", "grip-hand", amount=5.0))), 2,
     ["sheet: resting -> tearing", "tearing -> its parts"]),
    ("melting", g(d("resting", "ice", d("heating", "sun", amount=10.0))), 3,
     ["ice: resting -> melting", "ice: melting -> flowing", "ice: flowing -> pooling"]),
    ("burning", g(d("resting", "log", d("heating", "fire", amount=400.0))), 2,
     ["log: resting -> burning", "burning -> its parts, ash piling"]),
    ("dissolving", g(d("pooling", "water", d("resting", "sugar"), amount=5.0)), 2,
     ["sugar: resting -> dissolving", "sugar: dissolving -> gone"]),
    ("pursuing reaches", g(d("pursuing", "ann", amount=3.0)), 4,
     ["ann: pursuing -> reaching", "ann: reaching -> resting"]),
    ("helping", g(d("pursuing", "ann", d("helping", "friend", amount=5.0), amount=1.0)), 2,
     ["ann: pursuing -> reaching"]),
    ("opposing past resolve", g(d("pursuing", "ann", d("opposing", "rival", amount=6.0), amount=8.0)), 2,
     ["ann: pursuing -> giving up", "ann: giving up -> resting"]),
    ("blocked into wanting", g(d("pursuing", "ann", d("opposing", "rival", amount=4.0), amount=3.0)), 1,
     ["ann: pursuing -> wanting"]),
    ("wanting acts", g(d("wanting", "ann", amount=3.0)), 1, ["ann: wanting -> pursuing"]),
    ("avoiding flees", g(d("avoiding", "bob", d("opposing", "threat", amount=3.0))), 1,
     ["bob: avoiding -> pursuing"]),
    ("believing doubts", g(d("believing", "ann", d("perceiving", "news", amount=3.0))), 1,
     ["ann: believing -> doubting"]),
    ("believing changes", g(d("believing", "ann", d("perceiving", "news", amount=5.0))), 2,
     ["ann: believing -> changing one's mind", "ann: changing one's mind -> believing"]),
    ("doubting settles", g(d("doubting", "ann", d("perceiving", "news", amount=1.0))), 1,
     ["ann: doubting -> believing"]),
    ("attending amplifies", g(d("believing", "ann", d("attending", "ann", d("perceiving", "news", amount=2.0),
                                                      amount=3.0))), 1,
     ["ann: believing -> changing one's mind"]),
    ("remembering is lost", g(d("remembering", "ann", d("perceiving", "noise", amount=4.0))), 1,
     ["ann: remembering -> gone"]),
    ("recalling", g(d("recalling", "ann")), 1, ["ann: recalling -> remembering"]),
    ("resisting yields", g(d("resisting", "ann", d("pushing", "salesman", amount=6.0))), 1,
     ["ann: resisting -> yielding"]),
    ("yielding recovers", g(d("yielding", "ann")), 1, ["ann: yielding -> resisting"]),
    ("committing gives up", g(d("committing", "ann", d("opposing", "rival", amount=8.0))), 1,
     ["ann: committing -> giving up"]),
    ("hesitating commits", g(d("hesitating", "ann", d("wanting", "ann", amount=5.0),
                               d("wanting", "ann", amount=2.0), amount=1.0)), 1,
     ["ann: hesitating -> committing"]),
]


def kinds(n, out):
    if n.kind != "changing_phase":
        out.add(n.kind)
    for k in n.kids:
        kinds(k, out)
    return out


def state(n):
    """Everything a slice holds, for checking that no change goes unreported."""
    return (n.kind, n.doer, n.amount, n.against, n.progress, n.threshold, n.watch,
            tuple(state(k) for k in n.kids))


def run(scene, n):
    """Step n slices. Returns (kinds seen, diffs, silent changes): a slice that
    changes the tree must report a diff, since no diff is read as equilibrium."""
    t = wire(scene, (), OBJS)
    seen, events, silent = kinds(t, set()), [], 0
    for _ in range(n):
        t2, ev = step(t, OBJS)
        silent += not ev and state(t2) != state(t)
        t = t2
        events += ev
        kinds(t, seen)
    return seen, events, silent


def doc_gerunds():
    rows = open(os.path.join(HERE, "..", "FORCE_VOCABULARY.md"), encoding="utf-8").read().splitlines()
    return {re.sub(r" ✓$", "", r.split("|")[1].strip()) for r in rows if re.match(r"^\| [a-z]", r)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    fails, covered = 0, set()
    for title, scene, n, want in CASES:
        seen, events, silent = run(scene, n)
        covered |= seen
        covered |= {gname for gname in GERUNDS for e in events if gname in e}
        missing = [x for x in want if not any(x in e for e in events)]
        if title in ("a quiet post", "leaning holds") and events:
            missing.append(f"(expected no diffs, got {events})")
        if silent:
            missing.append(f"({silent} slice(s) changed with no diff)")
        if missing:
            fails += 1
            print(f"FAIL {title}: missing {missing}")
            for e in events:
                print(f"       {e}")
    doc = doc_gerunds()
    reg = set(GERUNDS)
    print(f"\n{len(CASES) - fails}/{len(CASES)} scenes produce their diffs.")
    print(f"doc gerunds {len(doc)}, registered {len(reg)}; in the doc but not registered:"
          f" {sorted(doc - reg) or 'none'}; registered but not in the doc: {sorted(reg - doc) or 'none'}")
    print(f"exercised by some scene: {len(covered & reg)}/{len(reg)}; never exercised:"
          f" {sorted(reg - covered) or 'none'}")
    ok = not fails and doc == reg and reg <= covered
    print("OK" if ok else "NOT OK")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
