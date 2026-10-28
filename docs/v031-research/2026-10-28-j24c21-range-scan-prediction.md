# J24C21 pre-result structural work bound (not a product benchmark)

**Source/experiment:** [preregistration](2026-10-28-j24c21-large-owner-released-floor-prereg.md), exact unmerged sealed Reader #676 at `3b6a73f9205f40f11124cd9ff332407e52cebb93` and frozen published v0.30.0 at `main@80c358f8824ec1b20d349c92ed94c898090969b0`. This analytical note is a lower-rung derivation produced **before** evaluating any J24C21 hosted timing artifact. It changes neither source nor the frozen acceptance test.

## Mechanism and exact count formula

For fixed-size positive RAW owners of `u` bytes and a `read_range(start, length)` with `end=start+length`, the published Reader's S_CHUNKS path starts at the first ref and scans exactly `ceil(end/u)` references for a nonempty in-bounds request. The fused/sealed checkpoint path uses validated logical prefix at every 256th ref; it starts from `256*floor(floor(start/u)/256)` and scans `ceil(end/u) - 256*floor(floor(start/u)/256)` references. The query shapes (from the preregistered court) request 8,192 bytes each and use `start=5`, six fixed fractions `{0.001,0.19,0.39,0.59,0.79,0.97}` or 32 evenly spaced half-bin fractions. All these geometries have nonzero physical owner lengths, so the formulas apply exactly. This is *logical reference visits*, not decoded work, wall time or RSS.

| Fixture | Regime | Published ref visits | Indexed ref visits | Avoidable-visit ratio |
|---|---|---:|---:|---:|
| 65,536 × 1 B, two physical owners | Q1 early | 8,197 | 8,197 | 1.00× |
| 65,536 × 1 B, two physical owners | Q6 spread | 235,010 | 43,522 | 5.40× |
| 65,536 × 1 B, two physical owners | Q32 spread | 1,294,336 | 245,760 | 5.27× |
| 262,144 × 4 KiB, two physical owners | Q1 early | 3 | 3 | 1.00× |
| 262,144 × 4 KiB, two physical owners | Q6 spread | 768,359 | 615 | 1,249.36× |
| 262,144 × 4 KiB, two physical owners | Q32 spread | 4,194,368 | 64 | 65,537× |
| 8,192 × 4 KiB, 4,096 independently signed owners | Q1 early | 3 | 3 | 1.00× |
| 8,192 × 4 KiB, 4,096 independently signed owners | Q6 spread | 24,026 | 474 | 50.69× |
| 8,192 × 4 KiB, 4,096 independently signed owners | Q32 spread | 131,136 | 4,160 | 31.52× |

## What observations discriminate the hypotheses?

For Q1 early on large-owner profiles, **both** paths inspect only three chunk references; any systematic slowdown from the candidate is not due to additional per-query ref walks. Look to admission, freezing, native proof, wheel/runtime or other opening work. The original ABI3 scan necessarily still touches every ref at construction. Do not falsely credit the 1,249×/65,537× ratios as whole-Reader speedups: they describe a cheap suboperation only.

For Q6/Q32 on the 262k repeated-owner profile, over 99% of baseline ref visits can be avoided with checkpoints, yet the actual physical data likely comes from just two reused 4 KiB RAW owners. A weak full-session improvement would mean a different cost dominates (admission, Python dispatch, cache, return-byte transport or process). On the 8k/4,096-distinct-owner control, avoiding 98% of ref visits competes with many distinct 4KiB SHA-authenticated owners and their physical I/O/cache. A reversal there would narrow generality and protect against optimizing solely synthetic repeated-byte geometry.

**Counterfactual discriminator:** these formulas could have been computed before implementing any checkpoint architecture. They cannot prove a product win but can predict which session shapes should exhibit a causal search advantage and prevent indiscriminate aggregation of Q1 with Qmany. They are not evidence for on-disk compression, portability, adversarial source recovery, memory, general codecs or release promotion.

## Method validation / reproducibility

This derivation follows the exact loops in historical `src/cmpct/reader.py` and #676 `src/cmpct/reader.py`, with 256-stride prefix marks and `bisect_right`. No instrumentation, source patch, fixture regeneration per control or benchmark threshold modification. The J24C21 hosted court, if successful, must still establish byte identity and same-source installed economics independently; if it fails, report infra failure rather than treating this analytical ratio as a product result.
