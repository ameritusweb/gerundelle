import Mathlib.Data.Finsupp.Weight
import Mathlib.Topology.UnitInterval
import Mathlib.Analysis.SpecialFunctions.Exp

/-!
# The ledger sort ℒ

The ledger is the etymology log: an append-only list of fiber events, one constructor per
fiber primitive (sov_operators §3: accrue, pool, partition, lien, discount-transfer, retract,
evict, anneal, coordination-accrue). Slot identifiers `S`, agents `A`, receptor channels `C`
and episode identifiers `E` are left abstract.

Two quantities are tracked, following the two documents that state conservation:

* **Lived mass μ** (two_sorted_core §3, C2): Fit-grounded funding. Replaying the log keeps
  μ per slot. The theorem `LedgerState.replay_conservation` says μ plus written-off mass
  equals the number of lived accruals: μ is created only by lived `accrue` (Fit) and
  destroyed only by `evict`. Pool, partition and Individuate's carve only move it.
* **Receipts** (sov_formal_spec §4.1, Laws 1–2): every receipt-bearing event appends one
  receipt. `Ledger.receipts_append` is Law 1's decomposition, and `Ledger.log_prefix_append`
  is Law 2. Bounding `earned` by what each geometry move licenses needs the operators
  (Phase 2).

## Encoding decisions

* The unassigned pool is lived mass at slot `none`. Fit's total miss accrues there, and
  Individuate pools from it into a new slot, so carving moves funding rather than minting it.
* An attested receipt carries its exporter and its discount `c₀ ∈ [0, 1]` as a parameter
  (TS-5 leaves the discount function open). It adds no μ to the importer. Conservation is
  stated across a population of ledgers, and the exporter keeps its own lived mass, so
  counting the import again would mint funding.
* IMAGINED content is not on the ledger (sov_formal_spec §4.2, Law 3), so there is no
  imagined receipt kind.
* Eviction appends an event that writes the slot's μ off; the receipts stay in the log.
-/

namespace SOV

/-- The non-lived accruals a geometry move can earn (sov_formal_spec §3.1). -/
inductive EarnedKind
  /-- Constrain: transitive accrual from the constraint's provenance. -/
  | transitive
  /-- Compose: structural-necessity accrual. -/
  | structural
  /-- Exclude: a negative receipt funded by the divergent receipts. -/
  | negative
  /-- Quote: meta-accrual from second-order receipt-arrival statistics. -/
  | secondOrder
  deriving DecidableEq, Repr

/-- What an `accrue` event records: a lived Fit receipt, or an earned accrual. -/
inductive Accrual (C E : Type*)
  | lived (channel : C) (episode : E)
  | earned (kind : EarnedKind)

/-- Lived mass carried by an accrual: one per lived receipt. -/
def Accrual.livedMass {C E : Type*} : Accrual C E → ℕ
  | lived _ _ => 1
  | earned _ => 0

/-- The provenance class of a receipt. -/
inductive ReceiptKind (A C E : Type*)
  | accrued (a : Accrual C E)
  /-- Imported by Attest: a reference to the exporter's receipts at discount `c₀`. -/
  | attested (exporter : A) (discount : unitInterval)
  /-- Bind's COORDINATED class, dual-grounded in both parties. -/
  | coordinated (a b : A)

/-- A receipt, filed on a slot or (`none`) in the unassigned pool. -/
structure Receipt (S A C E : Type*) where
  slot : Option S
  kind : ReceiptKind A C E

/-- The nine fiber primitives, as ledger events. -/
inductive FiberEvent (S A C E : Type*)
  /-- Fit (lived) and the earned accruals. `none` is the unassigned pool. -/
  | accrue (target : Option S) (a : Accrual C E)
  /-- Unify and Individuate: move up to `amount` lived mass from `src` into `dst`. -/
  | pool (src : Option S) (dst : S) (amount : ℕ)
  /-- Differentiate: `amount` to `dst₁`, the rest to `dst₂`. -/
  | partition (src dst₁ dst₂ : S) (amount : ℕ)
  /-- Abstract: a claim on the children's sub-patterns, not a copy. -/
  | lien (sup : S) (children : List S)
  /-- Attest: import at discount `c₀`, with dual provenance. -/
  | discountTransfer (dst : S) (exporter : A) (discount : unitInterval)
  /-- Retract and Reopen: a compensation event; history is kept. -/
  | retract (s : S)
  /-- Archaize: write the slot's lived mass off; history is kept. -/
  | evict (s : S)
  /-- Anneal: decay the slot's certainty toward the floor up to time `t` (T57). -/
  | anneal (s : S) (t : ℝ)
  /-- Bind: accrue to a jointly-owned interface object. -/
  | coordinationAccrue (iface : S) (a b : A)

namespace FiberEvent

