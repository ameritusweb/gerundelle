import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

/-!
# The two-stage Attest discount

TS-5 (two_sorted_core §5.5) resolves the Attest discount `c₀` as a prior times a posterior.
`sov.py` (`attest`, `bill_attest_outcome`) implements it as

  `c₀ = base × match × reliability`

* `base` is the cross-ledger discount, `C0_DISCOUNT = 0.5` in `social_ledger.py`;
* `match`, the stage-1 prior, is the overlap of the posed and local geometries' family
  thresholds, `Σ min / Σ max` (imports are refused below 0.1);
* `reliability`, the stage-2 posterior, is kept per exporter. It starts at 1, and each billed
  outcome moves it a fraction `α = 0.1` toward 1 if the import survived and toward 0 if not.

## Results

* **`c₀` stays in `[0, 1]`** (`discount_mem`), so the market theorems of `SOV.Market`, which
  assume `c₀ ∈ [0, 1]`, apply at every stage of calibration.
* **The initial value** (`discount_nil`) is `base × match`. It is the docs' 0.5 exactly when
  the match is perfect (`discount_nil_perfect`, with `matchScore_self`).
* An exporter whose imports always survive keeps reliability 1 (`reliability_all_survive`);
  one whose imports always fail decays geometrically (`reliability_all_fail`).
* **The implementation is order-dependent** (`reliability_order_dependent`): one survival and
  one failure leave 0.9 in one order and 0.91 in the other.

## Specification and implementation

TS-5 specifies that the posterior anneals "exactly as T57 anneals an entry", a
schedule-independent decay (`LedgerState.annealAt_comm`). The code's moving average is a
tractable approximation of that schedule, not the specification. The two levels differ in
exactly one checkable way: the specification doesn't depend on outcome order, and the
approximation does (`reliability_order_dependent` measures the gap).
-/

namespace SOV.Discount

open Finset

/-- Stage 1 prior: the overlap of two threshold vectors, `Σ min / Σ max`. -/
noncomputable def matchScore {ι : Type*} (s : Finset ι) (p q : ι → ℝ) : ℝ :=
  (∑ i ∈ s, min (p i) (q i)) / ∑ i ∈ s, max (p i) (q i)

theorem matchScore_nonneg {ι : Type*} (s : Finset ι) {p q : ι → ℝ} (hp : ∀ i, 0 ≤ p i)
    (hq : ∀ i, 0 ≤ q i) : 0 ≤ matchScore s p q :=
  div_nonneg (sum_nonneg fun i _ ↦ le_min (hp i) (hq i))
    (sum_nonneg fun i _ ↦ (hp i).trans (le_max_left _ _))

theorem matchScore_le_one {ι : Type*} (s : Finset ι) {p q : ι → ℝ} (hp : ∀ i, 0 ≤ p i) :
    matchScore s p q ≤ 1 :=
  div_le_one_of_le₀ (sum_le_sum fun _ _ ↦ min_le_max)
    (sum_nonneg fun i _ ↦ (hp i).trans (le_max_left _ _))

/-- A geometry matches itself perfectly, given any positive threshold. -/
theorem matchScore_self {ι : Type*} (s : Finset ι) (p : ι → ℝ) (h : ∑ i ∈ s, p i ≠ 0) :
    matchScore s p p = 1 := by
  simp [matchScore, h]

/-- One billed outcome (`bill_attest_outcome`): move a fraction `α` toward 1 if the import
survived, toward 0 if not. -/
def bill (α r : ℝ) (survived : Bool) : ℝ :=
  (1 - α) * r + α * (if survived then 1 else 0)

/-- Stage 2 posterior: reliability after a history of billed outcomes, starting from 1. -/
def reliability (α : ℝ) (outcomes : List Bool) : ℝ :=
  outcomes.foldl (bill α) 1

/-- The effective Attest discount. -/
noncomputable def discount (base m α : ℝ) (outcomes : List Bool) : ℝ :=
  base * m * reliability α outcomes

