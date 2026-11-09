# Mystery maze

A Gerundelle mind wants the cheese at the far end of a maze. It knows nothing of mazes, walls or words: it learns by pushing on a grounded force world, and gets faster at finding the cheese trip after trip.

## The design (the user)

- **A maze with cheese at the end.** The Gerundelle mind is given a want for cheese.
- **Each position is an object** with a potential force to walk onto it.
- **A 4-button controller.** Each button sets the heading: north, south, east or west. Each button is a potential force.
- **Perception depends on heading:** the mind perceives what is in front of it.
- **26 vocal cords,** which the mind perceives as 26 potential forces. Each one says a word of the military alphabet ("alfa", "hotel", ...).
- **Each word acts differently on each type of wall.** The wall's type is perceived through the force each word would exert on it.
- **A distance gerund on the controller:** whether the straight-line distance to the cheese is increasing, decreasing or holding, read out every step.
- **The buttons and words stop working** after a while without moving (the lock), so the walk is what's left on offer.

## How it is built

- **`maze.py`:** the world. Objects: every position, every wall (its type in its identity, as a chess piece's kind), the controller, the voice, the cheese. Every reading is a doing: a position `bearing` the body or `free`, a wall `blocking` or `yielding`, the heading `pointing_east`, the cheese `resting` or `borne`. Each push on offer carries the force it would exert on what it reaches: a word 3 on the wall it opens, 2 on a wall that holds against it, 1 with nothing to reach. Only legal pushes are offered. In a push's slice only the thing pushed changes.
- **`dream_maze.py`:** the dream planner between trips. It manipulates one force at a time (where the body stands, the heading, a wall), the mind's own tournament choosing which, and keeps what it dreams as imagined structure. It is how the mind reaches the cheese from a side it never came from, and how what always comes with the cheese is told apart from what came with one approach.
- **`run.py`:** a Gerundelle mind (`reference/v2`) with the switches listed in `LESSONS_LEARNED.md`, temperament `--acceptance`.
- **`gerundelle_path.py`:** puts `reference/v2` on the path, and holds two small pieces from the Warp chess work: potential forces as activation, and the dream's test of what the mind understands.
- **`test_maze.py`:** the grounding as tests.

## Run it

```bash
cd domains/mysterymaze
python -X utf8 run.py --seed 0 --slices 2000 --dreams --acceptance 6
python -X utf8 -m pytest -q test_maze.py
```

Set `PYTHONHASHSEED=0` to reproduce the numbers below.

## Result

Five mazes (seeds 0-4), 2,000 slices each, acceptance 6: the cheese reached 78 times. On seed 0 the trips fall from 130-160 slices to a steady 42-86 for the last fifteen; on seed 3 most trips take 26-62 slices, the shortest 26. Learning is not yet monotonic on every maze: long trips still occur. Temperament matters: a mind that lets questions go too quickly (acceptance 3) reached the cheese 44 times.

## What was learned

`LESSONS_LEARNED.md`: grounding the world, the mechanisms the traces led to (each a switch in `reference/v2`), what failed and why, and how to work on it.
