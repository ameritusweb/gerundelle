"""Beats -> a scene: what is worth telling, in what order, as a narrative structure of gerund ASTs.

The selection rules are the author's, stated so they can be varied and ablated:
- setup tells what the character perceives and will act on before the climax; what first appears as an
  effect it never expected is withheld until it happens (the reader's ledger gets it when the
  character's does: a surprise shared, not announced);
- a want, a wonder (a hole posed to oneself), a feeling, a learned condition are always told: they
  are the holes opening, turning and closing;
- a try is told with what followed; a try repeating the last with the same outcome is told as "again";
- the changes after a push are told per object (its first flip and where it ended), causes before
  effects, and only for objects that matter: acted on, wanted, or new to the character;
- a change something else made (a gust's) is told only if the character's beliefs used it.

Each plan is one sentence: the beats it tells (history: their refs), its stage in the scene's arc
(setup, tension, turn, resolution), and the gerund shape the printer must realize.
"""
from dataclasses import dataclass, field

from beats import effect_parts


@dataclass
class Plan:
    kind: str                     # the construction family (printer.py)
    stage: str                    # setup | tension | turn | resolution
    fill: dict                    # the construction's slots
    beats: tuple = ()             # indices of the beats told
    refs: tuple = ()              # earlier plans this sentence depends on (from the beats' refs)
    text: str = ""
    shape: str = ""               # the intended gerund shape (printer)
    reading: str = ""             # the reader's skeleton that matched it (measure)


@dataclass
class Scene:
    actor: str
    plans: list = field(default_factory=list)


