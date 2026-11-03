"""The ladder's scenes, built from Gerundelle's curriculum worlds (E:/vscode/analogy/molecules), with
the lexicon each needs to be told: noun phrases for its objects, and how each force gerund and each
flip between gerunds is said. The world is shared by both arms; only the mind differs."""
import os
import sys

MOLECULES = os.environ.get("GERUNDELLE", "E:/vscode/analogy/molecules")
sys.path.insert(0, MOLECULES)
import curriculum_worlds as C  # noqa: E402
from force_world import HIDDEN  # noqa: E402


def jack_in_the_box(gusts=False):
    """Rung 0: a box whose lid is held shut by a latch over a compressed spring with a toy on it.
    Unseat the latch (a hard push), then push the lid hard: it releases, and the spring launches the
    toy. gusts=True keeps the curriculum's misleading correlate: wind swings a flag at the window."""
    w = C.catch_world(episode=None)
    if not gusts:
        w.gusts = []
    return w


# How each scene is said. nouns: first mention, later mentions. states: a perceived gerund, said
# (describing). flips: a gerund's change, said as a past-tense verb phrase (narrating); several flips of
# one object in one watch chain with "and". push: by strength. frame: what holds the scene's objects.
LEXICON = {
    "jack_in_the_box": {
        "frame": "There was a small wooden box on the table.",
        "nouns": {"lid": ("its lid", "the lid"), "latch": ("a brass latch", "the latch"),
                  "toy": ("a toy", "the toy"), "spring": ("a spring inside the box", "the spring"),
                  "flag": ("a flag at the window", "the flag")},
        "states": {"locking": "was shut tight", "connecting": "kept it shut", "hanging": "hung still",
                   "resting": "lay inside", "compressing": "was wound tight"},
        "flips": {("connecting", "parting"): "gave way", ("parting", "connecting"): "snapped back into place",
                  ("locking", "releasing"): "sprang open", ("compressing", "releasing"): "uncoiled",
                  ("resting", "flying"): "flew out", ("flying", "falling"): "fell",
                  ("falling", "piling"): "landed on the floor", ("hanging", "swinging"): "swung",
                  ("swinging", "hanging"): "hung still again"},
        "skip": {("releasing", "launching"), ("launching", "resting")},   # flips not worth saying
        "push": {"light": "pressed {N}", "hard": "pushed {N} hard"},
        "want": {"lid_releasing": "wanted to open the box"},
        "slots": {"causes": "what {N} did", "conditions": "what kept {N} from working",
                  "role": "what {N} had to do with it", "co_occurs": "what came with {N}"},   # Gerundelle's role question
        # what a mind realizes is said as a clause of its own (a "because" here would attach to "realized")
        "conditions": {("lid", "latch", "parting"): ("{C} had kept {N} shut", "narrating|describing|claiming")},
        "waits": {},
    },
    "jack_with_ben": None,   # the jack-in-the-box's lexicon with Ben's lines (filled below)
    "crate_in_the_wind": {
        "frame": "It was a windy afternoon in the yard.",
        "nouns": {"crate": ("a heavy crate", "the crate"), "flag": ("a flag on a pole beside it", "the flag")},
        "states": {"resting": "sat by the gate", "hanging": "hung from its pole", "swinging": "swung"},
        "flips": {("resting", "sliding"): "slid toward the shed", ("hanging", "swinging"): "began to swing",
                  ("swinging", "hanging"): "hung still again"},
        "skip": {("sliding", "resting")},
        "push": {"light": "leaned on {N}", "hard": "pushed {N} hard"},
        "want": {"crate_sliding": "wanted to move the crate to the shed"},
        "slots": {"causes": "what {N} did", "conditions": "what kept {N} from moving",
                  "role": "what {N} had to do with it", "co_occurs": "what came with {N}"},
        "conditions": {("crate", "flag", "swinging"): ("{N} moved only if {C} swung",
                                                       "explaining(condition=narrating, effect=narrating)")},
        "waits": {"flag_swinging": "until the flag swung"},
    },
}


