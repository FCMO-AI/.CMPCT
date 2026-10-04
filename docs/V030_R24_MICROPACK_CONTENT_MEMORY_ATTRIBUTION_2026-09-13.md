# v0.30 r24 content-economic micro-pack memory attribution — 2026-09-13

Status: **research evidence; no release credit**

Exact measured head: `03c6c7ddb91a9dad66c73a2cf25b84ab2f562e35`

Hosted run: `34742863989`

Receipt artifact: `v030-memattr-dpeak4096-dmicro3424-dbuild7048-tpeak8588-tmicro3368-tbuild-2892-aud181-647-rej0-0-03c6c7ddb91a9dad66c73a2cf25b84ab2f562e35`

Artifact digest: `sha256:0651c0a1716c4e2ba45714b79e747df19a4254609414f08a8f29d068da7f3c0a`

Scientific verdict: **`CONTENT_MEMORY_ATTRIBUTION_COMPLETE`**

## Question

The preceding fresh-process economics referee showed content-economic peak RSS above same-grammar independent by roughly 3.5 MiB on Developer and 8.3 MiB on Tiny Files. `ru_maxrss` is a process high-water mark, so it cannot distinguish retained product/build state from transient discovery/compression traffic. This referee measured current Linux `VmRSS` after major Builder phases in separate fresh workers while retaining `ru_maxrss` as the high-water control.

No policy, pack geometry, admission threshold or codec setting was changed.

## Result

Artifact-bound content-minus-independent deltas:

| Source | peak RSS delta | post-micro-pack current RSS | post-build current RSS | auditions | rejected groups |
| --- | ---: | ---: | ---: | ---: | ---: |
| Developer | **+4,096 KiB** | **+3,424 KiB** | **+7,048 KiB** | 181 | 0 |
| Tiny Files | **+8,588 KiB** | **+3,368 KiB** | **-2,892 KiB** | 647 | 0 |

## Interpretation

The two workloads expose different mechanisms.

**Tiny Files:** the large peak increase is mostly transient. Current resident memory after micro-pack admission is only about +3.3 MiB and by post-build is **below** the independent control even though the process high-water remains +8.6 MiB. Treating the high-water number as retained product state would therefore be wrong. The likely debt is temporary discovery/encoding traffic or allocator high-water, which should be attacked by reducing redundant materialization/recompression rather than by changing archive representation.

**Developer:** the delta is not only transient. It is already visible immediately after micro-pack construction and grows to +7.0 MiB in current resident state post-build. This requires a retained-object attribution before promotion; simply optimizing temporary Zstd buffers would not be sufficient.

A particularly useful diagnostic is that these exact surfaces performed **181** and **647** content-economics auditions respectively, while rejecting **zero** groups in both. This does not justify deleting the admission proof globally—prior origin/hostile evidence did contain rejected groups—but it identifies redundant proof traffic on these shapes and motivates a causal reuse/cheap-gating investigation.

## Next action

1. Attribute retained Developer memory by object class / candidate population before introducing an optimization.
2. For Tiny, test whether audition compression can avoid duplicate materialization or reuse compression work without changing the strict byte-economic decision.
3. Keep RSS credit at zero until an exact fresh-process rerun shows a reproducible reduction. This receipt is diagnostic evidence only.
