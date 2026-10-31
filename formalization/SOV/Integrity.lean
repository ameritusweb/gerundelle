import SOV.Ledger

/-!
# Integrity under attack: signed logs

The cryptographic direction for the SOV algebra is integrity, not confidentiality
(`SOV.Crypto`; docs/sov/sov_cryptography_conjecture.md). This file adds an adversary and an
abstract signature interface to the log.

## The model

Signatures are symbolic (Dolev–Yao), the standard idealization of an unforgeable signature
scheme (EUF-CMA). A set of agents is corrupted; the adversary signs anything as them. For an
honest agent, a signature verifies only on what that agent actually signed. Quantum safety
is then a property of the primitive that realizes this interface: SLH-DSA (FIPS 205) or
ML-DSA (FIPS 204). The adversary controls the log: it may write any entries, under any
claimed author, as long as they verify.

An agent's *view* is the verified entries in the log that claim it as author. Its lived mass
is the weight of those entries.

## Results

* **Signing the event alone is not enough** (`replay_inflates`). If a signature covers only
  the payload, the adversary replays an honest agent's signed Fit receipt and doubles the
  lived mass that agent's view holds. Conservation of lived funding fails under attack.
* **Binding the signature to the log position fixes it.** With signatures over (position,
  payload):
  - **authenticity** (`authentic`): every entry the view attributes to an honest agent at
    position `n` is exactly what that agent signed for `n`;
  - **no inflation** (`view_weight_le`, `honest_livedMass_le`): an honest agent's viewed
    lived mass is at most what it signed. The adversary can't forge, replay or substitute.
* **What remains is suppression.** A truncated log still verifies (`accepted_take`), so the
  adversary can withhold an honest agent's later entries. Deleting an entry from the middle
  shifts every later position and breaks their signatures, so suppression is limited to
  truncation. Signed log heads, as in certificate-transparency logs, are the standard fix;
  they are not formalized here.

Attested imports from a corrupted exporter can't inflate an honest importer's lived mass
either: Attest mints no lived mass at all (`LedgerState.step_discountTransfer`).
-/

namespace SOV.Integrity

variable {A P : Type*}

/-! ### Signatures over payloads alone -/

/-- Keys when signatures cover the payload only: the corrupted agents, and what each honest
agent signed. -/
structure PayloadKeys (A P : Type*) where
  bad : Set A
  signed : A → Set P

/-- A log entry (claimed author, payload) verifies. -/
def PayloadKeys.Verifies (ks : PayloadKeys A P) (x : A × P) : Prop :=
  x.1 ∈ ks.bad ∨ x.2 ∈ ks.signed x.1

/-- The payloads in a log attributed to agent `a`. -/
def payloadView [DecidableEq A] (a : A) (L : List (A × P)) : List P :=
  (L.filter fun x ↦ x.1 = a).map Prod.snd

/-- **Signing the event alone is not enough**: replaying an honest agent's signed payload
verifies, and the agent's view holds it twice. -/
theorem replay_inflates [DecidableEq A] (ks : PayloadKeys A P) (a : A) (p : P)
    (hp : p ∈ ks.signed a) (w : P → ℕ) :
    (∀ x ∈ [(a, p), (a, p)], ks.Verifies x) ∧
      ((payloadView a [(a, p), (a, p)]).map w).sum = 2 * w p := by
  refine ⟨fun x hx ↦ ?_, ?_⟩
  · simp only [List.mem_cons, List.not_mem_nil, or_false, or_self] at hx
    exact hx ▸ Or.inr hp
  · simp [payloadView]
    ring

/-! ### Signatures bound to the log position -/

/-- Keys when signatures cover (position, payload): the corrupted agents, and what each honest
agent signed for each position (at most one payload per position). -/
structure Keys (A P : Type*) where
  bad : Set A
  record : A → ℕ → Option P

/-- The entry at position `n` verifies. -/
def Keys.Verifies (ks : Keys A P) (n : ℕ) (x : A × P) : Prop :=
  x.1 ∈ ks.bad ∨ ks.record x.1 n = some x.2

