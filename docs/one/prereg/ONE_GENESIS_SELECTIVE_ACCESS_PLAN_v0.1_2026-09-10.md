# CMPCT1 / ONE Genesis selective-access request plan v0.1

Date frozen: 2026-09-10
Status: preregistered before Genesis contender execution
Experimental lineage: ONE-G0.2

## Purpose

Define one contender-neutral selective request so the September 11 gate does not compare unlike operations after results are visible.

This document does not execute the frozen 15-workload matrix.

## Primary cross-contender request

For every workload containing at least two regular files:

1. enumerate regular files by normalized POSIX relative path;
2. select the file with greatest logical byte length; break ties by lexicographically smallest normalized path;
3. request that **one complete member only** from the archived state;
4. verify the returned member byte-for-byte against the executor-owned source file;
5. charge every archive/source byte touched, decoded/reconstructed byte, authentication/proof byte, temporary byte and open/preflight cost that the frozen reader exposes.

The logical request is therefore `read exactly one deterministic member`, not `extract archive then slice`, and not a candidate-specific byte range.

A contender with no proven direct selective member surface reports the selective measurement family as explicit `unavailable`. That absence is not zero-cost access and is not automatically a win for another contender.

## Single-regular-file workloads

A whole-member request would equal whole-object extraction and would not test selective behavior. For a workload with exactly one regular file, the cross-contender primary selective cell is `unavailable` unless every compared contender has a proven direct bounded range surface satisfying the same requested range without whole-root/archive materialization.

Candidate-only range evidence may still be retained as secondary capability evidence, clearly separated from the cross-contender cell.

## Why full-member rather than 4 KiB is the primary common request

Frozen v0.30 exposes `list_members`, `read_member` and `read_member_with_stats`, i.e. a member surface. ONE exposes both member and bounded range reconstruction. A 4 KiB ONE range compared with a v0.30 full-member decode would silently change request semantics. The common primary request therefore uses the strongest exact semantic intersection actually demonstrated before the gate.

Frozen v0.29 currently has no proven selective member/range surface. Its cell remains unavailable unless exact frozen authority is found before contender execution.

## Metric admission

Semantic exactness and access-resource instrumentation are separate claims.

- Correct returned bytes may establish selective semantic exactness.
- `decoded_context_bytes=None`, unknown touched bytes or unknown amplification remain `unavailable`; they are never converted to zero.
- For frozen v0.30 r24, its reader explicitly reports decoded-context/amplification as uninstrumented. Preserve that gap.
- A measured amplification value is admitted only if it is arithmetically consistent with decoded bytes divided by requested logical bytes.
- No wrapper may infer physical bytes touched from archive size unless the frozen operation actually reads the whole archive and that fact is measured at the process/I/O boundary.

## Deterministic selection receipt

The gate raw evidence must record, per workload where the primary request applies:

- selected relative path;
- selected logical bytes;
- selection rule version `largest-regular-member-lexical-tie-v1`;
- exact returned-byte verification result;
- whether the reader operation is direct member access or fallback extraction.

Fallback extraction is not admissible as selective access.

## Hostile-review failures

The selective comparison is invalid for a row if any contender-specific adapter:

- selects a different logical member;
- materializes the whole archive/root and reports only the returned member as touched work;
- changes from cold-open to already-open semantics selectively;
- turns unavailable instrumentation into zero;
- uses a non-frozen reader implementation for a historical comparator;
- omits authentication/proof work required by its product contract.
