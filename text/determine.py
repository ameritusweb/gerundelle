"""Sentence ambiguous abstraction determination (text POC; TEXT_EMBEDDING.md).

A real sentence -> its ambiguous gerund abstraction: the set of valid readings, each a tree
of gerund operations (TEXT_VOCABULARY.md) whose leaves are unnamed, typed slots. Content
words are stripped, as POC3's strip() strips names from a wired program, so "The company
moved to London in 1889" and "The family emigrated to Canada in 1902" get the same
abstraction. What's left is the structure.

- Sentence structure: a dependency parse (spaCy, PARSER below), split into clauses.
- Templates (templates.py): which structures read as which gerunds. The rules decide.
- Readings: every combination of each clause's gerunds and each relation's gerunds. Several
  readings is not an error: ambiguity is a form of abstraction.
- Validity (valid()): a reading is valid if every node has the parts its gerund needs; a
  sentence is determined if at least one reading is valid (there EXISTS an interpretation).

Usage: python determine.py [--file E:/E/parquet/a.txt] [--n 2000]
"""
import argparse
import itertools
import json
import os
import re
from collections import Counter

import templates as T

MAX_READINGS = 64  # per clause, and per sentence; hitting it is counted, not hidden
MAX_TOKENS = 80  # longer "sentences" are failed splits (a list run together); one nested a reading past Python's recursion limit


class Node:
    """A gerund with role-labelled kids, or a slot (kind 'slot', value = its type).

    span: the token positions of the sentence the node covers (a clause node its own words
    and its content clauses, a relation both its parts, a slot the words that fill it). It is
    not part of the node's identity, so sentences with the same structure share an AST; it is
    what lets each node be paired with the embedding of its own text."""
    __slots__ = ("kind", "kids", "value", "span")

    def __init__(self, kind, kids=(), value="", span=frozenset()):
        self.kind, self.kids, self.value = kind, tuple(kids), value
        self.span = frozenset(span).union(*(k.span for _, k in self.kids))

    def key(self):
        return (self.kind, self.value, tuple((r, k.key()) for r, k in self.kids))

    def __eq__(self, other):
        return isinstance(other, Node) and self.key() == other.key()

    def __hash__(self):
        return hash(self.key())

    def __str__(self):
        if self.kind == "slot":
            return self.value or "_"
        parts = []
        for role, k in self.kids:
            if k.kind == "slot":
                parts.append(f"{role}:{k.value}" if k.value else role)
            else:
                parts.append(f"{role}={k}")
        return f"{self.kind}({', '.join(parts)})"

    def gerunds(self):
        if self.kind != "slot":
            yield self.kind
        for _, k in self.kids:
            yield from k.gerunds()

    def walk(self, path=""):
        """(path, node) for this node and every node under it; a path is the roles from the
        root, joined by '/' ('' for the root)."""
        yield path, self
        for role, k in self.kids:
            yield from k.walk(f"{path}/{role}" if path else role)


def slot(value="", span=frozenset()):
    return Node("slot", (), value, span)


def span_text(doc, span, gap=" "):
    """The surface text of a span: its words in order, with the punctuation between them
    ("Ahmad cleared Bose's mind, explaining ..."). Where words of another node interrupt it,
    the runs are joined by gap. The text is what gets embedded, and the embedder is sensitive
    to the surface (a final period alone moves the cosine to 0.85), so it is the real text,
    not a display form."""
    idx = sorted(span)
    runs, run = [], []
    for i in idx:
        if run and i != run[-1] + 1 and not all(t.is_punct for t in doc[run[-1] + 1:i]):
            runs.append(run)
            run = []
        run.append(i)
    if run:
        runs.append(run)
    return balanced(gap.join(doc[r[0]:r[-1] + 1].text for r in runs))


