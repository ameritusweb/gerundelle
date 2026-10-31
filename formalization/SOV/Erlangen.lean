import Mathlib.GroupTheory.GroupAction.Quotient
import Mathlib.GroupTheory.Perm.Basic
import Mathlib.Topology.MetricSpace.Basic

/-!
# Phase 6a: the Erlangen foundation and the D-metric

sov_geometry §1–2. A geometry is a transformation group with its invariants. The organism's
transforms `T` act on observation space `O`; its world (the Umwelt) is `O` modulo `T`.

## Erlangen (§1)

* **Corollary 16.1** (`invariant_iff_factors`): a reading of observations is a function on
  the Umwelt exactly when it is `T`-invariant. The organism can perceive only what its group
  preserves.
* **More transforms, fewer invariants** (`InvariantUnder.mono`): enlarging the group can only
  remove invariants, never add them. The trivial group preserves every distinction
  (`invariantUnder_bot`), and enlarging it can lose one (`invariant_lost_by_enlarging`).
  §1.3 said that growing new eyes is "the transform group T expands, new invariants appear".
  That was backwards: new receptors, as new invariants, mean a *smaller* group of
  indistinguishable transforms and a finer quotient. The doc now says "T contracts"
  (2026-10-29), with `invariant_lost_by_enlarging` as the certificate. Klein's own hierarchy
  runs this way: the projective group is larger than the Euclidean and has fewer invariants.

## The D-metric (§2)

Two states are near when their consequence profiles match: `D a b = dist (profile a)
(profile b)` for profiles in a metric space.

* `D` is a pseudometric (`D_self`, `D_comm`, `D_triangle`), zero exactly between states with
  the same profile (`D_eq_zero_iff`): consequentially identical states are one point.
* **The D-metric lives on the Umwelt exactly when every transform is consequentially null**
  (`consequentially_null_iff_invariant`, `D_smul`). §1 and §2 are then two descriptions of
  one quotient only under this condition, which the doc does not state.
* §2.2's "does not satisfy the parallelogram law" needs a linear structure that consequence
  profiles don't come with; it is not formalized.
-/

namespace SOV.Erlangen

variable (T : Type*) {O X : Type*} [Group T] [MulAction T O]

/-- The Umwelt: observation space modulo the organism's transforms. -/
abbrev Umwelt (T O : Type*) [Group T] [MulAction T O] :=
  MulAction.orbitRel.Quotient T O

/-- A reading of observations that every transform preserves. -/
def Invariant (f : O → X) : Prop :=
  ∀ (t : T) (o : O), f (t • o) = f o

/-- **Corollary 16.1.** A reading is a function on the Umwelt exactly when it is invariant. -/
theorem invariant_iff_factors (f : O → X) :
    Invariant T f ↔
      ∃ g : Umwelt T O → X, ∀ o, f o = g (Quotient.mk (MulAction.orbitRel T O) o) := by
  constructor
  · intro h
    refine ⟨Quotient.lift f fun a b hab ↦ ?_, fun _ ↦ rfl⟩
    obtain ⟨t, rfl⟩ := MulAction.mem_orbit_iff.1 (MulAction.orbitRel_apply.1 hab)
    exact h t b
  · rintro ⟨g, hg⟩ t o
    calc f (t • o) = g (Quotient.mk _ (t • o)) := hg _
      _ = g (Quotient.mk _ o) :=
        congrArg g (Quotient.sound (MulAction.orbitRel_apply.2 (MulAction.mem_orbit o t)))
      _ = f o := (hg o).symm

variable {T}

/-- A reading that every transform in subgroup `H` preserves. -/
def InvariantUnder (H : Subgroup T) (f : O → X) : Prop :=
  ∀ t ∈ H, ∀ o : O, f (t • o) = f o

/-- **More transforms, fewer invariants**: an invariant of a larger group is an invariant of
every subgroup. -/
theorem InvariantUnder.mono {H K : Subgroup T} {f : O → X} (hHK : H ≤ K)
    (h : InvariantUnder K f) : InvariantUnder H f :=
  fun t ht ↦ h t (hHK ht)

/-- The trivial group preserves every distinction. -/
theorem invariantUnder_bot (f : O → X) : InvariantUnder (⊥ : Subgroup T) f := by
  intro t ht o
  rw [Subgroup.mem_bot.1 ht, one_smul]

theorem invariantUnder_top_iff (f : O → X) : InvariantUnder (⊤ : Subgroup T) f ↔ Invariant T f :=
  ⟨fun h t ↦ h t (Subgroup.mem_top t), fun h t _ ↦ h t⟩

/-- Enlarging the group can lose an invariant: the identity reading of a two-point space is
preserved by the trivial group and not by the full permutation group. -/
theorem invariant_lost_by_enlarging :
    InvariantUnder (⊥ : Subgroup (Equiv.Perm Bool)) (id : Bool → Bool) ∧
      ¬ InvariantUnder (⊤ : Subgroup (Equiv.Perm Bool)) (id : Bool → Bool) := by
  refine ⟨invariantUnder_bot _, fun h ↦ ?_⟩
  have := h (Equiv.swap true false) (Subgroup.mem_top _) true
  simp at this

/-! ### The D-metric -/

section DMetric

variable {S P : Type*}

/-- Consequential distance: the distance between consequence profiles. -/
def D [PseudoMetricSpace P] (profile : S → P) (a b : S) : ℝ :=
  dist (profile a) (profile b)

variable [PseudoMetricSpace P] (profile : S → P)

theorem D_self (a : S) : D profile a a = 0 :=
  dist_self _

theorem D_comm (a b : S) : D profile a b = D profile b a :=
  dist_comm _ _

theorem D_triangle (a b c : S) : D profile a c ≤ D profile a b + D profile b c :=
  dist_triangle _ _ _

theorem D_nonneg (a b : S) : 0 ≤ D profile a b :=
  dist_nonneg

/-- Consequentially identical states are one point. -/
theorem D_eq_zero_iff {P' : Type*} [MetricSpace P'] (profile : S → P') (a b : S) :
    D profile a b = 0 ↔ profile a = profile b :=
  dist_eq_zero

variable [MulAction T S]

/-- If the profile is invariant, transforms don't move states consequentially. -/
theorem D_smul (h : Invariant T profile) (t : T) (a b : S) :
    D profile (t • a) b = D profile a b := by
  simp only [D, h t a]

/-- **The D-metric lives on the Umwelt exactly when every transform is consequentially
null.** -/
theorem consequentially_null_iff_invariant {P' : Type*} [MetricSpace P'] (profile : S → P') :
    (∀ (t : T) (a : S), D profile (t • a) a = 0) ↔ Invariant T profile := by
  simp only [D, dist_eq_zero, Invariant]

end DMetric

end SOV.Erlangen
