# CMPCT ONE — Current Research State

**Status:** `ONE-G0.2` active; semantic substrate exact; shift-invariant reuse opportunity survives; **counter-based tail-aware four-segment minimizer maintenance is the current encoder-discovery baseline**; post-counter residual profiling and offset-only crossover characterization are active  
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
5. normal CMPCT authorities required by `AGENTS.md`
6. `docs/one/NEGATIVE_EVIDENCE.md`
7. `docs/one/evidence/ONE_G02_COUNTER_BOOKKEEPING_PROMOTION_2026-09-04.md`
8. `docs/one/evidence/ONE_G02_TAIL_SEGMENTED_PROMOTION_2026-09-04.md`
9. `docs/one/evidence/ONE_G02_RECORD_SUFFIX_NEGATIVE_2026-09-04.md`

Do not reconstruct this campaign from chat history.

## Mission remains locked

CMPCT ONE remains primary during the Genesis window. The reader-visible representation remains **Law + Surprise with selective Crystallization**. Historical compressors and mechanisms may teach the encoder useful predictive structure, but they may not become permanent reader-visible codec opcodes.

Speed and compute efficiency are co-equal with density. Charge source traffic, exact-proof traffic, retained/reserved state, derived-state traffic, elapsed compute, selective-read amplification, reconstruction work, failure blast radius and reader complexity. Reader discovery is forbidden.

Frozen comparator authorities remain:

- v0.29/main pivot: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30 authoritative integration: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

The full same-input 15-workload Genesis decision comparison is due at/after the first activation on **2026-09-11 America/Mexico_City**. No G0.x microbenchmark substitutes for that decision.

## ONE-01 — semantic substrate

The reader ontology remains six generic relations only: `surprise`, `concat`, `repeat`, `fill`, `xor`, `add8`. There are no opaque legacy-codec opcodes.

The reference evaluator retains cycle, depth, output-byte, work-byte, range, declared-length and root-SHA checks, with an independent tuple oracle and malformed/resource vectors.

Complete-wire G0.1 facts remain: 64 KiB repetition from a 64-byte basis is 137 wire bytes; 64 KiB fill is 69 bytes; a 131,072-byte exact-reuse pair is 65,657 bytes. Tiny framing remains expensive: 16 logical repeated bytes require 74 wire bytes. These are representation facts, not product-superiority claims.

## ONE-03 — fused observation and reuse discovery

### Fused observation survives

The one-pass observer removes one complete source scan versus equivalent separate run/reuse scans while preserving the same cheap opportunities. Current hosted evidence is reference/Python evidence only; it is not native product-speed authority.

### Current reuse opportunity hypothesis

The global discovery hypothesis uses inherited `cmpct-gear-v1` and the **rightmost minimum over a 4,096-position sliding Gear-state window**, alongside bounded local evidence. Survivors compile into generic exact reuse Laws.

It retains the frozen fixed-selector opportunities while additionally recovering:

- 524,288 B from the ordinary one-byte-shifted 512 KiB pair where aligned fixed chunks recover 0 B;
- 8,192 B from the zero-sparse-anchor 8 KiB adversary;
- the same 8,192 B after a one-byte insertion.

Sparse threshold Gear, local+sparse retention and absolute-coordinate gap fallback remain retired under the scoped conditions recorded in `docs/one/NEGATIVE_EVIDENCE.md`.

## Compute convergence history

### Deque baseline

The original compiled monotonic-deque minimizer was about **22.3x–23.1x** Gear-only on 1 MiB large cases, roughly 90–92 MiB/s versus about 2 GiB/s Gear-only. Ring-address tuning recovered only single-digit percentages and was retired as the primary owner.

### Prefix/suffix rehabilitation

A causally different prefix/suffix maintenance family preserved the exact selector. The first full-block Builder won on mature inputs but was rejected because the just-enabled 4,160-byte boundary regressed. Four-way segmentation reduced state; tail-aware suffix construction then removed EOF work that no future query could use.

Exact source `c40fdb518ba256a44fe0fdbf986e8bdcde0f900a`, workflow `33938347273`, job `101230624486`, artifact `9960981282` promoted tail-aware four-segment maintenance:

- large ratios vs masked deque: **0.5370x–0.5654x**;
- 4,160 B boundary: **0.9401x**;
- hostile 16,385 B: **0.9265x**;
- modeled state including Gear: **0.7590x** masked;
- source rescans: zero;
- anchor traces exact;
- large throughput about **209–211 MiB/s**.

Receipt: `docs/one/evidence/ONE_G02_TAIL_SEGMENTED_PROMOTION_2026-09-04.md`.

### Sparse suffix records are retired

A record-minimum suffix representation removed about **99.3%** of dense suffix writes but became **25.35%–31.60% slower on every large case**. Direct regular indexing beat sparse cursor/control/dependency overhead. Do not reopen this family merely by reducing record count further.

Receipt: `docs/one/evidence/ONE_G02_RECORD_SUFFIX_NEGATIVE_2026-09-04.md`.

## Current promoted baseline — monotone block counters

