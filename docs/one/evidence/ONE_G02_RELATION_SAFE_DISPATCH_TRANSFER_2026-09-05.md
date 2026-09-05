# ONE-G0.2 — Overlap-safe relation dispatch structurally transfers from 4 KiB through 256 KiB

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Status:** advance structural transfer; isolated writer primitive only  
**Result-bearing source:** `25e9cc075a22998879a7d4c302248b5834d908f9`

## Mission Lock

The overlap-safe no-alias relation dispatch had advanced at 32/64 KiB. This frozen transfer asked whether the result was a narrow compiler accident or a mechanism-level implementation recovery. The relation semantics, cases, exact accounting and safety dispatch were unchanged. Only the frozen relation-size ladder broadened to **4, 8, 16, 32, 64, 128 and 256 KiB**.

Advance required every one of the 35 rows to preserve exact result structs, select the proven-disjoint fast path, satisfy `dispatch/direct <= 0.97`, and satisfy `dispatch/compact-half <= 1.08`. No aggregate could hide a losing row.

## Exact-head receipt

- workflow: `33963218627`
- job: `101298639286`
- artifact: `9968618836`
- artifact zip SHA-256: `ff642217274e8f7d5aaf61a4074075795b87916f9f0a097d951a6f26c3b6f89e`
- `tests/one`: **76 passed**
- decision: **`advance_safe_dispatch_structural_transfer`**
- result-bearing rows: **35 / 35 passed**
- every result struct exact
- every disjoint row selected `dispatch_path=1`

## Transfer envelope

Across all 35 rows:

- `dispatch/direct`: **0.762662x to 0.950811x**
- `dispatch/compact-half`: **0.786643x to 0.948439x**

Thus even the weakest tested row remained about **4.92% faster than the alias-conservative generic direct kernel**, and every tested row was faster than the compact-half special-case control.

Median ratios by relation size:

| relation size | median dispatch/direct | median dispatch/half | worst dispatch/direct | worst dispatch/half |
|---:|---:|---:|---:|---:|
| 4 KiB | 0.947886x | 0.908687x | 0.950811x | 0.922338x |
| 8 KiB | 0.898496x | 0.919204x | 0.949399x | 0.947090x |
| 16 KiB | 0.881350x | 0.931316x | 0.895269x | 0.937340x |
| 32 KiB | 0.813402x | 0.886741x | 0.845053x | 0.934883x |
| 64 KiB | 0.843685x | 0.935615x | 0.869155x | 0.948439x |
| 128 KiB | 0.844540x | 0.922188x | 0.870002x | 0.930817x |
| 256 KiB | 0.833835x | 0.912956x | 0.850740x | 0.914553x |

The 4 KiB boundary is the most demanding fixed-cost regime and still clears the frozen transfer law. The advantage generally strengthens once relation work is large enough to amortize the dynamic range proof.

## Scientific interpretation

The generalized arbitrary-relation writer primitive no longer carries evidence of an inherent compute tax versus the compact half-layout special case in this isolated proof-led kernel. The earlier apparent penalty was exported implementation/measurement debt: independent timing distortion, pointer/API overhead and—decisively—compiler alias conservatism. A correctness-preserving disjointness proof plus safe fallback compiles the generalized relation into code that transfers across a 64x size span.

This is a concept-compression win in implementation shape: the generalized relation path can subsume the compact-half discovery special case in the tested regime rather than retaining a separate fast reader/writer mechanism merely for speed.

## Strongest remaining debt

This is still an **isolated writer-discovery primitive**. The experiment does not charge:

- nomination/opportunity-gating cost before the relation proof;
- total fused-observer elapsed time;
- fast-path incidence on natural multi-object/version workloads;
- memory/state traffic of relation candidate bookkeeping;
- interaction with the promoted 8 KiB tail-return selector;
- stored bytes, reader decode throughput, selective access, integrity/recovery, or platform portability.

The next decisive step is integrated transfer into the fused ONE discovery path. That experiment must charge the dynamic disjointness proof, fallback incidence, total writer elapsed, memory/state and false-control work while preserving exact Law+Surprise output semantics. Another isolated relation micro-optimization is lower value unless integration exposes a new causal owner.

## Claim boundary

Writer-side structural transfer only. No reader-visible operation changed. No density, stored-byte, product creation/decode speed, v0.29/v0.30 superiority, release or September-11 gate authority is created by this receipt.