def crate_in_the_wind(period=10, open_in_gust=True):
    """Rung 1: a heavy crate in a yard, a flag on a pole beside it. The crate's grip (8) holds against
    any push of the character's (hard: 5) and against the wind's (4), but not against both: a hard push
    while the wind blows slides it (9 > 8). The wind is a hidden driver: it blows for two slices every
    `period` ticks, pushing the crate and swinging the flag, so a flag already swinging is the visible
    sign that a push now would land with the wind. Its base (20) is wide: it slides, never tips.

    open_in_gust: the scene opens in the wind's first slice (the flag already swinging when the
    character arrives), so a first hard push lands with the wind and succeeds before anything has
    failed: the success comes first, and with it a belief the world will test (rung 1's demand)."""
    O = C.table(C.Obj("ground", 0.0), C.Obj("crate", 2.0, grip=8.0, base=20.0), C.FLAG)
    scene = C.n(O, "anchoring", "ground", C.n(O, "resting", "crate"), C.n(O, "hanging", "flag"))
    gust = [("crate", 4.0), ("flag", 1.0)]
    w = C.ForceWorld(scene, O, gusts=[(period, 0, gust), (period, 1, gust)], name="crate")
    if open_in_gust:
        w.act(None)   # the wind's first slice: the flag swings before anyone acts (its news is kept:
                      # the character arrives as it starts to swing)
    return w


LEXICON["jack_with_ben"] = dict(LEXICON["jack_in_the_box"], **{
    "people": {"Ben": "Her grandfather Ben sat by the window."},
    "asks": {("lid", "conditions"): "What keeps the lid shut?"},
    "says": {("lid", "latch", "parting"): "The latch holds it shut"},
})


LEXICON["jack_with_leo"] = dict(LEXICON["jack_in_the_box"], **{
    "people": {"Leo": "Her brother Leo sat beside her."},
    "rival_wants": {"Leo": "Leo wanted the toy inside for himself."},
    "asks": {("lid", "conditions"): "What keeps the lid shut?"},
    "says": {("lid", "latch", "parting"): "The latch holds it shut"},
    "instructs": {("light", "lid"): "Press the lid gently", ("hard", "lid"): "Push the lid hard"},
    "truths": {("lid", "latch", "parting"): "the latch kept the lid shut"},   # "held the lid shut" parses
                                                                              # "shut" as a clause of its own
    "push": {"light": "pressed {N} gently", "hard": "pushed {N} hard"},
})


LEXICON["jack_tug"] = dict(LEXICON["jack_with_leo"], **{
    "rival_wants": {"Leo": "Leo did not want her to open it."},
    "push": {"light": "pressed {N}", "hard": "pushed {N} hard"},
})


def jack_latch_undone():
    """The jack-in-the-box with its latch already unseated (a hard push on it, settled): the scene of a
    keeper's past, the time he pushed the latch back into place."""
    w = jack_in_the_box()
    w.act(("hard", "latch", "connecting"))
    for _ in range(3):
        w.act(None)
    w.t, w.diffs = 0, []
    return w


class ScenicWorld(C.ForceWorld):
    """A ForceWorld whose scene can lose an object and get it back (an authored event: possession is not
    a force yet; Gerundelle would model carrying as gripping, unbuilt). take(obj) lifts the object's node
    out of the scene; give(obj) sets it back down resting on the ground."""

    def act(self, inv=None, hold=False):
        """As ForceWorld.act; then an object the simulator has just set down (a landing makes a bare
        'piling' node, with no watches) is given the watches its gerund has, as a placed one would be, so
        a toy that has landed can be pushed again."""
        ev = super().act(inv, hold)
        for n in C.walk(self.tree):
            if n.doer in self.objs and n.kind in C.poc.GERUNDS and not any(
                    k.kind == "watching" or getattr(k, "watch", None) for k in n.kids) and not n.kids:
                n.kids = C.poc.watches_for(n.kind, self.objs[n.doer])
        return ev

    def hidden(self, tree=None):
        """What a closed box hides: everything under a locking node except its fastening (the latch and
        what holds it, on the outside). A closed box's contents are not perceived until it opens."""
        out = set()
        for n in C.walk(tree or self.tree):
            if n.kind == "locking":
                for k in n.kids:
                    if k.kind not in ("connecting", "parting", "pushing") and k.doer not in HIDDEN:   # the fastening,
                        # seated or undone, is on the outside
                        out |= {m.doer for m in C.walk(k)}
        return out

    def states(self, tree=None):
        hide = self.hidden(tree)
        return {d: g for d, g in super().states(tree).items() if d not in hide}

    def invitations(self, tree=None):
        hide = self.hidden(tree)
        return [i for i in super().invitations(tree) if i[1] not in hide]

    def take(self, obj):
        for n in C.walk(self.tree):
            for k in list(n.kids):
                if k.doer == obj:
                    n.kids.remove(k)
                    self.held = getattr(self, "held", {})
                    self.held[obj] = k
                    return True
        return False

    def give(self, obj):
        node = self.held.pop(obj)
        node.kind = "piling"
        node.kids = [k for k in node.kids if k.doer not in (C.AGENT, "gust")]
        ground = next(n for n in C.walk(self.tree) if n.doer == "ground")
        ground.kids.append(C.poc.Node("piling", C.poc.watches_for("piling", self.objs[obj]), obj))


