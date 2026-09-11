# ONE-G0.2 — Generic relation timing attribution: paired timing rehabilitates gate, FFI does not explain native residual

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Status:** immutable causal evidence; independent timing retired as a sufficient basis for the old transfer loss, Python/ctypes overhead retired as dominant native residual owner

## Mission Lock

The arbitrary-relation transfer preserved classification/proof signatures but exceeded the frozen <=1.10x 32/64 KiB compute ceiling under independently sampled medians. Pointer rebasing recovered substantial cost, while direct-pointer and spatial-locality diagnostics retired carrier API and physical stream distance as dominant residual owners. Two further frozen discriminators tested measurement shape before changing the algorithm.

## 1. Paired direct-pointer versus compact-half A/B

**Result-bearing source:** `2dfaef53931d6a7a014e050d4d7675f3bf923983`

- workflow: `33962590957`
- job: `101296953643`
- artifact: `9968430529`
- artifact zip SHA-256: `40fabad4f4bb6ae526724cf03e0535973ba97f8a0316324daf1f346a5478def1`
- `tests/one`: **76 passed**
- decision: `paired_timing_closes_transfer_gap`
- all result structs: exact

Paired ABBA timing brought every frozen row inside the existing **<=1.10x** transfer ceiling without changing semantics or the threshold:

| relation | case | direct / half |
|---:|---|---:|
| 32 KiB | shift +1 | 1.0739x |
| 32 KiB | quarter-damaged +1 | 1.0956x |
| 32 KiB | every96 positive | 1.0739x |
| 32 KiB | every32 false control | 1.0680x |
| 32 KiB | independent random | 1.0888x |
| 64 KiB | shift +1 | 1.0693x |
| 64 KiB | quarter-damaged +1 | 1.0631x |
| 64 KiB | every96 positive | 1.0657x |
| 64 KiB | every32 false control | 1.0700x |
| 64 KiB | independent random | 1.0551x |

This is a real rehabilitation of the **measurement result**, not a product-speed claim: the old independently timed ~1.11-1.22x residual was materially contaminated by measurement / runner-frequency ordering effects. A remaining ~5.5-9.6% paired residual still required attribution.

## 2. Native-internal A/B removes Python/ctypes from the timed loop

**Result-bearing source:** `b7cef202ec49e280b8ecdb80ba40764399e8cb81`

- workflow: `33962778531`
- job: `101297464977`
- artifact: `9968456359`
- artifact zip SHA-256: `b07d95e17031314b833af04e76ff9a1c1caa99151edb30551be8102abf96d176`
- `tests/one`: **76 passed**
- decision: `ffi_timing_not_dominant_residual_owner`
- all result structs: exact

The C harness executed ABBA batches internally (`64` calls per batch, `101` rounds), amortizing Python FFI and clock overhead. If FFI/timing call shape owned the residual, the frozen gate required native direct/half <=1.05 and <=50% of same-run Python-paired excess on every row. It failed decisively.

Native direct / compact-half ratios:

- 32 KiB: **1.1344x–1.1862x**
- 64 KiB: **1.1280x–1.1423x**

The native excess was generally **82%-117%** of the same-run Python-paired excess, not <=50%. Thus removing FFI did not collapse the residual; on several rows the native ratio was larger.

## Causal interpretation

Three measurement layers now separate cleanly:

1. **Independent median timing was materially misleading.** Paired ordering is required for these microsecond kernels and is retained as research-instrument law.
2. **Python/ctypes call overhead is not the remaining C-kernel owner.** Removing it did not approach parity.
3. The residual therefore lives in the compiled C paths themselves. Since the generic direct path presents separate source and target pointers while mutating an output object, the next lowest-sufficient discriminator is compiler alias analysis, followed by instruction/loop-shape inspection if alias guarantees are insufficient.

No representation change follows from this evidence. The writer-side generic relation remains semantically transferable; only its discovery implementation cost is under rehabilitation.

## Claim boundary

Writer-side causal compute attribution only. No ONE reader-visible operation, stored-byte result, density claim, product creation/decode speed claim, v0.29/v0.30 comparison or release authority changes.
