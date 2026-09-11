# ONE-G0.2 authenticated selective-open stage owner — pre-result hostile review

Date: 2026-09-08
Status: pre-result; owner thresholds frozen
Experimental version: `ONE-G0.2`

## Mission / bounded claim

This profiler asks which current in-memory selective-open stage owns compute after an authenticated tree already exists: proof extraction or proof verification/reconstruction. It does not introduce a reader mechanism and does not independently promote the packed interval path.

Two proof-production pipelines are measured against the same `verify_range()` implementation:

- materialized Python reference tree + `prove_range()`;
- packed native tree + `prove_range_packed_interval()`.

The second path has its own independent exact-source promotion evidence. Tree creation remains outside this profiler by design.

## Hostile findings addressed before result

1. **Block-order drift would bias owner attribution.** The first implementation timed all proof samples and then all verification samples. This was repaired before hosted evidence: proof and verification stage samples now alternate order within every repetition. The owner threshold remains 60% on both wall and CPU in at least 12/16 rows per pipeline.
2. **Object teardown is excluded.** The prior stage result is released before either clock starts, while the current result remains alive through both clock stops. This prevents proof/output destruction from being charged to the following stage.
3. **Verification receives a stable prebuilt proof.** Its timer measures verification/reconstruction, not hidden proof regeneration. Composed `prove -> verify` is timed separately as an audit.
4. **Matrix identity is exact.** The adjudicator compares the complete unique `(pipeline, leaf_bytes, start, length)` key set with the frozen 32-cell matrix; missing or duplicated cells invalidate. Adversarial tests cover both cases.
5. **The packed path cannot self-promote here.** Its independent interval falsifier remains authority for whether it is a preferred proof generator. This profiler only allocates the next optimization budget inside authenticated selective open.
6. **Stage sums are not assumed to equal composition.** `stage_sum / composed` is recorded for wall and CPU; large divergence is evidence of context/lifecycle interaction and limits interpretation.
7. **Payload materialization remains charged to proof extraction.** `RangeProof` still owns concrete leaf payload `bytes`; verification still hashes those payloads and joins them. A verifier-owner result would not establish that the final native design should preserve these Python objects.
8. **No storage/I/O authority.** File reads, page cache, persistent sidecar placement, proof coordinate encoding, RSS, crash recovery, remote access and failure isolation remain outside scope.

## Frozen interpretation

- `OWNER_AUTH_VERIFY`: verification reaches >=60% of stage-sum wall and CPU on >=12/16 rows in both pipelines. Stop proof micro-polishing; target verifier hashing/control/materialization next.
- `OWNER_PROOF_EXTRACT`: proof extraction reaches the same threshold in both pipelines. Continue at the proof boundary with a causally different design.
- `DISTRIBUTED_AUTH_SELECTIVE_OPEN`: neither stage owns broadly enough; optimize a fused boundary or move to integrated I/O evidence rather than local micro-tuning.
- `INVALIDATE_AUTH_SELECTIVE_OPEN_STAGE_OWNER`: semantics or matrix contract failed.
