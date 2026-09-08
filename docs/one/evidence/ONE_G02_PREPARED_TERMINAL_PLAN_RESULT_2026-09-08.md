# ONE-G0.2 Prepared Terminal Plan — exact result

Status: **HOLD_PREPARED_TERMINAL_PLAN**

## Authority

- source SHA: `6ba5041f2b63bb74bdfe3c39c177cdee957ad206`
- workflow: `CMPCT1 ONE-G0.2 prepared terminal plan`
- run: `34279283952`
- job: `102239871219`
- artifact: `10076953793`
- artifact digest: `sha256:dce7e039bd56f75f25f35df60eaccc2bf6d274268eb5f892ce2632e954a98460`
- artifact payload: `one_g02_prepared_terminal_plan.json`

Exact checkout/binding and semantic/decision-law tests passed. The frozen benchmark returned non-zero because its scientific decision was HOLD, not because the semantics suite failed.

## Frozen question

Can the unchanged terminal `Surprise` / `Fill` / `Concat` ONE Program be validated/lowered once into a deterministic bounded execution plan, then replayed without per-read graph walking or Fill-schedule construction, while preserving wire bytes, semantics, resource accounting, and paying back plan compilation within at most four replays?

The experiment measures compilation separately. It does not gift preprocessing to the candidate and does not claim one-shot cold-read or selective-range authority.

## Result

Prepared execution **does remove most of the schedule-on-read overhead**, but it does **not** make the useful Law-bearing cases competitive with the literal control. Therefore the prepared-plan architecture is not promoted in its current execution shape.

At 1 MiB:

| family | wire / literal | hot / literal wall | hot / literal CPU | hot / schedule-on-read wall | compile break-even wall |
|---|---:|---:|---:|---:|---:|
| structured | 0.875018x | 1.187541x | 1.187270x | 0.963520x | 0.457 replays |
| compressed_like | 1.000000x | 0.981116x | 0.980969x | 0.982772x | 0.804 replays |
| long_runs | 0.501019x | 1.172529x | 1.172290x | 0.687956x | 0.965 replays |
| random | 1.000000x | 0.976174x | 0.976145x | 0.978300x | 0.626 replays |
| near_repeats | 1.000000x | 0.977681x | 0.977082x | 0.973613x | 0.535 replays |

The same decisive problem appears below 1 MiB. `long_runs` is ~1.073x literal at 64 KiB and ~1.162x at 256 KiB; `structured` reaches ~1.175x literal at 256 KiB. All semantic rows remained exact. Modeled traffic is unchanged from the already-reviewed fused terminal schedule: 0.90x literal for `long_runs`, 0.975x for `structured`, and 1.00x for the other families.

## Causal interpretation

This falsifies the narrow hypothesis that rebuilding the execution schedule on every read was the whole reason useful terminal Laws lost on decode speed.

It was a real cost: at 1 MiB `long_runs`, the prepared hot path is ~31.2% faster than the schedule-on-read bulk path (`0.687956x`), and compilation repays in under one replay. However, after that bookkeeping is removed, the prepared Law path remains ~17.3% slower than literal reconstruction.

The remaining excess therefore lies inside the replay shape itself (terminal Surprise scatter / native Fill application / boundary handling around those writes, or their interaction with root materialization and authentication), not primarily in graph validation or schedule construction.

## Strongest negative

The result is unusually useful because both attractive properties survive while promotion still fails:

- density survives: `long_runs` remains ~0.501x literal wire and `structured` ~0.875x;
- modeled traffic survives: `long_runs` remains 0.90x literal and `structured` 0.975x;
- plan compilation is cheap enough to amortize quickly;
- **hot execution still misses the frozen <=1.05x literal wall+CPU gate on Law-bearing rows.**

Do not relax that gate and do not claim that prepared plans solved reader efficiency.

## Next disproof target

Do not spend another experiment on Fill-only dispatch. The next causal test should operate on the already-prepared generic terminal plan and determine whether one native mixed terminal replay (bulk Surprise copies + Fill writes in one bounded invocation, same Program and same root commitment) removes the remaining hot-path penalty. Compilation/marshalling for that mixed replay must be charged separately and subjected to a realistic replay break-even gate; no cryptographic or output-freeze work may be precomputed away.

If that still loses to literal control, stop terminal micro-optimization and move the reader effort upward to a more general reconstruction-plan/native execution model rather than continuing to polish this synthetic run family.

## Comparator / claim boundary

This result changes no reader-visible ONE grammar and earns no Genesis comparator point. Frozen v0.29 and deferred v0.30 authorities remain those recorded in `docs/CMPCT1_GENESIS.md`. The result is execution-mechanism evidence only.