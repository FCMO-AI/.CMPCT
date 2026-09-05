# CMPCT ONE — Current Research State

**Status:** `ONE-G0.2` active; semantic substrate exact; shift-invariant reuse opportunity survives; block-minimum maintenance is a formally rejected but high-upside rehabilitation candidate  
**Branch:** `research/cmpct1`  
**Control branch:** `research/cmpct1-cleanroom`  
**Research PR:** #88 (draft; base is the frozen v0.30 comparator branch to avoid inherited-CI fanout)  
**Experimental version:** `ONE-G0.2`  
**Date:** 2026-09-04

## Read first

1. `docs/architecture/CMPCT_ONE_CANON_v0.1.md`
2. `docs/roadmap/CMPCT_ONE_ENGINEERING_GRID_v0.1.md`
3. this file
4. `docs/CMPCT1_GENESIS.md`
5. normal CMPCT repository authorities required by `AGENTS.md`
6. `docs/one/NEGATIVE_EVIDENCE.md`
7. `docs/one/evidence/ONE_G02_BLOCK_MAINTENANCE_2026-09-04.md`

Do not reconstruct the design from chat history.

## Current decision

CMPCT ONE remains primary during the Genesis window. The reader-visible design is one representation: **Law + Surprise with selective Crystallization**. Historical mechanisms may inform discovery but may not become a permanent reader-visible codec zoo.

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

The one-pass observer still removes one complete source scan versus equivalent separate run/reuse scans. On the current hosted evidence family, fused/separate Python elapsed is 0.8263x on random 1 MiB, 0.9715x on zeros 1 MiB and 0.8070x on repeated 64 KiB basis, with 50%, 50% and 25.81% total-read reductions respectively.

Coalesced exact proof on zeros removes 16,383 redundant verification operations and about 66.67% of total source traffic versus naive fixed-chunk proof while preserving covered opportunity.

### Selector opportunity survives current falsifiers

The global hypothesis uses inherited `cmpct-gear-v1` and the **rightmost minimum over a 4,096-position sliding Gear-state window**, alongside bounded local evidence. It is encoder discovery only; survivors compile into generic exact reuse Laws.

It retains the current deterministic fixed-selector opportunities while additionally recovering:

- 524,288 B from the ordinary one-byte-shifted 512 KiB pair where aligned fixed chunks recover 0 B;
- 8,192 B from the zero-sparse-anchor 8 KiB adversary;
- the same 8,192 B after a one-byte insertion.

Sparse threshold Gear, local+sparse retention and absolute-coordinate gap fallback remain retired for scoped failures in `docs/one/NEGATIVE_EVIDENCE.md`.

### Compute diagnosis: ring addressing retired as primary owner

The original compiled deque minimizer was about **22.3x–23.1x** slower than Gear-only on 1 MiB large cases, around 90–92 MiB/s versus roughly 2.0 GiB/s Gear-only.

Exact-head source `970326480938d4461bdd5f99bad152b51bda129e`, workflow `33933740375`, job `101217501634`, artifact `9959505729` (`sha256:c17fadcc63202a745ce115325cc6d354b68603af9592393fe6f1f8f570ba77ec`) established that ring-address arithmetic is secondary. Replacing branch wrap with a power-of-two mask improved large cases only 5.15%–8.74% and regressed the 16,385-byte shifted-starvation case by 6.63%. Frozen decision: `retire_ring_addressing_as_primary_remaining_owner`.

The dominant target therefore moved into monotonic-minimum maintenance: variable pop/expiry control flow, comparisons and queue memory traffic.

### Block prefix/suffix Builder: frozen rejection, high-upside core

A causally different maintenance implementation computes the exact same rightmost sliding minimum using predictable prefix/suffix block work over derived Gear states. It consumes source bytes once; its backward pass never rereads source bytes.

Exact-head source `4b2c60b139d09606ad7499ff736158dd11fdb9f4`, workflow `33934157435`, job `101218708556`, artifact `9959767313` (`sha256:e50725d5abb0682a8f58971f0d8c551d6286274887d47995366aff55e2f3b13f9`) passed **50 ONE tests** and matched the independent reference's complete emitted anchor-position trace on every A/B case.

The frozen candidate is formally **rejected** because one just-enabled boundary violates its no-regression rule: at 4,160 B, masked deque 9.850 us -> block 12.411 us (**1.2600x / +26.0%**). The first 4,096-state suffix build is paid for almost no mature windows.

That rejection must remain immutable. However, the large-case result is strong enough for Breakthrough Rehabilitation:

| 1 MiB regime | masked deque | block | ratio | speedup |
| --- | ---: | ---: | ---: | ---: |
| random | 8.377 ms | 3.590 ms | 0.4286x | 2.33x |
| zlib-random | 8.379 ms | 3.606 ms | 0.4304x | 2.32x |
| exact pair | 8.308 ms | 3.591 ms | 0.4322x | 2.31x |
| shifted pair | 8.498 ms | 3.679 ms | 0.4329x | 2.31x |
| repeated 64 KiB basis | 8.247 ms | 3.563 ms | 0.4320x | 2.315x |

Reserved discovery state is 75,776 B including the shared Gear table versus 67,584 B for masked deque (**1.1212x**), inside the frozen 1.25x limit. The 16,385-byte shifted-starvation hostile case also improves 57.421 us -> 52.668 us (0.9172x). Repeated 128 B/256 B/4 KiB bases at 65,536 B improve to 0.5631x/0.5553x/0.5226x.

The gain is not enough for product-speed claims: about 3.6 ms per 1 MiB is roughly 278 MiB/s and remains around 7–8x slower than the Gear-only recurrence before proof, Law selection or emission costs.

## Active decisive experiment — causal startup crossover

A diagnostic sweep is now frozen in `benchmarks/one/one_g02_minimizer_block_crossover.py`. It does **not** promote or supersede the rejected block candidate. It maps lengths 4,160 through 65,536 B across deterministic random, zeros and periodic-257 content, preserving exact anchor traces and charging derived-state reads/state.

Question: is the 4,160-byte loss a stable fixed setup/amortization effect, or a content-dependent instability?

If a structural crossover is demonstrated consistently, the next scientific step is a **new preregistered superseding hybrid-maintenance A/B**: same single selector semantics, cheap deque maintenance below the causally justified crossover and block maintenance above it. Dual implementation/code maintenance is global carrying cost and must be charged. Do not choose the threshold post-hoc from a convenient winning row.

If the crossover is unstable or the hybrid cannot meet a new all-case speed/state gate, retire block rehabilitation and test another predictable maintenance family rather than weakening semantics.

## One-week decision boundary

At/after the first scheduled activation on 2026-09-11 America/Mexico_City, perform the full Genesis comparison against frozen v0.29 and strongest fair deferred-v0.30 evidence, preserving all 15 workloads and speed/access/resource accounting.

This file is mutable handoff state. Architecture Canon and Engineering Grid remain the stable design authorities.
