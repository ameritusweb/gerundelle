"""Theory coverage from a passage's exact gerund labels. Plain functions taken unchanged from the structural judge, which
itself needs torch and trained models; this measure needs neither."""
import re

# Theory signatures as top-level gerund sequences (TEXT_THEORIES.md). "a|b" = either;
# "expressing_*" = any emotional gerund. A first cut: order only, no dependency constraints.
THEORIES = {
    "claim-evidence-warrant": ["claiming", "grounding", "explaining"],
    "problem-solution-result": ["describing", "explaining", "grounding"],
    "concession-rebuttal": ["claiming", "grounding", "contrasting", "claiming"],
    "concept-explanation": ["claiming", "decomposing", "elaborating", "grounding"],
    "analogy-bridge": ["describing", "describing", "comparing", "explaining"],
    "compare-contrast": ["describing", "describing", "contrasting", "disambiguating", "claiming"],
    "narrative-arc": ["narrating", "narrating", "expressing_*", "narrating"],
    "lament": ["expressing_grief", "grounding", "expressing_longing", "expressing_hope|expressing_resignation"],
    "apology-repair": ["expressing_remorse", "grounding", "expressing_humility", "expressing_resolve"],
    "encouragement": ["expressing_empathy", "grounding", "expressing_encouragement", "expressing_determination"],
    "persuasion-arc": ["expressing_urgency", "claiming", "grounding", "expressing_resolve", "claiming"],
    "defiance-to-resolve": ["expressing_anger|expressing_defiance", "grounding", "expressing_determination", "claiming"],
    "gratitude": ["describing", "expressing_gratitude", "grounding", "expressing_humility"],
    "surrender-to-acceptance": ["expressing_restlessness", "expressing_resignation", "expressing_surrender", "grounding",
                                "expressing_calm|expressing_serenity"],
    "layered-detail": ["claiming", "elaborating", "qualifying", "grounding", "elaborating"],
    "diagnostic": ["describing", "decomposing", "disambiguating", "claiming", "grounding"],
    "deliberation": ["describing", "comparing", "contrasting", "judging", "claiming"],
    "testimony": ["narrating", "expressing_*", "grounding", "claiming"],
    "instruction": ["claiming", "decomposing", "elaborating", "grounding"],
    "wonder-to-understanding": ["expressing_wonder|expressing_curiosity", "describing", "decomposing", "explaining",
                                "expressing_awe|expressing_contentment"],
}


def gerunds_of(skel):
    """All gerunds in a skeleton string, root first."""
    return re.findall(r"\b([a-z_]+)\(", skel)


def provides(gerund_set, want):
    for w in want.split("|"):
        if w.endswith("*"):
            if any(g.startswith(w[:-1]) for g in gerund_set):
                return True
        elif w in gerund_set:
            return True
    return False


def theory_coverage(sentence_gerunds):
    """{theory: share of its signature matched in order by the sentences (each sentence
    satisfies at most one element)}."""
    out = {}
    for name, sig in THEORIES.items():
        k = 0
        for gs in sentence_gerunds:
            if k < len(sig) and provides(gs, sig[k]):
                k += 1
        out[name] = k / len(sig)
    return out
