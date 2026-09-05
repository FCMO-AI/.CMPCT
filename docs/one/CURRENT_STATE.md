# CMPCT ONE — Current Research State

**Status:** `ONE-G0.2` active; semantic substrate exact; shift-invariant reuse opportunity survives; tail-aware segmented minimizer maintenance is promoted as the current encoder-discovery baseline; sparse record-suffix compression is retired  
**Branch:** `research/cmpct1`  
**Control branch:** `research/cmpct1-cleanroom`  
**Research PR:** #88 (draft; base is the frozen v0.30 comparator branch)  
**Experimental version:** `ONE-G0.2`  
**Date:** 2026-09-04

## Read first

1. `docs/architecture/CMPCT_ONE_CANON_v0.1.md`
2. `docs/roadmap/CMPCT_ONE_ENGINEERING_GRID_v0.1.md`
3. this file
4. `docs/CMPCT1_GENESIS.md`
5. normal CMPCT repository authorities required by `AGENTS.md`
6. `docs/one/NEGATIVE_EVIDENCE.md`
7. `docs/one/evidence/ONE_G02_TAIL_SEGMENTED_PROMOTION_2026-09-04.md`
8. `docs/one/evidence/ONE_G02_RECORD_SUFFIX_NEGATIVE_2026-09-04.md`

Do not reconstruct the design from chat history.

## Current decision

CMPCT ONE remains primary during the Genesis window. The reader-visible design remains one representation: **Law + Surprise with selective Crystallization**. Historical mechanisms may inform discovery but may not become a permanent reader-visible codec zoo.

Speed/efficiency is co-equal with density. Charge source traffic, exact-proof traffic, retained/reserved state, derived-state traffic and elapsed compute. Reader discovery is forbidden.

Frozen comparison authorities remain:

- v0.29/main pivot: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30 authoritative integration: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

The full same-input 15-workload Genesis decision comparison is due at/after the first activation on **2026-09-11**. No G0.x microbenchmark substitutes for that decision.

## ONE-01 — semantic substrate

The reader ontology remains six generic relations only: `surprise`, `concat`, `repeat`, `fill`, `xor`, `add8`. There are no opaque legacy-codec opcodes.

The reference evaluator retains cycle, depth, output-byte, work-byte, range, declared-length and root-SHA checks, with an independent tuple oracle and malformed/resource vectors.

Complete-wire G0.1 facts remain: 64 KiB repetition from a 64-byte basis is 137 wire bytes; 64 KiB fill is 69 bytes; a 131,072-byte exact-reuse pair is 65,657 bytes. Tiny framing remains expensive: 16 logical repeated bytes require 74 wire bytes. These are representation facts, not product-superiority claims.

## ONE-03 — fused observation and reuse discovery

### Fused observation survives

The one-pass observer removes one complete source scan versus equivalent separate run/reuse scans. Current hosted evidence shows substantial source-read reduction and a Python elapsed benefit on random/repeated large cases. Coalesced exact proof also removes redundant verification operations on low-entropy repeated inputs while preserving opportunity.

### Selector opportunity survives current falsifiers

The current global hypothesis uses inherited `cmpct-gear-v1` and the **rightmost minimum over a 4,096-position sliding Gear-state window**, alongside bounded local evidence. It is encoder discovery only; survivors compile into generic exact reuse Laws.

It retains the frozen fixed-selector opportunities while additionally recovering:

- 524,288 B from the ordinary one-byte-shifted 512 KiB pair where aligned fixed chunks recover 0 B;
- 8,192 B from the zero-sparse-anchor 8 KiB adversary;
- the same 8,192 B after a one-byte insertion.

Sparse threshold Gear, local+sparse retention and absolute-coordinate gap fallback remain retired for scoped failures in `docs/one/NEGATIVE_EVIDENCE.md`.

### Compute history: monotonic deque -> segmented rehabilitation

The original compiled deque minimizer was about **22.3x–23.1x** slower than Gear-only on 1 MiB large cases, around 90–92 MiB/s versus roughly 2.0 GiB/s Gear-only. Ring-address changes recovered only single-digit percentages and were retired as the primary owner.

The first full prefix/suffix block Builder changed the maintenance algorithm while preserving the exact selector. It produced large mature-input gains but was correctly rejected because the just-enabled 4,160-byte boundary regressed. That rejection remains immutable.

Four-way segmentation then reduced the block-maintenance state and kept the mature-input gain, but its eager suffix construction still paid work at EOF that no future query could use. A frozen eager-vs-tail causal A/B proved that dead suffix construction was the startup debt: at 4,160 B, tail awareness reduced the eager segmented time to about 0.70x while skipping three dead suffix blocks and preserving exact traces, state and source-pass count.

### Promoted baseline — tail-aware four-segment maintenance

A superseding preregistered A/B then re-applied the **original all-case promotion law** to the causally repaired implementation. Nothing about Gear identity, selector semantics, test cases or thresholds was relaxed.

