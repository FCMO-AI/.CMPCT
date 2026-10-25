# O45b — Held-out filesystem semantics, before implementation

**Date:** 2026-10-25 UTC. **Scope:** independent replication of O45 on a materially different Linux filesystem, **not** a revision of O45's original prediction.

## Evidence already observed

Original O45 hosted [Actions 40154913865](https://github.com/FCMO-AI/.CMPCT/actions/runs/40154913865), implementation head `d0b48904f94792f12dfb04807be55511c6013454`, artifact `12583658630` (ZIP digest SHA-256 `68580c4321cfbfe2ea8694689ade71863445f334bead12dfd57a55649755090e`), correctly reported **NOT_SUPPORTED_ON_THIS_HOST**. Its five authentic Builder passes verified source integrity, reconstructability, a 159 B complete archive increase, and `S_SPARSE -> S_CDC`; importantly, the hosted `SEEK_DATA` changed from 8,384,512 to 0 after `posix_fallocate`, so it did **not** prove a false-negative `st_blocks` proxy relative to that host's own hole oracle.

An independent local Linux container lower-rung probe on `/tmp`, `/mnt/data`, and `/dev/shm` (not CMPCT product evidence) instead observed `st_blocks` 8→16,384 while `SEEK_DATA` remained 8,384,512. The host difference is materially decision-changing, not a reason to relabel the first hosted result.

## New question, prediction and controls

Does the *same unchanged* original source-exact Builder and original five-arm O45 instrument produce the alleged allocation/SEEK_DATA divergence on a Linux **tmpfs** scratch root? Run the original five-arm test under `/dev/shm`, keeping archives outside the corpus within the chosen scratch root, rather than modifying input bytes or any benchmark evaluator. Then check `st_blocks`, `SEEK_DATA`, O42 semantic witness, exact physical storage kinds, full archive bytes and all three strong roundtrip operations.

- If tmpfs shows A and B with identical `SEEK_DATA` but st_blocks above/below the cap, and original Builder changes to `S_CDC`, report a **filesystem-specific positive** (not a universal Linux guarantee).
- If tmpfs reports `SEEK_DATA` change too, preserve a second negative and retire this specific proxy false-negative route until a materially new filesystem mechanism appears.
- If tmpfs is unavailable/too small or the kernel reports unsupported operations, classify infrastructure/capability limit, not a product result.

## Disproof and evidence

Re-run original source-exact Builder/Reader and original independent JSON audit; no new codec/source/representation logic. **No modification to O45's historical output or frozen comparison.** A new workflow job/step should record both original and tmpfs results separately. Do not count administrative success as the positive; classification comes from recorded `SEEK_DATA`, `st_blocks` and storage kinds. Preserve false-green defenses, real artifact and exact HEAD.

Linux `lseek(2)` explicitly states `SEEK_DATA/SEEK_HOLE` are not guaranteed to report physically allocated holes exactly (https://man7.org/linux/man-pages/man2/lseek.2.html). This experiment addresses that host dependency; it cannot define portable physical-topology semantics. Any potential product fix must account for the added file-descriptor/seek costs, platform differences and nonzero maintenance burden.

**No product/release credit; shared Discovery Engine state remains owned by PR #240.**
