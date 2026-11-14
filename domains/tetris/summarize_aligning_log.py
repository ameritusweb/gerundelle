"""Summarize trace_aligning_<slice>.log: piece_alignment's holder history per 1000 slices, and the sub-want log after 13000."""
import ast
import collections
import sys

text = open(sys.argv[1], encoding="utf-8").read().splitlines()
row = next(l for l in text if l.startswith("territory row piece_alignment:"))
d = eval(row[len("territory row piece_alignment:"):].strip(), {"frozenset": frozenset, "set": set, "inf": float("inf"), "nan": float("nan")})
print({k: v for k, v in d.items() if k not in ("history", "claims", "seen_states", "held_states")})
print("seen_states:", d.get("seen_states"), "| held_states:", d.get("held_states"))
hist = d["history"]
by = collections.defaultdict(collections.Counter)
for t, h in hist:
    by[t // 1000 * 1000][h] += 1
print("holder changes per 1000 slices:")
for b in sorted(by):
    print(f"  {b:6d}: {dict(by[b])}")
print("last 12 changes:", hist[-12:])
for l in text:
    if l.startswith(("dormant", "slots in", "open slots", "world state", "meta relevant", "failed_subs", "goal")):
        print(l[:400])
i = text.index("sub_log after 13000 (every entry):")
ents = [ast.literal_eval(l.strip()) for l in text[i + 1:] if l.startswith("   (")]
print(f"\nsub_log after 13000: {len(ents)} entries")
c = collections.Counter((e[0] // 2000 * 2000, e[2]) for e in ents)
for b in sorted({k[0] for k in c}):
    print(f"  {b:6d}: " + ", ".join(f"{k} {c[(b, k)]}" for k in ("set", "met", "dropped", "yielded", "kept", "restored", "tried", "bridged") if c[(b, k)]))
sets = collections.Counter(e[1] for e in ents if e[2] == "set" and e[0] > 14000)
print("wants set after 14000:", sets.most_common(12))
print("last 15 entries:", ents[-15:])