variable {S A C E : Type*}

/-- The receipt an event appends, if any. -/
def receipt? : FiberEvent S A C E → Option (Receipt S A C E)
  | accrue t a => some ⟨t, .accrued a⟩
  | discountTransfer s x c => some ⟨some s, .attested x c⟩
  | coordinationAccrue i a b => some ⟨some i, .coordinated a b⟩
  | _ => none

/-- Lived mass an event mints: one for a lived accrual, zero otherwise. -/
def livedCount : FiberEvent S A C E → ℕ
  | accrue _ a => a.livedMass
  | _ => 0

/-- The event is an eviction. -/
def IsEvict : FiberEvent S A C E → Prop
  | evict _ => True
  | _ => False

end FiberEvent

/-! ### Replaying the log -/

section Move

variable {ι : Type*}

theorem degree_sub_single (m : ι →₀ ℕ) (i : ι) {a : ℕ} (h : a ≤ m i) :
    (m - Finsupp.single i a).degree + a = m.degree := by
  have := map_add Finsupp.degree (m - Finsupp.single i a) (Finsupp.single i a)
  rwa [tsub_add_cancel_of_le (Finsupp.single_le_iff.2 h), Finsupp.degree_single, eq_comm] at this

/-- Move up to `k` units of mass from `src` to `dst`. -/
noncomputable def move (m : ι →₀ ℕ) (src dst : ι) (k : ℕ) : ι →₀ ℕ :=
  m - Finsupp.single src (min k (m src)) + Finsupp.single dst (min k (m src))

@[simp]
theorem degree_move (m : ι →₀ ℕ) (src dst : ι) (k : ℕ) : (move m src dst k).degree = m.degree := by
  rw [move, map_add, Finsupp.degree_single, degree_sub_single _ _ (min_le_right _ _)]

end Move

/-- The state a log replays to: lived mass per slot (`none` is the unassigned pool), the
total written off by eviction, and per slot its certainty and when it was last annealed. -/
structure LedgerState (S : Type*) where
  mass : Option S →₀ ℕ
  writtenOff : ℕ
  certainty : S → ℝ
  lastAnneal : S → ℝ

/-- Anneal half-life, as in `sov.py` (`ANNEAL_HALFLIFE`). -/
def annealHalfLife : ℝ := 500

/-- Certainty floor, as in `sov.py` (`CERTAINTY_FLOOR`). -/
noncomputable def certaintyFloor : ℝ := 1 / 100

theorem certaintyFloor_nonneg : 0 ≤ certaintyFloor := by
  norm_num [certaintyFloor]

/-- Flooring between two decays changes nothing: decaying a floored value is the floor of the
decayed value. -/
theorem max_floor_mul {f x d : ℝ} (hf : 0 ≤ f) (hd₀ : 0 ≤ d) (hd₁ : d ≤ 1) :
    max f (max f x * d) = max f (x * d) := by
  rw [max_mul_of_nonneg _ _ hd₀, ← max_assoc, max_eq_left (by nlinarith : f * d ≤ f)]

namespace LedgerState

variable {S A C E : Type*} [DecidableEq S]

/-- T57 annealing (`sov.py`, `anneal`): decay slot `s`'s certainty by
`exp(-dt / annealHalfLife)`, floored at `certaintyFloor`, where `dt` runs from the last anneal
to `t`. An anneal at or before the last one does nothing. -/
noncomputable def annealAt (st : LedgerState S) (s : S) (t : ℝ) : LedgerState S :=
  if st.lastAnneal s < t then
    { st with
      certainty := Function.update st.certainty s
        (max certaintyFloor
          (st.certainty s * Real.exp (-(t - st.lastAnneal s) / annealHalfLife)))
      lastAnneal := Function.update st.lastAnneal s t }
  else st

@[simp]
theorem annealAt_mass (st : LedgerState S) (s : S) (t : ℝ) : (st.annealAt s t).mass = st.mass := by
  unfold annealAt
  split_ifs <;> rfl

@[simp]
theorem annealAt_writtenOff (st : LedgerState S) (s : S) (t : ℝ) :
    (st.annealAt s t).writtenOff = st.writtenOff := by
  unfold annealAt
  split_ifs <;> rfl

