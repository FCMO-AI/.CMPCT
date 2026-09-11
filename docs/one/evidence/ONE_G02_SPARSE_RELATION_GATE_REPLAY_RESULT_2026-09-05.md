# ONE-G0.2 — sparse relation gate evidence replay result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **retire the all-sizes sparse gate shape; preserve exact large-root turnstile evidence**

## Exact evidence

- source: `3c46d795d82b207ff292fbacb0b049afb8bac45b`
- workflow: `33974859908`
- artifact: `9972032362`
- artifact digest: `sha256:a14a8c35bfbfa16adb6ca3eb64580e89621ea994892429aa60e13cc575823276`
- pre-result ONE semantic/hostile tests: pass
- decision emitted by unchanged frozen benchmark: `retire_sparse_relation_gate_shape`

The prior historical run at source `c76590233f3880d6e91fbd76c04217c6cc78d3a9` never reached the benchmark and had no artifact. This replay executed the unchanged frozen benchmark and therefore supplies the first scientific result for that preregistered gate.

## Result

The gate is semantically exact on every frozen pair and size:

- productive relations retained: **100%**;
- exact enabled/disabled classification: **all rows**;
- exact best shift on productive rows: **all rows**;
- one independent-random pair cheaply rejected at every size;
- seven-size median gated/baseline elapsed: **0.816550286x**, comfortably better than the frozen <=0.95x aggregate threshold.

However, the all-sizes contract fails for two precise reasons:

| relation bytes | gate bytes / logical relation bytes | gated / baseline | frozen status |
|---:|---:|---:|---|
| 4 KiB | 3.90625% | 1.10196x | read-budget + runtime fail |
| 8 KiB | 1.953125% | 0.96343x | read-budget fail |
| 16 KiB | 0.9765625% | 0.81655x | pass |
| 32 KiB | 0.48828125% | 0.87045x | pass |
| 64 KiB | 0.244140625% | 0.77480x | pass |
| 128 KiB | 0.1220703125% | 0.77222x | pass |
| 256 KiB | 0.06103515625% | 0.75798x | pass |

The frozen all-sizes result is therefore a legitimate **negative** even though five larger rows are strong wins.

## Mechanism-level interpretation

The gate consumes a fixed 160 compared bytes per candidate pair on this geometry. With five candidate pairs, the reported read fraction is `800 / (5 * relation_bytes) = 160 / relation_bytes`. The frozen <=1% budget therefore has an exact amortization boundary:

`relation_bytes >= 160 / 0.01 = 16,000 bytes`.

This is not a tuned threshold inferred from timing. It follows algebraically from the frozen gate's fixed information cost and frozen 1% work budget. The first tested power-of-two size above the bound is 16 KiB, exactly where the read-budget gate turns green.

The 4 KiB runtime loss independently confirms that paying the constant turnstile cost on tiny relations is the wrong execution shape.

## Hostile Reviewer

Do not rewrite the gate to use fewer probes merely because the small rows fail. That would alter the frozen structural detector after seeing the result and could spend opportunity-retention debt.

Also do not call the gate generally solved: candidate relation-pair identity is supplied by the frozen adjacent-pair batch. Arbitrary-pair discovery remains outside this evidence.

The legitimate next Builder is an **amortization-safe exact dispatcher**: for known candidate pairs smaller than 16,000 bytes, run the existing exact proof directly; at or above 16,000 bytes, use the unchanged sparse gate before exact proof. This preserves every benchmark row and semantic requirement while refusing to pay a gate whose own fixed information cost cannot meet budget.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows.