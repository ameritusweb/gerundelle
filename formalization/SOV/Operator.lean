import SOV.Slot

/-!
# The named operators

The docs' sixteen named operators, plus Relabel, the vocabulary-mapping component of Transfer
(added 2026-10-29; see `SOV.Holonomy`).

Each named operator is a pair (base move, lift) (sov_formal_spec §2.1): a geometry move
`base : GeomWeb → GeomWeb` and a fiber move `fiber : Web → List FiberEvent` that appends to the
etymology ledger. `Operator.apply` runs both.

## The three conditions

* **C1, base-definability.** `base` is typed `GeomWeb → GeomWeb`, so it can't read the ledger
  (`apply_geom`, `base_definable`). The fiber may read geometry: Fit's boundary test and
  the identity checks of Unify, Attest and Bind gate what is appended.
* **C2, conservativity.** Every event an operator appends carries that operator's tag from the
  earning table (`fiber_tag`); this is the licence half of Law 1. Only Fit mints lived mass
  (`apply_mass_le`) and only Archaize destroys it (`apply_mass_eq`).
* **C3, functoriality.** Running `ops₁ ++ ops₂` is running `ops₁` then `ops₂` (`run_append`),
  and the log of a run is the old log plus the concatenated fibers (`run_log`). Provenance
  chains proper are Phase 3.

## Minimality

Fourteen operators append events, and their tags are pairwise distinct (`tag_injective`). So
no composite of the other operators appends an event with operator `k`'s tag
(`underivable`): no such operator is derivable from the others on the ledger. Posit and Pose
append nothing and leave the funded web unchanged (`posit_apply`, `pose_apply`); their
primitivity lives in their outputs (the imagination register and the posed message), not
on the funded web. Relabel appends nothing either; its primitivity is on the geometry sort:
no composite of meets produces it (`SOV.Holonomy.relabel_not_meets`). This is a syntactic
separation of fiber signatures. Whether, say, carving could be simulated semantically by
other moves is a stronger question this does not settle.

## Encoding decisions

* Fit routes a datum `x` to slot `i`: a hit (`x` feasible for `i`) accrues to `i`, a miss to
  the unassigned pool. Choosing the slot is the router's job, outside the algebra.
* Compose and Quote need a product and a reification that stay inside one 𝒢. Phase 1's
  `relProduct` changes type, so both are abstracted in `GeometryAlgebra`; this is the
  "enlarged 𝒢" of two_sorted_core §6.
* Constrain meets slot `i` with the geometry of a funding slot `j`, so its transitive
  accrual has receipts to cite (Phase 3), and Unify's base is mutual Constrain
  (TS-1, `unify_base_eq_mutual_constrain`). It appends a transitive accrual, following the
  formal spec's lift table (sov_formal_spec §2.1). two_sorted_core §2 says "no new
  receipts", and the formal spec's Law 1 list of accruing operators also omits Constrain,
  so the docs disagree here.
* Unify's identity check is that the meet is nonempty; both slots take the meet. Attest and
  Bind match when the message's feasible set equals the slot's.
* Licensing preconditions that need the ledger (Retract's failing receipts, Archaize's rent
  deficit) are not checked by `apply`; C1 forbids the base from reading them. Rent is not
  modelled yet.
* Operators that add a slot need a fresh id (`Fresh`) for Law 6.
* Relabel carries slot `i`'s geometry through a vocabulary map `σ` into a *new* slot `n`, the
  transferred copy in the target domain. Rewriting `i` in place would widen it, against
  Law 6. Its fiber is empty: the earning table has no row for it yet.
-/

namespace SOV

/-- The geometry primitives that need an enlarged 𝒢: Compose's product and Quote's
reification of geometry as content. -/
class GeometryAlgebra (B R : Type*) where
  product : ConnectorGeometry B R → ConnectorGeometry B R → ConnectorGeometry B R
  reify : ConnectorGeometry B R → ConnectorGeometry B R

/-- The operator names: the docs' sixteen, and Relabel. -/
inductive OpKind
  | fit | individuate | constrain | retract | compose | differentiate | unify | exclude
  | abstract | posit | pose | attest | bind | quote | archaize | anneal | relabel
  deriving DecidableEq, Repr

