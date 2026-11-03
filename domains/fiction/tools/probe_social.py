"""Read back every generated social line (people, questions, answers, instructions, truths) before a run."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import social  # noqa: E402
from probe import skeletons  # noqa: E402

texts = []
for key, card in social.CARDS.items():
    L = social.lines(card)
    a = card["actor"]
    texts += list(L["people"].values()) + list(L["rival_wants"].values())
    texts += [f'"{q}" {a} asked Ben.' for q in L["asks"].values()]
    texts += [f'"{s}," Ben said.' for s in L["says"].values()]
    texts += [f'"{s}," Leo said.' for s in L["instructs"].values()]
    texts += [f"But Leo knew that {t}." for t in L["truths"].values()]
    texts += [f"{a} realized that Ben had been right.", f"Leo did not want {social.OBJ[card['pronoun']]} to open it.",
              f"{a} remembered how Ben had opened {card['thing']}."]
bad = 0
for text, skels, why in skeletons(sorted(set(texts))):
    if not skels:
        bad += 1
        print("UNDETERMINED", text, why)
print(len(set(texts)), "lines,", bad, "undetermined")
