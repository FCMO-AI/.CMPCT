# Benchmark history

This directory contains **durable public benchmark records** for CMPCT. Benchmark conclusions must
not live only in chat, issue comments, terminal scrollback, or prose summaries.

## Current public records

- `2026-08-14-zip-parity-v024.json` — reproducible CMPCT-vs-Python-ZIP parity evidence with explicit library/CLI timing layers and semantic mismatch notes.
- `2026-08-14-raw-chunk-streaming-parity.json` — follow-up shared-runner evidence for the large-binary extraction frontier and related parity checks.

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