/-- The kind of a fiber event, as the earning table distinguishes them. -/
inductive EventTag
  | lived
  | earned (k : EarnedKind)
  | carve
  | pool
  | partition
  | lien
  | attest
  | retract
  | evict
  | anneal
  | coordinate
  deriving DecidableEq, Repr

namespace FiberEvent

variable {S A C E : Type*}

/-- The tag of a fiber event. Pooling out of the unassigned pool is Individuate's carve. -/
def tag : FiberEvent S A C E → EventTag
  | accrue _ (.lived _ _) => .lived
  | accrue _ (.earned k) => .earned k
  | pool none _ _ => .carve
  | pool (some _) _ _ => .pool
  | partition .. => .partition
  | lien .. => .lien
  | discountTransfer .. => .attest
  | retract _ => .retract
  | evict _ => .evict
  | anneal .. => .anneal
  | coordinationAccrue .. => .coordinate

theorem livedCount_eq_zero {e : FiberEvent S A C E} (h : e.tag ≠ .lived) :
    e.livedCount = 0 := by
  cases e <;> try rfl
  rename_i a
  cases a with
  | lived => exact absurd rfl h
  | earned => rfl

theorem not_isEvict {e : FiberEvent S A C E} (h : e.tag ≠ .evict) : ¬ e.IsEvict := by
  cases e <;> first | exact absurd rfl h | exact id

end FiberEvent

/-- The tag each operator's fiber appends: the earning table (sov_formal_spec §3.1). -/
def OpKind.tag : OpKind → Option EventTag
  | fit => some .lived
  | individuate => some .carve
  | constrain => some (.earned .transitive)
  | retract => some .retract
  | compose => some (.earned .structural)
  | differentiate => some .partition
  | unify => some .pool
  | exclude => some (.earned .negative)
  | abstract => some .lien
  | posit => none
  | pose => none
  | attest => some .attest
  | bind => some .coordinate
  | quote => some (.earned .secondOrder)
  | relabel => none
  | archaize => some .evict
  | anneal => some .anneal

/-- Distinct operators append distinct tags. -/
theorem OpKind.tag_injective :
    ∀ k k' : OpKind, k.tag = k'.tag → k.tag ≠ none → k = k' := by
  intro k k'
  cases k <;> cases k' <;> simp [OpKind.tag]

/-- The named operators with their arguments. -/
inductive Operator (S B R A C E : Type*)
  /-- Fit datum `x` to slot `i`, a lived event on `channel` in `episode`. -/
  | fit (i : S) (x : R) (channel : C) (episode : E)
  /-- Carve slot `n` with geometry `g` from up to `amount` unassigned records. -/
  | individuate (n : S) (g : ConnectorGeometry B R) (amount : ℕ)
  /-- Meet slot `i` with the geometry of slot `j`, the funded constraint. -/
  | constrain (i j : S)
  /-- Widen slot `i` by `restored`, as a logged compensation. -/
  | retract (i : S) (restored : Set R)
  /-- Compose slots `i` and `j` into new slot `n`. -/
  | compose (i j n : S)
  /-- Split slot `i` by `split` into `n₁` and `n₂`, sending `amount` to `n₁`. -/
  | differentiate (i n₁ n₂ : S) (split : Set R) (amount : ℕ)
  /-- Unify slot `j` into slot `i`. -/
  | unify (i j : S)
  /-- Cache that slots `i` and `j` differ. -/
  | exclude (i j : S)
  /-- Abstract slots `i` and `j` to their shared sub-pattern, new slot `n`. -/
  | abstract (i j n : S)
  /-- Clamp slot `i` to `x` in the imagination register. -/
  | posit (i : S) (x : R)
  /-- Serialize slot `i`'s geometry. -/
  | pose (i : S)
  /-- Import, onto slot `i` at `discount`, the receipts on `exporter`'s slot `j`, whose posed
  geometry is `msg`, if `msg` matches. -/
  | attest (i : S) (msg : ConnectorGeometry B R) (exporter : A) (j : S) (discount : unitInterval)
  /-- Bind slot `i` to the geometry `msg` that `partner` posed from its slot `j`, if it
  matches. -/
  | bind (i : S) (msg : ConnectorGeometry B R) (self partner : A) (j : S)
  /-- Reify slot `i`'s geometry as content of new slot `n`. -/
  | quote (i n : S)
  /-- Carry slot `i`'s geometry through the vocabulary map `σ` into new slot `n`. -/
  | relabel (i n : S) (σ : R ≃ R)
  /-- Evict slot `i`. -/
  | archaize (i : S)
  /-- Anneal slot `i`'s certainty up to time `t` (T57). -/
  | anneal (i : S) (t : ℝ)

