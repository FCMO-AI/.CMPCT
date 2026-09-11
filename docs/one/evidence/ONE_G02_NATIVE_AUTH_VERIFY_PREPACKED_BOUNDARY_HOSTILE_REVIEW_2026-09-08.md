# ONE-G0.2 prepacked native verifier boundary — hostile review

**Date:** 2026-09-08  
**Status:** pre-result hostile review  
**Branch:** `research/cmpct1`

## Referee question

Can the prior `HOLD_NATIVE_AUTH_VERIFY` be causally attributed to repeated Python-to-ctypes proof marshalling, or is the native interval verifier itself insufficiently competitive?

## Strongest attacks

### 1. Prepacking is not free

The candidate deliberately moves payload joining/copying, sibling-array construction and expected-root copying outside the hot verification call. That is **not** a product-latency claim. The experiment is admissible only as a decomposition of the already-measured charged wrapper.

A pass therefore requires a follow-up where packed proof extraction and verification share one charged boundary. The project may not report the prepacked number as end-to-end selective-open latency.

### 2. The prepared object duplicates proof state

`PreparedNativeRangeProof` retains both Python-level metadata and native ctypes buffers. It can use more memory than either final design should. This experiment does not measure RSS and may not claim a memory improvement. A promoted fused implementation must avoid dual materialization rather than institutionalize it.

### 3. Boundary savings could be output-limited

The prepacked call still allocates an output ctypes buffer and converts it to Python bytes. Large 64 KiB reads may therefore remain limited by output copying even if proof marshalling is removed. That is useful: a failure on those rows means the next boundary needs to include output/view semantics, not simply more native hashing.

### 4. Native scratch allocation remains charged

The C verifier still `malloc/free`s scratch buffers per call. This is intentionally retained. Reusable scratch may be a future experiment, but moving it outside the timer after observing the result would contaminate this causal test.

### 5. Three-arm timing drift

The benchmark rotates Python control, charged native, and prepacked native order every repetition rather than timing one complete arm before another. Previous result objects are cleared before clocks start. This limits systematic warmup/drift attribution.

### 6. Exact matrix identity

The adjudicator validates the exact 16 `(leaf,start,length)` cells, not only row count, before any `all`/count performance rule. Missing or duplicated cells invalidate.

### 7. Integrity may not be traded

The candidate uses the exact same C hash grammar and exact same proof elements as the charged native verifier. Unit coverage independently checks payload, sibling and root tampering. Any semantic or hostile failure invalidates regardless of speed.

### 8. Coarse leaves are the key falsifier

The 192-byte-leaf family caused the prior HOLD and must remain in the matrix. It may not be removed, down-weighted, or hidden behind a leaf-size dispatcher merely to promote native verification.

## Review verdict

The experiment is admissible **only as a causal boundary decomposition**. The thresholds remain frozen as preregistered. A green result establishes that repeated Python/native proof marshalling is a material owner and justifies a fused packed proof→native selective-open experiment. It does not establish a final proof format, persistent-index density solution, portability authority, or end-to-end product win.

A HOLD is equally useful: if stable prepacked buffers cannot clear the hard control gate, further wrapper work should stop and authentication research should move back to the representation/work model rather than polishing ctypes.
