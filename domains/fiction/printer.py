"""The construction printer: a scene's plans -> sentences, each with the gerund shape it must realize.

T155's language center, first cut: clause-scale constructions indexed by structure, slots filled from
the scene's lexicon and the plan. Deterministic, no model. A construction states its intended gerund
shape (the gerunds and their nesting, leaf roles left to the words: "sprang open" reads as an
attribute, "gave way" as a patient), with alternatives where the reader is ambiguous by design
("was shut tight" reads as describing or narrating). measure.py reads every sentence back with the
determination system: the construction is right only if a reading has the intended shape, and that
reading becomes the sentence's label.
"""
import itertools
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEXT_DIR = os.environ.get("ANALOGY_TEXT", os.path.join(REPO, "reference", "text"))
sys.path.insert(0, TEXT_DIR)
from clip import parse  # noqa: E402

ND = "narrating|describing"
POSSESSIVE = {"she": "her", "he": "his", "they": "their"}
# a phase said, with no anchor and with one (the object its region is): (construction, gerund)
FEELINGS = {"joy": (("laughed with joy", "was delighted with {N}"), "expressing_joy"),
            "frustration": (("frowned in frustration", "grew frustrated with {N}"), "expressing_exasperation"),
            "curiosity": (("was curious", "was curious about {N}"), "expressing_curiosity"),
            "wonder": (("marveled", "marveled at {N}"), "expressing_wonder"),
            "anxiety": (("grew anxious", "felt anxious about {N}"), "expressing_fear"),
            "anger": (("grew angry", "grew angry with {N}"), "expressing_anger"),
            "resignation": (("gave up, resigned", "gave up, resigned"), "expressing_resignation"),
            "forgiveness": (("forgave", "forgave {N}"), "expressing_forgiveness"),
            "gratitude": (("was grateful", "thanked {N}"), "expressing_gratitude"),
            "sadness": (("felt sad", "felt sad about {N}"), "expressing_sorrow"),
            "weariness": (("grew tired", "grew tired of {N}"), "narrating")}   # no fatigue gerund: an event
COUNTS = {1: "Once more", 2: "Twice more", 3: "Three more times"}


def shape_of(skel):
    """A reading's gerund shape: gerund nodes and the roles that hold gerunds, leaf slots dropped."""
    def walk(tree):
        kind, kids = tree
        inner = [f"{r}={walk(k)}" for r, k in kids if not k[0].startswith("slot:")]
        return f"{kind}({', '.join(inner)})" if inner else kind
    return walk(parse(skel))


def alternatives(shape):
    """Every shape a construction allows. At the top level '|' separates whole shapes ('narrating|
    elaborating(main=narrating, detail=narrating)'); inside parentheses it separates single gerunds
    ('explaining(cause=narrating|describing, effect=narrating)')."""
    tops, depth, cur = [], 0, ""
    for ch in shape:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "|" and depth == 0:
            tops.append(cur)
            cur = ""
        else:
            cur += ch
    tops.append(cur)
    out = set()
    for top in tops:
        parts = re.split(r"([a-z_]+(?:\|[a-z_]+)+)", top)
        opts = [p.split("|") if "|" in p else [p] for p in parts]
        out |= {"".join(c) for c in itertools.product(*opts)}
    return out


