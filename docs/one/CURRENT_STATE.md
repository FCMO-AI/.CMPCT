# CMPCT ONE — Current Research State

**Status:** `ONE-G0.2` active; ONE-01 semantic substrate is independently accounted and exact-head green, while ONE-03 fused-observation economics are under falsification  
**Branch:** `research/cmpct1`  
**Control branch:** `research/cmpct1-cleanroom`  
**Research PR:** #88 (draft; base is the frozen v0.30 comparator branch to avoid inherited-CI fanout)  
**Experimental version:** `ONE-G0.2`  
**Date:** 2026-09-04

## Read first

1. `docs/architecture/CMPCT_ONE_CANON_v0.1.md`
2. `docs/roadmap/CMPCT_ONE_ENGINEERING_GRID_v0.1.md`
3. `docs/CMPCT1_GENESIS.md`
4. normal CMPCT repository authorities required by `AGENTS.md`

Do not reconstruct the design from chat history.

## Current decision

CMPCT ONE is the primary CMPCT research line during the Genesis window. The design is one reader-visible information representation based on **Law + Surprise with selective Crystallization**. Historical mechanisms may inform Law discovery but are not the desired permanent reader ontology.

The encoder may be extremely sophisticated; the reader must remain bounded, deterministic, simple relative to the compiler, hostile-input-safe and capable of exact reconstruction.

Speed/efficiency is co-equal with density. The campaign optimizes useful bits eliminated per unit compute through fused observation, opportunity-gated search, branch-and-bound pruning, analysis reuse, incremental changed-cone work, bulk/vector semantics and Law fusion.

## Frozen comparison authorities

- v0.29/main pivot: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30 authoritative integration: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

Do not rewrite or delete the v0.30 evidence/branch forest.

The full same-input Genesis decision comparison is due at/after the first activation on 2026-09-11. No pre-gate G0.x microbenchmark is a substitute for that 15-workload decision.

## Important inherited negative evidence

The retired v0.30 F-01 reversible-structure thesis proved real composition headroom but failed its stronger general admission/generalization claim. CMPCT1 preserves these scoped constraints:

- human structural labels are not sufficient generic admission predicates;
- seed-local operator inactivity does not justify global grammar pruning;
- expanding a synthesis/operator grid is not progress without a new content-derived causal predictor;
- exact savings found after expensive search do not by themselves prove cheap generic discovery.

ONE therefore requires content-derived Opportunity Gates and explicit discovery economics.

## ONE-01 — semantic substrate checkpoint

The first reader ontology remains six generic relationships only: `surprise`, `concat`, `repeat`, `fill`, `xor`, `add8`. There are no opaque legacy-codec opcodes.

The reference evaluator retains cycle, depth, output-byte, work-byte, range, declared-length and root-SHA checks; the independent tuple oracle and malformed/resource vectors remain binding.

Exact-head semantic evidence at `4ec174c69a6107ae8f9f10443b48103de10fb1cd` completed green in workflow run `33928351439`, job `101201656121`:

- `38 passed` in `tests/one`;
- evidence artifact `9957633203`;
- artifact ZIP SHA-256 `6252045bd805ebe5edda0d9053f06e8a00d3933c2513130b329d0c1ebe2d8b0c`.

Complete experimental-wire facts from that exact head include:

| case | logical bytes | wire bytes | Surprise | control + integrity | reference evaluate |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1-byte literal | 1 | 61 | 1 | 60 | 0.044 MiB/s |
| 16-byte repetition | 16 | 74 | 1 | 73 | 0.671 MiB/s |
| 64 KiB literal | 65,536 | 65,605 | 65,536 | 69 | 1,089.8 MiB/s |
| 64 KiB repetition from 64 B | 65,536 | 137 | 64 | 73 | 951.3 MiB/s |
| 64 KiB zero fill | 65,536 | 69 | 0 | 69 | 1,043.7 MiB/s |
| 64 KiB exact reuse pair | 131,072 | 65,657 | 65,536 | 121 | 1,109.5 MiB/s |
| multi-parent XOR | 98,304 | 65,709 | 65,536 | 173 | 21.1 MiB/s |

These are representation/reference-evaluator facts, not product-speed or v0.29/v0.30 wins.

### ONE-01 surviving negatives