def tell(beats, objs, actor, people=(), reveal=True, rivals=(), plant="passing"):
    """reveal: when a teller lies, the narrator says what the teller holds (dramatic irony: the reader's
    ledger gets the truth the character's does not); False withholds it (the reader finds out with her)."""
    scene = Scene(actor)
    plan_of = {}   # beat index -> plan index

    def add(kind, stage, fill, told):
        refs = sorted({plan_of[r] for b in told for r in beats[b].refs if r in plan_of})
        # an earning plant shows the affordance (the detail used: pushed, changing) or states the lesson about
        # it; a summary that keeps the mechanism off the page, or a mere mention in a frame, does not
        cond = beats[told[0]].detail.get("condition") if told else None
        about = effect_parts(cond, objs)[0] if kind == "learn" and cond else (beats[told[0]].obj if told else "")
        if told and kind in ("try", "change", "learn") and told[0] < first_scene and about in recalled:
            fill = dict(fill, plant=about)   # the reader's ledger gets the detail here
        scene.plans.append(Plan(kind, stage, fill, tuple(told), tuple(refs)))
        for b in told:
            plan_of[b] = len(scene.plans) - 1

    planted = lambda b, j: False   # set below once the scenes are known
    reach = next((i for i, b in enumerate(beats) if b.kind == "reach"), len(beats))
    acted = {b.obj for b in beats[:reach + 1] if b.kind == "try"}
    wanted = {b.obj for b in beats if b.kind == "want"}
    # objects a learned condition is about: they will matter, so the setup shows them
    conditional = {effect_parts(b.detail["condition"], objs)[0] for b in beats if b.kind == "learn"}
    watching = set()   # condition objects the mind is now watching (after it learned of them)
    # setup: the scene as perceived, for what will be acted on or come to be understood (a second scene has
    # its own frame, at its scene beat)
    first_scene = next((i for i, b in enumerate(beats) if b.kind == "scene"), len(beats))
    acted |= {b.obj for b in beats if b.kind == "try"}
    sees = [i for i, b in enumerate(beats[:first_scene]) if b.kind == "see" and b.obj in acted | wanted | conditional]
    # the plant (rung 6): what a later recall carries over, as it was shown before the scene break
    recalled = {b.detail["from_cond"] for b in beats if b.kind == "recall"}
    if not recalled:   # no payoff: what was shown that could have been one (a lesson learned by watching)
        recalled = {effect_parts(b.detail["condition"], objs)[0] for b in beats[:first_scene]
                    if b.kind == "learn" and b.detail.get("watched")}
    planted = lambda b, j: j < first_scene and b.obj in recalled
    if sees:
        add("frame", "setup", {"objs": [beats[i].obj for i in sees], "states": {beats[i].obj: beats[i].detail["gerund"]
                                                                                 for i in sees},
                               "people": list(people), "rivals": list(rivals)}, sees)
    seen_effects, last_try, stage = set(), None, "tension"
    i = 0
    while i < len(beats):
        b = beats[i]
        if b.kind == "want":
            add("want", "setup", {"obj": b.obj, "change": b.detail["change"]}, [i])
        elif b.kind == "wonder":   # the question that won into action: the next push is on its object
            nxt = next((x for x in beats[i + 1:] if x.kind in ("try", "wonder")), None)
            told = {p.fill.get("obj") for p in scene.plans if p.kind == "wonder"}
            if nxt is not None and nxt.kind == "try" and nxt.obj == b.obj and b.obj not in told:
                add("wonder", stage, {"obj": b.obj, "slot": b.detail["slot"]}, [i])
        elif b.kind == "try" and b.actor != actor and plant == "none" and i < first_scene:
            # the plant not told: the helper's way with the box summarized, its mechanism kept off the page
            j = i + 1
            while j < len(beats) and beats[j].kind == "change" and beats[j].refs == (i,):
                j += 1
            if not any(p.kind == "summary" for p in scene.plans):
                add("summary", stage, {"who": b.actor}, list(range(i, j)))
            i = j
            continue
        elif b.kind == "try":
            j = i + 1
            outcome = []
            while j < len(beats) and beats[j].kind in ("change", "nothing", "surprise", "other") and beats[j].refs == (i,):
                if beats[j].kind != "other":   # something else's doing during the watch: not the push's
                    outcome.append(j)
                j += 1
            again = last_try is not None and last_try == (b.actor, b.obj, b.detail["strength"])   # the same one's
            last_try = (b.actor, b.obj, b.detail["strength"])
            is_reach = any(beats[k].kind == "reach" and beats[k].refs == (i,) for k in range(j, min(j + 3, len(beats))))
            if is_reach:
                stage = "turn"
            add("try", stage, {"obj": b.obj, "strength": b.detail["strength"], "again": again, "who": b.actor}, [i])
            changes = [k for k in outcome if beats[k].kind == "change"]
            surprised = any(beats[k].kind == "surprise" for k in outcome)
            told_way = any(beats[k].kind == "surprise" and beats[k].detail.get("told") for k in outcome)
            if b.actor != actor and not changes:   # another's push that did nothing is not told
                i = j
                continue
            if not changes:   # a belief contradicted reads as the contrast: "But this time it did not move."
                add("nothing", stage, {"obj": b.obj, "contrast": surprised, "told": told_way}, outcome)
            else:
                by_obj = {}
                for k in changes:
                    by_obj.setdefault(beats[k].obj, []).append(k)
                # the objects acted on or wanted first (the cause in hand), then what was new, in order
                for obj, ks in sorted(by_obj.items(), key=lambda kv: (kv[0] not in acted | wanted, kv[1][0])):
                    new = obj not in acted | wanted
                    flips = [(beats[k].detail["from"], beats[k].detail["to"]) for k in ks]
                    if new or obj in acted | wanted:
                        add("change", stage, {"obj": obj, "flips": flips, "new": new,
                                              "contrast": surprised and obj == b.obj}, ks)
                    seen_effects |= {f"{obj}_{t}" for _, t in flips}
            i = j
            continue
        elif b.kind == "learn" and b.detail.get("watched") and plant != "emphasized":
            pass   # learned by watching, and not said: the lesson stays in her ledger, off the page
        elif b.kind == "learn":
            cond_obj, cond_state = effect_parts(b.detail["condition"], objs)
            watching.add(cond_obj)
            also = [effect_parts(c, objs)[0] for c in b.detail.get("also", ())]   # an AND's other conditions
            for c in b.detail.get("also", ()):
                watching.add(effect_parts(c, objs)[0])
            add("learn", "resolution" if stage == "turn" else stage,
                {"obj": b.obj, "cond_obj": cond_obj, "cond_state": cond_state, "also": also,
                 "confirms": b.detail.get("confirms"), "exposes": b.detail.get("exposes")}, [i])
        elif b.kind == "ask":   # Pose across minds: the question, to someone
            add("ask", stage, {"obj": b.obj, "slot": b.detail["slot"], "to": b.detail["to"]}, [i])
        elif b.kind == "tell":   # Attest: the answer, from the teller's own receipts
            cond = b.detail.get("condition")
            co, cs = effect_parts(cond, objs) if cond else ("", "")
            add("tell", stage, {"who": b.actor, "to": b.detail["to"], "obj": b.obj, "cond_obj": co, "cond_state": cs,
                                "way": b.detail.get("way")}, [i])
            if b.detail.get("way") and reveal:   # a counterfeit: the narrator says what the teller holds
                to, ts = effect_parts(b.detail["truth"], objs)
                add("reveal", stage, {"who": b.actor, "obj": b.obj, "cond_obj": to, "cond_state": ts}, [i])
        elif b.kind == "scene":   # a new scene: its own frame
            later = [k for k in range(i + 1, len(beats)) if beats[k].kind == "see" and beats[k].obj in acted | wanted]
            add("scene", "setup", {"world": b.detail["world"], "objs": [beats[k].obj for k in later],
                                   "states": {beats[k].obj: beats[k].detail["gerund"] for k in later}}, [i] + later)
            last_try = None
        elif b.kind == "recall":   # an episode found again by its shape: the payoff of what was shown before
            add("recall", stage, {"obj": b.obj, "from_obj": b.detail["from_obj"], "watched": b.detail["watched"],
                                  "payoff": b.detail["from_cond"]}, [i])
        elif b.kind == "time":   # a scene break: time passing
            add("time", stage, {"ticks": b.detail["ticks"]}, [i])
        elif b.kind in ("leave", "return", "rise"):   # rung 7: authored comings and goings
            add(b.kind, stage, {"who": b.actor}, [i])
        elif b.kind == "lost":   # a kept state undone, found (rung 7): what the keeper sees
            add("lost", "resolution" if stage == "turn" else stage, {"who": b.actor, "obj": b.obj}, [i])
        elif b.kind == "believe":
            add("believe", stage, {"obj": b.obj, "strength": b.detail["cause"][0]}, [i])
        elif b.kind == "wait":
            prev = scene.plans[-1] if scene.plans else None
            if prev is not None and prev.kind == "wait" and prev.fill["condition"] == b.detail["condition"]:
                plan_of[i] = len(scene.plans) - 1   # still waiting for the same thing: one wait, told once
            else:
                add("wait", stage, {"condition": b.detail["condition"]}, [i])
        elif b.kind == "other" and b.obj in watching:   # a change the mind is watching for: told
            add("change", stage, {"obj": b.obj, "flips": [(b.detail["from"], b.detail["to"])], "new": False,
                                  "contrast": False}, [i])
        elif b.kind == "feel":   # a phase anchored on an object's region is about that object
            anchor = b.hole.split(":")[-1] if b.hole.startswith(("own:", "other:")) else ""
            if anchor in people or (b.actor != actor and anchor == actor):   # a phase anchored on a person
                add("feel", stage, {"phase": b.detail["phase"], "unexpected": [], "anchor": anchor, "person": True,
                                    "who": b.actor, "reopened": b.detail.get("reopened")}, [i])
                i += 1
                continue
            prev = scene.plans[-1] if scene.plans else None
            restates = (b.detail["phase"] == "curiosity" and prev is not None and prev.kind == "wonder"
                        and prev.fill["obj"] == anchor)
            if restates:   # the question just posed says it already
                plan_of[i] = len(scene.plans) - 1
                i += 1
                continue
            if b.detail["phase"] == "joy" and anchor in wanted and any(x.kind == "reach" for x in beats[:i]):
                anchor = ""   # joy at having what was wanted is about having it, not the object
            add("feel", "resolution" if stage == "turn" else stage,
                {"phase": b.detail["phase"], "unexpected": b.detail.get("unexpected", []),
                 "anchor": anchor if anchor in objs else "", "who": b.actor,
                 "reopened": b.detail.get("reopened"), "pull": b.detail.get("pull", 0.0)}, [i])
        i += 1
    scene.plans = summarize(combine(iterate(scene.plans)), actor)
    for i, p in enumerate(scene.plans):   # the turn after a run of failures: "At last ..."
        if p.kind == "try" and p.stage == "turn" and not p.fill.get("again") and p.fill.get("who", actor) == actor:
            before = scene.plans[max(0, i - 4):i]
            fails = sum(1 for q in before if q.kind in ("nothing", "explore") or
                        (q.kind == "attempt" and q.fill["outcome"] == "nothing"))
            if fails >= 2:
                p.fill = dict(p.fill, at_last=True)
    return scene


