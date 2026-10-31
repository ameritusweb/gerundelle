import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Data.Finset.Card

/-!
# Memory: two-phase storage

A formalization of storage in `analogy/molecules/molecules.py` (`new_box`, `warm`, `reopen`,
`contradict`, `tell`; THOUGHT_MOLECULES.md §5b–5c, tests T16–T24). A thought that closes leaves the
pool and is stored as a box, keyed by what resolved it. Each key remembers when it was last filled;
its warmth halves every `h_site` ticks, and below `cold` it is not checked. A box reopens three ways:

* **resonance**: at least `resonance` of its keys are warm and filled by this tick's winners, and it
  has gone out of resonance since it last resonated (`last_resonant < t - 1`);
* **a hole**: a blocked thought's hole finds it, through a warm key, unless it was told;
* **contradiction**: the world fails a prediction the box makes. Only this reaches a told box.

Told boxes arrive closed with no keys of the person's own (`tell`). Parked boxes, which
accumulate their keys over time, are not covered here.

## Results

* **Cooling, not deletion** (`warm_of_le`): a key warm now was warm at every earlier tick; warmth
  only falls while a key is unfilled. A filled key is warm again (`warm_self`).
* **Cold keys are never hit** (`warm_of_mem_hits`); a box whose keys are all cold cannot
  resonate (`not_resonates_of_cold`).
* **A told box reopens only by contradiction** (`told_reopens_iff`).
* **No rumination** (`not_reopens_after_resonating`): a box resonating this tick does not reopen
  by resonance next tick; it must go out of resonance first.
-/

namespace SOV.Memory

/-- `h_site`, `cold`, `resonance`. -/
structure Params where
  hSite : ℝ
  cold : ℝ
  resonance : ℝ

variable (P : Params)

/-- A key's warmth `t - last` ticks after it was last filled. -/
noncomputable def warmth (t last : ℝ) : ℝ :=
  (1 / 2 : ℝ) ^ ((t - last) / P.hSite)

/-- `warm`: a key is checked while its warmth is at least `cold`. -/
def Warm (t last : ℝ) : Prop :=
  P.cold ≤ warmth P t last

variable {P}

/-- **Cooling, not deletion**: a key warm now was warm at every earlier tick. -/
theorem warm_of_le (hh : 0 < P.hSite) {t t' last : ℝ} (hw : Warm P t last) (ht : t' ≤ t) :
    Warm P t' last := by
  refine hw.trans (Real.rpow_le_rpow_of_exponent_ge (by norm_num) (by norm_num) ?_)
  exact div_le_div_of_nonneg_right (by linarith) hh.le

/-- A key filled now is warm. -/
theorem warm_self (hc : P.cold ≤ 1) (t : ℝ) : Warm P t t := by
  simp [Warm, warmth, hc]

/-- A stored box: its keys, when each was last filled, when it last resonated (`none`: never),
and whether it was told. -/
structure Box (K : Type*) where
  keys : Finset K
  last : K → ℝ
  lastResonant : Option ℝ
  told : Bool

variable {K : Type*} (P)

open Classical in
/-- The keys this tick's winners fill (`fills`), among the warm ones. -/
noncomputable def hits (b : Box K) (t : ℝ) (fills : K → Prop) : Finset K :=
  b.keys.filter fun k ↦ Warm P t (b.last k) ∧ fills k

/-- At least `resonance` of the box's keys hit (`len(hit) / len(keys) >= resonance`). -/
def Resonates (b : Box K) (t : ℝ) (fills : K → Prop) : Prop :=
  b.keys.Nonempty ∧ P.resonance * b.keys.card ≤ (hits P b t fills).card

/-- Out of resonance since it last resonated. -/
def OutOfResonance (b : Box K) (t : ℝ) : Prop :=
  ∀ s, b.lastResonant = some s → s < t - 1

/-- Reopened by resonance. -/
def ReopensByResonance (b : Box K) (t : ℝ) (fills : K → Prop) : Prop :=
  Resonates P b t fills ∧ OutOfResonance b t

open Classical in
/-- The box after this tick's recognition: hit keys refreshed, the resonance time recorded. -/
noncomputable def after (b : Box K) (t : ℝ) (fills : K → Prop) : Box K :=
  { b with
    last := fun k ↦ if k ∈ hits P b t fills then t else b.last k
    lastResonant := if Resonates P b t fills then some t else b.lastResonant }

/-- A hole finds the box through a warm key, unless it was told. -/
def FoundByHole (b : Box K) (t : ℝ) : Prop :=
  b.told = false ∧ ∃ k ∈ b.keys, Warm P t (b.last k)

/-- The box reopens this tick, by resonance, a hole, or the world contradicting it. -/
def Reopens (b : Box K) (t : ℝ) (fills : K → Prop) (contradicted : Prop) : Prop :=
  ReopensByResonance P b t fills ∨ FoundByHole P b t ∨ contradicted

variable {P}

theorem warm_of_mem_hits {b : Box K} {t : ℝ} {fills : K → Prop} {k : K}
    (h : k ∈ hits P b t fills) : Warm P t (b.last k) := by
  classical
  simp only [hits, Finset.mem_filter] at h
  exact h.2.1

/-- **Cold keys are never hit**: a box whose keys are all cold cannot resonate. -/
theorem not_resonates_of_cold (hr : 0 < P.resonance) {b : Box K} {t : ℝ} {fills : K → Prop}
    (hc : ∀ k ∈ b.keys, ¬ Warm P t (b.last k)) : ¬ Resonates P b t fills := by
  classical
  rintro ⟨hne, hle⟩
  have : hits P b t fills = ∅ := Finset.filter_eq_empty_iff.2 fun k hk h ↦ hc k hk h.1
  rw [this, Finset.card_empty, Nat.cast_zero] at hle
  have : (0 : ℝ) < b.keys.card := by exact_mod_cast hne.card_pos
  nlinarith

/-- **A told box reopens only by contradiction**: it has no keys, so nothing resonates with it,
and holes skip it. -/
theorem told_reopens_iff {b : Box K} (ht : b.told = true) (hk : b.keys = ∅) {t : ℝ}
    {fills : K → Prop} {contradicted : Prop} :
    Reopens P b t fills contradicted ↔ contradicted := by
  refine ⟨fun h ↦ ?_, fun h ↦ Or.inr (Or.inr h)⟩
  rcases h with ⟨⟨hne, -⟩, -⟩ | ⟨hf, -⟩ | h
  · simp [hk] at hne
  · simp [ht] at hf
  · exact h

/-- **No rumination**: a box that resonated this tick does not reopen by resonance at the next. -/
theorem not_reopens_after_resonating {b : Box K} {t : ℝ} {fills fills' : K → Prop}
    (h : Resonates P b t fills) : ¬ ReopensByResonance P (after P b t fills) (t + 1) fills' := by
  classical
  rintro ⟨-, hout⟩
  have := hout t (by simp [after, h])
  linarith

end SOV.Memory