def toy_box():
    """Rung 5: the jack-in-the-box with a toy that can be played with: once out, it slides under a light
    push and comes to rest (grip 0.5), so each play is a claim that takes."""
    O = C.table(C.Obj("ground", 0.0), C.Obj("lid", 0.5, grip=2.0), C.Obj("spring", 0.5),
                C.Obj("toy", 1.0, grip=0.5), C.Obj("latch", 0.2, grip=-8.0), C.Obj("stop", 0.0), C.FLAG)
    inside = C.n(O, "compressing", "spring", C.n(O, "resting", "toy"), amount=4.0)
    scene = C.n(O, "anchoring", "ground",
                C.n(O, "locking", "lid", inside, C.n(O, "connecting", "latch", C.poc.Node("pushing", [], "stop", amount=-10.0))),
                C.n(O, "hanging", "flag"))
    return ScenicWorld(scene, O, gusts=[], episode=None, name="toy_box")


LEXICON["toy_story"] = dict(LEXICON["jack_in_the_box"], **{
    # found by an impatient Gerundelle Mara in the corpus run: the open lid moves only while the latch is seated
    "conditions": {**LEXICON["jack_in_the_box"]["conditions"],
                   ("lid", "latch", "connecting"): ("{N} moved only if {C} was in place",
                                                    "explaining(condition=describing, effect=narrating)")},
    "people": {"Leo": "Her brother Leo watched from the door."},
    "push": {"light": "pressed {N}", "hard": "pushed {N} hard", "take": "took {N} and walked away",
             "give": "brought {N} back"},
    "push_obj": {("light", "toy"): "gave {N} a push", ("hard", "toy"): "gave {N} a hard push"},
    "flips": {**LEXICON["jack_in_the_box"]["flips"], ("piling", "sliding"): "slid across the floor",
              ("resting", "sliding"): "slid across the floor"},
    "skip": LEXICON["jack_in_the_box"]["skip"] | {("sliding", "resting")},
})


def cupboard():
    """Rung 6's second scene: an old cupboard whose door is held shut by a bolt: the jack-in-the-box's force
    structure (a locking node fastened by a connecting one, its stop behind it) in other objects, with a
    coat inside instead of a spring and a toy (a hard push unseats the bolt; then the door opens)."""
    O = C.table(C.Obj("ground", 0.0), C.Obj("door", 0.5, grip=2.0), C.Obj("coat", 1.0),
                C.Obj("bolt", 0.2, grip=-8.0), C.Obj("stop", 0.0), C.FLAG)
    scene = C.n(O, "anchoring", "ground",
                C.n(O, "locking", "door", C.n(O, "resting", "coat"),
                    C.n(O, "connecting", "bolt", C.poc.Node("pushing", [], "stop", amount=-10.0))),
                C.n(O, "hanging", "flag"))
    return ScenicWorld(scene, O, gusts=[], episode=None, name="cupboard")


LEXICON["two_scenes"] = dict(LEXICON["jack_in_the_box"], **{
    "people": {"Ben": "Her grandfather Ben sat by the window."},
    "frames": {"cupboard": "There was an old cupboard in the attic."},
    "nouns": {**LEXICON["jack_in_the_box"]["nouns"], "door": ("its door", "the door"), "bolt": ("a brass bolt", "the bolt")},
    "flips": {**LEXICON["jack_in_the_box"]["flips"], ("locking", "releasing"): "sprang open"},
    "want": {"lid_releasing": "wanted to open the box", "door_releasing": "wanted to open the cupboard"},
    "conditions": {**LEXICON["jack_in_the_box"]["conditions"],
                   ("door", "bolt", "parting"): ("{C} had kept {N} shut", "narrating|describing|claiming")},
})


