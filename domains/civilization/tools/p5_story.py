"""The story of P5's curriculum for one temperament: python -X utf8 tools/p5_story.py <temper> <fresh|carried>."""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))
import dataclasses  # noqa: E402
import p0  # noqa: E402
import p5  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
temper, how = sys.argv[1], sys.argv[2]
world, m, log = p5.run_stages(800, temper, how == "carried")
lex = dict(p5.LEXICON, want={**p5.LEXICON["want"], "pool_glimmering": "wanted to fill the pool with light",
                             "skiff_lit": "wanted to light the skiff"})
scene, sentences, ms = p0.story(world, m, lex)
print(log)
print(" ".join(t for _, t, _ in sentences))
for r in ms["rows"]:
    if not r["ok"]:
        print(f"  MISS {r['text']}\n        intended {r['shape']}\n        reading  {r['reading'] or r['why']}")
print(f"round-trip {ms['round_trip']:.2f}; sentences {len(sentences)}")
with open(os.path.join(HERE, "results", f"p5_stages_{how}_{temper}.json"), "w", encoding="utf-8") as f:
    json.dump(dict(stages=log, sentences=[t for _, t, _ in sentences], round_trip=ms["round_trip"], ledger=world.history,
                   beats=[dataclasses.asdict(b) for b in m.beats]), f, indent=1, default=str)
