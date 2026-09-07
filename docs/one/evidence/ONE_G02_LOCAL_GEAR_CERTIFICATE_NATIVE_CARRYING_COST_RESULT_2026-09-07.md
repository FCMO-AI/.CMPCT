# ONE-G0.2 local Gear certificate native carrying-cost result — 2026-09-07

## Decision

**REJECT the present per-byte bottom-8 certificate carrying shape.**

This is the terminal result for the shape preregistered in `ONE_G02_LOCAL_GEAR_CERTIFICATE_NATIVE_CARRYING_COST_PREREG_2026-09-06.md`; it is not a rejection of content-local certification as a discovery principle.

## Exact authority

- branch: `research/cmpct1`
- evidence source: `56fc13f512266010bd0e61ae8ff509eb60770d9d`
- workflow: `ONE-G0.2 local Gear certificate native carrying cost`
- run: `34086475158`
- job: `101631372162`
- artifact: `10005400502`
- artifact zip SHA-256: `d74c578003798f4f1dbced1a1aa0c6cb01fbfd179e418ba56d823e3dde4f21a5`
- strict native build: PASS
- ONE semantic/hostile tests: **93 passed**
- workflow conclusion: failure because the final step correctly enforced the preregistered rejection.

## Measured result

Candidate / baseline elapsed ratios:

| row | ratio |
|---|---:|
| tiny 4 KiB shift+1 | 2.457307x |
| tiny 8 KiB fragmented96 | 2.625557x |
| mature 64 KiB shift+1 | 2.637271x |
| mature 256 KiB fragmented96 | 2.601851x |
| mature 256 KiB independent random | 4.079935x |
| mature 1 MiB independent random | 4.114829x |
| mature 1 MiB already-compressed-like | 4.085541x |
| mature 1 MiB repeated/versioned | 2.593823x |

Frozen aggregates:

- mature median: **3.358603x** (gate <=1.08x)
- fragmented mature median: **2.601851x** (gate <=1.10x)
- mature worst: **4.114829x** (gate <=1.15x)
- tiny median: **2.541432x** (gate <=1.15x)

The positive rows did produce exact certificate nominations. Independent-random and compressed-like controls produced zero exact nominations, so the rejection is performance-caused rather than a correctness or false-positive failure.

## Hostile review of the measurement

The candidate continues updating the target rolling certificate after its first exact nomination. That overcharges positive rows and should not be copied into a future design. It does **not** explain this rejection: the independent-random and compressed-like rows never nominate, therefore they necessarily pay the full candidate work and still land around **4.08–4.11x**. Even a perfect early-stop repair on positives cannot satisfy the frozen mature/worst gates.

The dominant avoidable cost is structural:

1. a second per-byte local rolling recurrence in addition to the mandatory observer Gear recurrence;
2. target-side comparison against up to eight retained certificate hashes for essentially every 32-byte window.

This is exactly the shape the preregistration said to retire if it failed. Do not rescue it with file-size thresholds, K/window tuning, corpus dispatch or weaker controls.

## Causal next hypothesis

A legitimate redesign should reuse the mandatory observer Gear state rather than maintain a second rolling signal. For recurrence `H_i = 2*H_{i-1} + gear[byte_i] (mod 2^64)`, the weighted fingerprint of the last 32 bytes is derivable as:

`W_i = H_i - (H_{i-32} << 32) (mod 2^64)`.

That requires only delayed observer state plus subtraction, not another Gear lookup/rotate/xor recurrence. Since the source certificate retains the eight numerically smallest `W`, target lookup can first compare `W_target` with the certificate's current maximum; almost all unrelated windows should fail that single comparison without an eight-way scan.

This is a new mechanism-level hypothesis, not threshold rehabilitation of the rejected shape. It must independently preserve exact nomination behavior and prove carrying cost before any writer integration.

## Claim boundary

No stored-byte, reader, density, RSS, release, v0.29/v0.30 or full-ingest claim follows. The result only retires the present native carrying shape and preserves a causal redesign direction.
