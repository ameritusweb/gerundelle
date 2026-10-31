import Mathlib.SetTheory.Cardinal.Order
import SOV.Firewall

/-!
# Does `no_outbound` give a perfectly secret cipher?

The SOV Cryptography Conjecture (2026-10-29) asks whether the no-outbound result
(`SOV.no_outbound`) yields a cipher with Shannon perfect secrecy and no pre-shared key as long
as the message. Its mapping: plaintext = a funded web, ciphertext = its projection into the
imagination register (`Web.toImag`), decryption = the inverse map that doesn't exist.

## The answer

* **Shannon's key bound holds for every scheme** (`key_bound`). A correctly decryptable,
  perfectly secret scheme has at least as many keys as messages, whatever its internal
  structure. Perfect secrecy is stated possibilistically (`PerfectlySecret`): any ciphertext
  one message can produce, every message can produce. Shannon's `P(m | c) = P(m)` implies this
  whenever every message has positive probability. So no construction, SOV-based or
  otherwise, achieves perfect secrecy with a key shorter than the message.
* **A keyless scheme can't do it** (`keyless_trivial`): a correct, perfectly secret scheme with
  one key has at most one message. The conjecture's mapping is keyless, so it is either
  incorrect or trivial. Here it is incorrect: `no_outbound` is the statement that no decryption
  map exists, and it applies to the legitimate receiver as much as to the adversary.
* **The projection leaks** (`projection_leaks`). Perfect secrecy needs the ciphertext to say
  nothing about the plaintext. A Constrain that narrows a slot changes both the geometry and
  the ledger, so an observer of the register learns that a Constrain receipt was written.
  `no_outbound` is worst-case non-invertibility, not independence.
* **What the firewall is.** `SOV.firewall` is noninterference *from* the register *to* the
  funded web: imagined structure can't influence funded structure. In information-flow terms
  that is integrity (Biba), not confidentiality. Funded structure flows freely into the
  register (`toImag_apply`), the opposite of what a secrecy property needs.
-/

namespace SOV.Crypto

universe u

/-- A symmetric encryption scheme that always decrypts correctly. -/
structure Scheme (K M Cph : Type*) where
  enc : K → M → Cph
  dec : K → Cph → M
  correct : ∀ k m, dec k (enc k m) = m

/-- Possibilistic perfect secrecy: every ciphertext one message can produce under some key,
every other message can produce under some key. -/
def PerfectlySecret {K M Cph : Type*} (s : Scheme K M Cph) : Prop :=
  ∀ m m' c, (∃ k, s.enc k m = c) → ∃ k, s.enc k m' = c

/-- **Shannon's key bound**: a correct, perfectly secret scheme has at least as many keys as
messages. -/
theorem key_bound {K M Cph : Type u} [Nonempty K] [Nonempty M] (s : Scheme K M Cph)
    (h : PerfectlySecret s) : Cardinal.mk M ≤ Cardinal.mk K := by
  obtain ⟨k₀⟩ := ‹Nonempty K›
  obtain ⟨m₀⟩ := ‹Nonempty M›
  have : ∀ m, ∃ k, s.enc k m = s.enc k₀ m₀ := fun m ↦ h m₀ m _ ⟨k₀, rfl⟩
  choose f hf using this
  refine Cardinal.mk_le_of_injective (f := f) fun m m' (hmm : f m = f m') ↦ ?_
  calc m = s.dec (f m) (s.enc (f m) m) := (s.correct _ _).symm
    _ = s.dec (f m) (s.enc k₀ m₀) := by rw [hf m]
    _ = s.dec (f m') (s.enc k₀ m₀) := by rw [hmm]
    _ = s.dec (f m') (s.enc (f m') m') := by rw [hf m']
    _ = m' := s.correct _ _

/-- **No keyless perfect secrecy**: with a single key, a correct, perfectly secret scheme has at
most one message. -/
theorem keyless_trivial {M Cph : Type*} (s : Scheme Unit M Cph) (h : PerfectlySecret s)
    (m m' : M) : m = m' := by
  obtain ⟨k, hk⟩ := h m m' (s.enc () m) ⟨(), rfl⟩
  calc m = s.dec () (s.enc () m) := (s.correct _ _).symm
    _ = s.dec () (s.enc () m') := by rw [← hk]
    _ = m' := s.correct _ _

open Operator

variable {S K B R A C E : Type*} [DecidableEq S] [Min B] [GeometryAlgebra B R]

/-- **The projection leaks**: a Constrain that narrows slot `i` changes what the register sees
and what the ledger holds, so the register reveals that the receipt was written. -/
theorem projection_leaks (w : Web S K B R A C E) (i j : S)
    (h : (w.geom.geometry i ⊓ w.geom.geometry j).feasibleSet ≠
      (w.geom.geometry i).feasibleSet) :
    ((constrain i j : Operator S B R A C E).apply w).toImag ≠ w.toImag ∧
      ((constrain i j : Operator S B R A C E).apply w).ledger.log ≠ w.ledger.log := by
  refine ⟨fun hw ↦ h ?_, fun hl ↦ ?_⟩
  · have := congrArg (fun v : ImagWeb S K B R ↦ (v.geom.geometry i).feasibleSet) hw
    simpa [Web.toImag, apply, base, GeomWeb.setGeometry] using this
  · have := congrArg List.length hl
    simp [apply, fiber, Ledger.append] at this

end SOV.Crypto
