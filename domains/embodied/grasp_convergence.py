"""Constraint convergence on the copied Gerundelle mind (the user, 2026-10-28): many grasps work and none
is distinctive; failures reveal constraints; the successful grasp is noticed among the attempts as where
the constraints converge. Here: does the attempt the constraints converge on win the top, as constraints
are revealed one at a time, with support off, from resolved bindings, or from candidate bindings?

The attempts are lived ones (the hand made them), each tagged with the constraints it happened to clear.
A constraint is a molecule tagged "constraint" whose open site is what clearing it looks like.

    python -X utf8 grasp_convergence.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "gerundelle", "molecules"))
from molecules import Mind, Params, clause  # noqa: E402

# what each constraint asks, in the order failures revealed them
CONSTRAINTS = [
    ("hot", "the body is hot: the fingers must not wrap it"),          # the burn on the first try
    ("bottle", "the bottle stands to the left: come from the right"),  # the knocked bottle
    ("spill", "it is full: it must not tilt"),                         # the spill
    ("chip", "the rim is chipped: keep clear of it"),                  # the cut lip
    ("span", "the hand's span: the fingers must go through"),          # the pinch that slipped
]

# the attempts the hand has made, and what each happened to clear
ATTEMPTS = {
    "handle_right_through": {"hot", "bottle", "spill", "chip", "span"},   # the one they converge on
    "handle_left_through": {"hot", "spill", "chip", "span"},
    "body_wrap_right": {"bottle", "spill", "chip", "span"},
    "rim_pinch_right": {"hot", "bottle", "span"},
    "handle_right_pinch": {"hot", "bottle", "chip"},
}


def molecules(revealed, extra=()):
    atts = [clause(f"attempt:{a}", tags=("attempt",) + tuple(f"clears:{c}" for c in cleared))
            for a, cleared in ATTEMPTS.items()]
    cons = [clause(f"constraint:{c}", tags=("constraint",), sites=(f"clears:{c}",)) for c in list(revealed) + list(extra)]
    return atts + cons


def run(mode, revealed, extra=(), ticks=6):
    mind = Mind(Params(support=mode, sov=False, meta=False, closure=False))
    tops, bids = [], {}
    for _ in range(ticks):
        rec = mind.tick(molecules(revealed, extra))
        top = [i for i in rec["levels"][-1]["winners"] if i.startswith("attempt:")]
        tops.append(top)
        bids = {i[8:]: round(b, 2) for i, b in rec["levels"][0]["bids"].items() if i.startswith("attempt:")}
    return tops, bids


def leader(bids):
    best = max(bids.values())
    return [a for a, b in bids.items() if b == best]


if __name__ == "__main__":
    names = [c for c, _ in CONSTRAINTS]
    stages = [names[:k] for k in range(len(names) + 1)]
    for mode in (None, "resolved", "candidates"):
        print(f"\n=== support: {mode}")
        for revealed in stages:
            tops, bids = run(mode, revealed)
            lead = leader(bids)
            mark = "  <- converged" if lead == ["handle_right_through"] else ""
            print(f"  revealed {len(revealed)} {revealed!s:44}  top at the last tick: {[t[8:] for t in tops[-1]]}")
            print(f"      level-0 bids: {bids}   leader: {lead}{mark}")
    # over-constrained: a constraint no attempt clears (the handle must not be touched: it is wet)
    print("\n=== over-constrained (add 'dry': no attempt clears it)")
    for mode in ("resolved", "candidates"):
        tops, bids = run(mode, names, extra=("dry",))
        print(f"  {mode:10} leader: {leader(bids)}   bids: {bids}")
