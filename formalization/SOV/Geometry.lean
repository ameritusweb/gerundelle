import Mathlib.Order.Lattice
import Mathlib.Data.Set.Prod

/-!
# The geometry sort 𝒢

A connector geometry is a receptor boundary pattern together with the set of resolutions
still feasible for it (two_sorted_core §1, sov_formal_spec §1.1). The carrier types are left
abstract: `B` (boundary patterns), `R` (resolutions).

## Encoding decisions

* A slot's relational position is its links to neighbouring slots and knowns
  (sov_formal_spec §1.1), so it lives in the web (`SOV.Web`), not in the geometry.
* two_sorted_core §1 says 𝒢 is partially ordered by feasible-set containment. With a
  boundary pattern alongside the feasible set this is only a preorder: geometries with equal
  feasible sets but different boundaries are equivalent without being equal
  (`not_antisymm`). The partial order lives on feasible sets, i.e. on `Set R`.
* `meet` intersects feasible sets and takes `⊓` on boundaries. It is a greatest lower bound
  for subsumption, and commutative/associative/idempotent on the nose when `B` is a
  meet-semilattice.
* `relProduct` changes type (`R` to `R × R'`), so it is not a binary operation on one 𝒢.
  On feasible sets it is the meet of the two pullbacks (`feasibleSet_relProduct_eq_meet`),
  which bears on the open question "does product reduce to meet over an enlarged 𝒢?"
  (two_sorted_core §6, §8).
-/

namespace SOV

/-- A connector geometry: boundary pattern and feasible resolutions. -/
@[ext]
structure ConnectorGeometry (B R : Type*) where
  boundary : B
  feasibleSet : Set R

namespace ConnectorGeometry

variable {B R : Type*}

/-! ### Subsumption -/

/-- Subsumption: `g ≤ g'` when every resolution feasible for `g` is feasible for `g'`. -/
instance : Preorder (ConnectorGeometry B R) :=
  Preorder.lift ConnectorGeometry.feasibleSet

