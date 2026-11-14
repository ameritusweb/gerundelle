"""Turn on Params.affords_relation for minds already playing (the user, 2026-11-13: "on please"): what held while a push was on offer
(affords_chain) is its own relation, "affords", not "enables" (molecules.py). A saved mind's affordances were written as "enables", so
they are relabelled; that is right only while Params.polarity is off (then every "enables" in the register is an affordance; polar()
writes the learned ones), which is checked. Everything else a mind has learned is kept.
Run: PYTHONHASHSEED=0 python -u -X utf8 evo_affords.py <minds folder>"""
import json
import os
import sys

HERE = __import__("paths").domain('go')
sys.path.insert(0, HERE)
import run  # noqa: E402,F401  (first: Gerundelle on the path)
import checkpoint  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    folder = sys.argv[1]
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".pkl"):
            continue
        path = os.path.join(folder, name)
        agent, seat, t = checkpoint.load(path)
        p = agent.mind.p
        assert not p.polarity, f"{name}: polarity is on, so its enables aren't all affordances"
        moved = 0
        for c, rels in agent.mind.understanding.rel.items():
            for key in [k for k in rels if k[0] == "enables"]:
                rels[("affords", key[1])] = rels.pop(key)
                moved += 1
        stored = agent.mind.understanding.__dict__.get("dormant_rel") or {}
        for c, rels in stored.items():   # (stored concepts too: they wake as they were)
            for key in [k for k in rels if k[0] == "enables"]:
                rels[("affords", key[1])] = rels.pop(key)
                moved += 1
        p.affords_relation = True
        checkpoint.save(agent, seat, t, path)
        print(f"{name}: {moved} affordances relabelled, affords_relation on", flush=True)
    pop_path = os.path.join(os.path.dirname(folder.rstrip("/\\")), "population.json")
    if os.path.exists(pop_path):
        pop = json.load(open(pop_path, encoding="utf-8"))
        state = json.load(open(os.path.join(os.path.dirname(pop_path), "state.json")))
        pop.setdefault("changes", []).append(dict(switch="affords_relation", now=True, after_subrounds=len(state["done"])))
        json.dump(pop, open(pop_path, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
