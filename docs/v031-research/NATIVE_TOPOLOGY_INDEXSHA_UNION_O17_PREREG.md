# O17 — Compose indexed logical SHA with native hardlink topology (preregistration)

Date: 2026-10-24 UTC. Status: prospectively registered before implementation or O17 measurement.

## Authority and narrow ownership
Released floor v0.30.0, revision 24; experimental v0.31 native ABI is unmerged. Base is **PR #349** exact HEAD `611d0ea67a94f552f9ebca07ba747f191dee160e`, inheriting PR #326's authenticated PACK + MessagePack security. Independent sibling **PR #340** exact HEAD `933ec4fba057584954a6c1da56f7ff25665df97c` owns the already investigated `cmpct_entry_logical_sha256` (CDC-positive / RAW-negative). Neither upstream PR is modified. This O17 branch owns only source-exact *composition* and new same-archive conformance, not a new hash claim or distributed extractor.

## Primary question, mechanism and prospectively testable prediction
Can these two optional native metadata APIs coexist in ONE genuine Rust/C Reader instance while preserving all earlier graph validation, PACK batching and exact signed-index commitments? Compose the **unchanged logical SHA function** from #340 into the precise Rust/header owner source of #349; do not duplicate parsing or change r24 bytes. Construct one Builder-produced tree with (1) at least one S_CDC large regular owner with index SHA, (2) an actual POSIX hardlink alias to it, (3) a second independent distinct regular file and hardlink alias, (4) a direct RAW owner for absent-SHA control, (5) a symlink and directory; verify independently using Python source SHA and inode identity. Exercise both C queries on one live handle, C streaming SHA for CDC, and fail-closed negatives (hardlink hash unsupported, RAW hash unsupported, invalid indices/null args). Run prior O14, O12 and Native PACK tests on the exact integrated source.

## Stronger control, alternative explanations, limits
Separate standalone success of PRs #340/#349 is **not composition evidence**. A consumer with a copied MessagePack parser or with source data as its sole truth is weaker than querying the one authenticated native handle. Even a successful composition does not make RAW streams authenticated, nor does it establish post-open source immutability, safe publication, efficient generic whole-tree extraction or external signer authenticity. No new format, codec, Builder/Writer semantics, release, benchmarks, thresholds, or inherited evaluator weakening.

## Falsifiers / decision gate
FAIL if cargo fmt/build/test/clippy fail; C header cannot compile against both exports; either inherited independent suite regresses; one handle returns incorrect terminal inode owner; the CDC expected row hash differs from source or streamed output; the hardlink or RAW missing-hash controls falsely succeed; non-file/out-of-range/null failure buffers are wrong; the source archive differs from verified original; PACK conformance regresses; or an unexpected regression is explained away. A CI success must be bound to exact HEAD, not to independently passed ancestor SHAs.

## Resource and cost accounting
The metadata APIs are index-only O(1) lookups after open, with 32-byte caller buffer for SHA. The O17 streamed consumer hashes a bounded 64 KiB buffer; builder-produced CDC stream decoding may still incur bounded native per-blob allocation. Measure archive bytes, logical reconstructed bytes and actual bytes streamed; no end-to-end wall/RSS claim absent matched ABBA. Graph preflight cost and ABI symbol carrying cost remain debt. If native hash query has no incremental product leverage relative to existing Reader verify/extract, keep research-only.

## Discriminator / independent replication / concurrency
PR #340 and #349 are the source-exact independent parent controls. PR #351 already exercises hardlink publication/owner + PACK; it does not exercise same-handle indexed SHA. Keep any O17 tests on this branch and do not retarget/upstream-overwrite other agents' branches; late writes require a fresh check. Another activation owning this exact same-handle composition makes further implementation redundant unless explicitly established as independent replication.

## PARETOBONK and handoff
Alternatives: (A) productize O11/O15 secure full-tree extraction: larger unresolved platform/security surface; (B) invent a direct RAW hash commitment: format/overhead and missing-index challenge exposed by O12; (C) union existing source-exact ABI then falsify within one handle: cheapest next measurable integration gate chosen; (D) wait for owner merges: loses same-handle evidence and no concurrent owner observed. Success permits a bounded CDC+hardlink authenticated-publication experiment, **not** release. Negatives are retained without score gardening.
