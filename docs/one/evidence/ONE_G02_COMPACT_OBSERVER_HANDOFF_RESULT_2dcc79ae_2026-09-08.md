# ONE-G0.2 compact observer handoff — exact result at `2dcc79ae` — 2026-09-08

Status: **negative result preserved; `HOLD_COMPACT_OBSERVER_HANDOFF`**.

## Exact evidence authority

- source branch: `research/cmpct1`
- exact source SHA: `2dcc79ae7d62a21fde6006a65aed49ada49b54d5`
- workflow run: `34214734980`
- job: `102023717570`
- artifact id: `10051391132`
- artifact name: `one-g02-compact-observer-handoff-2dcc79ae7d62a21fde6006a65aed49ada49b54d5`
- artifact digest: `sha256:43041c2579f5c826baec69065b6bde3e5f698327cbdefb660998fdcf2e44cf98`
- semantic proof step: passed
- frozen whole-writer falsifier: returned nonzero because the preregistered performance gate failed

This is a scientific red, not an infrastructure failure.

## Decision summary

The candidate kept the native observer's worst-case ctypes output arenas alive and deferred eager Python `RunOpportunity` / `ReuseOpportunity` materialization. All semantic gates were exact, but only one of three preregistered opportunity-oriented 1 MiB families cleared the <=0.90 wall/CPU win threshold. The all-rich and low-opportunity <=1.05 no-regression gates both failed.

Exact JSON summary:

- `semantic_gates_pass = true`
- `rich_wall_wins_1m = 1`
- `rich_cpu_wins_1m = 1`
- `rich_no_regression_1m = false`
- `control_no_regression_1m = false`
- `decision = HOLD_COMPACT_OBSERVER_HANDOFF`

## 1 MiB result matrix

| family | compact/eager wall | compact/eager CPU | run count | reuse count | useful native output | native capacity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| structured | 0.315594x | 0.315665x | 1 | 12,287 | 294,912 B | 3,539,040 B |
| compressed_like | 1.083153x | 1.082989x | 0 | 0 | 0 B | 3,539,040 B |
| long_runs | 1.038299x | 1.038179x | 220 | 0 | 5,280 B | 3,539,040 B |
| random | 1.069368x | 1.069304x | 0 | 0 | 0 B | 3,539,040 B |
| near_repeats | 1.015903x | 1.015923x | 1 | 0 | 24 B | 3,539,040 B |

The structured row is a very large mechanism-level gain: eager median wall was 23.689 ms and compact median wall was 7.476 ms. It demonstrates that eager Python opportunity-object construction can dominate the current charged writer when the observer emits many opportunities.

The candidate is nevertheless not generally advanceable in this form because `compressed_like` and `random` regressed by ~8.3% and ~6.9% respectively, and those losses cannot be averaged away. `long_runs` remained within the 5% no-regression floor but did not reach the 10% win target. `near_repeats` was close to parity.

## Mechanism interpretation

Every 1 MiB row reserved ~3.54 MiB of native output capacity. The arena-retaining compact view carried those ctypes arrays through the remainder of the writer even when useful output was 0–24 bytes. The eager wrapper also allocates those arrays during observation, but after it materializes Python opportunities the native scratch arrays fall out of scope before admission/segmentation/Program/validation/emission.

That lifetime difference is a plausible exported cost, but it is not yet proven causal. Allocator state, cache pressure, object lifetime, measurement noise, or the fact that the current downstream writer does not consume observation opportunities may also contribute. The follow-up packed-observer rehabilitation is explicitly designed to falsify the arena-lifetime explanation rather than assume it.

## Important workload correction

The preregistration called `compressed_like` opportunity-rich by construction intent, but the exact native observer found **zero** opportunities on the 1 MiB row. Do not rewrite the original preregistration after the fact. For follow-up interpretation, treat this row as a hostile zero-output case that still must not regress; do not use its label to claim opportunity-rich behavior that the observer did not actually see.

## Unchanged representation/resource truth

The writer output remained identical across arms. At 1 MiB the measured current temporal writer emitted 2,097,273 canonical bytes with 2,097,152 Surprise bytes and reconstructed both roots exactly. This experiment changes neither stored format nor reader semantics. It earns no v0.29/deferred-v0.30 Genesis score.

## Research consequence

Preserve the structured win as a breakthrough seed, preserve every red row as regression debt, and test exact-size packed retention before either promoting compact handoff or abandoning it. Do not relax the original 0.90 / 1.05 gates.
