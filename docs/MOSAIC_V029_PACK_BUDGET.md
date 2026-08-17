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

A bounded partition solver can use the **same <=8x weighted read budget** more efficiently by starting
from each existing global plan and selectively coarsening only adjacent similarity-ordered groups whose
exact compressed-byte saving pays for their extra decoded bytes.

Attempt #6 deliberately adds a stronger bound than the inherited planner: any *newly selected* physical
partition must also remain **<=8x for every direct-root member individually**. The current attempt-5
archive remains a byte-for-byte fallback when the stricter partition cannot win safely.

The mechanism can therefore improve physical root-pack bytes without requiring a new reader grammar,
deeper dependencies, new integrity semantics or a larger 2 MiB decode unit.

**Disproof:** reject the mechanism if it cannot improve at least two inherited-frontier workloads by an
additional 0.05% of the exact aggregate v0.28 bytes, if any accepted attempt-5 row grows, if weighted or
per-member read amplification exceeds 8x on a newly selected partition, or if bounded search caps are
exceeded on rows where savings are claimed.

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

The experiment:

- preserves v0.28's similarity ordering;
- starts from each existing global pack plan that already satisfies the <=8x weighted budget;
- allows only contiguous coarsening up to the existing 2 MiB physical ceiling;
- measures every proposed merged record with the real compressor before using its byte cost;
- keeps only exact non-dominated `(decoded bytes, stored bytes)` states;
- rejects a source plan rather than approximating if the Pareto frontier exceeds 4,096 states;
- bounds source plans to 512 groups and one merge to at most 64 source groups;
- requires every newly selected group to be <=8x for every member as well as <=8x in the workload-weighted metric;
- keeps the historical global plan on ties;
- builds the accepted attempt-5 archive separately and uses it as the final byte-for-byte fallback.

Footnote: the search cap is a safety boundary, not a tuning parameter. A capped row is negative evidence;
the benchmark must not silently increase the cap only on workloads where doing so improves the result.

## Preregistered research gate

The oracle is interesting enough for a production-shaped implementation only if all are true on the
same repaired 15-workload inherited frontier:

- v0.28 identity drift rows: **0**;
- accepted attempt-5 byte drift rows: **0**;
- workload regressions versus attempt #5: **0**;
- additional aggregate saving versus attempt #5: **>=0.05% of exact v0.28 aggregate bytes**;
- additional workloads improved versus attempt #5: **>=2**;
- allocator weighted pack read amplification: **<=8x**;
- allocator per-member physical amplification: **<=8x** on every newly selected partition;
- selected archive strong-verifies with the unchanged attempt-5 reader.

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
