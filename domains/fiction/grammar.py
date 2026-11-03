"""The fiction grammar: an additive extension of the determination system (E:/vscode/analogy/text).

DOMAIN_EXPANSION_PLAN.md phase 1: new templates, new gerunds, same engine; the Wikipedia templates are
untouched. Nothing here edits templates.py or determine.py: `install()` wraps their functions in place
for the process that calls it, so the Wikipedia corpus, the towers and the judge's skeleton bank keep the
readings they were built on, and a fiction run opts in. A sentence that matches an old template and a
new one gets both readings (ambiguity is a form of abstraction); the new ones fire only on patterns the
old ones misread. Each addition is a gap the fiction ladder found (fiction/LADDER.md):

    realizing    a hole closing in a mind: "She realized that the latch had held the lid."
                 (read as narrating: no gerund for the aha; rung 0)
    asking       a question put to someone, the Pose across minds: '"What keeps it shut?" she asked.',
                 "She asked Ben what kept it shut."   (read as narrating; rung 2)
    telling      an answer or report given to someone, the Attest across minds: '"The latch," Ben said.',
                 "Ben told her that the latch held it."   (read as narrating or claiming; rung 2)
    instructing  a command: '"Push the latch," Ben said.'   (an imperative had no gerund at all; rung 2)
    iterating    a repeated event: "Twice more he waited ...", "Again and again he pushed the crate.",
                 "Every time the flag swung, the crate moved."   (read as elaborating; rung 1)

and two fixes:
    "only when" / "only if": a condition (explaining), not a time ("only when" read as narrating; rung 1)
    "waited for the flag to swing": an infinitive with its own subject is an event (undetermined; rung 1)
"""
import os
import sys

TEXT_DIR = os.environ.get("ANALOGY_TEXT", "E:/vscode/analogy/text")
sys.path.insert(0, TEXT_DIR)
import determine as D  # noqa: E402
import templates as T  # noqa: E402

REALIZING = {"realize", "realise", "understand", "recognize", "recognise", "discover", "learn", "notice", "see",
             "grasp", "figure", "guess", "remember"}
ASKING = {"ask", "inquire", "enquire", "query", "question"}
TELLING = {"say", "tell", "answer", "reply", "explain", "whisper", "shout", "add", "insist", "warn",
           "murmur", "mutter", "cry", "admit", "inform", "assure", "remind"}   # not "call": calling is naming
ITERATING = [("again", "and", "again"), ("over", "and", "over"), ("time", "after", "time"), ("each", "time"),
             ("every", "time"), ("once", "more"), ("twice", "more"), ("more", "times"), ("repeatedly",)]
QUOTES = {'"', "“", "”", "'", "‘", "’"}
LONGING = {"long", "yearn", "pine", "ache"}   # verbs of longing (as VERB only: "a long day" is not one)

_installed = False


def quoted(verb):
    """Whether the verb's content is quoted speech: a content clause of the verb inside quotation marks
    ('"..." Mara asked', 'Ben said, "..."'); scare quotes on a noun ('calling it "a perfect doc"') are not."""
    return any(c.dep_ in ("ccomp", "parataxis", "xcomp") and in_quotes(c) for c in verb.children)


def has_content(verb):
    return any(c.dep_ in ("ccomp", "xcomp", "csubj", "parataxis") for c in verb.children)


def finite_content(verb):
    """Content a mind can realize: a clause with its own subject or a 'that'/wh opening ("learns that
    her sister ...", "noticing she is getting worse"); not a perception of a doing ("sees him talking")."""
    for c in verb.children:
        if c.dep_ in ("ccomp", "csubj"):
            tensed = c.tag_ in ("VBD", "VBZ", "VBP") or any(
                a.dep_ in ("aux", "auxpass") and a.tag_ in ("MD", "VBD", "VBZ", "VBP") for a in c.children)
            if tensed or any(m.dep_ == "mark" for m in c.children):
                return True
    return False


def speaker(verb):
    """A speaking subject: a person or a group (or a pronoun standing for one); "the plot questions
    whether" is a figure, read by personifying, not a question asked."""
    subj = next((c for c in verb.children if c.dep_ == "nsubj"), None)
    return subj is not None and (D.slot_type(subj) in ("person", "group") or subj.lower_ in ("they", "i", "we", "you"))


def has_recipient(verb):
    return any(c.dep_ in ("dative", "dobj") and D.slot_type(c) in ("person", "group") for c in verb.children)


def is_question(verb):
    """A question as content: a wh-word or 'whether'/'if' opening the content clause, or a '?' in it."""
    for c in verb.children:
        if c.dep_ in ("ccomp", "xcomp", "parataxis"):
            words = [t for t in c.subtree]
            if any(t.text == "?" for t in words) or any(t.tag_ in ("WDT", "WP", "WP$", "WRB") or
                                                       t.lower_ in ("whether",) for t in words[:3]):
                return True
    return any(t.text == "?" for t in verb.doc)


def in_quotes(tok):
    """Whether a token sits inside quotation marks (an odd number of quote marks before it)."""
    return sum(1 for t in tok.doc[:tok.i] if t.text in QUOTES) % 2 == 1


