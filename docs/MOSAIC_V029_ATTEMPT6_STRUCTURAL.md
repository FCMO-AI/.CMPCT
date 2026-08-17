# Mosaic v0.29 attempt #6 — structural crossing oracle

Status: **preregistered research tranche / attempt-6 inherited-frontier gate remains REJECT / no v0.29.0 claim**.

## Why this tranche exists

The Locality Budget Compiler was already falsified against its own inherited-frontier research gate.  It
saved **68,095 B beyond attempt #5**, improved **3/15** workloads and regressed none, but achieved
**0.049504%** additional saving versus the preregistered **>=0.05%** requirement.  That threshold is not
being changed after the result.

A separately measured product-level question remains.  On the corrected same-run structural hostile
aggregate, accepted attempt #5 measured **47,147,764 B**, while solid tar+Zstd-19 measured **47,065,652 B**
and ZPAQ m5 measured **47,062,640 B**.  CMPCT therefore trails the strongest measured size competitor by
only **85,124 B**, while already beating 7z/LZMA2 by **282,582 B**.

Attempt #6 changes only direct-root physical partitioning and keeps the attempt-5 reader unchanged.  Its
15-workload gains are large enough to justify one explicit test of whether locality-budget placement has
higher leverage when the hostile suite is archived as one complete recursive tree.

## Frozen hypothesis

Generate the resemblance-hostile suite once, archive that exact tree with attempt #6 and every available
structural competitor in one job, and compare exact complete-artifact bytes.

A **structural crossing** exists only if all are true:

- attempt #6 candidate bytes are **<= exact attempt #5 bytes** on the same aggregate;
- the candidate strong-verifies with the unchanged attempt-5 reader;
- selected Mosaic read amplification remains **<=8x**;
- additional residual-program read amplification remains **<=2x**;
- any selected Locality Budget root partition remains **<=8x weighted and <=8x per member**;
- both tar+Zstd-19 and ZPAQ m5 are available with positive same-run byte measurements; and
- CMPCT is **strictly smaller than both** tar+Zstd-19 and ZPAQ m5.

7z/LZMA2, ZIP/Deflate and Borg remain recorded but cannot satisfy this crossing gate because attempt #5
already beat 7z on this workload and ZIP/Borg are materially larger.

## Evidence discipline

- The attempt-6 inherited-frontier gate remains a historical **REJECT** regardless of this outcome.
- Previous competitor bytes are motivation only; the crossing decision uses **same-run** competitor files.
- No corpus, compressor level, semantic label, locality limit or threshold may change after observing the
  structural result.
- The workflow must upload its JSON even when the crossing is false.  A clean miss is durable evidence,
  not CI failure.

## What a crossing would and would not mean

A crossing would make Locality Budget placement materially more interesting because it would remove the
current hostile size deficit without a reader grammar change.  It would **not** by itself authorize
v0.29.0: creation cost, neutral-workload admission, canonical format/native parity, recovery and
portability still need release-shaped evidence.

A miss means this placement optimizer is retained as useful research but should not consume more tuning
budget.  The next representation experiments should move to cross-base residual-program packing or a
bounded columnar residual representation rather than weakening this gate.
