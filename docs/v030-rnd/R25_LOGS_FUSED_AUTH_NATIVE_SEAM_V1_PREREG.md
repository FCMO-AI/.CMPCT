# r25 Logs fused CRC32 + SHA-256 native seam v1 — frozen preregistration

Status: **FROZEN FORGE R2/R3 CAUSAL A/B / ZERO PRODUCT OR RELEASE CREDIT**

## Why this family is reopened

`R25_LOGS_NATIVE_FFI_READER_V1_RESULT.md` retired the historical whole-reader Rust FFI because it was slower than Python. Its reopening predicate explicitly permits a narrower native seam that does not reproduce the v1 whole-reader work. Subsequent exact-head pack attribution identified CRC32 and SHA-256 as separate mandatory authenticated-pack costs consuming about 6.33% and 14.94% of complete Logs extraction respectively, while the last cited release-runtime gap required only about 3.87% total extraction reduction. The current Python shipping-candidate extraction already shares member and pack caches across a complete operation, so operation-cache ownership is not the next shipping intervention.

The causal question is therefore narrow: can both mandatory pack identities be established through one native call over cache-sized chunks, preserving the exact CRC32 and SHA-256 facts, cheaply enough to reduce complete Logs extraction wall time?

## Frozen target

- corpus: `neutral_hostile_v1/05_logs_and_telemetry`
- archive producer and selected representation: current exact-head promoted Logs product candidate; selection must be `logs-inverse`
- product archive bytes, grammar, selector, recovery, locality, decode-unit limits and extraction semantics: unchanged
- operations: complete authenticated extraction only
- paired rounds: 11 after one untimed warm-up per arm
- order: alternating baseline/candidate within every pair
- native library load/build: outside timed region

## Arms

### Baseline

Unmodified promoted Python Logs extraction, including ordinary `_read_pack` authentication:

1. exact seek/read;
2. raw or bounded Zstd materialization;
3. full CRC32 over decoded pack;
4. full SHA-256 over decoded pack;
5. exact size/CRC/SHA comparison;
6. unchanged downstream logical-member SHA-256 and filesystem identity checks.

### Candidate

Only the two decoded-pack authentication calls in `_read_pack` are replaced by one research-only native FFI call. That call must consume every decoded byte and return both the CRC32 and the 32-byte SHA-256 digest. Zstd materialization, size checks, expected-value comparison, downstream logical-member SHA-256, archive bytes, filesystem checks and transactional publication remain unchanged.

The native helper may process the input in bounded cache-sized chunks and update both independent hash states for each chunk. It may not omit either algorithm, truncate either digest, trust metadata, reuse authentication across independent extraction operations, or receive precomputed expected identities.

## Validity

Every arm and round must:

- reconstruct the exact source tree;
- use the exact same archive bytes and SHA-256;
- execute the same number of authenticated pack reads;
- establish both CRC32 and SHA-256 for every decoded pack;
- reject a deterministic payload corruption that causes pack identity failure;
- keep the native library load outside timing;
- preserve no product source changes.

The helper must additionally match Python `binascii.crc32` and `hashlib.sha256` on deterministic zero-length, short, 64 KiB-boundary and multi-MiB buffers before timing.

Any validity failure => `INVALID_FUSED_AUTH_NATIVE_SEAM` and zero performance credit.

## Frozen decision law

Let `baseline_median` and `candidate_median` be complete-extraction paired medians.

Promotion signal requires **both**:

- candidate median <= 0.95 * baseline median (>=5% complete-extraction improvement), and
- baseline median - candidate median >= 0.001 s (>=1 ms absolute saving).

Decisions:

- valid + both thresholds pass => `FUSED_AUTH_NATIVE_SEAM_HEADROOM_SUPPORTED`
- valid + either threshold fails => `FUSED_AUTH_NATIVE_SEAM_HEADROOM_NOT_SUPPORTED`
- invalid => `INVALID_FUSED_AUTH_NATIVE_SEAM`

A positive result authorizes only a Builder prerequisite/productization review of this narrow seam. It grants no release credit. A negative result retires this exact fused-auth FFI family for the tested hosted-runner Logs regime unless implementation or attribution materially changes.

## Carrying cost / hostile review

This seam adds an FFI/native portability dependency, so a marginal micro-win is deliberately insufficient. Productization must still prove native/platform availability or a safe semantically identical fallback, hostile-input behavior, fuzz coverage and current-fingerprint runtime authority. Integrity remains non-borrowable debt.