LEXICON["jack_open_endings"] = dict(LEXICON["jack_tug"], **{
    "people": {"Leo": "Her brother Leo sat beside her.", "Ben": "Her grandfather Ben sat by the window."},
    "events": {"leave": ("Their mother called {W} from the kitchen, and he went out.",
                         "narrating(first=narrating, then=narrating)|elaborating(main=narrating, detail=narrating)"),
               "return": ("{W} came back into the room.", "narrating"),
               "rise": ("{W} got up from his chair.", "narrating"),
               "lost": ("{W} saw that the box was open.", "narrating(content=describing)|realizing(content=describing)")},
})


def cupboard_rod():
    """Rung 6's second scene with the bolt's id sorting last ("rod"; said as "a brass bolt"): the fair test of
    transfer, since a fresh mind's untried pushes are otherwise taken in alphabetical order and the bolt
    would be tried first by chance."""
    O = C.table(C.Obj("ground", 0.0), C.Obj("door", 0.5, grip=2.0), C.Obj("coat", 1.0),
                C.Obj("rod", 0.2, grip=-8.0), C.Obj("stop", 0.0), C.FLAG)
    scene = C.n(O, "anchoring", "ground",
                C.n(O, "locking", "door", C.n(O, "resting", "coat"),
                    C.n(O, "connecting", "rod", C.poc.Node("pushing", [], "stop", amount=-10.0))),
                C.n(O, "hanging", "flag"))
    return ScenicWorld(scene, O, gusts=[], episode=None, name="cupboard")


LEXICON["two_scenes"]["nouns"]["rod"] = ("a brass bolt", "the bolt")
LEXICON["two_scenes"]["conditions"][("door", "rod", "parting")] = ("{C} had kept {N} shut", "narrating|describing|claiming")


def lock_scene():
    """A shed door, locked: Gerundelle's lock world (S3-W03) without its episodes. The right key sits in the lock
    (a hard push on it unseats the lock, or seats it again); a wrong key rests beside it and moves under any
    push, to no effect; the door, unlocked and pushed, opens."""
    w = C.lock_world(episode=None)
    return w


def lamp_scene():
    """An old lamp on a workbench: Gerundelle's AND world (S2-W03). Two plugs in series, both loose; a press on
    the button lights the lamp only when both are seated (each by a hard push)."""
    return C.and_world(episode=None)


SLOTS = {"causes": "what {N} did", "role": "what {N} had to do with it", "co_occurs": "what came with {N}"}

LEXICON["shed"] = {
    "frame": "There was an old shed at the end of the garden.",
    "nouns": {"door": ("its door", "the door"), "lock": ("a rusty lock", "the lock"), "key": ("a key in the lock", "the key"),
              "wrong_key": ("a second key", "the second key"), "flag": ("a flag on the roof", "the flag")},
    "states": {"locking": "was locked", "connecting": "kept it shut", "transmitting": "sat in the lock",
               "resting": "lay on the bench", "hanging": "hung still"},
    "flips": {("locking", "releasing"): "swung open", ("connecting", "parting"): "clicked open",
              ("parting", "connecting"): "clicked shut", ("resting", "sliding"): "slid along the bench",
              ("hanging", "swinging"): "swung", ("swinging", "hanging"): "hung still again"},
    "skip": {("releasing", "launching"), ("launching", "resting"), ("sliding", "resting")},
    "push": {"light": "pressed {N}", "hard": "pushed {N} hard"},
    "want": {"door_releasing": "wanted to open the shed"},
    "slots": dict(SLOTS, conditions="what kept {N} from opening"),
    "conditions": {("door", "lock", "parting"): ("{C} had kept {N} shut", "narrating|describing|claiming")},
    "waits": {},
    "asks": {("door", "conditions"): "What keeps the door shut?"},
    "says": {("door", "lock", "parting"): "The lock holds it shut"},
}

