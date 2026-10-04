# v0.30 Analytics exact-parallel-repack scheduling floor

Status: **terminal negative for scheduling-only acceleration of the measured C25EG02 high-effort selection**.

This note preserves negative evidence from the exact CI receipt produced at source head
`6680a477514ecdb592dfd521d936a42a4187d6fe` by the `CMPCT v0.30 federated exact parallel repack`
authority. It does not grant release credit, change production policy, or weaken any v0.29, ZIP, Zstd,
locality, integrity, recovery, or platform gate.

## Referee / pre-mortem

Hypothesis under test: Analytics might cross its remaining creation-time boundary merely by scheduling
the already-selected high-effort pack recompressions more aggressively, without changing which work is
performed or the emitted bytes.

A decisive scheduling-only test must satisfy all of the following:

- exact bytes relative to the sequential policy;
- strict accepted-v0.29 size improvement;
- locality <= 8x and decode units <= 8 MiB;
- honest publication and strong-verification time inside the measured path;
- strict creation-time victory over ordinary ZIP/Deflate, not only over Zstd-19.

The hostile pre-mortem is simple: if even an impossible perfect eight-worker scheduler cannot fit the
same measured work below ZIP, additional worker-count tuning is not a credible route. The next family
must remove work, make the work materially cheaper (for example a native hot path), or change the
search/admission algorithm.

## Builder / decisive instrument

The exact receipt establishes the following Analytics row:

| Quantity | Exact receipt |
| --- | ---: |
| accepted v0.29 | 6,135,172 B |
| exact C25EG02 candidate | 6,134,723 B |
| margin vs v0.29 | -449 B |
| selected high-effort packs | 48 |
| measured parallel workers | 4 |
| measured parallel compression | 3.432959497 s |
| measured verified create | 3.956441341 s |
| sequential verified create | 8.883970215 s |
| measured parallel speedup | 2.245444694x |
| ZIP median create | 1.358917511 s |
| Zstd-19 median create | 13.381456636 s |
| max read amplification | 1.0x |
| max decode unit | 524,288 B |

The receipt also reports `modeled_serial_extra_ms = 8454` for the same selected high-effort pack work.
For a deliberately optimistic scheduling floor, gift the implementation perfect balance, zero scheduling
overhead, and full eight-way divisibility of that entire 8.454 s work total:

`ideal_8_worker_repack = 8.454 / 8 = 1.05675 s`

The measured non-repack work that cannot disappear merely by adding repack workers is:

- level-1 build: `0.229844521 s`
- publication: `0.027545564 s`
- strong verification: `0.266091759 s`

So the optimistic same-work scheduling floor is:

`1.05675 + 0.229844521 + 0.027545564 + 0.266091759 = 1.580231844 s`

That is still `0.221314333 s` slower than ZIP, or **1.16286x ZIP time**. The real implementation cannot
beat an impossible scheduler that has no coordination cost and perfect task balance.

This floor is intentionally narrow. It proves only that **the same high-effort selection, with the same
modeled work, cannot reach the ZIP boundary by scaling scheduling alone to the existing eight-worker
ceiling**. It does not claim that a native compressor, fewer auditions, a different representation, or a
different admission/search law cannot win.

## Hostile reviewer / post-mortem

Strongest surviving critique: `modeled_serial_extra_ms` is a modeled work total, not a hardware lower
bound on all possible implementations. A future native path could reduce the cost of each selected task,
or a different algorithm could avoid constructing some tasks entirely. Therefore this evidence must not
be misused as a representation impossibility proof.

That critique does not rehabilitate worker-count tuning. It strengthens the classification: Analytics is
not blocked by representation size here—the exact candidate is already 449 B below v0.29. It is blocked
by execution/search economics. Scheduling has already delivered a 2.245x measured speedup and remains
far outside ZIP; the idealized eight-worker same-work floor remains 16.286% slower than ZIP.

## Domination audit

- Strict target: every frozen workload strictly smaller **and** strictly faster to create than ZIP/Deflate
  and solid Zstd-19, while preserving accepted-v0.29 and all release laws.
- Diagnosis: **D2/D3** (duplicated/expensive execution plus search/admission work), not D4.
- Minimum justified radicality: **R2**, escalating to **R3** where exact work elimination requires a new
  admission/search algorithm.
- Saturation trigger: **S4** for scheduling-only acceleration; repeated work remains the exported cost.
- RPS for the next unblocked Analytics work-elimination/native hypothesis: **76/100** (high leverage but
  behind an unblocked higher-RPS D4 structural red such as Shifted).
- Measured gap change: exact bytes crossed v0.29 by 449 B; four-worker scheduling reduced verified create
  from 8.883970215 s to 3.956441341 s, but the result is still 2.91294x ZIP. The impossible eight-worker
  same-work floor is still 1.16286x ZIP.
- Strongest self-critique: the scheduling floor does not bound a faster implementation of each task.
- Terminal decision: **ESCALATE_RADICALITY** for Analytics execution; **RETIRE_FAMILY** only for
  scheduling-only worker-count scaling of the same high-effort selection.
- Next decisive test: instrument the selected high-effort path by phase and pack, then test an exact
  single-pass/native or proof-directed admission that removes enough compression work to fit the
  approximately 0.835 s repack budget left after measured fixed build/publication/verification costs.

The candidate remains research-only until normal generic admission, canonical semantics, reader and
verification, recovery/locality, native, Android, exact all-15 no-regression/external authority, and final
release authority all pass on one exact fingerprint.
