# ONE-G0.2 native fused nomination compact-local-SoA result — 2026-09-06

## Status

**Terminal negative for speed promotion; preserve as exact state/layout evidence.**

The compact local-SoA candidate preserves the authoritative 64-entry local nomination semantics and reduces local-ring state by exactly 512 B, but it does **not** satisfy the preregistered whole-consumer speed gate. Do not promote it as the fused nomination speed baseline and do not rescue it with post-hoc thresholds or workload classifiers.

## Frozen hypothesis

The preregistered hypothesis was that replacing the local AoS ring (`key`, `start`, `used`) with separate contiguous `key[64]` and `start[64]` arrays, deriving liveness from `local_count`/`local_head`, would preserve exact nomination semantics while making the mature productive fused nomination consumer at least 5% faster.

Disproof condition: any semantic mismatch, state delta other than the frozen -512 B, mature productive median ratio above 0.95x, any productive row above 1.03x, or control median above 1.03x.

## Provenance

- primary branch: `research/cmpct1`
- preregistration commit: `cf3e4dd24575bf6a3118aa80de80a0993437781e`
- exact-source Builder parent: `4c0dfd32d3027e01cc5ce4e9a24cfa878cd8f3`
- CI-binding commit: `c9fbac5c58142d1a874e1526cb80cdea66ac279f`
- workflow: `ONE-G0.2 native fused nomination compact local SoA`
- authoritative run: `34039464287`
- job: `101503463610`
- GitHub Actions tested PR merge commit: `7137300d9364bcf9b94100e3b0545df219f24b4b`; the benchmark/workflow sources were the source-pinned files introduced by the commits above.
- artifact: `9991250749`
- artifact digest: `fb152b3accdd0c311f8db90f34eb236373c5546efca039d2b541bc45f026de55`

## Exact result

The semantic gate stayed green:

- ONE suite: **93 passed**;
- semantic failures: **0**;
- local state reduction: **exactly 512 B** on every measured row;
- representative total fused state changed from 44,128 B to 43,616 B, and from 54,880 B to 54,368 B where the global demand-grown index expanded.

The speed hypothesis failed:

- mature productive whole-consumer median ratio: **0.9876326838751676x**;
- mature median speed improvement: **~1.2367%**;
- worst productive ratio: **1.0108768921439804x**;
- control median ratio: **0.9799530080286599x**;
- terminal benchmark decision: **`reject_local_soa_speed`**.

The workflow conclusion is `failure` because the benchmark correctly exits non-zero when the frozen promotion hypothesis is rejected; test/semantic infrastructure itself was green.

## Hostile-review interpretation

This is useful negative evidence. The local ring layout can be made 512 B smaller with exact semantics, but the whole fused consumer gains only about 1.24% at the mature median. Together with the terminal mirrored-fp8 result, this says the 64-entry local lookup is **not a sufficiently large universal clock owner to justify more unprofiled local-ring polishing**.

Do not cherry-pick isolated faster rows and do not retroactively redefine the experiment as a memory promotion. The exact -512 B state result remains reusable causal evidence, but a resource-only promotion would require its own preregistered system-level gate.

## Decision

**Reject compact local SoA as the fused nomination speed baseline.**

Retain:

1. the exact -512 B state fact;
2. exact semantic equivalence evidence;
3. the causal conclusion that local-ring layout alone cannot deliver the required material whole-consumer speed gain.

## Next decisive action

Stop iterating on local-ring representations without new attribution evidence. Re-measure the current fused/native writer boundary, identify the next stable elapsed-time or memory-traffic owner, and attack that owner with a frozen falsifier. Existing fp8 and SoA negatives should be treated as evidence against spending additional Genesis-window effort on local-ring micro-optimizations.
