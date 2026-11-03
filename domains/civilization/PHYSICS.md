# Physics of the civilization world

**Status (2026-10-30): every gerund below is built**, in `potential_world.py` (P0–P4) and `moon_world.py` (P5): drawing to levels, spilling, forming from a pattern, cleaving (with what was inside found), unmaking, fusing (the fused part lifts), propelling, flying, landing, escaping, drifting, arriving, and the voyage back (returning, beached). Conservation is asserted every slice, across two places since P3. See [LADDER.md](LADDER.md). This doc goes with [README.md](README.md) and builds on the force vocabulary in `E:/vscode/analogy/FORCE_VOCABULARY.md` and `forces/poc.py`.

## Principles

0. **In the slice a push lands, only the object pushed changes; consequences for anything else follow a slice later** (learned at P1 and again at P3, see LADDER.md). Gerundelle reads a change to another object in a push's own slice as part of the situation the push met, so a world that changes several objects at once teaches the minds that their own effects are their causes.

1. **Coherent by construction.** The world changes only when a quantity crosses a reserve and an object's gerund flips. This is the rule the force world already uses, and nothing happens by script. New physics means new gerunds with new reserves, written in the same vocabulary.
2. **One conserved quantity: potential.** Objects can appear "out of nothing" from the agents' point of view, but in the world's books they are condensed from potential. Breaking an object gives its potential back, and launching spends it as motion. The total never changes.
3. **Real to the agents.** Minds aren't told the rules. They find the conditions for forming, breaking and launching by interacting with the world, the same way Mara found the latch. A cheat code is simply how their world works.
4. **Generous first, scarce later.** At first potential is effectively unlimited and creation is cheap, so the whole pipeline can be built and run end to end. Scarcity is a set of knobs to turn later. The books are kept from day one so that turning the knobs needs no rewrite.

## What already exists

The force vocabulary already covers two of the three powers in a mundane form:

| Power | Existing gerunds |
|---|---|
| breaking apart | `coming apart` (load through > cohesion → its parts), `shattering`, `tearing`, `crumbling` |
| potential that propels | `stretching`, `compressing`, `loading` (store), `releasing` → `launching` → `flying` |
| holding together | `cohering`, `binding`, `tying`, `fastening`, `locking` |

What's missing is **creation**: no gerund produces a new object except as parts of something that broke. Nothing joins two objects into a new one, and nothing launches at a scale that leaves a world.

## Potential

- **In places.** Each place has a potential field: a reserve with a level, a capacity and a regeneration rate.
- **In objects (stored).** A doer can carry potential it has drawn, the way a raised weight carries `loading`.
- **In objects (embodied).** Every object holds the potential it cost to form. Its cost is computed from its finite reserves: `cost(obj) = rate × Σ finite reserves`, where `rate` is a knob.
- **In motion.** A launched object carries the potential spent on launching it until it lands.

**Conservation (a theorem to prove in Lean):** at every slice, *field + stored + embodied + in motion* is constant. No sequence of flips creates or destroys potential.

## New gerunds (proposed)

Same format as `FORCE_VOCABULARY.md`.

| Gerund | Forces it names | Flips to |
|---|---|---|
| **drawing** | A doer takes potential from its place's field into its own store | the doer **charged**; the place's field lower (**depleted** below a threshold) |
| **charged** | A doer holding stored potential, a reserve that can be spent | **forming**, **cleaving**, **propelling**, or **leaking** (loses its store when its hold is exceeded) |
| **forming** | Stored potential condensed into a new object after a **pattern** | a new node, the formed object, **resting**; the doer's store lowered by `cost(obj)` |
| **fusing** | Two objects and potential joined into one whose reserves combine | one node, the composite; cohesion paid from stored potential |
| **cleaving** | Stored potential driven through an object's cohesion with no load needed | its parts (as `coming apart`); the potential spent stays embodied in the parts |
| **unmaking** | An object returned whole to potential | gone; its embodied potential back to the place's field |
| **propelling** | Stored potential released as a sustained push, a `launching` that lasts | **flying** while the store lasts; **escaping** if the push beats the world's binding |
| **escaping** | Flight past a world's binding (a `weight` reserve at planetary scale) | **drifting** in space, a place with a sparse field |
| **drifting** | Moving with nothing bearing or opposing | **arriving** where another world's binding takes hold |

