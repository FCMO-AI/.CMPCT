# O51 — descriptor-bound Writer source admission: executed scientific result

**2026-10-25 UTC.** Research result and bounded product evidence; not a merge/release authorization. See the immutable [O51 preregistration](2026-10-25-o51-writer-fd-source-prereg.md), [PR #406](https://github.com/FCMO-AI/.CMPCT/pull/406), [Issue #403](https://github.com/FCMO-AI/.CMPCT/issues/403). Historical O49 baseline negative and its original `transactions.py` blob `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c` remain intact.

## Primary causal result

The unchanged historical Writer called `source.read_bytes()` **before** file-type admission, and a genuine no-writer FIFO source blocked an actual installed `cmpct update` on both Ubuntu/macOS for >3 s. That historical baseline was preregistered and completed in [O49 run 40157632143](https://github.com/FCMO-AI/.CMPCT/actions/runs/40157632143). We do not relabel it as a product PASS.

O51 changes one source file, `src/cmpct/transactions.py`, exact new Git blob `130638744d26dbf71a3ddd49b2545db9eb933ed4`. The Writer opens a source with `O_NONBLOCK` on POSIX, observes `fstat` of its **opened descriptor** to require a regular file before reading, then uses a second descriptor `fstat` to detect directly observable in-place changes and bind mode/mtime to the same opened inode. Windows retains ordinary-file open semantics; no POSIX FIFO claim for Windows. Symlink-to-regular is still followed. The on-disk revision remains 24.

## Direct installed-product result

Candidate source-bound HEAD `dfaac5b9ca0b3e87c6927f7b70ba757c42c9e1f8`, [hosted workflow 40159802389](https://github.com/FCMO-AI/.CMPCT/actions/runs/40159802389): **Ubuntu 24.04: 9 PASS / 0 SKIP; macOS 14: 9 PASS / 0 SKIP; Windows 2025: 3 PASS / 6 legitimate POSIX-only SKIP; all jobs SUCCESS.** The workflow checks the actual external `site-packages/cmpct/transactions.py` Git blob, not the checkout source, and emits JUnit and logs on success/failure.

The real, authenticated revision-24 Builder→Writer CLI→Reader cases cover: ordinary regular update; a genuine non-writer FIFO; symlink→regular success; bound AF_UNIX socket refusal; regular path replaced by FIFO just before the **actual** `os.open`; source pathname replaced with a *different regular inode immediately after open*, with the archived bytes/mode/mtime still from the originally opened inode; directory rejection on every platform; symlink→FIFO rejection; and **complete archive byte-for-byte identity** for stable regular updates against a control that substitutes only the exact historical `Path.read_bytes(); Path.stat()` primitive while keeping the rest of the Writer/codec/source tree identical. Each negative checks the original archive's complete SHA and last valid member, not just exit status.

Result artifacts / SHA-256:
- Ubuntu `12585830789` / `b332301617e5249c19476e939366d5e617317c41703aa1dca4d15c6f159a5d68`
- macOS `12586455550` / `e023be65f6e8fd04621a60a8287fcff75dd536f18a5109168e3a7203398936cc`
- Windows `12586475234` / `d1c32a824b7e41d151b3068601fd2544c183a10d634eab4550c4a7542ae4322e`

The initial [O51 workflow 40159215635](https://github.com/FCMO-AI/.CMPCT/actions/runs/40159215635) had macOS **one fixture failure** `AF_UNIX path too long` before product execution of the socket case; its remaining four adversarial cases passed, and Ubuntu passed all. The follow-up changed only the UNIX socket fixture path to short private `/tmp` while retaining a real bound socket and original rejection. This negative is preserved, not silently deleted.

## Economic cost / limits

Separate local warm-filesystem CPython 3.13 source-open *primitive-only* micro (nine randomized alternated blocks × 30 samples/arm/block, 270 samples/arm/size, **not** CMPCT product economics) measured old→candidate medians: 4 KiB 6.139→6.680 μs (+0.541 μs); 1 MiB 41.292→42.183 μs (+0.891 μs); 8 MiB 407.913→411.558 μs (+3.646 μs, noisy/mixed block directions). Those numbers cannot earn archive-create/extract speed or release credit.

The Writer **still materializes the whole regular source in memory**, may block on exotic/network filesystems, and cannot authenticate adversarial in-place regular-file mutations that mask `fstat` changes. This is **not** a full snapshot/TOCTOU/atomic transaction proof. Existing transaction-wide Writer lease, namespace and salvage ownership lives in [PR #247](https://github.com/FCMO-AI/.CMPCT/pull/247), [#295](https://github.com/FCMO-AI/.CMPCT/pull/295), [#304](https://github.com/FCMO-AI/.CMPCT/pull/304), [#311](https://github.com/FCMO-AI/.CMPCT/pull/311). In particular #311 source-exact `transactions.py` blob `a3b9c3375ed19f0b37d40ee47ead7b5d5b8905ee` retains `source.read_bytes()` **inside a serialized Writer**, so it requires separate integration and same-lease adversarial concurrency proof. No other owner branch was edited.

## Gates and next decision

The hosted **focused installed source-court is PASS** for the exact executable HEAD above. That does **not** imply the complete general suite, all installed native packages, full Windows named-pipe portability, native/fuzz, release comparator or Writer multi-process lease union is green. Latest generic workflow may be administratively SUCCESS with effective `performance` job SKIPPED: **do not count it as official r24/ZIP performance evidence**. Preserve all inherited v0.30/r24 release gates and never soften the frozen comparator. The next highest-leverage test is composition with #311's transaction-wide lease and already-authenticated Reader, plus source-error no-archive-change and multi-writer liveness under the real combined Writer.

**Decision: original FIFO source availability defect confirmed; O51 source-admission fix survives direct genuine installed Linux/macOS controls with Windows normal-update regression and stable-source archive-byte identity; full release promotion NOT EARNED.**
