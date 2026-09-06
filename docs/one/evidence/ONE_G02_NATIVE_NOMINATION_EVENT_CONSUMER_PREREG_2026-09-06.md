# ONE-G0.2 native nomination event consumer — preregistration

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`
Status: frozen before result-bearing execution

## Mission Lock

The native nomination trace bridge has proven that the promoted native rightmost-min selector emits exactly the anchor positions needed to reproduce the existing shared-observer pair-nomination semantics. However, event/index consumption remains Python and therefore cannot be charged honestly in the integrated native relation-dispatch A/B.

This Builder moves the **event consumer** into native code without yet duplicating or rewriting the proven selector. It receives the combined prior+current byte stream plus the already-proven native anchor trace, replays the existing local fixed-window and global minimizer nomination policy, and reports cross-object audition/exact counts and proof traffic.

This is a semantic/implementation bridge. Because producing the anchor trace and consuming it remain two passes, this experiment has no fused-observer product-speed authority.

## Baseline / oracle

Independent oracle: `_cross_object_reuse_nominations()` in `benchmarks/one/one_g02_relation_shared_observer_validation.py`.

Native anchor positions must continue to agree with the independent rightmost-min Python oracle before event-consumer agreement is evaluated.

## Invariants

The native event consumer must preserve exactly:

- 64-byte Gear witness semantics and the canonical `cmpct-gear-v1` table supplied by the harness;
- local fixed-window audition cadence;
- local index capacity and insertion/eviction behavior;
- global minimizer-index capacity and first-witness behavior;
- run-dominance suppression;
- `covered_until` suppression;
- exact witness equality before extension;
- non-overlapping right extension;
- left extension bounded by prior target coverage;
- cross-object classification at the prior/current boundary;
- no reader-visible ONE change.

No approximate hash match may become a Law. Negative controls must remain exact-negative.

## Falsifiable hypothesis

A compact native event/index consumer can reproduce every reference pair-nomination decision and accounting count from the already-proven native anchor trace, eliminating Python event-consumption semantics from the next integration boundary without adding a second discovery concept.

### Disproof

Reject or repair before further integration if any frozen row has:

- native/Python anchor-trace mismatch;
- cross-object audition-count mismatch;
- cross-object exact-nomination-count mismatch;
- false exact nomination on a reference-negative row;
- unreachable/out-of-order anchor consumption;
- index/resource-bound violation.

## Frozen validation envelope

Use the same generator-distinct family as the successful trace bridge:

- sizes: 4, 8, 16, 64, 256 KiB;
- seeds: 7, 29, 53;
- cases: `shift_plus1`, `damage_quarter`, `fragmented_every96`, `hostile_fixed_bands`, `fragmented_every32`, `independent_random`.

Persist per row:

- native and Python anchor counts;
- reference/native cross-object auditions;
- reference/native exact nominations;
- native local/global peak index entries;
- native verification and extension bytes inspected where available.

## Promotion law

Advance only if:

- `trace_mismatches = []`;
- `audition_mismatches = []`;
- `exact_mismatches = []`;
- `false_exact_nominations = []`;
- all existing ONE semantic/hostile tests pass.

No elapsed-time threshold exists for this stage. Any measured elapsed time is diagnostic only because selector trace production + event consumption are still separate passes.

## Decisions

- `advance_native_nomination_event_consumer` — all exact semantic/resource gates pass;
- `repair_native_nomination_event_consumer` — implementation disagrees with the reference;
- `retire_native_nomination_event_consumer_shape` — only if exact semantics require unreasonable state/complexity relative to the already-known policy.

## Hostile Reviewer

The most dangerous false win is to call this a fused native nominator merely because both pieces are native. It is not fused: the selector emits an intermediate trace and the consumer scans the combined bytes again. If this stage passes, the next experiment should fuse event consumption into the existing observation/minimizer pass and compare the fused result to this exact two-stage oracle before any writer-speed promotion.
