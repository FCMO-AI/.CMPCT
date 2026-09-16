# R34 regenerable-Deflate same-run phase attribution preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Supersedes R33 only for the residual-runtime attribution question. R33 remains immutable terminal negative evidence.

## Why R34 exists

R32 established a real byte/runtime tradeoff and showed that ordinary-Zstd output was dead while substantial runtime debt remained. R33 attempted to localize that residual debt but failed its frozen cross-run exact-byte/SHA prerequisite: the same bound Git substrate generated a second, internally deterministic archive identity on a different GitHub hosted-runner image.

R34 changes **only** the identity-control strategy needed to answer the same causal question. It does not change R32's mechanism, targets, representation bytes, comparator semantics, reconstruction obligations or phase-owner threshold.

## Frozen question

After removing output-dead ordinary Zstd work, is the remaining create-time debt of the regenerable-Deflate candidate owned by one profiler-visible exclusive-time phase that transfers from the nested source to Full Backups, or is it distributed/below the attribution floor?

## Frozen substrate and targets

- product/corpus substrate: exact blobs already bound by R32 at `0b1f3cd653f0e2489964b93cdd19fa8324adda2e`
- target 1: frozen Full Backups corpus
- target 2: frozen `snapshot_2.cmpct` nested-only source extracted from that corpus
- arms:
  - `release-all-exact`
  - `full-search`
  - `no-ordinary-zstd`
- repetitions: **3 fresh processes per arm per target**

No workload-name/product dispatch may be added. This remains diagnostic-only and earns no release credit.

## Same-run identity law

R34 deliberately does **not** preregister archive bytes/SHA copied from R32. Instead, a result-bearing run is admissible only when all of these hold inside that exact run:

1. each target/arm produces one identical `(archive_bytes, archive_sha256)` pair across all three fresh-process repetitions;
2. every row passes strong verification and reconstructs the frozen source tree;
3. for each target, `full-search` and `no-ordinary-zstd` are exactly byte-identical in all repetitions, re-proving the R32 output-dead inference under the execution environment actually being profiled;
4. for each target, the `full-search`/`no-ordinary-zstd` archive is strictly smaller than `release-all-exact`;
5. the frozen corpus tree and nested member identities match the R32 source contract.

Failure of any item yields `SUBSTRATE_OR_SAME_RUN_IDENTITY_FAILURE`; profiler deltas may not be interpreted.

## Environment fingerprint

The receipt must record, at minimum:

- Python version and implementation;
- `zlib.ZLIB_VERSION` and `zlib.ZLIB_RUNTIME_VERSION` when exposed;
- Python `zstandard` package version;
- OS/platform string;
- `ImageOS` / `ImageVersion` runner environment values when present;
- evidence Git SHA.

This records rather than gifts environmental variance. It does not turn a hosted runner into release authority.

## Frozen profiler/causal law

Use `cProfile` exclusive/internal time, not cumulative wrapper time, with the same product-frame/native-call inclusion rule as R33.

For phase ownership, compare the median profile of `no-ordinary-zstd` against `release-all-exact`. A signature is a transferable localized owner only when:

- nested-only internal-time delta is **>= 0.010 s**, and
- Full Backups internal-time delta is **> 0 s**.

The same signature must satisfy both conditions. Sort localized owners by descending nested internal-time delta.

Terminal grammar:

- `PHASE_OWNER_LOCALIZED` — at least one signature satisfies the frozen exclusive-time transfer law;
- `RESIDUAL_DISTRIBUTED_OR_BELOW_ATTRIBUTION_FLOOR` — identity law passes but no signature does;
- `SUBSTRATE_OR_SAME_RUN_IDENTITY_FAILURE` — any frozen source, reconstruction, determinism, output-dead or strict-byte-benefit prerequisite fails.

## Interpretation law

`PHASE_OWNER_LOCALIZED` authorizes only a lowest-sufficient Forge intervention against the localized phase, followed by a fresh Builder. It is not product or release evidence.

`RESIDUAL_DISTRIBUTED_OR_BELOW_ATTRIBUTION_FLOOR` retires profiler-guided single-owner surgery at this resolution; a new intervention requires new causal evidence rather than threshold tuning.

`SUBSTRATE_OR_SAME_RUN_IDENTITY_FAILURE` blocks attribution and must be diagnosed as Custody/correctness evidence before any runtime conclusion.

The >=10 ms nested threshold, positive Full Backups transfer condition, three-repetition count, arms and same-run identity grammar are frozen after the first result-bearing execution.
