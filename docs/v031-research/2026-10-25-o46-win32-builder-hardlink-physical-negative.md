# O46 Windows source-to-archive physical hardlink fidelity — independent negative

Date: 2026-10-25 UTC
Status: HOSTED NEGATIVE OBSERVED, exact-cause attribution **pending** until source-stat and archive-index diagnostic receipts execute.

## Original directly observed failure (do not rewrite)
- Parent O14 source-exact product head: `a8429ac195b1f1426b24eec3d5bd5ee0ab486c68`; O46 first executable research head: `a354f2edd01beca910952653a0da398c0f5fbebc`.
- Authenticated three-host test: [Actions run 40155875571](https://github.com/FCMO-AI/.CMPCT/actions/runs/40155875571). **Ubuntu PASS, macOS PASS, Windows FAIL, referee SKIPPED.**
- Actual Windows job `121057052814` reached installed authentic Builder/Reader extraction after creating a physical `os.link()` source and checking `os.path.samefile(source/owner,source/alias)` is true.
- Windows failed `assert os.path.samefile(destination / OWN, destination / ALIAS)` in `capture()` (line 127 on original head) after the member-byte `reader.read()` and extracted-file-byte checks passed.
- This is **not** a successful three-host O14 transfer result. It is a reproducible host-specific physical-filesystem-fidelity red on the inherited candidate, not yet a proven general released-v0.30 failure.
- The source `Builder.scan()` performs hardlink detection from `os.scandir()` entry `stat(follow_symlinks=False)` and tests `st_nlink > 1`; on Windows that stat source may differ from normal `os.stat()`. This is a **testable hypothesis**, not a confirmed explanation. An alternative is that a correctly encoded hardlink lost its physical ownership during extraction.

## Independent causal discriminator now implemented
- O46 now retains source `os.stat()` **and** `DirEntry.stat()` device/inode/link-count triples for source owner, alias and independent copy, preserving logical inputs without treating physical filesystem metadata as cross-host logical equality.
- It also saves authentic indexed K_HARDLINK rows/targets and extracted physical-identity booleans **before** failing; job remains FAIL on a single mismatched alias, no evaluator weakening.
- New workflow uploads the original diagnostic JSON even on a failed host step, while the CI job and cross-host referee continue to report the negative/blocked truth.
- Distinguishing observation: missing `K_HARDLINK` index row with DirEntry `st_nlink <= 1` despite os.stat reporting >=2 would attribute source enumeration as a plausible cause; a correctly present K_HARDLINK row with distinct output physical IDs would implicate extraction instead. Neither is asserted until hosted evidence arrives.

## Scope / non-promotion
O43 [PR #397](https://github.com/FCMO-AI/.CMPCT/pull/397) shows a later O38 installed Reader can materialize deliberately crafted authenticated hardlinks on Windows NTFS. That does **not** prove this earlier O14 Builder emits hardlink rows correctly from actual Win32 directory enumeration. Different source/fixture/proof layers must not be conflated. No shipping change, release claim, general Windows assertion or O14 scientific transfer credit; source-exact regression and raw negative evidence first.
