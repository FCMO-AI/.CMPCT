# J24I36d preregistration — one-header custody for fused CRC cost
Date: 2026-10-29 UTC
Status: **PREDICTION BEFORE IMPLEMENTATION**. Native candidate owner PR #765, current source exact `09ee165f3c74de7df65372a63a93b82115e3f695`. Parent #759 `e67ed337e78e021ba91f7bc6bdc271ae0ddd6b51` is a separate inherited correctness control. No main, version, format, frozen benchmark, comparator or release-gate changes.

## Problem / baseline
J24I36c source-exact Ubuntu in-process A/B twice measured positive fused-CRC cost (+2.308% and +5.89%) relative to native #759; all four adjacent pair medians in both runs favored the unmodified verifier. On current `vzip_dispatch.rs`, direct members first call `complete_member_identity`, which reads and authenticates a full CMA4 header; `verify_complete` immediately calls `checked_blob_layout` a second time and seeks/reads CRC32 at header offset 28. Compressed `read_range` may read the same physical header separately, but that is not this proposed mutation surface. One full logical SHA traversal remains mandatory.

## Primary falsifiable question
Can exposing the CRC field from the *same already-validated header read* that establishes the direct-member SHA identity remove redundant header seek/read work, without altering any physical/logical integrity semantics and with a repeatable same-source native verification cost improvement?

## Alternatives, controls and cost
A. Keep current redundant-header implementation: simplest, fully functional but measured overhead.
B. Add cached parsed headers at archive-open: may increase memory/lifetime complexity and stale-source risk; reject.
C. Return `(physical_sha, physical_crc)` from one validated CMA4 header read to the complete verifier; preserve the prior public helper for all unrelated decode paths via a wrapper. Choose C as the minimum reversible unit.
D. Skip/relax CRC or digest to gain speed: categorically rejected.

Preexisting #765 HEAD `09ee165...` is the exact *CRC-enabled* speed control, not #759 alone. Use one immutable installed 64×256 KiB Builder archive, pre-fusion candidate vs fused one-header candidate compiled independently in the same Ubuntu Actions job; alternate A/B/B/A and B/A/A/B with 24 warmup-excluded native in-process verifications per arm. Record raw ns, source SHA, archive SHA, all four adjacent pairing medians and the A/A variability envelope. The existing #759-vs-candidate cost court remains unchanged and must still report full original-to-candidate cost. Distinguish process compilation/startup from in-process verification. The new mechanism should reduce two header reads to one per direct member; CPU CRC work and hash work remain. Store byte, wall, CPU, RSS, temporary I/O as **unmeasured** unless actually recorded by a court.

## Predicted result / kill / disproof
Prediction: exact hash/CRC acceptance/rejection remains unchanged in all five direct codec families and real symlink, while median component verification improves vs 09ee on the same runner (expect small, not promise of eliminating all +5.89% overhead). A nonpositive or noisy A/B, non-portable behavior, new error-class discrepancy, valid golden rejection, accepted CRC-only/payload mutation, or A/A variability of same scale blocks declaring a speed win. A small gain without product significance can still justify retaining simpler custody only if complexity does not rise materially; otherwise keep baseline. No release credit from this court.

The stronger independent controls remain frozen builder-independent RAW/Zstd/Deflate, held-out WAV-FLAC and dictionary-Zstd vectors, original physical symlink, payload SHA mutation, Rust compile/format/clippy/CI and the complete real installed suite. Test macOS and Windows where available. The documented J24G43 zero-size nonempty Zstd frame defect is *outside this optimization* and must not be silently repaired, promoted, or counted green here.

## Expected decision
If exact-head same-input A/B consistently improves and inherited integrity courts remain green, preserve the optimized native candidate under PR #765 for parent #759 owner review. Otherwise revert the optional optimization, preserve the negative measurement and focus on CRC computation cost or changed physical ownership rather than local threshold gardening. Do not update `docs/discovery/STATE.json` merely because a new prereg exists.
