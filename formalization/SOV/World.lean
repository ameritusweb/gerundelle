import Mathlib.Data.Finsupp.Basic
import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Linarith

/-!
# The world: conservation of potential

A formalization of the conserving world (`civilization/potential_world.py`; PHYSICS.md, principle 2:
"One conserved quantity: potential … The total never changes", and "Conservation (a theorem to
prove in Lean): at every slice, field + stored + embodied + in motion is constant. No sequence of
flips creates or destroys potential.").

Potential lies in places: the spring's field, the jar's store, what each object embodies, what
each object carries in motion, and other places' fields. The ledger gives each place its amount.
Every change the world makes moves an amount from one place to another:

* draw: field → store; spill: store → field;
* form: store → the formed object's embodied potential;
* cleave: store → the boulder, then the boulder → each part found inside, and the rest → the
  pebbles;
* propel: store → the skiff's motion; landing: motion → field.

The code writes some of these as assignments (`embodied["skiff"] = form_cost`,
`motion["skiff"] = launch_cost`, the parts' shares). Each is a transfer when the place was empty
before, as it is in every case the code reaches: a skiff forms only when there is none, flies
only from rest, and the parts are new.

## Results

* **Conservation** (`total_transfer`, `total_runMoves`, `total_apply`): no move and no sequence of
  moves creates or destroys potential.
* **No place goes negative** (`nonneg_transfer`, `nonneg_runMoves`): a move takes at most what its
  source holds (`spend` fails when the store is short; a draw takes at most the field).
-/

namespace SOV.World

/-- Where potential lies. `O` names objects, `P` other places. -/
inductive Place (O P : Type*)
  | field
  | store
  | embodied (o : O)
  | motion (o : O)
  | elsewhere (p : P)
  deriving DecidableEq

variable {O P : Type*}

/-- The ledger: each place's potential. -/
abbrev Ledger (O P : Type*) := Place O P →₀ ℝ

/-- The total potential. -/
noncomputable def total (L : Ledger O P) : ℝ :=
  L.sum fun _ x ↦ x

/-- Move `x` from place `a` to place `b`. -/
noncomputable def transfer (a b : Place O P) (x : ℝ) (L : Ledger O P) : Ledger O P :=
  L + Finsupp.single a (-x) + Finsupp.single b x

theorem total_add (L M : Ledger O P) : total (L + M) = total L + total M :=
  Finsupp.sum_add_index' (fun _ ↦ rfl) fun _ _ _ ↦ rfl

theorem total_single (a : Place O P) (x : ℝ) : total (Finsupp.single a x) = x :=
  Finsupp.sum_single_index rfl

/-- **A move conserves potential.** -/
theorem total_transfer (a b : Place O P) (x : ℝ) (L : Ledger O P) :
    total (transfer a b x L) = total L := by
  rw [transfer, total_add, total_add, total_single, total_single]
  ring

/-- The world's moves. -/
inductive Move (O P : Type*)
  | draw (take : ℝ)
  | spill (amount : ℝ)
  | form (o : O) (cost : ℝ)
  | condense (o : O) (cost : ℝ)
  | part (whole piece : O) (share : ℝ)
  | propel (o : O) (cost : ℝ)
  | land (o : O) (amount : ℝ)
  | carry (p : P) (amount : ℝ)
  | arrive (p : P) (amount : ℝ)

/-- Each move as a transfer: its source, its destination, its amount. -/
def Move.route : Move O P → Place O P × Place O P × ℝ
  | .draw x => (.field, .store, x)
  | .spill x => (.store, .field, x)
  | .form o x => (.store, .embodied o, x)
  | .condense o x => (.store, .embodied o, x)
  | .part w p x => (.embodied w, .embodied p, x)
  | .propel o x => (.store, .motion o, x)
  | .land o x => (.motion o, .field, x)
  | .carry p x => (.field, .elsewhere p, x)
  | .arrive p x => (.elsewhere p, .field, x)

noncomputable def Move.apply (m : Move O P) (L : Ledger O P) : Ledger O P :=
  transfer m.route.1 m.route.2.1 m.route.2.2 L

/-- Apply moves in order. -/
noncomputable def runMoves (ms : List (Move O P)) (L : Ledger O P) : Ledger O P :=
  ms.foldl (fun L m ↦ m.apply L) L

theorem total_apply (m : Move O P) (L : Ledger O P) : total (m.apply L) = total L :=
  total_transfer _ _ _ _

/-- **No sequence of moves creates or destroys potential.** -/
theorem total_runMoves (ms : List (Move O P)) (L : Ledger O P) :
    total (runMoves ms L) = total L := by
  induction ms generalizing L with
  | nil => rfl
  | cons m ms ih => simp only [runMoves, List.foldl_cons] at ih ⊢; rw [ih, total_apply]

/-! ### No place goes negative -/

/-- Every place holds a nonnegative amount. -/
def Nonneg (L : Ledger O P) : Prop :=
  ∀ a, 0 ≤ L a

/-- A move is affordable: a nonnegative amount, at most what its source holds. -/
def Affordable (a : Place O P) (x : ℝ) (L : Ledger O P) : Prop :=
  0 ≤ x ∧ x ≤ L a

theorem nonneg_transfer [DecidableEq O] [DecidableEq P] {a b : Place O P} {x : ℝ}
    {L : Ledger O P} (hL : Nonneg L) (hx : Affordable a x L) : Nonneg (transfer a b x L) := by
  intro c
  simp only [transfer, Finsupp.coe_add, Pi.add_apply, Finsupp.single_apply]
  have := hL c
  obtain ⟨h1, h2⟩ := hx
  split_ifs with hac hbc hbc <;> subst_vars <;> linarith

/-- Moves in order, each affordable when it is made. -/
def AffordableRun : List (Move O P) → Ledger O P → Prop
  | [], _ => True
  | m :: ms, L => Affordable m.route.1 m.route.2.2 L ∧ AffordableRun ms (m.apply L)

theorem nonneg_runMoves [DecidableEq O] [DecidableEq P] (ms : List (Move O P)) {L : Ledger O P}
    (hL : Nonneg L) (h : AffordableRun ms L) : Nonneg (runMoves ms L) := by
  induction ms generalizing L with
  | nil => exact hL
  | cons m ms ih =>
    simp only [runMoves, List.foldl_cons] at ih ⊢
    exact ih (nonneg_transfer hL h.1) h.2

end SOV.World