def repair(doc):
    """Parse repair (before determination): a bare verb inside quotation marks attached to a verb of
    speech as xcomp, advcl, parataxis or dep is that verb's content ('"Push the latch," Ben said': the
    parser makes Push an xcomp, and its words fold into "said"). Relabelled ccomp."""
    for t in doc:
        speech = t.head.lemma_.lower() in TELLING | ASKING
        if (t.tag_ == "VB" and not T.has_subject(t) and in_quotes(t) and speech
                and t.dep_ in ("xcomp", "advcl", "parataxis", "dep")):
            t.dep_ = "ccomp"
    return doc


def imperative(verb):
    """A command: a bare verb (VB) with no subject and no auxiliary, either quoted content of a verb of
    speech, or at the root with nothing before it but adverbs or "please" (a plot summary's "Finally
    decide to ..." is a fragment, not a command)."""
    if verb.tag_ != "VB" or T.has_subject(verb) or any(c.dep_ in ("aux", "auxpass") for c in verb.children):
        return False
    if verb.dep_ in ("ccomp", "parataxis") and in_quotes(verb):
        return True
    before = [t for t in verb.doc[:verb.i] if not t.is_punct]
    return verb.dep_ == "ROOT" and all(t.lower_ == "please" for t in before)


def install():
    """Wrap the determination system's functions with the fiction templates (idempotent)."""
    global _installed
    if _installed:
        return
    _installed = True
    core, lexical, advcl, valid, determine_doc = T.core, T.lexical, D.advcl_relations, D.valid, D.determine_doc

    def core_ext(verb):
        if verb.pos_ in ("VERB", "AUX") and imperative(verb):
            return ["instructing"], True
        kinds, action = core(verb)
        lemma = verb.lemma_.lower()
        extra = []
        if lemma in REALIZING and finite_content(verb):
            extra.append("realizing")
        if lemma in ASKING and has_content(verb) and is_question(verb) and (quoted(verb) or speaker(verb)):
            extra.append("asking")
        if lemma in TELLING and has_content(verb) and (quoted(verb) or has_recipient(verb)) and (
                quoted(verb) or speaker(verb)):
            extra.append("telling")
        # an infinitive with its own subject ("waited for the flag to swing") is an event; a copula
        # ("expected her to be a politician") stays the description it was
        event = (lemma != "be" and T.tense(verb) == "base" and T.has_subject(verb) and verb.dep_ != "ROOT"
                 and any(c.dep_ == "aux" and c.lower_ == "to" for c in verb.children) and "narrating" not in kinds)
        if event:
            extra.append("narrating")
        return list(dict.fromkeys(kinds + extra)), action or event

    def lexical_ext(verb, own, agent_type, slot_types):
        out = lexical(verb, own, agent_type, slot_types)
        # emotion cues on verbs the lemmatizer misses ("forgave" is not lemmatized to "forgive"): the verb's
        # base form recovered by WordNet, checked against the same cue sets; and "long" (to long for), which
        # the cue table's own part-of-speech rule names but its longing set lacks
        from nltk.corpus import wordnet as wn
        for t in own:
            if t.pos_ != "VERB":
                continue
            base = wn.morphy(t.lower_, "v") or t.lemma_.lower()
            for gerund, cues in T.EMOTIONS.items():
                if base in cues and gerund not in out:
                    out.append(gerund)
            if base in LONGING and "expressing_longing" not in out:
                out.append("expressing_longing")
        words = [t.lower_ for t in own]
        # cue phrases in the clause's own words, or opening the sentence ("Every time ..., the crate moved")
        heads = [t.lower_ for t in verb.doc if not t.is_punct][:3]
        cue = any(D.phrase_at(own, i, w) for w in ITERATING for i in range(len(own)))
        opening = verb.dep_ == "ROOT" and any(tuple(heads[:len(w)]) == w for w in ITERATING)   # the root's only
        keeps = verb.lemma_.lower() == "keep" and any(c.dep_ == "xcomp" and c.tag_ == "VBG" for c in verb.children)
        if cue or opening or keeps:
            out.append("iterating")
        return list(dict.fromkeys(out))

    def advcl_ext(sub):
        # "only when", "only if": a condition the main clause holds under, not a time
        marks = [c for c in sub.children if c.dep_ == "mark" or (c.dep_ == "advmod" and c.lower_ == "when")]
        only = any(c.lower_ == "only" for c in sub.children) or any(
            c.lower_ == "only" for m in marks for c in m.children) or any(
            t.lower_ == "only" and t.i + 1 < len(sub.doc) and sub.doc[t.i + 1] in marks for t in sub.doc)
        if only and marks and marks[0].lower_ in ("when", "if", "whenever"):
            return [T.CONDITION]
        return advcl(sub)

    def valid_ext(node):
        if node.kind == "slot":
            return True
        roles = {r for r, _ in node.kids}
        if node.kind in ("realizing", "asking") and not roles & {"content", "subject"}:
            return False   # realizes nothing, asks nothing
        if node.kind == "telling" and not roles & {"content", "subject", "recipient", "patient"}:
            return False
        return valid(node)

    def determine_doc_ext(doc, stats=None):
        return determine_doc(repair(doc), stats)

    T.core, T.lexical, D.advcl_relations, D.valid = core_ext, lexical_ext, advcl_ext, valid_ext
    D.determine_doc = determine_doc_ext


if os.environ.get("FICTION_GRAMMAR", "1") != "0":
    install()
