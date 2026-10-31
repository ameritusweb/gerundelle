import Mathlib.Logic.Function.Basic
import Mathlib.Data.Set.Insert

/-!
# Affect: the phases as readings of the ownership graph

A formalization of `Phases.graph` (`analogy/molecules/molecules.py`; OWNERSHIP_SOV.md §7,
REORG.md step 7, test T79), with the curiosity reading as fixed on 2026-10-30: it sits in the
loop over live slots, so it reads the slot's own instance.

Each tick, `graph` reads the territory register and forms phases, each a pair (kind, anchor).
`form` is a pure function of the two (`Phases.pid`), so one tick's output is a set of pairs.

## What the code reads

* **The territory register**: open and live slot instances (live = open, not parked), each
  region's row (`fails`, `failed`, `other_since`, `taken_by`), and `took_now`, `helped_now`,
  `gave_up_now`.
* **The phases' memory of last tick**: `prev_live`, `prev_open`, and the calm counter.
* **Outside the register**: the tick's winners (`top`), which curiosity reads; the conditions
  reading of live frustrations through the meta layer's splits and the understanding's
  `conditioned_by` relations, and the tellers the world belied, which anger reads. Both anger
  sources are taken here as the sets of agents they blame (lines 2316–2332 and 2343–2346).

## Results

* **Frustration needs the slot to keep not taking** (`mem_graph_frustration`,
  `not_frustrated_of_fails_le_one`): it forms exactly on a live failing slot with two or more
  failures running. One failure on a contested slot is anxiety (`anxiety_of_one_failure`).
* **Joy is a slot closing by a claim** (`mem_graph_joy`, `joy_needs_take`): not any good outcome.
* **Calm is no tension** (`live_empty_of_calm`): calm forms only with no live instance, not
  merely low tension.
* **Curiosity is an unclaimed slot winning the ownership track** (`mem_graph_curiosity`).
* **Which layer each phase reads** (`register_phases_factor`, `curiosity_not_factor`,
  `curiosity_factors`, `anger_not_factor`). Frustration, anxiety, sadness, joy, calm, gratitude
  and resignation are functions of the register and last tick alone: two minds alike there feel
  alike in these. Curiosity is not; it needs the competition's winners as well, and with them it
  is a function again. Anger is not either; it reads understanding and meta.
  "Is a function of" is `Function.FactorsThrough`, the property `SOV.Erlangen`'s
  `invariant_iff_factors` characterizes for perception.
-/

namespace SOV.Affect

/-- The ownership SOV's slot kinds (`Territory.open_slots`). -/
inductive SlotKind
  | unclaimed | control | contested | lost | uniqueness | relation
  deriving DecidableEq, Repr

/-- A region's row, the fields the phases read. Absent fields read as their defaults. -/
structure Row (A : Type*) where
  /-- Tries running that did not take (`claimed`). -/
  fails : ℕ
  /-- A claim on a held region didn't take: contested until one takes again. -/
  failed : Bool
  /-- Moves by something else since the region was claimed. -/
  otherSince : ℕ
  /-- Who was seen taking it. -/
  takenBy : Option A

inductive PhaseKind
  | frustration | anger | anxiety | sadness | joy | curiosity | calm | resignation | gratitude
  deriving DecidableEq, Repr

/-- What a phase is about: an ownership instance `own:<kind>:<region>`, another agent, or the
pool. -/
inductive Anchor (R A : Type*)
  | own (k : SlotKind) (r : R)
  | other (a : A)
  | pool
  deriving DecidableEq

abbrev Phase (R A : Type*) := PhaseKind × Anchor R A

/-- The territory register, as the phases read it. -/
structure Register (R A : Type*) where
  openSlots : Set (SlotKind × R)
  /-- Open and not parked. -/
  live : Set (SlotKind × R)
  live_subset : live ⊆ openSlots
  rows : R → Row A
  tookNow : Set R
  /-- A want met by another's act, seen: (region, who). -/
  helpedNow : Set (R × A)
  gaveUpNow : Set R

/-- The phases' memory of last tick. -/
structure Memory (R : Type*) where
  prevLive : Set (SlotKind × R)
  prevOpen : Set (SlotKind × R)
  calmFor : ℕ

/-- What the phases read from outside the register. -/
structure Context (R A : Type*) where
  /-- Ownership instances among this tick's winners (the competition). -/
  top : Set (SlotKind × R)
  /-- Others blamed by the conditions reading of live frustrations (understanding, meta). -/
  inferredBlame : Set A
  /-- Tellers whose word the world contradicted last tick (understanding). -/
  belied : Set A

/-- Everything one call of `graph` reads. -/
structure Snapshot (R A : Type*) where
  reg : Register R A
  mem : Memory R
  ctx : Context R A

