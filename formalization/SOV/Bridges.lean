import SOV.Firewall
import SOV.Provenance
import SOV.Holonomy
import SOV.Pacing
import SOV.Market
import SOV.Erlangen
import SOV.Affect

/-!
# Bridges: the stand-alone modules on the SOV web

`SOV.Holonomy`, `SOV.Pacing`, `SOV.Market` and `SOV.Erlangen` are stated over generic carriers.
This file instantiates each on the SOV web, so their theorems are about the operators, the ledger
and the routing of data, not only about structures like them.

* **Transport is the operators' geometry** (`relabel_is_transport`, `constrain_is_transport`):
  Relabel's new slot is `Holonomy.Step.relabel` applied to its source, and Constrain is
  `Holonomy.Step.meet` with the constraining slot. The holonomy results (`relabel_path_dependent`,
  `relabel_accumulates`, `relabel_not_meets`) are about these moves.
* **Reading the ledger in order is a curriculum** (`reading_in_order_valid`,
  `ledger_curriculum_geodesic`): with citation as the prerequisite relation, an event-sourced
  log's entries learned in log order form a valid curriculum, and every valid curriculum over
  them is a geodesic (`Pacing.card_learn`).
* **Market trials are ledger receipts** (`took_trials`): read off the ledger, a slot's funding in
  the market is its lived accruals at weight 1 plus its attested imports at `c₀`. Imagined
  content has no ledger event, so it yields no trial.
* **Perception and affect are one property** (`invariant_iff_factorsThrough`): a reading is
  invariant under the agent's transforms exactly when it factors through the quotient map to the
  Umwelt. `Affect.register_phases_factor` is the same property for affect, with the register and
  last tick as the view.
* **Fit routes by the Umwelt** (`fit_fiber_smul`, `fit_factors_through_umwelt`): when a slot's
  feasible set is invariant under the agent's transforms, what Fit writes for a datum depends
  only on the datum's point in the Umwelt.
-/

namespace SOV.Bridges

/-! ### Transport is the operators' geometry -/

section Transport

open Holonomy

variable {S K B R A C E : Type*} [DecidableEq S] [Min B] [GeometryAlgebra B R]

/-- Relabel's new slot is the transport step `relabel σ` applied to its source slot. -/
theorem relabel_is_transport (i n : S) (σ : R ≃ R) (w : Web S K B R A C E) :
    (((Operator.relabel i n σ : Operator S B R A C E).apply w).geom.geometry n).feasibleSet =
      Step.apply (.relabel σ) (w.geom.geometry i).feasibleSet := by
  simp [Operator.apply, Operator.base, GeomWeb.addSlot, Step.apply]

/-- Constrain is the transport step `meet` with the constraining slot. -/
theorem constrain_is_transport (i j : S) (w : Web S K B R A C E) :
    (((Operator.constrain i j : Operator S B R A C E).apply w).geom.geometry i).feasibleSet =
      Step.apply (.meet (w.geom.geometry j).feasibleSet) (w.geom.geometry i).feasibleSet := by
  simp [Operator.apply, Operator.base, GeomWeb.setGeometry, Step.apply]

end Transport

/-! ### Reading the ledger in order is a curriculum -/

section Curriculum

open Provenance Pacing

variable {α : Type*}

theorem learn_range (k : ℕ) : learn ∅ (List.range k) = Finset.range k := by
  induction k with
  | zero => rfl
  | succ k ih =>
    rw [List.range_succ, learn_append, ih]
    simp [learn, Finset.range_add_one]

/-- **Reading an event-sourced log in order is a valid curriculum**, citation as prerequisite:
each entry is on the fringe when it is read. -/
theorem reading_in_order_valid {log : List (Cited α)} (h : Sourced log) (k : ℕ) :
    Valid (Cites log) ∅ (List.range k) := by
  induction k with
  | zero => trivial
  | succ k ih =>
    rw [List.range_succ, valid_append, learn_range]
    exact ⟨ih, ⟨by simp, fun a ha ↦ by simpa using h a k ha⟩, trivial⟩

/-- Every valid curriculum over a log's citations adds one entry per step. -/
theorem ledger_curriculum_geodesic (log : List (Cited α)) {cs : List ℕ}
    (h : Valid (Cites log) ∅ cs) : (learn ∅ cs).card = cs.length := by
  simpa using card_learn h

end Curriculum

/-! ### Market trials are ledger receipts -/

section Market

open Market

variable {S A C E : Type*} [DecidableEq S]