class Printer:
    def __init__(self, lexicon, actor, pronoun="she", seed=0):
        """seed: where this story starts each rotation of phrasings (stories in one world open differently)."""
        self.lex, self.actor, self.pronoun, self.seed = lexicon, actor, pronoun, seed
        self.mentioned = set()
        self.last_subject = None
        self.turns = {}   # phrasing rotations (key -> times used)

    def noun(self, obj, cap=False, definite=False):
        """definite: the later form even at a first mention (a feeling's object: "delighted with the clasp")."""
        first, later = self.lex["nouns"].get(obj, (f"the {obj}", f"the {obj}"))
        np = later if obj in self.mentioned or definite else first
        self.mentioned.add(obj)
        return np[0].upper() + np[1:] if cap else np

    def agent(self, cap=True):
        """The actor's name, or the pronoun when the last sentence was already about them."""
        a = self.pronoun if self.last_subject == self.actor else self.actor
        self.last_subject = self.actor
        return a[0].upper() + a[1:] if cap else a

    def subject(self, obj):
        self.last_subject = obj
        return self.noun(obj, cap=True)

    def render(self, plan):
        """[(text, intended shape)] for one plan (a frame plan may be several sentences)."""
        f, lex, k = plan.fill, self.lex, plan.kind
        if k == "frame":
            out = [(self.pick(lex["frame"], "frame"), ND)]
            for who in f.get("people", ()):   # an appositive ("Her grandfather Ben") picks out who: disambiguating
                out.append((lex["people"][who], f"{ND}|disambiguating(main={ND})"))
            for who in f.get("rivals", ()):   # a rival's want, which the reader holds from the start
                out.append((lex["rival_wants"][who], f"{ND}|narrating(content={ND})"))
            for obj in f["objs"]:
                state = self.state(obj, f["states"][obj])
                if state:
                    out.append((f"{self.subject(obj)} {state}.", ND))
            return out
        if k == "want":
            said = self.pick(lex["want"][f["change"]], "want")
            shape = ("explaining(means=expressing_longing|narrating, purpose=describing)" if said.startswith("longed")
                     else "explaining(means=narrating, purpose=describing)" if said.startswith("set out")
                     else "narrating")   # how the reader reads each way of wanting
            return [(f"{self.agent()} {said}.", shape)]
        if k == "wonder":
            q = lex["slots"][f["slot"]].format(N=self.noun(f["obj"]))
            return [(f"{self.agent()} wondered {q}.", f"expressing_curiosity(content={ND})")]
        if k == "scene":   # a new scene's frame
            out = [(self.pick(lex["frames"][f["world"]], "frame"), ND)]
            for obj in f["objs"]:
                state = self.state(obj, f["states"][obj])
                if state:
                    out.append((f"{self.subject(obj)} {state}.", ND))
            return out
        if k == "summary":   # the helper's way, not shown
            self.last_subject = f["who"]
            return [(f"{f['who']} opened it for her.", "narrating")]
        if k == "recall":   # the payoff: an episode found again by its shape
            who = f.get("watched")
            thing = lex.get("opened", "the box")   # what the remembered episode was about
            what = f"how {who} had opened {thing}" if who else thing
            return [(f"{self.agent()} remembered {what}.", "realizing(content=narrating)|narrating|realizing")]
        if k == "time":   # a scene break, said by how long
            n = f["ticks"]
            text = "A few days passed." if n <= 20 else "Weeks passed." if n <= 60 else "Months passed."
            return [(text, "grounding|narrating")]
        if k == "try" and f.get("who", self.actor) != self.actor:   # another mind's push
            push = lex.get("push_obj", {}).get((f["strength"], f["obj"]), lex["push"].get(f["strength"], ""))
            push = push.format(N=self.noun(f["obj"]))
            self.last_subject = f["who"]
            return [(f"{f['who']} {push}.", "narrating|narrating(first=narrating, then=narrating)|"
                                             "elaborating(main=narrating, detail=narrating)")]
        if k == "try":
            push = lex.get("push_obj", {}).get((f["strength"], f["obj"]), lex["push"][f["strength"]])
            push = push.format(N=self.noun(f["obj"]))
            if f["again"]:
                return [(f"Then {self.agent(cap=False)} {push} again.", "narrating(then=narrating)")]
            if f.get("at_last"):   # the push that turns the scene, after a run of failures
                return [(f"At last {self.agent(cap=False)} {push}.", "narrating")]
            return [(f"{self.agent()} {push}.", "narrating")]
        if k == "nothing":
            s = self.subject(f["obj"])
            if f.get("contrast"):   # a belief the world contradicted ("this time": against its own past; a
                when = "" if f.get("told") else "this time "   # told way has no past, only the telling)
                return [(f"But {when}{s[0].lower() + s[1:]} did not move.", "contrasting(main=narrating)")]
            return [(f"{s} did not move.", "narrating")]
        if k == "ask":   # Pose across minds: the hole's open slot, said as a question to someone
            q = lex["asks"][(f["obj"], f["slot"])]
            self.last_subject = self.actor
            return [(f'"{q}" {self.actor} asked {f["to"]}.', f"asking(content={ND})")]
        if k == "tell" and f.get("way"):   # a way offered (true or not, the sentence is the same)
            said = lex["instructs"][tuple(f["way"][:2])]
            self.last_subject = f["who"]
            return [(f'"{said}," {f["who"]} said.', "telling(content=instructing)")]
        if k == "reveal":   # the narrator says what the teller holds: the reader's ledger, not the character's
            truth = lex["truths"][(f["obj"], f["cond_obj"], f["cond_state"])]
            self.last_subject = f["who"]
            return [(f"But {f['who']} knew that {truth}.", f"contrasting(main={ND}(content={ND}|claiming))")]
        if k == "tell":   # Attest: the teller's own receipt, said
            said = lex["says"].get((f["obj"], f["cond_obj"], f["cond_state"]))
            shape = f"telling(content={ND}|instructing)"
            if said is None:   # no receipt: ignorance said with its shape, the posed question as its content
                q = lex["asks"][(f["obj"], "conditions")]
                said = "I don't know " + q[0].lower() + q[1:].rstrip("?")
                shape = f"telling(content=describing(content={ND}))"
            self.last_subject = f["who"]
            return [(f'"{said}," {f["who"]} said.', shape)]
        if k == "attempt":   # a push and what it did, one sentence
            t, r = f["try"], f["result"]
            who = t.get("who", self.actor)
            a = self.agent() if who == self.actor else who
            self.last_subject = who
            push = self.push_phrase(t["strength"], t["obj"])
            again = " again" if t.get("again") else ""
            if f["outcome"] == "nothing":
                tail = self.rotate("nothing", ["it did not move", "it would not move", "it did not budge",
                                                "nothing happened"])
                return [(f"{a} {push}{again}, but {tail}.", "contrasting(main=narrating, other=narrating)")]
            verbs = [self.verb(t["obj"], fl) for fl in r["flips"] if self.verb(t["obj"], fl)]
            verbs = [v for i, v in enumerate(verbs) if not i or v != verbs[i - 1]]   # "swung and swung": once
            if not verbs:
                return [(f"{a} {push}{again}.", "narrating")]
            if len(verbs) > 2:   # the first move and where it ended (its next move, if it ended as it began)
                verbs = [verbs[0], verbs[-1]] if verbs[-1] != verbs[0] else verbs[:2]
            if len(verbs) == 1:
                return [(f"{a} {push}{again}, and it {verbs[0]}.",
                         "elaborating(main=narrating, detail=narrating)|narrating(first=narrating, then=narrating)")]
            pair = ("elaborating(main=narrating, detail=narrating)", "narrating(first=narrating, then=narrating)")
            shapes = [f"{outer}{inner})" for outer in ("elaborating(main=narrating, detail=",
                                                       "narrating(first=narrating, then=") for inner in pair]
            return [(f"{a} {push}{again}, and it {verbs[0]} and {verbs[1]}.", "|".join(shapes))]
        if k == "explore":   # varied exploration, summarized
            names = [self.noun(o) for o in f["objs"]]
            what = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
            tail = "nothing came of it" if f["moved"] else "nothing gave"
            lead = self.rotate("explore", ["Again and again {a} tried {w}", "{A} kept trying {w}"])
            a = self.agent(cap=False)
            text = lead.format(a=a, A=a[0].upper() + a[1:], w=what)
            return [(f"{text[0].upper() + text[1:]}, but {tail}.", "contrasting(main=iterating|narrating, other=narrating)")]
        if k in ("leave", "return", "rise", "lost"):   # rung 7: comings and goings, and a kept state found undone
            text, shape = lex["events"][k]
            self.last_subject = f["who"]
            return [(text.format(W=f["who"]), shape)]
        if k == "believe":   # a worked-out belief, held as the mind's own claim
            push = POSSESSIVE.get(self.pronoun, "their")
            text = f"{self.agent()} thought {push} push had moved {self.noun(f['obj'])}."
            self.last_subject = self.actor
            return [(text, "claiming(content=narrating)")]
        single = k == "iterate" and len([p for p in f["window"] if p.kind == "try"]) == 1
        if single and not any(p.kind == "wait" for p in f["window"]):   # one push, again and again
            t = next(p for p in f["window"] if p.kind == "try")
            push = lex.get("push_obj", {}).get((t.fill["strength"], t.fill["obj"]), lex["push"][t.fill["strength"]])
            push = push.format(N=self.noun(t.fill["obj"]))
            moved = [p for p in f["window"] if p.kind == "change"]
            verbs = [self.verb(p.fill["obj"], fl) for p in moved for fl in p.fill["flips"]
                     if self.verb(p.fill["obj"], fl)]
            when = COUNTS.get(f["count"], str(f["count"]) + " more times")
            each = "once more" if f["count"] == 1 else "each time"
            a = self.agent(cap=False)
            text = f"{when} {a} {push}, and {each} it {verbs[0]}." if verbs else f"{when} {a} {push}."
            return [(text, "elaborating(main=iterating, detail=iterating)|narrating(first=iterating, then=iterating)|iterating")]
        if k == "iterate" and not any(p.kind == "wait" for p in f["window"]):   # a tug of war, repeated
            tries = [p for p in f["window"] if p.kind == "try"]
            a, b = tries[0], tries[-1]
            who_a = self.actor if a.fill.get("who", self.actor) == self.actor else a.fill["who"]
            push = lex["push"][a.fill["strength"]].format(N=self.noun(a.fill["obj"]))
            when = COUNTS.get(f["count"], str(f["count"]) + " more times")
            each = "once more" if f["count"] == 1 else "each time"
            text = f"{when} {who_a} {push}, and {each} {b.fill['who']} pushed it back."
            self.last_subject = b.fill["who"]
            return [(text, "elaborating(main=iterating, detail=iterating)|narrating(first=iterating, then=iterating)")]
        if k == "iterate":   # a cycle repeated: told once in full, then summarized (no gerund for it)
            wait = next(p for p in f["window"] if p.kind == "wait")
            moved = [p for p in f["window"] if p.kind == "change" and p.fill["obj"] == f["obj"]]
            verb = self.verb(moved[0].fill["obj"], moved[0].fill["flips"][0])
            a = self.agent(cap=False)
            text = (f"{COUNTS.get(f['count'], str(f['count']) + ' more times')} {a} waited "
                    f"{lex['waits'][wait.fill['condition']]}, and {'once more' if f['count'] == 1 else 'each time'} "
                    f"{self.noun(f['obj'])} {verb}.")
            return [(text, "elaborating(main=narrating(first=iterating, then=narrating), detail=iterating)|"
                           "narrating(first=narrating(first=iterating, then=narrating), then=iterating)")]
        if k == "wait":
            return [(f"{self.agent()} waited {lex['waits'][f['condition']]}.", "narrating(first=narrating, then=narrating)")]
        if k == "change":
            verbs = [self.verb(f["obj"], fl) for fl in f["flips"] if self.verb(f["obj"], fl)]
            verbs = [v for i, v in enumerate(verbs) if not i or v != verbs[i - 1]]
            if not verbs:
                return []
            if len(verbs) > 2:   # the first move and where it ended (its next move, if it ended as it began)
                verbs = [verbs[0], verbs[-1]] if verbs[-1] != verbs[0] else verbs[:2]
            s = self.subject(f["obj"])
            if f.get("contrast") and len(verbs) == 1:   # the world's testimony against the prediction
                return [(f"But this time {s[0].lower() + s[1:]} {verbs[0]}.", "contrasting(main=narrating)")]
            if len(verbs) == 1:
                return [(f"{s} {verbs[0]}.", "narrating")]
            return [(f"{s} {verbs[0]} and {verbs[1]}.", "narrating(first=narrating, then=narrating)|"
                                                         "elaborating(main=narrating, detail=narrating)")]
        if k == "learn":
            a = self.agent()   # the aha: a hole closing in a mind (realizing, a fiction-grammar gerund)
            if f.get("confirms"):   # what was told, now lived
                return [(f"{a} realized that {f['confirms']} had been right.", f"realizing(content={ND})")]
            out = []
            if f.get("exposes"):   # the lie, found out
                key = (f["obj"], f["cond_obj"], f["cond_state"])
                template, shape = self.condition(key)
                text = template.format(N=self.noun(f["obj"]), C=self.noun(f["cond_obj"]))
                return [(f"{a} realized that {text}.", f"realizing(content={shape})"),
                        (f"{self.agent()} realized that {f['exposes']} had lied.", f"realizing(content={ND})")]
            key = (f["obj"], f["cond_obj"], f["cond_state"])
            template, shape = self.condition(key)
            conds = self.noun(f["cond_obj"])
            for o in f.get("also", ()):   # an AND: its conditions joined ("the first plug and the second plug")
                conds += " and " + self.noun(o)
            text = template.format(N=self.noun(f["obj"]), C=conds)
            return [(f"{a} realized that {text}.", f"realizing(content={shape})")]
        if k == "feel" and f["phase"] == "fading":   # a grief stored open: no longer thought of, not resolved
            return [(f"In time, {self.agent(cap=False)} stopped thinking about {self.noun(f['anchor'])}.", "narrating")]
        if k == "feel" and f.get("reopened") and f["phase"] == "sadness":   # a grief reopened by resonance
            a = self.agent()
            pos = POSSESSIVE.get(self.pronoun, "their")
            return [(f"{a} remembered how {self.pronoun} had played with {self.noun(f['anchor'])}.",
                     "realizing(content=narrating)")]
        if k == "feel" and f["phase"] == "sadness" and f.get("pull", 0) >= 5:   # grief scales with what was held
            return [(f"{self.agent()} was heartbroken.", "expressing_sorrow")]
        if k == "feel":
            out = []
            news = [u.split("_", 1)[0] for u in f["unexpected"] if u.split("_", 1)[0] in lex["nouns"]]
            if f["phase"] == "joy" and news:   # the effect it never expected: wonder at it first
                (_, text), g = FEELINGS["wonder"]
                obj = news[-1]   # the one whose change came last: where the surprise ended up
                out.append((f"{self.agent()} {text.format(N=self.noun(obj))}.", g))
            if f["phase"] not in FEELINGS:
                return out
            (bare, anchored), g = FEELINGS[f["phase"]]
            about = f["anchor"] if f.get("person") else (self.noun(f["anchor"], definite=True) if f.get("anchor") else "")
            if about == self.actor and f.get("who", self.actor) != self.actor:
                about = self.actor   # another's phase about the character: by name
            text = anchored.format(N=about) if about else bare
            if f.get("reopened"):   # the same phase, reopened
                text += " again"
            if f.get("who", self.actor) != self.actor:   # another mind's phase
                self.last_subject = f["who"]
                out.append((f"{f['who']} {text}.", g))
            else:
                out.append((f"{self.agent()} {text}.", g))
            return out
        raise ValueError(k)

    def condition(self, key):
        """How a learned condition is said: the scene's own words for it, else the general form (any condition a
        mind learns must be sayable, a spurious one too): "{N} moved only if {C} <its verb for reaching that
        state>" (the crate world's form, explaining(condition, effect)), the verb found among the scene's changes."""
        said = self.lex["conditions"].get(key)
        if said:
            return said
        obj, cobj, cstate = key
        verb = next((self.verb(cobj, fl) for fl in list(self.lex["flips"]) + [k[1:] for k in self.lex.get("flips_obj", {})
                                                                            if k[0] == cobj]
                     if fl[1] == cstate and self.verb(cobj, fl)), None)
        if verb is None:
            verb = {"parting": "came loose", "connecting": "was in place", "swinging": "swung"}.get(cstate, f"was {cstate}")
        return "{N} moved only if {C} " + verb, "explaining(condition=narrating|describing, effect=narrating)"

    def verb(self, obj, flip):
        """How an object's change is said: its own verb (`flips_obj`: a chime rings, a flag beside it flutters),
        else the scene's for that change of gerund; None if it is not worth saying (skipped) or has no words."""
        own = self.lex.get("flips_obj", {}).get((obj,) + tuple(flip))
        if own:
            return self.pick(own, ("flip", obj) + tuple(flip))
        if tuple(flip) in self.lex.get("skip", ()):
            return None
        said = self.lex["flips"].get(tuple(flip))
        return self.pick(said, ("flip", obj) + tuple(flip)) if said else None

    def state(self, obj, gerund):
        """How an object's state is said in a frame: its own phrase (`states_obj`), else the scene's."""
        said = self.lex.get("states_obj", {}).get((obj, gerund)) or self.lex["states"].get(gerund)
        return self.pick(said, ("state", obj, gerund)) if said else None

    def pick(self, said, key):
        """A lexicon entry may be one phrasing or several (each admitted only if the reader recovers its shape):
        several are taken in turn, from this story's seed."""
        if isinstance(said, (list, tuple)):
            return self.rotate(key, list(said))
        return said

    def rotate(self, key, options):
        """The next of several phrasings, in turn (each is admitted only if the reader recovers its shape)."""
        n = self.turns.get(key, 0)
        self.turns[key] = n + 1
        return options[(n + self.seed) % len(options)]

    def push_phrase(self, strength, obj):
        """How a push is said: the lexicon's own phrase for the object, else its phrase for the strength, taking
        turns with other phrasings of the same push."""
        lex = self.lex
        fixed = lex.get("push_obj", {}).get((strength, obj))
        if fixed:
            return fixed.format(N=self.noun(obj))
        base = lex["push"][strength]
        alts = {"hard": [base, "gave {N} a hard push", "shoved {N}"], "light": [base, "pressed on {N}"]}.get(strength, [base])
        alts = [base] + [x for x in alts if x != base and not base.startswith("leaned")]   # the wind's crate keeps
        return self.rotate(("push", strength), alts).format(N=self.noun(obj))             # its own verb

    def print_scene(self, scene):
        """[(plan index, text, shape)] for every sentence of the scene, in order."""
        out = []
        for i, plan in enumerate(scene.plans):
            for text, shape in self.render(plan):
                out.append((i, text, shape))
        return out
