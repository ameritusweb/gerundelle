import SOV.Operator

/-!
# Phase 4: the P66 confluence conjecture

sov_operators §3a conjectures that propagation on the monotone fragment
`{Fit, Constrain, Exclude, Abstract, Archaize, Anneal, Pose, Attest}` reaches the same fixed
point under any update order. It notes what the argument still owes: one common order on
which each operator is shown monotone.

## What holds

* **Chaotic iteration without a complete lattice** (`runAct_confluent`). On any partial order,
  if every action is monotone and deflationary, two schedules over the same family that both
  end at a common fixed point end at the *same* point. Each endpoint lies below every point
  of the other's path. No finite height or completeness is needed, only antisymmetry.
* **Constrain and Exclude are confluent** (`p66_constrain_exclude`). The order is the
  propagation order on `GeomWeb`: same slots and constraints, more exclusions, and
  pointwise narrower geometry in both boundary and feasible set. Subsumption alone
  (Phase 1, a preorder) isn't antisymmetric, so the boundary has to be in the order. Fair
  schedules firing the same operators reach the same geometry and the same *set* of
  ledger events.

## What fails in the docs' monotone fragment

* **The log as a list or multiset is schedule-dependent** (`constrain_twice`). Constrain is
  idempotent on geometry but appends a receipt each time it fires, so two quiescent
  schedules can append different numbers of receipts. Confluence of the fiber needs a
  quotient that collapses repeats, e.g. events as a set. This bears on the open
  "compensation semantics" question (two_sorted_core §8).
* **Fit and Constrain don't commute** (`fit_constrain_not_perm`). Fit routes a datum by the
  current feasible set, which Constrain narrows. The same datum is filed on the slot in one
  order and in the unassigned pool in the other: same geometry, different ledgers, not
  related by any permutation. Attest's match test reads geometry the same way.
* **Fit and Archaize don't commute** (`fit_archaize_order`). Evicting after a hit writes the
  receipt's mass off; evicting before leaves it active.
* Anneal is *not* a counterexample. With `sov.py`'s timestamped decay, two anneals on a slot
  commute (`anneal_comm`): the docs' 2026-08-10 schedule-independence fix, proved.
* Abstract adds a slot, so it changes the carrier the order lives on; it isn't treated here.

So in this encoding, P66's falsification clause fires for the docs' monotone set as a whole:
order-dependence appears wherever a fiber reads geometry that another operator narrows, or
where an eviction writes off mass a later Fit would have kept. The confluent core is the
geometry-narrowing pair Constrain/Exclude, with the ledger read up to a set of events, and
Anneal commutes with itself.
-/

namespace SOV

/-! ### Chaotic iteration on a partial order -/

section Chaotic

variable {α ι : Type*} [PartialOrder α]

/-- Run a schedule of actions. -/
def runAct (act : ι → α → α) (σ : List ι) (x : α) : α :=
  σ.foldl (fun x i ↦ act i x) x

variable {act : ι → α → α} {I : Set ι}

theorem runAct_le (hdefl : ∀ i ∈ I, ∀ x, act i x ≤ x) {σ : List ι} (hσ : ∀ i ∈ σ, i ∈ I)
    (x : α) : runAct act σ x ≤ x := by
  induction σ generalizing x with
  | nil => exact le_rfl
  | cons i σ ih =>
    exact (ih (fun j hj ↦ hσ j (List.mem_cons_of_mem _ hj)) (act i x)).trans
      (hdefl i (hσ i List.mem_cons_self) x)

/-- A common fixed point below the start stays below every point of any schedule. -/
theorem le_runAct (hmono : ∀ i ∈ I, Monotone (act i)) {p : α} (hp : ∀ i ∈ I, act i p = p)
    {σ : List ι} (hσ : ∀ i ∈ σ, i ∈ I) {x : α} (hx : p ≤ x) : p ≤ runAct act σ x := by
  induction σ generalizing x with
  | nil => exact hx
  | cons i σ ih =>
    refine ih (fun j hj ↦ hσ j (List.mem_cons_of_mem _ hj)) ?_
    have := hmono i (hσ i List.mem_cons_self) hx
    rwa [hp i (hσ i List.mem_cons_self)] at this

