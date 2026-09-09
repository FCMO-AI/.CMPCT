# ONE-G0.2 relation-cue redundancy analysis

**Date:** 2026-09-08  
**Status:** mechanism-level negative / writer-discovery redirect

## Why the current global relation cues should not be optimized further

The two hosted carrying-cost falsifiers established that continuously carrying the current add8/XOR nomination statistics is too expensive:

- full per-byte relation statistics: `HOLD_NATIVE_MULTI_LAW_CARRY`, median ~1.599x the common native run+reuse pass;
- stride-16 relation statistics: `HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY`, median ~1.515x overall and ~1.552x at 1 MiB.

A second, more fundamental problem emerged during hostile review: the original relation-positive generators do not establish **non-redundant** information beyond exact reuse.

### Constant-delta ramp

For byte sequence

`x[i] = a + d*i (mod 256)`

with non-zero byte delta `d`, the exact period is

`T = 256 / gcd(d, 256)`

and therefore `T <= 256` bytes. Because `T` divides 256 and aligned observer chunks are 64 bytes, aligned 64-byte chunks must repeat after at most `lcm(T,64) <= 256` bytes. Exhaustive verification over all 255 non-zero deltas found an aligned 64-byte duplicate by chunk index 1..4 in every case. Thus the existing long `add8_ramp` positive is necessarily also an exact-reuse positive.

### Fixed-mask lag-64 XOR chain

For

`B[n+1] = B[n] XOR mask`

with a fixed byte mask, XOR is its own inverse:

`B[n+2] = B[n]`.

The sequence therefore repeats exactly after 128 bytes (two 64-byte blocks), for every non-zero mask and every initial 64-byte block. Exhaustive verification across all 255 non-zero masks confirms the first aligned duplicate at block index 2 in every case. Thus the existing `xor_chain` positive is also necessarily an exact-reuse positive.

## Consequence

The promoted Python multi-Law gate remains valid evidence that these statistics are selective on the frozen matrix, but it is **not evidence that the add8/XOR cues add unique writer information**. Combined with their native carrying-cost HOLDs, this removes the justification for continued threshold/stride tuning of those global statistics.

The next relation-discovery target must prove novelty: it should detect relation structure in inputs where exact reuse, Fill/run structure, and cheaper already-promoted Laws do not explain the same bytes.

## Better causal target

A promising geometry is bounded parent-child block probing:

1. keep the full native run/reuse observation pass;
2. at coarse block boundaries, inspect a small fixed sample of the current and plausible parent block;
3. only if the sample is consistent with an existing generic ONE relation (for example add8 or XOR), run an exact full-block proof;
4. only exact-verified pairs may contribute Law support;
5. explicitly suppress candidates already explained by cheaper structure such as identical chunks or uniform Fill regions;
6. measure sampled candidates, exact proofs, false-positive proof work, writer wall/CPU, memory traffic, support bytes, and bytes eliminated per extra CPU second.

The decisive positives should use **unique random parent chunks followed once by transformed children**, so no aligned exact duplicate exists. Hostile controls should include sample traps that match every cheap probe position but fail the exact relation elsewhere.

## Pre-result hostile-review correction

Source `64ab5f7fab8736ce4bc4c0bfdf9b33629de75517` briefly introduced a draft block-relation falsifier but is **inadmissible** and was withdrawn before hosted evidence. Hostile review found that transitions between two long constant runs are themselves valid constant-add block relations. The draft would therefore have treated a true-but-redundant relation as a false positive against its `long_runs` control.

The corrected experiment must suppress relations already explained by Fill/run structure before it can be scientific authority. No hosted benchmark result from the withdrawn source may be used.

## Research stop / redirect

Stop fixed global add8/XOR histogram tuning. The next relation work must demonstrate all three together:

- **novelty:** relation support is not already captured by cheaper ONE Laws;
- **cheap falsification:** most bytes do not pay exact relation search;
- **economics:** downstream exact proof plus final Program construction improves marginal information yield, not merely nomination accuracy.
