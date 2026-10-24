# O11 — prospective tracked-source custody of v0.31 fingerprint (preregistration)

**Date:** 2026-10-24 UTC. **Status:** PREREGISTERED BEFORE CODE OR O11 HOSTED RESULTS.
**Parent:** PR #352, exact `93e9a00fd352ac567e9b069654aa145148370d42`. **Issue:** #354.
**Release floor:** v0.30.0, r24, historical custody immutable. v0.31 draft.

## Baseline fact and hypothesis

At the same PR #352 HEAD, GitHub Actions general tests #40095303366 hashed 2,375 candidates and emitted SHA-256 `1774daee55a629d88959ccb268fa00f7566ba24ed9569c0e3982d943a88467e8`, whereas installed-package run #40095303436 emitted `185cc76efa901d3e751e54aff8a2207fb68026bef2ef91a671a33e7e4b8ab541`. Issue #354 independently found generated, **untracked** `native/cmpct-core/target/**` Rust files in the former roster. Current `glob.glob` scans mutable worktree output; the manifest source glob family includes `native/**/*.rs|c|h`. These identical-SHA fingerprints cannot both be a single canonical source identity.

**Hypothesis:** admitting **only Git-index-tracked paths**, while hashing their *actual checked-out bytes*, makes the fingerprint stable under generated/untracked build files without concealing source mutations, removals, renames or unsafe symlinks.

## Alternatives and falsification

(A) Explicit `native/**/target` exclusions: simpler one-off, but future generators outside that path could contaminate the manifest. (B) Hash `git show HEAD:path` for every member: wrong, because it hides uncommitted tracked-byte mutations and permits worktree-to-SHA mismatch. (C) Read Git's canonical tracked membership with `git ls-files -z --cached`, intersect existing glob semantics and continue checking actual file bytes, symlink policy and manifest required paths: selected as smallest general invariant. A missing Git repo must fail closed rather than silently revert to untracked glob scanning.

A valid local or hosted result requires:
1. Same exact commit on clean checkout and on post-native-build dirty worktree: **identical** source roster and SHA-256, despite new untracked `target/**` files that match broad globs. Cross-workflow parity on the same SHA must be checked; a self-comparison on one runner alone is weaker.
2. Tracked content mutation: fingerprint must change; staged tracked-file addition under an eligible glob must enter fingerprint; tracked-file deletion and tracked-file rename must change identity (no silent disappearance counted as source equality).
3. Untracked addition, including symlinks, may not pollute the identity; a tracked symlink or a tracked path replaced by symlink **must fail closed**. Missing required tracked paths must fail closed.
4. Existing historical lock blob test, `tests/test_v031_candidate_fingerprint.py` controls, installed-package 3-OS/source-custody evidence and general tests must remain honest. Preserve exact-head linkage; no production, benchmark, format or release policy edit.

**Kill/narrow:** If Git-index roster changes between exact-head clean and built runs in normal CI (e.g. a build stages files), fail and separate Git-index mutation from untracked noise. If required production source is genuinely untracked, record it and explicitly track it in version control instead of weakening candidate manifest. If clean/built hashes still disagree, inspect actual tracked path/byte differences before asserting a cure. A full-release claim remains unavailable until source-custody + all product/benchmark gates independently pass.

## Scope and scientific credit

This is evidence/infrastructure **enabling exact product promotion**, not a compression gain, r24 change or adopted v0.31 release. No old v0.30 receipts are regenerated. The previous contradictory receipts and negative data remain valid historical evidence. O11 owns only the tracked-roster fingerprint, its tests/court and evidence documentation; neighboring O9 Reader, O10R Reader limits and native branches remain owned elsewhere. Shared Discovery STATE is stale and is not a lock; no edit without reconciled decision-changing truth.
