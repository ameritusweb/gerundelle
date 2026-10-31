import Mathlib.GroupTheory.Perm.Basic
import Mathlib.Tactic.Group
import Mathlib.Order.Lattice
import Mathlib.Data.List.Perm.Basic

/-!
# Phase 6b: transport and holonomy

sov_geometry §4.1–4.4: Transfer is parallel transport of slot geometry between domains;
curvature is holonomy, the failure of transport around a loop to return; P53 predicts
stable, path-dependent holonomy at analogy-failure loci and zero holonomy where Transfer is
free.

## Invertible transport

Let `τ i j` transport geometry from domain `i` to domain `j`, as a permutation of a common
geometry type. The holonomy of the triangle `i → j → k → i` is the composite transport.

* **Flat iff trivializable** (`flat_iff_trivializable`): every triangle has trivial holonomy
  (and staying put transports nothing) exactly when there are global coordinates `φ` with
  `τ i j = φ j * (φ i)⁻¹`. Then every transfer factors through one common frame. This is §4.3's
  "flat regions certify free Transfer", made precise.

## Transfer as the algebra defines it

The operator algebra derives Transfer as Abstract then Constrain (sov_operators §2.1), and both
are meets. Take transport through domain `d` to be `g ↦ g ⊓ d`, in any meet-semilattice. Then
the holonomy of a loop through domains `ds` is `loop g ds`, and:

* it only narrows (`loop_le`) and is idempotent (`loop_idem`): going round twice is going
  round once, so holonomy does not accumulate the way a rotation does;
* **it doesn't depend on the path** (`loop_perm`): any reordering of the loop's domains gives
  the same result.

So P53's "path-dependent mismatch" cannot come from meet-only Transfer. (Phase 1's
`ConnectorGeometry` is only a preorder, so these results are stated for a meet-semilattice
such as `Set R` or the propagation order.)

## Relabel: the vocabulary-mapping component of Transfer

Transfer gains a primitive that carries geometry through a vocabulary map `σ` between domains
(`Operator.relabel`, added 2026-10-29). On feasible sets a transport step is now a meet or a
relabel (`Step`), and with relabels:

* **holonomy can be path-dependent** (`relabel_path_dependent`): relabel-then-meet and
  meet-then-relabel give different results, so P53 is expressible;
* **holonomy can accumulate** (`relabel_accumulates`): one loop moves the geometry and a
  second brings it back, the rotation-like behaviour meets can't show (`loop_idem`);
* **Relabel is primitive** (`relabel_not_meets`): no composite of meets produces it, since
  meets only narrow and a relabel can move a geometry off itself.
-/

namespace SOV.Holonomy

section Invertible

variable {ι G : Type*} (τ : ι → ι → Equiv.Perm G)

/-- Holonomy of the triangle `i → j → k → i`: transport to `j`, then `k`, then back. -/
def hol (i j k : ι) : Equiv.Perm G :=
  τ k i * τ j k * τ i j

/-- Flat: staying put transports nothing, and every triangle returns unchanged. -/
def Flat : Prop :=
  (∀ i, τ i i = 1) ∧ ∀ i j k, hol τ i j k = 1

/-- **Flat iff trivializable**: zero holonomy everywhere is exactly the existence of global
coordinates through which every transfer factors. -/
theorem flat_iff_trivializable [Nonempty ι] :
    Flat τ ↔ ∃ φ : ι → Equiv.Perm G, ∀ i j, τ i j = φ j * (φ i)⁻¹ := by
  constructor
  · rintro ⟨hid, htri⟩
    obtain ⟨o⟩ := ‹Nonempty ι›
    refine ⟨fun i ↦ τ o i, fun i j ↦ ?_⟩
    have e₁ : τ j o * τ i j = (τ o i)⁻¹ := eq_inv_of_mul_eq_one_left (htri o i j)
    have e₂ : τ j o = (τ o j)⁻¹ :=
      eq_inv_of_mul_eq_one_left (by simpa [hol, hid] using htri o j o)
    calc τ i j = (τ j o)⁻¹ * (τ j o * τ i j) := by group
      _ = τ o j * (τ o i)⁻¹ := by rw [e₁, e₂, inv_inv]
  · rintro ⟨φ, hφ⟩
    refine ⟨fun i ↦ by rw [hφ, mul_inv_cancel], fun i j k ↦ ?_⟩
    rw [hol, hφ, hφ, hφ]
    group