/-- **Confluence of chaotic iteration.** Two schedules of monotone, deflationary actions that
both end at a common fixed point of the family end at the same point. -/
theorem runAct_confluent (hmono : ∀ i ∈ I, Monotone (act i))
    (hdefl : ∀ i ∈ I, ∀ x, act i x ≤ x) (x₀ : α) {σ τ : List ι}
    (hσ : ∀ i ∈ σ, i ∈ I) (hτ : ∀ i ∈ τ, i ∈ I)
    (hqσ : ∀ i ∈ I, act i (runAct act σ x₀) = runAct act σ x₀)
    (hqτ : ∀ i ∈ I, act i (runAct act τ x₀) = runAct act τ x₀) :
    runAct act σ x₀ = runAct act τ x₀ :=
  le_antisymm (le_runAct hmono hqσ hτ (runAct_le hdefl hσ x₀))
    (le_runAct hmono hqτ hσ (runAct_le hdefl hτ x₀))

end Chaotic

/-! ### The propagation order on the geometry sort -/

namespace GeomWeb

variable {S K B R : Type*} [SemilatticeInf B]

/-- `w` is narrower than `w'`: same slots and constraints, at least the same exclusions, and
every slot's boundary and feasible set below `w'`'s. -/
structure Narrower (w w' : GeomWeb S K B R) : Prop where
  slots_eq : w.slots = w'.slots
  constraint_eq : w.constraint = w'.constraint
  excluded_supset : w'.excluded ⊆ w.excluded
  geometry_le : ∀ s, (w.geometry s).boundary ≤ (w'.geometry s).boundary ∧
    (w.geometry s).feasibleSet ⊆ (w'.geometry s).feasibleSet

instance : PartialOrder (GeomWeb S K B R) where
  le := Narrower
  le_refl _ := ⟨rfl, rfl, subset_rfl, fun _ ↦ ⟨le_rfl, subset_rfl⟩⟩
  le_trans _ _ _ h h' := ⟨h.1.trans h'.1, h.2.trans h'.2, h'.3.trans h.3,
    fun s ↦ ⟨(h.4 s).1.trans (h'.4 s).1, (h.4 s).2.trans (h'.4 s).2⟩⟩
  le_antisymm _ _ h h' := GeomWeb.ext h.1
    (funext fun s ↦ ConnectorGeometry.ext (le_antisymm (h.4 s).1 (h'.4 s).1)
      ((h.4 s).2.antisymm (h'.4 s).2))
    h.2 (h'.3.antisymm h.3)

theorem le_iff {w w' : GeomWeb S K B R} : w ≤ w' ↔ Narrower w w' :=
  Iff.rfl

end GeomWeb

namespace Operator

variable {S K B R A C E : Type*} [DecidableEq S] [SemilatticeInf B] [GeometryAlgebra B R]

/-- The confluent core: Constrain and Exclude. -/
def InFragment (op : Operator S B R A C E) : Prop :=
  op.kind = .constrain ∨ op.kind = .exclude

theorem monotone_base (op : Operator S B R A C E) (h : op.InFragment) :
    Monotone (op.base (K := K)) := by
  intro w w' hw
  rw [GeomWeb.le_iff] at hw ⊢
  obtain ⟨hs, hc, he, hg⟩ := hw
  cases op <;> simp [InFragment, kind] at h
  case constrain i j =>
    refine ⟨hs, hc, he, fun s ↦ ?_⟩
    simp only [base, GeomWeb.setGeometry, Function.update_apply]
    split_ifs
    · simp only [ConnectorGeometry.boundary_meet, ConnectorGeometry.feasibleSet_meet]
      exact ⟨inf_le_inf (hg i).1 (hg j).1, Set.inter_subset_inter (hg i).2 (hg j).2⟩
    · exact hg s
  case exclude i j => exact ⟨hs, hc, Set.insert_subset_insert he, hg⟩

theorem base_le (op : Operator S B R A C E) (h : op.InFragment) (w : GeomWeb S K B R) :
    op.base w ≤ w := by
  rw [GeomWeb.le_iff]
  cases op <;> simp [InFragment, kind] at h
  case constrain i j =>
    refine ⟨rfl, rfl, subset_rfl, fun s ↦ ?_⟩
    simp only [base, GeomWeb.setGeometry, Function.update_apply]
    split_ifs with hs
    · subst hs
      simp only [ConnectorGeometry.boundary_meet, ConnectorGeometry.feasibleSet_meet]
      exact ⟨inf_le_left, Set.inter_subset_left⟩
    · exact ⟨le_rfl, subset_rfl⟩
  case exclude i j => exact ⟨rfl, rfl, Set.subset_insert _ _, fun _ ↦ ⟨le_rfl, subset_rfl⟩⟩

/-- The fiber of a fragment operator, which doesn't depend on the web. -/
def fragFiber : Operator S B R A C E → List (FiberEvent S A C E)
  | constrain i _ => [.accrue (some i) (.earned .transitive)]
  | exclude i _ => [.accrue (some i) (.earned .negative)]
  | _ => []

omit [DecidableEq S] [SemilatticeInf B] [GeometryAlgebra B R] in
theorem fiber_eq_fragFiber [DecidableEq S] [Min B] (op : Operator S B R A C E)
    (h : op.InFragment) (w : Web S K B R A C E) : op.fiber w = op.fragFiber := by
  cases op <;> simp [InFragment, kind] at h <;> rfl

theorem run_geom (ops : List (Operator S B R A C E)) (w : Web S K B R A C E) :
    (run ops w).geom = runAct (fun op ↦ op.base) ops w.geom := by
  induction ops generalizing w with
  | nil => rfl
  | cons op ops ih => exact ih (op.apply w)

theorem run_log_fragment {ops : List (Operator S B R A C E)} (h : ∀ op ∈ ops, op.InFragment)
    (w : Web S K B R A C E) :
    (run ops w).ledger.log = w.ledger.log ++ ops.flatMap fragFiber := by
  induction ops generalizing w with
  | nil => simp [run_nil]
  | cons op ops ih =>
    rw [run_cons, ih (fun op' h' ↦ h op' (List.mem_cons_of_mem _ h'))]
    simp [apply, Ledger.append, fiber_eq_fragFiber op (h op List.mem_cons_self)]

/-- **P66 on the confluent core.** Two schedules of Constrain and Exclude operators that fire
the same operators and both reach quiescence on the family reach the same geometry and the
same set of ledger events. -/
theorem p66_constrain_exclude (I : Set (Operator S B R A C E)) (hI : ∀ op ∈ I, op.InFragment)
    (w : Web S K B R A C E) {σ τ : List (Operator S B R A C E)}
    (hσ : ∀ op ∈ σ, op ∈ I) (hτ : ∀ op ∈ τ, op ∈ I) (hst : ∀ op, op ∈ σ ↔ op ∈ τ)
    (hqσ : ∀ op ∈ I, op.base (run σ w).geom = (run σ w).geom)
    (hqτ : ∀ op ∈ I, op.base (run τ w).geom = (run τ w).geom) :
    (run σ w).geom = (run τ w).geom ∧
      {e | e ∈ (run σ w).ledger.log} = {e | e ∈ (run τ w).ledger.log} := by
  refine ⟨?_, ?_⟩
  · rw [run_geom] at hqσ hqτ ⊢
    rw [run_geom]
    exact runAct_confluent (fun op h ↦ monotone_base op (hI op h))
      (fun op h ↦ base_le op (hI op h)) w.geom hσ hτ hqσ hqτ
  · ext e
    simp [run_log_fragment (fun op h ↦ hI op (hσ op h)),
      run_log_fragment (fun op h ↦ hI op (hτ op h)), List.mem_flatMap, hst]

/-! ### Order-dependence in the docs' monotone fragment -/

/-- Constrain is idempotent on geometry. -/
theorem base_constrain_idem (i j : S) (gw : GeomWeb S K B R) :
    (constrain i j : Operator S B R A C E).base
        ((constrain i j : Operator S B R A C E).base gw) =
      (constrain i j : Operator S B R A C E).base gw := by
  simp only [base, GeomWeb.setGeometry, Function.update_self, Function.update_idem]
  congr 2
  by_cases h : j = i
  · subst h
    simp [ConnectorGeometry.meet_idem]
  · rw [Function.update_of_ne h, ConnectorGeometry.meet_assoc, ConnectorGeometry.meet_idem]

/-- **The log is schedule-dependent.** Firing Constrain twice reaches the same geometry as
firing it once, and both are quiescent, but appends one more receipt. -/
theorem constrain_twice (i j : S) (w : Web S K B R A C E) :
    (run [constrain i j, constrain i j] w).geom = (run [constrain i j] w).geom ∧
      (run [constrain i j, constrain i j] w).ledger.log.length =
        (run [constrain i j] w).ledger.log.length + 1 := by
  refine ⟨base_constrain_idem (A := A) (C := C) (E := E) i j w.geom, ?_⟩
  simp [run_cons, run_nil, apply, fiber, Ledger.append]

/-- **Fit and Constrain don't commute.** If datum `x` is feasible for slot `i` but not for
slot `j`, then Fit-then-Constrain files it on `i` and Constrain-then-Fit files it in the
unassigned pool. The geometries agree; the logs are not permutations of each other. -/
theorem fit_constrain_not_perm (w : Web S K B R A C E) (i j : S) (x : R) (c : C) (e : E)
    (hx : x ∈ (w.geom.geometry i).feasibleSet) (hxj : x ∉ (w.geom.geometry j).feasibleSet) :
    (run [fit i x c e, constrain i j] w).geom = (run [constrain i j, fit i x c e] w).geom ∧
      ¬ (run [fit i x c e, constrain i j] w).ledger.log.Perm
        (run [constrain i j, fit i x c e] w).ledger.log := by
  refine ⟨rfl, fun hp ↦ ?_⟩
  simp only [run_cons, run_nil, apply, fiber, base, Ledger.append, GeomWeb.setGeometry,
    Function.update_self, ConnectorGeometry.feasibleSet_meet, Set.mem_inter_iff, hx, hxj,
    and_false, ↓reduceIte, List.append_assoc, List.singleton_append,
    List.perm_append_left_iff] at hp
  have := hp.mem_iff.1 List.mem_cons_self
  simp at this

/-- **Fit and Archaize don't commute.** After a hit on slot `i`, evicting writes the receipt
off; evicting first leaves the new receipt active. -/
theorem fit_archaize_order (w : Web S K B R A C E) (i : S) (x : R) (c : C) (e : E)
    (hx : x ∈ (w.geom.geometry i).feasibleSet) :
    (run [fit i x c e, archaize i] w).ledger.massAt (some i) = 0 ∧
      (run [archaize i, fit i x c e] w).ledger.massAt (some i) = 1 := by
  simp [run_cons, run_nil, apply, fiber, base, hx, Ledger.massAt, Ledger.state_append,
    LedgerState.replay, LedgerState.step, Accrual.livedMass]

/-- **Anneal commutes with itself.** Two anneals on one slot reach the same ledger state in
either order: the docs' 2026-08-10 schedule-independence fix. -/
theorem anneal_comm (w : Web S K B R A C E) (i : S) (t₁ t₂ : ℝ) (prior : S → ℝ) :
    (run [anneal i t₁, anneal i t₂] w).ledger.state prior =
      (run [anneal i t₂, anneal i t₁] w).ledger.state prior := by
  simp only [run_cons, run_nil, apply, fiber, Ledger.state_append, LedgerState.replay,
    List.foldl_cons, List.foldl_nil, LedgerState.step]
  exact LedgerState.annealAt_comm _ i t₁ t₂

end Operator

end SOV
