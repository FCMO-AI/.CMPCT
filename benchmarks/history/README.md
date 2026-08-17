# Benchmark history

This directory contains **durable public benchmark records** for CMPCT. Benchmark conclusions must
not live only in chat, issue comments, terminal scrollback, or prose summaries.

## Current public records

- `2026-08-14-zip-parity-v024.json` — reproducible CMPCT-vs-Python-ZIP parity evidence with explicit library/CLI timing layers and semantic mismatch notes.
- `2026-08-14-raw-chunk-streaming-parity.json` — follow-up shared-runner evidence for the large-binary extraction frontier and related parity checks.
- `2026-08-16-entropygraph-v025.json` — public neutral/hostile EntropyGraph research frontier with ZIP/Zstd/Deflate and solid-Zstd comparison evidence for that exact historical workload set.
- `2026-08-16-entropygraph-v028.json` — EntropyGraph II release-causality record plus matched whole-suite structural competitor sweep.
- `2026-08-17-entropygraph-v028-category.json` — fresh same-lifetime per-workload CMPCT vs solid tar+Zstd-19 and ZIP/Deflate-9 category evidence. All 15 workloads are retained, including Zstd losses; this record is intentionally distinct from whole-suite aggregation and canonical ZIP execution parity.
- `2026-08-17-zip-parity-v0280.json` — current v0.28 canonical executable CMPCT-vs-ZIP ABBA/parity evidence.

Footnote: the v0.28 category record measures CMPCT and both category baselines while each generated
workload tree is still alive. This avoids pretending that a separately regenerated office/media tree is
byte-identical when producer metadata can differ across runs. Its tree hashes are row-local provenance;
whole-suite structural totals and direct-base release totals retain their own separate aggregation
contracts.

The earlier private development campaign materially influenced CMPCT's architecture, but its private
corpus identity and private artifact provenance are intentionally **not** part of this public benchmark
archive. Generalized technical conclusions remain in `docs/HISTORY.md` and `docs/RESEARCH_LOG.md`.

## Required fields for future benchmark records

Future result files should record, when known:

- CMPCT Git commit and format revision;
- benchmark harness Git commit;
- corpus generator/version and content hashes or reproducible seed;
- CPU model and core/thread count;
- RAM and storage device;
- OS/kernel and filesystem;
- Python/native compiler/runtime versions;
- Zstd/Deflate/other codec library versions;
- archive/codec settings;
- process-start vs in-process timing;
- cold/warm cache semantics;
- integrity work included;
- filesystem metadata restoration semantics;
- durability/fsync semantics for mutation tests;
- repetition count and statistic reported;
- raw measurements when practical, not only medians;
- any known semantic mismatch in the comparison.

## Benchmark acceptance rule

A result may guide public encoder policy only when the workload is reproducible and the comparison has
equivalent or explicitly qualified semantics. A benchmark where CMPCT loses is valuable and should be
preserved.

Private development data may still be used locally as a regression signal, but must not be copied here
unless it has been deliberately sanitized and made independently publishable under
`docs/PUBLIC_SURFACE.md`.
