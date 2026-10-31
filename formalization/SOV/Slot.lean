import Mathlib.Data.Finset.Filter
import Mathlib.Data.Sym.Sym2
import SOV.Geometry
import SOV.Ledger

/-!
# Slots, knowns, and the web

A slot is a pair (g, ℓ) of a geometry and its receipts. A known is a slot whose feasible set
is a singleton, with its ledger intact (two_sorted_core §1). The web is the typed graph of
slots, constraints, and knowns.

## Encoding decisions

* The etymology ledger is web-wide: pool, partition and lien span several slots. A slot's
  ledger is the view of the receipts filed on it (`Web.slot`). Receipts filed on `none` form
  the unassigned pool that Fit writes to on a total miss and Individuate carves from.
* Constraints are stored direction-free (TS-2): an edge is keyed by an unordered pair
  `Sym2 S`, so `constraint s(i, j) = constraint s(j, i)` holds by construction. These links
  are the slots' relational positions (sov_formal_spec §1.1).
* `IsKnown` asks for exactly one feasible resolution. `Set.Subsingleton` also admits the
  empty set, which would make an infeasible slot a known (`subsingleton_not_known`).
* Knowns are computed from slots rather than stored separately, so they can't drift.
* The web splits into its geometry part `GeomWeb` and the ledger, so a base move can be
  typed `GeomWeb → GeomWeb` and C1 (base-definability) holds by construction.
* Well-formedness (edges only join slots of the web) is a predicate, not a field.
-/

namespace SOV

/-- A slot: a geometry paired with the receipts filed on it. -/
structure Slot (B R S A C E : Type*) where
  geometry : ConnectorGeometry B R
  receipts : List (Receipt S A C E)

namespace Slot

variable {B R S A C E : Type*}

/-- A slot is known when exactly one resolution is feasible. -/
def IsKnown (s : Slot B R S A C E) : Prop :=
  ∃ x, s.geometry.feasibleSet = {x}

theorem isKnown_iff (s : Slot B R S A C E) :
    s.IsKnown ↔ s.geometry.feasibleSet.Nonempty ∧ s.geometry.feasibleSet.Subsingleton :=
  Set.exists_eq_singleton_iff_nonempty_subsingleton

/-- `Set.Subsingleton` is too weak: a slot with no feasible resolution satisfies it. -/
theorem subsingleton_not_known (s : Slot B R S A C E) (h : s.geometry.feasibleSet = ∅) :
    s.geometry.feasibleSet.Subsingleton ∧ ¬ s.IsKnown := by
  refine ⟨h ▸ Set.subsingleton_empty, fun ⟨x, hx⟩ ↦ ?_⟩
  exact Set.singleton_ne_empty x (hx.symm.trans h)

end Slot

/-- A known: a slot with exactly one feasible resolution. -/
def Known (B R S A C E : Type*) := { s : Slot B R S A C E // s.IsKnown }

/-- The geometry part of the web: slots, their geometries, direction-free labelled
constraints, and the disequality cache that Exclude writes. Base moves act on this alone. -/
@[ext]
structure GeomWeb (S K B R : Type*) where
  slots : Finset S
  geometry : S → ConnectorGeometry B R
  constraint : Sym2 S → Option K
  excluded : Set (Sym2 S)

namespace GeomWeb

variable {S K B R : Type*}

/-- Constraints and exclusions only join slots of the web. -/
def WellFormed (gw : GeomWeb S K B R) : Prop :=
  (∀ e k, gw.constraint e = some k → ∀ i ∈ e, i ∈ gw.slots) ∧
    ∀ e ∈ gw.excluded, ∀ i ∈ e, i ∈ gw.slots

theorem constraint_comm (gw : GeomWeb S K B R) (i j : S) :
    gw.constraint s(i, j) = gw.constraint s(j, i) := by
  rw [Sym2.eq_swap]

variable [DecidableEq S]

/-- Replace the geometry of slot `i`. -/
def setGeometry (gw : GeomWeb S K B R) (i : S) (g : ConnectorGeometry B R) :
    GeomWeb S K B R :=
  { gw with geometry := Function.update gw.geometry i g }

/-- Add slot `n` with geometry `g`. -/
def addSlot (gw : GeomWeb S K B R) (n : S) (g : ConnectorGeometry B R) : GeomWeb S K B R :=
  { gw with slots := insert n gw.slots, geometry := Function.update gw.geometry n g }

end GeomWeb

/-- The web: its geometry part and the etymology ledger. -/
structure Web (S K B R A C E : Type*) where
  geom : GeomWeb S K B R
  ledger : Ledger S A C E

namespace Web

variable {S K B R A C E : Type*} [DecidableEq S]

/-- The slot at `i`: its geometry and the receipts filed on it. -/
def slot (w : Web S K B R A C E) (i : S) : Slot B R S A C E :=
  ⟨w.geom.geometry i, w.ledger.receipts.filter (·.slot = some i)⟩

/-- The unassigned pool: receipts not yet filed on any slot. -/
def unassigned (w : Web S K B R A C E) : List (Receipt S A C E) :=
  w.ledger.receipts.filter (·.slot.isNone)

open Classical in
/-- The knowns of a web: its slots with exactly one feasible resolution. -/
noncomputable def knowns (w : Web S K B R A C E) : Finset S :=
  w.geom.slots.filter fun i ↦ (w.slot i).IsKnown

theorem mem_knowns (w : Web S K B R A C E) (i : S) :
    i ∈ w.knowns ↔ i ∈ w.geom.slots ∧ (w.slot i).IsKnown := by
  classical
  simp [knowns]

theorem knowns_subset (w : Web S K B R A C E) : w.knowns ⊆ w.geom.slots :=
  fun _ hi ↦ ((w.mem_knowns _).1 hi).1

end Web

end SOV
