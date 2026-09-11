# ONE-G0.2 exact-root native authentication-tree creation profile

**Experimental line:** `ONE-G0.2`  
**Result-bearing source:** `b52c18c279b7cae04f035cc92501efcb9e3dd426`  
**Workflow:** `33952580540`  
**Job:** `101269999855`  
**Artifact:** `9965320426`  
**Artifact digest:** `sha256:5f5840102a3962152e68b297c5e10376bfb476066b5f79b1813ede6a6c13a52e`  
**Decision:** `native_creation_debt_survives_but_requires_end_to_end_miy`

## Question

The hosted Python creation audit measured 17–39x elapsed versus one whole-root SHA-256 and thousands of exact hash nodes for the shared-graph passing leaves. That result mixed structural hash work with Python object/interpreter overhead. This experiment removes that ambiguity.

A committed C/OpenSSL implementation reproduces the **exact existing ONE research tree grammar**: identical leaf domains and metadata, identical binary parents, identical root commitment. The Python evaluator independently computes the expected root before any timing result is accepted.

Frozen cases are 64 KiB and 256 KiB deterministic roots at the four shared-graph passing leaves: 80, 96, 112 and 192 bytes. Each case uses 31 repetitions and compares complete exact-tree construction against one OpenSSL SHA-256 over the same source bytes.

## Result

All **8/8 native roots matched the independent Python implementation exactly**. The hosted-reference 17–39x slowdown largely disappears in native code:

| Root | Leaf | Tree median | Whole SHA median | Ratio |
|---:|---:|---:|---:|---:|
| 64 KiB | 80 B | 199.824 us | 41.228 us | 4.847x |
| 64 KiB | 96 B | 166.071 us | 41.257 us | 4.025x |
| 64 KiB | **112 B** | **168.896 us** | **41.247 us** | **4.095x** |
| 64 KiB | 192 B | 110.437 us | 41.237 us | 2.678x |
| 256 KiB | 80 B | 835.543 us | 164.768 us | 5.071x |
| 256 KiB | 96 B | 673.641 us | 164.147 us | 4.104x |
| 256 KiB | **112 B** | **691.855 us** | **164.708 us** | **4.200x** |
| 256 KiB | 192 B | 454.149 us | 164.177 us | 2.766x |

The preregistered catastrophic-blocker criterion (>10x on the balanced 112-byte point at both sizes) is therefore **falsified**. The stronger all-cases <=5x falsifier narrowly misses because the 256 KiB / 80-byte case is 5.071x.

## Interpretation

Creation hashing remains a real cost—especially because a normal whole-root digest is only one pass—but it is now an engineering debt rather than evidence that the representation is computationally hopeless. The balanced 112-byte point costs about **4.1–4.2x a single SHA pass** in this exact hosted x86-64 native microprofile while retaining the pair experiment's complete-byte and selective-access gains.

The structural work accounting from the prior audit still matters: the 112-byte point performs 1,178 SHA calls at 64 KiB and 4,690 at 256 KiB, presenting about 1.86x source bytes to SHA-256. The gap between ~1.86x input traffic and ~4.2x elapsed identifies per-node initialization/finalization and tiny-message overhead as an optimization target. Level batching or multi-buffer SHA can attack that overhead without changing a single authenticated byte.

## Strongest self-critique

This is a microprofile, not end-to-end creation throughput. It excludes Law discovery, Surprise construction, manifest writing, allocation policy, persistent I/O and concurrency with the fused observation pass. It also uses hosted x86-64 OpenSSL rather than the eventual portable/native ONE implementation. Product promotion still requires marginal-information-yield accounting across the complete creator.

## Decision

Preserve the authenticated stored-graph gain and advance to end-to-end MIY/native batching work. Do not coarsen leaves merely to make the hash microbenchmark prettier; any speed Builder must retain byte-identical roots/proofs and the measured density/access result.
