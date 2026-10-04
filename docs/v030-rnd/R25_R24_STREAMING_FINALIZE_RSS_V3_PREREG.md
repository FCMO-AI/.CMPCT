# r24 streaming-finalize RSS v3 preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / FORGE D2→R1 / NO RELEASE CREDIT**

Supersedes no prior evidence. `R25_R24_STREAMING_FINALIZE_RSS_V2_RESULT.md` remains immutable and terminal for its exact implementation: the semantic-owner v2 reduced Shifted complete-product incremental peak RSS to `0.7546867932x` shipping while improving wall time, but missed the frozen `<=0.75x` promotion boundary. V3 tests one narrower ownership change rather than rerunning v2 or changing its threshold.

## Question

After the streaming finalizer has captured immutable record ingredients for one r24 candidate and released that candidate's raw/Deflate payload, does retaining the now-consumed `Candidate` shell in `Builder.cands` contribute enough residual process high-water to explain the remaining Shifted miss?

The candidate shell contains only bookkeeping after record emission; finished archive construction later resolves file/recipe references through the independent `href` hash→record map. V3 therefore tests immediate removal of consumed candidate objects from `Builder.cands` after their record ingredients are captured. It does **not** change codec competition, record order, bytes, hashes, dictionary policy, worker count, spool size, archive grammar or publication.

## Exact intervention

One reusable semantic-owner module exposes two classes sharing one implementation:

1. **control** — v2 behavior: after encoding, set `candidate.raw = b""` and clear `candidate.deflates`, but retain the consumed candidate shell in `Builder.cands` until the builder dies;
2. **evict** — identical code path plus `Builder.cands.pop(hash)` immediately after immutable record ingredients have been captured and raw/Deflate state cleared.

The evict arm may not change:

- `SPOOL_MEMORY_BYTES = 1,048,576`;
- `MAX_IN_FLIGHT_FACTOR = 1`;
- shipping r24 encoder policy or worker count;
- sorted content-hash record order;
- codec selection/compression levels;
- dictionary training or bytes;
- CRC/SHA calculation;
- r24 grammar/index semantics;
- r25 candidate construction or selector/admission rules;
- strong verification, locality/decode-unit, integrity/recovery or release thresholds.

No garbage-collector forcing, allocator trimming, subprocess isolation, scheduler serialization or benchmark-specific branch is allowed.

## Corpus and measurement

Use exactly the v2 frozen corpus/identity contract:

- `resemblance_hostile_v1 / 01_shifted_versions`;
- `neutral_hostile_v1 / 09_ml_artifacts`.

For each arm and operation, regenerate the accepted repaired source, assert its accepted historical identity, run in a fresh Python process and strongly verify output.

Operations:

- genuine shipping-r24 operation;
- complete promoted-product operation.

Arms:

- shipping mature Builder;
- streaming control;
- streaming consumed-candidate eviction.

Use two repetitions with order reversal/rotation sufficient to avoid one fixed arm always receiving the same runner position. `ru_maxrss` total operation high-water is authoritative; baseline-subtracted high-water is the frozen ratio metric for continuity with v2. Wall time remains charged and visible.

Every streaming control/evict repetition must emit byte-identical r24 and complete-product artifacts relative to shipping for the same source: archive bytes, physical SHA-256 and logical tree SHA-256 must all match. Any mismatch invalidates the experiment and forbids interpretation.

## Frozen decision bands

### Productization signal

`promotion_signal=true` only if the **evict** arm satisfies the entire inherited v2 conjunction:

1. exact output identity on every arm/repetition;
2. no complete-product wall-time ratio above `1.05x` versus shipping on either target;
3. Shifted complete-product incremental-RSS ratio versus shipping `<=0.75x`;
4. Shifted genuine-r24 incremental-RSS ratio versus shipping `<=0.50x`.

The `0.75x` boundary is unchanged. A value above it is a miss even if close.

### Causal shell-ownership decision

On Shifted complete-product incremental peak RSS, compare **evict vs streaming-control in the same v3 run**:

- `<=0.98x` (>=2% reduction) with exact identity and no >5% wall regression: **CANDIDATE_SHELL_RETENTION_SUPPORTED**;
- `>=0.99x` (<1% reduction): **CANDIDATE_SHELL_RETENTION_RETIRED_AS_MATERIAL_OWNER**;
- `(0.98, 0.99)`: **AMBIGUOUS_SMALL_EFFECT**.

If the shell effect is supported but the inherited productization conjunction still fails, preserve the measured gain and continue same-family lifetime attribution; do not promote.

If eviction worsens Shifted wall time by >5% or causes any output/verification mismatch, it is not a productization candidate regardless of RSS.

## Interpretation limits

A positive result proves only that retaining already-consumed r24 candidate bookkeeping materially contributes to the measured complete-product high-water under this exact regime. It does not prove that all Python object retention is costly or that r25 candidate objects share the same ownership pattern.

A negative result retires only **consumed r24 Candidate shell retention** as the remaining material owner. It does not weaken the v2 evidence for raw/encoded lifetime streaming, which remains a separate measured mechanism.

This diagnostic grants **no release credit**. Any production adoption must still regenerate exact-fingerprint runtime/RSS, full parity, correctness, native/platform and strict release authority.
