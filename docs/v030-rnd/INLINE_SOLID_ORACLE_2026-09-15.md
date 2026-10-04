# v0.30 inline-solid oracle decision — 2026-09-15

Status: **research-only negative for universal promotion; scoped seed preserved**. This receipt grants no release credit and changes no release threshold.

## Question

Can a simple exact-tree physical organization — one inline metadata+content payload compressed as one solid Zstd frame — simultaneously beat ordinary ZIP/Deflate and tar+Zstd-19 on both complete stored bytes and charged creation time across all 15 frozen domination workloads?

The oracle deliberately prices source scan, inline metadata packing, payload SHA-256, compression, and archive write once per candidate. Extraction is exact-tree verified. It compares `inline-path` and `inline-ext`, Zstd levels 1/3/6/9/12/15/19, and 0/4-thread modes where applicable.

## Exact receipt

GitHub Actions run `34933162829`, artifact `v030-inline-solid-58cbd9bd08c7473ce1872a7582c3b1eacc0b7f68`, exact candidate head `992d86760007181d81d6ce3393d3a3cf6256c67e`.

Summary from `cmpct-v030-fast-solid-inline-oracle-v3`:

- 15 workloads tested; every candidate selected below was exact-tree verified.
- Only **6/15** workloads had a candidate that was strictly smaller than both ZIP and tar+Zstd-19 **and** strictly faster to create than both.
- **11/15** workloads had an inline-solid candidate that at least matched or beat tar+Zstd-19 size; therefore the representation has real size headroom, but that headroom often requires expensive Zstd-19 work.
- Aggregate closest remaining tar+Zstd-19 size gap across all workloads: **10,702 B**; maximum single-workload gap: **5,306 B**.
- Aggregate closest remaining ZIP-create gap: **31.176972436 s**. This is the decisive universal-promotion blocker.
- Viable workloads: `neutral_hostile_v1/07_incompressible_and_encrypted_like`, `neutral_hostile_v1/08_many_tiny_files`, `neutral_hostile_v1/10_large_mixed_binary`, `resemblance_hostile_v1/01_shifted_versions`, `resemblance_hostile_v1/02_false_neighbors`, and `resemblance_hostile_v1/05_incompressible`.

The largest creation losses are not packing overhead. For example, `neutral_hostile_v1/04_analytics_and_database` packs in ~0.00875 s but needs the level-19 candidate at ~13.979 s versus ZIP at ~1.357 s; `05_logs_and_telemetry` packs in ~0.00622 s but the closest size-winning candidate creates in ~7.424 s versus ZIP at ~0.637 s. The dominant exported cost is high-level compression, not metadata framing.

## Decision

**Retire the universal inline-solid family as a direct 15/15 domination route.** The experiment falsifies the useful version of the hypothesis: merely changing the physical organization to one inline solid frame does not remove the compression-level tradeoff. Tuning packing, thread count, or nearby framing details cannot plausibly erase the measured multi-second ZIP-create deficits while retaining Zstd-19 size on the hard compressible workloads.

Preserve the representation as a **scoped portfolio seed**, not a release mechanism. Six workloads already show simultaneous size/create wins and eleven show size competitiveness. Any rehabilitation must therefore answer a different question: can a cheap, generic, benchmark-identity-free admission rule identify the regimes where low/mid-level inline-solid already dominates, while fallback preserves current product semantics and exported audition cost stays bounded? That is materially different from trying to tune the same universal solid frame until all 15 turn green.

## Strongest self-critique / claim boundary

This oracle does **not** prove that solid organization is useless, nor that a different compressor, transform-before-solid representation, learned/generic level predictor, or bounded portfolio cannot exploit the seed. It also does not establish production filesystem-semantic completeness beyond the oracle's exact-tree contract. It proves only that this tested inline-solid family, under the charged creation boundary and tested Zstd level/thread sweep, is not a universal 15/15 route.

## Next implication

Do not spend another cycle threshold-gardening this family. Near-term product work should stay on the measured canonical runtime bottleneck (especially ML decode/extract) unless a new representation-level mechanism can move the size/speed frontier rather than merely select another Zstd level. If inline-solid returns, require a preregistered generic admission mechanism and held-out transfer/hostile controls before productization.