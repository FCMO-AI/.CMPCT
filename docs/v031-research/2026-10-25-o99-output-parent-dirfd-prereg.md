# O99 — descriptor-bound output parent for postscan namespace pivots (prospective)

**Status:** preregistered before O99 product edits/tests. **Date:** 2026-10-25 UTC.
**Episode:** E-20261025T172206Z-15aac3f81-output-parent.
**Authority:** released v0.30.0/r24; canonical v0.31 branch @ 4545d7d5; prospective product owner O93 PR #451 HEAD 15aac3f81c23e0a54ae66de3f6b2146642afa350. Original Builder blob 7214a46b781bb10051e6782ba7731989ebf05edb. No canonical release promotion or format changes.

## Decision-making prior evidence and ownership
O96 PR #454 (science-only, no Builder edits) confirmed under authentic installed O93 source that an attacker swapping a symlink *ancestor* after Builder.scan can redirect a previously absent output into the source root; two-host court run 40216220159, unlike O91's final-leaf swap already refused by O93. O96 remains independent evidence owner. O75/O78 own failure-atomic versus output-inode semantic tension, not changed here.

## Primary question / falsifiable hypothesis
Can an existing parent-directory identity witness plus an **open parent-directory descriptor** at the final leaf-open boundary refuse the O96 postscan symlink-ancestor rebind, while retaining O93's original leaf-descriptor custody, ordinary symlink-to-regular behavior, inode/hardlink/xattr identity, and unchanged r24 archive bytes? The parent witness is acquired before the genuine source scan. After the scan, open the current parent as a directory descriptor, compare fstat(dev,ino) to the witness, and use os.open(leaf, dir_fd=verified_parent_fd); never re-resolve the mutable parent path between parent validation and destructive leaf open. Only POSIX dir_fd-capable systems earn namespace-binding credit. Preserve Windows original implementation unless an equally strong native mechanism is independently demonstrated.

**Prediction:** POSIX hostile postscan symlink-ancestor pivot must raise before constructing an output in the source root; no archive published at either path. Stable symlink-to-external-parent and regular existing-output controls must pass with byte-accurate reconstruction. Original O93 original leaf-pivot and FIFO guards must continue to pass. Windows must retain its genuine baseline controls; **no Windows ancestor-race claim**.

## Simpler and alternative routes
- Second path stat alone has another check/use race; disallowed as product proof.
- Reject all ancestor symlinks is robust but unnecessarily removes valid stable usage.
- Open the parent before the entire scan holds an FD across expensive work, complicates cleanup and peak FD use; defer parent open to publication but bind it to pre-scan dev/ino.
- Atomic rename via O75 changes inode/hardlinks/xattrs as proven by O78; not imported.
- Full openat2 or source snapshot has broader platform and semantic expense; not justified for this scoped rebind.

## Disproof and independent checks
Any genuine O96 actor swap that still plants an output under source; unexpected regular-file refusal; changed r24 bytes for stable input; lost inode, hardlink, xattr or mode; reopened output by unverified pathname; failing inherited O93 court; resource leaks or new directory permission regression that cannot be explained; or Windows regression narrows/rejects this candidate. Linux/macOS root results are independent of generic primitive-only proof. A new parent directory with the same device/inode after reuse is an unproven ABA lifetime risk, not universal atomic namespace security.

## Evidence and release boundaries
Perform cheapest historical test first (O96 hostile positive vs O99 hostile refusal plus stable control), then installed full inherited court, exact-HEAD hosted Linux/macOS/Windows, and archive-byte/CPU/RSS evidence if tests survive. The new dirfd may require read access on some POSIX hosts; explicitly measure/test directory execute-only use before any promotion. Even with success, prior partial-write failure atomicity, source-root concurrent mutation and power-loss durability remain unproven. Preserve raw negatives and never weaken O93/O96/historical gates.
