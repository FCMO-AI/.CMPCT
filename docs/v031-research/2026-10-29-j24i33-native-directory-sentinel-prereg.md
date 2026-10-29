# J24I33 preregistration — authentic r24 directory sentinel × native admission

**Frozen before instrument/code; 2026-10-29 UTC.** Research-only, stacked from J24I30 #754 exact `0c99eca3890b7fb4a7625d9f11152fac5cf34a61`. Published `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains v0.30.0/r24. No format, product, evaluator, release or frozen benchmark edits. #755 owns the eventual native fix; this independent narrow court establishes whether the problem affects authentic ordinary trees.

## Baseline and scientific question

J24I30 [#754](https://github.com/FCMO-AI/.CMPCT/pull/754) already established **on Ubuntu and macOS** that native `parse_hash` rejects synthetic symlink row `b''` while Python accepts it, and native complete verification skips symlinks. In the inherited actual Builder source blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`, nested directories are emitted as `[rel,K_DIR,mode,mtime_ns,0,b'',None]`; `native/cmpct-core/src/lib.rs` blob `463c50633be74423e92a074b7d7577db6a4b0cf9` invokes strict `parse_hash` on every row without a directory exception. Static code strongly predicts real everyday archives cannot be opened by the native reader, but no authentic native directory-tree run has yet been executed.

**Primary prediction:** exact installed `Builder(root containing nested directory/payload.bin)` produces genuine r24 with `K_DIR` and `b''` and a valid nested file; installed Python preflight/read/verify succeed, but unmodified native `Archive::open` rejects the actual file-row `b''` with `invalid logical SHA-256 length`. A byte-identical no-directory control with the same nested file payload but at the root must be accepted by Python and native, and native verify must authenticate its regular payload (strong simpler control).

**Kill/narrow conditions:** native accepts the actual directory tree; Python rejects it; the archive has no directory `b''`; the no-directory control also fails; any mismatch attributable to builder installation/format/CI rather than the hash sentinel. Any such result kills the strong claim and must be preserved.

## Experimental design

- Genuine source: one empty nested directory plus one nonempty nested directory with `payload.bin`; both contain real `K_DIR` rows with raw `b''`. No symlinks required for the primary question.
- Real no-directory Builder control with same payload bytes, one root regular file, identical Builder settings.
- Derived second *diagnostic* case: structurally valid re-signed index with only directory row `b''` changed to `None`, both index copies/hash/footer rewritten; physical payload bytes remain byte-identical. It must allow Rust admission and full regular-file verification, establishing that `b''` is causal, not merely correlated. This derived file is not historical Builder output and earns no product compatibility credit.
- Cheap hostile countercontrol: re-signed directory row with one-byte nonempty digest `b'X'` must be rejected by both Python preflight and native; never normalize arbitrary wrong-length hashes.
- Python installed from exact source; Rust compiled from same HEAD; Ubuntu and macOS independent hosted jobs. Preserve physical archives, checksums, raw receipts, stderr, CI source SHA.
- Detached auditor independent of CMPCT imports checks native r24 header, dual indexes, hashes, footers, physical blob/frame/CRC/SHA and byte-identical data span across derived cases.

## PARETOBONK and ownership

This is a cheap causal falsifier, cheaper than changing Rust immediately or extending cross-platform packaging. Reuses the J24I30 successful installed-source pattern; no competing native implementation or duplicate #750 Python SHA fix. No numeric compression, create/extract speed, RSS, security or release credit. Never suppress the older #754 scientific red when a later product fix eventually inverts it. If confirmed, authorize a separately preregistered minimal native change that treats **only empty binary SHA** as optional absence, leaves nonempty invalid lengths rejected, retains mapped-member mandatory SHA constraints and proves native symlink completeness independently. #755 remains native owner.

**Counterfactual question (after evidence only):** would the original r24 Builder directory row and native strict parser comparison alone have been prospectively sufficient to skip the synthetic symlink sentinel study? Record only a transferable rule if repeatable; no Discovery STATE edit without a real decision-changing frontier update.