variable {α : ℝ}

theorem bill_mem (h₀ : 0 ≤ α) (h₁ : α ≤ 1) {r : ℝ} (hr₀ : 0 ≤ r) (hr₁ : r ≤ 1) (b : Bool) :
    0 ≤ bill α r b ∧ bill α r b ≤ 1 := by
  unfold bill
  cases b <;> simp <;> constructor <;> nlinarith

theorem foldl_bill_mem (h₀ : 0 ≤ α) (h₁ : α ≤ 1) (outcomes : List Bool) {r : ℝ}
    (hr₀ : 0 ≤ r) (hr₁ : r ≤ 1) :
    0 ≤ outcomes.foldl (bill α) r ∧ outcomes.foldl (bill α) r ≤ 1 := by
  induction outcomes generalizing r with
  | nil => exact ⟨hr₀, hr₁⟩
  | cons b bs ih =>
    have := bill_mem h₀ h₁ hr₀ hr₁ b
    exact ih this.1 this.2

theorem reliability_mem (h₀ : 0 ≤ α) (h₁ : α ≤ 1) (outcomes : List Bool) :
    0 ≤ reliability α outcomes ∧ reliability α outcomes ≤ 1 :=
  foldl_bill_mem h₀ h₁ outcomes zero_le_one le_rfl

/-- **`c₀` stays in `[0, 1]`** at every stage of calibration. -/
theorem discount_mem {base m : ℝ} (hb₀ : 0 ≤ base) (hb₁ : base ≤ 1) (hm₀ : 0 ≤ m)
    (hm₁ : m ≤ 1) (h₀ : 0 ≤ α) (h₁ : α ≤ 1) (outcomes : List Bool) :
    0 ≤ discount base m α outcomes ∧ discount base m α outcomes ≤ 1 := by
  obtain ⟨hr₀, hr₁⟩ := reliability_mem h₀ h₁ outcomes
  have hbm : base * m ≤ 1 := by nlinarith
  unfold discount
  exact ⟨mul_nonneg (mul_nonneg hb₀ hm₀) hr₀, by nlinarith [mul_nonneg hb₀ hm₀]⟩

/-- **The initial value**: with no billing history, `c₀ = base × match`. -/
theorem discount_nil (base m : ℝ) : discount base m α [] = base * m := by
  simp [discount, reliability]

/-- With a perfect match and no history, `c₀` is the base discount: the docs' 0.5. -/
theorem discount_nil_perfect : discount (1 / 2) 1 α [] = 1 / 2 := by
  simp [discount_nil]

/-- An exporter whose imports always survive keeps reliability 1. -/
theorem reliability_all_survive (n : ℕ) : reliability α (List.replicate n true) = 1 := by
  suffices ∀ r, r = 1 → (List.replicate n true).foldl (bill α) r = 1 from this 1 rfl
  induction n with
  | zero => exact fun r h ↦ h
  | succ n ih =>
    intro r h
    rw [List.replicate_succ, List.foldl_cons]
    exact ih _ (by simp [bill, h])

/-- An exporter whose imports always fail decays geometrically. -/
theorem reliability_all_fail (n : ℕ) :
    reliability α (List.replicate n false) = (1 - α) ^ n := by
  suffices ∀ r, (List.replicate n false).foldl (bill α) r = (1 - α) ^ n * r by
    simpa [reliability] using this 1
  induction n with
  | zero => simp
  | succ n ih =>
    intro r
    rw [List.replicate_succ, List.foldl_cons, ih]
    simp [bill]
    ring

/-- **The posterior is order-dependent**: at the code's rate `α = 0.1`, a survival then a
failure leaves 0.9, and a failure then a survival leaves 0.91. -/
theorem reliability_order_dependent :
    reliability (1 / 10) [true, false] = 9 / 10 ∧
      reliability (1 / 10) [false, true] = 91 / 100 := by
  constructor <;> norm_num [reliability, bill]

end SOV.Discount
