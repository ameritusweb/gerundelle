import SOV.Operator

/-!
# The imagination firewall

The imagination register is the geometry sort acting on itself with no fiber
(imagination_register §2). Its relation to the funded web (imagination_register §4):

* **Inbound, a morphism exists.** Forgetting the ledger (`Web.toImag`) sends any funded web
  to the register, and it commutes with every operator's geometry move (`toImag_apply`).
* **Outbound, no morphism exists.** The plan's `¬∃ f : ImagSlot → Slot, IsMonadMorphism f`
  doesn't typecheck (slots are not monads), and some function always exists. Two statements
  carry the content instead:
  - `no_outbound`: any map from the register back to funded webs gets lived mass wrong on
    some web. Webs with the same geometry can differ in funding, so funding can't be read
    off imagined structure.
  - `firewall` (non-interference): run any interleaving of funded operators, free register
    moves, and Posit seeds. The funded web that results is the run of the funded operators
    alone. Nothing in the register, and no register move, reaches it.
* **The only return path is external.** Register contents can influence the funded web only
  through which operators the generator chooses to run, e.g. which data Fit receives. That
  choice is outside the algebra, which is why `firewall` quantifies over all operator lists.

The monad structure itself (graded writer over the etymology monoid) is Phase 5.
-/

namespace SOV

open Operator

variable {S K B R A C E : Type*}

namespace Web

/-- The inbound morphism: forget the ledger. Any funded web is a valid register seed. -/
def toImag (w : Web S K B R A C E) : ImagWeb S K B R :=
  ⟨w.geom⟩

variable [DecidableEq S]

/-- Lived mass of a web's ledger. -/
noncomputable def livedMass (w : Web S K B R A C E) : ℕ :=
  (w.ledger.state 0).mass.degree

/-- A lived accrual adds one unit of lived mass. -/
theorem livedMass_append_lived (w : Web S K B R A C E) (t : Option S) (c : C) (e : E) :
    (⟨w.geom, w.ledger.append [.accrue t (.lived c e)]⟩ : Web S K B R A C E).livedMass =
      w.livedMass + 1 := by
  have h₁ := LedgerState.step_conservation (w.ledger.state 0)
    (FiberEvent.accrue t (.lived c e) : FiberEvent S A C E)
  have h₂ := LedgerState.step_writtenOff_of_not_evict (w.ledger.state 0)
    (e := (FiberEvent.accrue t (.lived c e) : FiberEvent S A C E)) (by simp [FiberEvent.IsEvict])
  simp only [livedMass, Ledger.state_append, LedgerState.replay, List.foldl_cons,
    List.foldl_nil]
  simp only [FiberEvent.livedCount, Accrual.livedMass] at h₁
  omega

end Web

variable [DecidableEq S] [Min B] [GeometryAlgebra B R]

/-- The inbound morphism commutes with every operator's geometry move. -/
theorem toImag_apply (op : Operator S B R A C E) (w : Web S K B R A C E) :
    (op.apply w).toImag = ⟨op.base w.toImag.geom⟩ :=
  rfl

omit [Min B] [GeometryAlgebra B R] in
/-- **No outbound morphism.** Every map from the register to funded webs misreports lived
mass on some web with the given geometry. -/
theorem no_outbound [Inhabited C] [Inhabited E] (g : ImagWeb S K B R → Web S K B R A C E)
    (w : Web S K B R A C E) :
    ∃ w' : Web S K B R A C E, w'.geom = w.geom ∧ (g w'.toImag).livedMass ≠ w'.livedMass := by
  by_cases h : (g w.toImag).livedMass = w.livedMass
  · refine ⟨⟨w.geom, w.ledger.append [.accrue none (.lived default default)]⟩, rfl, ?_⟩
    rw [Web.livedMass_append_lived]
    change (g w.toImag).livedMass ≠ _
    omega
  · exact ⟨w, rfl, h⟩

/-- A step of the combined system: a funded operator, a free move inside the register
(any geometry move, widening included: Law 6 does not hold there), or a Posit seed. -/
inductive SysOp (S K B R A C E : Type*)
  | funded (op : Operator S B R A C E)
  | imagine (f : GeomWeb S K B R → GeomWeb S K B R)
  | posit (i : S) (x : R)

namespace SysOp

/-- Apply a system step to a funded web and a register. -/
noncomputable def step :
    SysOp S K B R A C E → Web S K B R A C E × ImagWeb S K B R →
      Web S K B R A C E × ImagWeb S K B R
  | funded op, (w, h) => (op.apply w, h)
  | imagine f, (w, h) => (w, ⟨f h.geom⟩)
  | posit i x, (w, _) => (w, positImage w i x)

/-- The funded operator in a step, if any. -/
def funded? : SysOp S K B R A C E → Option (Operator S B R A C E)
  | funded op => some op
  | _ => none

/-- Run a list of system steps. -/
noncomputable def run (sops : List (SysOp S K B R A C E))
    (st : Web S K B R A C E × ImagWeb S K B R) : Web S K B R A C E × ImagWeb S K B R :=
  sops.foldl (fun st o ↦ o.step st) st

end SysOp

/-- **The firewall** (non-interference): the funded web after any run of the combined system
is the run of its funded operators alone, whatever the register holds or does. -/
theorem firewall (sops : List (SysOp S K B R A C E)) (w : Web S K B R A C E)
    (h : ImagWeb S K B R) :
    (SysOp.run sops (w, h)).1 = Operator.run (sops.filterMap SysOp.funded?) w := by
  induction sops generalizing w h with
  | nil => rfl
  | cons o sops ih =>
    cases o with
    | funded op => exact ih (op.apply w) h
    | imagine f => exact ih w ⟨f h.geom⟩
    | posit i x => exact ih w (positImage w i x)

/-- The funded result does not depend on the register's starting contents. -/
theorem firewall_register_irrelevant (sops : List (SysOp S K B R A C E))
    (w : Web S K B R A C E) (h h' : ImagWeb S K B R) :
    (SysOp.run sops (w, h)).1 = (SysOp.run sops (w, h')).1 := by
  rw [firewall, firewall]

end SOV
