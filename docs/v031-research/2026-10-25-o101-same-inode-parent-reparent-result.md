# O101 — Same-inode output parent relocation invalidates earlier source-root exclusion

Date: 2026-10-25 UTC
Evidence class: **SOURCE-EXACT INSTALLED-PRODUCT ADVERSARIAL RESEARCH**. This is not a product fix or release approval.
Decision: **HYPOTHESIS CONFIRMED** for the scoped POSIX adversarial family; O99 remains effective on different-inode pivots.

## Pre-result prediction, provenance and non-interference

Original prospective question/hypothesis frozen in [O101 prereg](2026-10-25-o101-same-inode-parent-reparent-prereg.md) at `81373baf91702fef111ecbfbc522cde470f18c3a`, before creating the test and before the first hosted result. Candidate base O99 PR #455 `2fbdba24d0dfb29231c3710eb9b272a2aea89b9b`. O99 `src/cmpct/builder.py` original Git blob **`7400d0b0c2f8bf664e7022ae499cd0ab07b18968`**. The hosted court independently verified the installed Builder's Git-blob identity and the unchanged product-source diff.

The source-exact result-bearing experiment HEAD before writing this result note is **`9e93c4a8bd6408f50fe2d955cecac9068d85998d`**. [GitHub Actions run 40218371351](https://github.com/FCMO-AI/.CMPCT/actions/runs/40218371351) succeeded on **both Ubuntu 24.04 and macOS 14**. Test court included the unchanged O99 inherited tests and only three new O101 tests per host.

## Hypothesis versus observations

Before source scan, output path `active-parent/archive.cmpct` resolves through a symlink to a regular directory physically **outside** `source/`; archive leaf is initially absent. Builder records the parent `(dev,ino)`, scans one fixed-seed original 4096-byte leaf, then calls its normal output publication. A tightly bounded independent postscan actor renames the **same** external directory under `source/relocated-parent` and replaces the alias symlink to its relocated path. Physical parent `(dev,ino)` stays **identical**; resolved ancestry becomes **inside source**. The unmodified O99 Builder performs its actual parent `fstat` equality check and `openat` relative write.

Observed on both tested hosts:

- **O101_STABLE_EXTERNAL=PASS**: unchanged external parent allowed, original 4096-byte payload preserved, normal full archive Reader verification.
- **O101_DIFFERENT_INODE_REFUSED=PASS**: changed parent `(dev,ino)` rejected with O99's unchanged `ValueError('archive output parent identity changed after admission')`; no new archive and source bytes preserved.
- **O101_SAME_INODE_REPARENT_INTO_SOURCE=PASS**: same parent `(dev,ino)` and new in-source realpath verified before publication; Builder **returned success**, new CMPCT archive was created **inside source**, Reader `verify()` passed and read exactly the original leaf, and the source original leaf SHA-256 was unchanged. Builder returned `logical_files == 1` although the post-build physical root had the original leaf plus relocated destination directory containing the newly built archive.
- **Unchanged O99 controls**: stable regular, stable symlink parent/inode, changed-inode pivot into source and other external directory all PASS; Linux O_PATH execute-only parent PASS (the same platform-specific case SKIPPED on macOS).

**Interpretation:** authentic physical directory-inode binding does **not** preserve the earlier containment/authorization of its *location* in a mutable namespace. This is narrower than O91's one-link source-content clobber and different from O96's changed-inode rebind. The invariant `parent_fd (dev,ino) == preflight_parent (dev,ino)` held exactly; the predicate `out not beneath source` did not.

## Exact hosted receipts and independent controls

| Host | JUnit | Original source verified | Raw artifact | Artifact SHA-256 |
|---|---|---|---|---|
| Ubuntu 24.04 | 8 PASS / 0 SKIP / 0 FAIL | `7400d0b0c2f8bf664e7022ae499cd0ab07b18968` | [#12608064665](https://github.com/FCMO-AI/.CMPCT/actions/runs/40218371351/artifacts/12608064665) | `4cbe06eb08c30c8b0c08b07989e8416fcd50abd2538fc9ca0f9a649ebefa6747` |
| macOS 14 | 7 PASS / 1 justified Linux-only SKIP / 0 FAIL | `7400d0b0c2f8bf664e7022ae499cd0ab07b18968` | [#12607584443](https://github.com/FCMO-AI/.CMPCT/actions/runs/40218371351/artifacts/12607584443) | `30e365e553659796082a41b7d4f6e15bec0dc160094d3293de64df1ed76da554` |

Artifacts preserve `head.sha`, `builder.blob`, `instrument.blob`, complete JUnit XML, `court.log`, per-O101-case JSON (`dev/ino` before/after, pre/post realpaths, source and archive SHA-256, Reader verification), and `audit.json`. The independent audit step ran successfully on both hosts and required the *adverse-result* markers. A scientific test PASS is **not** an assertion that output publication is safe.

No artifact has been reinterpreted as released CMPCT behavior: experimental O99 remains unmerged in draft PR #455, based on v0.31 candidate; shipping v0.30/r24 is unchanged.

## Negative/self-critique and expected costs

This is an adversarial concurrent actor that can both rename a directory and replace a symlink between scan and publication. It is not an ordinary stable-tree failure, Windows result, privilege escalation, original-source-content corruption or universal proof that all postscan namespace writes are insecure. The archive is valid; the **location** of its creation violates the earlier exclusion. O99's improvement against final-component and different-inode parent pivots remains real.

The experiment measures **correctness**, not compression, create time, RSS, I/O, extraction performance or process-failure atomicity. POSIX supported file permission and source inode details were not varied. A path-identity recheck after writing would at best detect a violation after the file already exists in source. An extra pre-write pathname check does not turn mutable ancestor topology into a stable invariant against another concurrent rename.

## Decision and next lowest-cost action

**Confirmed:** parent physical identity is necessary for O99's claim but **insufficient** to preserve original parent ancestry when the same directory inode is moved. The O99 owner should choose a precise security contract (e.g., stable namespace prerequisite vs. stronger explicit location-custody guarantee) and use this exact hostile two-host court to test any candidate; do not regress the inherited O99 guards or claims. A new implementation from this research branch would duplicate ownership and is **not authorized** by the evidence.

Counterfactual: the cheapest prospective discriminator was to move the *original inode itself* into source after preflight, then verify that `fstat` remained equal. This transfers to all safety policies that use a stable object inode as a proxy for mutable namespace ancestry. It justifies a new **test**, not a rewrite of Discovery Engine normative policy.

**Status:** science decision changed; no codec/format/source implementation, no merge, no release. Current CI for the final documentation HEAD must be checked separately; do not transfer the source-HEAD receipt automatically to new HEAD.