namespace Operator

variable {S K B R A C E : Type*}

/-- The name of an operator. -/
def kind : Operator S B R A C E → OpKind
  | fit .. => .fit
  | individuate .. => .individuate
  | constrain .. => .constrain
  | retract .. => .retract
  | compose .. => .compose
  | differentiate .. => .differentiate
  | unify .. => .unify
  | exclude .. => .exclude
  | abstract .. => .abstract
  | posit .. => .posit
  | pose .. => .pose
  | attest .. => .attest
  | bind .. => .bind
  | quote .. => .quote
  | relabel .. => .relabel
  | archaize .. => .archaize
  | anneal .. => .anneal

/-- Operators that add a slot need a fresh id. -/
def Fresh [DecidableEq S] (op : Operator S B R A C E) (gw : GeomWeb S K B R) : Prop :=
  match op with
  | individuate n .. | compose _ _ n | abstract _ _ n | quote _ n | relabel _ n _ =>
    n ∉ gw.slots
  | differentiate _ n₁ n₂ .. => n₁ ∉ gw.slots ∧ n₂ ∉ gw.slots ∧ n₁ ≠ n₂
  | _ => True

variable [DecidableEq S] [Min B] [GeometryAlgebra B R]

/-- Unify's identity check: the two slots have a common feasible resolution. -/
def Unifiable (gw : GeomWeb S K B R) (i j : S) : Prop :=
  (gw.geometry i ⊓ gw.geometry j).feasibleSet.Nonempty

open Classical in
/-- The base move: the geometry component of the operator. -/
noncomputable def base (op : Operator S B R A C E) (gw : GeomWeb S K B R) : GeomWeb S K B R :=
  match op with
  | individuate n g _ => gw.addSlot n g
  | constrain i j => gw.setGeometry i (gw.geometry i ⊓ gw.geometry j)
  | retract i restored =>
    gw.setGeometry i ⟨(gw.geometry i).boundary, (gw.geometry i).feasibleSet ∪ restored⟩
  | compose i j n => gw.addSlot n (GeometryAlgebra.product (gw.geometry i) (gw.geometry j))
  | differentiate i n₁ n₂ split _ =>
    let g := gw.geometry i
    (gw.addSlot n₁ ⟨g.boundary, g.feasibleSet ∩ split⟩).addSlot n₂
      ⟨g.boundary, g.feasibleSet \ split⟩
  | unify i j =>
    let m := gw.geometry i ⊓ gw.geometry j
    if Unifiable gw i j then (gw.setGeometry i m).setGeometry j m else gw
  | exclude i j => { gw with excluded := insert s(i, j) gw.excluded }
  | abstract i j n => gw.addSlot n (gw.geometry i ⊓ gw.geometry j)
  | quote i n => gw.addSlot n (GeometryAlgebra.reify (gw.geometry i))
  | relabel i n σ => gw.addSlot n ⟨(gw.geometry i).boundary, σ '' (gw.geometry i).feasibleSet⟩
  | fit .. | posit .. | pose _ | attest .. | bind .. | archaize _ | anneal .. => gw

