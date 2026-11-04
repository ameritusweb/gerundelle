# The SOV Algebra: Seventeen Operators

Every operation the algebra can perform on a web of understanding is done by a named
operator. Each operator has two parts: what it does to the graph (the geometry of
feasible sets and relations between slots), and what it writes in the provenance record
(the evidence ledger). The graph move cannot read the provenance record. The provenance
record can read the graph.

## The operators

| # | Operator | What it does to the graph | What it writes in the provenance record |
|---|---|---|---|
| 1 | **Fit** | Nothing | A lived receipt on the slot if the datum fits, otherwise to the unassigned pool. The only way to create lived evidence. |
| 2 | **Individuate** | Carves a new slot with a given geometry from unassigned records | A carve event |
| 3 | **Constrain** | Narrows a slot's feasible set to what is also feasible for another slot | A transitive accrual (noting the narrowing happened) |
| 4 | **Retract** | Widens a slot by restoring resolutions that were ruled out | A retraction event |
| 5 | **Compose** | Creates a new slot whose geometry is the product of two existing slots | A structural accrual |
| 6 | **Differentiate** | Splits a slot's feasible set between two new slots | A partition event dividing the receipts between them |
| 7 | **Unify** | Merges two slots to the feasible set they share (if any) | Pools one slot's receipts into the other |
| 8 | **Exclude** | Records that two slots resolve differently | A negative accrual |
| 9 | **Abstract** | Creates a new slot from the shared sub-pattern of two existing slots | A lien (a note that the new slot depends on both) |
| 10 | **Posit** | Nothing (seeds the imagination register) | Nothing |
| 11 | **Pose** | Nothing (sends a slot's geometry to another agent) | Nothing |
| 12 | **Attest** | Nothing | Imports another agent's receipts at a discount, if the posed geometry matches |
| 13 | **Bind** | Nothing | A coordination accrual between two agents' matching slots |
| 14 | **Quote** | Creates a new slot whose geometry is the reification of another slot's geometry (structure as content) | A second-order accrual |
| 15 | **Archaize** | Nothing | Evicts a slot's lived evidence (the only way to destroy lived mass) |
| 16 | **Anneal** | Nothing | An annealing event that adjusts a slot's certainty over time |
| 17 | **Relabel** | Carries a slot's geometry through a vocabulary map into a new slot in another domain | Nothing |

## Properties proved in Lean (Operator.lean, 22 theorems)

**Base-definability (C1).** The geometry an operator produces depends on the input
geometry alone. The graph move is typed so it cannot read the provenance record.

**Conservativity (C2).** Every event an operator appends carries that operator's tag.
Only Fit mints lived mass. Only Archaize destroys it.

**Functoriality (C3).** Running a list of operators in sequence is the same as running
each one in order. The log of a run is the old log plus the concatenated fiber events.

**Minimality.** Fourteen operators append events with pairwise distinct tags. No
composite of the other operators can append an event with a given operator's tag — no
operator is derivable from the others on the ledger. Posit, Pose, and Relabel append
nothing; their primitivity lives elsewhere (the imagination register, the posed message,
and the geometry sort respectively).

## How they group

**Evidence:** Fit (lived), Constrain (transitive), Exclude (negative), Compose
(structural), Quote (second-order) — these create or narrow evidence.

**Structure:** Individuate (carve a new slot), Differentiate (split), Unify (merge),
Abstract (shared pattern), Retract (widen) — these reshape the graph.

**Social:** Pose (send geometry), Attest (import receipts at a discount), Bind
(coordinate matching slots) — these move knowledge between agents.

**Maintenance:** Archaize (evict evidence), Anneal (adjust certainty over time) — these
manage the ledger over time.

**Imagination:** Posit (seed the imagination register) — tries things that don't count.

**Transfer:** Relabel (carry geometry through a vocabulary map) — the operator that makes
understanding local. Transport by Constrain alone is path-independent. Relabel makes it
path-dependent. No composite of meets produces it (proved in Holonomy.lean).