def key(p):
    """What makes two plans the same beat of a cycle (again-ness and contrast aside)."""
    return (p.kind, tuple(sorted((k, str(v)) for k, v in p.fill.items() if k not in ("again", "contrast"))))


def iterate(plans):
    """A window of plans that repeats right after itself, beginning with a wait and moving the object the
    window is about: the first telling stays, the repeats become one 'iterate' plan (a cycle summarized:
    "Twice more he waited ..., and each time ..."). Refs into the collapsed plans point at it."""
    out, i, remap = [], 0, {}
    while i < len(plans):
        done = False
        for w in range(2, 9):
            win = plans[i:i + w]
            two = len({p.fill.get("who") for p in win if p.kind == "try"}) > 1   # a tug of war: two minds' pushes
            one = sum(1 for p in win if p.kind == "try") == 1   # one push and what it did, again and again
            if len(win) < w or not (win[0].kind == "wait" or (win[0].kind == "try" and (two or one))):
                continue
            n = 0
            while plans[i + w * (n + 1):i + w * (n + 2)] and                     [key(p) for p in plans[i + w * (n + 1):i + w * (n + 2)]] == [key(p) for p in win]:
                n += 1
            moved = [p.fill["obj"] for p in win if p.kind == "change"]
            if n and moved:
                tries = [p for p in win if p.kind == "try"]
                obj = tries[0].fill["obj"] if tries else moved[0]
                for k, p in enumerate(win):
                    remap[i + k] = len(out)
                    out.append(p)
                reps = plans[i + w:i + w * (n + 1)]
                for k in range(len(reps)):
                    remap[i + w + k] = len(out)
                out.append(Plan("iterate", reps[-1].stage, {"window": win, "count": n, "obj": obj},
                                tuple(b for p in reps for b in p.beats), ()))
                i += w * (n + 1)
                done = True
                break
        if not done:
            remap[i] = len(out)
            out.append(plans[i])
            i += 1
    for p in out:
        p.refs = tuple(sorted({remap[r] for r in p.refs if r in remap and remap[r] < out.index(p)}))
    return out


