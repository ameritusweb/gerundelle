import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.Order.Field.Basic
import SOV.Provenance

/-!
# Selection: the author's telling and its score

A formalization of the provenance of a told scene (`fiction/story.py`) and of the author's
score (`fiction/rung7.py`, `score` and `search`).

## A scene is a provenance log

Each plan (one sentence) carries `refs`, the earlier plans it depends on. `tell` builds the plans
in order, citing only plans already made (`add` reads `plan_of` before appending). Then three
passes, `iterate`, `combine` and `summarize`, rebuild the list, remap each plan's refs, and keep
only those strictly before the plan: `remap[r] < out.index(p)`. `out.index` finds the first plan
equal to `p`, at or before its own position, so the code's filter is at least as strict as
filtering by position.

A scene is therefore a `Cited` log, as the ledger is (`SOV.Provenance`), and:

* **Telling appends sourced sentences** (`sourced_append`): `tell`'s plans form a sourced log.
* **Every rebuilding pass leaves a sourced scene** (`sourced_rebuild`), whatever its remap and
  whatever the plans before it, for any filter bound at or before each plan's position.
* **No sentence is in its own chain of dependence** (`scene_not_transGen_self`), and dependence
  is well-founded (`scene_wellFounded`): `Provenance.wellFounded_cites`, the ledger's theorem,
  applied to the story.

## The author's score

`search` values a story as `held × max(rise, 0)`. `held` is the reader's entropy over endings,
each sentence weighted by how far into the story it is (`(i + 1) / n`), normalized: suspense held
late. `rise` is how far the text moved the reader toward the ending it closes on: the ending's
probability just before it became certain, minus its probability at the start. The entropies are
taken as given here, with only their nonnegativity used.

* **A fiat scores zero** (`value_eq_zero_of_rise_nonpos`, `value_eq_zero_of_unforeshadowed`): an
  ending no likelier just before it became certain than at the start earns nothing, however much
  suspense was held.
* **Value needs suspense and foreshadowing both** (`value_pos_iff`).
-/

namespace SOV.Selection

open Provenance

/-! ### A scene is a provenance log -/

variable {α : Type*}

/-- Entry `n` cites only entries before `n`. -/
def SourcedAt (log : List (Cited α)) : Prop :=
  ∀ n (h : n < log.length), ∀ m ∈ log[n].sources, m < n

theorem sourced_iff (log : List (Cited α)) : Sourced log ↔ SourcedAt log :=
  ⟨fun h n hn m hm ↦ h m n ⟨hn, hm⟩, fun h m n ⟨hn, hm⟩ ↦ h n hn m hm⟩

/-- **Telling appends sourced sentences**: a plan citing only plans already made keeps the scene
sourced. -/
theorem sourced_append {log : List (Cited α)} (h : Sourced log) (e : α) {srcs : List ℕ}
    (hs : ∀ m ∈ srcs, m < log.length) : Sourced (log ++ [⟨e, srcs⟩]) := by
  rw [sourced_iff] at h ⊢
  intro n hn m hm
  rw [List.length_append, List.length_singleton] at hn
  rcases Nat.lt_succ_iff_lt_or_eq.1 hn with hlt | rfl
  · rw [List.getElem_append_left hlt] at hm
    exact h n hlt m hm
  · rw [List.getElem_append_right (le_refl _)] at hm
    simpa using hs m (by simpa using hm)

/-- One rebuilding pass (`iterate`, `combine`, `summarize`): each plan's refs are remapped, and only
those before `bound n` are kept, `bound n` at or before the plan's position `n`. -/
def rebuild (remap : ℕ → Option ℕ) (bound : ℕ → ℕ) (plans : List (Cited α)) : List (Cited α) :=
  plans.mapIdx fun n p ↦ ⟨p.event, (p.sources.filterMap remap).filter fun m ↦ m < bound n⟩

/-- **Every rebuilding pass leaves a sourced scene.** -/
theorem sourced_rebuild (remap : ℕ → Option ℕ) {bound : ℕ → ℕ} (hb : ∀ n, bound n ≤ n)
    (plans : List (Cited α)) : Sourced (rebuild remap bound plans) := by
  rw [sourced_iff]
  intro n hn m hm
  simp only [rebuild, List.getElem_mapIdx, List.mem_filter, decide_eq_true_eq] at hm
  exact lt_of_lt_of_le hm.2 (hb n)

/-- Dependence among a scene's sentences is well-founded. -/
theorem scene_wellFounded (remap : ℕ → Option ℕ) {bound : ℕ → ℕ} (hb : ∀ n, bound n ≤ n)
    (plans : List (Cited α)) : WellFounded (Cites (rebuild remap bound plans)) :=
  wellFounded_cites (sourced_rebuild remap hb plans)

/-- **No sentence is in its own chain of dependence.** -/
theorem scene_not_transGen_self (remap : ℕ → Option ℕ) {bound : ℕ → ℕ} (hb : ∀ n, bound n ≤ n)
    (plans : List (Cited α)) (n : ℕ) :
    ¬ Relation.TransGen (Cites (rebuild remap bound plans)) n n :=
  not_transGen_self (sourced_rebuild remap hb plans) n

/-! ### The author's score -/

/-- Suspense held late: each sentence's entropy weighted by its position `(i + 1)`, normalized
(the code's `/ n` cancels). -/
noncomputable def held (hs : List ℝ) : ℝ :=
  (∑ i : Fin hs.length, ((i : ℝ) + 1) * hs[i]) / ∑ i : Fin hs.length, ((i : ℝ) + 1)

theorem held_nonneg {hs : List ℝ} (h : ∀ x ∈ hs, 0 ≤ x) : 0 ≤ held hs := by
  refine div_nonneg (Finset.sum_nonneg fun i _ ↦ mul_nonneg (by positivity) ?_)
    (Finset.sum_nonneg fun i _ ↦ by positivity)
  exact h _ (List.getElem_mem _)

/-- Foreshadowing: the ending's probability just before it became certain, minus at the start. -/
def rise (before prior : ℝ) : ℝ :=
  before - prior

/-- `search`'s value: suspense held late, times the ending earned. -/
def value (held rise : ℝ) : ℝ :=
  held * max rise 0

/-- **A fiat scores zero.** -/
theorem value_eq_zero_of_rise_nonpos {h r : ℝ} (hr : r ≤ 0) : value h r = 0 := by
  simp [value, max_eq_right hr]

/-- An ending no likelier just before it became certain than at the start earns nothing. -/
theorem value_eq_zero_of_unforeshadowed {h before prior : ℝ} (hb : before ≤ prior) :
    value h (rise before prior) = 0 :=
  value_eq_zero_of_rise_nonpos (by simp [rise, hb])

/-- **Value needs suspense and foreshadowing both.** -/
theorem value_pos_iff {h r : ℝ} (hh : 0 ≤ h) : 0 < value h r ↔ 0 < h ∧ 0 < r := by
  constructor
  · intro hv
    by_contra hc
    rcases not_and_or.1 hc with h0 | r0
    · have : h = 0 := le_antisymm (not_lt.1 h0) hh
      simp [value, this] at hv
    · simp [value_eq_zero_of_rise_nonpos (not_lt.1 r0)] at hv
  · rintro ⟨h0, r0⟩
    exact mul_pos h0 (lt_max_of_lt_left r0)

end SOV.Selection
