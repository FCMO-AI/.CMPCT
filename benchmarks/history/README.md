# Benchmark history

This directory contains **durable benchmark records** for CMPCT. Benchmark conclusions must not live only in chat, issue comments, terminal scrollback, or prose summaries.

## Files

- `2026-08-13-development-campaign.json` — machine-readable reconstruction of the complete surviving first CMPCT development campaign, including precursor Seekable-Zstd experiments, indexed/adaptive prototypes, v0.5–v0.24-era checkpoints, Hermes and synthetic/adversarial corpora.

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

A result may guide encoder policy only when the workload is reproducible and the comparison has equivalent semantics. A benchmark where CMPCT loses is valuable and should be preserved.

Historical records imported from the pre-repository research campaign are explicitly marked as such and are **regression clues, not public performance guarantees**.
