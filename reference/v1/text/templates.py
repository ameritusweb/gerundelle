"""Templates: which sentence structures read as which gerunds (TEXT_VOCABULARY.md).

Hand-written rules over a dependency parse, as rules.py is for code: they define what
counts, and determine.py only applies them. Three kinds:
- core(): what one clause does, from its verb (claiming, describing, narrating, ...).
- lexical(): further readings of the same clause from cue words (grounding, judging, the
  expressing_* gerunds, personifying). These are alternatives, not replacements: a clause
  with a date reads as narrating and as grounding. Ambiguity is a form of abstraction.
- relations: how two clauses (or a clause and a phrase) combine, from markers such as
  "because", "although", "when", a relative clause or "such as". A relation is
  (gerund, main role, other role, other comes first); a marker can have several.

When a sentence gets a wrong reading, the fix is a template, not a looser matcher.
"""


def rel(kind, main, other, other_first=False):
    return (kind, main, other, other_first)


CAUSE = rel("explaining", "effect", "cause", True)        # Y because X
EFFECT = rel("explaining", "cause", "effect")             # X, so Y
CONDITION = rel("explaining", "effect", "condition", True)  # Y if X
PURPOSE = rel("explaining", "means", "purpose")           # Y in order to X
CONTRAST = rel("contrasting", "main", "other")            # Y although X
COMPARE = rel("comparing", "main", "other")               # Y, as X
AFTER = rel("narrating", "then", "first", True)           # Y after X: X happened first
BEFORE = rel("narrating", "first", "then")                # Y before X: Y happened first
MEANWHILE = rel("narrating", "main", "meanwhile")         # Y while X
SEQUENCE = rel("narrating", "first", "then")              # X and Y (both past)
ELABORATE = rel("elaborating", "main", "detail")
DISAMBIGUATE = rel("disambiguating", "main", "detail")
SOURCED = rel("grounding", "main", "source", True)       # according to X, Y
EXAMPLE_GROUNDS = rel("grounding", "main", "example")
EXAMPLE_ELABORATES = rel("elaborating", "main", "example")

# subordinating markers of an adverbial clause
MARKS = {
    "because": [CAUSE], "since": [CAUSE, AFTER], "as": [CAUSE, MEANWHILE, COMPARE], "so": [EFFECT],
    "although": [CONTRAST], "though": [CONTRAST], "even though": [CONTRAST], "whereas": [CONTRAST],
    "while": [CONTRAST, MEANWHILE], "whilst": [CONTRAST, MEANWHILE], "even if": [CONTRAST],
    "if": [CONDITION], "unless": [CONDITION], "provided": [CONDITION],
    "when": [AFTER, MEANWHILE], "whenever": [MEANWHILE], "after": [AFTER], "once": [AFTER],
    "before": [BEFORE], "until": [BEFORE], "till": [BEFORE], "as soon as": [AFTER],
    "so that": [PURPOSE], "in order": [PURPOSE], "than": [COMPARE], "like": [COMPARE], "as if": [COMPARE],
}

# coordinators between two clauses
CONJUNCTIONS = {"and": [ELABORATE], "or": [ELABORATE], "": [ELABORATE], "but": [CONTRAST], "yet": [CONTRAST],
                "so": [EFFECT], "nor": [ELABORATE]}

# phrases inside a clause that relate it to a noun phrase (the other side is a slot)
PHRASES = [
    (("because", "of"), [CAUSE]), (("due", "to"), [CAUSE]), (("owing", "to"), [CAUSE]), (("thanks", "to"), [CAUSE]),
    (("as", "a", "result", "of"), [CAUSE]),
    (("despite",), [CONTRAST]), (("in", "spite", "of"), [CONTRAST]), (("unlike",), [CONTRAST]),
    (("instead", "of"), [CONTRAST]), (("rather", "than"), [CONTRAST]), (("in", "contrast", "to"), [CONTRAST]),
    (("similar", "to"), [COMPARE]), (("compared", "to"), [COMPARE]), (("compared", "with"), [COMPARE]),
    (("such", "as"), [EXAMPLE_GROUNDS, EXAMPLE_ELABORATES]), (("including",), [EXAMPLE_GROUNDS, EXAMPLE_ELABORATES]),
    (("for", "example"), [EXAMPLE_GROUNDS, EXAMPLE_ELABORATES]), (("for", "instance"), [EXAMPLE_GROUNDS, EXAMPLE_ELABORATES]),
    (("e.g.",), [EXAMPLE_GROUNDS, EXAMPLE_ELABORATES]),
    (("known", "as"), [DISAMBIGUATE]), (("also", "called"), [DISAMBIGUATE]), (("referred", "to", "as"), [DISAMBIGUATE]),
    (("not", "to", "be", "confused"), [DISAMBIGUATE]), (("also", "spelled"), [DISAMBIGUATE]),
    (("or", "simply"), [DISAMBIGUATE]),
]

