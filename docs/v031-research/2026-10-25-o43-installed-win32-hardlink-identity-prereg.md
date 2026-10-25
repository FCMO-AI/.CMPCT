# O43 — Windows installed-wheel physical hardlink identity (preregistered)

Date: 2026-10-25 UTC. Stage: prospectively registered BEFORE touching test or CI code.

## Baseline and narrow unclaimed question

CMPCT O31/O35b/O38 already read/verify/extract the same signed r24 mixed-separator multihop hardlink archive from clean-installed wheels on Ubuntu, macOS, and Windows. Original O35b asserts POSIX inode equivalence only; its Windows PASS certifies content and lexical target resolution **but explicitly does not certify hardlink physical identity**. Source candidate O38 is pinned to `dffc6da03b588e209843f2fc6e219e5bce3a7800`; its shipped Reader blob is `4aee9e8ddf50ff3c3e0db20ebf7671e2ac477867`. This court is independent from O38 startup performance, #393 O39 32k scaling, and #395 source witness. No overlapping physical-identity owner found in the current open PR shortlist.

**Question:** Does the clean-installed Windows Reader reconstruct all four logical hardlink members as one actual Windows filesystem file identity, rather than four distinct files containing equal bytes?

## Prediction, stronger control, independent evidence

Reuse the *same signed O35b archive*, same source SHA and unchanged hostile parent-escape/cycle controls. After extraction use Python `os.path.samefile` and independently query Win32 `GetFileInformationByHandle` on each extracted regular leaf. Assert equal tuple (volume serial, 64-bit file index), at least four hardlink names for owner, and positive equality for owner and three aliases. A same-byte, separately created regular file must have a different file ID and `os.path.samefile` must reject it. On POSIX retain the original POSIX inode assertions; do **not** substitute Windows metadata as a POSIX proof. The native Windows API control defeats a false positive caused by content equality or a degenerate `st_ino`. All four entries must still match exact SHA/ranges and all two signed negatives must reject.

The *simpler control* is existing byte equality; it is insufficient because duplicate independent regular files satisfy it. The stronger samefile + native file ID and same-byte distinct-owner negative can decide the additional physical-fidelity claim without a new archive representation or product implementation.

## Kill/narrow conditions

Reject the Windows physical-hardlink claim if any hardlink alias has a different native file ID, the separately written same-byte control has the same identity, `os.path.samefile` disagrees with Win32 evidence, the host does not provide the required native APIs, a signed negative becomes accepted, the source or actual installed package mismatches the pinned O38 Reader, the effective Windows job is skipped, or the aggregated receipt fails to require the new proof. Any infrastructure-only failure must be kept distinct from product loss. Do not mark absent or skipped evidence PASS.

## Cost and safety law

No changes to Builder/Reader/Writer/Rust/on-disk revision, official r24/ZIP comparator, thresholds, fixture bytes, release metadata, original physical SHA or timing boundaries. Additional work is a handful of Windows file-handle opens and samefile/stat calls inside already-budgeted installed-wheel CI. These are functional checks, not performance results. Do not claim race-free containment, NTFS behavior on all hosts, ACL/xattr fidelity, or user-created hardlink behavior outside the measured synthetic clean installed-wheel filesystem. Preserve original 21 effective installed-package jobs, 15 Python compatibility tasks, source SHA and existing 3-host positives/negatives.

## Admission and release

Positive exact-head Windows file-identity evidence may strengthen O38/O31 filesystem-fidelity conformance but is **not** compression or release credit, and does not authorize merges. Negative results preserve the simpler preexisting O35b content guarantee without erasing the failure. Full v0.31 product release remains gated by its own release law; current v0.30/r24 unaffected. Communicate decision and concrete hosted artifact to the owning O38 PR without modifying that owner branch.