def balanced(text):
    """Drop brackets left without their partner by a span's edge ("Alessia Leolini (born
    3 February 1997" -> "Alessia Leolini born 3 February 1997")."""
    keep, opened = [True] * len(text), []
    for i, ch in enumerate(text):
        if ch == "(":
            opened.append(i)
        elif ch == ")":
            if opened:
                opened.pop()
            else:
                keep[i] = False
    for i in opened:
        keep[i] = False
    return " ".join("".join(ch for ch, k in zip(text, keep) if k).split())


def node_texts(reading, doc):
    """Per-node mapping: [path, node, text] for every node of a reading; the root's text is
    the whole sentence as written."""
    return [[path, str(n), doc.text.strip() if not path else span_text(doc, n.span)] for path, n in reading.walk()]


# -- slots --------------------------------------------------------------------------------
ENTITY_TYPES = {"PERSON": "person", "NORP": "group", "ORG": "group", "GPE": "place", "LOC": "place", "FAC": "place",
                "DATE": "time", "TIME": "time", "CARDINAL": "amount", "QUANTITY": "amount", "MONEY": "amount",
                "PERCENT": "amount", "ORDINAL": "amount", "EVENT": "event", "WORK_OF_ART": "work", "LAW": "work"}
REFLEXIVES = {"itself", "himself", "herself", "themselves", "myself", "yourself", "ourselves"}
PERSON_WORDS = {"he", "she", "we", "i", "you", "him", "her", "us", "me", "who", "whom", "someone",
                "himself", "herself", "myself", "yourself", "ourselves",
                "everyone", "anyone", "nobody", "people", "man", "woman", "men", "women", "person", "child",
                "children", "boy", "girl", "father", "mother", "son", "daughter", "wife", "husband", "king", "queen"}
ROLE_ORDER = ["agent", "event", "state", "not", "hedge", "obligation", "future", "patient", "recipient", "attribute", "quality", "parts", "content",
              "subject", "source", "place", "time", "amount", "detail"]


# WordNet's noun categories for common nouns (the first, most frequent sense): villagers
# are people, a band is a group. Time and amount stay with the named-entity recognizer, so
# grounding still means a date or a number, not any word for a time.
LEXNAMES = {"noun.person": "person", "noun.group": "group", "noun.location": "place"}
_LEX = {}


def noun_category(lemma):
    if lemma not in _LEX:
        from nltk.corpus import wordnet as wn
        senses = wn.synsets(lemma, "n")
        _LEX[lemma] = LEXNAMES.get(senses[0].lexname(), "thing") if senses else "thing"
    return _LEX[lemma]


# "they" can be people, a team, fish or plant parts: the word alone doesn't say, so the slot
# stays untyped (the ambiguity is kept, not guessed)
UNTYPED = {"they", "them", "themselves"}


QUANTIFIERS = {"some", "many", "most", "all", "several", "none", "each", "both", "few", "any", "much", "half",
               "majority", "minority", "rest", "remainder", "number", "part", "bulk"}


def slot_type(tok):
    if tok.lower_ in UNTYPED:
        return ""
    # a partitive takes the type of the whole: "one of the contributors", "two of the matches",
    # "some of his friends"
    if tok.like_num or tok.ent_type_ in ("CARDINAL", "ORDINAL", "PERCENT", "QUANTITY") or tok.lower_ in QUANTIFIERS:
        whole = [p for c in tok.children if c.dep_ == "prep" and c.lower_ == "of" for p in c.children if p.dep_ == "pobj"]
        if whole:
            return slot_type(whole[0])
    if tok.ent_type_:
        return ENTITY_TYPES.get(tok.ent_type_, "thing")
    if tok.lower_ in PERSON_WORDS:
        return "person"
    if tok.like_num and tok.lower_ != "one":  # "one of the greatest" is a thing, not a count
        return "amount"
    if tok.pos_ == "NOUN":
        return noun_category(tok.lemma_.lower())
    return "thing"


def is_list(tok):
    """A noun heading three or more coordinated items: travel guides, novels, and science books."""
    n, t = 1, tok
    while True:
        nxt = [c for c in t.children if c.dep_ == "conj"]
        if not nxt:
            return n >= 3
        n, t = n + 1, nxt[0]


