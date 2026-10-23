# v0.31 O0 — serialized-append stale-snapshot falsifier (preregistered)

**Status:** PREDICTION FROZEN; scientific/behavioral court only; no product patch, promotion, or format change.

**Exact authority at preregistration (2026-10-23 UTC):**
- Canonical development: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`
- `src/cmpct/transactions.py` blob: `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`
- Shipping checkpoint: v0.30.0; wire revision 24.
- Source semantics: `append_rename` reads `latest_footer_pos` under `CMPCT`, leaves that snapshot, and later passes `prev_footer` into `_append_generation`; no exclusive writer authority spans the read-modify-commit transaction.

## Primary question
If two individually valid disjoint public `append_rename` operations both snapshot the same committed footer, and their *whole generation appends are serialized without byte interleaving*, can both return success while only one operation remains in the live committed logical generation?

## Prediction before observation
- **Sequential baseline:** two disjoint renames, one after the other, both survive, remain readable, and satisfy structural preflight.
- **Controlled concurrency:** barrier after both `CMPCT` snapshots, then a lock around each *unchanged* `_append_generation` call to remove write-byte interleaving. Both calls return without error, but the final committed index includes exactly one of the two requested new names because both footers use the same predecessor. The earlier appended generation is not reachable along the newest footer chain.
- No format mutation, synthetic footer, or evaluator weakening is permitted.

## Strongest simpler control / alternative explanation
Sequential same-archive updates control general rename correctness. Serializing the entire original generation writer controls physical byte interleaving, so an observed lost update cannot be explained merely by races between individual `write()` or `fsync()` calls. A direct comparison of each call's return and final `CMPCT.by` is required. If both renames survive, the hypothesis is falsified. If the archive becomes unreadable or an operation raises, classify as a different concurrency failure, not as the predicted silent lost-update mechanism.

## Scope and kill condition
This test does **not** establish an API promise of supported multiwriter semantics and does not allege corruption of historical releases. Its outcome must be interpreted as an unsatisfied capability/single-writer assumption if no multiwriter contract exists. No product credit from the research court. A prospective repair would need an explicit single-writer/locking contract (including process, platform and failure recovery semantics), a new adversarial test, and unchanged sequential performance/recovery gates.

## Concurrency coordination
An old branch `agent/phased1-v031-transaction-multiwriter-ownership` exists at the **unchanged** development SHA with zero unique commits and no associated PR in current search. This branch is not modified. The present lane is explicitly preregistered as an *independent read-only-source falsifier*, not an alternative writer implementation; it shares neither mutation surface nor authority with that dormant branch. Other v0.31 Writer namespace/hardlink fixes (#241/#245/#247/#250) own different semantic conditions and remain untouched.

## Disposition to record after evidence
Retain the actual test outputs and head-bound workflow run, including failing / infrastructure observations. Mark CONFIRMED, FALSIFIED or AMBIGUOUS separately for lost update, physical interleaving and supported-contract claims. Notify the existing transaction ownership lane through a durable GitHub issue/PR handoff only if decision-changing evidence appears. Counterfactual discriminator: snapshot both footer references and serialize whole appends; the experiment should exclude superficial OS-interleaving explanations.