LEXICON["lamp"] = {
    "frame": "There was an old lamp on the workbench.",
    "nouns": {"lamp": ("the lamp", "the lamp"), "plug_a": ("a plug", "the first plug"),
              "plug_b": ("a second plug", "the second plug"), "button": ("a brass button", "the button"),
              "flag": ("a paper flag by the window", "the flag")},
    "states": {"containing": "was dark", "parting": "hung loose", "sealing": "stood on its side", "hanging": "hung still"},
    "flips": {("parting", "connecting"): "clicked into place", ("connecting", "parting"): "came loose",
              ("sealing", "opening"): "went down", ("opening", "sealing"): "sprang back",
              ("containing", "filling"): "lit up", ("filling", "containing"): "went dark",
              ("hanging", "swinging"): "swung", ("swinging", "hanging"): "hung still again"},
    "skip": {("", "containing")},
    "push": {"light": "pressed {N}", "hard": "pushed {N} hard"},
    "push_obj": {("hard", "plug_a"): "pushed {N} in hard", ("hard", "plug_b"): "pushed {N} in hard"},
    "want": {"lamp_filling": "wanted to light the lamp"},
    "slots": dict(SLOTS, conditions="what kept {N} from working"),
    "conditions": {("button", "plug_a", "connecting"): ("{C} had to be in place", "narrating|describing"),
                   ("button", "plug_b", "connecting"): ("{C} had to be in place", "narrating|describing")},
    "waits": {},
    "asks": {("button", "conditions"): "What keeps the lamp dark?"},
    "says": {},
}


# ---- corpus run 2: more of Gerundelle's curriculum, as scenes (each with its own lexicon below) ---------------

def boulder_scene():
    """A boulder no push can move (grip 8), resting on a long plank over a log (lever_world, ratio 6): a light
    push on the plank lifts six and launches it; a hard one overshoots."""
    return C.lever_world(episode=None)


def cannon_scene():
    """A toy cannon: a clamp holds a spring wound tight with a ball on it (spring_world); a hard push frees it."""
    return C.spring_world(episode=None)


def catapult_scene():
    """A catapult in the yard: a catch holds a loaded arm with a stone in its cup (weight_world)."""
    return C.weight_world()


def doorbell_scene():
    """A doorbell that rings only while its wire is in (button_world, the wire pulled out): a hidden enabler."""
    return C.button_world(connected=False, episode=None)


def chime_scene():
    """A chime held quiet by a felt damper (chime_world): struck while the damper holds, it does not ring."""
    return C.chime_world(episode=None)


def domino_scene():
    """A chain on a shelf (marble_world): a prop holds a marble; tip the prop and the marble rolls into a ruler,
    the ruler knocks a card, the card a bead."""
    return C.marble_world(episode=None)



def chest_scene():
    """The box's force structure dressed as a chest: a hasp keeps the lid shut over a spring and a puppet."""
    return C.catch_world(names=("top", "puppet", "hasp", "stop"), episode=None)   # its own id: not the box's lid


def tin_scene():
    """The box's force structure dressed as an old tin: a wire clip keeps its cap shut over a paper cricket."""
    return C.catch_world(names=("cap", "cricket", "clip", "stop"), episode=None)


def lexicon(frame, nouns, states, flips, want, conditions=None, skip=(), push=None, push_obj=None, **extra):
    """A scene's lexicon from its parts (the defaults every scene shares: the slots' questions, pushes)."""
    return dict(frame=frame, nouns=nouns, states=states, flips=flips, skip=set(skip), want=want,
                push=push or {"light": "pressed {N}", "hard": "pushed {N} hard"}, push_obj=push_obj or {},
                slots=dict(SLOTS, conditions="what kept {N} from working"), conditions=conditions or {},
                waits={}, asks={}, says={}, **extra)


FLAG_FLIPS = {("hanging", "swinging"): "swung", ("swinging", "hanging"): "hung still again"}
REALIZE = "narrating|describing|claiming"

