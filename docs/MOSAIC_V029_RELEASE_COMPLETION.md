# CMPCT v0.29.0 — Mosaic campaign completion handoff

Status: **release-candidate research-engine milestone; canonical format r24 unchanged**

This document closes the v0.29 Mosaic / Residual Program Packing campaign as a durable zero-chat-history
handoff. It is subordinate to `docs/FORMAT.md` for canonical archive semantics and to
`docs/PERFORMANCE_RELEASE_GATE.md` for release policy.

## Accepted mechanism

The accepted research mechanism is attempt #5:

- bounded multi-root Mosaic Placement;
- Residual Program Packing over qualifying delta residuals;
- exact inherited v0.28 fallback when the research graph is not smaller;
- the accepted single-file fast-reject policy;
- the byte-identical parallel portfolio scheduler exposed through
  `experiments/entropygraph_v029_release.py`.

The experimental graph magic remains `CMPNX11`. It is **not** revision-24 syntax and is not accepted by
the canonical r24 reader.

## Release evidence

### Portable direct-base frontier

Across 15 deterministic inherited-frontier workloads:

- v0.28: **137,550,416 B**
- v0.29 attempt #5: **137,501,815 B**
- saving: **48,601 B (0.035333%)**
- improved: **2/15**
- regressed: **0/15**
- exact v0.28 fallback: **13/15**

This is a conservative portfolio result. The release does not claim that attempt #5 wins broadly; it
claims that it adds two verified wins while refusing deterministic size regressions.

### Mechanism hostile suites

Across the dedicated v1+v2 attempt-5 suites:

- v0.28: **14,829,232 B**
- attempt #5: **14,175,654 B**
- reduction: **4.407362%**
- improved / regressed: **9 / 0** across 18 workloads.

### Matched structural aggregate

On the deterministic 724-file / 93,526,384-byte resemblance-hostile tree:

- attempt #5: **47,147,764 B**
- 7z/LZMA2: **47,430,343 B**
- solid tar/Zstd-19: **47,065,652 B**
- ZPAQ m5: **47,062,639 B**

Attempt #5 is **282,579 B smaller than 7z/LZMA2**, but remains **82,112 B larger than solid
tar/Zstd-19** and **85,125 B larger than ZPAQ m5**. These are stored-byte comparisons, not feature-parity
claims.

### Accepted scheduler

The first scheduler proof was invalidated because it targeted obsolete attempt #1 even though its
internal byte-identity check passed. The corrected gate pins engine identity to
`attempt5-residual-program-packing` and uses four balanced ABBA pairs.

Corrected fixed-hostile result:

- sequential median: **182.453859 s**
- parallel median: **97.944072 s**
- saved: **84.509787 s**
- improvement: **46.318443%**
- every pair cleared both **>=20%** and **>=5 s**
- selected archive in every pair: **47,147,764 B**
- SHA-256: `9e1d587a15e5499e4b9e7f8352d33f014fdfcb55a18339884942e7887b56d376`
- sequential/parallel archive bytes: **exactly identical**

Footnote: this is a fixed-hostile scheduler result, not a universal speed guarantee. The older portable
generalization record's sequential 2.175x attempt-5/v0.28 creation ratio remains valid evidence for that
separate experiment.

## Rejected mechanisms

Measured but not promoted:

- shared dictionary record context;
- one-hop reference context;
- bounded per-record LZMA2;
- bounded solid LZMA2;
- local pair fusion;
- attempt #6 locality-budget compiler;
- attempt #7 cross-base residual packing;
- reversible columnar residual encoding.

Each either failed its preregistered materiality gate, saved nothing, or remained behind the accepted
portfolio after full-artifact accounting.

## Canonical boundary

v0.29.0 advances the **project/research engine**. It does not advance the canonical on-disk revision.

Any future promotion of CMPNX11 semantics must separately earn:

- canonical reader/writer integration;
- conformance vectors;
- malformed/resource-limit tests;
- native reader parity;
- recovery semantics;
- portability/interoperability coverage;
- direct-base canonical performance evidence.

## Durable sources

See:

- `docs/releases/v0.29.0.md`
- `benchmarks/history/2026-08-17-mosaic-v029-full-artifact-attempt5.json`
- `benchmarks/history/2026-08-17-mosaic-v029-generalization-v3.json`
- `benchmarks/history/2026-08-17-mosaic-v029-attempt7-crossbase-structural-reject.json`
- `benchmarks/history/2026-08-17-mosaic-v029-parallel-portfolio-pass-v1.json` (invalidated old engine)
- `benchmarks/history/2026-08-17-mosaic-v029-parallel-portfolio-attempt5-v2.json`
- `benchmarks/history/2026-08-17-mosaic-v029-public.json`

Footnote: the invalidated scheduler record remains in history intentionally. Keeping the false-positive
path visible is part of the campaign's evidence, because future scheduler work must prove *engine
identity* as well as archive-byte identity.
