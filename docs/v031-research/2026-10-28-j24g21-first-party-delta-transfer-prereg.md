# J24G21 — First-party transaction transfer falsifier (preregistration)

Date: 2026-10-28 UTC. **RESEARCH ONLY; NO PRODUCT OR RELEASE CREDIT.**

## Current authority and distinct ownership
Published CMPCT main `80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / r24. Independent **generality/economics falsifier** stacked on certified-projection research #691/#694, neither a duplicate implementation nor a promotion. #574 exclusively owns Discovery STATE reconciliation; #690/#693/#697 own extraction-budget correctness. No mutations to those surfaces.

## Primary scientific question (before outcome)
Does J24G19's C-certified projection actually improve **ordinary first-party Writer-generated deltas**, or do its large memory wins require `extension` metadata absent from the legitimate transaction creation paths?

**Source-derived baseline:** `src/cmpct/transactions.py` emits deltas in `append_update`, `append_delete`, `append_rename` as maps containing `blobs` and `ops`; no `extension` value. Every 64 deltas may yield a full checkpoint rather than a delta. The experimental `projected()` scans then discards unknown fields; without those fields no payload materialization is avoided. Previous J24G19 physical Reader controls already reported small-input slowdown, but a clean first-party transfer court and component-level causal attribution are not yet established.

## Frozen hypotheses and decision
- H1 structural: extracted physical Writer r24 delta and independently generated first-party-equivalent deltas (rename/delete/update-shaped, short and long member names, ASCII and Unicode, object-count perturbations) contain no ignored large extension; projected values for `ops`/`blobs` exactly match original. First-party Writers have no relevant `extension` producer according to this exact audited source; any counterexample rejects the structural generality claim.
- H2 economic: for the ordinary first-party physical rename delta, full-decoder is not materially slower than certification+projection. Measure repeated warmed component CPU/wall, identical immutable bytes and same decoded semantics; report raw independent process samples and confounding overhead. Do not select a threshold from the result.
- H3 contrast: a fully signed, research-constructed large `extension` delta from #691 retains a certifiable positive class. It is a research-only different input distribution, **not evidence of first-party prevalence**. Confirm original/projection known-field equivalence, original structural size and certification eligibility, without claiming first-party adoption.
- H4 hostile: unknown nested bad keys, duplicate known keys, truncation, long/non-ASCII keys, and trailing bytes retain original acceptance or rejection with fallback.

**Disproof:** an ordinary physical first-party delta showing a repeatable meaningful CPU+memory win at same semantics, a Writer codepath producing a large ignored extension, a certificate that changes accepted/rejected semantics, or source/hash custody mismatch. Retire the claim if evidence cannot be tied to authentic physical payload.

## Evidence ladder
1. Exact current `transactions.py` source and signed footer payload extraction from unmodified first-party Writer archive in J24G19 original hosted artifact.
2. Independent detached C certificate compiled from the exact J24G19 C source; Python projection with preserved source identity; no CMPCT dependencies in local referee.
3. Unmodified signed-physical contrast, deterministic structural perturbations and CPU/wall ABBA with raw repetitions; no `tracemalloc` in timing.
4. Cold process VmHWM only if economic decision genuinely depends on it. Product/Windows/macOS/release claims remain unearned.

## BONK
- Exploit stronger owner: #691/#694 already prove synthetic ignored-extension class. Do not rerun 800k memory.
- Different frame: **producer-reachable opportunity and global feature carrying cost**, not codec tweak or more extension sizes.
- Cheapest falsifier: inspect producer plus actual physical Writer delta, then small direct-vs-projected timing. No full product benchmark until generic product applicability survives.
- Controls: direct `msgpack.unpackb`, original real first-party Writer signed data, positive synthetic large extension, malformed/duplicate negative.
- Potential alternative explanation: if unmodified Writer metadata is so small all comparisons are dominated by Python/ctypes scheduling overhead, limit claim to absence of avoided decode and retain conservative timing evidence.

No existing experimental hypothesis/threshold or release gate may be weakened. Preserve all results including negatives.