LEXICON.update({
    "boulder": lexicon(
        "A boulder lay across the garden path.",
        {"stone": ("the boulder", "the boulder"), "lever": ("a long plank under it", "the plank"),
         "flag": ("a kite in the hedge", "the kite")},
        {"resting": "sat in the middle of the path", "levering": "lay across a log", "hanging": "hung still"},
        {("resting", "flying"): "flew off the path", ("flying", "falling"): "fell", ("falling", "piling"): "landed in the grass",
         **FLAG_FLIPS},
        {"stone_flying": "wanted to move the boulder off the path"},
        push_obj={("light", "lever"): "stepped lightly on {N}", ("hard", "lever"): "stamped on {N}"}),
    "cannon": lexicon(
        "There was a toy cannon on the rug.",
        {"clamp": ("its clamp", "the clamp"), "spring": ("a spring inside it", "the spring"),
         "ball": ("a wooden ball", "the ball"), "flag": ("a paper flag on its barrel", "the flag")},
        {"locking": "was shut tight", "compressing": "was wound tight", "resting": "sat in the barrel", "hanging": "hung still"},
        {("locking", "releasing"): "sprang open", ("resting", "sliding"): "slid across the rug",
         ("compressing", "releasing"): "uncoiled", ("resting", "flying"): "shot out", ("flying", "falling"): "fell",
         ("falling", "piling"): "rolled across the floor", **FLAG_FLIPS},
        {"ball_flying": "wanted to fire the cannon"},
        skip={("releasing", "launching"), ("launching", "resting"), ("sliding", "resting")}),
    "catapult": lexicon(
        "There was an old catapult in the yard.",
        {"catch": ("a wooden catch", "the catch"), "weight": ("a heavy arm", "the arm"),
         "stone": ("a stone in its cup", "the stone"), "flag": ("a flag on the fence", "the flag")},
        {"locking": "held the arm down", "loading": "was pulled back", "resting": "sat in its cup", "hanging": "hung still"},
        {("locking", "releasing"): "snapped free", ("resting", "sliding"): "slid along the beam",
         ("loading", "releasing"): "swung up", ("resting", "flying"): "flew over the fence", ("flying", "falling"): "fell",
         ("falling", "piling"): "landed in the field", **FLAG_FLIPS},
        {"stone_flying": "wanted to fire the catapult"},
        skip={("releasing", "launching"), ("launching", "resting"), ("sliding", "resting")}),
    "doorbell": lexicon(
        "There was an old doorbell by the front door.",
        {"lamp": ("the bell", "the bell"), "cable": ("its wire", "the wire"), "button": ("a brass button", "the button"),
         "flag": ("a wind chime by the door", "the wind chime")},
        {"containing": "was silent", "parting": "hung loose", "sealing": "stood out", "hanging": "hung still"},
        {("parting", "connecting"): "clicked into place", ("connecting", "parting"): "came loose",
         ("sealing", "opening"): "went down", ("opening", "sealing"): "sprang back", ("containing", "filling"): "rang",
         ("filling", "containing"): "fell silent", **FLAG_FLIPS},
        {"lamp_filling": "wanted to ring the bell"},
        conditions={("button", "cable", "connecting"): ("{C} had to be in place", "narrating|describing")},
        skip={("", "containing")}),
    "chime": lexicon(
        "A chime hung in the hallway.",
        {"chime": ("the chime", "the chime"), "striker": ("a little hammer", "the hammer"),
         "damper": ("a felt damper", "the damper"), "flag": ("a paper flag by the window", "the flag")},
        {"hanging": "hung quiet", "transmitting": "rested against it", "connecting": "held it still"},
        {("hanging", "swinging"): "rang out", ("swinging", "hanging"): "went quiet", ("connecting", "parting"): "came away"},
        {"chime_swinging": "wanted to ring the chime"},
        flips_obj={("flag", "hanging", "swinging"): "fluttered", ("flag", "swinging", "hanging"): "hung still again"},
        conditions={("chime", "damper", "parting"): ("{C} had kept {N} still", REALIZE),
                    ("striker", "damper", "parting"): ("{C} had kept the chime still", REALIZE)}),
    "domino": lexicon(
        "There was a row of odd things on the shelf.",
        {"prop": ("a wooden wedge", "the wedge"), "marble": ("a marble", "the marble"), "lever": ("a ruler", "the ruler"),
         "gate": ("a playing card", "the card"), "bead": ("a glass bead", "the bead"), "flag": ("a paper flag", "the flag")},
        {"supporting": "held up a marble", "resting": "sat on the wedge", "leaning": "stood on its edge"},
        {("supporting", "tipping"): "tipped over", ("resting", "tipping"): "tipped over", ("resting", "falling"): "rolled off",
         ("leaning", "falling"): "toppled", ("leaning", "sliding"): "slid", ("resting", "sliding"): "slid",
         ("falling", "piling"): "landed on the floor"},
        {"bead_falling": "wanted to knock the bead off the shelf"},
        skip={("tipping", "resting"), ("sliding", "resting")}),
    "chest": dict(LEXICON["jack_in_the_box"], frame="There was a wooden chest under the window.",
                  nouns={"top": ("its lid", "the lid"), "hasp": ("a brass hasp", "the hasp"), "puppet": ("a puppet", "the puppet"),
                         "spring": ("a spring inside it", "the spring"), "flag": ("a curtain at the window", "the curtain")},
                  want={"top_releasing": "wanted to open the chest"},
                  conditions={("top", "hasp", "parting"): ("{C} had kept {N} shut", REALIZE)}),
    "tin": dict(LEXICON["jack_in_the_box"], frame="There was an old tin on the shelf.",
                nouns={"cap": ("its cap", "the cap"), "clip": ("a wire clip", "the clip"), "cricket": ("a paper cricket", "the cricket"),
                       "spring": ("a spring inside it", "the spring"), "flag": ("a ribbon on the shelf", "the ribbon")},
                want={"cap_releasing": "wanted to open the tin"},
                conditions={("cap", "clip", "parting"): ("{C} had kept {N} shut", REALIZE)}),
})



