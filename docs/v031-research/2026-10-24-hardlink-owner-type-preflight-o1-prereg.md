# O1 prereg — strict preflight must resolve hardlink owners to ordinary files

**Date:** 2026-10-24 UTC; prospective independent held-out strict-validation question after the O0 signed non-directory ancestor outcome. **Exact O1 base:** PR #339 `3995a4b96b2b977ac1d0ec75fa5944778b47302e`; O0 validation trie already implemented. Do not modify O0 test or evaluator criteria.

## Prediction
The unchanged `preflight_archive()` walks hardlink cycles and checks owner name existence, but does **not** check the terminal owner's kind. A genuine r24 Builder archive containing an actual directory `folder`, with one authenticated new `K_HARDLINK` alias naming `folder` as its target, will be structurally **accepted by strict preflight** while the same real Reader extraction cannot materialize a POSIX/Win32 hardlink to a directory. The negative has to establish intact physical bytes, SHA-consistent both indexes, valid control source, exact-source preflight acceptance and extract-side failure. No re-labeled fake fixture counts.

## Cheapest discriminator and controls
Append one new self-contained **same-fixture** assertion to the dedicated signed-preflight court, requiring `ValidationError` with 'hardlink'+'regular' diagnostic; O0 cases and legitimate ordinary-file hardlink controls unchanged. Run on exact original source and preserve expected negative. A clearly acceptable and simpler control is leave preflight as index-only and document the non-regular alias weakness; it loses strict structural truth and consumer portability, so prefer narrow proof. Do not alter Reader or on-disk format, archive Writer, platform host policies, or release thresholds.

## Smallest bounded candidate
During existing row validation record canonical path -> kind (already stored in seen set). After existing hardlink cycle traversal, verify the terminal resolved owner is `K_FILE`. Acyclic chains that resolve to a normal file remain admitted; chains ending at a directory/symlink are structurally incompatible with portable hardlink materialization. Complexity O(number of file rows + current hardlink-chain work); no content decoding or filesystem writes added.

## Kill conditions, negatives and portability
Retire this hypothesis if existing strict preflight already rejects the signed directory alias on source, or if Reader can legitimately reconstruct a portable directory-hardlink relationship with identical declared semantics. Preserve valid regular owner aliases, nested ordinary files, row order controls and all O0 signed-tree rejections. Candidate must pass original tests unchanged, include exact-head multi-platform CI, and leave inherited general/release/performance reds intact. This is not a declaration that strict preflight proves all destination security or metadata fidelity.