# sentence-initial markers that relate the sentence to what came before (the context)
CONTEXT = [
    (("however",), rel("contrasting", "main", "context", True)), (("nevertheless",), rel("contrasting", "main", "context", True)),
    (("but",), rel("contrasting", "main", "context", True)), (("yet",), rel("contrasting", "main", "context", True)),
    (("nonetheless",), rel("contrasting", "main", "context", True)), (("instead",), rel("contrasting", "main", "context", True)),
    (("conversely",), rel("contrasting", "main", "context", True)), (("in", "contrast"), rel("contrasting", "main", "context", True)),
    (("on", "the", "other", "hand"), rel("contrasting", "main", "context", True)),
    (("therefore",), rel("explaining", "effect", "context", True)), (("thus",), rel("explaining", "effect", "context", True)),
    (("hence",), rel("explaining", "effect", "context", True)), (("consequently",), rel("explaining", "effect", "context", True)),
    (("as", "a", "result"), rel("explaining", "effect", "context", True)), (("accordingly",), rel("explaining", "effect", "context", True)),
    (("for", "example"), rel("grounding", "example", "context", True)), (("for", "instance"), rel("grounding", "example", "context", True)),
    (("and",), rel("elaborating", "detail", "context", True)),
    (("moreover",), rel("elaborating", "detail", "context", True)), (("furthermore",), rel("elaborating", "detail", "context", True)),
    (("additionally",), rel("elaborating", "detail", "context", True)), (("in", "addition"), rel("elaborating", "detail", "context", True)),
    (("also",), rel("elaborating", "detail", "context", True)),
    (("likewise",), rel("comparing", "main", "context", True)), (("similarly",), rel("comparing", "main", "context", True)),
    (("then",), rel("narrating", "then", "context", True)), (("later",), rel("narrating", "then", "context", True)),
    (("subsequently",), rel("narrating", "then", "context", True)), (("afterwards",), rel("narrating", "then", "context", True)),
    (("afterward",), rel("narrating", "then", "context", True)), (("meanwhile",), rel("narrating", "meanwhile", "context", True)),
]

# -- core: what one clause does ----------------------------------------------------------
REPORTING = {"say", "state", "argue", "claim", "believe", "suggest", "report", "note", "write", "announce", "insist",
             "deny", "assert", "maintain", "think", "contend", "declare", "allege", "estimate", "conclude", "propose",
             "predict", "speculate", "hypothesize", "theorize", "acknowledge", "admit", "explain", "add", "observe",
             "consider", "regard", "describe", "deem", "hold", "feel", "doubt", "find", "show", "indicate", "reveal"}
PASSIVE_REPORTING = {"consider", "regard", "believe", "think", "say", "know", "describe", "deem", "hold", "call",
                     "report", "rumor", "rumour", "suppose", "presume", "expect", "estimate"}
DECOMPOSING = {"consist", "comprise", "compose", "divide", "split", "constitute", "subdivide", "break"}
CONTAINING = {"include", "contain", "encompass", "feature"}
CAUSING = {"cause", "lead", "result", "prompt", "trigger", "enable", "prevent", "force", "allow",
           "contribute", "spark", "provoke", "induce"}
