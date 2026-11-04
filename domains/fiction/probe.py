"""Read sentences with the determination system and print their skeletons (a development tool for the
construction printer: a construction is admitted only if the reader recovers its skeleton).

Run: python probe.py "Sentence one." "Sentence two."   (or one sentence per line on stdin)
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEXT_DIR = os.environ.get("ANALOGY_TEXT", os.path.join(REPO, "reference", "text"))
sys.path.insert(0, TEXT_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grammar  # noqa: E402,F401  (the fiction templates; FICTION_GRAMMAR=0 reads with the Wikipedia ones only)
import determine as D  # noqa: E402
from structural import skeleton  # noqa: E402


def skeletons(texts):
    """[(text, sorted skeletons of its readings, why undetermined or '')] per text."""
    out = []
    for doc, readings in D.determine_many(texts):
        skels = sorted({skeleton(str(r)) for r in readings})
        why = "" if readings else " ".join(map(str, D.why_undetermined(doc)))
        out.append((doc.text, skels, why))
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    texts = sys.argv[1:] or [l.strip() for l in sys.stdin if l.strip()]
    for text, skels, why in skeletons(texts):
        print(text)
        for s in skels:
            print("    " + s)
        if why:
            print("    UNDETERMINED: " + why)


if __name__ == "__main__":
    main()
