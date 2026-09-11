# ONE-G0.2 native Segment SWAR — terminal result (2026-09-06)

## Mission lock

Test whether a semantics-preserving word-at-a-time (`uint64_t`) equality precheck can materially accelerate the native Segment proof path without violating ONE's universal hostile/resource contract. The candidate may accelerate proof only; it may not alter Segment boundaries, Law/Surprise decisions, reconstruction semantics, wire semantics, locality, recovery, or reader behavior.

This experiment was preregistered before the result in `ONE_G02_NATIVE_SEGMENT_SWAR_PREREG_2026-09-06.md`. Per that preregistration, a result that is fast on productive relations but materially regresses hostile fragmented cases is a terminal rejection. It must not be rescued after the fact with a workload/size/density dispatcher or threshold.

## Exact CI authority

- Workflow: `ONE-G0.2 native Segment SWAR`
- Run: `34053437699`
- Job: `101541009475`
- Exact-source head: `42dbbe02be476a13b27a083d8b6eb0c582f5efa0`
- Artifact: `9995259025`
- Artifact name: `one-g02-native-segment-swar-42dbbe02be476a13b27a083d8b6eb0c582f5efa0`
- Artifact SHA-256 digest: `7c401ef9a406ff0b82077246d66b83f9328d8cdf3f854143833c0089ed925a80`
- Unit tests: `93 passed`
- Semantic failures: `0`

The workflow conclusion is red because the preregistered benchmark gate intentionally exits non-zero when the hypothesis is falsified. This is a result-bearing rejection, not a unit-test or infrastructure failure.

## Measured result

Productive mature rows are extremely strong:

- mature productive median ratio: `0.5897473687185409x`
- mature productive improvement: `41.02526312814591%`
- mature productive rows `<=0.95x`: `20`

However, the preregistered fragmented hostile family fails badly while remaining semantically exact:

- hostile ratio: `1.8863208659317698x`
- hostile correctness: `pass`
- hostile performance: `fail`

The candidate therefore violates the universal speed/resource contract despite its large productive gain.

## Hostile review and causal interpretation

The failure is mechanism-level rather than a tuning accident. On long equal stretches, the 64-bit precheck proves eight bytes at once and removes scalar byte comparisons. On fragmented/false-pattern input, the same precheck is paid repeatedly, quickly fails, and then hands control back to scalar proof. The candidate therefore adds fixed failed-proof work exactly where useful equality runs are absent.

That means the attractive productive median does not justify promotion: ONE must not become fast only when a hidden workload classifier happens to predict the right relation shape. A post-result dispatcher would merely convert this clean falsification into heuristic debt.

## Terminal decision

**REJECT native Segment SWAR as the default ONE-G0.2 Segment speed baseline.**

Preserve the result as a strong negative. Do not continue local word-at-a-time/SWAR tuning, per-size thresholds, density gates, or workload dispatchers as ordinary Genesis speed work.

## What the negative teaches

The useful principle is not "compare bytes wider." The productive gain proves that repeated Segment proof is expensive enough to matter, while the hostile regression proves that another speculative local proof layer is the wrong universal abstraction.

The next speed hypothesis should instead attack the reread itself: fuse or reuse Segment-boundary/proof information from an already-required native observation/relation pass so that bytes are not independently revisited for segmentation. Any such experiment must preserve the same Segment boundaries and Law/Surprise semantics and must include an instrumentation-overhead or equivalent-control gate.

This remains ONE representation work. No reader-visible mechanism, opcode, legacy-codec fallback, comparator weakening, locality relaxation, or recovery relaxation is authorized by this result.
