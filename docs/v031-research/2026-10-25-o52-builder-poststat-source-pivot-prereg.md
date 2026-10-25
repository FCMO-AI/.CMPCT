# O52 preregistration — Builder post-stat source substitution (2026-10-25 UTC)

## Authority / frozen source
Released v0.30.0 / physical r24 unchanged. Independent research-only child of the O50 composition PR #405 **exact head** `17c96603e33b02b3f2f9e0079eec2b128f293be8`, Builder blob `21a9ec696df13961c25301654feb607a7e161a4c`. O47/#401 and O48/#402 own the Builder's Win32 physical hardlink and static unsupported-entry admission changes; O50/#405 owns their product composition. This experiment edits none of those files or owners, `docs/discovery/STATE.json`, frozen benchmarks, gates, format or release.

## Question / baseline
The actual O50 Builder calls `DirEntry.stat(follow_symlinks=False)`, then checks kind and collects metadata, but later reads the same *pathname* with `open(e.path, 'rb')`. Does O48's genuine static FIFO refusal remain sufficient if a local actor changes the path *after* that stat but before its open? Can a regular entry change into a symlink to a file outside the selected source root and become archived as regular data? This is a source-file descriptor/custody question, not a codec or decompression question.

## Prospective predictions and controls
Execute the exact unmodified O50 Builder in clean-installed Python on hosted POSIX runners; require exact installed `cmpct.builder` blob and r24 Reader strong verification. Control: ordinary stable regular file creates a valid archive, correct regular entry and byte-exact contents; O50 ordinary static unsupported FIFO is rejected before output. Intervention A: deterministic test-controlled interleaving when the original `open()` is about to read an already-`lstat`ed regular input changes that path into a real symlink pointing to a distinct file outside the tree. Prediction: historical/O50 source stores outside file bytes under an ordinary K_FILE member instead of aborting. Intervention B: same boundary changes the path into a real no-writer FIFO. Prediction: genuine Builder creation process blocks until killed by a bounded independent-parent watchdog. Preserve sentinel output file and original source files as control where possible; no claims about remote exploitation or atomic filesystem snapshots.

## Stronger controls and alternatives
The interleaving must be after *real* O50 kind admission and immediately before *real* builtin file open; do not replace any CMPCT encoder or mutate tests/evaluators. Disclose that a Python monkeypatch coordinates a real pathname replacement rather than claiming an uncontrolled scheduler race. Ensure a stable symlink known from the start is represented as K_SYMLINK (it must not leak as a regular member); static FIFO is rejected by O50 before opening. A second OS runner (macOS) is ideal; Windows classifies POSIX-only tests as explicit skips. The outer process, not a hung in-process worker, owns timeout termination. If O50 already binds the opened descriptor or refuses this substitution, retire the hypothesis; if changing a path does not trigger the claimed gap, preserve the negative.

## Decision / attribution
Positive means O47/O48/O50 correct *static* capture but do not close a post-stat source lifetime trust boundary. It does not invalidate O50's static gains. A product candidate would need descriptor-anchored `O_NOFOLLOW`/same-handle `fstat` and a declared symlink/freshness policy on POSIX, with independent copy/CDC/sparse/virtual-ZIP and native/Windows parity; a mere second pathname `stat` is still raceable. No proposal gets product, cross-host, security-release or benchmark credit from a research-only test. Track child CI run ID, exact source SHA, artifacts and results in a separate result note, and inform O50 owner without editing its branch.

## disproof:
- Clean-installed exact O50 Builder refuses both post-stat pivots before reading; or control file fails; or a test does not reach the actual intended read path; or no substantive tests execute.
- Static unsupported FIFO or pre-existing symlink control weakens; or actual archive SHA/reconstruction cannot be verified for intervention A.

## quality-ratchet:
Preserve all inherited exactness/format/release safety. Do not modify baseline source, comparison semantics, tests, source kind policy, release thresholds, artifact trust, or PR owners. New code is isolated research/evidence, with no release authority.
