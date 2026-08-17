# Mosaic v0.29 — Locality Budget Compiler oracle

Status: **preregistered research attempt / no v0.29.0 claim / canonical revision 24 unchanged**.

## Problem and baseline

Accepted attempt #5 materially clears the dedicated 18-workload full-artifact campaign, but on the
inherited 15-workload v0.28 frontier it saves only 48,601 bytes (0.03533%) and improves 2/15 workloads.
That is useful evidence, not enough by itself to spend a scarce numeric revision.

The direct-root pack planner inherited from v0.28 auditions one global physical ceiling for an entire
workload: 64, 128, 256, 512, 1024 or 2048 KiB. Every direct-root region therefore receives the same
context policy even when some regions compress profitably with larger context and others need small
selective-read units.

## Hypothesis

A bounded physical planner can spend the **same <=8x read budget** more efficiently by preserving the
inherited similarity order but merging only adjacent root groups whose exact compressed-byte saving pays
for the extra decoded context.

Attempt #6 starts from independent direct roots and auditions two deterministic policies: one prioritizes
absolute stored-byte saving, the other saving per additional decoded byte. Exact final archive bytes—not
the heuristic score—decide whether either candidate can replace attempt #5.

Any newly selected physical partition must remain **<=8x both in the workload-weighted metric and for
every direct-root member individually**. The current attempt-5 archive remains a byte-for-byte fallback
when the stricter planner cannot win safely.

**Disproof:** reject the mechanism if it cannot improve at least two inherited-frontier workloads by an
additional 0.05% of the exact aggregate v0.28 bytes, if any accepted attempt-5 row grows, if weighted,
per-member or final selected pack read amplification exceeds 8x, or if bounded search/probe caps are
exceeded on rows where savings are claimed.

## Pre-evidence design correction

The first code draft used a dynamic program over many possible contiguous intervals. It was rejected in
review **before any attempt-6 benchmark result existed** because its bounded worst case still implied too
many level-19 compression probes on medium workloads. Git history preserves that draft.

The active oracle uses agglomerative adjacent merges with an exact cost cache. Re-scanning old neighbor
pairs is cheap because their compressed cost is cached; after a merge, only the new local boundaries need
new physical compression measurements in practice. This keeps the experiment falsifiable without turning
encoder brute force into the source of an apparent compression win.

## Why this attempt precedes other ideas

Three mechanism classes were considered after attempt #5:

1. **Cross-base residual-program packing.** Semantically plausible because every packed delta descriptor
   already carries its own direct `base_id`, but the accepted generalization evidence shows residual
   programs are small enough that physical recipe consolidation alone has limited byte ceiling.
2. **Columnar delta-program coding.** Separating control/address/literal streams may lower recipe entropy,
   but it adds a new physical representation and parser surface before simpler placement economics are
   exhausted.
3. **Physical integrity-field deduplication.** The research grammar carries payload Merkle leaves plus
   physical logical hashes/CRC and node/file hashes. Removing a provably redundant commitment could save
   per-record metadata, but it changes the byte grammar and needs a separate recovery/integrity proof.

The Locality Budget Compiler is tested first because it can create a strict Pareto improvement while
leaving the attempt-5 reader completely unchanged.

## Solver contract

The active experiment:

- preserves v0.28's direct-root similarity ordering exactly;
- starts each strategy from independent root groups;
- considers only adjacent physical merges;
- measures each newly encountered group with the real compressor before using its byte cost;
- accepts only strictly positive stored-byte merges;
- never exceeds the existing 2 MiB physical ceiling;
- tracks the exact historical weighted decoded-byte metric and keeps it <=8x;
- requires every newly selected group to be <=8x for every member individually;
- caps one strategy at 2,048 roots and 8,208 exact physical-cost probes;
- auditions two deterministic priorities (`bytes` and `efficiency`) and lets exact final bytes choose;
- keeps the historical global plan on exact ties;
- builds the accepted attempt-5 archive separately and uses it as the final byte-for-byte fallback.

Footnote: search/probe caps are safety boundaries, not tuning parameters. A capped row is negative
evidence; the benchmark must not raise a cap only because a particular workload would then improve.

## Preregistered research gate

The oracle is interesting enough for a production-shaped implementation only if all are true on the
same repaired 15-workload inherited frontier:

- v0.28 identity drift rows: **0**;
- accepted attempt-5 byte drift rows: **0**;
- workload regressions versus attempt #5: **0**;
- additional aggregate saving versus attempt #5: **>=0.05% of exact v0.28 aggregate bytes**;
- additional workloads improved versus attempt #5: **>=2**;
- allocator weighted pack read amplification: **<=8x**;
- allocator per-member physical amplification: **<=8x**;
- final selected pack read amplification after Mosaic placement: **<=8x**;
- selected archive strong-verifies with the unchanged attempt-5 reader.

The 0.05% threshold is enforced exactly as the integer relation `additional_bytes * 2000 >= v028_bytes`.
Passing this gate does **not** authorize v0.29.0.

## Revision-worthiness ratchet

After a research pass, replace the double-build oracle with a single integrated planner and remeasure
creation cost. A numeric v0.29 proposal still needs the wider campaign evidence plus at least one
revision-sized performance result, such as:

- >=0.5% aggregate improvement over exact v0.28 across at least three inherited-frontier workloads; or
- a fresh same-run structural-competitor crossing on the resemblance-hostile aggregate (not a comparison
  to stale competitor bytes), with all CMPCT locality, integrity, recovery and portability gates green.

Small optimizer wins remain research history. Numeric scarcity is intentional.

## Evidence policy

The workflow uploads the raw JSON and stdout whether the research gate passes or fails. A failed attempt
must be preserved before the mechanism is replaced. Thresholds, repaired source identities, attempt-5
bytes and v0.28 bytes are immutable inputs to this tranche.
