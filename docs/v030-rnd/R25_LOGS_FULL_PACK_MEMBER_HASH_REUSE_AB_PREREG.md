# Logs full-pack member identity proof-reuse A/B — frozen preregistration

Status: **FROZEN R1 FORGE PREREGISTRATION / ZERO RELEASE CREDIT**

## Question

The promoted Logs full-operation restore authenticates every payload pack with both CRC32 and SHA-256 inside `_read_pack`, then `_restore_session` separately computes SHA-256 for every logical member. When a stored member is exactly the complete authenticated pack (`offset == 0`, `length == len(pack)`) and the member's expected SHA-256 is byte-identical to the authenticated pack SHA-256 declared in the pack header, the second SHA-256 pass proves no new fact: pack bytes and member bytes are the same byte string and both declarations demand the same digest.

Does reusing that already-established identity proof, only for this exact whole-pack case and only inside full-operation restore, recover enough complete Logs extraction wall time to materially close the current runtime red without weakening integrity, recovery, locality, cold selective-read semantics, archive bytes, or logical identity?

This is proof reuse, not authentication removal. CRC32 and SHA-256 pack authentication remain mandatory and unchanged.

## Frozen authority and target

- authoritative branch: `agent/v030-authoritative-integration`;
- target: `neutral_hostile_v1/05_logs_and_telemetry`;
- promoted representation must remain `logs-inverse`;
- control: exact promoted fused Logs full extraction;
- candidate: same full extraction with one narrowly scoped `_restore_session` rule: skip the logical-member SHA-256 recomputation only when all of the following are true:
  1. storage kind is `pack` or `raw`;
  2. the already-authenticated pack was materialized through unchanged `_read_pack`;
  3. member offset is exactly `0`;
  4. member length equals both declared logical size and `len(pack)`;
  5. the member's expected SHA-256 bytes equal the pack header's expected SHA-256 bytes for that exact pack.

All other logical members, including every derived member and every partial-pack slice, retain the inherited logical SHA-256 computation.

## Frozen non-borrowable facts

The candidate may not change or bypass:

- pack payload bounds or codec handling;
- complete pack CRC32 verification;
- complete pack SHA-256 verification;
- metadata SHA-256, primary/tail recovery, or fail-closed behavior;
- logical size checks;
- logical SHA-256 for derived members or partial-pack members;
- archive bytes, pack framing, selected representation, tree identity, inverse codecs, filesystem manifest semantics, locality/decode-unit bounds, or extraction destination safety;
- cold `read_member` selective-read semantics;
- any benchmark, runtime, recovery, integrity, or release threshold.

The candidate must not trust storage geometry alone. The pack header SHA and member SHA declarations must be exactly equal before proof reuse is permitted.

## Hostile proof-separation checks

Before timing interpretation, the instrument must demonstrate fail-closed behavior for the trust boundary:

1. normal candidate extraction strongly reconstructs the exact canonical user tree;
2. candidate reports at least one whole-pack logical SHA proof reuse on the frozen target;
3. a synthetic in-memory mismatch between the member expected SHA and authenticated pack-header SHA makes that member ineligible for proof reuse and causes the inherited logical SHA check to reject if the logical expected hash is wrong;
4. pack CRC32 and pack SHA-256 remain exercised by unchanged `_read_pack` for every unique pack touched in the full extraction;
5. the monkeypatch/subclass experiment restores the exact inherited class method after every measured arm.

A candidate that skips a member hash when pack/member expected SHA declarations differ is invalid regardless of speed.

## Measurement

- deterministic corpus from `benchmarks.neutral_hostile_corpus_v1.corpus_logs`;
- one promoted archive built once per experiment;
- one warm-up extraction per arm;
- **21 paired alternating rounds**;
- destination deleted before every extraction;
- `gc.collect()` before every timed arm;
- timed boundary is complete `RUNTIME.extract(archive, dst)`, including full authenticated restore and filesystem publication;
- canonical tree hash checked after every extraction;
- report medians and candidate/control wall ratio;
- record per-round proof-reuse count, ordinary logical-SHA count, pack-call count, and method-restoration state.

## Frozen decision bands

The latest substantive Logs product red requires only a few percent extraction recovery, so this R1 mechanism must clear a release-relevant hurdle rather than merely measure above noise.

- candidate complete-extraction reduction **>=4.0%** and candidate/control wall ratio **<=0.96x**, with every exactness/hostile/lifecycle gate passing -> `LOGS_FULL_PACK_MEMBER_HASH_REUSE_SUPPORTED`;
- reduction **<1.0%** -> `LOGS_FULL_PACK_MEMBER_HASH_REUSE_RETIRED`;
- reduction from **1.0% to <4.0%** -> `LOGS_FULL_PACK_MEMBER_HASH_REUSE_AMBIGUOUS`;
- any identity, hostile, lifecycle, pack-authentication, selection, or tree failure -> `INVALID_LOGS_FULL_PACK_MEMBER_HASH_REUSE_AB`.

The bands are immutable after result-bearing execution.

## Interpretation

A supported result would justify the smallest production intervention in the promoted full-operation reader: cache/reuse the already-established pack SHA identity only for exact whole-pack logical members, leaving selective reads and every other identity check untouched. It would still require normal product/runtime, recovery, fuzz, native/platform and final release authorities on the exact integrated fingerprint.

A retirement result means this exact duplicate logical SHA pass is not worth carrying for v0.30. Do not broaden the proof to partial packs, derived members, different hashes, or unauthenticated state after seeing the timing. The next Logs Forge step should return to the independently measured inverse-decode or authenticated-pack implementation owners.

No result from this experiment grants release credit by itself.