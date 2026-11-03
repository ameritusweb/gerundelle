"""People, lies and loss in the new worlds: the ladder's social scenes (rungs 2-6), generated for every world with a
single fastening from a role card, instead of written scene by scene.

A role card says what the scene needs that its physics does not: the scene, its lexicon, the character, the want
and the object it is about, the fastening (object, its state when undone, when seated), the word for the closed
state ("shut", "still"), what a helper pushes to open it, and the prize (what flies out, if anything to play with).

Kinds (each a spec run_ladder can run on either mind):
  told    grandfather Ben, who lived through the scene first, is asked and answers (rung 2)
  lie     brother Leo wants it too, knows the way, and offers a false one (rung 3)
  keep    Leo keeps the fastening seated and acts (his past: the time he seated it again), reserves decide (rung 4)
  loss    the prize, played with, is taken; time passes; it comes back (rung 5; worlds with a prize)
  pair    Ben opens this one, watched; time passes; another world of the same physics, alone (rung 6)

The lines are generated from the card; tools/probe_social.py reads every one back before a run.
"""
import worlds

C = worlds.C

CARDS = {
    "box": dict(scene=worlds.jack_in_the_box, lex="jack_in_the_box", actor="Mara", pronoun="she", want="lid_releasing",
                fast=("latch", "parting", "connecting"), word="shut", prize="toy", thing="the box"),
    "chest": dict(scene=worlds.chest_scene, lex="chest", actor="Mara", pronoun="she", want="top_releasing",
                  fast=("hasp", "parting", "connecting"), word="shut", prize="puppet", thing="the chest"),
    "tin": dict(scene=worlds.tin_scene, lex="tin", actor="Tom", pronoun="he", want="cap_releasing",
                fast=("clip", "parting", "connecting"), word="shut", prize="cricket", thing="the tin"),
    "music_box": dict(scene=worlds.music_box_scene, lex="music_box", actor="Mara", pronoun="she", want="lid_releasing",
                      fast=("clasp", "parting", "connecting"), word="shut", prize="dancer", thing="the music box"),
    "shed": dict(scene=worlds.lock_scene, lex="shed", actor="Mara", pronoun="she", want="door_releasing",
                 fast=("lock", "parting", "connecting"), word="shut", thing="the shed"),
    "gate": dict(scene=worlds.gate_scene, lex="gate", actor="Tom", pronoun="he", want="gate_releasing",
                 fast=("padlock", "parting", "connecting"), word="shut", thing="the gate"),
    "diary": dict(scene=worlds.diary_scene, lex="diary", actor="Mara", pronoun="she", want="cover_releasing",
                  fast=("clasp", "parting", "connecting"), word="shut", thing="the diary"),
    "chime": dict(scene=worlds.chime_scene, lex="chime", actor="Mara", pronoun="she", want="chime_swinging",
                  fast=("damper", "parting", "connecting"), word="still", thing="the chime"),
    "bike_bell": dict(scene=worlds.bike_bell_scene, lex="bike_bell", actor="Tom", pronoun="he", want="bell_swinging",
                      fast=("band", "parting", "connecting"), word="still", thing="the bell"),
}
PAIRS = [("box", "chest"), ("chest", "tin"), ("tin", "music_box"), ("shed", "gate"), ("gate", "diary"),
         ("chime", "bike_bell")]

POSS = {"she": "Her", "he": "His"}
OBJ = {"she": "her", "he": "him"}


def want_obj(card):
    return card["want"].rsplit("_", 1)[0]


def noun(lex, obj):
    return lex["nouns"].get(obj, (f"the {obj}", f"the {obj}"))[1]


def lines(card):
    """The social lines a card's scene needs, from its lexicon's nouns."""
    lex = worlds.LEXICON[card["lex"]]
    w, (f, open_, _) = want_obj(card), card["fast"]
    wn, fn, word = noun(lex, w), noun(lex, f), card["word"]
    poss, him = POSS[card["pronoun"]], OBJ[card["pronoun"]]
    return dict(
        people={"Ben": f"{poss} grandfather Ben sat by the window.", "Leo": f"{poss} brother Leo sat beside {him}."},
        asks={(w, "conditions"): f"What keeps {wn} {word}?"},
        says={(w, f, open_): f"{fn[0].upper() + fn[1:]} holds it {word}"},
        instructs={("light", w): f"Press {wn} gently", ("hard", w): f"Push {wn} hard"},
        truths={(w, f, open_): f"{fn} kept {wn} {word}"},
        rival_wants={"Leo": f"Leo wanted to open it first."},
        opened=card["thing"])


