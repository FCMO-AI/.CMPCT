# r25 PrefixGraph-isolated r24-prebuild barrier RSS result

Status: **ACCEPTED SCOPED NEGATIVE / Forge-Custody / no release credit**

This record preserves the result-bearing execution of the frozen `R25_PG_ISOLATED_R24_PREBUILD_BARRIER_RSS_PREREG.md` experiment. The experiment changes no production source, representation bytes, selector, grammar, locality/decode-unit rule, integrity/recovery condition, product floor, competitor setting, release threshold or publication state.

## Authority

- source commit: `0d2e5d2dacce5d79962fc868780a5fa4765847e6`
- workflow run: `33616543545`
- substantive job: `100203579973`
- artifact: `v030-r25-pg-isolated-r24-prebuild-barrier-0d2e5d2dacce5d79962fc868780a5fa4765847e6`
- artifact id: `9841401578`
- artifact digest: `sha256:6cddbbc771d18f33cae9a28d6eff1ed135f866abe05d12bfc30d7b05668d31ec`
- schema: `cmpct-v030-r25-pg-isolated-r24-prebuild-barrier-rss-v1`
- experiment valid: `true`
- worker failures: `0`
- release credit: `false`

All three AB/BA/AB pairs satisfied the frozen identity contract: exact repaired Shifted source identity, exact canonical semantic owners, one successful disposable PrefixGraph child, G0-G4 retained in the parent, exact r24-prebuild barrier behavior, canonical reuse of the same prebuilt r24 artifact, restored bindings, and identical selected representation/archive identity/tree across arms.

## Exact result

| Metric | inherited overlap | r24-prebuild barrier |
|---|---:|---:|
| Median whole-process-tree peak RSS | **289,048 KiB** | **286,960 KiB** |
| Median product wall time | **68.8869 s** | **69.9065 s** |
| Peak RSS repetitions | 289,920 / 289,048 / 288,668 KiB | 286,852 / 286,960 / 287,160 KiB |

The completion barrier reduced median whole-process-tree peak RSS by only **2,088 KiB / 0.72237%**. It increased median wall time by **1.48012%** (`1.01480x`).

The frozen decision rule was >=20% for support, <10% for retirement and 10-20% for ambiguity. The observed **0.72237%** is therefore unambiguously:

**`R24_PREBUILD_OVERLAP_RETIRED`**

## Causal interpretation

Under the exact PrefixGraph-isolated Shifted regime tested here, overlap between the already-started genuine-r24 prebuild and later r25 construction is **not a primary owner of the residual ~289 MiB product peak**. Waiting for the exact existing prebuild before allowing later construction recovers only about 2 MiB of peak RSS while slightly worsening wall time.

This closes another scheduler/lifetime hypothesis. It does not say genuine-r24 construction has zero memory cost, nor does it generalize beyond this changed topology. It says further r24-prebuild barriers are not justified as the next Forge intervention for the current residual Shifted memory red.

## Scoped negative / reopening predicate

Do not revisit r24-prebuild overlap as the primary Shifted RSS explanation unless the r24 prebuild implementation, candidate composition or lifetime topology materially changes, or exact allocation/heap evidence identifies a large r24-owned allocation class capable of overturning the measured <1% effect. Runner noise is not a reopening predicate.

## Next Forge implication

Follow the preregistered terminal direction: move from scheduler permutations to **allocation/heap ownership inside the remaining parent r25/product state**. The next experiment should identify a live allocation class large enough to explain a material fraction of the ~289 MiB peak before any Builder change. Preserve the proven PrefixGraph process-isolation win and continue charging complete product bytes, wall time, correctness and portability.
