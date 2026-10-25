# O84 — Prospective Builder source-fidelity × output ownership composition

Date: 2026-10-25 UTC. State: **PREREGISTERED BEFORE O84 PRODUCT EDIT OR OUTCOME**. Research/product candidate only; no release authority. On-disk format stays revision 24, released v0.30.0 remains immutable.

## Exact authority and ownership

Canonical development is `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Compose on the exact current O80 PR #437 head `4d65f1bcbc68f1ad770e706197ece8355dd10637`, Builder Git blob `37833f09dee4671b8ca6f3f3690a7fdebfbc4c70`. O80 already includes distinct O64 NTFS named-stream refusal, O65 xattr observed-error refusal and O67 in-tree hardlinked-symlink refusal with O47 Windows regular-hardlink ownership. Output/source alias detection is separately owned by O81 PR #439 at `1d11268417736e464742ccbedd818ecd25724da2`, Builder blob `d252e3244d51f5000269a5c759531a14015f39cd`, unchanged adversarial test Git blob `f23cd936ace4019e654f5042f3cb476e3682f2a2`. Original v0.31 Builder blob is `663ef0922992b1fbb8f19e6eea88d55c10a56044`.

Do not transplant the full O81 Builder (it would delete O80's source-fidelity fixes), rewrite O80/O81 owner branches or claim release. There is no open PR claiming this exact composition at the time of preregistration. Before late writes recheck owner HEADs and Git truth.

## Primary falsifiable question

Can O81's output/source physical-identity and in-tree destination guards be composed into O80 without dropping NTFS/xattr/symlink fidelity, altering ordinary archive bytes, or falsely refusing safe external outputs?

**Prediction:** unchanged O80 inherited owner tests and unchanged O81 eight tests pass against one installed package in Linux/macOS/Windows; a mixed source with xattrs, ordinary hardlinks and independent symlinks rejects an external output hardlink without mutating source, then admits a disjoint output and reconstructs exact bytes/topology/available xattrs. Original historical Builder continues exhibiting the O81 clobber negative. Any omitted mandatory test, source SHA drift, unsupported stream silently admitted, xattr silently dropped, source-overwrite, byte mismatch on controlled disjoint archive, or incorrect accepted destination falsifies promotion.

## Mechanism and strongest controls

Integrate only O81's initial `realpath/commonpath` and existing-target multi-link admission, plus one source-inode comparison using O80's already-computed `ownership_st` (avoids redundant Win32 `stat` used separately by O81). Keep O80 ADS/xattr/symlink-hardware paths byte-identical. Controls: unchanged inherited O47/O48/O50/O57/O61D2/O64/O65/O67/O80 suites; unchanged original O81 eight tests; exact-historical-Builder negative and whole-archive A/B with the same physical source; newly written mixed interaction checks. Dedicated exact-head installed-wheel GitHub Actions across Ubuntu/macOS/Windows, source fingerprint binding and raw JUnit counts/skip honesty.

Simpler alternative is to ship O80 and O81 independently: it cannot establish joint preservation of two source-identity boundaries. Whole-file O81 transplantation would erase O80 and is rejected. Full descriptor-root snapshot addresses a stronger concurrent mutation model already owned by O52; not in O84.

## Resource, semantics, and kill/narrow conditions

Normal external single-link output adds two canonical-path resolutions and one output `stat`, but no per-source-regular-file identity syscall over those already paid by O80. Existing external hardlinked output enables O(n) cheap comparisons to already-scanned identity records. Time/RSS/temporary I/O/full release parity **unmeasured** until a real same-source ABBA; no speed claim. No format change.

O81's deliberate rejection of in-tree output is an API narrowing and POSIX path/inode races remain unresolved. No assertion of atomic tree snapshot, power-loss durability or hardlink-neutral `os.replace`. If composed tests fail, preserve negative with exact HEAD and narrow/falsify; never modify inherited comparators to pass.

## Next decision

Only a genuine installed-product focused court can turn compatibility inference into evidence. Official benchmark and release promotion remain separately gated.