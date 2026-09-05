# ONE-G0.2 — amortization-safe known-pair relation gate result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **advance the known-pair amortization-safe turnstile architecture**

## Exact evidence

- source: `32f8d0a61b181b25343ca8224fd7640f8b2dc49c`
- workflow: `33977093905`
- job: `101335602095`
- artifact: `9972635192`
- artifact digest: `sha256:7a706926b7bb0826ced0449c5e8c5a6747bdc617d5fd06ed240cfe5b5b525fae`
- pre-result ONE semantic/hostile tests: pass
- emitted decision: `advance_known_pair_amortization_safe_gate`

## Mission / hypothesis

The parent sparse exact-shift gate retained every productive relation and produced a strong aggregate speed win, but its fixed 160-byte comparison bill made it structurally ineligible for small relations under the frozen 1% information-read budget. The preregistered repair changed only admission ownership:

- relation length `< 16,000 B`: run the existing exact safe relation proof directly;
- relation length `>= 16,000 B`: run the unchanged sparse gate before exact proof.

The 16,000-byte boundary is algebraic: `160 / 0.01 = 16,000`, not selected from timing.

## Result

All frozen gates passed.

- exact enabled/disabled classification: **all 35 case/size rows**;
- exact best shift on every productive relation: **all productive rows**;
- productive relation retention: **100%**;
- false enabled relations: **0**;
- every eligible size cheaply rejected the independent-random pair;
- direct small rows used **0 gate bytes**;
- seven-size median candidate/baseline elapsed: **0.782869392x**.

| relation bytes | execution shape | gate read fraction | candidate / baseline elapsed | status |
|---:|---|---:|---:|---|
| 4 KiB | direct exact proof | 0.000000% | 1.003882x | pass |
| 8 KiB | direct exact proof | 0.000000% | 1.003526x | pass |
| 16 KiB | sparse gate + exact proof on fires | 0.9765625% | 0.782869x | pass |
| 32 KiB | sparse gate + exact proof on fires | 0.48828125% | 0.855537x | pass |
| 64 KiB | sparse gate + exact proof on fires | 0.244140625% | 0.739629x | pass |
| 128 KiB | sparse gate + exact proof on fires | 0.1220703125% | 0.688495x | pass |
| 256 KiB | sparse gate + exact proof on fires | 0.06103515625% | 0.764747x | pass |

The two direct-proof rows export only ~0.35–0.39% wrapper overhead, comfortably inside the frozen 1.03x row ceiling. The five eligible rows preserve the parent mechanism-level benefit while respecting the information-read budget.

## Mechanism-level conclusion

The important result is not a tuned size threshold. It is a reusable execution rule:

> A fixed-cost falsifier should only run where its own worst-case information cost can satisfy the search budget; below that exact amortization boundary, direct proof is cheaper and simpler.

This is compatible with ONE's marginal-information-yield doctrine because admission is derived from known detector work rather than corpus identity or benchmark timing.

## Hostile review / claim boundary

This is still **known-pair** evidence. The frozen adjacent-pair batch supplies relation identity. The result does not make arbitrary-pair discovery cheap and does not justify a rich global certificate scan.

The next decisive integration is therefore a context in which pair identity is genuinely available without extra discovery: temporal/version adjacency in the ONE writer. The turnstile must be charged end-to-end there, including nomination bookkeeping, exact proof work, emitted Law/Surprise bytes, total creation elapsed time, retained state and any access/reconstruction consequences.

No density, reader-speed, format, product, v0.29 or deferred-v0.30 superiority claim follows from this microbenchmark.
