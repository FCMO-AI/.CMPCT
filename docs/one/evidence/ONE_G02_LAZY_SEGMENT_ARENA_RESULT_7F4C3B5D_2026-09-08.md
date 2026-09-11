# ONE-G0.2 lazy native segment arena — exact result at `7f4c3b5d` — 2026-09-08

Status: **`ADVANCE_LAZY_SEGMENT_ARENA` as a writer resource-scheduling result.**

## Exact evidence authority

- source SHA: `7f4c3b5df729bcffc4d51acba8da1d337c320a02`
- workflow run: `34220784946`
- job: `102043138312`
- artifact id: `10053738928`
- artifact name: `one-g02-lazy-segment-arena-7f4c3b5df729bcffc4d51acba8da1d337c320a02`
- artifact digest: `sha256:0e94e95b2a79671fdb4a41cfbca58aa7edc99b456e5e85ef0639799f9c75389f`
- exact SHA binding, admitted/rejected reconstruction probes, frozen falsifier and artifact retention: passed

## Frozen decision

- `semantic_gates_pass = true`
- `rejected_memory_gate_pass = true`
- `admitted_peak_gate_pass = true`
- `decision = ADVANCE_LAZY_SEGMENT_ARENA`

The hosted ABI reports `sizeof(Segment) = 12`, so the old eager 1 MiB harness reserves **12,582,912 bytes** of segment output capacity before relation admission.

## Measured memory effect

| case | admitted | segments | eager peak RSS | lazy peak RSS | lazy/eager peak | current RSS saved after admission |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| shift_plus1 | yes | 2 | 43,096 KiB | 43,100 KiB | 1.0001x | 12,264 KiB before lazy allocation |
| shift_plus1_damage_quarter | yes | 2,052 | 45,604 KiB | 45,524 KiB | 0.9982x | 12,336 KiB before lazy allocation |
| fragmented_every96 | yes | 21,848 | 51,200 KiB | 51,004 KiB | 0.9962x | 12,444 KiB before lazy allocation |
| fragmented_every32 | **no** | 0 | **47,104 KiB** | **34,872 KiB** | **0.7403x** | **12,384 KiB** |
| independent_random | **no** | 0 | **47,140 KiB** | **34,864 KiB** | **0.7396x** | **12,200 KiB** |

On rejected roots, the candidate allocates exactly zero segment-capacity bytes and reduces fresh-process peak RSS by roughly **26%**. On admitted cases it allocates the exact same 12,582,912-byte capacity as the eager control after admission; final peak RSS remains essentially parity, and the relation decision, best shift, proof count, segment plan, Program, canonical wire and reconstructed roots remain exact.

The hostile fragmented admitted case produced 21,848 native segments and still passed, so the result is not limited to trivial two-segment relations.

## Mechanism interpretation

This is a clean opportunity-gating result: **do not allocate expensive downstream state before the cheap gate says the downstream stage will run.** It matches the ONE speed/efficiency law more directly than shrinking an arena by a guessed constant.

It also explains why the earlier packed-observer `ru_maxrss` gate was censored at ~93.46 MiB: that experiment constructed a maximum segment arena before entering its writer timing/memory boundary even though all five observer families rejected the temporal relation. The packed observer did not create that common peak; it merely could not move a high-water mark already dominated by common writer state.

## Strongest limitation

This result does **not** solve the admitted arena's worst-case capacity. Even a two-segment `shift_plus1` case still reserves the full 12 MiB once admitted. The fragmented case demonstrates why blindly capping capacity is unsafe: legitimate plans can contain tens of thousands of segments.

The next admitted-memory question is therefore growable/bounded segment output or a provable capacity bound—not an arbitrary smaller fixed buffer.

## Speed/accounting debt

Historical writer microbenchmarks usually allocated `seg_buf` outside the timed writer arm because both compared mechanisms used the same buffer. That preserved comparative fairness but undercounted absolute creation cost. A production-shape lazy arena must face a whole-writer timing gate where segment allocation is charged in both arms:

- eager control charges maximum allocation before admission;
- lazy candidate charges it only after successful admission;
- rejected roots must not pay it at all.

Do not claim a creation-speed win from this memory experiment alone.

## Campaign boundary

No ONE representation or reader behavior changed. Stored bytes, selective-read amplification, failure blast radius, recovery, portability and frozen v0.29/deferred-v0.30 authority are unchanged. This result advances native writer resource scheduling only.