def roles(verb, own):
    """The clause's slots: (role, type, span) triples from the verb's dependents, deduplicated
    and in a fixed order (several places read as one place: the abstraction keeps the shape;
    their words are merged into one span)."""
    own_ids = {t.i for t in own}
    out = []

    def words(tok):
        """The words of tok's phrase that belong to this clause."""
        return {t.i for t in tok.subtree if t.i in own_ids}

    def add(role, type_, span):
        out.append((role, type_, frozenset(span)))

    def noun(role, tok):
        add(role, slot_type(tok), words(tok))
        for x in tok.children:
            if x.dep_ == "det" and x.lower_ == "no":
                add("not", "", {x.i})  # "involves no harmful radiation", "there is no indication"
        if is_list(tok):
            add("parts", "list", words(tok))
        # a time or place on one of the clause's nouns places the clause's event: "scored his
        # first goal on 9 December 2017"
        for c in tok.children:
            if c.dep_ == "prep":
                for p in c.children:
                    if p.dep_ == "pobj" and slot_type(p) in ("time", "place"):
                        add(slot_type(p), slot_type(p), words(c))

    heads = [verb] + [c for c in verb.children if c.dep_ == "xcomp" and c in own]
    for h in heads:
        # a preposition under an adverb counts as the verb's: "weighing up to 55 lbs"
        kids = list(h.children) + [p for a in h.children if a.dep_ == "advmod" for p in a.children if p.dep_ == "prep"]
        for c in kids:
            d = c.dep_
            if d == "nsubj" and h.i == verb.i:
                noun("agent", c)
            elif d == "nsubjpass" and h.i == verb.i:
                noun("patient", c)
            elif d == "expl":
                pass
            elif d == "agent":
                for p in c.children:
                    if p.dep_ == "pobj":
                        noun("agent", p)
            elif d == "dobj":
                noun("patient", c)
            elif d == "dative":
                # "gave him a book", or "create circumstances for each athlete" (the preposition
                # is marked: the recipient is its object)
                objs = [p for p in c.children if p.dep_ == "pobj"] if c.pos_ == "ADP" else [c]
                for o in objs:
                    noun("recipient", o)
            elif d in ("attr", "oprd"):
                noun("attribute", c)
            elif d == "acomp":
                add("quality", "", words(c))
            elif d == "neg":
                add("not", "", {c.i})
            elif d == "npadvmod" and slot_type(c) == "time":
                add("time", "time", words(c))
            elif d == "prep":
                objs = [p for p in c.children if p.dep_ in ("pobj", "pcomp")]
                if c.lower_ == "according":
                    add("source", slot_type(objs[0]) if objs else "thing", words(c))
                for p in objs:
                    t = "event" if p.dep_ == "pcomp" else slot_type(p)
                    if t in ("time", "place", "amount"):
                        add(t, t, words(c))
                    elif c.lower_ == "by" and t in ("person", "group"):
                        add("agent", t, words(c))
                    elif c.lower_ in ("to", "for") and t in ("person", "group"):
                        add("recipient", t, words(c))
                    else:
                        add("detail", t, words(c))
                    if p.dep_ == "pobj" and is_list(p):
                        add("parts", "list", words(p))
    # a coordinated verb with no subject shares its head's: "they travel back and establish
    # new patterns"; passive, the shared subject is what was acted on ("... and was released").
    # The subject's words belong to the head's clause, so the slot's span is the shared subject.
    if verb.dep_ == "conj" and not T.has_subject(verb):
        h = verb.head
        while h.dep_ == "conj" and not T.has_subject(h):
            h = h.head
        subj = next((c for c in h.children if c.dep_ in ("nsubj", "nsubjpass")), None)
        if subj is not None:
            add("patient" if T.passive(verb) else "agent", slot_type(subj), {t.i for t in subj.subtree})
    # "..., nor did Elias": a coordinated clause after "nor" is negated
    nors = [c for c in list(verb.head.children) + list(verb.children)
            if c.dep_ in ("cc", "preconj") and c.lower_ == "nor" and c.i < verb.i]
    if verb.dep_ == "conj" and nors:
        add("not", "", {nors[-1].i})
    # a clause modifying a noun with no subject of its own: the noun fills the gap
    # ("the greatest films ever made": films is what was made; "a man living in Paris")
    if verb.dep_ in ("acl", "relcl") and not T.has_subject(verb):
        role = {"VBN": "patient", "VBG": "agent", "VB": "detail"}.get(verb.tag_)
        if role:  # "ways to hunt": the noun is what the act is about
            # the noun with the words before it ("Alessia Leolini (born ...)": the whole name)
            noun_words = {verb.head.i} | {t.i for c in verb.head.lefts for t in c.subtree}
            add(role, slot_type(verb.head), noun_words)
    for t in own:
        if t.dep_ == "aux" and t.tag_ == "MD" and t.lower_ in T.HEDGES:
            add("hedge", "", {t.i})
        elif t.dep_ == "aux" and t.tag_ == "MD" and t.lower_ in T.OBLIGATIONS:
            add("obligation", "", {t.i})
        elif t.dep_ == "aux" and t.tag_ == "MD" and t.lower_ in ("will", "'ll"):
            add("future", "", {t.i})
    # "black holes exist", "the problem remains": a state verb with nothing else attached
    # describes a state by itself
    if (verb.lemma_.lower() in T.STATIVE - {"be", "have"} and {r for r, _, _ in out} <= {"agent"}
            and not any(c.dep_ in ("ccomp", "xcomp", "csubj") for c in verb.children)):
        add("state", "", {verb.i})
    merged = {}
    for role, type_, span in out:
        merged[(role, type_)] = merged.get((role, type_), frozenset()) | span
    return sorted(((r, t, s) for (r, t), s in merged.items()), key=lambda rts: (ROLE_ORDER.index(rts[0]), rts[1]))


