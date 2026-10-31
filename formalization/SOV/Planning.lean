import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.Fintype.Card
import Mathlib.Basic.Real.Basic

/-!
# Planning: sub-wants and constraint convergence

## Sub-wants

A formalization of the sub-want stack (`analogy/molecules/sov_agent.py`: `planned`, `subwant`,
`drop_sub`, `watch`; civilization LADDER.md P6). A want the planner finds no way to sets a nearer
want; the want it served goes on a stack. A sub-want is set only when the stack is under four deep
(`planned`), and only a fact not already taken: not the current want, not one on the stack, and not
one dropped before (`subwant`'s `makeable`). A sub-want met hands back to the want it served; one
not met in time is dropped, recorded as failed, and the want it served taken up again. When a want
further up is met on the way, the sub-wants under it go.

The stack is written here innermost first (the code keeps it outermost first and pops from the
end). The P8 option `keep_subs`, off by default, can restore a dropped fact; it is not modelled.

* **At most four deep** and **no want twice** (`inv_run`): along any run, the stack never exceeds
  four, and no want appears twice among the current want and the stack, so backward chaining never
  cycles.
* **A dropped sub-want is never set again** (`inv_run`: no current or stacked want is failed).
* **The search gives up finitely** (`drops_le_card`): over a finite set of facts, a run drops at most
  as many sub-wants as there are facts.

## Constraint convergence (`JustOne`)

`Mind.support` in `candidates` mode: an attempt is supported by every constraint whose open site it
fills, each by its activation (CONSTRAINT_DISCOVERY.md: "Failures reveal constraints; the solution
is the one left standing"). Support is recomputed each tick, never accumulated.

* **An attempt meeting every constraint is supported at least as much as any other**
  (`support_le_of_fills_all`), and strictly more than one missing a live constraint
  (`support_lt_of_misses`).
* **JustOne** (`justOne`): when exactly one attempt meets every constraint and each other misses a
  live one, that attempt is the unique best supported.
-/

namespace SOV.Planning

/-! ### Sub-wants -/

variable {W : Type*} [DecidableEq W]

/-- The want being pursued, the wants it serves (innermost first), and the sub-wants dropped. -/
structure Wants (W : Type*) where
  goal : W
  stack : List W
  failed : Finset W

inductive Op (W : Type*)
  /-- `planned`: a nearer want set. -/
  | set (sub : W)
  /-- `watch`: the sub-want met, the want it served taken up again. -/
  | met
  /-- `drop_sub`: not met in time, set aside for good. -/
  | drop
  /-- `watch`: a want `k + 1` places up met on the way; the sub-wants under it go. -/
  | ancestor (k : ℕ)

/-- One step; `none` when it does not apply (the code does not take it). -/
def step (s : Wants W) : Op W → Option (Wants W)
  | .set sub =>
    if s.stack.length < 4 ∧ sub ∉ s.goal :: s.stack ∧ sub ∉ s.failed then
      some ⟨sub, s.goal :: s.stack, s.failed⟩
    else none
  | .met =>
    match s.stack with
    | p :: rest => some ⟨p, rest, s.failed⟩
    | [] => none
  | .drop =>
    match s.stack with
    | p :: rest => some ⟨p, rest, insert s.goal s.failed⟩
    | [] => none
  | .ancestor k =>
    match s.stack.drop k with
    | p :: rest => some ⟨p, rest, s.failed⟩
    | [] => none

/-- Run steps in order. -/
def run : Wants W → List (Op W) → Option (Wants W)
  | s, [] => some s
  | s, o :: os => (step s o).bind fun s' ↦ run s' os

def Op.isDrop : Op W → Bool
  | .drop => true
  | _ => false

/-- The invariant: at most four deep, no want twice, none of them failed. -/
def Inv (s : Wants W) : Prop :=
  s.stack.length ≤ 4 ∧ (s.goal :: s.stack).Nodup ∧ ∀ x ∈ s.goal :: s.stack, x ∉ s.failed

omit [DecidableEq W] in
theorem inv_start (g : W) : Inv (⟨g, [], ∅⟩ : Wants W) := by
  simp [Inv]

theorem inv_step {s s' : Wants W} {o : Op W} (hs : Inv s) (h : step s o = some s') :
    Inv s' ∧ s'.failed.card = s.failed.card + if o.isDrop then 1 else 0 := by
  obtain ⟨hlen, hnd, hnf⟩ := hs
  cases o with
  | set sub =>
    simp only [step] at h
    split_ifs at h with hc
    cases h
    obtain ⟨hl, hnot, hf⟩ := hc
    refine ⟨⟨by simp; omega, List.nodup_cons.2 ⟨hnot, hnd⟩, ?_⟩, by simp [Op.isDrop]⟩
    intro x hx
    rcases List.mem_cons.1 hx with rfl | hx
    · exact hf
    · exact hnf x hx
  | met =>
    simp only [step] at h
    split at h
    · rename_i p rest hst
      cases h
      rw [hst] at hlen hnd hnf
      refine ⟨⟨by simp at hlen ⊢; omega, (List.nodup_cons.1 hnd).2, fun x hx ↦ hnf x (by simp_all)⟩,
        by simp [Op.isDrop]⟩
    · cases h
  | drop =>
    simp only [step] at h
    split at h
    · rename_i p rest hst
      cases h
      rw [hst] at hlen hnd hnf
      have hg : s.goal ∉ s.failed := hnf _ (by simp)
      refine ⟨⟨by simp at hlen ⊢; omega, (List.nodup_cons.1 hnd).2, fun x hx ↦ ?_⟩, ?_⟩
      · simp only [Finset.mem_insert, not_or]
        refine ⟨fun hxg ↦ ?_, hnf x (by simp_all)⟩
        subst hxg
        exact (List.nodup_cons.1 hnd).1 hx
      · simp [Op.isDrop, Finset.card_insert_of_notMem hg]
    · cases h
  | ancestor k =>
    simp only [step] at h
    split at h
    · rename_i p rest hst
      cases h
      have hsub : p :: rest = s.stack.drop k := hst.symm
      have hsl : (p :: rest).Sublist s.stack := hsub ▸ List.drop_sublist _ _
      refine ⟨⟨?_, ?_, fun x hx ↦ hnf x (List.mem_cons_of_mem _ (hsl.subset hx))⟩,
        by simp [Op.isDrop]⟩
      · have := hsl.length_le
        simp at this ⊢
        omega
      · exact (hsl.trans (List.sublist_cons_self _ _)).nodup hnd
    · cases h

/-- **The invariant holds along any run**, and the failed sub-wants are exactly the drops. -/
theorem inv_run {s s' : Wants W} {os : List (Op W)} (hs : Inv s) (h : run s os = some s') :
    Inv s' ∧ s'.failed.card = s.failed.card + (os.filter Op.isDrop).length := by
  induction os generalizing s with
  | nil => cases h; simp [hs]
  | cons o os ih =>
    simp only [run, Option.bind_eq_some_iff] at h
    obtain ⟨s₁, h₁, h₂⟩ := h
    obtain ⟨hi, hc⟩ := inv_step hs h₁
    obtain ⟨hi', hc'⟩ := ih hi h₂
    refine ⟨hi', ?_⟩
    rw [hc', hc, List.filter_cons]
    cases o.isDrop
    · simp
    · simp only [ite_eq_left, List.length_cons]
      omega

/-- **The search gives up finitely**: a run from the start drops at most as many sub-wants as there
are facts. -/
theorem drops_le_card [Fintype W] (g : W) {s' : Wants W} {os : List (Op W)}
    (h : run ⟨g, [], ∅⟩ os = some s') : (os.filter Op.isDrop).length ≤ Fintype.card W := by
  have := (inv_run (inv_start g) h).2
  simp only [Finset.card_empty, zero_add] at this
  rw [← this]
  exact Finset.card_le_univ _

/-! ### Constraint convergence -/

variable {X Cn : Type*}

open Classical in
/-- An attempt's support: the activations of the constraints whose sites it fills. -/
noncomputable def support (cons : Finset Cn) (act : Cn → ℝ) (fills : X → Cn → Prop) (x : X) : ℝ :=
  ∑ c ∈ cons.filter (fills x), act c

variable {cons : Finset Cn} {act : Cn → ℝ} {fills : X → Cn → Prop}

/-- An attempt meeting every constraint is supported at least as much as any other. -/
theorem support_le_of_fills_all (hact : ∀ c, 0 ≤ act c) {x : X} (hx : ∀ c ∈ cons, fills x c)
    (y : X) : support cons act fills y ≤ support cons act fills x := by
  classical
  have : cons.filter (fills x) = cons := Finset.filter_true_of_mem hx
  simp only [support, this]
  exact Finset.sum_le_sum_of_subset_of_nonneg (Finset.filter_subset _ _) fun c _ _ ↦ hact c

/-- And strictly more than one that misses a live constraint. -/
theorem support_lt_of_misses (hact : ∀ c, 0 ≤ act c) {x y : X} (hx : ∀ c ∈ cons, fills x c)
    {c : Cn} (hc : c ∈ cons) (hyc : ¬ fills y c) (hpos : 0 < act c) :
    support cons act fills y < support cons act fills x := by
  classical
  have : cons.filter (fills x) = cons := Finset.filter_true_of_mem hx
  simp only [support, this]
  exact Finset.sum_lt_sum_of_subset (Finset.filter_subset _ _) hc
    (by simp [hyc]) hpos fun j _ _ ↦ hact j

/-- **JustOne**: when one attempt meets every constraint and each other misses a live one, it is the
unique best supported. -/
theorem justOne (hact : ∀ c, 0 ≤ act c) {x : X} (hx : ∀ c ∈ cons, fills x c)
    (hothers : ∀ y, y ≠ x → ∃ c ∈ cons, ¬ fills y c ∧ 0 < act c) (y : X) (hy : y ≠ x) :
    support cons act fills y < support cons act fills x := by
  obtain ⟨c, hc, hyc, hpos⟩ := hothers y hy
  exact support_lt_of_misses hact hx hc hyc hpos

end SOV.Planning
