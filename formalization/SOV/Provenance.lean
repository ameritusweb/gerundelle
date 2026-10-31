import SOV.Operator

/-!
# Provenance: well-foundedness, grounding, and Laws 3–4

Every logged event cites the entries that fund it. two_sorted_core §3 states the discipline:
every event references only strictly earlier events, grounding in Fit events, which reference
only world occurrences.

## The generic theory (`SOV.Provenance`)

* `Cites log m n`: entry `n` cites entry `m`. Citations are raw data: an entry may cite
  itself or a later entry. Self-reference is not syntactically forbidden.
* **Well-foundedness theorem** (`wellFounded_cites`): in an event-sourced log (`Sourced`:
  every citation points strictly back), citation is well-founded. Corollary 1
  (`not_transGen_self`): no entry is in its own funding chain.
* `Grounded`: an entry is grounded if it is a root (a lived Fit receipt) or cites a strictly
  earlier grounded entry. Corollary 2, paradoxes are broke, not banned
  (`not_grounded_of_selfCited`): an entry that cites only itself or later entries, and is
  not a root, is a legal entry that can never be grounded. The liar-slot is unfundable.

## The population (`SOV.Population`)

Attest and Bind cite other agents' receipts, so grounding is stated over one log shared by
all agents, ordered by global time. Each agent's ledger is its projection (`ledger`), and
applying an operator for agent `a` (`applyAt`) projects to `Operator.apply` on `a`'s web and
leaves every other agent alone (`web_applyAt_self`, `web_applyAt_other`).

* **Law 3** (`receiptsGrounded_applyAt`): if every receipt in the log is grounded and the
  operator is funded (a non-Fit operator that appends a receipt cites at least one), then
  every receipt is still grounded. The log stays event-sourced (`sourced_applyAt`).
* **Law 3 needs the funding gate** (`not_grounded_of_unfunded`): a non-Fit operator that
  appends a receipt but cites nothing, e.g. Compose of two slots with no receipts, appends an
  ungrounded receipt. The gate is a precondition on firing, as for Retract's licence.
* **Law 4** (`mem_cites_attest`): an attested receipt cites the exporter's receipts on the
  exporter's slot, so its chain runs through the exporter's ledger to a Fit receipt there.
  Bind cites both parties (`mem_cites_bind`).

## Encoding decisions

* Citations name receipts by the slot they were filed on when accrued. Pool and partition
  move lived mass, not filings, so after a Unify the merged slot's later citations reach the
  absorbed slot's receipts only through `j`'s filing.
* Bind is dual-grounded only if both parties have receipts; `Funded` asks for one citation.
-/

namespace SOV

/-- A log entry with the indices of the entries it cites. -/
structure Cited (α : Type*) where
  event : α
  sources : List ℕ

namespace Provenance

variable {α : Type*}

/-- Entry `n` of `log` cites entry `m`. -/
def Cites (log : List (Cited α)) (m n : ℕ) : Prop :=
  ∃ h : n < log.length, m ∈ log[n].sources

/-- Event-sourced: every entry cites only strictly earlier entries. -/
def Sourced (log : List (Cited α)) : Prop :=
  ∀ m n, Cites log m n → m < n

/-- **Well-foundedness theorem.** In an event-sourced log, citation is well-founded. -/
theorem wellFounded_cites {log : List (Cited α)} (h : Sourced log) :
    WellFounded (Cites log) :=
  Subrelation.wf (fun hc ↦ h _ _ hc) wellFounded_lt

theorem lt_of_transGen {log : List (Cited α)} (h : Sourced log) {m n : ℕ}
    (hmn : Relation.TransGen (Cites log) m n) : m < n := by
  induction hmn with
  | single hc => exact h _ _ hc
  | tail _ hc ih => exact ih.trans (h _ _ hc)

/-- Corollary 1: no entry appears in its own funding chain. -/
theorem not_transGen_self {log : List (Cited α)} (h : Sourced log) (n : ℕ) :
    ¬ Relation.TransGen (Cites log) n n :=
  fun hn ↦ lt_irrefl n (lt_of_transGen h hn)

