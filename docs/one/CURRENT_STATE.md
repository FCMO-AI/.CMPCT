# CMPCT ONE — Current Research State

**Status:** `ONE-G0.2` active; ONE-01 semantic substrate is exact-head green, ONE-03 has a surviving shift-invariant reuse selector, and compiled minimizer maintenance is the current falsification target  
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
6. `docs/one/NEGATIVE_EVIDENCE.md` before reopening a selector family

Do not reconstruct the design from chat history.

## Current decision

CMPCT ONE remains the primary CMPCT research line during the Genesis window. The design is one reader-visible information representation based on **Law + Surprise with selective Crystallization**. Historical mechanisms may inform Law discovery but are not a permanent reader ontology.

The encoder may be sophisticated; the reader must remain bounded, deterministic, simple relative to the compiler, hostile-input-safe and exactly reconstructing. Speed/efficiency is co-equal with density. The campaign therefore measures source traffic, verification traffic, retained state and compute alongside opportunity bytes.

## Frozen comparison authorities

- v0.29/main pivot: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30 authoritative integration: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

Do not rewrite or delete the v0.30 evidence/branch forest. The full same-input Genesis decision comparison is due at/after the first activation on **2026-09-11**. No G0.x microbenchmark substitutes for that 15-workload decision.

## ONE-01 — semantic substrate

The first reader ontology remains six generic relationships only: `surprise`, `concat`, `repeat`, `fill`, `xor`, `add8`. There are no opaque legacy-codec opcodes.

The reference evaluator retains cycle, depth, output-byte, work-byte, range, declared-length and root-SHA checks; the independent tuple oracle and malformed/resource vectors remain binding. The current exact-head ONE workflow at source `970326480938d4461bdd5f99bad152b51bda129e` passed **50 tests** in workflow `33933740375`, job `101217501634`, artifact `9959505729` (`sha256:c17fadcc63202a745ce115325cc6d354b68603af9592393fe6f1f8f570ba77ec`).

Complete-wire G0.1 evidence still shows the key representation facts: 64 KiB repetition from a 64-byte basis is 137 wire bytes; 64 KiB fill is 69 bytes; 131,072-byte exact-reuse pair is 65,657 bytes. Tiny framing remains expensive (16 logical repeated bytes -> 74 wire bytes). These are representation facts, not product-speed claims.

## ONE-03 — fused observation and reuse discovery

### Fused pass survives

The one-pass observer continues to eliminate one complete source scan versus equivalent separate run/reuse scans. On the current exact-head runner:

| deterministic regime | fused / separate Python elapsed | source/read effect |
| --- | ---: | --- |
| random 1 MiB | 0.8263x | 50.0% total-read reduction |
| zeros 1 MiB | 0.9715x | 50.0% total-read reduction |
| repeated 64 KiB basis | 0.8070x | 25.81% total-read reduction |

Coalesced exact proof remains causally useful: on zeros it removes 16,383 redundant verification operations and about 66.67% of total source traffic versus naive fixed-chunk proof while preserving covered opportunity. The repeated-64-KiB regime still exposes extension/proof rereads as real carrying cost.

### Selector path: shift-invariant rolling Gear minima

The current surviving global reuse-discovery hypothesis uses the inherited `cmpct-gear-v1` signal and a **rightmost minimum over a 4,096-position sliding window**, alongside bounded local evidence for short relationships. It is encoder discovery only; surviving candidates compile into generic exact reuse Laws. No CDC/minimizer opcode enters the reader.

The selector survived the current opportunity falsifiers:

- no fixed-selector opportunity loss in the deterministic matrix;
- +524,288 B opportunity on the ordinary one-byte-shifted 512 KiB pair where aligned fixed chunks see 0 B;
- recovers the 8,192 B zero-sparse-anchor adversary both aligned and after a one-byte insertion;
- random/compressed negatives produce no reuse proof rereads;
- observed queue/index state is much smaller than full fixed indexing on the large regimes.

Sparse threshold Gear, local+sparse retention, and absolute-coordinate gap fallback are retired for their scoped failures. See `docs/one/NEGATIVE_EVIDENCE.md`.

### Current blocker: compiled monotonic-minimum cost

Exact-head native evidence proves the selector's compute debt is structural, not merely Python overhead. For 1 MiB large cases:

| regime | Gear-only | current minimizer | elapsed multiplier | incremental minimizer |
| --- | ---: | ---: | ---: | ---: |
| random | 2064.4 MiB/s | 90.35 MiB/s | 22.85x | 10.093 ns/B |
| zlib-random | 2054.9 MiB/s | 90.42 MiB/s | 22.73x | 10.083 ns/B |
| exact pair | 2097.0 MiB/s | 90.62 MiB/s | 23.14x | 10.070 ns/B |
| shifted pair | 2020.1 MiB/s | 90.60 MiB/s | 22.30x | 10.054 ns/B |
| repeated 64 KiB | 2090.4 MiB/s | 92.12 MiB/s | 22.69x | 9.897 ns/B |

Runtime modulo was a real but secondary owner: branch-wrap improved the old modulo kernel roughly 12–15% on large cases but failed its frozen 15%-every-large-case promotion rule. A stricter power-of-two masked-ring follow-up then improved branch-wrap by only **5.15–8.74%** on large cases and regressed the 16,385-byte shifted-starvation adversary by **6.63%**. Its frozen decision is `retire_ring_addressing_as_primary_remaining_owner`.

That narrows the primary causal target to the **monotonic-minimum maintenance itself**: variable pop/expiry control flow, comparisons and queue memory traffic. Do not resume isolated ring-wrap tuning without a new causal layout.

### Collision stress

Bounded multi-source retention did not recover any additional exact opportunity over one-source retention even under deterministic 8/12/16-bit signal truncation stress, while adding state. The natural 64-bit control also showed no benefit. Keep one-source retention until a hostile case proves otherwise.

## Next decisive experiment

Mission Lock for the next G0.2 unit:

- **Hypothesis:** replacing variable deque maintenance with a predictable bounded sliding-minimum algorithm can preserve the exact rightmost-minimum anchor sequence while materially reducing compiled minimizer cost.
- **Builder constraint:** keep the inherited Gear identity, 64-byte Gear window, 4,096-position minimizer span, rightmost tie rule, opportunity/proof semantics and reader representation unchanged. This is an encoder-only implementation A/B, not a new mechanism.
- **Required evidence:** exact emitted anchor positions against an independent reference, not merely equal counts; large-case elapsed improvement; explicit reserved/observed state and derived-state traffic; hostile boundary/small cases; no hidden second source scan.
- **Disproof/reform:** if a block/two-stack/prefix-suffix implementation merely trades branch work for disproportionate state/memory traffic or fails to materially narrow the ~22x Gear-only gap, retire that maintenance family rather than tune thresholds.
- **Non-goal:** no product-speed, stored-byte, v0.29 or v0.30 superiority claim from this microkernel.

The most promising first Builder is a block prefix/suffix sliding minimum: it can compute the same exact window minimum with predictable comparisons and one bounded backward pass over **derived Gear states**, not a second source read. Its state cost must be charged explicitly.

## One-week decision boundary

At/after the first scheduled activation on 2026-09-11 America/Mexico_City, perform the Genesis comparison against frozen v0.29 and strongest fair deferred-v0.30 evidence, preserving the full 15-workload matrix plus speed/access/resource accounting.

This file is mutable handoff state. The Architecture Canon and Engineering Grid are the stable design authorities.