Each one flips only when a reserve is crossed, so coherence holds the same way it does for the rest of the force world.

## Patterns: creation by shape

`forming` needs a **pattern**: the gerund subtree and reserves of the object to be made. A mind can hold a pattern in three ways, matching the provenances the architecture already has:

- **seen:** it has perceived such an object (lived).
- **told:** someone described it, as a blueprint (told, at half weight).
- **recalled:** it maps a known pattern onto a new need by shape (fiction rung 6, cognitivecode rung 5b).

Why keep this condition even in the generous world:
- It's what makes forming *learnable*. Forming has a hidden condition that minds discover by contrast, like the latch.
- It turns knowledge into the thing that matters. Blueprints become told receipts, and those are culture and technology.
- It sets up the slow-communication what-if: a blueprint from a distant world may be stale for local conditions.

## Knobs

| Knob | Generous (phase 1) | Turned later |
|---|---|---|
| field level and capacity | effectively unlimited | finite |
| regeneration rate | instant | slow, like sunlight or ore |
| distribution across places | even | uneven, so rich places are worth claiming |
| cost `rate` per reserve | tiny | substantial |
| hidden conditions on forming | one (a pattern held) | more (field threshold, place, material) |
| planetary binding | low (escape is easy) | high |
| field in space | some | sparse |

Each later setting is a what-if run against the generous baseline (README: paired runs, reported as ranges).

## Decisions taken for phase 1 *(proposed)*

- **Creation is potential-based, not truly from nothing.** Conservation is what makes the world feel real and what lets scarcity be turned on later.
- **No self-replication.** Formed objects cannot themselves draw or form, and minds cannot be formed. That avoids runaway growth until the rest works. Revisit later as its own what-if.
- **Agents are not objects with potential.** A mind's reserves (resolve, conviction, retention, goal) are not formed or unmade.

## Revised early rungs

With abundance first, the README's ladder needs a physics-first prefix. "Specialization under scarcity" moves later.

| Rung | Question | World | Measures |
|---|---|---|---|
| P0 | Does one mind draw, form, break and launch, and does a story come out? | one mind, one place, generous field, one pattern already seen | conservation holds every slice; want reached; story round-trips |
| P1 | Does a mind learn forming's hidden condition? | forming needs a pattern; the mind starts without the right one | conditions learned by contrast (fiction rung 0's arc) |
| P2 | Does a told blueprint change what a mind can make? | two minds; one holds a pattern and tells it | told receipt used; Attest saves search (fiction rung 2's test) |
| P3 | Does a mind reach space? | planetary binding; a want that lies beyond it | propelling → escaping → drifting → arriving; a story of the voyage |
| P4 | What does a population do with no scarcity? | many minds, generous field | the baseline. Written prediction: little specialization, trade or conflict (cognitivecode lesson 9) |

After P4, the knobs turn and the README's ladder picks up (specialization, generations, trade, conflict, transfer, divergence), each rung run against the P4 baseline.

## Built on

- `E:/vscode/analogy/forces/poc.py`: `Obj` reserves, watches and phase changes. New reserves (`field`, `store`, `binding`) and the new gerunds go here or in a civilization extension of it.
- `E:/vscode/analogy/molecules/force_world.py`: `ForceWorld` and its `invitations()` (pushes are read off the structure, never off names).
- `../fiction/`: `ScenicWorld`, the beats, the printer, and both minds (`lean.py`, `gerundelle_arm.py`).
- `../relations/RELATION_TYPES.md`: forming and unmaking are coming into existence and going out of it. That's GO from or to nothing, a form not in the 15. If minds treat it as distinct, it gets a row in the primitive × field table (README lesson 14).

## Open questions

- Is a place's field one number, or does it have kinds of potential (which would be the start of "materials")?
- ~~Does forming take one slice or several?~~ **One slice (P1):** forming in the push's own slice taught Gerundelle that forming turns on its own product. Several slices would still give a window for interruption and contest later.
- What does a mind perceive of a field: its level, only its effects, or nothing until it draws?
- How patterns are represented, so that "seen" and "told" are the same object at different provenances.
- ~~Whether `fusing` produces anything new or only sums its parts.~~ **Both (P5):** the parts' potential sums, so conservation stays simple, and the whole gets a property neither part had: a lantern fused into a skiff lifts it (the binding on it is the world's binding less its fused store).