/-- **Annealing is schedule-independent.** Annealing to `t₁` and then to `t₂` is annealing once
to the later of the two. -/
theorem annealAt_annealAt (st : LedgerState S) (s : S) (t₁ t₂ : ℝ) :
    (st.annealAt s t₁).annealAt s t₂ = st.annealAt s (max t₁ t₂) := by
  rcases lt_or_ge (st.lastAnneal s) t₁ with h₁ | h₁
  · rcases lt_or_ge t₁ t₂ with h₂ | h₂
    · have h₃ : st.lastAnneal s < t₂ := h₁.trans h₂
      have hd : -(t₂ - t₁) / annealHalfLife ≤ 0 := by unfold annealHalfLife; linarith
      simp only [annealAt, h₁, h₂, h₃, ↓reduceIte, Function.update_self, max_eq_right h₂.le,
        Function.update_idem]
      rw [max_floor_mul certaintyFloor_nonneg (Real.exp_pos _).le (Real.exp_le_one_iff.2 hd),
        mul_assoc, ← Real.exp_add]
      congr 5
      ring
    · simp only [annealAt, h₁, ↓reduceIte, Function.update_self, not_lt.2 h₂,
        max_eq_left h₂]
  · have h₀ : st.annealAt s t₁ = st := by
      unfold annealAt
      simp [not_lt.2 h₁]
    rw [h₀]
    rcases le_total t₁ t₂ with h | h
    · rw [max_eq_right h]
    · rw [max_eq_left h, h₀]
      unfold annealAt
      simp [not_lt.2 (h.trans h₁)]

/-- Anneals on one slot commute. -/
theorem annealAt_comm (st : LedgerState S) (s : S) (t₁ t₂ : ℝ) :
    (st.annealAt s t₁).annealAt s t₂ = (st.annealAt s t₂).annealAt s t₁ := by
  rw [annealAt_annealAt, annealAt_annealAt, max_comm]

/-- Apply one fiber event. Events that move no lived mass and don't anneal leave the state
unchanged; their effect is the receipt they append to the log. -/
noncomputable def step (st : LedgerState S) : FiberEvent S A C E → LedgerState S
  | .accrue t a => { st with mass := st.mass + Finsupp.single t a.livedMass }
  | .pool src dst k => { st with mass := move st.mass src (some dst) k }
  | .partition s s₁ s₂ k =>
    let m := move st.mass (some s) (some s₁) k
    { st with mass := move m (some s) (some s₂) (m (some s)) }
  | .evict s =>
    { st with
      mass := st.mass - Finsupp.single (some s) (st.mass (some s))
      writtenOff := st.writtenOff + st.mass (some s) }
  | .anneal s t => st.annealAt s t
  | _ => st

/-- Replay a list of events. -/
noncomputable def replay (st : LedgerState S) (es : List (FiberEvent S A C E)) : LedgerState S :=
  es.foldl step st

/-- One step of conservation: lived plus written-off mass grows exactly by the lived mass
the event mints. -/
theorem step_conservation (st : LedgerState S) (e : FiberEvent S A C E) :
    (st.step e).mass.degree + (st.step e).writtenOff =
      st.mass.degree + st.writtenOff + e.livedCount := by
  cases e
  case evict s =>
    have := degree_sub_single st.mass (some s) le_rfl
    dsimp only [step, FiberEvent.livedCount]
    omega
  all_goals simp [step, FiberEvent.livedCount, map_add]
  omega

theorem writtenOff_le_step (st : LedgerState S) (e : FiberEvent S A C E) :
    st.writtenOff ≤ (st.step e).writtenOff := by
  cases e <;> simp only [step, annealAt_writtenOff] <;> omega

theorem step_writtenOff_of_not_evict (st : LedgerState S) {e : FiberEvent S A C E}
    (h : ¬ e.IsEvict) : (st.step e).writtenOff = st.writtenOff := by
  cases e <;> first | exact absurd trivial h | rfl | exact annealAt_writtenOff ..

/-- Attest moves no lived mass: an import is a discounted reference, not new funding. -/
theorem step_discountTransfer (st : LedgerState S) (s : S) (x : A) (c : unitInterval) :
    st.step (.discountTransfer s x c : FiberEvent S A C E) = st :=
  rfl

/-- **Conservation of lived funding.** Lived plus written-off mass equals the starting mass
plus the number of lived accruals in the log. -/
theorem replay_conservation (st : LedgerState S) (es : List (FiberEvent S A C E)) :
    (st.replay es).mass.degree + (st.replay es).writtenOff =
      st.mass.degree + st.writtenOff + (es.map FiberEvent.livedCount).sum := by
  induction es generalizing st with
  | nil => simp [replay]
  | cons e es ih =>
    change ((st.step e).replay es).mass.degree + ((st.step e).replay es).writtenOff = _
    rw [ih, step_conservation, List.map_cons, List.sum_cons]
    omega

theorem writtenOff_le_replay (st : LedgerState S) (es : List (FiberEvent S A C E)) :
    st.writtenOff ≤ (st.replay es).writtenOff := by
  induction es generalizing st with
  | nil => exact le_rfl
  | cons e es ih => exact (writtenOff_le_step st e).trans (ih (st.step e))