# -- clauses ------------------------------------------------------------------------------
CLAUSE_DEPS = {"conj", "advcl", "relcl", "ccomp", "csubj", "csubjpass", "acl", "parataxis"}


def is_clause(tok):
    if tok.dep_ == "ROOT":
        return True
    if T.purpose_infinitive(tok):
        return True
    # a verb with its own subject is a clause wherever the parse attaches it ("..., and he was
    # a star" attached to an adjective): otherwise its words vanish into another clause
    if tok.pos_ in ("VERB", "AUX") and tok.dep_ not in ("aux", "auxpass") and any(
            c.dep_ in ("nsubj", "nsubjpass") for c in tok.children):
        return True
    if tok.dep_ not in CLAUSE_DEPS or tok.pos_ not in ("VERB", "AUX"):
        return False
    if tok.dep_ == "conj":
        return is_clause(tok.head)
    return True


def clause_of(tok):
    t = tok
    while not is_clause(t):
        t = t.head
    return t


def phrase_at(toks, i, words):
    return tuple(t.lower_ for t in toks[i:i + len(words)]) == words


def advcl_relations(sub):
    marks = [c for c in sub.children if c.dep_ == "mark"] + [c for c in sub.children if c.dep_ == "advmod" and c.lower_ in ("when", "whenever")]
    if marks:
        words = " ".join(m.lower_ for m in sorted(marks, key=lambda m: m.i))
        for key in (words, marks[0].lower_):
            if key in T.MARKS:
                return T.MARKS[key]
        if marks[0].lower_ == "in" or (marks[0].lower_ == "so" and len(marks) > 1):
            return [T.PURPOSE]
        return [T.ELABORATE]
    if any(c.dep_ == "aux" and c.lower_ == "to" for c in sub.children):
        return [T.PURPOSE]
    if sub.tag_ in ("VBG", "VBN"):  # Founded in 1850, the company ...
        return [T.ELABORATE, T.SEQUENCE]
    return [T.ELABORATE]


