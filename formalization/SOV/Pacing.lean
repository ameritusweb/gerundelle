import Mathlib.Data.Finset.Max
import Mathlib.Order.Preorder.Finite

/-!
# Phase 6c: the Pacing Proposition as a theorem about prerequisites

sov_geometry §4.5: learning moves only along the fringe; off-fringe depth "is not a hard
geodesic — it is a point not on the manifold"; a curriculum is geodesic flow (P59).

Concepts carry a prerequisite relation `pre a c` (`a` is a prerequisite of `c`). A learner's
state is the finite set `K` of concepts it knows. A concept is on the fringe of `K` when it is
not yet known and all its prerequisites are. A curriculum is a list of concepts learned in
order, each on the fringe when it is learned.

* **Only down-closed states are on the manifold** (`DownClosed.learn`): learning along the
  fringe never leaves the down-closed sets. A state missing a prerequisite of something it
  knows is not reachable at all, not merely hard to reach.
* **Every down-closed state is reachable** (`reachable_of_downClosed`), when prerequisites
  form a strict order. So the reachable states, the "prerequisite manifold", are exactly the
  finite down-closed sets.
* **Cycles are off the manifold forever** (`never_enters`): if every concept in a set has a
  prerequisite inside the set (a prerequisite cycle, say), no curriculum ever reaches any of
  them.
* **Every valid curriculum is a geodesic** (`card_learn`): a curriculum from `K` adds exactly
  one new concept per step, so all curricula between two states have the same length. P59's
  "geodesic curriculum advantage" therefore can't be a path-length advantage within the
  manifold. It contrasts curricula on the manifold with off-manifold ones, as §4.5 says
  ("not in difficulty reduction but in accessibility").
-/

namespace SOV.Pacing

variable {C : Type*} (pre : C → C → Prop)

/-- `c` is on the fringe of `K`: not yet known, every prerequisite known. -/
def InFringe (K : Finset C) (c : C) : Prop :=
  c ∉ K ∧ ∀ a, pre a c → a ∈ K

/-- `K` contains the prerequisites of everything it contains. -/
def DownClosed (K : Finset C) : Prop :=
  ∀ c ∈ K, ∀ a, pre a c → a ∈ K

variable [DecidableEq C]

/-- A curriculum is valid from `K` when each concept is on the fringe when it is learned. -/
def Valid : Finset C → List C → Prop
  | _, [] => True
  | K, c :: cs => InFringe pre K c ∧ Valid (insert c K) cs

/-- The state after learning a curriculum. -/
def learn (K : Finset C) (cs : List C) : Finset C :=
  cs.foldl (fun K c ↦ insert c K) K

variable {pre}

theorem valid_append {K : Finset C} {xs ys : List C} :
    Valid pre K (xs ++ ys) ↔ Valid pre K xs ∧ Valid pre (learn K xs) ys := by
  induction xs generalizing K with
  | nil => simp [Valid, learn]
  | cons x xs ih => simp only [List.cons_append, Valid, ih, learn, List.foldl_cons, and_assoc]

theorem learn_append (K : Finset C) (xs ys : List C) :
    learn K (xs ++ ys) = learn (learn K xs) ys :=
  List.foldl_append ..

/-- **Only down-closed states are on the manifold**: learning along the fringe preserves
down-closure. -/
theorem DownClosed.learn {K : Finset C} (hK : DownClosed pre K) {cs : List C}
    (h : Valid pre K cs) : DownClosed pre (SOV.Pacing.learn K cs) := by
  induction cs generalizing K with
  | nil => exact hK
  | cons c cs ih =>
    obtain ⟨⟨_, hc⟩, hcs⟩ := h
    refine ih (fun x hx a ha ↦ ?_) hcs
    rcases Finset.mem_insert.1 hx with rfl | hx
    · exact Finset.mem_insert_of_mem (hc a ha)
    · exact Finset.mem_insert_of_mem (hK x hx a ha)

/-- Reachable from knowing nothing. -/
theorem downClosed_of_reachable {K : Finset C} {cs : List C} (h : Valid pre ∅ cs)
    (hK : SOV.Pacing.learn ∅ cs = K) : DownClosed pre K :=
  hK ▸ DownClosed.learn (fun _ hc ↦ absurd hc (Finset.notMem_empty _)) h

/-- **Cycles are off the manifold forever**: if every concept in `S` has a prerequisite in `S`,
a learner that knows nothing in `S` never learns anything in `S`. -/
theorem never_enters {S : Set C} (hS : ∀ c ∈ S, ∃ a ∈ S, pre a c) {K : Finset C}
    (hK : ∀ c ∈ K, c ∉ S) {cs : List C} (h : Valid pre K cs) :
    ∀ c ∈ SOV.Pacing.learn K cs, c ∉ S := by
  induction cs generalizing K with
  | nil => exact hK
  | cons c cs ih =>
    obtain ⟨⟨_, hc⟩, hcs⟩ := h
    refine ih (fun x hx hxS ↦ ?_) hcs
    rcases Finset.mem_insert.1 hx with rfl | hx
    · obtain ⟨a, haS, ha⟩ := hS x hxS
      exact hK a (hc a ha) haS
    · exact hK x hx hxS

/-- **Every valid curriculum is a geodesic**: each step adds one new concept. -/
theorem card_learn {K : Finset C} {cs : List C} (h : Valid pre K cs) :
    (SOV.Pacing.learn K cs).card = K.card + cs.length := by
  induction cs generalizing K with
  | nil => rfl
  | cons c cs ih =>
    obtain ⟨⟨hc, _⟩, hcs⟩ := h
    change (SOV.Pacing.learn (insert c K) cs).card = _
    rw [ih hcs, Finset.card_insert_of_notMem hc, List.length_cons]
    omega

/-- **Every down-closed state is reachable**, when prerequisites are a strict order. -/
theorem reachable_of_downClosed {P : Type*} [PartialOrder P] [DecidableEq P] (K : Finset P)
    (hK : DownClosed (· < ·) K) :
    ∃ cs, Valid (· < ·) ∅ cs ∧ SOV.Pacing.learn ∅ cs = K := by
  induction h : K.card generalizing K with
  | zero => exact ⟨[], trivial, by simp [SOV.Pacing.learn, Finset.card_eq_zero.1 h]⟩
  | succ n ih =>
    obtain ⟨c, hcK, hmax⟩ := K.exists_maximal (Finset.card_pos.1 (by omega))
    have hK' : DownClosed (· < ·) (K.erase c) := by
      intro x hx a ha
      refine Finset.mem_erase.2 ⟨?_, hK x (Finset.mem_of_mem_erase hx) a ha⟩
      rintro rfl
      exact lt_irrefl _ (ha.trans_le (hmax (Finset.mem_of_mem_erase hx) ha.le))
    obtain ⟨cs, hv, hl⟩ := ih (K.erase c) hK' (by rw [Finset.card_erase_of_mem hcK, h]; rfl)
    refine ⟨cs ++ [c], valid_append.2 ⟨hv, ?_, trivial⟩, ?_⟩
    · rw [hl]
      refine ⟨Finset.notMem_erase c K, fun a ha ↦ Finset.mem_erase.2 ⟨ha.ne, hK c hcK a ha⟩⟩
    · rw [learn_append, hl]
      exact Finset.insert_erase hcK

end SOV.Pacing
