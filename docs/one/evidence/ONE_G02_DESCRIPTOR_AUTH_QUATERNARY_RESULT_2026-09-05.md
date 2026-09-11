# ONE-G0.2 — quaternary descriptor-authentication A/B — 2026-09-05

## Mission lock

The binary selectively authenticated descriptor tree had already restored the frozen density + authenticated 4 KiB access gate, but exported control/authentication bytes and hash work. The preceding cost profile showed that V=8 selective reads/updates reduce SHA-256 input traffic while creation becomes materially more expensive. A frozen arity prefilter selected arity 4 as the next structural Builder.

This result changes only the generic descriptor-authentication tree from binary to quaternary. Law control, Surprise payloads, basis AuthTree geometry, corpus, version families, density comparator and the `<=1.20x` median authenticated-touch law are unchanged. The binary instrument is rerun in-process and must remain exact/corruption-clean.

Frozen advancement rule: advance only if every quaternary descriptor authenticates, deterministic control/Surprise/proof corruption is rejected, the binary source rows remain exact, and at least one frozen basis leaf is strictly smaller than the independent-literal family while keeping every row's median authenticated 4 KiB touch `<=1.20x`.

## Exact execution identity

- experimental version: `ONE-G0.2`
- result-bearing source: `50ed62ce1c9a6b2f25715d7fadb0be2c15a469c6`
- workflow run: `33953976043`
- result-bearing job: `101273804837`
- artifact: `9965766193`
- artifact ZIP SHA-256: `9dc319bb4e6cc5cdf9e89c133b91b582d91422f2f94efd8523e07ddf76a2803a`
- ONE semantic boundary: **76/76 passed**
- authentication failures: **0**
- corruption-rejection failures: **0**
- decision: **`advance_quaternary_descriptor_auth`**

## Structural result

Quaternary descriptor-tree shape:

| versions | persisted non-root descriptor hashes | maximum descriptor proof |
| ---: | ---: | ---: |
| 1 | 0 B | 0 B |
| 2 | 64 B | 32 B |
| 4 | 128 B | 96 B |
| 8 | 320 B | 128 B |

For comparison, the binary tree uses 192 B persisted / 64 B proof at V=4 and 448 B persisted / 96 B proof at V=8. Arity 4 therefore buys `-64 B` persisted at V=4 and `-128 B` at V=8 while spending `+32 B` of worst-case proof traffic at each of those counts.

Exactly one frozen basis leaf survives the unchanged complete-storage + access gate: **80 bytes**.

For that survivor:

- worst frozen-family complete stored fraction versus independent literals: **0.9018325805664062x**;
- worst-row median authenticated 4 KiB touch amplification: **1.18603515625x**;
- worst individual authenticated-touch amplification: **1.25244140625x**.

The gate is defined on row medians, so the 80-byte leaf passes. The 1.2524x individual maximum remains visible debt; it is not averaged away or redefined as green.

Nearby failures are informative:

- 64 B leaves remain slightly larger than literals: `1.0004653930664062x` and also miss touch;
- 96 B leaves are dense (`0.8351821899414062x`) but miss the median-touch law at `1.20166015625x`;
- 192 B leaves are very dense (`0.6684341430664062x`) but still miss the median-touch law at `1.20166015625x` and have `1.24853515625x` max touch.

This is therefore a real Pareto knee rather than a density-only victory.

## Hostile review / exported debt

The structural win is not yet a speed claim. Higher arity reduces tree depth and persisted internal hashes but hashes wider parent messages and transfers more siblings in a proof. The preceding binary compute profile already showed that authentication economics can invert by version count; bytes alone cannot determine the runtime winner.

The strongest next falsifier is an exact same-input binary-vs-quaternary authentication compute A/B. It must separately measure creation and selective verification, preserve the same descriptor semantics, use repeated same-runner timing rather than one sample, and retain deterministic hash-work accounting so a wall-clock result has a causal explanation.

## Claim boundary

Research evidence for the generic ONE descriptor-authentication representation only. No canonical wire-format mutation, native-product speed, peak-memory, full 15-workload, v0.29/v0.30 supremacy, portability or release authority is claimed.
