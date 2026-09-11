# ONE-G0.2 second-stage relation falsifier — hosted result — 2026-09-10

## Claim boundary

Transfer-only modeled relation-check traffic oracle. This result does **not** change the ONE representation, does not authorize product runtime claims, does not enable a second-stage filter in the writer, and does not execute Genesis inputs.

## Exact source and hosted evidence

- branch: `research/cmpct1`
- exact source: `ea2e3e9d824bee69051a96f778b5e0c744fcbad2`
- experimental version: `ONE-G0.2`
- workflow: `CMPCT1 ONE-G0.2 second-stage relation falsifier`
- run: `34530892434`
- job: `103051054506`
- job conclusion: `success`
- artifact: `10173531887`
- artifact name: `one-g02-second-stage-relation-falsifier-ea2e3e9d824bee69051a96f778b5e0c744fcbad2`
- artifact digest: `sha256:8af228e54d418d18de2d881a365256ab64c46e77f6bcd65dae3294ebc55a0d32`
- hostile tests: `4 passed in 0.23s`

The workflow bound checkout HEAD to the exact source before executing the tests and preregistered oracle.

## Preregistered decision

`ADVANCE_SECOND_STAGE_FALSIFIER_ORACLE_ONLY`

All hypotheses passed:

- H1 independent geometry: true
- H2 true-Law retention: true
- H3 stage-2 kill: true
- H4 dual-collision honesty: true
- H5 information-yield accounting: true

This authorizes only a subsequent writer-integration experiment with actual CPU/wall/RSS/cache measurements. Full exact proof remains the only positive authority for ADD8/XOR Laws.

## Frozen matrix

Relations:

- ADD8(+37)
- XOR(0xA5)

Lengths:

- 32 B
- 256 B
- 4,096 B
- 16,384 B

Each relation/length pair has three deterministic rows:

1. true relation;
2. `stage2_collision`: one poisoned byte outside all 16 primary probes but on a second-stage midpoint probe;
3. `dual_collision`: one poisoned byte outside both sparse probe sets.

The writer's current 16-point primary geometry matched the independently transcribed oracle on every row. The second-stage set is 15 midpoint probes and is disjoint from the primary set.

## Modeled relation-check traffic

The accounting begins after the already-paid primary sampler. For every tested length the second stage inspects 15 source bytes + 15 target bytes = **30 B**.

For a baseline candidate proceeding directly to exact proof, remaining relation-check traffic is `2N`.

### Stage-2 collision rows

All eight stage-2 collision rows passed the primary sampler, failed the second stage, and were false under independent complete relation checking. Under the modeled ladder they therefore avoid the complete proof.

| Length | Baseline remaining | Stage-2 remaining | Modeled ratio |
|---:|---:|---:|---:|
| 32 B | 64 B | 30 B | 2.133333x |
| 256 B | 512 B | 30 B | 17.066667x |
| 4,096 B | 8,192 B | 30 B | 273.066667x |
| 16,384 B | 32,768 B | 30 B | 1,092.266667x |

Across ADD8 and XOR together:

- hostile kill rows: **8**
- exact-proof bytes avoided: **83,072 B**
- candidate second-stage bytes: **240 B**

These ratios are **modeled observed-byte ratios, not CPU speedups**.

### True and dual-collision rows

The experiment deliberately preserves the cost when the second stage cannot decide:

- every true relation passes both sparse stages and still pays exact proof;
- every dual-collision adversary passes both sparse stages, then is correctly rejected by exact proof;
- both classes pay exactly **+30 B** of sparse relation checking per row relative to the baseline remaining proof path;
- total added second-stage traffic is **240 B** across the 8 true rows and **240 B** across the 8 dual-collision rows.

The dual-collision negative is material: adding a sparse stage cannot eliminate the need for exact proof. An adversary can always place a mismatch outside both fixed sparse sets; in that case the new stage is pure overhead.

## Causal interpretation

The current 16-point sampler is safe because it never has positive authority, but sampler-collision evidence showed that a crafted near-miss can force `2N` exact-proof traffic. This hosted experiment demonstrates that a disjoint rejection-only observation set can cheaply kill a selected class of those near-misses while preserving true relations and the exact-proof safety boundary.

The result is intentionally narrower than a writer optimization. Fixed midpoint probes may be cheap in modeled traffic but expensive in elapsed time if they add irregular memory accesses or duplicate information already available from fused observation. The next question is therefore not whether another sampler can work in principle; it is whether a second-stage signal can be obtained with positive **real** marginal information yield.

## Strongest negative / hostile review

A dual-collision input defeats both sparse stages by construction and makes the candidate path strictly worse by 30 observed bytes before exact proof. Therefore:

- no claim of universal proof-work reduction is allowed;
- no sample-count or position tuning is justified from this corpus;
- no writer integration is authorized without actual CPU, wall, RSS and cache/memory-traffic evidence;
- the preferred implementation candidate should reuse already-paid fused-observation/block-sketch information if that signal is sufficiently independent, rather than automatically adding 15 new sparse loads.

## Next decisive experiment

Preregister a writer-integration A/B that compares:

1. current `primary sampler -> economic gate -> exact proof`;
2. `primary sampler -> economic gate -> rejection-only second-stage signal -> exact proof for survivors`.

The A/B must use generator-distinct true relations, ordinary false candidates, stage-1 collisions and dual collisions. It must preserve byte-identical wire/reader semantics and independently verify exactness. Charge actual creation CPU/wall, peak RSS, relation-check/source traffic and any incremental state. A candidate advances only if real elapsed/CPU economics support the modeled traffic reduction without materially harming true-Law or ordinary-negative paths.

Before adding new sparse loads, audit whether the existing native block-relation sketch/fused-observation state can supply an independent second-stage rejection signal at near-zero incremental read traffic.

## Genesis separation

- `genesis_inputs_executed = false`
- `genesis_comparison_executed = false`
- `genesis_scoring_executed = false`
- `genesis_winner_selected = false`

Frozen comparison authorities remain unchanged:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`