- Tiny-object framing/integrity remains a real loss: a 16-byte repeated logical object occupies 74 bytes. Do not tune away required metadata to hide it.
- The Python multi-parent XOR evaluator is dramatically slower than the bulk copy/fill/repeat cases (~21 MiB/s versus roughly 0.95–1.11 GiB/s on the same hosted evidence run). This is implementation evidence that bytewise Python arithmetic cannot stand in for the eventual bulk/native path; it is not yet permission to start production native ONE work before the Grid preconditions are met.

The six-operation vocabulary remains provisional until wider inherited-relationship translation shows whether a missing generic primitive is actually needed.

## ONE-03 — fused observation checkpoint

`experiments/one/observe.py` now performs one bounded forward source pass that simultaneously observes:

- runs;
- fixed-chunk 64-bit fingerprints;
- exact reuse nominations after byte verification;
- bounded retained index state;
- explicit source-scan, verification-reread, opportunity-mass and retained-index-payload accounting.

Fixed chunks and FNV are discovery instrumentation, not canonical archive semantics.

### Active falsifiable hypothesis

A fused observation pass can remove redundant source scans for cheap Law nomination and, after implementation overhead is controlled, provide a better compute/memory-traffic foundation than separate mechanism-like rescans.

### Exact A/B result

`benchmarks/one/one_g02_fusion_ab.py` compares the fused observer with an equivalent two-pass reference that separately scans runs and fixed-chunk reuse while requiring the same candidate/opportunity output.

On exact head `4ec174c69a6107ae8f9f10443b48103de10fb1cd`, 7-repetition medians on the hosted runner were:

| deterministic 1 MiB regime | fused total source reads | separate total source reads | total-read reduction | fused/separate Python elapsed |
| --- | ---: | ---: | ---: | ---: |
| random | 1,048,576 | 2,097,152 | 50.00% | 1.0369x (+3.69%) |
| zeros | 3,145,600 | 4,194,176 | 25.00% | 1.1259x (+12.59%) |
| repeated 64 KiB basis | 3,014,656 | 4,063,232 | 25.81% | 1.1230x (+12.30%) |

The fused algorithm eliminates exactly one full input-sized source scan in all three cases. **It does not yet produce an elapsed-time win in Python.** The current reference loop is 3.7–12.6% slower than the two specialized loops despite lower memory traffic.

This is decision-changing negative evidence, not a reason to narrate a speed win.

### Causal evidence exposed by the A/B

The positive-pattern regimes reveal a second cost that fusion alone does not solve:

- zeros: exact candidate verification rereads 2,097,024 bytes, making fused total source traffic almost `3.0x` input despite a one-pass base scan;
- repeated 64 KiB basis: verification rereads 1,966,080 bytes, making total source traffic `2.875x` input;
- random: zero false reuse candidates and zero verification rereads, so the cheap negative path remains exactly one source scan.

Thus the next performance question is not "add more features." It is whether reuse nominations can be **coalesced/extended and verified in larger contiguous regions** so the compiler preserves exact proof while avoiding thousands of overlapping 64-byte verification rereads and candidate objects.

## Next decisive experiment

Mission Lock for the next G0.2 unit:

- **Hypothesis:** content-derived adjacency/sequence evidence can coalesce fixed-chunk reuse nominations into larger contiguous candidate regions, preserving exact reuse proof while materially reducing verification rereads and candidate count on repeated data, with negligible extra work on random data.
- **Success evidence:** same exact nominated reusable bytes (or a strictly explained superset later charged by the Law cost model), fewer verification operations/read bytes and lower or neutral elapsed work on positive regimes; random/false-pattern inputs remain sparse and bounded.
- **Disproof/reform:** if coalescing requires another full source scan, materially raises random-input work/memory, misses ordinary shifted relationships without a compensating later stage, or merely moves the same read traffic into hidden work, reject/reform it rather than tune a benchmark threshold.
- **Non-goal:** no extension-based/workload-label dispatch and no product/native claim from Python timings.

After verification granularity is understood, add the next observation feature family only if it earns measurable opportunity value per added source/CPU/memory cost.

## One-week decision boundary

At/after the first scheduled activation on 2026-09-11 America/Mexico_City, perform the Genesis comparison against frozen v0.29 and strongest fair deferred-v0.30 evidence, preserving the full 15-workload matrix plus speed/access/resource accounting.

This file is mutable handoff state. The Architecture Canon and Engineering Grid are the stable design authorities.