def conj_relations(sub, head):
    # the coordinator in front of this verb; one after it ("..., but did not publish anything
    # and did not submit") belongs to the next coordination
    ccs = [c for c in list(head.children) + list(sub.children) if c.dep_ == "cc" and c.i < sub.i]
    word = max(ccs, key=lambda c: c.i).lower_ if ccs else ""
    rels = list(T.CONJUNCTIONS.get(word, [T.ELABORATE]))
    if word in ("and", "") and T.tense(head) == "past" and T.tense(sub) == "past":
        rels.append(T.SEQUENCE)
    return rels


def same_entity(a, b):
    """Two tokens of one named entity ("March 16, 2016"): a parse that links them as an
    apposition is reading the inside of a name, not two noun phrases."""
    return any(e.start <= a.i < e.end and e.start <= b.i < e.end for e in a.doc.ents)


def modifier_relations(sub):
    """A relative or reduced relative clause: set off by a comma it adds detail, without one
    it picks out which thing is meant."""
    first = min(t.i for t in sub.subtree)
    doc = sub.doc
    commaed = (first > 0 and doc[first - 1].text in (",", "(", "—", "–")) or doc[first].text in ("(", "—", "–", ",")
    # "In order to create ...": parsed as a clause modifying the noun "order", it is a purpose
    if sub.head.lower_ == "order" and sub.head.head.lower_ == "in":
        return [T.PURPOSE]
    # a name already says which one: "West Germany where he worked" adds detail
    named = sub.head.pos_ == "PROPN"
    return [T.ELABORATE] if commaed or named else [T.DISAMBIGUATE]


def wrap(mains, rels, others):
    out = []
    for m in mains:
        for (kind, main_role, other_role, other_first) in rels:
            for o in others:
                kids = ((other_role, o), (main_role, m)) if other_first else ((main_role, m), (other_role, o))
                out.append(Node(kind, kids))
    return out


def cap(nodes, stats):
    nodes = list(dict.fromkeys(nodes))
    if len(nodes) > MAX_READINGS:
        stats["capped"] += 1
        nodes = nodes[:MAX_READINGS]
    return nodes


