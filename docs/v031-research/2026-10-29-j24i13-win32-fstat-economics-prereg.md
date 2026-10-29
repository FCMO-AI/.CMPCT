# J24I13 — Win32 Builder physical-identity syscall economics (preregistered)

2026-10-29 UTC. Status: **PREDICTION BEFORE INSTRUMENT / NO PRODUCT CREDIT**.

## Authority and concurrency
Canonical published baseline remains main v0.30.0/revision-24; local integration parent is PR #730 at `f190a566950970895cec54e215538691aa7595ca`. Existing real source hardlink correctness owner is PR #401 (O47). PR #730 owns its integration with private compaction; PR #726 owns an independent stage-name safety veto, and PR #731 studies sparse verification memory. This research-only child must not overwrite those implementations or relax release law.

## Problem and falsifiable question
O47 restores physical Win32 hardlink identity with an extra nonfollowing `os.stat(path)` on each regular file. J24I11's source-exact 256-independent-file diagnostic measured 36.523 ms historical vs 44.959 ms O47 (**+23.10%**) on Windows 2022. Does the OS call itself dominate this cost, and can an `os.fstat` on a file descriptor already required to read data offer meaningful headroom?

## Mechanism, controls and predicted observations
On identical deterministic physical trees compare A = `os.stat(path, follow_symlinks=False)` followed by the normal `open/read` versus B = `open`, `os.fstat(fd)`, `read` for each regular file. B reuses the already-open read descriptor; both retain actual `(st_dev, st_ino, st_nlink)`, mode, size and SHA. Use fresh independent trees with 256 unique regular files and a separate 3-path graph (owner + real hardlink + content-identical independent copy). At least 4 ABBA rounds, raw wall/CPU per iteration, exact bytes/file reads, platform/build metadata, independent-corpus SHA, no claims from only one median. For a direct claim about Builder, perform a later real source-locked Builder A/B: this probe alone does **not** establish product improvement.

Hypothesis: Windows may save the per-file extra source pathname query by using `fstat` on the existing reader, with unchanged physical hardlink classification. A minimum useful signal is **>=10%** reduction in elapsed time on the 256-unique-file probe in at least 3 of 4 paired ABBA rounds, with matching physical ownership and data digests. If lower, noisy or hostile behavior differs, retire/narrow the route rather than build a new implementation.

Strongest simpler control: O47's current `os.stat` is already correct. Alternative explanation: Windows `fstat` itself requires equal kernel work and the 23% Builder delta is dominated by other work/host noise. A/A same-path duplication and Linux control help discriminate timer/scheduling artifacts. Separate legacy `DirEntry.stat` timing is NOT correctness-equivalent on Windows and cannot replace either control.

## Safety disqualifier and exactness
`os.fstat(fd)` binds identity to the opened data source but open(path) may follow a symlink substituted after earlier `DirEntry.stat(follow_symlinks=False)`, whereas O47's immediate `os.stat(..., follow_symlinks=False)` still detects one class of substitution. This is **not** a semantics-preserving drop-in replacement without a non-following source-open/inode-authorization design. Explicitly test/report that difference; a faster fstat micro probe alone cannot earn product implementation or release permission. Do not weaken source-race protection to gain time.

A compelling result only authorizes a new bounded descriptor-owned source identity design with type/no-follow/census checks and actual archive/source/reader semantics. The alternative of SHA-based post-read link grouping is deferred; it risks double work and changing virtual ZIP ownership. If fstat does not win cleanly, return to #726 safety/other frontier.

## Evidence and decision
Evidence ladder: source/API derivation -> installed Win32/Linux repeated micro A/B with retained raw receipts -> (only if prospective positive) source-exact Builder integration, installed 3-host topology/negative cases, full cost and security gates. A positive micro court is **research evidence**, never product improvement. A negative retires the narrow fstat-cost shortcut, not O47 hardlink correctness.

No code, format, release, policy, discovery STATE, benchmark evaluator or threshold modifications are permitted in this preregistration commit. Keep direct scientific results in this branch/PR and communicate any decision to O47/#730 without changing their work.
