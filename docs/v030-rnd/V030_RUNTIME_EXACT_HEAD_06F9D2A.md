# v0.30 exact-head runtime authority — 06f9d2a

Status: **DURABLE PRODUCT EVIDENCE / RELEASE BLOCKER PRESERVED**

Source head: `06f9d2a3300780ac01856b5ad427ad718cb3d12c`

Candidate fingerprint emitted by the authority worker: `6ae9ce381e807877d318c9d9bb44fd3fa410456b642ab04fe033c910a0a4ded9`

GitHub Actions authority-v2 run: `35353867602`

Runtime artifact: `v030-authority-v2-runtime-06f9d2a3300780ac01856b5ad427ad718cb3d12c`, artifact id `10551702716`, artifact digest `sha256:fe0f56d0e46f03d493a05002e6ac7402cd12af5ebd8300704f55598727833ed4`.

Generalization artifact: `v030-authority-v2-generalization-06f9d2a3300780ac01856b5ad427ad718cb3d12c`, artifact id `10552260417`, artifact digest `sha256:7b64b682a85813b43df689a7b7275a454438ba3f517acebad8ed036a93aae7e4`.

This record does not grant release credit to later fingerprints. It preserves the exact evidence that made efficiency recovery the dominant engineering problem at this head.

## Direct authority result

The 15-workload generalization job passed. The promoted-product runtime job failed. The failure is therefore not a compression-generalization failure and must not be repaired by weakening the byte contract.

The fresh-process paired runtime gate reported:

| Workload | median create ratio v0.30/v0.29 | median extract ratio v0.30/v0.29 | parent-only max pack RSS ratio |
|---|---:|---:|---:|
| `01_shifted_versions` | 1.14155x | 0.91878x | 2.16621x |
| `05_logs_and_telemetry` | 0.00880x | 1.37782x | 1.42694x |
| `09_ml_artifacts` | 1.39082x | 1.48462x | 1.81800x |

Aggregate gate values were:

- median create ratio: **1.14155x** vs `<=1.10x`;
- maximum workload create ratio: **1.39082x** vs `<=1.25x`;
- median extract ratio: **1.37782x** vs `<=1.10x`;
- maximum workload extract ratio: **1.48462x** vs `<=1.25x`;
- parent-only peak RSS ratio: **2.16621x**, but this RSS interpretation is superseded by the whole-process-tree companion below;
- size regression: **none** on all three runtime targets.

The dominant current product reds are therefore not symmetric. Logs creation is already dramatically faster than the inherited path and must not be disturbed casually; its remaining problem is extraction. ML is red on both creation and extraction. Shifted creation is a smaller but still real aggregate-gate owner, while shifted extraction is already green.

## Whole-process-tree RSS companion changes the diagnosis

The same authority job ran the repository's whole-process-tree RSS companion with the same operation windows and a 10 ms live process-tree sampler. That companion reported:

| Workload | median create ratio | median extract ratio | max whole-tree pack RSS ratio |
|---|---:|---:|---:|
| `01_shifted_versions` | 1.11984x | 0.88134x | 0.98958x |
| `05_logs_and_telemetry` | 0.00889x | 1.37710x | 0.63080x |
| `09_ml_artifacts` | 1.38147x | 1.49751x | 0.72457x |

Whole-process-tree decisive peak RSS passed at **1.00000x maximum** against the `<=1.25x` ceiling. The earlier parent-process-only ratios therefore must not be treated as a real product-memory regression: v0.29 spends substantial memory in child processes that parent `ru_maxrss` does not capture, while the tree sampler does. This is evidence-topology correction, not a weakened threshold; the timing boundary and RSS threshold were unchanged.

## Causal priority

This evidence narrows the highest-value efficiency work to three owners in order of product leverage:

1. **ML create + extract** — largest two-sided runtime debt. A useful intervention must preserve its byte gain and exact semantics while removing enough work to move both ratios materially toward the unchanged release ceilings.
2. **Logs extract only** — creation is already a major win, so broad changes to logs construction are poorly targeted. Attribute reader/extractor work and remove duplicated decode/verification/materialization without sacrificing the promoted inverse representation.
3. **Shifted create** — smaller create debt; extraction is already better than v0.29. Attack only after the larger ML/logs owners unless a shared architectural fix demonstrably covers it.

RSS is **not** the current dominant blocker. Do not spend the primary recovery budget optimizing memory from the parent-only reading unless newer whole-tree evidence reverses this result.

## Strongest negative / self-critique

These ratios establish *where* the release gate is red, not yet *why*. They do not prove whether ML creation debt is search, duplicate traversal, child-process orchestration, compression effort, hashing, publication, or another owner; likewise they do not prove whether ML/logs extraction debt is decode, Python orchestration, verification, filesystem materialization, or startup. A code change justified only by these aggregate ratios would still be premature.

The next decisive instrument should therefore attribute wall/CPU/I/O by semantic phase on the promoted ML and Logs paths under the same exact input and process boundary, then test the largest owner with a paired A/B. The kill rule for a local optimization family is simple: if its optimistic removable budget cannot close a material fraction of the observed 39–50% workload debt, escalate to D2/D3/D4 rather than polishing it.

## Release truth

At this head, v0.30 remains **LOCKED**. Compression/generalization passed; fresh-process runtime failed; whole-process-tree RSS passed. This record is evidence only and does not merge, tag, version-bump, publish, lower a threshold, or authorize promotion.
