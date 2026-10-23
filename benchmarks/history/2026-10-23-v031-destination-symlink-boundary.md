# v0.31 — pre-existing destination symlink boundary (2026-10-23)

**Status:** preregistered, source-exact scientific correctness/security-boundary court. This document is NOT a claim of a remotely exploitable vulnerability and does not imply a product fix.

## Source and ownership
- Target: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, shipping v0.30.0 / r24.
- Reader blob: `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Builder blob: `663ef0922992b1fbb8f19e6eea88d55c10a56044`.
- Existing Reader/extractor PRs #255, #256, #262 own sparse verification, temporary basename budgets and hardlink order respectively. This study changes none of those code paths.
- Source history/PR search found no existing owner for a *pre-existing destination directory/leaf symlink* pivot; consult new work before implementing.

## Question / prediction / kill condition
Given a valid archive containing only ordinary relative files, and a destination tree prepopulated by a symlink under its root, can `CMPCT.extractall(dest,safe_symlinks=True)` replace a sibling file **outside the requested destination root**?

Hypothesis: yes, under two independent mechanisms:
1. **Ancestor pivot:** `dest/subdir` is an existing symlink to `outside/`. A regular archived `subdir/file.bin` is written using a pathname after `os.path.isdir` follows the symlink, leading outside. Directory `os.makedirs(exist_ok=True)` may accept the symlink.
2. **Leaf pivot:** `dest/file.bin` is an existing symlink to `outside/victim.bin`. The ordinary BLOB `os.open(O_TRUNC|O_CREAT)` follows it and changes the outside victim.

Controls: verify/read authentic CMPCT archive before extraction, check no `..`/absolute names, verify both destination and outside sentinels before the call, run clean-destination extraction to demonstrate ordinary correct behavior. Synthetic paths stay entirely within a temporary test root; no system or unrelated user files are touched.

**Prospective result:** both outside victim files change to source payload while `safe_symlinks=True`; clean destination remains correct. An exception before an outside modification, absence of source identity, unexpected filesystem mode, or a source/head mismatch falsifies or narrows the hypothesis rather than counting as success. Independently track whether source is `S_BLOB`; do not assume the same mechanism applies to CDC, sparse or pre-existing host races.

## Alternatives / implications if observed
- A lexical archive-only parent-symlink check is insufficient against preexisting destination state. Merely checking `resolve()`, `lstat()` or `is_symlink()` in an earlier preflight could catch static pivots but still permits concurrent TOCTOU replacement.
- A trustworthy hardened implementation probably requires directory-handle-relative traversal (`openat`/`dir_fd`, `O_DIRECTORY|O_NOFOLLOW` or stronger platform equivalents) plus no-follow leaf semantics and careful atomic publication for every storage kind. These capabilities and cross-platform equivalents must be measured; this experiment does not implement them.
- Alternative contract: refuse extraction into nonempty trees or document the caller-supplied destination as a trusted mutable boundary, though this reduces usability and must not be misrepresented as a security repair.
- A truly concurrent attacker may still race any path-by-name implementation; no race-safety claim follows from static tests.

## Evidence ladder
1. Static mechanism in canonical `src/cmpct/reader.py`: validation only detects symlinks listed **in archive**; `os.makedirs`, `os.path.isdir`, ordinary `os.open` resolve pre-existing filesystem links.
2. Exact-source hosted Builder+Reader corpus, read/verify/relative-path controls; save JSON results even on predicted failure.
3. Only after source-exact result: separately scoped, owner-coordinated product fix and adversarial evaluation of leaf/parent, chunked/sparse, hardlinks, existing destination contents, cross-platform behavior, races and release parity.

## Nonclaims
No compression gain, no product fix, no portable guarantee, no proof of external exploitation, no official release regression result. The current public contract for caller-controlled preexisting destination trees needs explicit review. Do not weaken existing validators/release gates or silently reinterpret `safe_symlinks`.
