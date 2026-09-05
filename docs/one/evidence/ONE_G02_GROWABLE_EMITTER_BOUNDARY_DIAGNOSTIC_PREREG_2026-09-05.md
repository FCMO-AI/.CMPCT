# ONE-G0.2 growable emitter boundary diagnostic — preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`
Parent gate result: `docs/one/evidence/ONE_G02_GROWABLE_DIRECT_CANONICAL_EMITTER_RESULT_2026-09-05.md`

## Mission Lock / Referee

The growable-direct canonical emitter failed its absolute promotion gate because one row, 256 KiB `shift_plus1`, measured 2.752696x baseline. This is not negotiable. However 20/21 productive rows improved, all control size medians improved, the same exact-shift case was 0.558059x at 128 KiB, and the other 256 KiB Programs measured 0.354544x–0.731095x. The isolated discontinuity must therefore be diagnosed before either promoting or broadly retiring the underlying direct-write mechanism.

## Falsifiable hypotheses

H1 — **runtime growth boundary:** a reproducible Python `bytearray` growth/reallocation transition near the 256 KiB exact-shift wire shape causes the direct emitter to lose abruptly while smaller/larger or control-dense Programs do not.

H2 — **runner/timing outlier:** the 2.75x row does not reproduce under a denser boundary sweep and repeated paired trials; the mechanism is broadly fast and the parent gate failure remains a real failed run but not a stable mechanism-level regression.

H3 — **unexplained direct-write instability:** losses recur without a stable size/growth boundary or affect multiple neighboring sizes unpredictably. In that case the direct emitter family is not stable enough for promotion and should remain retired pending a native or fundamentally different implementation.

## Frozen diagnostic envelope

Build the exact same three-node `shift_plus1` Program shape used by the parent benchmark, plus the two-node literal control, at these target sizes in bytes:

`98304, 131072, 163840, 196608, 229376, 245760, 253952, 258048, 262144, 266240, 270336, 294912, 327680`.

For each shape/size:

- validate canonical byte equality and `WireStats` equality;
- ordinary decode/reconstruction exactness;
- 101 paired alternating A/B-B/A emission rounds;
- record canonical wire bytes, Surprise bytes, baseline median ns, direct median ns and ratio.

Also isolate the dominant blob append operation using the same payload length and output-prefix shape, comparing baseline helper-style temporary blob construction + append against direct uvarint append + `bytearray.extend`. This micro-stage is diagnostic only; it cannot promote the full emitter.

## Decision law

This is a diagnostic, not a promotion gate.

- `confirm_growth_boundary` only if the full-emitter slowdown >=1.20x reproduces in at least two neighboring sizes and the isolated blob-append ratio shows a corresponding local slowdown pattern.
- `classify_parent_outlier_nonrepeatable` only if **all** swept full-emitter rows are <=1.03x and the isolated blob stage has no >=1.20x local slowdown. This does not retroactively pass the parent gate; it authorizes an exact repeatability run of the unchanged parent gate.
- otherwise `hold_direct_emitter_instability` and keep the family retired.

No threshold dispatcher may be derived from this diagnostic. The purpose is causal attribution and repeatability, not corpus fitting.

## Claim boundary

Python runtime diagnostic only. No format, reader, stored-byte, product-speed, integrity/recovery, or comparator authority.