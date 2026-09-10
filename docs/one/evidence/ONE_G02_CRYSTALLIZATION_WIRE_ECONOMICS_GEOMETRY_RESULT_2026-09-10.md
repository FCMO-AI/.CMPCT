# ONE-G0.2 Crystallization complete-wire economics geometry — hosted result

Date: 2026-09-10
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Source under test: `7133713e5a3718bb39842734302717d18c4639cd`
Hosted run: `34509161237`
Hosted job: `102978693211`
Artifact: `10165474263`
Artifact digest: `sha256:f4aebcadbefc52c52803f64e6ffd8ae752ea0d711cbe4c31f3ad43af29889ce0`
Conclusion: **SUCCESS**
Scientific decision: **ADVANCE_CRYSTALLIZATION_ECONOMICS_MODEL**

## Mission lock

This is transfer-only descriptive evidence about complete authenticated ONE wire economics. It is not a product threshold, not a writer-policy change, not a Genesis result, and not evidence against the frozen v0.29/v0.30 comparators.

The run explicitly preserved:

- `genesis_inputs_executed = false`
- `genesis_comparison_executed = false`
- `genesis_scoring_executed = false`
- `genesis_winner_selected = false`

## Hosted result

All structural gates passed. Candidate and authenticated Surprise-only control reconstructed exactly, candidate wire was deterministic, reader-visible ontology remained generic ONE, and intended reader-side Law structure was present.

The preregistered 48-row matrix produced:

| family | first non-regressing | stable non-regressing | later regressions |
|---|---:|---:|---|
| exact reuse | 2 B | 2 B | none |
| Fill | 2 B | 2 B | none |
| ADD8(+37) | 16 B | 16 B | none |
| XOR(0xA5) | 16 B | 16 B | none |

`stable_non_regressing_tail_all_families = true` and `tiny_regression_present = true`.

For ADD8 and XOR the observed complete-wire deltas around the transition were identical:

- 2 B: `+9 B`
- 4 B: `+7 B`
- 8 B: `+3 B`
- 16 B: `-5 B`
- 32 B: `-21 B`
- 64 B: `-53 B`
- 128 B: `-116 B`
- 256 B: `-244 B`
- 512 B: `-500 B`
- 1024 B: `-1012 B`
- 4096 B: `-4084 B`
- 16384 B: `-16371 B`

Fill was already non-regressing at the smallest measured row and then tracked almost exactly one fixed byte of representation cost against `n` Surprise bytes removed: 2 B -> `-1 B`, 4 B -> `-3 B`, 8 B -> `-7 B`, 16 B -> `-15 B`, through 16384 B -> `-16383 B`.

Exact reuse was also favorable from 2 B onward; e.g. 2 B -> `-5 B`, 4 B -> `-7 B`, 8 B -> `-11 B`, 16 B -> `-19 B`, 32 B -> `-35 B`, 64 B -> `-67 B`.

## Causal interpretation

The ADD8/XOR sequence is close to an affine law `delta ~= K - n`, with a small serialization-boundary residual at larger lengths. The important result is therefore not “16 bytes is the threshold.” Sixteen is only the first measured power-of-two row on the non-regressing side. The mechanism-level hypothesis is that Crystallization should be admitted when avoided Surprise bytes exceed the generic representation/control cost of the Law.

This is consistent with CMPCT1's marginal-information-yield doctrine: semantic predictability is necessary but not sufficient. A proven Law that costs more persistent bytes than the Surprise it replaces should remain Surprise unless another product property deliberately justifies that Pareto move.

## Strongest negative result

Current automatic discovery does crystallize semantically exact tiny ADD8/XOR relations that make the complete authenticated archive larger. At 2, 4, and 8 bytes the measured regressions were +9, +7, and +3 bytes respectively. This is real regression debt in the current candidate seam, not benchmark noise, because complete wire size is deterministic.

Do not repair this by hard-coding a 16-byte family threshold from this matrix. The next experiment is preregistered separately and asks whether a local marginal-cost model predicts the sign safely across unseen lengths and serialization/authentication boundaries.

## Next decisive action

Falsify the preregistered marginal-cost admission model on its independent 144-row transfer matrix. Any predicted admission that actually enlarges complete wire retires/repairs the model. Boundary false rejects are preserved as HOLD rather than being laundered into ADVANCE. Only after that evidence is hosted and exact-source should the writer be changed, followed by a fresh-process CPU/wall/RSS and memory-traffic A/B.
