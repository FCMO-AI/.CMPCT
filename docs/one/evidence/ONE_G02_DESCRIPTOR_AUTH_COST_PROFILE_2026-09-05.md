# ONE-G0.2 — Descriptor authentication compute-debt profile — 2026-09-05

## Question

The selectively authenticated descriptor tree restored the frozen density + 4 KiB authenticated-access gate, but added Merkle structure. This frozen diagnostic asks whether that locality win merely moves the bill into authentication compute.

The comparison is against the complete-manifest authentication design it replaced, on the same version families and Surprise payloads. Common basis-tree proof/reconstruction work is excluded symmetrically. SHA-256 input accounting includes domain separators, indices/level tags, and every byte actually fed to each hash. Creation, selective read and one-existing-version update are all charged.

Frozen V=8 disproof: selective descriptor authentication must strictly reduce both selective-read SHA-256 input bytes and single-version-update SHA-256 input bytes. Creation cost is reported, not gifted. No density/access threshold is changed.

## Exact execution identity

- experimental version: `ONE-G0.2`
- result-bearing source: `0b557d987bdc65cce249ec4c295e11d678edf028`
- workflow run: `33953565992`
- result-bearing job: `101272684600`
- artifact: `9965621555`
- artifact ZIP SHA-256: `b6231f6468e1dcd0965bc9432a77c45b9baac6edfeb6f28c4a9ed364769c6682`
- result JSON SHA-256: `06b8d16d9f991d3ca0f9f3bdbfadc441b001f1429859f6d71645b63d1b14477a`
- decision: **`descriptor_auth_compute_debt_bounded_at_v8`**
- frozen V=8 disproof: **passed**

## Results

| versions | old/new persisted control+auth | old/new read hash ops | old/new update hash ops | old/new creation hash ops | mean / worst read hash-input ratio | mean / worst update ratio | mean / worst creation ratio |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 128 / 120 B | 2 / 3 | 2 / 3 | 2 / 3 | 1.2811 / 1.2828x | 1.2811 / 1.2828x | 1.2811 / 1.2828x |
| 2 | 200 / 224 B | 2 / 4 | 2 / 4 | 3 / 6 | 1.2231 / 1.2258x | 1.2231 / 1.2258x | 1.6055 / 1.6089x |
| 4 | 344 / 432 B | 2 / 5 | 2 / 5 | 5 / 12 | 0.9596 / 0.9613x | 0.9596 / 0.9613x | 1.7959 / 1.8044x |
| 8 | 632 / 848 B | 2 / 6 | 2 / 6 | 9 / 24 | **0.6844 / 0.7342x** | **0.6844 / 0.7342x** | **1.6030 / 1.6120x** |

At V=8, selective descriptor authentication therefore reduces bytes fed into SHA-256 on selective reads and one-version updates by about **31.6% on average**, with the worst tested row still reducing them by **26.6%**. This is a real data-traffic reduction, not a gifted cost.

But it is not a free compute win. At V=8:

- persisted control/auth metadata grows from **632 B to 848 B** (`+216 B`, `+34.2%` for this control/auth component);
- selective-read hash invocations grow from **2 to 6**;
- one-version-update hash invocations grow from **2 to 6**;
- creation hash invocations grow from **9 to 24**;
- creation SHA-256 input bytes grow by about **60.3% on average** and up to **61.2%**.

At V=1 and V=2, the tree is a compute loss even on read/update hash-input bytes. The crossover appears only once enough descriptors exist for avoiding the complete-manifest hash to pay for the proof path. At V=4 the read/update input-byte gain is small (~4%); at V=8 it becomes substantial.

## Interpretation

The frozen V=8 disproof is passed: the locality mechanism does **not** merely move all of the read/update data-processing bill elsewhere. It reduces hash input traffic while preserving the previously measured density/access success.

However, hash-input bytes are not wall-clock time. The new design performs more, smaller SHA-256 calls, so function-call/setup costs and implementation details may erase some or all of the modeled read/update gain. Creation clearly becomes more expensive by both bytes hashed and invocation count. This is therefore bounded exported debt, not a speed victory.

The next Builder should attack the shape of the authentication tree rather than tune thresholds. A higher-arity generic descriptor tree is a plausible concept-compression direction: it can reduce stored internal hashes and creation parent-hash work while spending a small, explicit proof-byte increase. Any such experiment must rerun exact reconstruction, corruption rejection, complete persisted bytes, and the unchanged `<=1.20x` authenticated-touch gate. Native wall-clock profiling remains mandatory before promotion to an efficiency claim.

## Claim boundary

Deterministic control-authentication work accounting only. No native wall-clock, peak-memory, full 15-workload, v0.29/v0.30, canonical-wire, portability, or release authority is claimed.
