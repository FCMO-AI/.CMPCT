# ONE-G0.2 — Gear-difference content-local phase certificate preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Mission Lock / Referee

The raw-word phase certificate is structurally successful but its unconditional native carrying shape was rejected at 2.7600x the promoted observer. Native decomposition shows a near-co-dominant hot-loop bill: rolling raw-word maintenance, phase hashing, and bottom-K selection all matter.

A selection-local sorted-4 rehabilitation is independently frozen. This experiment is a distinct mechanism-level hypothesis: **derive content-local 8-byte evidence from the Gear state that ONE already computes**, instead of maintaining a second raw-byte rolling word.

It does not change the ONE reader, Law grammar, exact relation proof, shift set, or source/target semantics.

## Algebraic invariant

The promoted observer updates a 64-bit Gear prefix state modulo `2^64`:

`P_i = 2 * P_{i-1} + G[x_i]`.

For an 8-byte window beginning at `s`, repeated substitution gives:

`P_{s+7} = 2^8 * P_{s-1} + 2^7 G[x_s] + ... + G[x_{s+7}] (mod 2^64)`.

Therefore:

`L_s = P_{s+7} - 2^8 * P_{s-1} (mod 2^64)`

is a **content-local function of exactly the same 8 input bytes**, despite being derived from prefix Gear states. Prefix history cancels algebraically.

This identity is deterministic and table-independent. It must also be checked in the validation implementation against a direct eight-byte Gear fold before structural results count.

## Candidate certificate

Keep the proven phase geometry unchanged:

- stride: 32 bytes;
- source start phases: `{0,1,2,30,31}`;
- K=4 witnesses per phase;
- target phase: 0.

Replace only the raw-word hash input. For each sampled start `s`, compute `L_s` above and use:

`H_s = mix64(L_s ^ 0x9E3779B97F4A7C15)`.

The encoder can obtain `P_{s-1}` by retaining one prefix-Gear snapshot per source phase and `P_{s+7}` from the already-live observer state. No outgoing byte, second source scan, or extra Gear-table lookup is conceptually required.

Modeled phase-certificate state is 240 B for the twenty `(u64 hash, u32 position)` witness slots plus 40 B for five `u64` prefix snapshots = **280 B**. This is writer-only discovery state.

## Frozen structural controls

Use exactly the established bounded-shift phase-certificate cohort:

- sizes 4, 8, 16, 64, 256 KiB;
- seeds 11, 37, 59;
- `shift_plus1`;
- `damage_quarter`;
- `fragmented_every96`;
- `hostile_fixed_bands`;
- `prior_certificate_targeted`;
- `fragmented_every32`;
- `independent_random`.

The existing exact safe relation dispatcher remains the authority for whether a relation truly exists.

## Falsifiable hypothesis

The Gear-difference certificate will preserve **all exact-positive nominations** captured by the frozen raw-word phase certificate and produce **zero independent-random false nominations** on the frozen matrix, while preserving the same sampled-position fraction bound (`<=0.19`).

## Frozen structural gate

Advance to native carrying-cost work only if all are true:

- prefix-difference `L_s` equals an independently computed direct eight-byte Gear fold on every sampled window tested;
- zero required positive misses against the exact relation dispatcher;
- zero independent-random false nominations;
- maximum sampled-position fraction <=0.19;
- modeled writer discovery state <=280 B;
- pre-existing ONE semantic/hostile tests pass first.

No timing claim follows from structural success.

## Disproof / next move

If the algebraic identity implementation disagrees with the direct fold, the experiment is invalid.

If the identity is exact but structural coverage regresses, retire this certificate algebra rather than adding phases/K after seeing the failures. The raw-word phase certificate remains the structural reference.

If structural coverage passes, the decisive next experiment is a native fused observer A/B that computes the Gear-difference witnesses from live prefix Gear state and five snapshots. It must compare total observer elapsed and memory traffic against both the rejected raw-word fused certificate and the promoted observer baseline. The point is work elimination, not merely a different hash spelling.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows from this experiment.