# causal only with this preposition: "led to the war" causes, "led the league" doesn't
CAUSING_WITH = {"lead": {"to"}, "result": {"in", "from"}, "contribute": {"to"}}
# verbs whose "to"-infinitive completes them ("began to write"); after any other verb a
# "to"-infinitive is a purpose ("uses the camera to obtain numbers")
CONTROL = {"begin", "start", "continue", "try", "attempt", "want", "wish", "hope", "plan", "decide", "need", "seem",
           "appear", "fail", "manage", "refuse", "agree", "promise", "intend", "expect", "learn", "choose", "come",
           "go", "have", "be", "like", "love", "hate", "prefer", "offer", "threaten", "ask", "tell", "allow",
           "enable", "force", "help", "able", "tend", "cease", "stop", "proceed", "aim", "seek", "struggle", "vote",
           "prepare", "pretend", "claim", "happen", "remain", "get", "order", "urge", "encourage", "invite", "persuade",
           "convince", "require", "permit", "teach", "train", "elect", "appoint", "advise", "cause", "lead", "move",
           # passive and adjectival frames: "is scheduled to", "is said to", "is likely to"
           "schedule", "set", "say", "believe", "think", "know", "report", "suppose", "estimate", "consider",
           "due", "likely", "unlikely", "unable", "willing", "ready", "eager", "reluctant", "free", "bound", "sure"}


def purpose_infinitive(xcomp):
    """A "to"-infinitive that is a purpose, not the completion of its verb."""
    if xcomp.dep_ != "xcomp" or not any(c.dep_ == "aux" and c.lower_ == "to" for c in xcomp.children):
        return False
    head = xcomp.head
    lemma = head.lemma_.lower()
    if lemma == "use" and not any(c.dep_ == "dobj" for c in head.children) and not passive(head):
        return False  # "used to live": a habit ("was used to run the AGC" is a purpose)
    return lemma not in CONTROL


COMPARING ={"resemble", "compare", "exceed", "surpass", "outnumber", "equal", "mirror", "parallel", "rival", "match"}
CONTRASTING = {"differ", "contrast", "oppose", "distinguish", "contradict"}
DEFINING = {"mean", "refer", "denote", "signify", "stand", "name", "rename", "translate", "spell", "abbreviate"}
LOCATING = {"locate", "base", "situate", "headquarter", "border", "lie"}
HEDGES = {"may", "might", "could", "can"}
# verbs of states, not events: present tense describes, it does not narrate
STATIVE = {"be", "have", "contain", "include", "consist", "comprise", "require", "need", "own", "belong", "mean",
           "know", "seem", "appear", "resemble", "remain", "lie", "stand", "exist", "represent", "involve",
           "depend", "equal", "measure", "weigh", "cost", "cover", "serve", "hold", "range", "vary", "use"}
OBLIGATIONS = {"must", "should", "ought", "shall"}


def shares_head(verb):
    """A coordinated verb with no auxiliary of its own takes its head's tense and voice:
    "It was written by X and directed by Y"."""
    return verb.dep_ == "conj" and verb.tag_ in ("VBN", "VB", "VBG") and not any(
        c.dep_ in ("aux", "auxpass") for c in verb.children) and verb.head.pos_ in ("VERB", "AUX")


def tense(verb):
    """'past', 'present', 'modal:<word>' or 'base' (no tense: an imperative or fragment)."""
    if shares_head(verb):
        return tense(verb.head)
    for a in verb.children:
        if a.dep_ == "aux" and a.tag_ == "MD":
            return "modal:" + a.lower_
    if verb.tag_ == "VBD":
        return "past"
    for a in verb.children:
        if a.dep_ in ("aux", "auxpass") and a.tag_ == "VBD":
            return "past"
        if a.dep_ == "aux" and a.lemma_ == "have":  # has published: a past event told now
            return "past"
    if verb.tag_ in ("VBZ", "VBP"):
        return "present"
    for a in verb.children:
        if a.dep_ in ("aux", "auxpass") and a.tag_ in ("VBZ", "VBP"):
            return "present"
    return "base"


def passive(verb):
    if any(c.dep_ in ("auxpass", "nsubjpass") for c in verb.children):
        return True
    return verb.tag_ == "VBN" and shares_head(verb) and passive(verb.head)