def clause_readings(verb, stats, is_root=False):
    """Every reading of the clause headed by verb, with its subordinate clauses."""
    doc = verb.doc
    if verb.pos_ not in ("VERB", "AUX"):
        return []  # a fragment (a citation, a URL, a title) reads as nothing, cue words or not
    own = sorted((t for t in verb.subtree if clause_of(t).i == verb.i), key=lambda t: t.i)
    subs = [c for t in own for c in t.children if c.i != verb.i and is_clause(c) and c.dep_ != "ROOT"]
    slots = roles(verb, own)
    own_ids = {t.i for t in own}
    contents = [s for s in subs if s.dep_ in ("ccomp", "csubj", "csubjpass")]
    kinds, action = T.core(verb)
    agent_type = next((t for r, t, _ in slots if r == "agent"), "")
    kinds = kinds + [k for k in T.lexical(verb, own, agent_type, {t for _, t, _ in slots}) if k not in kinds]
    if not kinds:
        return []
    base = [(r, slot(t, s)) for r, t, s in slots]
    if action:  # the event is the verb with its auxiliaries ("had been rewriting")
        verb_group = {verb.i} | {c.i for c in verb.children if c.dep_ in ("aux", "auxpass") and c.i in own_ids}
        base.insert(next((i for i, (r, _) in enumerate(base) if r != "agent"), len(base)), ("event", slot("", verb_group)))
    # a sentence-initial marker relating the sentence to its context ("However", "As a result")
    context = None
    if is_root:
        start = [t for t in doc if not t.is_punct][:4]
        for words, r in T.CONTEXT:
            # "As a result of X, ...", "In addition to her work, ..." name their own object; only
            # "As a result, ...", "In addition, ..." point to the context
            followed_by_of = len(start) > len(words) and start[len(words)].lower_ in ("of", "to")
            if phrase_at(start, 0, words) and clause_of(start[0]).i == verb.i and not followed_by_of:
                context = (r, {t.i for t in start[:len(words)]})
                break
    # the clause node covers the clause's own words (not a context marker: that is the
    # context relation's); its content clauses add theirs
    clause_span = {t.i for t in own if not t.is_punct} - (context[1] if context else set())
    # content clauses are parts of the node (what was claimed); each has readings of its own
    content_options = [[(("content" if s.dep_ == "ccomp" else "subject"), r) for r in clause_readings(s, stats)] for s in contents]
    if any(not opts for opts in content_options):
        return []  # what was said reads as nothing: so does the saying (no reading may skip a part)
    nodes = []
    for combo in itertools.product(*content_options):
        for k in kinds:
            nodes.append(Node(k, base + list(combo), span=clause_span))
    nodes = cap(nodes, stats)

    def phrase_words(tok):
        return {t.i for t in tok.subtree if t.i in own_ids}

    # phrases inside the clause relate it to a noun phrase (a slot: the phrase and its object)
    for i in range(len(own)):
        for words, rels in T.PHRASES:
            if phrase_at(own, i, words):
                matched = own[i:i + len(words)]
                filler = {t.i for t in matched} | phrase_words(matched[-1])
                nodes = cap(wrap(nodes, rels, [slot("thing", filler)]), stats)
    for t in own:
        for c in t.children:
            if c.dep_ == "prep" and c.lower_ in ("than", "like") and any(p.dep_ == "pobj" for p in c.children):
                # "like" after a noun gives an example ("trains like the Orient Express");
                # after a verb or adjective it compares ("sings like a bird")
                example = c.lower_ == "like" and t.pos_ in ("NOUN", "PROPN", "PRON")
                rels = [T.EXAMPLE_GROUNDS, T.EXAMPLE_ELABORATES] if example else [T.COMPARE]
                nodes = cap(wrap(nodes, rels, [slot("thing", phrase_words(c))]), stats)
            if c.dep_ == "appos" and not same_entity(c, t) and c.lower_ not in REFLEXIVES:
                rels = [T.DISAMBIGUATE] if c.pos_ == "PROPN" or c.ent_type_ else [T.ELABORATE]
                nodes = cap(wrap(nodes, rels, [slot(slot_type(c), phrase_words(c))]), stats)
    # subordinate clauses, in sentence order
    for s in sorted((s for s in subs if s not in contents), key=lambda s: s.i):
        if s.lower_ == "according":  # "According to al-Tabari, ...": the clause has a source
            objs = [p for c in s.children if c.dep_ == "prep" for p in c.children if p.dep_ == "pobj"]
            source = slot(slot_type(objs[0]) if objs else "thing", {t.i for t in s.subtree})
            nodes = cap(wrap(nodes, [T.SOURCED], [source]), stats)
            continue
        others = clause_readings(s, stats)
        if not others:
            return []  # a part that reads as nothing: no valid reading of the whole
        if s.dep_ == "advcl":
            rels = advcl_relations(s)
        elif s.dep_ in ("relcl", "acl"):
            rels = modifier_relations(s)
        elif s.dep_ == "conj":
            rels = conj_relations(s, verb)
        elif s.dep_ == "xcomp":
            rels = [T.PURPOSE]
        else:
            rels = [T.ELABORATE]
        nodes = cap(wrap(nodes, rels, others), stats)
    # the context relation wraps the whole clause (the slot's words are the marker; the
    # context itself is the previous sentence)
    if context:
        nodes = cap(wrap(nodes, [context[0]], [slot("context", context[1])]), stats)
    return [n for n in nodes if valid(n)]