variable {R A : Type*}

/-- A slot whose claims keep failing: control, or contested by its own failure. -/
def Failing (k : SlotKind) (row : Row A) : Prop :=
  k = .control ∨ (k = .contested ∧ row.failed = true ∧ row.otherSince = 0)

open Classical in
/-- The calm counter after this tick: one more with nothing live, else reset. -/
noncomputable def calmFor' (reg : Register R A) (mem : Memory R) : ℕ :=
  if reg.live = ∅ then mem.calmFor + 1 else 0

/-- The readings off the register and last tick (`graph`, lines 2292–2313 and 2336–2359). -/
def registerReading (reg : Register R A) (mem : Memory R) : Set (Phase R A) :=
  -- live slots: frustration, else anxiety; a lost slot grieves, with anger at who took it
  {p | ∃ k r, (k, r) ∈ reg.live ∧
    ((Failing k (reg.rows r) ∧ 2 ≤ (reg.rows r).fails ∧ p = (.frustration, .own k r)) ∨
     (¬ (Failing k (reg.rows r) ∧ 2 ≤ (reg.rows r).fails) ∧ k = .contested ∧
        (reg.rows r).failed = true ∧ (reg.rows r).otherSince = 0 ∧ (reg.rows r).fails = 1 ∧
        p = (.anxiety, .own k r)) ∨
     (k = .lost ∧ p = (.sadness, .own k r)) ∨
     (k = .lost ∧ ∃ a, (reg.rows r).takenBy = some a ∧ p = (.anger, .other a)))} ∪
  -- a lost slot opening while parked still grieves, once
  {p | ∃ r, (SlotKind.lost, r) ∈ reg.openSlots ∧ (SlotKind.lost, r) ∉ reg.live ∧
    (SlotKind.lost, r) ∉ mem.prevOpen ∧
    (p = (.sadness, .own .lost r) ∨ ∃ a, (reg.rows r).takenBy = some a ∧ p = (.anger, .other a))} ∪
  -- joy: an instance closed because a claim took on its region (not because it was lost)
  {p | ∃ k r, ((k, r) ∈ mem.prevLive ∨ (k, r) ∈ mem.prevOpen) ∧ (k, r) ∉ reg.openSlots ∧
    r ∈ reg.tookNow ∧ (SlotKind.lost, r) ∉ reg.openSlots ∧ p = (.joy, .own k r)} ∪
  {p | ∃ r a, (r, a) ∈ reg.helpedNow ∧ p = (.gratitude, .other a)} ∪
  {p | ∃ r, r ∈ reg.gaveUpNow ∧ p = (.resignation, .own .control r)} ∪
  {p | 5 ≤ calmFor' reg mem ∧ p = (.calm, .pool)}

/-- Curiosity: an unclaimed slot winning the ownership track (line 2312, as fixed). -/
def curiosityReading (reg : Register R A) (ctx : Context R A) : Set (Phase R A) :=
  {p | ∃ r, (SlotKind.unclaimed, r) ∈ reg.live ∧ (SlotKind.unclaimed, r) ∈ ctx.top ∧
    p = (.curiosity, .own .unclaimed r)}

/-- Anger read through understanding and meta (lines 2316–2332, 2343–2346). -/
def contextReading (ctx : Context R A) : Set (Phase R A) :=
  {p | ∃ a, (a ∈ ctx.inferredBlame ∨ a ∈ ctx.belied) ∧ p = (.anger, .other a)}

/-- The phases one tick forms. -/
def graph (s : Snapshot R A) : Set (Phase R A) :=
  registerReading s.reg s.mem ∪ curiosityReading s.reg s.ctx ∪ contextReading s.ctx

/-! ### The phases one at a time -/

variable {s : Snapshot R A}

/-- **Frustration needs the slot to keep not taking.** -/
theorem mem_graph_frustration {k : SlotKind} {r : R} :
    ((.frustration, .own k r) : Phase R A) ∈ graph s ↔
      (k, r) ∈ s.reg.live ∧ Failing k (s.reg.rows r) ∧ 2 ≤ (s.reg.rows r).fails := by
  simp only [graph, registerReading, curiosityReading, contextReading, Set.mem_union,
    Set.mem_ofPred_eq, Prod.mk.injEq, Anchor.own.injEq, reduceCtorEq, false_and, and_false,
    or_false, exists_false, true_and]
  constructor
  · rintro ⟨k', r', hl, hf, h2, rfl, rfl⟩
    exact ⟨hl, hf, h2⟩
  · rintro ⟨hl, hf, h2⟩
    exact ⟨k, r, hl, hf, h2, rfl, rfl⟩

/-- One failure is not enough. -/
theorem not_frustrated_of_fails_le_one {k : SlotKind} {r : R}
    (h : (s.reg.rows r).fails ≤ 1) : ((.frustration, .own k r) : Phase R A) ∉ graph s := by
  rw [mem_graph_frustration]
  omega

/-- One failure on a contested slot, nothing else moving it: anxiety, not frustration. -/
theorem anxiety_of_one_failure {r : R} (hl : (SlotKind.contested, r) ∈ s.reg.live)
    (hf : (s.reg.rows r).failed = true) (ho : (s.reg.rows r).otherSince = 0)
    (h1 : (s.reg.rows r).fails = 1) :
    ((.anxiety, .own .contested r) : Phase R A) ∈ graph s ∧
      ((.frustration, .own .contested r) : Phase R A) ∉ graph s := by
  refine ⟨?_, not_frustrated_of_fails_le_one h1.le⟩
  refine Or.inl (Or.inl (Or.inl (Or.inl (Or.inl (Or.inl (Or.inl ?_))))))
  exact ⟨.contested, r, hl, Or.inr (Or.inl ⟨by omega, rfl, hf, ho, h1, rfl⟩)⟩

/-- **Joy is a slot closing by a claim.** -/
theorem mem_graph_joy {k : SlotKind} {r : R} :
    ((.joy, .own k r) : Phase R A) ∈ graph s ↔
      ((k, r) ∈ s.mem.prevLive ∨ (k, r) ∈ s.mem.prevOpen) ∧ (k, r) ∉ s.reg.openSlots ∧
        r ∈ s.reg.tookNow ∧ (SlotKind.lost, r) ∉ s.reg.openSlots := by
  simp only [graph, registerReading, curiosityReading, contextReading, Set.mem_union,
    Set.mem_ofPred_eq, Prod.mk.injEq, Anchor.own.injEq, reduceCtorEq, false_and, and_false,
    or_false, false_or, exists_false, true_and]
  constructor
  · rintro ⟨k', r', hp, ho, ht, hl, rfl, rfl⟩
    exact ⟨hp, ho, ht, hl⟩
  · rintro ⟨hp, ho, ht, hl⟩
    exact ⟨k, r, hp, ho, ht, hl, rfl, rfl⟩

/-- Joy needs a claim that took: a good outcome alone is not joy. -/
theorem joy_needs_take {k : SlotKind} {r : R}
    (h : ((.joy, .own k r) : Phase R A) ∈ graph s) : r ∈ s.reg.tookNow :=
  (mem_graph_joy.1 h).2.2.1

theorem mem_graph_calm :
    ((.calm, .pool) : Phase R A) ∈ graph s ↔ 5 ≤ calmFor' s.reg s.mem := by
  simp [graph, registerReading, curiosityReading, contextReading]

/-- **Calm is no tension**: it forms only with nothing live. -/
theorem live_empty_of_calm (h : ((.calm, .pool) : Phase R A) ∈ graph s) : s.reg.live = ∅ := by
  classical
  rw [mem_graph_calm, calmFor'] at h
  split_ifs at h with hl
  · exact hl
  · omega

/-- **Curiosity is an unclaimed slot winning the ownership track.** -/
theorem mem_graph_curiosity {a : Anchor R A} :
    ((.curiosity, a) : Phase R A) ∈ graph s ↔
      ∃ r, a = .own .unclaimed r ∧ (SlotKind.unclaimed, r) ∈ s.reg.live ∧
        (SlotKind.unclaimed, r) ∈ s.ctx.top := by
  simp only [graph, registerReading, curiosityReading, contextReading, Set.mem_union,
    Set.mem_ofPred_eq, Prod.mk.injEq, reduceCtorEq, false_and, and_false, or_false, false_or,
    exists_false, true_and]
  constructor
  · rintro ⟨r, hl, ht, rfl⟩
    exact ⟨r, rfl, hl, ht⟩
  · rintro ⟨r, rfl, hl, ht⟩
    exact ⟨r, hl, ht, rfl⟩

/-! ### Which layer each phase reads -/

/-- The phase kinds read off the register and last tick alone. -/
def registerKinds : Set PhaseKind :=
  {.frustration, .anxiety, .sadness, .joy, .calm, .gratitude, .resignation}

/-- The phases of the kinds in `S` that one tick forms. -/
def reading (S : Set PhaseKind) (s : Snapshot R A) : Set (Phase R A) :=
  {p | p ∈ graph s ∧ p.1 ∈ S}

/-- What the register and last tick show. -/
def view (s : Snapshot R A) : Register R A × Memory R :=
  (s.reg, s.mem)

theorem mem_graph_of_registerKind {p : Phase R A} (hp : p.1 ∈ registerKinds) :
    p ∈ graph s ↔ p ∈ registerReading s.reg s.mem := by
  obtain ⟨k, a⟩ := p
  simp only [registerKinds, Set.mem_insert_iff, Set.mem_singleton_iff] at hp
  simp only [graph, curiosityReading, contextReading, Set.mem_union, Set.mem_ofPred_eq,
    Prod.mk.injEq]
  constructor
  · rintro ((h | ⟨_, _, _, rfl, _⟩) | ⟨_, _, rfl, _⟩)
    · exact h
    all_goals simp at hp
  · exact fun h ↦ Or.inl (Or.inl h)

/-- **The register phases are functions of the register and last tick.** -/
theorem register_phases_factor :
    Function.FactorsThrough (reading (R := R) (A := A) registerKinds) view := by
  intro s₁ s₂ h
  simp only [view, Prod.mk.injEq] at h
  ext p
  simp only [reading, Set.mem_ofPred_eq]
  constructor
  · rintro ⟨hp, hk⟩
    rw [mem_graph_of_registerKind hk, h.1, h.2, ← mem_graph_of_registerKind hk] at hp
    exact ⟨hp, hk⟩
  · rintro ⟨hp, hk⟩
    rw [mem_graph_of_registerKind hk, ← h.1, ← h.2, ← mem_graph_of_registerKind hk] at hp
    exact ⟨hp, hk⟩

/-- Curiosity is a function of the live slots and the competition's winners. -/
theorem curiosity_factors :
    Function.FactorsThrough (reading (R := R) (A := A) {.curiosity})
      fun s ↦ (s.reg.live, s.ctx.top) := by
  intro s₁ s₂ h
  simp only [Prod.mk.injEq] at h
  ext ⟨k, a⟩
  simp only [reading, Set.mem_ofPred_eq, Set.mem_singleton_iff]
  constructor
  · rintro ⟨hp, rfl⟩
    rw [mem_graph_curiosity, h.1, h.2, ← mem_graph_curiosity] at hp
    exact ⟨hp, rfl⟩
  · rintro ⟨hp, rfl⟩
    rw [mem_graph_curiosity, ← h.1, ← h.2, ← mem_graph_curiosity] at hp
    exact ⟨hp, rfl⟩

/-- A register with one live unclaimed slot and nothing else. -/
def oneUnclaimed : Register Unit Unit where
  openSlots := {(.unclaimed, ())}
  live := {(.unclaimed, ())}
  live_subset := subset_rfl
  rows := fun _ ↦ ⟨0, false, 0, none⟩
  tookNow := ∅
  helpedNow := ∅
  gaveUpNow := ∅

/-- An empty memory. -/
def noMemory : Memory Unit :=
  ⟨∅, ∅, 0⟩

/-- **Curiosity is not a function of the register.** Two minds alike in the register and last
tick, differing only in what won the competition, differ in curiosity. -/
theorem curiosity_not_factor :
    ¬ Function.FactorsThrough (reading (R := Unit) (A := Unit) {.curiosity}) view := by
  intro h
  have := h (a := ⟨oneUnclaimed, noMemory, ⟨{(.unclaimed, ())}, ∅, ∅⟩⟩)
    (b := ⟨oneUnclaimed, noMemory, ⟨∅, ∅, ∅⟩⟩) rfl
  have hp : ((.curiosity, .own .unclaimed ()) : Phase Unit Unit) ∈
      reading {.curiosity} ⟨oneUnclaimed, noMemory, ⟨{(.unclaimed, ())}, ∅, ∅⟩⟩ :=
    ⟨mem_graph_curiosity.2 ⟨(), rfl, rfl, rfl⟩, rfl⟩
  rw [this] at hp
  obtain ⟨r, -, -, hr⟩ := mem_graph_curiosity.1 hp.1
  simp at hr

/-- **Anger is not a function of the register.** Two minds alike in the register and last tick,
differing only in whom understanding blames, differ in anger. -/
theorem anger_not_factor :
    ¬ Function.FactorsThrough (reading (R := Unit) (A := Unit) {.anger}) view := by
  intro h
  have := h (a := ⟨oneUnclaimed, noMemory, ⟨∅, {()}, ∅⟩⟩)
    (b := ⟨oneUnclaimed, noMemory, ⟨∅, ∅, ∅⟩⟩) rfl
  have hp : ((.anger, .other ()) : Phase Unit Unit) ∈
      reading {.anger} ⟨oneUnclaimed, noMemory, ⟨∅, {()}, ∅⟩⟩ :=
    ⟨Or.inr ⟨(), Or.inl rfl, rfl⟩, rfl⟩
  rw [this] at hp
  obtain ⟨hp, -⟩ := hp
  simp [graph, registerReading, curiosityReading, contextReading, oneUnclaimed, noMemory,
    calmFor'] at hp

end SOV.Affect
