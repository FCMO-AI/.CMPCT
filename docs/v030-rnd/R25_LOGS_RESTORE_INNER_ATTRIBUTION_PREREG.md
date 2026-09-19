# Logs authenticated-restore inner attribution — preregistration

Status: **FROZEN FORGE D2 FOLLOW-UP / NO RELEASE CREDIT**

## Predecessor fact

`R25_LOGS_FUSED_PHASE_ATTRIBUTION_RESULT.md` measured the promoted one-session fused extractor and found authenticated logical restore (`Archive._restore_session`) at **26.265 ms / 82.8%** of the instrumented extraction median. Manifest decode and filesystem metadata were both below 1% and are retired as primary explanations under that regime.

This follow-up asks which directly observable sub-boundary inside authenticated restore owns the next millisecond-scale intervention opportunity.

## Frozen target and semantic owner

- target: deterministic `neutral_hostile_v1/05_logs_and_telemetry`;
- exact promoted fused extractor and `logs-inverse` archive bytes;
- semantic owner: `experiments.entropygraph_v030_logs_inverse_profile_v2.Archive._restore_session` as inherited by canonical v3;
- exact source tree required on every extraction;
- no production source, archive bytes, locality, integrity, recovery or release threshold changes.

## Frozen tracked boundaries

Instrument only existing functions and immediately delegate to their originals:

1. `Archive._read_pack` — authenticated physical pack seek/read, Zstd decompression where applicable, CRC32 and pack SHA-256 verification. Because `_restore_session` calls `_read_pack` only on a pack-cache miss, this measures unique pack materialization in the one-session fused operation.
2. `BASE._decode` — inverse-edge reconstruction (gzip/Zstd sidecar inverse decode) after the source logical member is available.

The remainder inside the predecessor 26.265 ms restore boundary is **not free**. It includes member-cache bookkeeping, recursive dispatch, slicing/copying pack members, per-logical-member SHA-256 identity hashing and Python overhead. This follow-up reports an explicit predecessor-scale remainder rather than assigning it to an unmeasured cause.

## Frozen execution

- one untimed warm-up per arm;
- **11 paired rounds**, alternating control-first/instrumented-first;
- control is exact uninstrumented fused extraction;
- instrumented arm wraps only `_read_pack` and `BASE._decode`;
- `gc.collect()` before each timed extraction;
- exact source tree after every extraction;
- the same archive/SHA/selected representation in all rounds.

Instrumentation is valid only when instrumented median total / control median total is `<=1.10x`.

## Frozen material-headroom rule

A tracked sub-boundary is material only if its median is both:

- `>=0.0020 s`; and
- `>=5%` of instrumented total extraction wall.

The 2 ms absolute floor is unchanged from the predecessor and matches the scale of the remaining strict Logs row deficit on the latest substantive complete-product receipt. Crossing it authorizes only the next narrow A/B; it does not authorize skipping integrity work.

Terminal decisions:

- invalid exactness/selection/instrumentation overhead -> **`INVALID_RESTORE_INNER_ATTRIBUTION`**;
- `_read_pack` material -> include **`PACK_MATERIALIZATION_HEADROOM`**;
- inverse decode material -> include **`INVERSE_DECODE_HEADROOM`**;
- neither material -> **`TRACKED_RESTORE_SUBBOUNDARIES_INSUFFICIENT`**.

If both are material, both are preserved; the larger median is the next lowest-radicality Forge priority. If neither is material, the next attribution must move to per-logical identity hashing/copy/cache overhead rather than polishing these two boundaries.

## Safety and release law

No hashing, CRC, authentication, inverse reconstruction, locality accounting or transactional publication may be disabled to obtain speed. This diagnostic grants **zero release credit**. A future optimization must preserve exact archive bytes/tree, hostile corruption rejection and all existing runtime/release gates.