def has_subject(verb):
    return any(c.dep_ in ("nsubj", "nsubjpass", "csubj", "csubjpass", "expl") for c in verb.children)


def core(verb):
    """The gerunds one clause's verb reads as, and whether it is an action (has an event)."""
    if verb.pos_ not in ("VERB", "AUX"):
        return [], False
    lemma = verb.lemma_.lower()
    deps = {c.dep_ for c in verb.children}
    t = tense(verb)
    if t == "base" and verb.dep_ == "ROOT" and not has_subject(verb):
        return [], True  # an imperative: no gerund for it yet (a gap, reported)
    if lemma == "be" and verb.dep_ != "aux":
        return ["describing"], False
    if lemma == "have" and verb.dep_ not in ("aux", "auxpass") and "dobj" in deps and t != "past":
        return ["describing"], False
    out = []
    if passive(verb) and lemma in PASSIVE_REPORTING:
        out += ["claiming", "describing"]
    elif lemma in REPORTING and deps & {"ccomp", "xcomp"}:
        out.append("claiming")
    if lemma in DECOMPOSING:
        out.append("decomposing")
    if lemma in CONTAINING:
        out += ["decomposing", "describing"]
    if lemma in CAUSING and (lemma not in CAUSING_WITH or any(
            c.dep_ == "prep" and c.lower_ in CAUSING_WITH[lemma] for c in verb.children)):
        out.append("explaining")
    if lemma in COMPARING:
        out.append("comparing")
    if lemma in CONTRASTING:
        out.append("contrasting")
    if lemma in DEFINING:
        out += ["disambiguating", "describing"]
    if passive(verb) and lemma in LOCATING:
        out.append("describing")
    if t.startswith("modal:"):
        word = t[6:]
        if word in HEDGES or word in OBLIGATIONS:
            out.append("claiming")
        elif word in ("will", "'ll"):  # a prediction, or the future told as narration
            out += ["claiming", "narrating"]
        elif word == "would":  # "would later become": the past's future, told as narration
            out.append("narrating")
    if t == "past":
        out.append("narrating")
        if lemma in STATIVE:  # "they had training", "relations have existed": a past state
            out.append("describing")
    elif t == "present" or (t == "base" and not out):
        out.append("describing")
        if t == "present" and lemma not in STATIVE:  # plot summaries narrate in the present
            out.append("narrating")
    return list(dict.fromkeys(out)), True


