"""Set a temperament trait on evolution minds already playing, both colours, and record it in evo/population.json (the user, 2026-11-13:
"restore patience None for the mutants please before re-running"). Everything a mind has learned is kept; only Params changes.
Run: PYTHONHASHSEED=0 python -u -X utf8 evo_set_trait.py <trait> <value> <profile> [profile ...]   (value: a Python literal, e.g. None)"""
import ast
import json
import sys

HERE = __import__("paths").domain('go')
sys.path.insert(0, HERE)
import run  # noqa: E402,F401  (first: Gerundelle on the path)
import checkpoint  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    trait, value, names = sys.argv[1], ast.literal_eval(sys.argv[2]), sys.argv[3:]
    pop_path = f"{HERE}/evo/population.json"
    pop = json.load(open(pop_path, encoding="utf-8"))
    for name in names:
        for colour in ("black", "white"):
            path = f"{HERE}/evo/minds/{name}_{colour}.pkl"
            agent, seat, t = checkpoint.load(path)
            before = getattr(agent.mind.p, trait)
            setattr(agent.mind.p, trait, value)
            checkpoint.save(agent, seat, t, path)
            print(f"{name} {colour}: {trait} {before} -> {value}")
        entry = pop["population"][name]
        entry.setdefault("changes", []).append(dict(trait=trait, was=entry["traits"][trait], now=value,
                                                    after_subrounds=len(json.load(open(f"{HERE}/evo/state.json"))["done"])))
        entry["traits"][trait] = value
    json.dump(pop, open(pop_path, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