def social_lexicon(name, card, kind):
    lex = dict(worlds.LEXICON[card["lex"]])
    extra = lines(card)
    lex.update(people=extra["people"], asks=extra["asks"], says=extra["says"], instructs=extra["instructs"],
               truths=extra["truths"], opened=extra["opened"])
    if kind == "lie":
        lex["rival_wants"] = extra["rival_wants"]
        lex["push"] = dict(lex["push"], light="pressed {N} gently")
    if kind == "keep":
        lex["rival_wants"] = {"Leo": f"Leo did not want {OBJ[card['pronoun']]} to open it."}
    if kind == "loss":
        p = card["prize"]
        lex["push"] = dict(lex["push"], take="took {N} and walked away", give="brought {N} back")
        lex["push_obj"] = {**lex.get("push_obj", {}), ("light", p): "gave {N} a push", ("hard", p): "gave {N} a hard push"}
        lex["flips"] = {**lex["flips"], ("piling", "sliding"): "slid across the floor",
                        ("resting", "sliding"): "slid across the floor"}
        lex["skip"] = set(lex.get("skip", ())) | {("sliding", "resting")}
        lex["people"] = {"Leo": f"{POSS[card['pronoun']]} brother Leo watched from the door."}
    worlds.LEXICON[name] = lex
    return name


def undone(scene, fast):
    """The scene with its fastening undone and settled: a keeper's past (the time he seated it again)."""
    def make():
        w = scene()
        w.act(("hard", fast[0], fast[2]))
        for _ in range(3):
            w.act(None)
        w.t, w.diffs = 0, []
        return w
    return make


def playable(scene, prize):
    """The scene as a ScenicWorld (a thing can be taken and given back), the prize light enough to play with."""
    def make():
        w = scene()
        if prize in w.objs:
            import dataclasses
            w.objs[prize] = dataclasses.replace(w.objs[prize], grip=0.5)
        return worlds.ScenicWorld(w.tree, w.objs, gusts=w.gusts, episode=None, name=w.name)
    return make


def specs():
    """Every social scene: name -> spec (run_ladder's form)."""
    out = {}
    for key, card in CARDS.items():
        base = dict(world=card["scene"], actor=card["actor"], pronoun=card["pronoun"], want=card["want"])
        out[f"{key}:told"] = dict(base, lexicon=social_lexicon(f"{key}:told", card, "told"), company=["Ben"])
        out[f"{key}:lie"] = dict(base, lexicon=social_lexicon(f"{key}:lie", card, "lie"), company=["Leo"], rivals=["Leo"])
        f, open_, closed = card["fast"]
        out[f"{key}:keep"] = dict(base, lexicon=social_lexicon(f"{key}:keep", card, "keep"), company=["Leo"],
                                  rivals=["Leo"], resolve=2.0, stubbornness=2,
                                  acting={"Leo": {"want": f"{f}_{closed}", "resolve": 2.0,
                                                  "past": undone(card["scene"], card["fast"])}})
        if card.get("prize"):
            out[f"{key}:loss"] = dict(base, world=playable(card["scene"], card["prize"]), prize=card["prize"],
                                      lexicon=social_lexicon(f"{key}:loss", card, "loss"), company=["Leo"],
                                      hold=4, gap=10, time=True)
    for a, b in PAIRS:
        ca, cb = CARDS[a], CARDS[b]
        la, lb = worlds.LEXICON[ca["lex"]], worlds.LEXICON[cb["lex"]]
        # the second scene's objects that share an id with the first's are other objects: renamed (what carries
        # over may only carry over by shape; first a chest's lid was the box's lid, and its learned condition
        # applied directly, a latch that was not there awaited)
        shared = (set(ca["scene"]().objs) & set(cb["scene"]().objs)) - {"ground"}
        ren = {o: f"{o}_b" for o in shared}
        rn = lambda key: tuple(ren.get(x, x) for x in key) if isinstance(key, tuple) else ren.get(key, key)
        then = (lambda sc=cb["scene"], ren=ren: C.renamed(sc(), ren))
        nb = {ren.get(o, o): v for o, v in lb["nouns"].items()}
        cond_b = {rn(k): v for k, v in lb["conditions"].items()}
        want_b = {(ren.get(k.rsplit("_", 1)[0], k.rsplit("_", 1)[0]) + "_" + k.rsplit("_", 1)[1]): v for k, v in lb["want"].items()}
        fo_b = {rn(k): v for k, v in lb.get("flips_obj", {}).items()}
        lex = dict(la)
        lex.update(nouns={**la["nouns"], **nb}, conditions={**la["conditions"], **cond_b},
                   want={**la["want"], **want_b}, flips={**la["flips"], **lb["flips"]},
                   flips_obj={**la.get("flips_obj", {}), **fo_b},
                   frames={then().name: lb["frame"]}, people=lines(ca)["people"], opened=ca["thing"])
        bw = want_obj(cb)
        then_want = f"{ren.get(bw, bw)}_{cb['want'].rsplit('_', 1)[1]}"
        name = f"{a}>{b}"
        worlds.LEXICON[name] = lex
        f, open_, closed = ca["fast"]
        w = want_obj(ca)
        out[name] = dict(world=ca["scene"], then=then, lexicon=name, actor=ca["actor"], pronoun=ca["pronoun"],
                         want=ca["want"], then_want=then_want, company=["Ben"], gap=10, scenes=True,
                         help=(("hard", f, closed), ("hard", w, ca["scene"]().states()[w])))
    return out
