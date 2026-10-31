import Mathlib.Data.List.Perm.Basic
import Mathlib.Data.Finset.Basic

/-!
# Self-awareness: the meta layer

A formalization of `class Meta` and the meta track of `Mind.think`
(`analogy/molecules/molecules.py`; THOUGHT_MOLECULES.md §5f, tests T35–T39).

## The prediction lifecycle (`emit`, `check`, `settle`)

A meta molecule stands with a deadline. Each tick its prediction is checked (`holds`); a verdict
settles it. Confirmed, it is refreshed with a new deadline; refuted, it is dropped. Being detected
again while it stands does nothing (`emit` returns early). It may also fade out of the pool.

* **The mirror trap** (`detect_standing`, `deadline_changes_only_by_confirmation`,
  `refuted_dropped`): re-detection never refreshes a meta molecule, its deadline moves only on a
  confirmed prediction, and a refuted one is gone. With funding knocked out (`meta_funding`
  off, T37's control arm) a refuted molecule stays (`unfunded_refuted_stays`).
* **Nothing outlives its deadline undecided** (`check_before_deadline`, `standing_before_deadline`):
  `holds` decides every tick-checked kind at the deadline, so after each tick every standing meta
  molecule's deadline is still ahead.

## The meta track (`think`)

Meta molecules compete only among themselves for `meta_slots`, beside the thoughts' slots; the
kinds with an operation are ordered first.

* **Thinking about thinking never displaces a thought** (`base_filter_meta`): the thoughts'
  winners are computed from the non-meta bidders alone.
* **At most `meta_slots` meta winners** (`metaWinners_length_le`).
* **Operations take the meta slots first** (`operable_win_first`): a meta molecule without an
  operation wins only when every one with an operation has won.
* **Noticing gates the operation** (`operated_mem_top`): `observe` operates exactly on the meta
  molecules among the top winners.

## The parking rule (`parkable`)

* **A want is never parked** (`not_goal_of_parkable`), and nothing is parked while a thought, the
  facts register or storage carries what one of its holes needs (`no_key_near_of_parkable`).

## Splitting and mending (`differentiate`, `unify`)

* **Differentiation partitions the outcomes** (`mem_split_iff`).
* **Mending inverts splitting** (`unify_differentiate`): unifying the halves restores the
  outcomes, up to order. Outcomes that came to the halves after the split are kept
  (`unify_keeps_later`).
-/

namespace SOV.Meta

open scoped List

/-! ### The prediction lifecycle -/

/-- What can happen to one meta molecule in a tick. -/
inductive Event
  /-- Its formation condition is detected (`emit`). -/
  | detect
  /-- Its prediction is decided (`settle`). -/
  | verdict (ok : Bool)
  /-- It faded out of the pool (`check` archives it). -/
  | fade

/-- `meta_horizon` and the `meta_funding` ablation flag. -/
structure Params where
  horizon : ℕ
  funding : Bool

/-- One event at tick `t` on a meta molecule's watch entry: its deadline if it stands. -/
def step (P : Params) (t : ℕ) : Option ℕ → Event → Option ℕ
  | none, .detect => some (t + P.horizon)
  | some d, .detect => some d
  | some _, .verdict true => some (t + P.horizon)
  | some _, .verdict false => if P.funding then none else some (t + P.horizon)
  | some _, .fade => none
  | none, _ => none

variable {P : Params} {t d : ℕ}

/-- **Re-detection never refreshes**: it lives by its prediction, not by being re-seen. -/
theorem detect_standing : step P t (some d) .detect = some d :=
  rfl

/-- A refuted prediction drops the meta molecule. -/
theorem refuted_dropped (hP : P.funding = true) : step P t (some d) (.verdict false) = none := by
  simp [step, hP]

/-- Knocked out, funding no longer decides: a refuted meta molecule stays. -/
theorem unfunded_refuted_stays (hP : P.funding = false) :
    step P t (some d) (.verdict false) = some (t + P.horizon) := by
  simp [step, hP]

/-- **The deadline moves only on a confirmed prediction.** -/
theorem deadline_changes_only_by_confirmation (hP : P.funding = true) {e : Event} {d' : ℕ}
    (h : step P t (some d) e = some d') (hne : d' ≠ d) : e = .verdict true := by
  cases e with
  | detect => exact absurd (Option.some.inj h).symm hne
  | verdict ok => cases ok <;> simp_all [step]
  | fade => simp [step] at h

/-- `holds` decides at the deadline: a verdict for every tick-checked kind once final. -/
def DecidesAtDeadline (v : Bool → Option Bool) : Prop :=
  (v true).isSome

/-- The check of one standing meta molecule at tick `t`: the verdict `holds` gives, `final` when
the deadline is reached. -/
def check (P : Params) (t : ℕ) (v : Bool → Option Bool) : Option ℕ → Option ℕ
  | none => none
  | some d =>
    match v (decide (d ≤ t)) with
    | some ok => step P t (some d) (.verdict ok)
    | none => some d

/-- **Nothing outlives its deadline undecided**: after the check, a standing meta molecule's
deadline is ahead. -/
theorem check_before_deadline {v : Bool → Option Bool} (hv : DecidesAtDeadline v)
    (hh : 0 < P.horizon) (hP : P.funding = true) {d' : ℕ} {o : Option ℕ}
    (h : check P t v o = some d') : t < d' := by
  cases o with
  | none => simp [check] at h
  | some d =>
    simp only [check] at h
    by_cases hd : d ≤ t
    · obtain ⟨ok, hok⟩ := Option.isSome_iff_exists.1 hv
      rw [decide_eq_true hd, hok] at h
      cases ok
      · simp [step, hP] at h
      · simp only [step, Option.some.injEq] at h
        omega
    · rw [decide_eq_false hd] at h
      cases hvf : v false with
      | none => rw [hvf] at h; cases h; omega
      | some ok =>
        rw [hvf] at h
        cases ok
        · simp [step, hP] at h
        · simp only [step, Option.some.injEq] at h
          omega

/-- Formation after the check: a new meta molecule's deadline is ahead too. -/
theorem standing_before_deadline {v : Bool → Option Bool} (hv : DecidesAtDeadline v)
    (hh : 0 < P.horizon) (hP : P.funding = true) {o : Option ℕ} {d' : ℕ}
    (h : step P t (check P t v o) .detect = some d') : t < d' := by
  cases hc : check P t v o with
  | none => rw [hc] at h; simp [step] at h; omega
  | some d => rw [hc] at h; cases h; exact check_before_deadline hv hh hP hc

/-! ### Depth -/

/-- `emit`'s depth gate: a meta molecule about a subject at depth `s` forms only when `s` is below
`meta_depth`, and its id `meta:<kind>:<subject>` has depth `s + 1` (`depth` counts `meta:`). -/
def emitDepth (metaDepth s : ℕ) : Option ℕ :=
  if metaDepth ≤ s then none else some (s + 1)

/-- **The reflection tower is bounded**: no meta molecule is deeper than `meta_depth`. -/
theorem emitDepth_le {D s d : ℕ} (h : emitDepth D s = some d) : d ≤ D := by
  unfold emitDepth at h
  split_ifs at h with hs
  cases h
  omega

/-! ### The meta track -/

variable {I : Type*}

/-- `think`'s tracks on one level: the thoughts' winners from the non-meta bidders, then the meta
molecules, the operable kinds first, each list ordered by `order`. -/
def baseWinners (order : List I → List I) (isMeta : I → Bool) (k : ℕ) (bidders : List I) :
    List I :=
  (order (bidders.filter fun i ↦ !isMeta i)).take k

def metaWinners (order : List I → List I) (isMeta operable : I → Bool) (m : ℕ)
    (bidders : List I) : List I :=
  (order (bidders.filter fun i ↦ isMeta i && operable i) ++
    order (bidders.filter fun i ↦ isMeta i && !operable i)).take m

/-- **Thinking about thinking never displaces a thought**: the thoughts' winners depend only on
the non-meta bidders. -/
theorem base_filter_meta (order : List I → List I) (isMeta : I → Bool) (k : ℕ)
    {b₁ b₂ : List I} (h : b₁.filter (fun i ↦ !isMeta i) = b₂.filter fun i ↦ !isMeta i) :
    baseWinners order isMeta k b₁ = baseWinners order isMeta k b₂ := by
  simp only [baseWinners, h]

theorem metaWinners_length_le (order : List I → List I) (isMeta operable : I → Bool) (m : ℕ)
    (bidders : List I) : (metaWinners order isMeta operable m bidders).length ≤ m :=
  List.length_take_le _ _

/-- **Operations take the meta slots first**: if a meta molecule without an operation wins, every
one with an operation won. Requires only that `order` permutes its input. -/
theorem operable_win_first (order : List I → List I) (horder : ∀ l, order l ~ l)
    (isMeta operable : I → Bool) (m : ℕ) (bidders : List I) {x y : I}
    (hx : x ∈ metaWinners order isMeta operable m bidders) (hxo : operable x = false)
    (hy : y ∈ order (bidders.filter fun i ↦ isMeta i && operable i)) :
    y ∈ metaWinners order isMeta operable m bidders := by
  set A := order (bidders.filter fun i ↦ isMeta i && operable i)
  set B := order (bidders.filter fun i ↦ isMeta i && !operable i)
  simp only [metaWinners, List.take_append] at hx ⊢
  rcases List.mem_append.1 hx with hxA | hxB
  · have := (horder _).subset (List.mem_of_mem_take hxA)
    simp [hxo] at this
  · have hlt : A.length < m := by
      by_contra hle
      rw [Nat.sub_eq_zero_of_le (not_lt.1 hle)] at hxB
      simp at hxB
    exact List.mem_append_left _ (by rwa [List.take_of_length_le hlt.le])

/-- **Noticing gates the operation**: `observe` operates on the meta molecules among the top
winners that still stand. -/
def operated (isMeta : I → Bool) (standing : I → Prop) [DecidablePred standing] (top : List I) :
    List I :=
  top.filter fun i ↦ isMeta i && decide (standing i)

theorem operated_mem_top (isMeta : I → Bool) (standing : I → Prop) [DecidablePred standing]
    {top : List I} {i : I} (h : i ∈ operated isMeta standing top) : i ∈ top ∧ isMeta i :=
  ⟨List.mem_of_mem_filter h, by simp_all [operated]⟩

/-! ### The parking rule -/

variable {T : Type*}

/-- `parkable`: never a want, an experiment, an ownership instance or an answerable question, and
never while something near carries one of its keys. -/
def Parkable (goal : T) (tags : Set T) (exempt : Prop) (keys : List T) (near : List (Set T)) :
    Prop :=
  goal ∉ tags ∧ ¬ exempt ∧ ∀ k ∈ keys, ∀ x ∈ near, k ∉ x

/-- **A want is never parked.** -/
theorem not_goal_of_parkable {goal : T} {tags : Set T} {exempt : Prop} {keys : List T}
    {near : List (Set T)} (h : Parkable goal tags exempt keys near) : goal ∉ tags :=
  h.1

theorem no_key_near_of_parkable {goal : T} {tags : Set T} {exempt : Prop} {keys : List T}
    {near : List (Set T)} (h : Parkable goal tags exempt keys near) {k : T} (hk : k ∈ keys)
    {x : Set T} (hx : x ∈ near) : k ∉ x :=
  h.2.2 k hk x hx

/-! ### Splitting and mending -/

/-- An outcome: its tick, the situation's tags, and its sign. -/
structure Outcome (T : Type*) where
  tick : ℕ
  context : Finset T
  sign : ℤ

variable [DecidableEq T]

/-- `differentiate` on the boundary tag: the outcomes with the tag and those without. -/
def differentiate (tag : T) (hist : List (Outcome T)) : List (Outcome T) × List (Outcome T) :=
  (hist.filter fun o ↦ decide (tag ∈ o.context), hist.filter fun o ↦ !decide (tag ∈ o.context))

/-- `unify`: the halves merged back, their outcomes pooled. -/
def unify (halves : List (Outcome T) × List (Outcome T)) : List (Outcome T) :=
  halves.1 ++ halves.2

/-- **Differentiation partitions the outcomes**: each lands in the half its context selects. -/
theorem mem_split_iff (tag : T) (hist : List (Outcome T)) (o : Outcome T) :
    (o ∈ (differentiate tag hist).1 ↔ o ∈ hist ∧ tag ∈ o.context) ∧
      (o ∈ (differentiate tag hist).2 ↔ o ∈ hist ∧ tag ∉ o.context) := by
  simp [differentiate]

/-- **Mending inverts splitting**: unified, the halves give back the outcomes. -/
theorem unify_differentiate (tag : T) (hist : List (Outcome T)) :
    unify (differentiate tag hist) ~ hist :=
  List.filter_append_perm _ _

/-- Outcomes the halves gathered after the split are kept when they are unified. -/
theorem unify_keeps_later (tag : T) (hist ys ns : List (Outcome T)) :
    unify ((differentiate tag hist).1 ++ ys, (differentiate tag hist).2 ++ ns) ~ hist ++ ys ++ ns := by
  set Y := (differentiate tag hist).1
  set N := (differentiate tag hist).2
  calc Y ++ ys ++ (N ++ ns)
      _ ~ Y ++ (N ++ (ys ++ ns)) := by
        rw [List.append_assoc]
        exact (List.perm_append_comm_assoc _ _ _).append_left Y
      _ = unify (Y, N) ++ (ys ++ ns) := by simp [unify]
      _ ~ hist ++ ys ++ ns := by
        rw [List.append_assoc]
        exact (unify_differentiate tag hist).append_right _

end SOV.Meta
