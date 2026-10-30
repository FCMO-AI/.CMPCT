# J24I56 — Prospectively compose O47 Win32 source ownership with J24G79 signed Reader court

Date: 2026-10-30 UTC. **FROZEN PRE-IMPLEMENTATION QUESTION; RESEARCH / PRODUCT-CORRECTNESS COMPOSITION ONLY. NO MERGE, RELEASE, VERSION, FORMAT, GATE OR PUBLIC-PERFORMANCE CLAIM.**

## Exact authority / baseline
- Published canonical: CMPCT v0.30.0, on-disk r24. The current v0.31 work remains unmerged.
- This isolated branch starts **exactly** from #827 / J24G79 head `d75763393cf2f6b638447bf8dff02868a5207b6a`. Inherited Builder blob `a2160a2f6b1ca3ef8cd94897cb68bb2fcb74ebc2`.
- #827 measured genuine signed mixed 63-generation Reader/recovery parity and POSIX physical hardlink/xattr fidelity, but **Windows failed to encode the original physical hardlink**: authenticated `z-alias.dat` was ordinary `K_FILE=0`; its Windows SUCCESS was logical only. Original run #41048277198 and physical audit are inherited, not new proof.
- Independent donor #401 is **unmerged** at `29d9688ae6bff6d1eccc27f019893866abe5b5c3`, exact Builder blob `6f60dfe63742ff4b777f959a15d6fb828ae29610`; actual O47 three-host installed test #401 run #40156468439 passed. The donor changes only Win32 regular-file physical ownership capture using `os.stat` instead of zero-valued `DirEntry.stat`, keeping cached metadata and rejecting a type-change race.
- Do not alter shared discovery STATE (owner #574); no concurrency protocol/tool exists at currently fetched main. No duplicate narrow cross-integration PR was found in the inspected open frontier.

## Scientific question / preregistered hypothesis
Does **transplanting exactly the O47 Win32 identity guard** into J24G79's stacked Builder preserve the successful Linux/macOS private-owned-Reader signed-journal court and *upgrade* the Windows control from logical-only to **physical hardlink fidelity**, without falsely claiming Windows xattrs?

**H1 prediction:** A genuine Windows `os.link` source, across 21 renames + 21 deletes + 21 puts (63 journal updates, full checkpoint), encodes `z-alias.dat` as authenticated `K_HARDLINK=3` pointing to `a-owner.dat`; `OwnedCMPCT.extractall()` restores `samefile` owner/alias; all three Reader classes agree on full index, bytes, strong verify, recovery; separate inherited O47 test continues to reject same-byte independent files as hardlinks. Ubuntu/macOS preserve physical inode and native signed xattr fidelity with identical original Reader source. Windows xattr support remains **unclaimed**, not tested.

## Strong controls / alternatives
- Strongest simpler control: #827 unchanged per-host source, original exact-host receipts, and #401 independent installed-package O47 physical regression; this *composition* tests only their interaction.
- Do nothing keeps untrue Windows physical fidelity (negative established). Rewrite Reader to infer hardlinks by equal content would violate filesystem semantics. Copy all #401 Builder bytes would overwrite independent #820 changes; forbidden. Apply only donor's minimal Win32 identity block.
- Original #827 independent no-CMPCT signed-wire parser and raw 64 signed footers is retained; tighten its platform verdict and require authenticated hardlink tuple **also on Windows**, preserving corruption and forged-receipt rejections.
- The original O47 same-byte-but-different-inode and reproducible-byte-repeat test is copied byte-identically; run it on all three hosts.
- Bound the experiment to the original 130-entry signed fixture, 119 final members, three hosts, and 63 updates. No mass-scale or create performance inference.

## Disproof and decision
Fail/stop if any platform: cannot create genuine source hardlink, encodes alias as two regular files, loses source/extracted inode identity, coalesces equal-byte independent copy, changes signed index/footers/recovery/Reader equality, drops POSIX native signed xattrs, fails any originally strong verifier, skips an actual required platform, or cannot independently reconstruct signed metadata. Preserve infrastructure failures separately.
Success on Ubuntu/macOS/Windows means **source+Reader composition correctness evidence** only, not released/native Rust correctness, full performance/release parity or new product capability on main. Win32 added `os.stat` per regular source file carries unmeasured CPU/I/O cost; official r24/ZIP performance and full General Tests must be reconciled before product promotion.

## Source/ownership boundaries
Modify only stacked `src/cmpct/builder.py` with the O47 donor physical-identity block, research J24G79 court/referee for stronger three-host assertions, copy O47 unchanged exact focused test, and add a new source-bound workflow. Preserve existing #827 and #401 PRs/branches and their evidence. Claim no physical Windows xattr fidelity. If CI runs independently, record exact run/head/artifact and leave publication/release unlocked.

## Why this frame now
#819→#825 repeatedly narrowed, but did not solve, a noisy Builder timing-family regression. #827 independently revealed a crisp **non-noise correctness deficit** that is directly addressed by a proven different family's source-ownership correction. A decisive integration costs one narrow Win32 code transplant plus original hardlink/source/SHA courts, and improves platform semantics rather than buying another ambiguous timing microbenchmark.
