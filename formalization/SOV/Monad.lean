import SOV.Operator

/-!
# Phase 5: the graded writer monad

sov_formal_spec §7 identifies the algebra as the Kleisli category of a graded writer monad
over the etymology monoid, indexed by web state: a named operator is an arrow
`state → state × events`, and arrows compose by concatenating events.

## The writer structure

* Kleisli arrows on a state `σ` writing to the free monoid of events (`List`, which is
  `FreeMonoid` by definition) satisfy the unit and associativity laws (`Writer.pure_comp`,
  `Writer.comp_pure`, `Writer.comp_assoc`).
* Each operator is an arrow (`Operator.arrow`); a schedule is their Kleisli composite
  (`Operator.arrows`). Its state is `run`, and the written events are exactly what the run
  appends to the etymology ledger (`arrows_fst`, `run_log_eq_arrows`).
* **Functoriality is associativity** (`arrows_append`): the arrow of `ops₁ ++ ops₂` is the
  Kleisli composite of the two, so provenance composes because logs concatenate.
* **The unit law is the trivial fiber**: Posit and Pose are the unit arrow (`arrow_posit`,
  `arrow_pose`).
* **Law 2 is the free monoid** (`log_ne_nil_comp`): nothing has an inverse in a free
  monoid, so no continuation can cancel what an operator wrote. Compensation appends.

## The grading

* **Conservativity is a grading, not the unit law.** An arrow has grade `g` when every event
  it writes carries a tag in `g` (`HasGrade`). Grades compose by union and the unit has
  grade `∅`. Every operator's arrow has the grade its row of the earning table gives
  (`arrow_hasGrade`), and so does every schedule (`arrows_hasGrade`).
* **Inadmissible pairings are grade errors.** Pose's and Posit's grade is empty, so any arrow
  with that grade writes nothing (`writes_nothing_of_grade`). The Lamarckian pairing (Pose
  base, accrue fiber) is not graded by Pose (`lamarckian_ill_graded`).

## The presentation question

The formal spec recasts compensation semantics as presenting the event monoid by generators
and relations, with "same ledger state" as the quotient. Taking "same ledger state" to mean
"replays to the same state" (`LedgerEquiv`):

* it is a congruence (`LedgerEquiv.append_left`, `LedgerEquiv.append_right`);
* the docs' empirical relation holds: `anneal(t₁); anneal(t₂) = anneal(t₂)` for `t₁ ≤ t₂`
  (`anneal_relation`), and anneals on one slot commute (`anneal_comm`). With the
  timestamped decay of `sov.py` these are theorems, not imposed relations;
* **the commutation P66 needs fails**: a lived accrual and an eviction on the same slot
  form a permutation pair that replays to different states (`accrue_evict_not_comm`). No
  quotient that respects ledger state can make them commute, so the docs' monotone
  fragment can't be confluent on the ledger. Phase 4's `fit_archaize_order` is the
  operator-level face of this.
* the replay quotient is also *too coarse* to be the etymology ledger: an earned accrual
  replays as the empty log (`earned_equiv_nil`). The quotient the spec asks for sits strictly
  between lists and replay states; this formalization does not pick one.