The next causal hypothesis isolated block-coordinate bookkeeping. The prior tail-aware kernel reconstructed block number and offset on every state with runtime division/remainder by the runtime `block_size`. The Builder preserved every selector and state semantic but advanced `q/r` as explicit monotone counters.

Exact result-bearing source `4c906a13ceede4599d3052f22c3ee45058da7432`, workflow `33939806976`, job `101234876826`, artifact `9961421301` (`sha256:923b6b6e0f69a9f9992c414090ca845bd181f60370f9666d205b73c8f1278aa6`) passed all 50 ONE tests and the complete independent anchor oracle.

**Decision:** `promote_counter_bookkeeping`.

Counter/prior-tail elapsed ratios:

- 4,159 B: **0.6621x**;
- 4,160 B: **0.5253x**;
- random 1 MiB: **0.8590x**;
- zlib-random ~1 MiB: **0.8044x**;
- exact pair ~1 MiB: **0.8736x**;
- shifted pair +1 B: **0.8450x**;
- repeated 64 KiB basis, 1 MiB: **0.8931x**;
- hostile 16,385 B: **0.8102x**.

Large-case median is **0.8590x**, about **14.10% faster**. Every frozen row improved. Reserved state stays **49,248 B**, derived-state read counts and suffix lifecycle are unchanged, source rescans remain zero, and all emitted anchors are exact.

Same-compiler disassembly supports the intended cause: the old target function contains **1 integer division instruction**; the counter Builder contains **0** (366 vs 362 decoded instructions). This is causal support, not a substitute for elapsed evidence.

Receipt: `docs/one/evidence/ONE_G02_COUNTER_BOOKKEEPING_PROMOTION_2026-09-04.md`.

## Current scoped negatives and unresolved candidates

### Event-driven dense selection — rejected

The frozen event-driven dense experiment reduced mature selection recomputes to only about **1.39%–1.47% of windows** and suffix candidate loads to **0.65%–0.74%**, yet four of five large cases slowed; zlib-random reached **1.0576x**, and the 4,159 B below-enablement row reached **1.7294x**. Fewer nominal selection events do not automatically mean lower elapsed time when event-state/control overhead replaces cheap regular comparisons.

**Decision:** `reject_event_driven_dense_maintenance`. Reopen only with new causal evidence that removes/fuses the exported event-control cost; do not reopen merely because the event count is small.

### Offset-only dense suffix — unresolved crossover

A separate Builder keeps four raw Gear-state blocks and stores only `uint16` suffix argmin offsets, avoiding duplicated 64-bit suffix values while retaining direct indexing and zero source rescans.

It reduces enabled reserved state from **49,248 B to 41,056 B**, **0.83366x** (about **16.63% less**). All five 1 MiB large cases improved, with ratios **0.9394x, 0.9551x, 0.9892x, 0.9689x, 0.9489x** and median **0.9551x**, while the 4,159 B and 4,160 B rows regressed to **1.1194x** and **1.0937x**.

**Decision:** `offset_only_dense_suffix_inconclusive`. This is a plausible size-dependent crossover, not a promotion and not a retirement. `benchmarks/one/one_g02_minimizer_offset_crossover.py` freezes a geometric size ladder and three data regimes to map that crossover without retroactively choosing a dispatch threshold.

### Other constraints

- ring addressing is not the primary remaining owner;
- two 2,048-state segments preserved exact semantics but did not consistently beat four segments and used about 1.1588x state;
- bounded multi-source buckets recovered no extra reuse in the frozen collision probes while exporting state/proof traffic;
- sparse record-suffix change points are retired under their tested regime.

## Active decisive work

The old cost ladder included the now-removed quotient/remainder overhead, so its layer percentages are historical diagnostics only. The branch now contains a **post-counter residual ladder**:

- `benchmarks/one/one_g02_minimizer_counter_cost_ladder.c`
- `benchmarks/one/one_g02_minimizer_counter_cost_ladder.py`

It remeasures Gear recurrence -> counter buffer/prefix -> counter dense suffix -> exact counter selector on the same runner and exposes the dominant median incremental ns/input-byte layer. The next Builder must target that measured owner rather than reuse stale ownership percentages.

In parallel, the offset-only geometric crossover instrument is allowed to map evidence but **not** to choose a dispatch threshold. Any thresholded Builder requires a new preregistration after the map exists.

Do not integrate the minimizer into the normal observer as a product-speed claim until the remaining charged compute is materially reduced or the opportunity value demonstrably justifies it under the broader ONE objective.

## Product laws remain non-borrowable

Eventually ONE must still preserve zero-byte release regression tolerance, same-runner timing law, exact reconstruction, bounded hostile-input behavior, selective-read locality/amplification, integrity/recovery semantics, native/shared-reader parity and platform portability. G0.2 discovery microbenchmarks grant none of those authorities.

## One-week decision boundary

At/after the first scheduled activation on **2026-09-11 America/Mexico_City**, run the full same-input Genesis comparison against frozen v0.29 and the strongest fair deferred-v0.30 evidence, preserving all 15 workloads and size/speed/access/resource accounting.

This file is mutable handoff state. Architecture Canon, Engineering Grid and immutable experiment receipts remain the stable authorities.