open Classical in
/-- The lift: the fiber events the operator appends to the ledger. -/
noncomputable def fiber (op : Operator S B R A C E) (w : Web S K B R A C E) :
    List (FiberEvent S A C E) :=
  match op with
  | fit i x c e =>
    [.accrue (if x ∈ (w.geom.geometry i).feasibleSet then some i else none) (.lived c e)]
  | individuate n _ k => [.pool none n k]
  | constrain i _ => [.accrue (some i) (.earned .transitive)]
  | retract i _ => [.retract i]
  | compose _ _ n => [.accrue (some n) (.earned .structural)]
  | differentiate i n₁ n₂ _ k => [.partition i n₁ n₂ k]
  | unify i j => if Unifiable w.geom i j then [.pool (some j) i (w.ledger.massAt (some j))] else []
  | exclude i _ => [.accrue (some i) (.earned .negative)]
  | abstract i j n => [.lien n [i, j]]
  | posit .. | pose _ | relabel .. => []
  | attest i msg x _ c =>
    if msg.feasibleSet = (w.geom.geometry i).feasibleSet then [.discountTransfer i x c] else []
  | bind i msg a b _ =>
    if msg.feasibleSet = (w.geom.geometry i).feasibleSet then [.coordinationAccrue i a b] else []
  | quote _ n => [.accrue (some n) (.earned .secondOrder)]
  | archaize i => [.evict i]
  | anneal i t => [.anneal i t]

/-- Apply an operator: its base move to the geometry, its fiber to the ledger. -/
noncomputable def apply (op : Operator S B R A C E) (w : Web S K B R A C E) :
    Web S K B R A C E :=
  ⟨op.base w.geom, w.ledger.append (op.fiber w)⟩

/-- Apply a list of operators in order. -/
noncomputable def run (ops : List (Operator S B R A C E)) (w : Web S K B R A C E) :
    Web S K B R A C E :=
  ops.foldl (fun w op ↦ op.apply w) w

/-! ### C1: base-definability -/

theorem apply_geom (op : Operator S B R A C E) (w : Web S K B R A C E) :
    (op.apply w).geom = op.base w.geom :=
  rfl