/-- Every entry of a log starting at position `n` verifies at its position. -/
def Accepted (ks : Keys A P) : ℕ → List (A × P) → Prop
  | _, [] => True
  | n, x :: L => ks.Verifies n x ∧ Accepted ks (n + 1) L

/-- The (position, payload) pairs a log starting at position `n` attributes to agent `a`. -/
def view [DecidableEq A] (a : A) : ℕ → List (A × P) → List (ℕ × P)
  | _, [] => []
  | n, x :: L => (if x.1 = a then [(n, x.2)] else []) ++ view a (n + 1) L

/-- **Authenticity**: what the view attributes to an honest agent at position `n` is exactly
what it signed for `n`. -/
theorem authentic [DecidableEq A] (ks : Keys A P) {a : A} (ha : a ∉ ks.bad) :
    ∀ {n : ℕ} {L : List (A × P)}, Accepted ks n L → ∀ {k : ℕ} {p : P}, (k, p) ∈ view a n L →
      ks.record a k = some p := by
  intro n L
  induction L generalizing n with
  | nil => simp [view]
  | cons x L ih =>
    rintro ⟨hx, hL⟩ k p hk
    simp only [view, List.mem_append] at hk
    rcases hk with hk | hk
    · split_ifs at hk with hxa
      · simp only [List.mem_singleton, Prod.mk.injEq] at hk
        obtain ⟨rfl, rfl⟩ := hk
        rcases hx with hbad | hrec
        · exact absurd (hxa ▸ hbad) ha
        · exact hxa ▸ hrec
      · simp at hk
    · exact ih hL hk

/-- **No inflation**: an honest agent's viewed weight is at most the weight of what it signed
for the positions the log covers. -/
theorem view_weight_le [DecidableEq A] (ks : Keys A P) {a : A} (ha : a ∉ ks.bad) (w : P → ℕ) :
    ∀ {n : ℕ} {L : List (A × P)}, Accepted ks n L →
      ((view a n L).map (fun q ↦ w q.2)).sum ≤
        ((List.range' n L.length).map fun k ↦ (ks.record a k).elim 0 w).sum := by
  intro n L
  induction L generalizing n with
  | nil => simp [view]
  | cons x L ih =>
    rintro ⟨hx, hL⟩
    have ih := ih hL
    rw [List.length_cons, List.range'_succ, List.map_cons, List.sum_cons]
    simp only [view, List.map_append, List.sum_append]
    split_ifs with hxa
    · have hrec : ks.record a n = some x.2 := by
        rcases hx with hbad | hrec
        · exact absurd (hxa ▸ hbad) ha
        · exact hxa ▸ hrec
      have hw : (ks.record a n).elim 0 w = w x.2 := by rw [hrec]; rfl
      rw [hw]
      simp only [List.map_cons, List.map_nil, List.sum_cons, List.sum_nil, add_zero]
      omega
    · simp only [List.map_nil, List.sum_nil, zero_add]
      omega

/-- **Suppression by truncation**: any prefix of an accepted log is accepted. -/
theorem accepted_take (ks : Keys A P) :
    ∀ {n : ℕ} {L : List (A × P)}, Accepted ks n L → ∀ k, Accepted ks n (L.take k) := by
  intro n L
  induction L generalizing n with
  | nil => simp [Accepted]
  | cons x L ih =>
    rintro ⟨hx, hL⟩ k
    cases k with
    | zero => trivial
    | succ k => exact ⟨hx, ih hL k⟩

/-- **Honest lived mass can't be inflated.** With position-bound signatures, an honest agent's
viewed lived mass is at most the lived mass it signed. -/
theorem honest_livedMass_le {S C E : Type*} [DecidableEq A]
    (ks : Keys A (FiberEvent S A C E)) {a : A} (ha : a ∉ ks.bad) {L : List (A × FiberEvent S A C E)}
    (hL : Accepted ks 0 L) :
    ((view a 0 L).map (fun q ↦ q.2.livedCount)).sum ≤
      ((List.range' 0 L.length).map fun k ↦ (ks.record a k).elim 0 FiberEvent.livedCount).sum :=
  view_weight_le ks ha _ hL

end SOV.Integrity