theorem le_def {g g' : ConnectorGeometry B R} : g ≤ g' ↔ g.feasibleSet ⊆ g'.feasibleSet :=
  Iff.rfl

/-- Mutual subsumption is exactly equality of feasible sets. -/
theorem le_antisymm_iff {g g' : ConnectorGeometry B R} :
    g ≤ g' ∧ g' ≤ g ↔ g.feasibleSet = g'.feasibleSet :=
  ⟨fun h ↦ Set.Subset.antisymm h.1 h.2, fun h ↦ ⟨h.subset, h.symm.subset⟩⟩

/-- Subsumption is not antisymmetric once there are two distinct boundary patterns. -/
theorem not_antisymm [Nontrivial B] :
    ¬ ∀ g g' : ConnectorGeometry B R, g ≤ g' → g' ≤ g → g = g' := by
  intro h
  obtain ⟨b₁, b₂, hb⟩ := exists_pair_ne B
  let g₁ : ConnectorGeometry B R := ⟨b₁, ∅⟩
  let g₂ : ConnectorGeometry B R := ⟨b₂, ∅⟩
  exact hb (congrArg boundary (h g₁ g₂ (le_def.2 subset_rfl) (le_def.2 subset_rfl)))

/-! ### Meet -/

section Meet

variable [Min B]

/-- Meet: the shared sub-pattern of two geometries. -/
instance : Min (ConnectorGeometry B R) where
  min g g' := ⟨g.boundary ⊓ g'.boundary, g.feasibleSet ∩ g'.feasibleSet⟩

@[simp]
theorem boundary_meet (g g' : ConnectorGeometry B R) :
    (g ⊓ g').boundary = g.boundary ⊓ g'.boundary :=
  rfl

@[simp]
theorem feasibleSet_meet (g g' : ConnectorGeometry B R) :
    (g ⊓ g').feasibleSet = g.feasibleSet ∩ g'.feasibleSet :=
  rfl

theorem meet_le_left (g g' : ConnectorGeometry B R) : g ⊓ g' ≤ g :=
  Set.inter_subset_left

theorem meet_le_right (g g' : ConnectorGeometry B R) : g ⊓ g' ≤ g' :=
  Set.inter_subset_right

/-- `meet` is a greatest lower bound for subsumption. -/
theorem le_meet {h g g' : ConnectorGeometry B R} (hg : h ≤ g) (hg' : h ≤ g') :
    h ≤ g ⊓ g' :=
  Set.subset_inter hg hg'

end Meet

section MeetLaws

variable [SemilatticeInf B]

theorem meet_comm (g g' : ConnectorGeometry B R) : g ⊓ g' = g' ⊓ g :=
  ConnectorGeometry.ext (inf_comm _ _) (Set.inter_comm _ _)

theorem meet_assoc (g g' g'' : ConnectorGeometry B R) : g ⊓ g' ⊓ g'' = g ⊓ (g' ⊓ g'') :=
  ConnectorGeometry.ext (inf_assoc _ _ _) (Set.inter_assoc _ _ _)

theorem meet_idem (g : ConnectorGeometry B R) : g ⊓ g = g :=
  ConnectorGeometry.ext (inf_idem _) (Set.inter_self _)

end MeetLaws

/-! ### Relational product -/

section Product

variable {B' R' B'' R'' : Type*}

/-- Relational product: pair the boundaries and the feasible resolutions. -/
def relProduct (g : ConnectorGeometry B R) (g' : ConnectorGeometry B' R') :
    ConnectorGeometry (B × B') (R × R') :=
  ⟨(g.boundary, g'.boundary), g.feasibleSet ×ˢ g'.feasibleSet⟩

@[simp]
theorem feasibleSet_relProduct (g : ConnectorGeometry B R) (g' : ConnectorGeometry B' R') :
    (g.relProduct g').feasibleSet = g.feasibleSet ×ˢ g'.feasibleSet :=
  rfl

/-- On feasible sets, the product is the meet of the pullbacks along the two projections.
This is the precise sense in which "product reduces to meet". -/
theorem feasibleSet_relProduct_eq_meet (g : ConnectorGeometry B R)
    (g' : ConnectorGeometry B' R') :
    (g.relProduct g').feasibleSet = Prod.fst ⁻¹' g.feasibleSet ∩ Prod.snd ⁻¹' g'.feasibleSet :=
  Set.prod_eq _ _

theorem relProduct_mono {g₁ g₂ : ConnectorGeometry B R} {h₁ h₂ : ConnectorGeometry B' R'}
    (hg : g₁ ≤ g₂) (hh : h₁ ≤ h₂) : g₁.relProduct h₁ ≤ g₂.relProduct h₂ :=
  Set.prod_mono hg hh

/-- Commutativity, up to swapping coordinates. -/
theorem relProduct_comm (g : ConnectorGeometry B R) (g' : ConnectorGeometry B' R')
    (x : R) (y : R') :
    (x, y) ∈ (g.relProduct g').feasibleSet ↔ (y, x) ∈ (g'.relProduct g).feasibleSet := by
  simp [and_comm]

/-- Associativity, up to reassociating coordinates. -/
theorem relProduct_assoc (g : ConnectorGeometry B R) (g' : ConnectorGeometry B' R')
    (g'' : ConnectorGeometry B'' R'') (x : R) (y : R') (z : R'') :
    ((x, y), z) ∈ ((g.relProduct g').relProduct g'').feasibleSet ↔
      (x, (y, z)) ∈ (g.relProduct (g'.relProduct g'')).feasibleSet := by
  simp [and_assoc]

/-- Product distributes over meet in the left argument. -/
theorem relProduct_meet_left [SemilatticeInf B] [SemilatticeInf B']
    (g₁ g₂ : ConnectorGeometry B R) (h : ConnectorGeometry B' R') :
    (g₁ ⊓ g₂).relProduct h = g₁.relProduct h ⊓ g₂.relProduct h :=
  ConnectorGeometry.ext (by simp [relProduct]) (by simp [relProduct, Set.inter_prod])

end Product

end ConnectorGeometry

end SOV
