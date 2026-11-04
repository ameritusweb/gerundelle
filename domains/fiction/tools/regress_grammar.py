"""What the fiction grammar changes on Wikipedia: the same sentences read without and with it.

Run: python tools/regress_grammar.py [--n 1500]
Runs itself twice (FICTION_GRAMMAR=0, then 1) in subprocesses (installing the grammar is per process),
then compares: determination rate, sentences whose readings changed, the new gerunds that fired and
examples of each (read them: a new gerund on Wikipedia prose is either right or a false positive).
"""
import argparse
import json
import os
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The parsed Wikipedia articles this compares against aren't in the repo: set ANALOGY_TEXT to a folder that has them.
ARTICLES = os.path.join(os.environ.get("ANALOGY_TEXT", os.path.join(os.path.dirname(os.path.dirname(HERE)), "text")),
                        "results", "articles_a.jsonl")
NEW = ("realizing", "asking", "telling", "instructing", "iterating")


def sample(n):
    size = os.path.getsize(ARTICLES)
    out = []
    with open(ARTICLES, "rb") as f:
        for k in range(n):
            f.seek(size * k // n)
            if k:
                f.readline()
            line = f.readline()
            if line:
                out.append(json.loads(line)["text"])
    return out


def run(n, flag):
    path = os.path.join(HERE, "results", f"regress_grammar_{flag}.jsonl")
    env = dict(os.environ, FICTION_GRAMMAR=flag)
    subprocess.run([sys.executable, "-X", "utf8", os.path.abspath(__file__), "--worker", "--n", str(n), "--out", path],
                   env=env, check=True)
    return [json.loads(l) for l in open(path, encoding="utf-8")]


def worker(n, out):
    sys.path.insert(0, HERE)
    from probe import skeletons
    rows = skeletons(sample(n))
    with open(out, "w", encoding="utf-8") as f:
        for text, skels, _ in rows:
            f.write(json.dumps({"text": text, "skels": skels}) + "\n")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1500)
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.worker:
        worker(args.n, args.out)
        return
    off, on = run(args.n, "0"), run(args.n, "1")
    det_off = sum(bool(r["skels"]) for r in off) / len(off)
    det_on = sum(bool(r["skels"]) for r in on) / len(on)
    changed = [(a, b) for a, b in zip(off, on) if a["skels"] != b["skels"]]
    lost = [(a, b) for a, b in changed if not set(a["skels"]) <= set(b["skels"])]
    fired = Counter()
    examples = {}
    for a, b in changed:
        for g in NEW:
            if any(f"{g}(" in s for s in b["skels"]):
                fired[g] += 1
                examples.setdefault(g, []).append(b["text"])
    print(f"{len(off)} Wikipedia sentences")
    print(f"determined: without {det_off:.1%}, with {det_on:.1%}")
    print(f"readings changed: {len(changed)} ({len(changed) / len(off):.1%}); of them, an old reading lost: {len(lost)}")
    print(f"new gerunds fired (sentences): {dict(fired)}")
    for g, ex in examples.items():
        print(f"\n{g}:")
        for t in ex[:8]:
            print(f"   {t[:150]}")
    if lost:
        print("\nold readings lost (should be only the 'only when' condition fix and the quoted-speech repair):")
        for a, b in lost[:8]:
            print(f"   {a['text'][:150]}")
            print(f"      without: {a['skels'][:2]}")
            print(f"      with:    {b['skels'][:2]}")


if __name__ == "__main__":
    main()