/-- In a flat region, transfer from `i` to `k` is the same directly or through `j`. -/
theorem Flat.comp {τ : ι → ι → Equiv.Perm G} [Nonempty ι] (h : Flat τ) (i j k : ι) :
    τ j k * τ i j = τ i k := by
  obtain ⟨φ, hφ⟩ := (flat_iff_trivializable τ).1 h
  rw [hφ, hφ, hφ]
  group

end Invertible

section Meet

variable {α : Type*} [SemilatticeInf α]

/-- Holonomy of meet-based Transfer: transport `g` through each domain of `ds` in turn. -/
def loop (g : α) (ds : List α) : α :=
  ds.foldl (· ⊓ ·) g

theorem le_loop_iff {x g : α} {ds : List α} : x ≤ loop g ds ↔ x ≤ g ∧ ∀ d ∈ ds, x ≤ d := by
  induction ds generalizing g with
  | nil => simp [loop]
  | cons d ds ih =>
    change x ≤ loop (g ⊓ d) ds ↔ _
    rw [ih]
    simp [le_inf_iff, and_assoc]

/-- Meet-based holonomy only narrows. -/
theorem loop_le (g : α) (ds : List α) : loop g ds ≤ g :=
  (le_loop_iff.1 le_rfl).1

/-- Meet-based holonomy is idempotent: going round twice is going round once. -/
theorem loop_idem (g : α) (ds : List α) : loop (loop g ds) ds = loop g ds :=
  le_antisymm (loop_le _ _) (le_loop_iff.2 ⟨le_rfl, (le_loop_iff.1 le_rfl).2⟩)

/-- **Meet-based holonomy doesn't depend on the path**: reordering the loop's domains changes
nothing. -/
theorem loop_perm (g : α) {ds ds' : List α} (h : ds.Perm ds') : loop g ds = loop g ds' :=
  le_antisymm
    (le_loop_iff.2 ⟨loop_le _ _, fun d hd ↦ (le_loop_iff.1 le_rfl).2 d (h.mem_iff.2 hd)⟩)
    (le_loop_iff.2 ⟨loop_le _ _, fun d hd ↦ (le_loop_iff.1 le_rfl).2 d (h.mem_iff.1 hd)⟩)

end Meet

section Relabel

/-- One transport step on feasible sets: meet with a domain's geometry, or relabel through a
vocabulary map. -/
inductive Step (R : Type*)
  | meet (d : Set R)
  | relabel (σ : R ≃ R)

/-- Apply one transport step. -/
def Step.apply {R : Type*} : Step R → Set R → Set R
  | .meet d, g => g ∩ d
  | .relabel σ, g => σ '' g

/-- Transport a geometry along a list of steps. -/
def transport {R : Type*} (steps : List (Step R)) (g : Set R) : Set R :=
  steps.foldl (fun g s ↦ s.apply g) g

/-- Meet-only transport is `loop`. -/
theorem transport_meets {R : Type*} (ds : List (Set R)) (g : Set R) :
    transport (ds.map Step.meet) g = loop g ds := by
  induction ds generalizing g with
  | nil => rfl
  | cons d ds ih => exact ih (g ∩ d)

/-- **Relabel makes holonomy path-dependent**: relabelling then meeting differs from meeting
then relabelling. -/
theorem relabel_path_dependent :
    transport [.relabel (Equiv.swap true false), .meet {true}] {true} ≠
      transport [.meet {true}, .relabel (Equiv.swap true false)] {true} := by
  simp [transport, Step.apply]

/-- **Relabel's holonomy accumulates**: one loop moves the geometry, a second brings it back. -/
theorem relabel_accumulates :
    transport [.relabel (Equiv.swap true false)] {true} ≠ {true} ∧
      transport [.relabel (Equiv.swap true false), .relabel (Equiv.swap true false)] {true} =
        {true} := by
  simp [transport, Step.apply]

/-- **Relabel is primitive**: no composite of meets produces it. -/
theorem relabel_not_meets :
    ¬ ∃ ds : List (Set Bool), ∀ g, loop g ds = Equiv.swap true false '' g := by
  rintro ⟨ds, h⟩
  have := loop_le ({true} : Set Bool) ds
  rw [h] at this
  simp at this

end Relabel

end SOV.Holonomy
