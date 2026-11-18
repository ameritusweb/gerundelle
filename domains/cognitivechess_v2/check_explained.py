"""Params.explained_needs on the game-12 mind (the user, 2026-11-17: "break the conflation, and figure out when it's OK to have it
captured"). For the wants it set (sub_log) and each push its record knows brought one (makers), the push's needs with the switch off
and on. Expectations written before the run:
  X1 (on): no need is a piece of its own captured unless the record explains it (held at every success, absent at some failure).
  X2: the needs shrink from hundreds of facts to a few.
python -X utf8 check_explained.py"""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
from chessduel import fresh_seat
from rung4p import load_run

a, w0, _, _ = load_run("checkpoints/rung4p_full_s0_g12.pkl")
w = fresh_seat(a, True, old=w0, half_moves=300)
wants = [g for g, n in Counter(g for t, g, k in a.sub_log if k == "set" and not g.startswith("all:")).most_common(40)]
sizes = {False: [], True: []}
own_captured = {False: Counter(), True: Counter()}
explained_captures = []
pairs = 0
for want in wants:
    for inv in a.makers(want)[:5]:
        pairs += 1
        for on in (False, True):
            a.mind.p.explained_needs = on
            needs = a.needs(inv, want)
            sizes[on].append(len(needs))
            caps = [f for f in needs if f.startswith("white_") and f.endswith("_captured")]
            own_captured[on][len(caps) > 0] += 1
            if on and caps:
                explained_captures.append((want, inv[0], caps))
a.mind.p.explained_needs = False
avg = lambda xs: sum(xs) / max(len(xs), 1)
print(f"wants {len(wants)}, (want, push) pairs {pairs}")
print(f"needs per push, off: mean {avg(sizes[False]):.1f}, max {max(sizes[False], default=0)} | on: mean {avg(sizes[True]):.1f}, "
      f"max {max(sizes[True], default=0)}")
print(f"pairs whose needs include a piece of its own captured, off: {own_captured[False][True]}, on: {own_captured[True][True]}")
for want, label, caps in explained_captures[:5]:
    print(f"   explained on: {label} for {want}: {caps}")
x1 = all(all(f in a.explained(inv, want) for f in caps) for want, _, caps in explained_captures)
print(f"X1: {'met' if x1 else 'NOT met'} (every own capture left among the needs is explained)")
print(f"X2: {'met' if avg(sizes[True]) < 10 and avg(sizes[False]) > 50 else 'NOT met'}")
