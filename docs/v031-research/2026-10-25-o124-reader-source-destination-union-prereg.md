# O124 — Reader static destination/own-source inode protection composition: prospective preregistration

Date: 2026-10-25
Status: PREDICTION FROZEN BEFORE THIS BRANCH'S PRODUCT CODE MODIFICATION
Repo: FCMO-AI/.CMPCT
Exact inherited owner: PR #294 head `700fa74df7d9101b3d00322ab5b3606ee64faf88`, stacked on PR #269 head `0273c628872dce672936aa0ddd555ed10a900bf7`.
Independent source-inode guard owner: PR #468 head `e4eedabb7eec8fe97e9833bd775077d3f385ec4c`; released/development original Reader `e716233403dabd0966863c45635e18fa5ac6afb8`.
No upstream branch changes authorized; this experiment owns only a draft composition branch.

## Primary scientific question
Can the original source-archive inode guard from O118 be added **without weakening** PR #294's existing POSIX symlink-ancestor and outside-hardlink-leaf protections, including safe opt-out, ordinary single-link reuse, chunked/CDC replacement, S_PACK/S_VZIP and rejection before partial output? Is there an inherited gap the #294 owner does not close: *single-link same-path source archive overwrite*? The original O118 court already demonstrated its standalone failure/repair; this experiment is about joint implementation and unchanged tests, not rediscovering that failure.

## Baseline and mechanism
PR #294 adds a static `lstat` preflight when `safe_symlinks=True` but checks against external hardlink aliases only when `st_nlink>1`. A source archive stored at its destination member path may have one link (`st_nlink==1`); that path is not rejected as an unsafe external hardlink or symlink. The Reader's direct `O_TRUNC` path can therefore overwrite the archive it is simultaneously reading. In contrast, O118 independently compares the opened archive's `fstat` device/inode to `os.stat` (following symlink) for every existing non-directory output leaf before writing, and rejects all static aliases. Transfer *exactly* that guard into the #294 source after canonical path verification and before the owner's destination preflight, retaining all existing semantics.

## Prospective predictions / falsifiers
1. Authentic installed #294 parent: a valid same-path single-link alias still reports success or changes source bytes, unlike a correctly guarded composition. A failure to demonstrate this gap narrows novelty; it does not permit inventing a defect.
2. Composed candidate: **all nine** unchanged PR #294 functional controls pass, including ordinary single-link reuse, unchanged outside hardlink victims and explicit `safe_symlinks=False` behavior.
3. Composed candidate: all original O118 source-alias cases reject with its original diagnostic, preserving source SHA and no partial member writes, while a clean extraction succeeds and reproduces original bytes.
4. Stronger independently rooted control: source archive source inode equality must be proven by `fstat` versus `stat`, not solely matching file path strings; positive read/verify and source SHA are mandatory.
5. If O118 preflight masks the parent's expected outside-hardlink diagnostic, breaks an ordinary overwrite, introduces Windows/macOS regressions or creates a source mutation, reject composition instead of adjusting tests/evaluators.
6. All archive bytes/format revision, canonical parser, existing historical tests, source SHA evidence, and release gates remain unchanged.

## Alternative designs considered
A pathname comparison misses hardlink and symlink aliases. Detecting `st_nlink>1` cannot catch same-path single-link source destruction. Full fresh-inode staging (PR #297) is promising but adds filesystem metadata/inode and temporary I/O tradeoffs and does not itself prove archive-source custody. Fully fd-relative root-constrained publication would be stronger against races but is a larger independent architectural owner. One additional O(N) `os.stat` pass is a bounded research candidate, not yet an economic optimization.

## Evidence tier, risk, and causal interpretation
First rung: exact published historical patch and inherited code inspection. Second rung: unchanged original #294 and O118 installed Reader courts on genuine Builder-generated revision-24 archives, independently installed original, parent and candidate code; actual byte/inode witnesses. Third rung only if the court survives: full tests and same-runner performance gate. No product release credit from green focused tests.

Source identity, provenance and direct negative controls must be recorded per CI run; raw artifacts and JUnit records are needed. Run Linux and macOS where filesystem inode semantics and original O118 corpus have evidence. Windows requires separate product-level validation. Source code and tests are public-safe synthetic only.

## Limitations and kill condition
This is **static-only**. `stat` followed by pathname write remains susceptible to TOCTOU, and `st_dev/st_ino` is not a universal immutable filename/capability proof. A symlink ancestor can be replaced after preflight. User-specified root creation occurs before the preflight in the inherited Reader. The new O(N) path-stat pass adds CPU/syscall work that must be measured before promotion. Cross-platform alias semantics remain unmeasured. Failure to preserve any ancestor/hardlink/correct extraction control kills this candidate.

## Decision and handoff
If both historical courts survive unchanged on the exact candidate and the #294 same-path negative is directly confirmed, this is a positive **integration candidate**, not a complete reader-safety solution and not a release. Notify owners #294/#468 with exact identity, tests, costs and remaining TOCTOU debt. Do not touch `docs/discovery/STATE.json` unless project-wide decision truth changes and competing owner #440 is reconciled. Never alter benchmark thresholds, comparative semantics or immutable original research predictions.
