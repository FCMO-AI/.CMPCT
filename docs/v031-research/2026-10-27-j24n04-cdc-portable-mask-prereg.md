# J24N04 — portable native CDC late-mask arithmetic (preregistered)

Date: 2026-10-27 UTC. Parent: #608, commit `b0be37721a7defbb570b2b3920a7924abb37379b`, C source blob `216189c6a15f1579d596bc4df5128ae63f794168`. Independent historical falsifier: #611 / [J24N03](https://github.com/FCMO-AI/.CMPCT/actions/runs/40551215387). **This record precedes all new C/test/workflow changes.**

## Primary question and strict predictions

Can the native optional CDC helper produce identical chunk geometry under 32-bit and 64-bit `size_t` without losing #608's saturating-bounds repair, immutable Gear table, ABI, ordinary 64-bit geometry or validity checks?

The prior C expression `(uint64_t)(avg_size / 2 - 1)` underflows in `size_t` when valid `avg_size=1`: x86 historical mask 0x00000000ffffffff, x64 mask 0xffffffffffffffff. Shift the subtraction into explicitly 64-bit unsigned arithmetic, preserving the existing low-level hash domain: `(uint64_t)(avg_size / 2) - UINT64_C(1)`. Predict the same seven witness bytes `00 de 1a 53 f0 11 63` at n=7,min=1,avg=1,max=7,cap>=2 now yield **[7] on both MSVC x86 and x64**. Positive control avg=2 predicts **[2,5,7]** on both. On 64-bit all legal inputs, including avg=1, should retain the original bit-mask semantics; on either architecture all inputs avg>=2 should retain historical mask semantics. Do not alter any Gear entry, bound-repair expression, error return, output capacity or ABI.

## Alternatives and charged costs

- **Reject avg=1:** removes supported native API input, undesirable compatibility narrowing.
- **Keep native-size modular underflow:** preserves divergent producer geometry, falsified as a portable contract by #611.
- **Explicit 64-bit subtraction:** one-expression source correction, no storage/index/dependency or extra reconstruction cost; expected identical 64-bit behavior and ordinary inputs, but may intentionally change historically divergent 32-bit avg=1 chunks. Archives remain self-describing through stored chunk lengths; this must not be elevated to a completed-reader proof.

## Cheapest decisive instrument, ownership, and disproof

Create a **new candidate court**, not a mutation of frozen J24N03 historical observation, compiling actual candidate `native/cmpct_cdc.c` on hosted Windows MSVC x86 and x64. Before running, assert Git native source blob identity (to be recorded after edit) and #608 inherited court remains unchanged. Require both [7] and avg=2 [2,5,7], increasing complete ends, count<=capacity. Add a held-out deterministic matrix across ordinary avg>=2 and avg=1 with n>max; both bitnesses must emit the **same stable cryptographic digest** of count/offset records under identical data/parameter sequences. Assert boundary cases `max=SIZE_MAX` still produce complete partitions without arithmetic wrap, and insufficient cap still returns zero. Include normal general CI and native sanitizer (when available), without weakening historical tests.

**Kill/narrow immediately** on any different x86/x64 candidate digest, loss of inherited avg>=2 vector, differing x64 seven-byte witness, nonmonotone/incomplete partition, unsupported 32-bit integer presentation, source-identity mismatch, or boundary-regression. If toolchain/test infrastructure fails, preserve failure and preregister only a narrow fix. No new benchmark credit without the installed native path and full same-input Builder/Reader archive test. Historical #612 expected divergence must remain frozen rather than being merged into the corrected source.

## Promotion boundary and coordination

This is a child branch and PR of source-owner #608; do **not** mutate that parent's branch, PR #501, issue-owned code, frozen evaluators, v0.30.0 release, r24 format, main, benchmarks or Discovery `STATE.json`. Collision check: #611 is open, #612 is closed historical observation and #608 remains sole open native CDC source-fix owner. The new child isolates the portability change. Once hosted evidence terminates, link exact run, HEAD/blobs, negative evidence and update #611 and #608. Specialized C green is component science/product-correctness candidate, **not** default installed-path proof, merge or release authority.
