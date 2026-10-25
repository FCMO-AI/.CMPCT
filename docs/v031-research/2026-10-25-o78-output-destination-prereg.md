# O78 — Builder destination identity and metadata publication court (prospective installed-product test)

Date: 2026-10-25 UTC. Research-only stacked on O75 [#432](https://github.com/FCMO-AI/.CMPCT/pull/432) exact parent `878268e48be8a33ff6d5305ad25f22659cc6918d`, Builder blob `d92c78119e9613b2c3ae1886a8fba841dc313fca`. Release remains v0.30.0 / r24. Do not edit O75 owner files.

## Existing pilot evidence / transparency

Before this preregistration, **one lower-rung local Linux Python primitive probe was already observed** (not CMPCT execution). The historical `Path.write_bytes()` and the O75 `O_EXCL`/write/`os.replace()` primitive were tested in independent temporary trees: regular destination inode changes under replacement, preexisting hardlink alias retains old bytes, symlink referent remains old while path changes from symlink to regular, `user.*` xattr was dropped, and on a non-root UID a read-only output was refused by historical `write_bytes` but replaced by staging. This is NOT preregistered evidence and receives no product or portability credit. The next exact installed-Builder test is prospectively frozen here.

## Primary question

Does O75 materially change **existing output artifact namespace/metadata semantics**, even while preserving r24 archive bytes and process-level failure atomicity, relative to the true historical Builder?

## Mechanism / strong control / alternative

A new staged inode swapped by rename cannot modify aliases to the old inode; it lacks previously attached xattrs and permission-to-write checks on the old inode unless explicitly preserved or checked. Strong control is authentic historical Builder on the same constructed source tree and destination state. Alternative explanation: product's higher-level Builder may apply checks or metadata operations that make the raw primitive divergence irrelevant. A true Builder A/B decides this.

## Predictions / kill and narrow

On non-root Linux with ordinary POSIX local filesystem: (1) original Builder updates a hardlinked alias; O75 leaves it pointing to the previous archive; (2) original Builder preserves a preexisting destination user xattr, O75 drops it; (3) original Builder follows an output symlink while O75 replaces that link itself; (4) original Builder raises PermissionError on a read-only existing output in a writable parent while O75 succeeds, preserving 0444 mode on the new inode. The successful output archive bytes for both arms should be identical on the same source and both should verify with the authentic Reader. Failing to observe one behavior narrows that case; no evaluator or baseline is weakened. Absence of xattr support is an explicit SKIP, not PASS.

## Scope and decision

Execute real original Builder `4545d7d5...:src/cmpct/builder.py` under Git blob custody alongside installed O75 Builder; use isolated physically created file trees, distinct candidate paths, and verify outputs/aliases with SHA and inode/xattr facts. Run on an actual Linux CI host, preserve raw JSON/JUnit and source SHA. This is a **semantic adversary, not a release benchmark**. If observed, O75 must explicitly choose a policy for old-output symlinks, hardlinks, security/ACL/xattrs and write permission before promotion, or demonstrate an alternative publication boundary. Do not mutate product, frozen evaluators, thresholds, version, format or published locks. Ownership of O75 source remains PR #432.

## Cost / unknowns

No cold I/O, CPU, peak RSS, portability, power-failure durability, live concurrent writer, or all-filesystem equivalence is measured. Changed output inode semantics might be intentional and acceptable for some callers; the test informs an explicit product contract rather than prescribing a hidden waiver.
