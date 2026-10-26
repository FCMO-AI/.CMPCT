# O168 — Preregistered reverse one-archive macOS→Linux topology test
Date: 2026-10-26 (UTC)
Status: PROSPECTIVE; no outcome observed at preregistration.

## Source, distinct question, and ownership
Base is O165 PR #503 exact head `9e9bb88e7a2c96749fbd27880f72517d9e975e67`, whose authentic Linux→macOS one-binary test passes within a *portable* O155 topology projection, while strict physical symlink modes differ. O155 and O162 own the immutable strict oracle and genuine installed-product fixture. O14/#372 and O46/#400 tested independently built cross-host reproducible archives, **not** one macOS-built archive transported into a Linux Reader. No present open PR owns the reverse macOS→Linux one-binary test. This question measures cross-host **directional** interoperability; it is not a second implementation of format, Reader, Builder, or oracle.

## Primary scientific question and prediction
Can one macOS 14-built, genuinely installed CMPCT revision-24 archive be SHA-bound through GitHub artifact transfer to an independently installed Ubuntu 24.04 Reader, verifying and reconstructing O162's unchanged 10-entry typed POSIX tree without losing data, hardlink equivalence, symlink targets, file/dir modes or names? Prediction H1: yes for O165's prospective portable projection, with any strict metadata differences isolated **only** to physical symlink `mode` (expected direction macOS 0755 → Linux 0777 from O162/O165 independent host observations). The raw strict manifests are retained, not normalized in place.

Disproof: any different archive bytes/identity between stages, invalid r24 magic, installation/worktree source drift, install/verify/extract failure, unsupported/unsafe target, content/type/name/direct hardlink mismatch, or **any non-symlink-mode physical delta**, including differences in non-symlink POSIX mode, defeats H1. If unexpectedly strict-equal, record that result instead of inventing deltas. If host prerequisite blocks fixture construction, classify separately from product fidelity.

## Strongest controls and alternatives
- Positive same-host control: macOS independently installs exact source, creates archive exactly once and verifies/roundtrips that identical archive under unchanged O155 strict witness before upload.
- Transfer/authenticity control: hash and byte size of actual `.cmpct` binary, not just logged SHA, must match at Linux receiver; source SHA and installed engine Git blobs must match.
- Differently rooted hostile controls on genuine Linux extracted tree: sever one hardlink while copying identical bytes/mode; separately retarget an in-tree symlink while retaining its type/mode. Both must change the **portable** digest (no metric/expectation watering).
- Simpler control: compare only payload hashes. Rejected as insufficient to prove physical relationship and metadata semantics.
- Redundant independent archive-building on Linux. Rejected as not a transported-binary test (already explored in O162/O46).
- Shipping universal mode normalizer. Rejected: would change lossless metadata contract based on synthetic evidence and duplicate O14/O46 work.
- Stronger held-out Unicode/xattr/race/Windows matrix is downstream and not implied by a 10-entry proof.

## Evidence class, economics and scope
Research plus installed-product interoperability evidence, **not** release promotion or whole-product performance. Two hosted jobs, one source archive, source-exact historical O155/O162/O165; executable source + JSON receipt + SHA + uploaded original artifact. No changes to `src/`, `native/`, `docs/discovery/STATE.json`, evaluator, thresholds, format, release or prior test code. Record actual complete archive bytes and process-inclusive one-shot timings as observables, not A/B speed claims; no new CPU/RSS/temp I/O/large-workload guarantees.

## Decision and next boundary
Positive result supports **bidirectional** (two separately evidenced one-way experiments) narrowly portable topology for supported POSIX fixtures. It does not prove arbitrary filesystems, strict physical identity, xattrs/ACL/uid/gid/mtimes/sparse allocation, invalid-byte names, concurrency, crash recovery, no-loss full general CI or v0.31 release readiness. Negative result opens a scoped Reader/metadata diagnostic, not release policy changes.

## Counterfactual discriminator
Before spending on a full interoperability matrix, invert only the source/destination roles of O165 with the original strict receipts and one byte-authenticated archive. This can falsify directional asymmetry without reinventing fixtures or comparators. A discovery-policy change requires repeat evidence, not this one episode.