Exact-head source `c40fdb518ba256a44fe0fdbf986e8bdcde0f900a`, workflow `33938347273`, job `101230624486`, artifact `9960981282` (`sha256:5add89250184eadb1ead3e62a9a598025709c195088e9b7a3f4043e4ef193bb6`) passed all 50 ONE tests and the complete independent anchor-trace oracle.

Frozen gate and result:

- every large case required tail-aware elapsed <= 0.70x masked deque: **passed**, observed 0.5370x–0.5654x;
- every tested case required <= 1.10x masked deque: **passed**;
- 4,160-byte just-enabled boundary: masked 12.198 us -> tail 11.467 us, **0.9401x**;
- hostile 16,385-byte shifted-starvation case: 71.648 us -> 66.380 us, **0.9265x**;
- modeled state including Gear: 51,296 B vs masked 67,584 B, **0.7590x**;
- source-byte rescans: zero;
- all emitted anchor traces exact.

Large-case tail-aware throughput in this gate was about **209–211 MiB/s**, versus roughly 113–119 MiB/s for the masked deque. This is encoder-discovery microkernel evidence only, not product-speed evidence.

**Decision:** `promote_tail_aware_segmented_maintenance` as the current exact rightmost-minimum maintenance baseline.

Durable receipt: `docs/one/evidence/ONE_G02_TAIL_SEGMENTED_PROMOTION_2026-09-04.md`.

### Scoped negative — sparse record-minimum suffix change points

The next causal hypothesis asked whether dense suffix **write traffic** was the remaining owner. A record-minimum representation stored only change points in each 1,024-state suffix function and consumed them with a monotone cursor.

Exact-head source `0c204c815c4bb4179ba04fa0049a1e6ac0d3e572`, workflow `33938622782`, job `101231422797`, artifact `9961088338` (`sha256:edd023c6bcf81d943d9e6afc04ad1996e23d2d0c9b241c52891eec8a8cb3d7ab`) passed all semantic tests and matched the independent oracle exactly.

The mechanism did what it claimed mechanically: on every large frozen case record writes fell to only **0.65%–0.74%** of dense suffix entries, roughly a **99.3% write reduction**, with at most 17 records observed per 1,024-state block and only 1.0025x modeled state.

But elapsed time became **25.35%–31.60% slower on every large case** (record/dense-tail 1.2535x–1.3160x), and the 16,385-byte hostile case was 1.2107x. Only the 4,160-byte startup row improved.

**Decision:** `retire_record_suffix_candidate`. Dense suffix writes are not the primary remaining owner. Direct dense indexing is sufficiently regular that sparse cursor/control/dependency cost dominates the write savings. Do not reopen by merely reducing record count further; the tested mechanism already removed ~99.3% of writes and lost.

Durable receipt: `docs/one/evidence/ONE_G02_RECORD_SUFFIX_NEGATIVE_2026-09-04.md`.

### Other current negative constraints

- Ring addressing is not the primary remaining owner; isolated wrap/mask tuning is retired.
- Two 2,048-state segments preserve exact semantics but did not produce a consistent speed gain over four segments and used about **1.1588x** the four-segment state. Do not promote the simplification without new causal evidence.
- Under forced collision pressure, bounded multi-source buckets recovered no additional reuse in the frozen collision probes while exporting extra state/proof traffic. One-source retention remains preferred under the tested regime.

## Remaining compute debt / next decisive action

Tail-aware segmented maintenance is now the strongest evidence-backed implementation of the current selector, but it is not compute-cheap enough to declare the selector solved. The previously measured dense-segmented residual was still roughly **9.18x–9.33x Gear-only** on large cases before proof, extension, Law selection or emission. The tail repair closes startup debt but does not erase this large residual.

The record-suffix negative narrows the search: **dense suffix write volume is not the owner**. The next experiment should profile/decompose the promoted tail-aware kernel's remaining critical path without changing selector semantics. Priority hypotheses are direct per-position candidate comparison/selection, derived-state construction/read traffic, block-transition bookkeeping, and missed compiler/SIMD fusion opportunities. A new Builder should target one measured owner and preserve the current exact oracle, zero source rescans and all-case gate.

Do not integrate the selector into the normal observer as a product-speed claim until this residual has either been materially reduced or its opportunity value is shown to justify its charged compute under the broader ONE objective.

## Product laws that remain non-borrowable

The ONE campaign does not supersede existing product invariants. Eventual product evidence must still preserve zero-byte release regression tolerance, same-runner timing policy, exact reconstruction, bounded hostile-input behavior, selective-read locality/amplification, integrity/recovery semantics, native/shared-reader parity and platform portability. G0.2 discovery microbenchmarks do not grant authority over those gates.

## One-week decision boundary

At/after the first scheduled activation on **2026-09-11 America/Mexico_City**, perform the full same-input Genesis comparison against frozen v0.29 and the strongest fair deferred-v0.30 evidence, preserving all 15 workloads and size/speed/access/resource accounting.

This file is mutable handoff state. Architecture Canon and Engineering Grid remain the stable design authorities.