The full structure is state-indexed (an operator's fiber may read the web: Unify's identity
check, Fit's routing), so these are endo-arrows on one state type, not the textbook monad on
types.
-/

namespace SOV

namespace Writer

variable {σ M : Type*}

/-- The unit arrow: change nothing, write nothing. -/
def pure : σ → σ × List M :=
  fun s ↦ (s, [])

/-- Kleisli composition: run `f`, then `g`, concatenating what they write. -/
def comp (f g : σ → σ × List M) : σ → σ × List M :=
  fun s ↦ ((g (f s).1).1, (f s).2 ++ (g (f s).1).2)

theorem pure_comp (f : σ → σ × List M) : comp pure f = f := by
  funext s
  simp [comp, pure]

theorem comp_pure (f : σ → σ × List M) : comp f pure = f := by
  funext s
  simp [comp, pure]

theorem comp_assoc (f g h : σ → σ × List M) : comp (comp f g) h = comp f (comp g h) := by
  funext s
  simp [comp]

/-- The arrow writes only events whose tag is in `g`. -/
def HasGrade {T : Type*} (tag : M → T) (f : σ → σ × List M) (g : Set T) : Prop :=
  ∀ s, ∀ e ∈ (f s).2, tag e ∈ g

variable {T : Type*} {tag : M → T}

theorem hasGrade_pure : HasGrade tag (pure : σ → σ × List M) ∅ :=
  fun _ _ he ↦ absurd he List.not_mem_nil

theorem HasGrade.comp {f g : σ → σ × List M} {a b : Set T} (hf : HasGrade tag f a)
    (hg : HasGrade tag g b) : HasGrade tag (comp f g) (a ∪ b) := by
  intro s e he
  rcases List.mem_append.1 he with he | he
  · exact Or.inl (hf s e he)
  · exact Or.inr (hg _ e he)

theorem HasGrade.mono {f : σ → σ × List M} {a b : Set T} (hf : HasGrade tag f a)
    (hab : a ⊆ b) : HasGrade tag f b :=
  fun s e he ↦ hab (hf s e he)

/-- An arrow graded by `∅` writes nothing. -/
theorem HasGrade.eq_nil {f : σ → σ × List M} (hf : HasGrade tag f ∅) (s : σ) :
    (f s).2 = [] :=
  List.eq_nil_iff_forall_not_mem.2 fun e he ↦ hf s e he

end Writer

open Writer

/-- The earning-table grade of an operator name. -/
def OpKind.grade (k : OpKind) : Set EventTag :=
  {t | k.tag = some t}

namespace Operator

variable {S K B R A C E : Type*} [DecidableEq S] [Min B] [GeometryAlgebra B R]

/-- An operator as a Kleisli arrow: its effect on the web, and the events it writes. -/
noncomputable def arrow (op : Operator S B R A C E) :
    Web S K B R A C E → Web S K B R A C E × List (FiberEvent S A C E) :=
  fun w ↦ (op.apply w, op.fiber w)

/-- A schedule as the Kleisli composite of its operators. -/
noncomputable def arrows :
    List (Operator S B R A C E) →
      Web S K B R A C E → Web S K B R A C E × List (FiberEvent S A C E)
  | [] => pure
  | op :: ops => comp op.arrow (arrows ops)

theorem arrows_fst (ops : List (Operator S B R A C E)) (w : Web S K B R A C E) :
    (arrows ops w).1 = run ops w := by
  induction ops generalizing w with
  | nil => rfl
  | cons op ops ih => exact ih (op.apply w)

/-- The events a schedule writes are what its run appends to the etymology ledger. -/
theorem run_log_eq_arrows (ops : List (Operator S B R A C E)) (w : Web S K B R A C E) :
    (run ops w).ledger.log = w.ledger.log ++ (arrows ops w).2 := by
  induction ops generalizing w with
  | nil => simp [run_nil, arrows, Writer.pure]
  | cons op ops ih =>
    rw [run_cons, ih]
    simp [arrows, comp, arrow, apply, Ledger.append]

/-- **Functoriality is associativity.** The arrow of a concatenated schedule is the Kleisli
composite of the arrows of its parts. -/
theorem arrows_append (ops₁ ops₂ : List (Operator S B R A C E)) :
    (arrows (ops₁ ++ ops₂) : Web S K B R A C E → _) = comp (arrows ops₁) (arrows ops₂) := by
  induction ops₁ with
  | nil => exact (pure_comp _).symm
  | cons op ops ih => rw [List.cons_append, arrows, arrows, ih, comp_assoc]

/-- **The unit law is the trivial fiber**: Posit is the unit arrow on the funded web. -/
theorem arrow_posit (i : S) (x : R) :
    ((posit i x : Operator S B R A C E).arrow : Web S K B R A C E → _) = pure := by
  funext w
  simp [arrow, posit_apply, fiber, Writer.pure]

/-- Pose is the unit arrow on the funded web. -/
theorem arrow_pose (i : S) :
    ((pose i : Operator S B R A C E).arrow : Web S K B R A C E → _) = pure := by
  funext w
  simp [arrow, pose_apply, fiber, Writer.pure]

/-- **Law 2 is the free monoid.** No continuation cancels what an operator wrote. -/
theorem log_ne_nil_comp (op : Operator S B R A C E) (w : Web S K B R A C E)
    (h : op.fiber w ≠ [])
    (g : Web S K B R A C E → Web S K B R A C E × List (FiberEvent S A C E)) :
    (comp op.arrow g w).2 ≠ [] := by
  simp only [comp, arrow]
  exact fun h' ↦ h (List.append_eq_nil_iff.1 h').1

/-- **Conservativity is a grading.** An operator's arrow has its earning-table grade. -/
theorem arrow_hasGrade (op : Operator S B R A C E) :
    HasGrade FiberEvent.tag (op.arrow : Web S K B R A C E → _) op.kind.grade :=
  fun w e he ↦ (fiber_tag op w e he).symm

/-- A schedule is graded by the union of its operators' grades. -/
theorem arrows_hasGrade (ops : List (Operator S B R A C E)) :
    HasGrade FiberEvent.tag (arrows ops : Web S K B R A C E → _)
      {t | ∃ op ∈ ops, op.kind.tag = some t} := by
  induction ops with
  | nil => exact hasGrade_pure.mono (Set.empty_subset _)
  | cons op ops ih =>
    refine ((arrow_hasGrade op).comp ih).mono ?_
    rintro t (ht | ⟨op', hop', ht⟩)
    · exact ⟨op, List.mem_cons_self, ht⟩
    · exact ⟨op', List.mem_cons_of_mem _ hop', ht⟩