# -- validity -----------------------------------------------------------------------------
def valid(node):
    """Every gerund node has the parts it needs (rules over the abstraction)."""
    if node.kind == "slot":
        return True
    roles_ = {r for r, _ in node.kids}
    types = {k.value for _, k in node.kids if k.kind == "slot"}
    clause = "main" not in roles_ and not any(k.kind != "slot" and r not in ("content", "subject") for r, k in node.kids)
    if clause:
        if node.kind == "describing" and not roles_ - {"agent", "event", "not", "hedge", "obligation", "future"}:
            return False  # describes nothing
        if node.kind == "narrating" and not roles_ & {"agent", "patient"}:
            return False  # an event with no one taking part
        if node.kind == "grounding" and not (types & T.GROUNDING_TYPES or "source" in roles_):
            return False
        if node.kind == "claiming" and not roles_ & {"content", "hedge", "obligation", "future", "attribute", "quality", "patient"}:
            return False  # claims nothing
    return all(valid(k) for _, k in node.kids)


# A line cut off by the corpus's sentence splitter at an abbreviation ("Colorado Springs U.",
# "directed by I.", "p.") is part of a sentence, not a sentence: it reads as nothing.
TRUNCATED = re.compile(r"((?:^|[\s(])\d{1,2}|\b[A-Z]|\b(?:p|pp|i|e|vs|St|Dr|Mr|Mrs|Ms|Jr|Sr|No|no|Vol|Inc|Co|Ltd|Bros|ca|cf|al))\.$")


def truncated(text):
    """Cut at the end (an abbreviation) or at the start (a lowercase letter or punctuation:
    "between the years ...", ", the air traffic controller ...")."""
    text = text.strip()
    return (not text or bool(TRUNCATED.search(text)) or text[0].islower() or text[0] in ",;:.)](["
            or bool(re.match(r"\d+\)", text))  # "4) came out in April 2004": a list number
            or bool(re.match(r"\d+ (?:km|m|mi|kg|cm|mm|ft|in|lb|lbs)\b", text))  # "9 km circuit": cut from "4.9 km"
            or bool(re.search(r"[A-Za-z]\d\.$", text))  # "the guideline states that PM2.": cut from "PM2.5"
            or bool(re.search(r"\s[a-z]\.$", text))  # "available at 7:30 a.": cut from "a.m."
            or bool(re.match(r"\d+,? (?:In|The|A|An|He|She|It|They|On|At|After|During|This|His|Her|[A-Z][a-z]+ \d)\b", text))
            or text.endswith(" ."))  # "1082, He died ...", "63 In 1992, ...": a leftover reference number;
                                     # "on display at the .": a dropped word


def determine_doc(doc, stats=None):
    """The valid readings of a parsed sentence (several roots read as one elaborating chain)."""
    stats = stats if stats is not None else Counter()
    if truncated(doc.text):
        return []
    if len(doc) > MAX_TOKENS:
        return []  # a list or table run together by a failed sentence split, not a sentence
    roots = [s.root for s in doc.sents]
    readings = None
    for r in roots:
        rs = clause_readings(r, stats, is_root=True)
        if not rs:
            return []
        readings = rs if readings is None else cap(wrap(readings, [T.ELABORATE], rs), stats)
    return readings or []


def why_undetermined(doc):
    """For a sentence with no valid reading: why, for the first clause (deepest first) that
    reads as nothing. 'fragment' = no verb at the root; 'no gerund' = no template matched;
    'invalid' = templates matched but every reading broke a validity rule."""
    stats = Counter()
    clauses = sorted((t for t in doc if is_clause(t)), key=lambda t: -sum(1 for _ in t.ancestors))
    for c in clauses:
        if c.lower_ == "according" or clause_readings(c, stats, is_root=c.dep_ == "ROOT"):
            continue
        own = [t for t in c.subtree if clause_of(t).i == c.i]
        kinds, _ = T.core(c)
        slots = roles(c, own)
        if c.pos_ not in ("VERB", "AUX"):
            return "fragment", c
        agent = next((t for r, t, _ in slots if r == "agent"), "")
        lex = T.lexical(c, own, agent, {t for _, t, _ in slots})
        if not kinds and not lex:
            return f"no gerund ({c.dep_}, tense {T.tense(c)})", c
        if any(clause_readings(s, stats) == [] for t in own for s in t.children if s.i != c.i and is_clause(s)):
            continue  # a part of it failed; that part is reported on its own
        return f"invalid {'/'.join(kinds + lex)} with roles {[r for r, _, _ in slots]}", c
    return "unknown", doc[0]


