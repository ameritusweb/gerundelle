import Mathlib.Data.List.Perm.Basic
import Mathlib.Order.Basic

/-!
# Competition: the tournament

A formalization of `Mind.think` and `Mind.resolve` (`analogy/molecules/molecules.py`; the
tournament of THOUGHT_MOLECULES.md). Each level, every molecule resolves its binding among its
competitors, bids, and the bidders are ordered; the first `k` win the level's slots, and only
winners compete at the next level.

The order (`order` in `think`) sorts by a total key: bid, then surprise, then time waited, then
id. It is taken here as any reordering that permutes its input and leaves it sorted by a key,
so the results hold for that order.

## Results

* **Winners outbid losers** (`winner_outbids`): a bidder that did not win a slot has a key no
  higher than any winner's. Scarcity: at most `k` win (`winners_length_le`).
* **Levels nest** (`tower_nested`): a molecule reaches level `L + 1` only by winning level `L`.
* **Aboutness is one-way** (`partner_not_meta`, `meta_partner_is_subject`,
  `bid_ignores_meta`): a thought never binds to a thought about thinking, and a meta molecule
  binds only to its subject. A thought's bid is computed from its admissible partners and the
  support of constraint molecules, so adding meta molecules, which are not constraints, never
  changes it: a meta molecule cannot lift its subject's bid.
-/

namespace SOV.Competition

open scoped List

variable {I K : Type*} [LinearOrder K]

/-- `order`: a permutation of the bidders, sorted by `key`, highest first. -/
structure Order (key : I → K) where
  run : List I → List I
  perm : ∀ l, run l ~ l
  sorted : ∀ l, (run l).Pairwise fun a b ↦ key b ≤ key a

variable {key : I → K} (o : Order key)

/-- A level's winners: the first `k` bidders in order. -/
def winners (k : ℕ) (bidders : List I) : List I :=
  (o.run bidders).take k

theorem winners_length_le (k : ℕ) (bidders : List I) : (winners o k bidders).length ≤ k :=
  List.length_take_le _ _

theorem winners_subset (k : ℕ) (bidders : List I) : winners o k bidders ⊆ bidders :=
  fun _ hx ↦ (o.perm bidders).subset (List.mem_of_mem_take hx)

/-- **Winners outbid losers.** -/
theorem winner_outbids {k : ℕ} {bidders : List I} {x y : I} (hx : x ∈ winners o k bidders)
    (hy : y ∈ bidders) (hny : y ∉ winners o k bidders) : key y ≤ key x := by
  have hs := o.sorted bidders
  rw [← List.take_append_drop k (o.run bidders), List.pairwise_append] at hs
  have hyd : y ∈ (o.run bidders).drop k := by
    have := (o.perm bidders).symm.subset hy
    rw [← List.take_append_drop k (o.run bidders)] at this
    exact (List.mem_append.1 this).resolve_left hny
  exact hs.2.2 x hx y hyd

/-- The levels: each level's winners are the next level's competitors. -/
def tower : List ℕ → List I → List (List I)
  | [], _ => []
  | k :: ks, comps => winners o k comps :: tower ks (winners o k comps)

/-- **Levels nest**: each level's winners are among the level before's. -/
theorem tower_nested (ks : List ℕ) (comps : List I) :
    (tower o ks comps).IsChain fun a b ↦ b ⊆ a := by
  induction ks generalizing comps with
  | nil => exact List.IsChain.nil
  | cons k ks ih =>
    cases ks with
    | nil => exact List.IsChain.singleton _
    | cons k' ks =>
      simp only [tower] at ih ⊢
      exact List.IsChain.cons_cons (winners_subset o _ _) (ih _)

/-! ### Aboutness is one-way -/

variable [DecidableEq I]

/-- `resolve`'s candidate filter for meta molecules: a thought skips a meta candidate, and a meta
molecule binds only to its subject. -/
def Admissible (isMeta : I → Bool) (about : I → Option I) (m p : I) : Bool :=
  !(isMeta p && !isMeta m) && (!isMeta m || about m == some p)

variable {isMeta : I → Bool} {about : I → Option I}

/-- A thought never binds to a thought about thinking. -/
theorem partner_not_meta {m p : I} (h : Admissible isMeta about m p) (hm : isMeta m = false) :
    isMeta p = false := by
  simp_all [Admissible]

/-- A meta molecule binds only to its subject. -/
theorem meta_partner_is_subject {m p : I} (h : Admissible isMeta about m p)
    (hm : isMeta m = true) : about m = some p := by
  simp_all [Admissible]

/-- A thought's admissible partners ignore any meta molecules among the competitors. -/
theorem admissible_filter_meta {m : I} (hm : isMeta m = false) (cs ms : List I)
    (hms : ∀ x ∈ ms, isMeta x = true) :
    (cs ++ ms).filter (Admissible isMeta about m) = cs.filter (Admissible isMeta about m) := by
  have h0 : ms.filter (Admissible isMeta about m) = [] :=
    List.filter_eq_nil_iff.2 fun x hx ↦ by simp [Admissible, hm, hms x hx]
  rw [List.filter_append, h0, List.append_nil]

/-- **A meta molecule cannot lift its subject's bid.** A thought's bid is a function of its
admissible partners and of the constraint molecules supporting it; meta molecules, never
constraints, change neither. -/
theorem bid_ignores_meta {β : Type*} (bid : I → List I → List I → β) (isConstraint : I → Bool)
    {m : I} (hm : isMeta m = false) (cs ms : List I) (hms : ∀ x ∈ ms, isMeta x = true)
    (hmc : ∀ x ∈ ms, isConstraint x = false) :
    bid m ((cs ++ ms).filter (Admissible isMeta about m)) ((cs ++ ms).filter isConstraint) =
      bid m (cs.filter (Admissible isMeta about m)) (cs.filter isConstraint) := by
  have h0 : ms.filter isConstraint = [] := List.filter_eq_nil_iff.2 fun x hx ↦ by simp [hmc x hx]
  rw [admissible_filter_meta hm cs ms hms, List.filter_append, h0, List.append_nil]

end SOV.Competition