/-- An entry is grounded: it is a root, or it cites a strictly earlier grounded entry. -/
inductive Grounded (IsRoot : α → Prop) (log : List (Cited α)) : ℕ → Prop
  | ofRoot {n : ℕ} (h : n < log.length) (hr : IsRoot log[n].event) : Grounded IsRoot log n
  | ofCite {m n : ℕ} (hc : Cites log m n) (hmn : m < n) (hm : Grounded IsRoot log m) :
    Grounded IsRoot log n

/-- Corollary 2 (paradoxes are broke, not banned): a non-root entry that cites only itself or
later entries is legal but can never be grounded. -/
theorem not_grounded_of_selfCited {IsRoot : α → Prop} {log : List (Cited α)} {n : ℕ}
    (hn : ∀ m, Cites log m n → n ≤ m) (hr : ∀ h : n < log.length, ¬ IsRoot log[n].event) :
    ¬ Grounded IsRoot log n := by
  intro hg
  cases hg with
  | ofRoot h hroot => exact hr h hroot
  | ofCite hc hmn _ => exact absurd (hn _ hc) (not_le.2 hmn)

theorem Cites.append {log : List (Cited α)} (es : List (Cited α)) {m n : ℕ}
    (h : Cites log m n) : Cites (log ++ es) m n := by
  obtain ⟨hn, hm⟩ := h
  exact ⟨by rw [List.length_append]; omega, by simpa [List.getElem_append_left hn] using hm⟩

/-- Appending to the log never ungrounds an entry. -/
theorem Grounded.append {IsRoot : α → Prop} {log : List (Cited α)} (es : List (Cited α))
    {n : ℕ} (h : Grounded IsRoot log n) : Grounded IsRoot (log ++ es) n := by
  induction h with
  | ofRoot h hr =>
    exact .ofRoot (by rw [List.length_append]; omega)
      (by simpa [List.getElem_append_left h] using hr)
  | ofCite hc hmn _ ih => exact .ofCite (hc.append es) hmn ih

end Provenance

open Provenance

/-- A lived Fit receipt: the root of every funding chain. -/
def IsLivedEntry {A S C E : Type*} (x : A × FiberEvent S A C E) : Prop :=
  x.2.tag = .lived

/-- A population: each agent's geometry, and one cited log of every agent's fiber events,
in global time order. -/
structure Population (A S K B R C E : Type*) where
  geom : A → GeomWeb S K B R
  log : List (Cited (A × FiberEvent S A C E))

namespace Population

variable {A S K B R C E : Type*}

/-- Entry `n` is a receipt that agent `b` filed on `s`. -/
def IsReceiptOn (p : Population A S K B R C E) (b : A) (s : Option S) (n : ℕ) : Prop :=
  ∃ h : n < p.log.length,
    p.log[n].event.1 = b ∧ (p.log[n].event.2.receipt?).map Receipt.slot = some s

open Classical in
/-- The entries that are receipts agent `b` filed on `s`. -/
noncomputable def receiptsOn (p : Population A S K B R C E) (b : A) (s : Option S) :
    List ℕ :=
  (List.range p.log.length).filter fun n ↦ decide (p.IsReceiptOn b s n)

theorem mem_receiptsOn {p : Population A S K B R C E} {b : A} {s : Option S} {n : ℕ} :
    n ∈ p.receiptsOn b s ↔ p.IsReceiptOn b s n := by
  simp only [receiptsOn, List.mem_filter, List.mem_range, decide_eq_true_eq]
  exact ⟨fun h ↦ h.2, fun h ↦ ⟨h.1, h⟩⟩

/-- The entries an operator, applied for agent `a`, cites (sov_formal_spec §3.1). -/
noncomputable def cites {B : Type*} (p : Population A S K B R C E) (a : A)
    (op : Operator S B R A C E) : List ℕ :=
  match op with
  | .fit .. | .posit .. | .pose _ | .anneal .. | .relabel .. => []
  | .individuate .. => p.receiptsOn a none
  | .constrain _ j => p.receiptsOn a (some j)
  | .retract i _ | .differentiate i .. | .quote i _ | .archaize i => p.receiptsOn a (some i)
  | .compose i j _ | .unify i j | .exclude i j | .abstract i j _ =>
    p.receiptsOn a (some i) ++ p.receiptsOn a (some j)
  | .attest _ _ x j _ => p.receiptsOn x (some j)
  | .bind i _ _ partner j => p.receiptsOn a (some i) ++ p.receiptsOn partner (some j)