# -- lexical: more readings from cue words ---------------------------------------------
EMOTIONS = {
    "expressing_disbelief": {"disbelief", "unbelievable", "incredulous", "incredulity", "unthinkable"},
    "expressing_grief": {"grief", "grieve", "mourn", "mourning", "bereave", "bereavement", "bereaved"},
    "expressing_sorrow": {"sorrow", "sad", "sadness", "sorrowful", "heartbroken", "melancholy", "unhappy", "tragic"},
    "expressing_exasperation": {"exasperate", "exasperation", "exasperated", "frustrate", "frustration", "frustrated",
                                "annoy", "annoyance", "annoyed", "irritate", "irritation"},
    "expressing_anger": {"anger", "angry", "rage", "furious", "outrage", "outraged", "indignant", "indignation",
                         "resent", "resentment", "fury"},
    "expressing_fear": {"fear", "afraid", "terrify", "terror", "frighten", "dread", "anxiety", "anxious", "panic",
                        "scared", "fearful"},
    "expressing_joy": {"joy", "happy", "happiness", "delight", "delighted", "joyful", "elated", "glee", "jubilant"},
    "expressing_hope": {"hope", "hopeful", "aspire", "aspiration", "optimism", "optimistic"},
    "expressing_love": {"love", "beloved", "adore", "affection", "cherish", "fond"},
    "expressing_gratitude": {"thank", "thanks", "grateful", "gratitude", "appreciate", "appreciation", "indebted"},
    "expressing_pride": {"pride", "proud"},
    "expressing_awe": {"awe", "awestruck", "majestic", "sublime", "breathtaking"},
    "expressing_contentment": {"contentment", "satisfied", "satisfaction"},
    "expressing_serenity": {"serene", "serenity", "tranquil", "tranquility", "tranquillity", "peaceful"},
    "expressing_empathy": {"empathy", "empathize", "sympathize", "sympathy", "sympathetic"},
    "expressing_solidarity": {"solidarity", "unity"},
    "expressing_compassion": {"compassion", "compassionate", "mercy", "merciful", "kindness"},
    "expressing_encouragement": {"encourage", "encouragement", "inspire", "motivate", "reassure"},
    "expressing_forgiveness": {"forgive", "forgiveness", "pardon", "absolve"},
    "expressing_remorse": {"remorse", "remorseful", "apologize", "apologise", "apology", "repent"},
    "expressing_humility": {"humble", "humility", "modest", "modesty"},
    "expressing_longing": {"longing", "yearn", "yearning", "nostalgia", "nostalgic"},
    "expressing_regret": {"regret", "regretful", "rue"},
    "expressing_defiance": {"defy", "defiance", "defiant", "rebel", "rebellion", "resist", "resistance"},
    "expressing_resignation": {"futile", "hopeless", "inevitable", "resigned"},
    "expressing_surrender": {"surrender", "capitulate", "capitulation"},
    "expressing_resolve": {"resolute", "vow", "pledge"},
    "expressing_determination": {"determination", "determined", "persevere", "perseverance", "persist", "tenacity",
                                 "tenacious"},
    "expressing_patience": {"patience", "gradually", "slowly", "eventually", "gradual"},
    "expressing_urgency": {"urgent", "urgently", "immediately", "hurry", "swiftly", "emergency", "hastily"},
    "expressing_calm": {"calm", "calmly", "quietly", "steadily"},
    "expressing_restlessness": {"restless", "restlessly", "incessant", "incessantly", "frantic", "frantically"},
    "expressing_curiosity": {"curious", "curiosity", "unknown", "unclear", "mystery", "mysterious", "wonder"},
    "expressing_wonder": {"marvel", "astonish", "astonishing", "amazing", "amaze", "remarkable", "extraordinary",
                          "spectacular", "wondrous"},
}
# a cue word with another common sense: only this part of speech counts
CUE_POS = {"patience": None, "fond": "ADJ", "wonder": "VERB", "fear": None, "hope": None, "long": "VERB"}

JUDGING = {"good", "bad", "best", "worst", "great", "greatest", "important", "significant", "notable", "famous",
           "renowned", "prominent", "influential", "successful", "unsuccessful", "popular", "controversial",
           "acclaimed", "excellent", "poor", "praise", "criticize", "criticise", "criticism", "acclaim", "celebrated",
           "infamous", "notorious", "legendary", "iconic", "seminal", "landmark", "outstanding", "mediocre"}
# a mind's verbs on a subject that has no mind
MINDFUL = {"believe", "think", "want", "wish", "feel", "hope", "decide", "refuse", "insist", "love", "hate", "fear",
           "remember", "forget", "desire", "dream", "struggle", "welcome", "embrace", "suffer", "sleep", "breathe",
           "weep", "smile", "sing", "whisper", "dance", "wander", "sigh", "yearn", "mourn", "rejoice", "beg"}
GROUNDING_TYPES = {"time", "amount"}


def lexical(verb, own, agent_type, slot_types):
    """Readings of the clause from its own words. slot_types: the clause's slot types."""
    out = []
    lemmas = {(t.lemma_.lower(), t.pos_) for t in own} | {(t.lower_, t.pos_) for t in own}
    words = {w for w, _ in lemmas}
    if slot_types & GROUNDING_TYPES or ("according" in words):
        out.append("grounding")
    if words & JUDGING:
        out.append("judging")
    for gerund, cues in EMOTIONS.items():
        for w, pos in lemmas:
            if w in cues and CUE_POS.get(w, pos) in (pos, None):
                out.append(gerund)
                break
    if verb.dep_ == "ROOT" and any(t.text == "?" for t in own):
        out.append("expressing_curiosity")
    if agent_type in ("group", "thing", "place") and verb.lemma_.lower() in MINDFUL:
        out.append("personifying")
    return list(dict.fromkeys(out))
