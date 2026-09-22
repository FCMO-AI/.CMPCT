# R33 regenerable-Deflate residual phase attribution — terminal result

Status: **TERMINAL / NEGATIVE CUSTODY RESULT**

R33's frozen grammar is preserved unchanged. The result-bearing execution did **not** authorize phase attribution because its preregistered cross-run byte/SHA identity prerequisite failed.

## Receipt

- workflow run: `33839947373`
- result job: `100920113668`
- evidence head: `b2e7ff4cdf5e1dfd7b75d37c1c9e9304b8fc1331`
- artifact: `9924649389`
- artifact ZIP SHA-256: `4d18e60d5e208cfd02e1f6ab515b543e57f26d7cde5d66b11fff548a4c6d9145`
- terminal decision: `SUBSTRATE_OR_IDENTITY_FAILURE`

The exact R32 Git substrate binding passed before execution. All result rows strong-verified and reproduced deterministically within R33, but none matched the frozen R32 archive bytes/SHA values.

## Exact mismatch

| target | arm | frozen R32 bytes | R33 bytes, all 3 reps | delta | within-R33 deterministic |
| --- | --- | ---: | ---: | ---: | --- |
| Full Backups | `release-all-exact` | 8,088,619 | 8,088,397 | -222 B | yes |
| Full Backups | `no-ordinary-zstd` | 8,056,193 | 8,055,981 | -212 B | yes |
| nested-only | `release-all-exact` | 2,231,160 | 2,231,156 | -4 B | yes |
| nested-only | `no-ordinary-zstd` | 2,197,414 | 2,197,412 | -2 B | yes |

Observed R33 SHA-256 values were likewise stable across all three repetitions but differed from R32:

- Full Backups release: `b5a3ffaff91d972b445f852d9fc0d1b6787e4eec6026000625ad12d91854aa5d`
- Full Backups no-Zstd: `b21b5ddaf9de0c769c4aacdda52059f2d3ddc60c234c2b42eea4e9b66008bee7`
- nested release: `ecccad7fd33cd9b9763cd8dc354e43998913c26ae98dbfb1d421dc087f963de4`
- nested no-Zstd: `4651ec292aaaa6913d803ad48ecd2003d9b5a37a954d677fe53b4904cbb7e171`

The source identities remained bound (`tree_sha256=a823728d98e5882542645e3ab0f777894479cfb3de4dedcec14341fedbb11a05`; nested source SHA-256 `04adcccf11c67cde4e4a917e6619e4e14dfdb29d18db15a23f56a2fb363e5b43`).

## Causal interpretation

This is not evidence that the R32 byte-saving mechanism disappeared, and it is not permission to consume R33's profiler deltas. It is evidence that the R33 prerequisite encoded a stronger cross-run identity assumption than the environment actually guaranteed.

The most concrete observed environmental difference is the GitHub hosted-runner image:

- R32: Ubuntu 24.04 runner image `20260831.293.1`
- R33: Ubuntu 24.04 runner image `20260823.283.1`

Both runs used CPython `3.11.16` and resolved the same visible Python dependency versions, including `zstandard 0.25.0`. Therefore a mutable hosted image / native-library boundary remains a live cause; the evidence does **not** establish which lower-level library owns the byte drift.

The important scientific fact is stronger than an environment guess: R33 produced one deterministic identity inside its own run, while the older R32 run produced another deterministic identity on the same bound Git substrate. Cross-run exact archive identity is therefore not presently an admissible premise unless the binary environment is also frozen.

## Scoped negative constraint

Do not use exact archive bytes/SHA copied from a prior hosted-runner execution as the sole identity gate for this diagnostic family unless the complete byte-affecting runtime/toolchain environment is itself pinned and fingerprinted.

This does **not** relax release determinism. Product/release evidence still owes exact-byte determinism under its declared environment contract. It only rejects an unsupported causal shortcut for the R32/R33 diagnostic chain.

## Terminal decision and reopening predicate

R33 is terminal as `SUBSTRATE_OR_IDENTITY_FAILURE`; its frozen expected bytes, SHAs, arms, repetitions and interpretation remain immutable.

A superseding experiment may reopen residual phase attribution only if it preserves R32's causal question while replacing the unsupported cross-run identity premise with a stronger same-run control, at minimum:

1. fresh-process repetitions remain deterministic within each arm;
2. `full-search` and `no-ordinary-zstd` are byte-identical within the same run on both targets, proving the Zstd-elision arm remains output-dead;
3. every arm strong-verifies and reconstructs the same frozen source tree;
4. the no-Zstd/full-search arm remains strictly smaller than the exact release arm on both targets;
5. the execution records the relevant runtime/environment fingerprint;
6. phase ownership still uses exclusive/internal time and the frozen >=10 ms nested + positive-full transfer rule.

Until that superseding receipt succeeds, R32's residual runtime debt remains open and **no phase owner is authorized**.
