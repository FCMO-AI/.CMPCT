# CMPCT ONE — Current Research State

**Status:** `ONE-G0.2` active; semantic substrate exact; shift-invariant reuse opportunity survives; **tail-return 8 KiB size dispatch is the current encoder-discovery baseline** (counter path below 8,192 B, lower-state offset-only path at/above 8,192 B); post-counter residual work is now constrained to the co-dominant suffix+selection cluster  
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
10. `docs/one/evidence/ONE_G02_OFFSET_PARETO_PAIRED_2026-09-04.md`
11. `docs/one/evidence/ONE_G02_OFFSET_CROSSOVER_PAIRED_2026-09-04.md`
12. `docs/one/evidence/ONE_G02_TAIL_8K_DISPATCH_PROMOTION_2026-09-04.md`
13. `docs/one/evidence/ONE_G02_PAIRED_RESIDUAL_REPEATABILITY_2026-09-04.md`

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

### Counter bookkeeping promotion

The tail-aware kernel originally reconstructed block number and offset on every state with runtime division/remainder by runtime `block_size`. Explicit monotone `q/r` counters preserved every selector/state semantic while removing runtime division.

Exact result-bearing source `4c906a13ceede4599d3052f22c3ee45058da7432`, workflow `33939806976`, job `101234876826`, artifact `9961421301` (`sha256:923b6b6e0f69a9f9992c414090ca845bd181f60370f9666d205b73c8f1278aa6`) passed all 50 ONE tests and the complete independent anchor oracle.

**Decision:** `promote_counter_bookkeeping`.

Counter/prior-tail elapsed ratios included 4,159 B **0.6621x**, 4,160 B **0.5253x**, random 1 MiB **0.8590x**, zlib-random ~1 MiB **0.8044x**, exact pair **0.8736x**, shifted pair **0.8450x**, repeated 64 KiB basis **0.8931x**, hostile 16,385 B **0.8102x**. Large-case median was **0.8590x**, about **14.10% faster**. Reserved state remained **49,248 B** and source rescans stayed zero. Same-compiler disassembly changed the target from one integer division to zero.

Receipt: `docs/one/evidence/ONE_G02_COUNTER_BOOKKEEPING_PROMOTION_2026-09-04.md`.

## Current promoted encoder-discovery baseline — tail-return 8 KiB dispatch

The offset-only dense suffix representation removes duplicated 64-bit suffix values and retains direct indexing, exact rightmost-min semantics and zero source rescans. Its enabled reserved state is **41,056 B vs 49,248 B** for the counter representation, a **16.63% reduction**.

Paired Pareto replay established a real regime split: exact enablement at 4,160 B was slower (**1.04660x** median, **1.09247x** p90), while the cross-large median was **0.794097x** counter. The preregistered geometric crossover map then selected **8,192 B** as the first size at which all tested random, repeated and zlib-random-like rows at that size and above met the frozen non-inferiority law. Neither experiment could promote a dispatcher by itself.

The first ordinary 8 KiB wrapper dispatcher was inconclusive: cross-large median **0.998407x**, showing that wrapper/layout debt could erase the lower-state kernel advantage.

A causal rehabilitation changed only the integration shape to a tail-return dispatcher while preserving the frozen 8,192-byte boundary, comparison, size ladder, regimes and 13-round gate. Exact source `dbf5a940ce22c058567dcd4889c13e64200cc741`, workflow `33941920994`, job `101240914393`, artifact `9962132188` (`sha256:52444fe65ff6db0eccc8b9306d68977223adc21f5076fddcd7ea6fa96128ef6a`) passed all **50 ONE tests** and the unchanged promotion gate.

**Decision:** `promote_tail_8k_size_dispatch`.

Key exact-head measurements:

- cross-large median dispatch/counter: **0.900864x** — about **9.91% lower elapsed**;
- state on enabled offset path: **41,056 B vs 49,248 B** — **16.63% less**;
- source-byte rescans: **0**;
- static dispatcher shape: **25 instructions, 0 calls, 4 jumps** (code-shape evidence only);
- 8,192 B random: median **0.946528x**, p90 **0.958496x**;
- 8,192 B repeated 4 KiB basis: median **0.936286x**, p90 **0.956490x**;
- zlib-random-like at the boundary: median **0.913483x**, p90 **0.935492x**;
- 1 MiB random: **0.906862x**;
- 1 MiB repeated: **0.901449x**;
- 1 MiB zlib-random-like: **0.906472x**.