/-- The geometry an operator produces depends on the input geometry alone. -/
theorem base_definable (op : Operator S B R A C E) {w w' : Web S K B R A C E}
    (h : w.geom = w'.geom) : (op.apply w).geom = (op.apply w').geom := by
  rw [apply_geom, apply_geom, h]

/-- Law 5 (shape persistence): the pure fiber moves leave geometry unchanged. -/
theorem apply_geom_of_fiberOnly (op : Operator S B R A C E) (w : Web S K B R A C E)
    (h : op.kind = .archaize ∨ op.kind = .anneal) : (op.apply w).geom = w.geom := by
  cases op <;> simp [kind] at h <;> rfl

/-! ### C2: conservativity -/

omit [GeometryAlgebra B R] in
/-- Every event an operator appends carries that operator's tag. -/
theorem fiber_tag (op : Operator S B R A C E) (w : Web S K B R A C E) :
    ∀ e ∈ op.fiber w, some e.tag = op.kind.tag := by
  cases op <;> simp only [fiber] <;> (try split_ifs) <;>
    simp [FiberEvent.tag, kind, OpKind.tag]

omit [GeometryAlgebra B R] in
theorem kind_eq_of_mem_fiber {op : Operator S B R A C E} {w : Web S K B R A C E}
    {e : FiberEvent S A C E} (he : e ∈ op.fiber w) {k : OpKind} (hk : k.tag = some e.tag) :
    op.kind = k :=
  OpKind.tag_injective _ _ (by rw [← fiber_tag op w e he, hk])
    (by rw [← fiber_tag op w e he]; simp)

/-- Only Fit mints lived mass. -/
theorem apply_mass_le (op : Operator S B R A C E) (w : Web S K B R A C E)
    (h : op.kind ≠ .fit) (prior : S → ℝ) :
    ((op.apply w).ledger.state prior).mass.degree ≤ (w.ledger.state prior).mass.degree := by
  rw [show (op.apply w).ledger = w.ledger.append (op.fiber w) from rfl, Ledger.state_append]
  exact LedgerState.replay_mass_le _ fun e he ↦
    FiberEvent.livedCount_eq_zero fun ht ↦ h (kind_eq_of_mem_fiber he (by rw [ht]; rfl))

/-- Only Fit and Archaize change lived mass. -/
theorem apply_mass_eq (op : Operator S B R A C E) (w : Web S K B R A C E)
    (h₁ : op.kind ≠ .fit) (h₂ : op.kind ≠ .archaize) (prior : S → ℝ) :
    ((op.apply w).ledger.state prior).mass.degree = (w.ledger.state prior).mass.degree := by
  rw [show (op.apply w).ledger = w.ledger.append (op.fiber w) from rfl, Ledger.state_append]
  exact LedgerState.replay_mass_eq _ fun e he ↦
    ⟨FiberEvent.livedCount_eq_zero fun ht ↦ h₁ (kind_eq_of_mem_fiber he (by rw [ht]; rfl)),
      FiberEvent.not_isEvict fun ht ↦ h₂ (kind_eq_of_mem_fiber he (by rw [ht]; rfl))⟩

/-! ### Law 6: feasibility monotonicity -/

/-- Base moves never remove a slot. -/
theorem slots_subset_base (op : Operator S B R A C E) (gw : GeomWeb S K B R) :
    gw.slots ⊆ (op.base gw).slots := by
  cases op <;> simp only [base] <;> (try split_ifs) <;>
    simp [GeomWeb.addSlot, GeomWeb.setGeometry, Finset.subset_insert,
      (Finset.subset_insert _ _).trans (Finset.subset_insert _ _)]

/-- Base moves never add or change constraint edges. -/
theorem constraint_base (op : Operator S B R A C E) (gw : GeomWeb S K B R) :
    (op.base gw).constraint = gw.constraint := by
  cases op <;> simp only [base] <;> (try split_ifs) <;> rfl

/-- **Law 6.** Every operator but Retract narrows (or keeps) the feasible set of every
existing slot. -/
theorem base_narrows (op : Operator S B R A C E) (gw : GeomWeb S K B R)
    (hop : op.kind ≠ .retract) (hf : op.Fresh gw) {s : S} (hs : s ∈ gw.slots) :
    (op.base gw).geometry s ≤ gw.geometry s := by
  cases op
  case retract => exact absurd rfl hop
  case individuate n g k =>
    simp [base, GeomWeb.addSlot, ne_of_mem_of_not_mem hs hf]
  case compose i j n =>
    simp [base, GeomWeb.addSlot, ne_of_mem_of_not_mem hs hf]
  case abstract i j n =>
    simp [base, GeomWeb.addSlot, ne_of_mem_of_not_mem hs hf]
  case relabel i n σ =>
    simp [base, GeomWeb.addSlot, ne_of_mem_of_not_mem hs hf]
  case quote i n =>
    simp [base, GeomWeb.addSlot, ne_of_mem_of_not_mem hs hf]
  case differentiate i n₁ n₂ split k =>
    simp [base, GeomWeb.addSlot, ne_of_mem_of_not_mem hs hf.1,
      ne_of_mem_of_not_mem hs hf.2.1]
  case constrain i j =>
    simp only [base, GeomWeb.setGeometry, Function.update_apply]
    split_ifs with h
    · subst h; exact ConnectorGeometry.meet_le_left _ _
    · exact le_rfl
  case unify i j =>
    simp only [base]
    split_ifs
    · simp only [GeomWeb.setGeometry, Function.update_apply]
      split_ifs with h₁ h₂
      · subst h₁; exact ConnectorGeometry.meet_le_right _ _
      · subst h₂; exact ConnectorGeometry.meet_le_left _ _
      · exact le_rfl
    · exact le_rfl
  all_goals exact le_rfl

/-! ### C3: functoriality -/

theorem run_nil (w : Web S K B R A C E) : run [] w = w :=
  rfl

theorem run_cons (op : Operator S B R A C E) (ops : List (Operator S B R A C E))
    (w : Web S K B R A C E) : run (op :: ops) w = run ops (op.apply w) :=
  rfl

/-- Running `ops₁ ++ ops₂` is running `ops₁`, then `ops₂`. -/
theorem run_append (ops₁ ops₂ : List (Operator S B R A C E)) (w : Web S K B R A C E) :
    run (ops₁ ++ ops₂) w = run ops₂ (run ops₁ w) :=
  List.foldl_append ..

/-- A run appends to the log, and every appended event carries the tag of some operator in
the run. -/
theorem run_log (ops : List (Operator S B R A C E)) (w : Web S K B R A C E) :
    ∃ es, (run ops w).ledger.log = w.ledger.log ++ es ∧
      ∀ e ∈ es, ∃ op ∈ ops, some e.tag = op.kind.tag := by
  induction ops generalizing w with
  | nil => exact ⟨[], by simp [run_nil], by simp⟩
  | cons op ops ih =>
    obtain ⟨es, h₁, h₂⟩ := ih (op.apply w)
    refine ⟨op.fiber w ++ es, ?_, fun e he ↦ ?_⟩
    · rw [run_cons, h₁]
      simp [apply, Ledger.append]
    · rcases List.mem_append.1 he with he | he
      · exact ⟨op, List.mem_cons_self, fiber_tag op w e he⟩
      · obtain ⟨op', hop', h⟩ := h₂ e he
        exact ⟨op', List.mem_cons_of_mem _ hop', h⟩

/-! ### Minimality on the ledger -/

/-- No run of operators other than `k` appends an event with `k`'s tag. -/
theorem underivable (k : OpKind) {t : EventTag} (hk : k.tag = some t)
    (ops : List (Operator S B R A C E)) (h : ∀ op ∈ ops, op.kind ≠ k)
    (w : Web S K B R A C E) :
    ∃ es, (run ops w).ledger.log = w.ledger.log ++ es ∧ ∀ e ∈ es, e.tag ≠ t := by
  obtain ⟨es, h₁, h₂⟩ := run_log ops w
  refine ⟨es, h₁, fun e he het ↦ ?_⟩
  obtain ⟨op, hop, ht⟩ := h₂ e he
  exact h op hop (OpKind.tag_injective _ _ (by rw [← ht, het, hk]) (by rw [← ht]; simp))

omit [GeometryAlgebra B R] in
/-- Operators whose fiber is unconditional always append their tag. -/
theorem fiber_ne_nil (op : Operator S B R A C E) (w : Web S K B R A C E)
    (h : op.kind ∉ [.posit, .pose, .unify, .attest, .bind, .relabel]) : op.fiber w ≠ [] := by
  cases op <;> simp [kind, fiber] at h ⊢

/-! ### Posit and Pose -/

/-- The imagination register: geometry only, with no ledger to write to. -/
structure ImagWeb (S K B R : Type*) where
  geom : GeomWeb S K B R

/-- Posit's clamp: a copy of the web's geometry with slot `i` clamped to `x`, in the
imagination register. Propagation through constraints is Phase 3. -/
def positImage (w : Web S K B R A C E) (i : S) (x : R) : ImagWeb S K B R :=
  ⟨w.geom.setGeometry i ⟨(w.geom.geometry i).boundary, {x}⟩⟩

/-- Pose's message: the slot's geometry, with no receipts. -/
def poseMessage (w : Web S K B R A C E) (i : S) : ConnectorGeometry B R :=
  w.geom.geometry i

/-- Posit leaves the funded web unchanged. -/
theorem posit_apply (w : Web S K B R A C E) (i : S) (x : R) :
    (posit i x : Operator S B R A C E).apply w = w := by
  simp [apply, base, fiber, Ledger.append]

/-- Pose leaves the funded web unchanged. -/
theorem pose_apply (w : Web S K B R A C E) (i : S) :
    (pose i : Operator S B R A C E).apply w = w := by
  simp [apply, base, fiber, Ledger.append]

end Operator

namespace Operator

variable {S K B R A C E : Type*} [DecidableEq S] [SemilatticeInf B] [GeometryAlgebra B R]

/-- **TS-1, base half.** When the identity check passes, Unify's base move is mutual
Constrain: each slot meets the other's geometry. -/
theorem unify_base_eq_mutual_constrain (gw : GeomWeb S K B R) (i j : S)
    (h : Unifiable gw i j) :
    (unify i j : Operator S B R A C E).base gw =
      (constrain j i : Operator S B R A C E).base
        ((constrain i j : Operator S B R A C E).base gw) := by
  simp only [base, h, ↓reduceIte, GeomWeb.setGeometry, Function.update_self]
  congr 1
  by_cases hij : j = i
  · subst hij
    simp [ConnectorGeometry.meet_idem]
  · rw [Function.update_of_ne hij]
    congr 1
    -- the meet absorbs a further meet with one of its own arguments
    refine ConnectorGeometry.ext ?_ ?_
    · simp only [ConnectorGeometry.boundary_meet]
      exact (inf_eq_right.2 inf_le_right).symm
    · simp only [ConnectorGeometry.feasibleSet_meet]
      exact (Set.inter_eq_right.2 Set.inter_subset_right).symm

end Operator

end SOV
