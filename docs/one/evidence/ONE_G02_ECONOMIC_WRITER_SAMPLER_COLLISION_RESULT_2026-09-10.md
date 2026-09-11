# ONE-G0.2 economic writer sampler-collision hosted result — 2026-09-10

## Decision

`ADVANCE_SAMPLER_COLLISION_SAFETY_ONLY`

This is transfer-only adversarial selection-safety evidence. It is not a density promotion, not a product threshold, not a Genesis comparison, and not permission to weaken exact proof.

## Exact hosted authority

- branch: `research/cmpct1`
- source: `5878d25d8da7a1c47232182055a0e15d774fd0b2`
- workflow: `CMPCT1 ONE-G0.2 Crystallization marginal cost model`
- run: `34517588644`
- economic-writer-admission job: `103006792531`
- run conclusion: `success`
- artifact: `10168607487`
- artifact digest: `sha256:1d1bc9cd8edd0682855fd5502ba8e13baff412ac6282c4515c26ad3bf6d9f42c`

The exact-source job completed all writer-admission tests, the preregistered transfer writer-admission experiment, independent admission oracle, selective-access companion falsifier, sampler-collision tests, sampler-collision experiment, claim-boundary assertions, and artifact retention.

## Hosted sampler-collision result

Frozen hostile matrix:
- relations: ADD8(+37), XOR(0xA5)
- lengths: 17, 32, 256, 4096 bytes
- eight rows total
- frozen sample count: 16

Every row was constructed so that all 16 sampled bytes satisfy the nominated relation while one independently selected unsampled byte violates it. The independent frozen sampler oracle matched the writer sampler on every row.

Every hostile target remained reader-visible `surprise` in both the ungated and economic writers. There were zero false survivors. Exact reconstruction, deterministic economic wire, generic ONE reader ontology, and complete-byte non-regression all passed.

Exact-proof accounting proves the intended causal boundary: economic admission did **not** claim a proof-work win on these economically admissible lengths. The hostile nomination proceeded to full proof and was rejected:

| relation | length | poison index | current proof bytes | economic proof bytes | current wire | economic wire |
|---|---:|---:|---:|---:|---:|---:|
| ADD8 | 17 | 15 | 34 | 34 | 891 | 891 |
| ADD8 | 32 | 1 | 64 | 64 | 921 | 921 |
| ADD8 | 256 | 1 | 512 | 512 | 1377 | 1377 |
| ADD8 | 4096 | 1 | 8192 | 8192 | 9060 | 9060 |
| XOR | 17 | 15 | 34 | 34 | 891 | 891 |
| XOR | 32 | 1 | 64 | 64 | 921 | 921 |
| XOR | 256 | 1 | 512 | 512 | 1377 | 1377 |
| XOR | 4096 | 1 | 8192 | 8192 | 9060 | 9060 |

All H1–H4 gates passed.

## Companion writer-admission evidence from the same artifact

The broader preregistered transfer writer-admission experiment also returned `ADVANCE_ECONOMIC_WRITER_ADMISSION`:
- complete-byte economic safety passed;
- no false admits;
- no false rejects;
- exact semantics / deterministic wire / generic ontology passed;
- measured exact-proof work dropped from 132 bytes to 0 on the tiny-binary rejection set, a 132-byte reduction;
- no timing regressions crossed the preregistered 5% + 3 ms gate;
- mixed-tree complete wire changed from 4149 to 4146 bytes while rejecting the short ADD8 as Surprise;
- mixed-tree exact-proof work changed from 216 to 200 bytes;
- independent admission oracle returned `ADVANCE_INDEPENDENT_ADMISSION_ORACLE`;
- selective-access companion returned `ADVANCE_ECONOMIC_WRITER_SELECTIVE_ACCESS` with native no-fallback true.

These are synthetic/transfer writer-selection results only and must not be promoted into Genesis claims.

## Hostile-review note

The first draft of the sampler oracle imported the writer's `SAMPLE_POINTS`, which would have allowed production and oracle sampling to drift together. That shared-authority bug was repaired before hosted execution: the oracle now freezes a literal 16-point contract and separately requires production `SAMPLE_POINTS == 16`.

## Interpretation

The current seam behaves correctly on the strongest targeted near-miss tested here:

`cheap sample nomination -> economic admission -> full exact proof -> Surprise fallback`

Sampling is therefore an opportunity gate, not semantic authority. A near-miss that fools every sampled byte still cannot become reader-visible Law without exact proof.

This result does **not** show that 16 samples are globally optimal, that the false-positive rate is acceptable on arbitrary data, or that economically admissible candidates are cheap to disprove. The 4096-byte adversarial rows deliberately demonstrate the opposite cost shape: a false sampled nomination can still force 8192 exact-proof bytes before rejection.

That remaining cost is now the interesting optimization target: reduce expensive false-positive proof work without sacrificing the exact-proof semantic firewall.

## Genesis separation

- `genesis_inputs_executed = false`
- `genesis_comparison_executed = false`
- `genesis_scoring_executed = false`
- `genesis_winner_selected = false`

Frozen comparators remain:
- v0.29 `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- v0.30 `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

## Next causal question

Do not remove exact proof. Instead test whether a cheap second-stage falsifier (for example a second independent sparse probe or block sketch already available in ONE discovery infrastructure) can reject sampler-collision near-misses before the O(n) proof while preserving true Law nominations, complete-wire economics, CPU/wall/RSS, and the same reader representation.