theorem replay_writtenOff_of_no_evict (st : LedgerState S) {es : List (FiberEvent S A C E)}
    (h : ∀ e ∈ es, ¬ e.IsEvict) : (st.replay es).writtenOff = st.writtenOff := by
  induction es generalizing st with
  | nil => rfl
  | cons e es ih =>
    change ((st.step e).replay es).writtenOff = _
    rw [ih (st.step e) fun e' he' ↦ h e' (List.mem_cons_of_mem _ he'),
      step_writtenOff_of_not_evict _ (h e List.mem_cons_self)]

omit [DecidableEq S] in
private theorem sum_livedCount_eq_zero {es : List (FiberEvent S A C E)}
    (h : ∀ e ∈ es, e.livedCount = 0) : (es.map FiberEvent.livedCount).sum = 0 :=
  List.sum_eq_zero fun x hx ↦ by
    obtain ⟨e, he, rfl⟩ := List.mem_map.1 hx
    exact h e he

/-- Lived mass can't grow without a lived accrual (Fit). -/
theorem replay_mass_le (st : LedgerState S) {es : List (FiberEvent S A C E)}
    (h : ∀ e ∈ es, e.livedCount = 0) : (st.replay es).mass.degree ≤ st.mass.degree := by
  have := replay_conservation st es
  have := writtenOff_le_replay st es
  rw [sum_livedCount_eq_zero h] at *
  omega

/-- Lived mass can't shrink without an eviction (Archaize). -/
theorem replay_mass_eq (st : LedgerState S) {es : List (FiberEvent S A C E)}
    (h : ∀ e ∈ es, e.livedCount = 0 ∧ ¬ e.IsEvict) :
    (st.replay es).mass.degree = st.mass.degree := by
  have := replay_conservation st es
  rw [sum_livedCount_eq_zero fun e he ↦ (h e he).1,
    replay_writtenOff_of_no_evict st fun e he ↦ (h e he).2] at this
  omega

end LedgerState

/-! ### The etymology ledger -/

/-- The etymology ledger: an append-only event log. -/
structure Ledger (S A C E : Type*) where
  log : List (FiberEvent S A C E)

namespace Ledger

variable {S A C E : Type*}

/-- Append events to the ledger, the only way it may change. -/
def append (ℓ : Ledger S A C E) (es : List (FiberEvent S A C E)) : Ledger S A C E :=
  ⟨ℓ.log ++ es⟩

/-- The receipts in the ledger, in log order. -/
def receipts (ℓ : Ledger S A C E) : List (Receipt S A C E) :=
  ℓ.log.filterMap FiberEvent.receipt?

/-- The receipts a batch of events appends. -/
def earned (es : List (FiberEvent S A C E)) : List (Receipt S A C E) :=
  es.filterMap FiberEvent.receipt?

/-- Law 2 (no destruction): the log only grows. -/
theorem log_prefix_append (ℓ : Ledger S A C E) (es : List (FiberEvent S A C E)) :
    ℓ.log <+: (ℓ.append es).log :=
  List.prefix_append _ _

/-- Law 1 (no creation), decomposition: the receipts after appending are the old receipts
plus exactly those the new events earn. -/
theorem receipts_append (ℓ : Ledger S A C E) (es : List (FiberEvent S A C E)) :
    (ℓ.append es).receipts = ℓ.receipts ++ earned es :=
  List.filterMap_append

theorem receipts_length_append (ℓ : Ledger S A C E) (es : List (FiberEvent S A C E)) :
    (ℓ.append es).receipts.length = ℓ.receipts.length + (earned es).length := by
  rw [receipts_append, List.length_append]

/-- The state the ledger replays to from an empty one with prior certainties. -/
noncomputable def state [DecidableEq S] (ℓ : Ledger S A C E) (prior : S → ℝ) :
    LedgerState S :=
  (⟨0, 0, prior, fun _ ↦ 0⟩ : LedgerState S).replay ℓ.log

theorem state_append [DecidableEq S] (ℓ : Ledger S A C E) (es : List (FiberEvent S A C E))
    (prior : S → ℝ) : (ℓ.append es).state prior = (ℓ.state prior).replay es := by
  simp [state, append, LedgerState.replay, List.foldl_append]

/-- The lived mass currently filed at `s` (`none` is the unassigned pool). -/
noncomputable def massAt [DecidableEq S] (ℓ : Ledger S A C E) (s : Option S) : ℕ :=
  (ℓ.state 0).mass s

/-- Conservation of lived funding for a whole ledger: lived mass plus written-off mass is
the number of lived accruals in the log. -/
theorem state_conservation [DecidableEq S] (ℓ : Ledger S A C E) (prior : S → ℝ) :
    (ℓ.state prior).mass.degree + (ℓ.state prior).writtenOff =
      (ℓ.log.map FiberEvent.livedCount).sum := by
  rw [state, LedgerState.replay_conservation]
  simp

end Ledger

end SOV
