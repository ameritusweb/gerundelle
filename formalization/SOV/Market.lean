import Mathlib.Data.Finset.Max
import Mathlib.Algebra.Order.Field.Basic
import SOV.Ledger

/-!
# Market cognition: bidding and ownership

A formalization of the market in `analogy/MARKET_COGNITION.md` (primitives 1–4), with bids
computed the way the territory register computes holding strength
(`analogy/molecules/molecules.py`, `Territory.strength`) and pulls as in `Territory.pull`.

## Bidding

An agent's evidence on a slot is a list of trials, each lived, told or imagined, and each
either taking or not. A trial counts at its provenance weight: lived 1, told `c₀`, imagined 0.
`c₀` is the Attest discount of the formal spec (TS-5): a prior from consequence-profile
overlap, refined by a posterior from per-channel reliability as attested receipts are billed.
`MARKET_COGNITION.md`'s told weight of 1/2 is `c₀`'s initial value, the prior before the
posterior has data. The theorems here hold for any `c₀ ∈ [0, 1]`, so they cover both stages;
`SOV.Discount` formalizes the two stages and shows `c₀` stays in `[0, 1]` (`discount_mem`).
An agent's bid is its weighted take rate shrunk toward a base rate `b`, the register's form:
`(took + κ b) / (tried + κ)`.

* Bids lie in `[0, 1]` (`bid_nonneg`, `bid_le_one`).
* **Funding is order-free** (`bid_perm`): a bid depends only on the multiset of trials.
* **Imagined evidence is inert** (`bid_filter_imagined`): dropping imagined trials changes no
  bid.
* **Told evidence can't be promoted** (`took_told_le`): told-only evidence funds at most `c₀`
  per trial, whatever the processing.

## Ownership