The baseline is therefore now: **counter path below 8,192 input bytes; offset-only path at/above 8,192 bytes; tail-return dispatch**. This is encoder-discovery promotion only. It does not change the ONE reader ontology or establish product speed/stored-byte superiority.

Receipt: `docs/one/evidence/ONE_G02_TAIL_8K_DISPATCH_PROMOTION_2026-09-04.md`.

## Current scoped negatives and causal constraints

### Event-driven dense selection — rejected

The frozen event-driven dense experiment reduced mature selection recomputes to only about **1.39%–1.47% of windows** and suffix candidate loads to **0.65%–0.74%**, yet four of five large cases slowed; zlib-random reached **1.0576x**, and the 4,159 B below-enablement row reached **1.7294x**. Fewer nominal selection events do not automatically mean lower elapsed time when event-state/control overhead replaces cheap regular comparisons.

**Decision:** `reject_event_driven_dense_maintenance`. Reopen only with new causal evidence that removes/fuses the exported event-control cost; do not reopen merely because the event count is small.

### Single residual-owner ranking — now constrained by repeatability

The post-counter paired A-B-B-A ladder is useful, but two immutable exact-source runs invert the top-two owner ordering:

- source `295d2ebe...`: buffer/prefix **0.662275**, dense suffix **1.459584**, exact selection **1.406956 ns/input-byte** -> run-local owner `dense_suffix`;
- source `dbf5a940...`: buffer/prefix **0.713417**, dense suffix **1.775622**, exact selection **1.779149 ns/input-byte** -> run-local owner `exact_selection`.

On the later run selection exceeds suffix by only **0.003527 ns/input-byte (~0.20%)**. Both runs agree on the useful causal fact: buffer/prefix is materially smaller and **suffix construction + exact selection are one co-dominant residual cluster**. Hosted timing does not support targeting either one in isolation as a stable global owner.

**Scoped negative constraint:** do not reopen single-layer micro-tuning merely from a rank flip. The next intervention must reduce shared suffix+selection work or demonstrate a stable material separation without transferring the cost to the other layer.

Receipt: `docs/one/evidence/ONE_G02_PAIRED_RESIDUAL_REPEATABILITY_2026-09-04.md`.

### Other constraints

- ring addressing is not the primary remaining owner;
- two 2,048-state segments preserved exact semantics but did not consistently beat four segments and used about 1.1588x state;
- bounded multi-source buckets recovered no extra reuse in the frozen collision probes while exporting state/proof traffic;
- sparse record-suffix change points are retired under their tested regime;
- a naive ordinary 8 KiB dispatcher is superseded by the tail-return integration because it failed to preserve the kernel-level advantage.

## Active decisive work

The 8 KiB size gate is no longer the research question: it has survived end-to-end wrapper charging under the tail-return integration and is promoted as the encoder-discovery baseline.

The next causal Builder must attack the **combined suffix+selection cluster** rather than choosing whichever layer happens to rank first on one hosted run. Preferred hypotheses are forms of concept/work fusion: carry exactly the sufficient argmin information needed by selection during suffix construction, fuse construction and query work so an intermediate state walk disappears, or otherwise collapse the two costs without adding reader semantics, source rescans, irregular branch debt or extra retained state.

Any such Builder must preserve exact rightmost-min selector traces, zero source rescans, the 8 KiB counter/offset dispatch law unless separately superseded, and complete state/elapsed accounting. A win that merely moves time from suffix construction into selection is a rejection.

Do not integrate the minimizer into the normal observer as a product-speed claim until the remaining charged compute is materially reduced or the opportunity value demonstrably justifies it under the broader ONE objective.

## Product laws remain non-borrowable

Eventually ONE must still preserve zero-byte release regression tolerance, same-runner timing law, exact reconstruction, bounded hostile-input behavior, selective-read locality/amplification, integrity/recovery semantics, native/shared-reader parity and platform portability. G0.2 discovery microbenchmarks grant none of those authorities.

## One-week decision boundary

At/after the first scheduled activation on **2026-09-11 America/Mexico_City**, run the full same-input Genesis comparison against frozen v0.29 and the strongest fair deferred-v0.30 evidence, preserving all 15 workloads and size/speed/access/resource accounting.

This file is mutable handoff state. Architecture Canon, Engineering Grid and immutable experiment receipts remain the stable authorities.