def _rebuild(plans, groups, make):
    """Replace runs of plans by one plan each. groups: [(start, end)] (end exclusive, non-overlapping, sorted);
    make(run) -> the plan that tells the run. Refs into a run point at its plan."""
    out, remap, i, g = [], {}, 0, 0
    while i < len(plans):
        if g < len(groups) and groups[g][0] == i:
            a, b = groups[g]
            run = plans[a:b]
            merged = make(run)
            merged.refs = tuple(sorted({r for p in run for r in p.refs}))
            for k in range(a, b):
                remap[k] = len(out)
            out.append(merged)
            i, g = b, g + 1
            continue
        remap[i] = len(out)
        out.append(plans[i])
        i += 1
    for p in out:
        p.refs = tuple(sorted({remap[r] for r in p.refs if r in remap and remap[r] < out.index(p)}))
    return out


def combine(plans):
    """A push and what it did to the object pushed, told as one sentence ("She pushed the lid hard, but it did
    not move."): a try followed by its outcome on the same object. A contrast (an outcome against what was
    believed or told) stays a sentence of its own: it is the scene's turn."""
    groups, i = [], 0
    while i + 1 < len(plans):
        p, q = plans[i], plans[i + 1]
        if p.kind == "try" and q.kind in ("nothing", "change") and q.fill.get("obj") == p.fill.get("obj")                 and not q.fill.get("contrast") and not q.fill.get("new"):
            groups.append((i, i + 2))
            i += 2
            continue
        i += 1

    def make(run):
        p, q = run
        fill = {"try": p.fill, "outcome": q.kind, "result": q.fill, "obj": p.fill["obj"], "who": p.fill.get("who")}
        plant = q.fill.get("plant") or p.fill.get("plant")
        if plant:
            fill["plant"] = plant
        return Plan("attempt", q.stage, fill, p.beats + q.beats, ())
    return _rebuild(plans, groups, make)


def summarize(plans, actor, least=2):
    """Varied exploration (rung 4, finding 6): a run of failed attempts by the character, on whatever objects,
    with nothing else between them, is told by its first attempt and then one sentence for the rest ("Again and
    again she tried the lid and the flag, but nothing came of it."). A run that teaches nothing has nothing for
    the reader to keep but its length and what was tried."""
    def failed(p):
        return (p.kind == "attempt" and p.fill.get("who", actor) == actor and not p.fill.get("plant")
                and (p.fill["outcome"] == "nothing" or reverted(p.fill["result"])))

    def reverted(r):   # a change that ended where it began (a flag that swung and hung still): nothing came of it
        flips = r.get("flips", [])
        return bool(flips) and flips[0][0] == flips[-1][1] and not r.get("new")
    groups, i = [], 0
    while i < len(plans):
        j = i
        while j < len(plans) and failed(plans[j]):
            j += 1
        if j - i >= least + 1:   # the first is told in full; the rest summarized
            groups.append((i + 1, j))
        i = max(j, i + 1)

    def make(run):
        objs = []
        for p in run:
            if p.fill["obj"] not in objs:
                objs.append(p.fill["obj"])
        moved = any(p.fill["outcome"] == "change" for p in run)
        return Plan("explore", run[-1].stage, {"objs": objs, "count": len(run), "moved": moved, "who": actor},
                    tuple(b for p in run for b in p.beats), ())
    return _rebuild(plans, groups, make)