A market holds each agent's evidence per slot and at most one owner per slot (`owner : S →
Option G`, so exclusivity is by type). Three events:

* `trial g s t` records evidence;
* `close s B` runs an auction on an open slot among bidders `B`: the highest bid wins, and
  takes the slot if its funding (weighted takes) reaches the threshold `M0`;
* `contradict s` reopens the slot.

Results:

* **Auction soundness** (`owner_close`): an owner set by `close` was a bidder, outbid no one,
  and was funded past `M0`.
* **The market firewall** (`run_owner_filter_imagined`): inserting or deleting imagined
  trials anywhere in an event sequence changes no owner.
* **Ownership is order-dependent** (`ownership_order_dependent`): the same three events in
  two orders leave the slot held in one and open in the other. With `bid_perm`, this places
  the "Time" claim (the algebra is non-commutative) precisely: funding commutes, and the
  non-commutativity is in the threshold and reopen gates of ownership.
* **Ties need a rule.** `MARKET_COGNITION.md` says the strongest pull wins but gives no
  tie-break; exclusivity forces one. `winner` breaks ties by choice, so any theorem here holds
  for every tie-breaking rule.

## Pull order

The register's design order is lost > control > unclaimed (`Territory.pull`). It holds when
`curiosity ≤ 1`, with no lower bound needed (`pull_order`). The "restless" temperament
(`fiction/temperament.py`, `curiosity = 2.0`) inverts it: an unclaimed region with nothing
else moving it outpulls every control slot (`restless_inverts`). This is intended.
Temperament is a hyperparameter, and different settings are different people: a restless
agent finds unclaimed territory more compelling than contested territory. The order is the
default temperament's, and `restless_inverts` is what restless means.

## Simplifications

* The base rate `b` is a parameter; the register computes it over all regions.
* The register's holder states (mine, contested, lost, another, nobody, unknown), hysteresis and
  half-lives are not modelled. Ownership here is the market-level open/held.
* An untried slot bids `b` here; the register returns strength 0 when nothing was tried.
-/

namespace SOV.Market

/-- How a trial's evidence was acquired. -/
inductive Provenance
  | lived
  | told
  | imagined
  deriving DecidableEq, Repr

/-- Provenance weight: lived 1, told at discount `c₀`, imagined 0. -/
def Provenance.weight (c₀ : ℝ) : Provenance → ℝ
  | lived => 1
  | told => c₀
  | imagined => 0

/-- One trial of an agent's claim on a slot: how the evidence came, and whether it took. -/
structure Trial where
  prov : Provenance
  took : Bool
  deriving DecidableEq

/-- Weighted tries in a body of evidence. -/
def tried (c₀ : ℝ) (ev : List Trial) : ℝ :=
  (ev.map fun t ↦ t.prov.weight c₀).sum

/-- Weighted takes: the evidence's funding. -/
def took (c₀ : ℝ) (ev : List Trial) : ℝ :=
  (ev.map fun t ↦ if t.took then t.prov.weight c₀ else 0).sum

/-- A bid: the weighted take rate shrunk toward the base rate `b`. -/
noncomputable def bid (c₀ κ b : ℝ) (ev : List Trial) : ℝ :=
  (took c₀ ev + κ * b) / (tried c₀ ev + κ)

/-! ### Bids -/

section Bids

variable {c₀ : ℝ}

theorem weight_nonneg (h₀ : 0 ≤ c₀) (p : Provenance) : 0 ≤ p.weight c₀ := by
  cases p <;> simp [Provenance.weight, h₀]

theorem weight_le_one (h₁ : c₀ ≤ 1) (p : Provenance) : p.weight c₀ ≤ 1 := by
  cases p <;> simp [Provenance.weight, h₁]

theorem took_nonneg (h₀ : 0 ≤ c₀) (ev : List Trial) : 0 ≤ took c₀ ev := by
  induction ev with
  | nil => simp [took]
  | cons t ev ih =>
    simp only [took, List.map_cons, List.sum_cons] at ih ⊢
    have := weight_nonneg h₀ t.prov
    split_ifs <;> linarith

theorem took_le_tried (h₀ : 0 ≤ c₀) (ev : List Trial) : took c₀ ev ≤ tried c₀ ev := by
  induction ev with
  | nil => simp [took, tried]
  | cons t ev ih =>
    simp only [took, tried, List.map_cons, List.sum_cons] at ih ⊢
    have := weight_nonneg h₀ t.prov
    split_ifs <;> linarith

theorem bid_nonneg (h₀ : 0 ≤ c₀) {κ b : ℝ} (hκ : 0 < κ) (hb : 0 ≤ b) (ev : List Trial) :
    0 ≤ bid c₀ κ b ev :=
  div_nonneg (add_nonneg (took_nonneg h₀ ev) (mul_nonneg hκ.le hb))
    (add_nonneg ((took_nonneg h₀ ev).trans (took_le_tried h₀ ev)) hκ.le)

theorem bid_le_one (h₀ : 0 ≤ c₀) {κ b : ℝ} (hκ : 0 < κ) (hb : b ≤ 1) (ev : List Trial) :
    bid c₀ κ b ev ≤ 1 := by
  have ht := (took_nonneg h₀ ev).trans (took_le_tried h₀ ev)
  rw [bid, div_le_one (by linarith)]
  nlinarith [took_le_tried h₀ ev]

/-- **Funding is order-free**: a bid depends only on the multiset of trials. -/
theorem bid_perm {κ b : ℝ} {ev ev' : List Trial} (h : ev.Perm ev') :
    bid c₀ κ b ev = bid c₀ κ b ev' := by
  simp only [bid, tried, took, (h.map _).sum_eq]

theorem tried_filter_imagined (ev : List Trial) :
    tried c₀ (ev.filter fun t ↦ t.prov ≠ .imagined) = tried c₀ ev := by
  induction ev with
  | nil => rfl
  | cons t ev ih =>
    rcases t with ⟨p, x⟩
    cases p <;> simp_all [tried, Provenance.weight]

theorem took_filter_imagined (ev : List Trial) :
    took c₀ (ev.filter fun t ↦ t.prov ≠ .imagined) = took c₀ ev := by
  induction ev with
  | nil => rfl
  | cons t ev ih =>
    rcases t with ⟨p, x⟩
    cases p <;> simp_all [took, Provenance.weight]

/-- **Imagined evidence is inert**: dropping imagined trials changes no bid. -/
theorem bid_filter_imagined {κ b : ℝ} (ev : List Trial) :
    bid c₀ κ b (ev.filter fun t ↦ t.prov ≠ .imagined) = bid c₀ κ b ev := by
  rw [bid, bid, tried_filter_imagined, took_filter_imagined]

/-- **Told evidence can't be promoted**: told-only evidence funds at most `c₀` per trial. -/
theorem took_told_le (h₀ : 0 ≤ c₀) {ev : List Trial} (h : ∀ t ∈ ev, t.prov = .told) :
    took c₀ ev ≤ c₀ * ev.length := by
  induction ev with
  | nil => simp [took]
  | cons t ev ih =>
    have ih := ih fun t' h' ↦ h t' (List.mem_cons_of_mem _ h')
    have hterm : (if t.took then t.prov.weight c₀ else 0) ≤ c₀ := by
      rw [h t List.mem_cons_self]
      split_ifs <;> simp [Provenance.weight, h₀]
    calc took c₀ (t :: ev) = (if t.took then t.prov.weight c₀ else 0) + took c₀ ev := by
          simp only [took, List.map_cons, List.sum_cons]
      _ ≤ c₀ + c₀ * ev.length := add_le_add hterm ih
      _ = c₀ * (t :: ev).length := by
          rw [List.length_cons]
          push_cast
          ring

end Bids

/-! ### The market -/

/-- The market's parameters: told discount, shrinkage, base rate, and closing threshold. -/
structure Params where
  c₀ : ℝ
  κ : ℝ
  b : ℝ
  M0 : ℝ

/-- A market: each agent's evidence per slot, and at most one owner per slot. -/
structure State (G S : Type*) where
  evidence : G × S → List Trial
  owner : S → Option G

/-- Market events. -/
inductive Event (G S : Type*)
  /-- Agent `g` tried a claim on slot `s`. -/
  | trial (g : G) (s : S) (t : Trial)
  /-- Auction open slot `s` among `bidders`. -/
  | close (s : S) (bidders : Finset G)
  /-- The world contradicted slot `s`'s closure: reopen it. -/
  | contradict (s : S)

variable {G S : Type*}

open Classical in
/-- The auction's winner: a bidder whose bid no other bidder exceeds. Ties are broken by
choice; the docs give no rule. -/
noncomputable def winner (f : G → ℝ) (bidders : Finset G) : Option G :=
  if h : bidders.Nonempty then some (Classical.choose (bidders.exists_max_image f h)) else none

theorem winner_spec {f : G → ℝ} {bidders : Finset G} {g : G} (h : winner f bidders = some g) :
    g ∈ bidders ∧ ∀ g' ∈ bidders, f g' ≤ f g := by
  unfold winner at h
  split_ifs at h with hne
  · cases h
    exact Classical.choose_spec (bidders.exists_max_image f hne)

namespace State

variable [DecidableEq G] [DecidableEq S]

/-- An agent's bid on a slot. -/
noncomputable def bidOf (P : Params) (m : State G S) (s : S) (g : G) : ℝ :=
  bid P.c₀ P.κ P.b (m.evidence (g, s))

/-- An agent's funding on a slot: its weighted takes. -/
def fundOf (P : Params) (m : State G S) (s : S) (g : G) : ℝ :=
  took P.c₀ (m.evidence (g, s))

open Classical in
/-- Apply one market event. -/
noncomputable def step (P : Params) (m : State G S) : Event G S → State G S
  | .trial g s t =>
    { m with evidence := Function.update m.evidence (g, s) (m.evidence (g, s) ++ [t]) }
  | .close s B =>
    match m.owner s, winner (m.bidOf P s) B with
    | none, some g =>
      if P.M0 ≤ m.fundOf P s g then { m with owner := Function.update m.owner s (some g) } else m
    | _, _ => m
  | .contradict s => { m with owner := Function.update m.owner s none }

/-- Run a list of events. -/
noncomputable def run (P : Params) (m : State G S) (es : List (Event G S)) : State G S :=
  es.foldl (step P) m

/-- **Auction soundness.** If closing leaves `g` holding the slot, either `g` already held it,
or `g` was a bidder that no bidder outbid, funded past the threshold. -/
theorem owner_close (P : Params) (m : State G S) (s : S) (B : Finset G) {g : G}
    (h : (m.step P (.close s B)).owner s = some g) :
    m.owner s = some g ∨
      (g ∈ B ∧ (∀ g' ∈ B, m.bidOf P s g' ≤ m.bidOf P s g) ∧ P.M0 ≤ m.fundOf P s g) := by
  simp only [step] at h
  split at h
  · rename_i g' hown hw
    split_ifs at h with hM
    · simp only [Function.update_self, Option.some.injEq] at h
      subst h
      exact Or.inr ⟨(winner_spec hw).1, (winner_spec hw).2, hM⟩
    · exact Or.inl h
  · exact Or.inl h

/-! ### The market firewall -/

/-- Two markets are indistinguishable to the auction: same owners, and the same weighted
tries and takes everywhere. -/
def Equiv (P : Params) (m m' : State G S) : Prop :=
  m.owner = m'.owner ∧ ∀ x, tried P.c₀ (m.evidence x) = tried P.c₀ (m'.evidence x) ∧
    took P.c₀ (m.evidence x) = took P.c₀ (m'.evidence x)

omit [DecidableEq G] [DecidableEq S] in
theorem Equiv.bidOf {P : Params} {m m' : State G S} (h : Equiv P m m') :
    m.bidOf P = m'.bidOf P := by
  funext s g
  simp [State.bidOf, bid, (h.2 (g, s)).1, (h.2 (g, s)).2]

omit [DecidableEq G] [DecidableEq S] in
theorem Equiv.fundOf {P : Params} {m m' : State G S} (h : Equiv P m m') :
    m.fundOf P = m'.fundOf P := by
  funext s g
  simp [State.fundOf, (h.2 (g, s)).2]

theorem Equiv.step {P : Params} {m m' : State G S} (h : Equiv P m m') (e : Event G S) :
    Equiv P (m.step P e) (m'.step P e) := by
  cases e with
  | trial g s t =>
    refine ⟨h.1, fun x ↦ ?_⟩
    simp only [State.step, Function.update_apply]
    split_ifs
    · have h₁ := (h.2 (g, s)).1
      have h₂ := (h.2 (g, s)).2
      simp only [tried, took, List.map_append, List.sum_append] at h₁ h₂ ⊢
      exact ⟨by rw [h₁], by rw [h₂]⟩
    · exact h.2 x
  | close s B =>
    simp only [State.step, h.1, h.bidOf, h.fundOf]
    split
    · split_ifs
      · exact ⟨rfl, h.2⟩
      · exact h
    · exact h
  | contradict s => exact ⟨by simp only [State.step, h.1], h.2⟩

/-- Recording an imagined trial is invisible to the auction. -/
theorem equiv_step_imagined (P : Params) (m : State G S) (g : G) (s : S) (x : Bool) :
    Equiv P (m.step P (.trial g s ⟨.imagined, x⟩)) m := by
  refine ⟨rfl, fun y ↦ ?_⟩
  simp only [State.step, Function.update_apply]
  split_ifs with hy
  · subst hy
    simp [tried, took, Provenance.weight]
  · exact ⟨rfl, rfl⟩

/-- The event is an imagined trial. -/
def _root_.SOV.Market.Event.IsImagined : Event G S → Prop
  | .trial _ _ t => t.prov = .imagined
  | _ => False

open Classical in
/-- **The market firewall.** Deleting every imagined trial from an event sequence changes no
owner. -/
theorem run_owner_filter_imagined (P : Params) (m : State G S) (es : List (Event G S)) :
    (m.run P (es.filter fun e ↦ ¬ e.IsImagined)).owner = (m.run P es).owner := by
  suffices ∀ m m' : State G S, Equiv P m m' →
      Equiv P (m.run P (es.filter fun e ↦ ¬ e.IsImagined)) (m'.run P es) from
    (this m m ⟨rfl, fun _ ↦ ⟨rfl, rfl⟩⟩).1
  induction es with
  | nil => exact fun _ _ h ↦ h
  | cons e es ih =>
    intro m m' h
    by_cases he : e.IsImagined
    · rw [List.filter_cons_of_neg (by simpa using he)]
      cases e with
      | trial g s t =>
        have ht : t = ⟨.imagined, t.took⟩ := by cases t; simp_all [Event.IsImagined]
        refine ih m (m'.step P (.trial g s t)) ?_
        rw [ht]
        exact ⟨h.1.trans (equiv_step_imagined P m' g s t.took).1.symm, fun x ↦
          ⟨(h.2 x).1.trans ((equiv_step_imagined P m' g s t.took).2 x).1.symm,
            (h.2 x).2.trans ((equiv_step_imagined P m' g s t.took).2 x).2.symm⟩⟩
      | close _ _ => exact (he : False).elim
      | contradict _ => exact (he : False).elim
    · rw [List.filter_cons_of_pos (by simpa using he)]
      exact ih _ _ (h.step e)

/-! ### Ownership is order-dependent -/

/-- The empty market: no evidence, no owners. -/
def empty : State G S :=
  ⟨fun _ ↦ [], fun _ ↦ none⟩

/-- **Ownership is order-dependent.** One lived take, an auction, and a contradiction: in
one order the slot ends open, in another it ends held. Funding is order-free (`bid_perm`), so
the order-dependence is in ownership's threshold and reopen gates. -/
theorem ownership_order_dependent (P : Params) (hM : P.M0 ≤ 1) (g : G) (s : S) :
    ((empty : State G S).run P [.trial g s ⟨.lived, true⟩, .close s {g}, .contradict s]).owner s
        = none ∧
      ((empty : State G S).run P [.contradict s, .trial g s ⟨.lived, true⟩, .close s {g}]).owner s
        = some g := by
  have hw : ∀ m : State G S, winner (m.bidOf P s) {g} = some g := fun m ↦ by
    cases hm : winner (m.bidOf P s) {g} with
    | none => simp [winner] at hm
    | some g' => rw [Finset.mem_singleton.1 (winner_spec hm).1]
  refine ⟨by simp [run, step], ?_⟩
  simp only [run, List.foldl_cons, List.foldl_nil, step, Function.update_self]
  rw [hw]
  simp [fundOf, took, Provenance.weight, hM, empty]

end State

/-! ### Pull order -/

/-- Pull of an unclaimed slot (`Territory.pull`): curiosity weighted by uniqueness. -/
noncomputable def pullUnclaimed (curiosity κ other : ℝ) : ℝ :=
  curiosity * κ / (κ + other)

/-- Pull of a control slot: a claim started, more the more it was tried. -/
noncomputable def pullControl (κ tried : ℝ) : ℝ :=
  1 + tried / (tried + κ)

/-- Pull of a lost slot: the more was held, the more to lose. -/
def pullLost (held : ℝ) : ℝ :=
  1 + held

/-- **The design order lost > control > unclaimed** holds when curiosity is at most 1, for a
tried control slot and a lost slot that held at least once. -/
theorem pull_order {curiosity κ other tried held : ℝ} (hc₁ : curiosity ≤ 1) (hκ : 0 < κ)
    (ho : 0 ≤ other) (ht : 0 < tried) (hh : 1 ≤ held) :
    pullUnclaimed curiosity κ other < pullControl κ tried ∧
      pullControl κ tried < pullLost held := by
  have hfrac : 0 < tried / (tried + κ) := div_pos ht (by linarith)
  have hfrac' : tried / (tried + κ) < 1 := (div_lt_one (by linarith)).2 (by linarith)
  refine ⟨?_, by unfold pullControl pullLost; linarith⟩
  have : curiosity * κ / (κ + other) ≤ 1 := by
    rw [div_le_one (by linarith)]
    nlinarith
  unfold pullUnclaimed pullControl
  linarith

/-- **The restless temperament inverts it.** With curiosity 2 and nothing else moving the
region, an unclaimed slot outpulls every control slot. -/
theorem restless_inverts {κ tried : ℝ} (hκ : 0 < κ) (ht : 0 ≤ tried) :
    pullControl κ tried < pullUnclaimed 2 κ 0 := by
  have : tried / (tried + κ) < 1 := (div_lt_one (by linarith)).2 (by linarith)
  unfold pullControl pullUnclaimed
  rw [add_zero, mul_div_assoc, div_self hκ.ne']
  linarith

end SOV.Market