/-- The trial a ledger event is on slot `s`: a lived accrual is a lived take, an attested import a
told one. -/
def trialOn (s : S) : FiberEvent S A C E → Option Trial
  | .accrue (some s') (.lived _ _) => if s' = s then some ⟨.lived, true⟩ else none
  | .discountTransfer s' _ _ => if s' = s then some ⟨.told, true⟩ else none
  | _ => none

/-- Lived accruals on slot `s`. -/
def livedOn (s : S) : FiberEvent S A C E → ℕ
  | .accrue (some s') (.lived _ _) => if s' = s then 1 else 0
  | _ => 0

/-- Attested imports onto slot `s`. -/
def toldOn (s : S) : FiberEvent S A C E → ℕ
  | .discountTransfer s' _ _ => if s' = s then 1 else 0
  | _ => 0

theorem took_append (c₀ : ℝ) (l₁ l₂ : List Trial) :
    took c₀ (l₁ ++ l₂) = took c₀ l₁ + took c₀ l₂ := by
  simp [took]

/-- One event's trial, weighed. -/
theorem took_trialOn (c₀ : ℝ) (s : S) (e : FiberEvent S A C E) :
    took c₀ (trialOn s e).toList = (livedOn s e : ℝ) + c₀ * (toldOn s e : ℝ) := by
  rcases e with ⟨_ | s', _ | _⟩ | _ | _ | _ | ⟨s', _, _⟩ | _ | _ | _ | _
  all_goals simp only [trialOn, livedOn, toldOn]
  all_goals try split_ifs
  all_goals simp [took, Provenance.weight]

/-- **A slot's market funding, read off the ledger**: its lived accruals at weight 1 and its
attested imports at `c₀`. -/
theorem took_trials (c₀ : ℝ) (s : S) (es : List (FiberEvent S A C E)) :
    took c₀ (es.filterMap (trialOn s)) =
      ((es.map (livedOn s)).sum : ℝ) + c₀ * ((es.map (toldOn s)).sum : ℝ) := by
  induction es with
  | nil => simp [took]
  | cons e es ih =>
    have hcons : (e :: es).filterMap (trialOn s) = (trialOn s e).toList ++ es.filterMap (trialOn s) := by
      cases h : trialOn s e <;> simp [h]
    rw [hcons, took_append, took_trialOn, ih]
    push_cast [List.map_cons, List.sum_cons]
    ring

end Market

/-! ### Perception and affect are one property -/

section Perception

open Erlangen

variable {T O X : Type*} [Group T] [MulAction T O]

/-- **A reading is invariant exactly when it factors through the Umwelt.** -/
theorem invariant_iff_factorsThrough (f : O → X) :
    Invariant T f ↔ Function.FactorsThrough f (Quotient.mk (MulAction.orbitRel T O)) := by
  constructor
  · intro h a b hab
    obtain ⟨t, rfl⟩ := MulAction.mem_orbit_iff.1 (MulAction.orbitRel_apply.1 (Quotient.exact hab))
    exact h t b
  · intro h t o
    exact h (Quotient.sound (MulAction.orbitRel_apply.2 (MulAction.mem_orbit o t)))

/-- Affect's register phases, in the same form: they factor through the register view. -/
theorem affect_factorsThrough {R A : Type*} :
    Function.FactorsThrough (Affect.reading (R := R) (A := A) Affect.registerKinds) Affect.view :=
  Affect.register_phases_factor

end Perception

/-! ### Fit routes by the Umwelt -/

section Routing

open Erlangen

variable {T S K B R A C E : Type*} [Group T] [MulAction T R] [DecidableEq S] [Min B]
  [GeometryAlgebra B R]

omit [GeometryAlgebra B R] in
/-- With a feasible set the agent's transforms preserve, a transformed datum is filed as the
datum is. -/
theorem fit_fiber_smul (i : S) (c : C) (e : E) (w : Web S K B R A C E)
    (hF : ∀ (t : T) (x : R), t • x ∈ (w.geom.geometry i).feasibleSet ↔
      x ∈ (w.geom.geometry i).feasibleSet) (t : T) (x : R) :
    (Operator.fit i (t • x) c e : Operator S B R A C E).fiber w =
      (Operator.fit i x c e : Operator S B R A C E).fiber w := by
  by_cases hx : x ∈ (w.geom.geometry i).feasibleSet
  · simp [Operator.fiber, hx, (hF t x).2 hx]
  · have htx : t • x ∉ (w.geom.geometry i).feasibleSet := fun h ↦ hx ((hF t x).1 h)
    simp [Operator.fiber, hx, htx]

omit [GeometryAlgebra B R] in
/-- **Fit routes by the Umwelt**: what it writes depends only on the datum's orbit. -/
theorem fit_factors_through_umwelt (i : S) (c : C) (e : E) (w : Web S K B R A C E)
    (hF : ∀ (t : T) (x : R), t • x ∈ (w.geom.geometry i).feasibleSet ↔
      x ∈ (w.geom.geometry i).feasibleSet) :
    Function.FactorsThrough (fun x : R ↦ (Operator.fit i x c e : Operator S B R A C E).fiber w)
      (Quotient.mk (MulAction.orbitRel T R)) :=
  (invariant_iff_factorsThrough _).1 fun t x ↦ fit_fiber_smul i c e w hF t x

end Routing

end SOV.Bridges
