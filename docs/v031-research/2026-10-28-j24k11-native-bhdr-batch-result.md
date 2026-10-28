# J24K11 — Batched physical BHDR witness: scientific result

Date: 2026-10-28 UTC
Status: **NATIVE_BATCH_MECHANISM_HEADROOM — ONE HOSTED COMPONENT COURT PASS; NO PRODUCT PROMOTION.**
Owner branch: `agent/phased1-v031-j24k11-native-bhdr-batch-oracle-20261028`; [Draft PR #660](https://github.com/FCMO-AI/.CMPCT/pull/660).
Base: [J24K09 PR #653](https://github.com/FCMO-AI/.CMPCT/pull/653) `2d30cc6da41c136f3b1a412ccf3f1f5686dca54a`.
Frozen preregistration: `cfcd7e6a42f837219c25515ea8eea7f2fa451741`.
**Measured code HEAD**: `8ed88be05a69070dd9f565cf11616fcd79b5e9ca`.
[Original hosted scientific court #40654643276](https://github.com/FCMO-AI/.CMPCT/actions/runs/40654643276) **SUCCESS**, Ubuntu 24.04 / CPython 3.11.
[Original result artifact #12801161029](https://github.com/FCMO-AI/.CMPCT/actions/runs/40654643276/artifacts/12801161029), ZIP digest `sha256:465d094bae14d25a5206765bd93b0aca5c41e016aaec74af63f459e127a11f14`.

## Question and decision

J24K09 has already demonstrated a *correct* signed/physical BHDR size witness, but per-read Python checking of thousands of preceding streams costs several milliseconds. J24K10 falsified the idea that making a private full-archive copy is automatically a viable way to amortize the proof. This test asks whether checking all preceding BHDRs in one native call avoids both expensive per-stream Python overhead **and** unsafe reuse of stale proof.

**Preregistered threshold:** >=1.5x lower wall AND CPU time against both the method-loop and *strong direct Python-loop* control, at 4,096 streams for each of three physical modes; parity on hostile geometry is mandatory.

The narrower component-tier answer is **YES, the representation has measurable native throughput headroom**, not that the released product already improved.

## Exact hosted 4,096-stream result

| Physical mode modeled | Direct Python loop wall | Batched native wall | Wall speedup vs strong loop | Native CPU |
|---|---:|---:|---:|---:|
| STORED (RAW owner) | 4.538912 ms | 0.212981 ms | **21.31x** | 0.213133 ms |
| Canonical mode0 (Deflate owner) | 4.570680 ms | 0.218489 ms | **20.92x** | 0.218600 ms |
| Retained mode1 (opaque owner) | 4.517446 ms | 0.209563 ms | **21.56x** | 0.209702 ms |

All 4096-stream CPU ratios versus the strong loop are >=20.90x. The inherited per-method reference cost was approximately 5.13–5.22 ms. The same control shape at 64/512 modeled streams also favored the batched native path; none of these numbers belongs to product/open/read/extract performance.

The limited-ABI helper compiled in **0.608027 s**, producing a **27,288 B** Linux binary. Binary compilation and fresh-process startup are **not** charged to the reported steady-state component call speedups and must be paid at product level.

## Adversarial and independent evidence

The hosted experiment recorded **nine cells** (64/512/4096 streams x 3 physical modes), each with **36 timed observations** (12 method-Python, 12 direct-loop Python, 12 native), yielding **324 raw CPU/wall samples**. The native scanner was called with exactly the same existing 7-field Python tuples as the two reference paths, including the one buffer acquisition and all C tuple enumeration on each native call. The instrument ran 120 input perturbation cells across two geometry sizes and three modes: **114 malformed physical/signed cases rejected; six deliberately empty-list controls accepted**. The local independent auditor recomputed all medians and minimum ratios from raw receipts and rejected **8/8 deliberately falsified records**.

The C source fingerprint was `05a2187c9e2e359e4004c996b6d81bbdfd34ac875bb59fb033b6c93df96a5b81`. This fingerprint and all sample rows are preserved in original GitHub Actions artifact #12801161029.

A separate local CPython 3.13.5 run also passed the instrument and hostile controls; it is **not** a second hosted OS, not a cross-platform ABI test, and not a same-runner benchmark comparison against CPython 3.11. Both observations are Linux mechanisms only.

## Strongest self-critique and exact boundaries

**Major exported cost not charged:** Both Python and C arms receive **prebuilt seven-field tuples**, whereas CMPCT's authentic Reader currently holds authenticated blob descriptors and VZIP recipe fields in other structures. The runtime cost/memory of projecting those actual effective-index structures into native-scannable rows **on every read** is not measured here. This gap can completely remove the improvement. A generic "C is 21x faster" product narrative would therefore be misleading.

The synthetic 64-byte physical records have r24-compatible BHDR geometry, but they are **not complete authenticated CMPCT archives**; there was no full Reader `read_range`, `verify`, zlib/Zstd decode, physical ZIP extraction, real signed index, actual mmap/source truncation, concurrency, codec-bound inference, or ABI3 wheel installation in this experiment. Retained-mode opaque synthetic payload bytes are not a valid Zstd-compressed payload; only physical header/coordinate accounting is measured. Partial SHA authentication is neither claimed nor provided. Memory/allocator traffic, Wheel/ABI portability beyond this Linux interpreter, startup, cleanup, source mutation and longer host/corpus variation remain unmeasured.

Native `False` on invalid input is a candidate for **strict Python fallback**, not permission to omit inherited error diagnostics or safety guards. The C module does not become part of `src/` or `native/` through this result.

## Decision and cheapest next experiment

The narrower hypothesis crossed the original >=1.5x CPU/wall threshold in the 4,096-stream component geometry with zero observed mutant acceptances, so **keep the batch-scanner idea on the nondominated research frontier**.

Before any product implementation, preregister and measure a **fully charged actual Reader→7-field-row bridge** against direct Python J24K09 BHDR witness on the same effective signed index/mmap, with held-out mixed streams, Python exceptions, 1 and 64 ranges and memory allocation. The first cheap falsifier is simply charging row projection and its retention/invalidation alternatives: if the projected native route loses to the direct Python loop after bridge work, stop the family. Only if this survives should code be composed under J24K09 #653 ownership and submitted to three-host, hostile source mutation, full Reader and release parity.

Published CMPCT remains **v0.30.0 / format r24**. **No merge, release, format, benchmark, native ABI or product source change**. Discovery STATE.json deliberately untouched while #574 owns its reconciliation. No discovery policy change earned from one result.

## Historical CI caveat

The first J24K11 CI attempt failed before running the experiment because the workflow used malformed interpolation syntax; it was corrected without changing the scientific evaluator. A separate Engineering Evidence job initially failed on missing required PR headings and later on required falsifiability markers; PR metadata was amended, never the validator. The original scientific court cited above is green, but generic test/CI on subsequent documentary HEAD must be checked separately before any claim of exact-head completeness.
