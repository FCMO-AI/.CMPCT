# ONE-G0.2 native authenticated verifier — hostile review

Date: 2026-09-08
Status: pre-result review; thresholds frozen in preregistration.

## Mission / evidence trigger

Exact-source stage-owner run `34247338432` at `b70f592f440b7ffe0a1fa28cfc858d8da8b964ca` returned `OWNER_AUTH_VERIFY`. Verification owns the majority of measured selective-open stage time in both the generic reference and packed-interval pipelines, so the next speed experiment attacks verification rather than continuing proof extraction.

## Strongest attacks

### 1. Native speed must not buy weaker integrity

The candidate hashes the same domain-separated leaf messages, parent messages with identical level numbering, and final root commitment. It consumes the existing `RangeProof`; no proof hash is omitted and no stored/proof byte count is changed. Exact output and root agreement are required before timing.

Tampered payload, sibling digest and expected root must all fail. Malformed sibling geometry/order must fail closed. Any failure invalidates regardless of speed.

### 2. Contiguous-interval arithmetic is only valid because RangeProof payload leaves are contiguous

The candidate does not attempt to generalize to arbitrary sparse leaf sets. `RangeProof` is generated for one byte range and therefore carries one contiguous leaf interval. Each ancestor set remains a contiguous interval, so only an optional left and optional right sibling can be external at a level. The verifier checks exact expected sibling coordinates/order and rejects extras or omissions.

If future proof grammar allows arbitrary sparse multi-ranges, this kernel is not automatically authoritative for that grammar.

### 3. Marshalling is charged

The candidate accepts the existing Python `RangeProof`, joins its payload tuple, validates/splits sibling triples and crosses ctypes inside the timed verifier call. These costs are not hidden as setup. A green result therefore has to overcome the current real Python/native boundary rather than benchmark a bare C inner loop.

This also makes the test conservative relative to a future packed proof representation that could avoid rebuilding ctypes arrays.

### 4. OpenSSL is research machinery, not a format dependency

The kernel uses system libcrypto to reproduce SHA-256 exactly. A green result proves a native/batched implementation opportunity; it does not canonize OpenSSL or satisfy portability. Promotion beyond research requires a controlled portable backend or project-owned implementation strategy with the same vectors.

### 5. malloc/free occur inside native verification

The first candidate allocates two scratch digest buffers per call. This is deliberately charged. If the result is only marginal, do not hide allocator cost by moving it outside the boundary after seeing the result. A later reusable-scratch experiment would need separate preregistration and concurrency/resource semantics.

### 6. Decision law attacks

The benchmark requires the exact 16-row identity, not only cardinality. Any semantic/hostile failure invalidates. Every row must stay at or below 0.65x wall and CPU, and at least 12/16 must reach 0.50x on both. Synthetic tests cover 0.651 boundary failures, insufficient material rows, missing rows and duplicate-replaces-missing attacks.

### 7. Claim boundary remains narrow

The experiment does not measure tree creation, filesystem I/O, sidecar placement, persistent authentication-index density, peak RSS, process startup or full product selective-open. It does not solve the known density/locality tension of a reconstructed-output hash tree. It only asks whether exact verification of the current proof grammar should remain a Python object/dict algorithm.

## Pre-result judgment

The experiment is admissible. Its strongest risk is not semantic but economic: for large 64 KiB reads, SHA-256 over payload bytes may dominate enough that Python control removal cannot meet the 2x-majority gate. If that happens, preserve the negative and move toward a fused packed-proof/native-open boundary or a different authenticated representation rather than weakening thresholds.
