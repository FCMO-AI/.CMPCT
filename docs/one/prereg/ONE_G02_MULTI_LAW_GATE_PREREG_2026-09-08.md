# ONE-G0.2 — fused multi-Law opportunity gate preregistration

**Status:** frozen before result-bearing hosted evidence  
**Date:** 2026-09-08  
**Branch:** `research/cmpct1`  
**Experimental version:** `ONE-G0.2`

## Mission lock / referee

Reader execution is no longer the highest-uncertainty boundary: the generic prepared execution control plane and native arithmetic bulk path have already produced exact, reproducible reader-side gains. The next Engineering Grid debt is writer discovery economics: ONE must discover useful Law without recreating a portfolio of expensive independent scanners.

The current fused observer already collects run and exact-reuse evidence in one forward source pass. The repository also contains bounded relation-band and morphology-gate work. This experiment asks whether one small additional feature set can nominate four generic ONE Law families — run/fill, exact reuse/repetition, add8-like arithmetic progression, and xor/resemblance relation — without another source scan and without carrying an unbounded discovery index.

No reader-visible operation, wire format, canonical version, or reconstruction semantic changes in this experiment.

## Falsifiable hypothesis

A single forward pass can provide sufficiently selective evidence to launch deeper exact search for the four tested generic Law families while:

1. missing **zero** required positive families on a generator-distinct frozen matrix;
2. producing at most **one total nomination** across the negative-control rows;
3. charging exactly **1.0x source scan bytes** on every row;
4. retaining at most **15% of input bytes** as modeled feature payload even at the smallest 64 KiB scale.

This first gate is intentionally about semantic recall/selectivity/resource shape. Python timing is retained but is **not** a promotion criterion because a Python byte loop cannot establish native carrying economics. A green result earns a separate native fused-cost/MIY experiment; it does not establish production-speed authority.

## Candidate

`experiments/one/multi_law_gate.py` performs one forward byte pass and maintains only bounded discovery state:

- run length/value state;
- aligned 64-byte FNV64 fingerprints, retaining at most 256 first-source entries;
- a 256-bin modulo-256 first-difference histogram;
- a 256-bin xor histogram at fixed lag 64;
- a 64-byte lag ring.

The gate emits only nominations. A repeated fingerprint is not exact-reuse authority; downstream exact proof remains mandatory. Arithmetic and xor nominations require at least 256 relation pairs and >=87.5% support. Dominant delta `0` and xor `0` do not launch separate arithmetic/xor search because those structures are already ordinary repeat/fill/reuse evidence.

## Frozen matrix

Sizes:

- 64 KiB
- 256 KiB
- 1 MiB

Families:

- `long_runs`
- `exact_repeat`
- `add8_ramp`
- `xor_chain`
- `mixed_structured`
- `random`
- `compressed_like`
- `false_pattern`

Total: **24 exact cells**, **9 repetitions** each for hosted timing telemetry.

Independent expected-family oracle:

- `long_runs`: run + reuse
- `exact_repeat`: reuse
- `add8_ramp`: reuse + add8
- `xor_chain`: reuse + xor
- `mixed_structured`: run + reuse
- negative controls: no required nomination

The family name is never supplied to the gate.

## Frozen adjudication

`INVALIDATE_MULTI_LAW_GATE` if:

- the 24-cell matrix is incomplete or contains a duplicate cell; or
- any row reports source-scan ratio other than exactly 1.0.

`HOLD_MULTI_LAW_GATE` if semantics/accounting are valid but any of the following occurs:

- any required positive nomination is missed;
- negative controls collectively receive more than one nomination;
- retained feature payload exceeds 15% of input on any row.

`ADVANCE_MULTI_LAW_GATE` only if all frozen gates pass.

## Claim boundary / next action

ADVANCE means only that the feature set is a credible one-pass opportunity gate. The next experiment must integrate the same signals into the native fused observer and charge actual elapsed/CPU cost, memory/RSS where practical, exact downstream proof cost, bytes eliminated, and `bytes_saved / extra_cpu_second` or equivalent MIY. It must retain incompressible/already-compressed/false-pattern controls.

HOLD means reform the feature mechanism, not the benchmark. INVALIDATE means repair semantics/accounting before accepting performance evidence.