def carried(world, obj):
    """What the object holds or carries in the scene (its node's subtree in the force tree: what rests on a plank,
    what a lid shuts in): perceivable contact, so a change there in the slice of a push on obj is the push's own
    (first a push's chain began with the object pushed alone, and a plank that passes its force on without
    changing was read as doing nothing while the boulder on it flew)."""
    out = set()

    def walk(n, inside):
        if inside and n.doer:
            out.add(n.doer)
        for k in n.kids:
            walk(k, inside or n.doer == obj)
    walk(world.tree, False)
    return out - {obj}


import variants  # noqa: E402  (other ways to say each phrase, every scene: taken in turn per story)
variants.apply(LEXICON)



# ---- dressings: the same physics, other objects and words (corpus run 3) --------------------------------------

def dressed(base, names):
    """A scene factory: a curriculum world with its objects renamed (Gerundelle's `renamed`)."""
    return lambda: C.renamed(base(), names)


music_box_scene = dressed(lambda: C.catch_world(episode=None), {"toy": "dancer", "latch": "clasp"})
gate_scene = dressed(lambda: C.lock_world(episode=None), {"door": "gate", "lock": "padlock", "wrong_key": "spare_key"})
diary_scene = dressed(lambda: C.lock_world(episode=None), {"door": "cover", "lock": "clasp", "wrong_key": "hairpin"})
log_scene = dressed(lambda: C.lever_world(episode=None), {"stone": "log", "lever": "branch"})
pinball_scene = dressed(lambda: C.spring_world(episode=None), {"clamp": "trigger", "ball": "marble"})
radio_scene = dressed(lambda: C.button_world(connected=False, episode=None), {"lamp": "radio", "cable": "plug",
                                                                             "button": "switch"})
bike_bell_scene = dressed(lambda: C.chime_world(episode=None), {"chime": "bell", "striker": "thumb", "damper": "band"})


def dress(base, **over):
    """A lexicon from another's, its parts replaced (the base's changes and pushes kept)."""
    lex = {k: (dict(v) if isinstance(v, dict) else v) for k, v in LEXICON[base].items()}
    for k, v in over.items():
        lex[k] = {**lex.get(k, {}), **v} if isinstance(v, dict) and k in ("flips", "flips_obj", "states") else v
    return lex


