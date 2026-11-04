"""Hand-built reference programs, as operation trees (PoC step 1, rebuilt).

Theories:
- parallel strings: two sequences read or spliced at the same positions (simple: the
  color line; full: the editor's styled insert and delete);
- pub/sub: a collection appended to in one function, iterated with calls in another.

ALTERNATIVES are other honest ways to write a domain's program, used as extra seeds
for seeded search. They're hand-written too, so variety is measured against them.
"""
from grammar import (FN, INT, LIST, NONE, PAIR, STR, DICT, accumulating, appending, binding, block,
                     branching, calling, concatenating, constant, creating_empty, func, indexing, iterating_over_items,
                     iterating_over_positions, iterating_together, iterating_with_positions, looking_up,
                     module, name, negating, pairing, removing, returning, slicing_before, slicing_from,
                     storing, testing_membership, wrapping)

PAIRS = LIST(PAIR(STR, STR))


def color_line_with(loop):
    """The color line's shape around a given loop: bind an empty result, loop, return it."""
    return module(state=[], funcs=[
        func("f1", ["v1", "v2"], FN([STR, STR], PAIRS), block(
            binding(name("v3"), creating_empty(PAIRS)),
            loop,
            returning(name("v3")),
        )),
    ])


def color_line():
    """Parallel strings, simple domain: a read-only line and its meta-line of colors.
    f1(content, meta) pairs each character with its color, position by position."""
    return color_line_with(iterating_over_positions(name("v4"), name("v1"), block(
        appending(name("v3"), pairing(indexing(name("v1"), name("v4")), indexing(name("v2"), name("v4")))),
    )))


def color_line_zip():
    """iterating together over content and meta: pairing them."""
    return color_line_with(iterating_together(name("v4"), name("v5"), name("v1"), name("v2"), block(
        appending(name("v3"), pairing(name("v4"), name("v5"))),
    )))


def color_line_enumerate():
    """iterating with positions over content: pairing each character with meta at its position."""
    return color_line_with(iterating_with_positions(name("v4"), name("v5"), name("v1"), block(
        appending(name("v3"), pairing(name("v5"), indexing(name("v2"), name("v4")))),
    )))


def color_line_accumulating():
    """iterating over positions, accumulating wrapped pairs instead of appending."""
    return color_line_with(iterating_over_positions(name("v4"), name("v1"), block(
        accumulating(name("v3"), wrapping(pairing(indexing(name("v1"), name("v4")), indexing(name("v2"), name("v4"))))),
    )))


def splicing(line, at, text):
    """concatenating(slicing before line at, text, slicing from line at): an insert."""
    return concatenating(slicing_before(name(line), name(at)), name(text), slicing_from(name(line), name(at)))


def cutting(line, start, end):
    """concatenating(slicing before line at start, slicing from line at end): a delete."""
    return concatenating(slicing_before(name(line), name(start)), slicing_from(name(line), name(end)))


def styled_edit():
    """Parallel strings, full domain (two of the editor's operations): content v1 and
    styles v2 are edited at the same positions, so they stay the same length.
    f1(at, text, styles) inserts; f2(start, end) deletes."""
    return module(state=[binding(name("v1"), constant("")), binding(name("v2"), constant(""))], funcs=[
        func("f1", ["v3", "v4", "v5"], FN([INT, STR, STR], NONE), block(
            binding(name("v1"), splicing("v1", "v3", "v4")),
            binding(name("v2"), splicing("v2", "v3", "v5")),
        )),
        func("f2", ["v3", "v4"], FN([INT, INT], NONE), block(
            binding(name("v1"), cutting("v1", "v3", "v4")),
            binding(name("v2"), cutting("v2", "v3", "v4")),
        )),
    ])


def pubsub():
    """Pub/sub, simple domain: handlers per topic in v1.
    f1(topic, handler) subscribes, f2(topic, handler) unsubscribes, f3(topic, message) publishes."""
    handler = FN([STR], NONE)
    topics = DICT(STR, LIST(handler))
    return module(state=[binding(name("v1"), creating_empty(topics))], funcs=[
        func("f1", ["v2", "v3"], FN([STR, handler], NONE), block(
            branching(negating(testing_membership(name("v2"), name("v1"))), block(
                storing(name("v1"), name("v2"), creating_empty(LIST(handler))),
            )),
            appending(looking_up(name("v1"), name("v2")), name("v3")),
        )),
        func("f2", ["v2", "v3"], FN([STR, handler], NONE), block(
            removing(looking_up(name("v1"), name("v2")), name("v3")),
        )),
        func("f3", ["v2", "v4"], FN([STR, STR], NONE), block(
            branching(testing_membership(name("v2"), name("v1")), block(
                iterating_over_items(name("v5"), looking_up(name("v1"), name("v2")), block(
                    calling(name("v5"), name("v4")),
                )),
            )),
        )),
    ])


REFERENCES = {"color_line": color_line, "styled_edit": styled_edit, "pubsub_chat": pubsub}  # keys are domains
ALTERNATIVES = {"color_line": [color_line_zip, color_line_enumerate, color_line_accumulating]}


def seeds(domain):
    return [REFERENCES[domain]()] + [v() for v in ALTERNATIVES.get(domain, [])]