/-- Every cited entry is an existing receipt. -/
theorem mem_cites {op : Operator S B R A C E} {p : Population A S K B R C E} {a : A} {m : ℕ}
    (hm : m ∈ p.cites a op) : ∃ b s, p.IsReceiptOn b s m := by
  cases op <;> simp only [cites, List.mem_append, List.not_mem_nil] at hm <;>
    first
    | exact ⟨_, _, mem_receiptsOn.1 hm⟩
    | rcases hm with hm | hm <;> exact ⟨_, _, mem_receiptsOn.1 hm⟩

theorem IsReceiptOn.lt {p : Population A S K B R C E} {b : A} {s : Option S} {n : ℕ}
    (h : p.IsReceiptOn b s n) : n < p.log.length :=
  h.1

theorem IsReceiptOn.isSome {p : Population A S K B R C E} {b : A} {s : Option S} {n : ℕ}
    (h : p.IsReceiptOn b s n) : (p.log[n]'h.lt).event.2.receipt?.isSome := by
  obtain ⟨_, _, hs⟩ := h
  simpa using congrArg Option.isSome hs

/-- **Law 4.** An attested receipt cites receipts filed by the exporter on its slot `j`. -/
theorem mem_cites_attest {p : Population A S K B R C E} {a : A} {i j : S}
    {msg : ConnectorGeometry B R} {x : A} {c : unitInterval} {m : ℕ}
    (hm : m ∈ p.cites a (Operator.attest i msg x j c : Operator S B R A C E)) :
    p.IsReceiptOn x (some j) m :=
  mem_receiptsOn.1 hm

/-- A binding cites receipts of both parties. -/
theorem mem_cites_bind {p : Population A S K B R C E} {a : A} {i j : S}
    {msg : ConnectorGeometry B R} {self partner : A} {m : ℕ}
    (hm : m ∈ p.cites a (Operator.bind i msg self partner j : Operator S B R A C E)) :
    p.IsReceiptOn a (some i) m ∨ p.IsReceiptOn partner (some j) m := by
  simpa [cites, mem_receiptsOn] using hm

/-- Every receipt in the log is grounded in a lived Fit receipt. -/
def ReceiptsGrounded (p : Population A S K B R C E) : Prop :=
  ∀ n (h : n < p.log.length), (p.log[n].event.2.receipt?).isSome →
    Grounded IsLivedEntry p.log n

theorem receiptsGrounded_nil (geom : A → GeomWeb S K B R) :
    (⟨geom, []⟩ : Population A S K B R C E).ReceiptsGrounded :=
  fun _ h ↦ absurd h (Nat.not_lt_zero _)

variable [DecidableEq A] [DecidableEq S]

/-- Agent `a`'s ledger: its events, in log order. -/
def ledger (p : Population A S K B R C E) (a : A) : Ledger S A C E :=
  ⟨p.log.filterMap fun c ↦ if c.event.1 = a then some c.event.2 else none⟩

/-- Agent `a`'s web. -/
def web (p : Population A S K B R C E) (a : A) : Web S K B R A C E :=
  ⟨p.geom a, p.ledger a⟩

variable [Min B] [GeometryAlgebra B R]

/-- Apply operator `op` for agent `a`: its base move to `a`'s geometry, its fiber appended
to the log, each event citing `p.cites a op`. -/
noncomputable def applyAt (p : Population A S K B R C E) (a : A)
    (op : Operator S B R A C E) : Population A S K B R C E where
  geom := Function.update p.geom a (op.base (p.geom a))
  log := p.log ++ (op.fiber (p.web a)).map fun e ↦ ⟨(a, e), p.cites a op⟩

/-- The population step projects to `Operator.apply` on the acting agent's web. -/
theorem web_applyAt_self (p : Population A S K B R C E) (a : A) (op : Operator S B R A C E) :
    (p.applyAt a op).web a = op.apply (p.web a) := by
  simp [applyAt, web, ledger, Operator.apply, Ledger.append, List.filterMap_append,
    List.filterMap_map]

/-- The population step leaves every other agent's web unchanged. -/
theorem web_applyAt_other (p : Population A S K B R C E) {a b : A} (hb : b ≠ a)
    (op : Operator S B R A C E) : (p.applyAt a op).web b = p.web b := by
  simp [applyAt, web, ledger, List.filterMap_append, List.filterMap_map,
    Function.update_of_ne hb, Ne.symm hb]

theorem getElem_applyAt_old (p : Population A S K B R C E) (a : A) (op : Operator S B R A C E)
    {n : ℕ} (hn : n < p.log.length) :
    (p.applyAt a op).log[n]'(by simp [applyAt]; omega) = p.log[n] := by
  simp [applyAt, List.getElem_append_left hn]

theorem getElem_applyAt_new (p : Population A S K B R C E) (a : A) (op : Operator S B R A C E)
    {n : ℕ} (hn : n < (p.applyAt a op).log.length) (hle : p.log.length ≤ n) :
    ∃ e ∈ op.fiber (p.web a), (p.applyAt a op).log[n] = ⟨(a, e), p.cites a op⟩ := by
  have h : n - p.log.length < (op.fiber (p.web a)).length := by
    simp [applyAt] at hn
    omega
  exact ⟨_, List.getElem_mem h, by simp [applyAt, List.getElem_append, not_lt.2 hle]⟩

/-- The log stays event-sourced. -/
theorem sourced_applyAt (p : Population A S K B R C E) (a : A) (op : Operator S B R A C E)
    (h : Sourced p.log) : Sourced (p.applyAt a op).log := by
  rintro m n ⟨hn, hm⟩
  by_cases hlt : n < p.log.length
  · rw [getElem_applyAt_old p a op hlt] at hm
    exact h m n ⟨hlt, hm⟩
  · obtain ⟨e, -, heq⟩ := getElem_applyAt_new p a op hn (not_lt.1 hlt)
    rw [heq] at hm
    obtain ⟨b, s, hb⟩ := mem_cites hm
    exact lt_of_lt_of_le hb.lt (not_lt.1 hlt)

/-- A non-Fit operator that appends a receipt must cite at least one entry. -/
def Funded (p : Population A S K B R C E) (a : A) (op : Operator S B R A C E) : Prop :=
  op.kind ≠ .fit → (∃ e ∈ op.fiber (p.web a), (e.receipt?).isSome) → p.cites a op ≠ []

/-- **Law 3.** A funded operator keeps every receipt grounded. -/
theorem receiptsGrounded_applyAt (p : Population A S K B R C E) (a : A)
    (op : Operator S B R A C E) (hg : p.ReceiptsGrounded) (hf : p.Funded a op) :
    (p.applyAt a op).ReceiptsGrounded := by
  intro n hn hr
  by_cases hlt : n < p.log.length
  · rw [getElem_applyAt_old p a op hlt] at hr
    exact (hg n hlt hr).append _
  · obtain ⟨e, he, heq⟩ := getElem_applyAt_new p a op hn (not_lt.1 hlt)
    by_cases hk : op.kind = .fit
    · refine .ofRoot hn ?_
      rw [heq]
      exact Option.some_injective _ ((Operator.fiber_tag op _ e he).trans (by rw [hk]; rfl))
    · rw [heq] at hr
      obtain ⟨m, hm⟩ := List.exists_mem_of_ne_nil _ (hf hk ⟨e, he, hr⟩)
      obtain ⟨b, s, hb⟩ := mem_cites hm
      exact .ofCite ⟨hn, by rw [heq]; exact hm⟩ (lt_of_lt_of_le hb.lt (not_lt.1 hlt))
        ((hg m hb.lt hb.isSome).append _)

/-- Law 3 needs the funding gate: a non-Fit operator that cites nothing appends only
ungrounded entries. -/
theorem not_grounded_of_unfunded (p : Population A S K B R C E) (a : A)
    (op : Operator S B R A C E) (hk : op.kind ≠ .fit) (hc : p.cites a op = [])
    {n : ℕ} (hn : n < (p.applyAt a op).log.length) (hle : p.log.length ≤ n) :
    ¬ Grounded IsLivedEntry (p.applyAt a op).log n := by
  obtain ⟨e, he, heq⟩ := getElem_applyAt_new p a op hn hle
  refine not_grounded_of_selfCited (fun m ⟨_, hm⟩ ↦ ?_) (fun _ hr ↦ ?_)
  · rw [heq, hc] at hm
    exact absurd hm List.not_mem_nil
  · rw [heq] at hr
    exact hk (Operator.kind_eq_of_mem_fiber he (by rw [show e.tag = .lived from hr]; rfl))

end Population

end SOV