omit [DecidableEq S] [Min B] [GeometryAlgebra B R] in
/-- Pose's and Posit's grade is empty: any arrow with that grade writes nothing. -/
theorem writes_nothing_of_grade {σ : Type*} {f : σ → σ × List (FiberEvent S A C E)}
    {k : OpKind} (hk : k = .pose ∨ k = .posit) (hf : HasGrade FiberEvent.tag f k.grade)
    (s : σ) : (f s).2 = [] := by
  refine HasGrade.eq_nil (hf.mono ?_) s
  rcases hk with rfl | rfl <;> intro t ht <;> simp [OpKind.grade, OpKind.tag] at ht

/-- **The Lamarckian pairing is a grade error**: Pose's base with an accrue fiber writes a
receipt, so it is not graded by Pose. -/
theorem lamarckian_ill_graded (w : Web S K B R A C E) (i : S) (t : Option S) (c : C) (e : E) :
    ¬ HasGrade FiberEvent.tag
      (fun w : Web S K B R A C E ↦ ((pose i : Operator S B R A C E).apply w,
        [(FiberEvent.accrue t (.lived c e) : FiberEvent S A C E)]))
      OpKind.pose.grade := by
  intro h
  have := h w
  simp [OpKind.grade, OpKind.tag] at this

end Operator

/-! ### The presentation question -/

namespace LedgerState

variable {S A C E : Type*} [DecidableEq S]

/-- Two event lists present the same ledger state: they replay identically from any state. -/
def LedgerEquiv (l l' : List (FiberEvent S A C E)) : Prop :=
  ∀ st : LedgerState S, st.replay l = st.replay l'

theorem replay_append (st : LedgerState S) (l l' : List (FiberEvent S A C E)) :
    st.replay (l ++ l') = (st.replay l).replay l' :=
  List.foldl_append ..

theorem LedgerEquiv.append_right {l l' : List (FiberEvent S A C E)} (h : LedgerEquiv l l')
    (m : List (FiberEvent S A C E)) : LedgerEquiv (l ++ m) (l' ++ m) := fun st ↦ by
  rw [replay_append, replay_append, h]

theorem LedgerEquiv.append_left {l l' : List (FiberEvent S A C E)} (h : LedgerEquiv l l')
    (m : List (FiberEvent S A C E)) : LedgerEquiv (m ++ l) (m ++ l') := fun st ↦ by
  rw [replay_append, replay_append, h]

/-- Two anneals present the same state as one anneal to the later time. -/
theorem anneal_anneal (s : S) (t₁ t₂ : ℝ) :
    LedgerEquiv [(.anneal s t₁ : FiberEvent S A C E), .anneal s t₂] [.anneal s (max t₁ t₂)] :=
  fun st ↦ st.annealAt_annealAt s t₁ t₂

/-- The docs' empirical relation: `anneal(t₁); anneal(t₂) = anneal(t₂)` when `t₁ ≤ t₂`. -/
theorem anneal_relation (s : S) {t₁ t₂ : ℝ} (h : t₁ ≤ t₂) :
    LedgerEquiv [(.anneal s t₁ : FiberEvent S A C E), .anneal s t₂] [.anneal s t₂] := by
  simpa [max_eq_right h] using anneal_anneal (A := A) (C := C) (E := E) s t₁ t₂

/-- Anneals on one slot commute. -/
theorem anneal_comm (s : S) (t₁ t₂ : ℝ) :
    LedgerEquiv [(.anneal s t₁ : FiberEvent S A C E), .anneal s t₂]
      [.anneal s t₂, .anneal s t₁] :=
  fun st ↦ st.annealAt_comm s t₁ t₂

/-- **The commutation P66 needs fails.** A lived accrual and an eviction on one slot are a
permutation pair that replays to different states. -/
theorem accrue_evict_not_comm (i : S) (c : C) (e : E) :
    ([.accrue (some i) (.lived c e), .evict i] : List (FiberEvent S A C E)).Perm
        [.evict i, .accrue (some i) (.lived c e)] ∧
      ¬ LedgerEquiv ([.accrue (some i) (.lived c e), .evict i] : List (FiberEvent S A C E))
        [.evict i, .accrue (some i) (.lived c e)] := by
  refine ⟨List.Perm.swap _ _ _, fun h ↦ ?_⟩
  have := congrArg (fun st : LedgerState S ↦ st.mass (some i)) (h ⟨0, 0, fun _ ↦ 0, fun _ ↦ 0⟩)
  simp [replay, step, Accrual.livedMass] at this

/-- The replay quotient is too coarse for the etymology ledger: it forgets earned receipts. -/
theorem earned_equiv_nil (t : Option S) (k : EarnedKind) :
    LedgerEquiv [(.accrue t (.earned k) : FiberEvent S A C E)] [] :=
  fun st ↦ by simp [replay, step, Accrual.livedMass]

end LedgerState

end SOV
