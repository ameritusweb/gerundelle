"""Rulesets (PoC step 2, rebuilt): base rules + a theory's core facets + a domain's must-haves.

Validity is base rules plus the theory's core facets. The domain is defined by its
behavior spec (specs.py); MUSTS are weak necessary conditions kept only so a search can
prune early (POC.md: decisions after the assumptions audit). FACETS (rules.FACETS) give
the labels; only their core members are validity rules.
"""
from dataflow import no_dead_code
from rules import (FACETS, calls_in, must_loop, must_write_all_state, no_aliases, no_built_access, no_char_index, no_churn,
                   no_built_comparisons, no_double_constants, no_empty_slices, no_insert_at_length, no_literal_destructuring,
                   no_measuring_built, no_self_concat, no_slice_of_slice, no_unread_loop_names,
                   no_constant_conditions, no_dead_locals, no_disguised_constants, no_edit_while_iterating,
                   no_empty_blocks, no_len_index, no_literal_access, no_loop_var_writes, no_overwritten_stores,
                   no_param_writes, no_recursion, no_self_assign, no_single_pass_loops, no_temp_edits,
                   no_trailing_return, no_trivial_ops, no_unreachable, returns_value, uses_params, uses_state,
                   writes_state_in)

BASE = [uses_params, returns_value, no_dead_locals, uses_state, no_self_assign,
        # hygiene and audit rounds 1-6 from poc/
        no_unreachable, no_empty_blocks, no_literal_access, no_trivial_ops, no_recursion, no_param_writes,
        no_constant_conditions, no_temp_edits, no_loop_var_writes, no_disguised_constants, no_churn,
        no_char_index, no_overwritten_stores, no_len_index, no_edit_while_iterating, no_single_pass_loops,
        no_trailing_return,
        # POC3 audit rounds 1-6
        no_aliases, no_empty_slices, no_slice_of_slice, no_self_concat, no_measuring_built, no_built_access,
        no_literal_destructuring, no_double_constants, no_unread_loop_names, no_built_comparisons, no_insert_at_length,
        # load-bearing pressure (dataflow.py)
        no_dead_code]

THEORIES = {theory: [fc for fc in facets if fc.core] for theory, facets in FACETS.items()}

# domain -> (theory, the domain's must-haves)
DOMAINS = {
    "color_line": ("parallel_strings", [must_loop]),
    "styled_edit": ("parallel_strings", [must_write_all_state]),
    "pubsub_chat": ("pubsub", [writes_state_in("f1"), writes_state_in("f2"), calls_in("f3")]),
}


def ruleset(domain):
    theory, musts = DOMAINS[domain]
    return BASE + THEORIES[theory] + musts


def judge(rules, tree):
    """{rule name: True, False or None}."""
    import rules as _rules
    if len(_rules._FINISHED) > 10_000:
        _rules._FINISHED.clear()
    return {r.__name__: r(tree) for r in rules}


def verdict(results):
    """False if any rule failed (final), True if all passed, else None (undecided)."""
    vals = list(results.values())
    return False if False in vals else True if all(v is True for v in vals) else None
