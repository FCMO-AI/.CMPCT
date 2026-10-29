# J24I06 — Private compaction representation and metadata fidelity (preregistration)

Date: 2026-10-29 UTC. **Status: prediction, not observation.** Parent evidence: PR #720 at `b316440eced8f3023e4a26f7b05c02dcd26ad86a`, source `main@80c358f8824ec1b20d349c92ed94c898090969b0`. Owner: Phased3, stacked exclusively on the existing J24I05 compaction research branch. No change to ordinary Reader/extractor policy, format revision, or release gate.

## Primary product question

Can `compact_archive` preserve the exact logical information of valid revision-24 archives containing absolute or parent-relative symlink target **bytes** without permitting the archived symlink to become a filesystem traversal primitive, and without changing recorded UID/GID, xattrs, type/mode/mtime, hardlink classes or logical payload hashes?

**Baseline/negative:** installed source #720 (unchanged published Builder/Reader/transactions) rejects absolute and parent-relative symlinks at ordinary `extractall`; even successful compactions recapture runner UID/GID instead of source index metadata (0/0 source to 1001/1001 staged output). Compaction currently writes its destination directly.

## Falsifiable mechanism

Option A (preferred bounded product experiment): materialize into an exclusive private scratch directory *only after rejecting all canonical path collisions, any symlink-as-ancestor and any hardlink-to-symlink/nonregular owner*. Permit arbitrary **literal** symlink target text in this private scratch path, never in user-directed `extractall`, and only when no archive member can appear below a symlink. Rebuild with source-index per-path metadata injected after Builder scan, not from host `chown`/xattr outcomes. Validate the resulting archive's complete logical rows, metadata and member hashes **before** atomically replacing the destination. Existing extraction safety defaults and compatibility remain unchanged. If the private boundary cannot be demonstrated safe, retain the baseline and do not ship the approach.

Option B: typed inert manifest/physical-owner transfer without staging symlink filesystem entries (stronger isolation but larger rewrite). Option C: restrict compaction API explicitly (simpler but leaves the proven general-purpose capability gap). Option D: bare `safe_symlinks=False` with no lexical/ownership preflight (REJECTED as unsafe). Reuse current Reader and Builder, do not create a second parser.

## Tests and prospective decision

1. Same exact genuine Builder-produced revision-24 archive: normal file; safe relative symlink; absolute symlink; parent-relative symlink. All should compact, preserve symlink target bytes and full parsed metadata including source `fsmeta.owner` 0/0. Ordinary `extractall` **must still reject** restricted symlink targets. External sentinel SHA must never change.
2. Hardlink to regular owner and sparse-member control: validate logical bytes/hash, kind, hardlink target identity, metadata; fail closed if any path/kind cannot be represented. Source and destination must be equal by a full logical manifest (not necessarily identical archive bytes).
3. Hostile link-parent and hardlink-to-symlink preflight negatives; verify no temporary external writes and no destination mutation. Validate destination sentinel survives a corrupt-source failure.
4. Run focused installed-source court on Ubuntu first, then three OS where supported, plus general tests. Record source and artifact SHA, raw receipts, exact host, CI, and full costs when available. Any unsupported symlink platform is evidence of portability debt, not success.
5. Strict kill/narrow condition: any external sentinel mutation, symlink-parent traversal, metadata drift, lost hardlink topology, unverified output, overwrite before validation, or changed normal `extractall` safety. A green tiny test does not earn release credit; full platform/hostile/performance gate still required.

## Concurrency and authority

PR #720 owns the initial falsifier; this is a stacked, separable productization fork and must not rewrite its preregistration/results. Relevant adjacent owners: extraction namespace #265/#619, compaction destination identity branch, hardlink/sparse work and atomic publication #492. Read current PR heads again before writes; the current materialization protocol is not a generic weakening of symlink policy. `docs/discovery/STATE.json` remains untouched (PR #574 owner).

## Outcome rubric

**PASS (bounded experimental product candidate):** expected genuine cases, exact indexed metadata and no effect on sentinel, destination stays unchanged on failure, installed test evidence. **FAIL:** one hard invariant violation. **AMBIGUOUS:** infrastructure/OS limitation or absent exact-head evidence. No merge or release without owner and release evidence. Product performance, peak RSS, temporary I/O and update-recovery cost stay unmeasured until a dedicated same-source trial.