# The parser: en_core_web_trf (a transformer, on the GPU when there is one); set
# TEXT_PARSER=en_core_web_sm for the small model. The small model's named-entity errors were
# the most common reason a mapping wasn't confident (TEXT_EMBEDDING.md).
PARSER = os.environ.get("TEXT_PARSER", "en_core_web_trf")
_NLP = None


def nlp():
    global _NLP
    if _NLP is None:
        import spacy
        spacy.prefer_gpu()
        _NLP = spacy.load(PARSER)
    return _NLP


def determine(text, stats=None):
    return determine_doc(nlp()(text), stats)


def determine_many(texts, stats=None, batch_size=256):
    """(doc, readings) per text."""
    for doc in nlp().pipe(texts, batch_size=batch_size):
        yield doc, determine_doc(doc, stats)


# -- run over a corpus sample ---------------------------------------------------------------
def sample(path, n):
    """n sentences spread evenly through the file (read by byte offsets, no full load)."""
    size = os.path.getsize(path)
    out = []
    with open(path, "rb") as f:
        for k in range(n):
            f.seek(size * k // n)
            if k:
                f.readline()
            line = f.readline().decode("utf-8", "replace").strip()
            if line:
                out.append(line)
    return out


def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="E:/E/parquet/a.txt")
    ap.add_argument("--n", type=int, default=2000)
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "results"), exist_ok=True)
    tag = f"{os.path.splitext(os.path.basename(args.file))[0]}_{args.n}"
    stats, by_reading, gerund_count, readings_hist, undetermined = Counter(), {}, Counter(), Counter(), []
    sentences = sample(args.file, args.n)
    with open(os.path.join(here, "results", f"determine_{tag}.jsonl"), "w", encoding="utf-8") as out:
        for doc, readings in determine_many(sentences, stats):
            text = doc.text
            # per reading, the per-node mapping: [path, node, the words it covers]
            out.write(json.dumps({"text": text, "readings": [str(r) for r in readings],
                                  "nodes": [node_texts(r, doc) for r in readings]}) + "\n")
            readings_hist[min(len(readings), 10)] += 1
            if not readings:
                undetermined.append(text)
                continue
            for g in {g for r in readings for g in r.gerunds()}:
                gerund_count[g] += 1
            key = " | ".join(sorted(str(r) for r in readings))
            by_reading.setdefault(key, []).append(text)
    n = len(sentences)
    lines = [f"Sentences: {n} from {args.file}",
             f"Determined (at least one valid reading): {n - len(undetermined)} ({(n - len(undetermined)) / n:.1%})",
             f"Readings per sentence (10 = 10 or more): {dict(sorted(readings_hist.items()))}",
             f"Readings capped at {MAX_READINGS}: {stats['capped']} times",
             f"Distinct abstractions: {len(by_reading)}; shared by 2+ sentences: {sum(len(v) > 1 for v in by_reading.values())}",
             "", "Sentences with each gerund in some reading:"]
    lines += [f"  {g}: {c}" for g, c in gerund_count.most_common()]
    lines += ["", "Most shared abstractions (all readings, | between them):"]
    for key, texts in sorted(by_reading.items(), key=lambda kv: -len(kv[1]))[:15]:
        lines += [f"  [{len(texts)}] {key}", *[f"      e.g. {t}" for t in texts[:2]]]
    lines += ["", "Undetermined examples:"] + [f"  {t}" for t in undetermined[:25]]
    report = "\n".join(lines)
    with open(os.path.join(here, "results", f"determine_{tag}.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(report)


if __name__ == "__main__":
    main()
