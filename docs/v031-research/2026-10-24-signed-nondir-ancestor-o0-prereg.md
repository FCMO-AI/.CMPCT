# O0 preregistration — signed r24 non-directory ancestor extraction

**Frozen before the new adverse test and before a product edit — 2026-10-24 UTC.** Research/product hardening; not shipping authority, format or version change.

## Custody, source and concurrency
Exact starting composite Reader: PR #336 `28d57e13a1b8e89a70f857f180b4403592b96e12`, stacked on #334 and #332. Independent narrow question: **lexical non-directory ancestor preflight**, not the already-owned Win32/APFS case/normalization/hardlink alias guards. Do not change owner original tests or safety policy. The canonical development remains `agent/v031-development` and the currently published release remains v0.30.0/r24. New branch is independently owned by this investigation. Communicate same-file overlap and leave merge/release to coordinated owner.

## Falsifiable mechanism
A physically impossible logical tree can be *byte-integrity-consistent*: an authenticated index may contain regular file `parent.bin` and regular file `parent.bin/child.bin`, even though no filesystem can materialize both. The current Reader `extractall` validates duplicate lexical paths and symlink parents but not a non-directory ancestor of a descendant. It writes `parent.bin` before trying its child; `os.makedirs(parent.bin)` then fails after partial publication. This is **not** a claim of remote arbitrary file overwrite; it is a fail-before-write and reconstructibility invariant.

## Baseline and independent controls
Build a real revision-24 archive using the unchanged `Builder.build` on ordinary physical files, preserve its physical blob records, mutate only logical file names into impossible ancestors, reserialize *both* indexes and recompute the exact header/footer unkeyed SHA-256 commitments. Exercise real `CMPCT(path)` and `extractall` rather than mock object rows. A valid normal nested archive from the same Builder must still extract exactly. Test non-directory one-level and multi-level ancestors; keep POSIX, Windows and macOS hosts separate, disclose environment failures.

## Prediction and alternative explanation
Prediction: baseline Reader accepts the signed index at open, reconstructs both individual files with `read()`, begins extraction, raises after writing an ancestor. Alternative: ordinary open/preflight already protects the prefix relation, or a different early rejection prevents the partial write. If so, retire as duplicate/no-gap without softening tests. Another alternative is an environmental codec/runner issue; classify separately.

## Smallest bounded repair, only if baseline fails
Before creating directories or files, build a mapping from canonical logical path to kind, and reject any entry whose proper lexical prefix exists as a **non-directory** member. Prefer a single O(total components) traversal / dictionary or set, not n^2 rescans. Preserve legitimate implicit directory prefixes and valid explicit directory owners. Reject before any member publication. Do not change the r24 wire grammar, data bytes, Builder, native ABI, symlink/alias policies or release evaluators.

## Kill/acceptance and strongest controls
Original signed negative must show actual partial output on the unmodified Reader, with SHA-matching physical data unchanged. The post-fix **same immutable adverse fixture** must reject before any file is created; valid nested archives must still be readable and extracted byte-identically. All tests on the same candidate source; original owner Windows/APFS courts remain unchanged. Any incompatible legitimate tree, semantic relaxation, unmeasured complete-system performance claim, or no hosted exact-head result keeps draft status. Hostile model: an attacker can edit and rehash an unkeyed archive index; SHA proves byte integrity, not trusted origin.

## Costs and boundaries
Expected extra O(number of normalized path components) preflight CPU and O(number of logical rows) canonical-type entries, or reuse existing canonical-key dictionary. No complete memory/RSS/ABBA measurement yet. Does not solve destination symlink/race/root rebinding (#265), external hardlink contamination, portable namespace aliases, source archive mutation, or global extraction atomicity. Structural validator parity is independent debt unless verified with its own oracle.
