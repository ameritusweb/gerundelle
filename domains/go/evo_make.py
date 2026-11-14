"""One generation of temperament mutants for the league (the user, 2026-11-13: "do evolutionary mutation on unflinching, trusting, and
grieving temperament parameters ... the mutation should result in 9-11 minds competing"; then "Parents + 2 mutants each", "One
generation", "All six, about +-30%").

The parents are the league's minds as saved mid-league (evo/source/, from league/minds.7z, 6 sub-rounds played). Each offspring starts as
a copy of its parent's learned minds, Black and White (everything it has learned), with its temperament mutated; the parent is kept
unchanged, as the control. 3 parents x (1 + 2) = 9 profiles, 18 minds, in evo/minds/.

Mutation (my reading of "about +-30%"; each can change):
- the six temperament traits: patience, persistence, curiosity, credulity, aversion, acceptance (fiction/temperament.py's, with the Go
  mind's aversion and acceptance);
- each multiplied by exp(N(0, 0.3));
- whole-number traits (patience, acceptance) rounded, at least 1;
- credulity kept within 0.05..0.95;
- patience unset (never gives a want up) stays unset, unless a coin flip (1 in 2) sets it, to round(4 x exp(N(0, 0.3))), around the
  league's patient/impatient values;
- both of a profile's minds (Black, White) get the same values;
- the random source is seeded (SEED), so the population can be made again.

Run: PYTHONHASHSEED=0 python -u -X utf8 evo_make.py"""
import json
import math
import os
import random
import shutil
import sys

HERE = __import__("paths").domain('go')
SRC, DST = f"{HERE}/evo/source/minds", f"{HERE}/evo/minds"
PARENTS = ["unflinching", "trusting", "grieving"]
TRAITS = ["patience", "persistence", "curiosity", "credulity", "aversion", "acceptance"]
SEED, SIGMA, CHILDREN = 2026_11_13, 0.3, 2


def mutate(t, rng):
    out = dict(t)
    f = lambda: math.exp(rng.gauss(0.0, SIGMA))
    for k in TRAITS:
        v = t[k]
        if k == "patience":
            if v is None:
                out[k] = max(1, round(4 * f())) if rng.random() < 0.5 else None
            else:
                out[k] = max(1, round(v * f()))
        elif k == "acceptance":
            out[k] = max(1, round(v * f()))
        elif k == "credulity":
            out[k] = round(min(0.95, max(0.05, v * f())), 3)
        else:
            out[k] = round(v * f(), 3)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, HERE)
    import run  # noqa: F401  (first: Gerundelle on the path)
    import checkpoint
    os.makedirs(DST, exist_ok=True)
    rng = random.Random(SEED)
    population = {}
    for parent in PARENTS:
        a, _, _ = checkpoint.load(f"{SRC}/{parent}_black.pkl")
        base = {k: getattr(a.mind.p, k) for k in TRAITS}
        population[parent] = dict(parent=parent, traits=base)
        for colour in ("black", "white"):
            shutil.copyfile(f"{SRC}/{parent}_{colour}.pkl", f"{DST}/{parent}_{colour}.pkl")
        for i in range(1, CHILDREN + 1):
            name = f"{parent}_m{i}"
            traits = mutate(base, rng)
            population[name] = dict(parent=parent, traits=traits)
            for colour in ("black", "white"):
                agent, seat, t = checkpoint.load(f"{SRC}/{parent}_{colour}.pkl")
                for k, v in traits.items():
                    setattr(agent.mind.p, k, v)
                checkpoint.save(agent, seat, t, f"{DST}/{name}_{colour}.pkl")
    with open(f"{HERE}/evo/population.json", "w", encoding="utf-8") as f:
        json.dump(dict(seed=SEED, sigma=SIGMA, population=population), f, indent=1)
    for name, p in population.items():
        print(f"{name:15s} {p['traits']}")


if __name__ == "__main__":
    main()
