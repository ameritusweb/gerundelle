"""The first corpus run: every scene x temperament profiles x both minds, each story told, printed and read back.

Writes corpus/stories.jsonl (one story per line) and corpus/summary.md. A story's record:
  id, rung, world, mind (lean | gerundelle), temperament, outcome (reached | gave up | unresolved, and by whom),
  sentences: [{text, label (the reader's skeleton), shape (the construction's intended shape), plan, stage}],
  round_trip, measures (judge share, variety, exact theory, history), duplicate_of (an earlier identical story).
Only labels the reader recovered are labels: a sentence whose reading did not match its intended shape has
label None, and the story is flagged (round_trip < 1).

Run: python -X utf8 tools/corpus.py [--rungs 0,1,...] [--tempers steady,...] [--minds lean,gerundelle]
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import run_ladder  # noqa: E402

WORLDS = {0: "box", 1: "crate in the wind", 2: "box, Ben knows", 3: "box, Leo lies", 4: "box, Leo keeps it shut",
          5: "toy taken and returned", 6: "box then cupboard", 61: "box then cupboard (bolt sorts last)",
          8: "shed with a wrong key", 9: "lamp with two plugs", 10: "boulder on a plank", 11: "toy cannon",
          12: "catapult", 13: "doorbell with its wire out", 14: "chime with a damper", 15: "chain on a shelf",
          16: "chest (the box, dressed)", 17: "tin (the box, dressed)", 18: "music box (the box)",
          19: "garden gate (the shed)", 20: "diary (the shed)", 21: "log in a stream (the boulder)",
          22: "pinball launcher (the cannon)", 23: "radio (the doorbell)", 24: "bicycle bell (the chime)"}
MAX_SENTENCES = 90   # a story longer than this is kept but marked (a question a mind could not let go of, told
                     # whole, is not a story a reader finishes): left out of the clean set
TEMPERS = ["steady", "impatient", "restless", "dogged", "trusting", "skeptical"]


def outcome(beats, actor):
    reach = next((b for b in reversed(beats) if b.kind == "reach" and b.actor == actor), None)   # the story's last
    if reach is not None:
        by = reach.detail.get("by")
        return f"reached (by {by})" if by and by != actor else "reached"
    if any(b.kind == "feel" and b.actor == actor and b.detail.get("phase") == "resignation" for b in beats):
        return "gave up"
    return "unresolved"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--rungs", default=",".join([str(r) for r in WORLDS] + list(run_ladder.SOCIAL)),
                    help="rung numbers and social scenes' names (social.py), comma-separated")
    ap.add_argument("--tempers", default=",".join(TEMPERS))
    ap.add_argument("--minds", default="lean,gerundelle")
    ap.add_argument("--ticks", type=int, default=300)
    args = ap.parse_args()
    out_dir = os.path.join(HERE, "corpus")
    os.makedirs(out_dir, exist_ok=True)
    seen, rows = {}, []
    t0 = time.time()
    with open(os.path.join(out_dir, "stories.jsonl"), "w", encoding="utf-8") as f:
        for rung in args.rungs.split(","):
            spec = run_ladder.SOCIAL[rung] if rung in run_ladder.SOCIAL else run_ladder.RUNGS[int(rung)]
            rung = rung if rung in run_ladder.SOCIAL else int(rung)
            for mind in args.minds.split(","):
                for temper in args.tempers.split(","):
                    name = f"{mind}-{temper}"
                    run_ladder.CONFIGS.setdefault(name, (mind, {"_temper": temper} if temper != "steady" else {}))
                    try:
                        beats, scene, sentences, m = run_ladder.compose(name, spec, args.ticks)
                    except Exception as ex:   # a scene a mind cannot yet play is recorded, not hidden
                        print(f"rung {rung} {name}: FAILED {type(ex).__name__}: {ex}")
                        rows.append(dict(rung=rung, mind=mind, temperament=temper, failed=str(ex)))
                        continue
                    texts = tuple(r["text"] for r in m["rows"])
                    sid = f"r{rung}-{mind}-{temper}"
                    dup = seen.get(texts)
                    seen.setdefault(texts, sid)
                    rec = dict(id=sid, rung=rung, world=WORLDS.get(rung, str(rung)), mind=mind, temperament=temper,
                               outcome=outcome(beats, spec["actor"]), duplicate_of=dup,
                               sentences=[dict(text=r["text"], label=r["reading"] or None, shape=r["shape"],
                                               plan=scene.plans[r["plan"]].kind, stage=scene.plans[r["plan"]].stage)
                                          for r in m["rows"]],
                               round_trip=m["round_trip"], too_long=len(texts) > MAX_SENTENCES,
                               measures=dict(judge=m["matched_share"], variety=m["variety"],
                                             exact_theory=m["exact_theory"], exact_coverage=m["exact_coverage"],
                                             history=m["history"], irony=m["irony"], reader=m["reader"]))
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    rows.append(rec)
                    print(f"rung {str(rung):16} {name:22} {len(texts):3d} sents trip {m['round_trip']:.2f} var {m['variety']:.2f} "
                          f"{rec['outcome']:18} {'dup of ' + dup if dup else ''}  [{time.time() - t0:.0f}s]", flush=True)
    ok = [r for r in rows if "failed" not in r]
    unique = [r for r in ok if not r["duplicate_of"]]
    clean = [r for r in unique if r["round_trip"] == 1.0 and not r.get("too_long")]
    lines = [f"# Corpus run ({len(set(r['rung'] for r in rows))} scenes)", "",
             f"{len(rows)} runs; {len(ok)} stories; {len(unique)} unique; {len(clean)} unique with every sentence read back; "
             f"{sum(len(r['sentences']) for r in clean)} labelled sentences.", "",
             "| rung | world | mind | temperament | sentences | trip | variety | outcome | duplicate of |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        if "failed" in r:
            lines.append(f"| {r['rung']} | {WORLDS.get(r['rung'])} | {r['mind']} | {r['temperament']} | | | | FAILED: {r['failed']} | |")
            continue
        lines.append(f"| {r['rung']} | {r['world']} | {r['mind']} | {r['temperament']} | {len(r['sentences'])} | "
                     f"{r['round_trip']:.2f} | {r['measures']['variety']:.2f} | {r['outcome']} | {r['duplicate_of'] or ''} |")
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[:3]))


if __name__ == "__main__":
    main()