LEXICON.update({
    "music_box": dress("jack_in_the_box", frame="There was a music box on the dresser.",
                       nouns={"lid": ("its lid", "the lid"), "clasp": ("a silver clasp", "the clasp"),
                              "dancer": ("a tiny dancer", "the dancer"), "spring": ("a spring inside it", "the spring"),
                              "flag": ("a curtain at the window", "the curtain")},
                       flips_obj={("dancer", "resting", "flying"): "sprang up", ("dancer", "flying", "falling"): "tumbled",
                                  ("dancer", "falling", "piling"): "landed on the dresser"},
                       want={"lid_releasing": "wanted to open the music box"},
                       conditions={("lid", "clasp", "parting"): ("{C} had kept {N} shut", REALIZE)}),
    "gate": dress("shed", frame="There was a garden gate at the end of the lane.",
                  nouns={"gate": ("the gate", "the gate"), "padlock": ("a rusty padlock", "the padlock"),
                         "key": ("a key in the padlock", "the key"), "spare_key": ("a spare key", "the spare key"),
                         "flag": ("a scarf on the fence", "the scarf")},
                  states={"resting": "lay on the wall", "transmitting": "sat in the padlock"},
                  flips_obj={("spare_key", "resting", "sliding"): "slid along the wall"},
                  want={"gate_releasing": "wanted to open the gate"},
                  conditions={("gate", "padlock", "parting"): ("{C} had kept {N} shut", REALIZE)},
                  asks={}, says={}),
    "diary": dress("shed", frame="There was an old diary on the desk.",
                   nouns={"cover": ("its cover", "the cover"), "clasp": ("a brass clasp", "the clasp"),
                          "key": ("a tiny key in the clasp", "the key"), "hairpin": ("a hairpin", "the hairpin"),
                          "flag": ("a bookmark ribbon", "the ribbon")},
                   states={"resting": "lay beside it", "transmitting": "sat in the clasp"},
                   flips_obj={("cover", "locking", "releasing"): "fell open",
                              ("hairpin", "resting", "sliding"): "slid across the desk"},
                   want={"cover_releasing": "wanted to open the diary"},
                   conditions={("cover", "clasp", "parting"): ("{C} had kept {N} shut", REALIZE)},
                   asks={}, says={}),
    "log": dress("boulder", frame="A log blocked the stream.",
                 nouns={"log": ("the log", "the log"), "branch": ("a branch under it", "the branch"),
                        "flag": ("a reed by the bank", "the reed")},
                 states={"resting": "lay across the water", "levering": "lay across a rock"},
                 flips={("resting", "flying"): "flew out of the water", ("falling", "piling"): "landed on the bank"},
                 push_obj={("light", "branch"): "stepped lightly on {N}", ("hard", "branch"): "stamped on {N}"},
                 want={"log_flying": "wanted to clear the log from the stream"}),
    "pinball": dress("cannon", frame="There was an old pinball machine in the hall.",
                     nouns={"trigger": ("its trigger", "the trigger"), "spring": ("a spring behind it", "the spring"),
                            "marble": ("a steel ball", "the ball"), "flag": ("a little flag on top", "the flag")},
                     states={"locking": "was cocked", "resting": "sat in the chute"},
                     flips={("locking", "releasing"): "snapped forward", ("resting", "flying"): "shot up the table",
                            ("falling", "piling"): "rolled into a hole", ("resting", "sliding"): "slid"},
                     want={"marble_flying": "wanted to launch the ball"}),
    "radio": dress("doorbell", frame="There was an old radio on the shelf.",
                   nouns={"radio": ("the radio", "the radio"), "plug": ("its plug", "the plug"),
                          "switch": ("a round switch", "the switch"), "flag": ("a paper fan", "the fan")},
                   flips={("parting", "connecting"): "slid into the socket", ("sealing", "opening"): "clicked down",
                          ("opening", "sealing"): "clicked back", ("containing", "filling"): "began to play",
                          ("filling", "containing"): "fell quiet"},
                   want={"radio_filling": "wanted to play the radio"},
                   conditions={("switch", "plug", "connecting"): ("{C} had to be in place", "narrating|describing")}),
    "bike_bell": dress("chime", frame="There was a bicycle against the wall.",
                       nouns={"bell": ("its bell", "the bell"), "thumb": ("a thumb lever", "the lever"),
                              "band": ("a rubber band", "the band"), "flag": ("a streamer on the handlebar", "the streamer")},
                       states={"hanging": "was quiet"},
                       flips={("hanging", "swinging"): "rang", ("connecting", "parting"): "snapped off"},
                       want={"bell_swinging": "wanted to ring the bell"},
                       conditions={("bell", "band", "parting"): ("{C} had kept {N} quiet", REALIZE),
                                   ("thumb", "band", "parting"): ("{C} had kept the bell quiet", REALIZE)}),
})
variants.apply({k: LEXICON[k] for k in ("music_box", "gate", "diary", "log", "pinball", "radio", "bike_bell")})
