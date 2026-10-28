# J24G03b — Git index trust-flag adversarial continuation (prospective)

**Status: preregistration before second implementation.** Recorded 2026-10-28 UTC, after the first J24G03 fail-closed guard and its seven tests, but *before* changing that guard for Git index flags. The previous first fix and its historical evidence stay intact.

## Independent local falsifier and new mechanism

An independently rooted temporary real Git repository, not CMPCT product code, proves `git diff --no-ext-diff --no-textconv --name-only -z HEAD --` can return **empty** after `git update-index --assume-unchanged source.py` and a material byte mutation. `git ls-tree HEAD` still recognizes the file, so the first J24G03 two-part guard would issue a successful head-bound receipt despite source drift. `git ls-files -v` records `h source.py` instead of normal `H source.py`. This is a real evidence-gap *under Git index flags*, not proof of an external exploit or that default CI ordinarily sets such flags.

## Testable hypothesis and alternative explanations

A minimal third index-attestation check using NUL-delimited `git ls-files -v -z` can fail closed when any *fingerprinted* tracked entry is marked assume-unchanged or skip-worktree, before relying on `git diff`. This preserves normal clean-repository acceptance, the original mutation/rename semantics, and generated native target exclusion.

Alternative controls:
- `git diff` alone: falsified by the observed `assume-unchanged` case.
- Recompute every blob with raw Git object hashes: more demanding than needed for the current incremental checkout model and risks cross-platform clean/smudge disagreement.
- Silently clear index flags: mutates checkout state without ownership and could cause bypass/false authority; rejected.
- Reject flagged source while preserving source hashing: selected reversible fail-closed gate.

## Acceptance, falsifiers and boundary

1. Reproduce hidden dirty worktree with real `git update-index --assume-unchanged` and prove the new guard refuses it even though `git diff` is empty.
2. Set skip-worktree on a covered source and require refusal, even if contents are currently clean; restore flags and regain clean admission.
3. Keep ordinary clean/head mismatch, added untracked, staged/unstaged/deleted, generated Cargo and root setup.py tests unchanged.
4. No Reader/Builder/Writer/validator/format/release-lock or frozen controls changed; old #639 base exact-head evidence remains separately attributable.
5. This still is **not** atomic filesystem snapshot assurance, a cryptographic comparison of every checkout byte with the Git blob under all configured filters, or hardening against an adversary controlling Git executables/configuration. Limit claim accordingly.

**Disproof:** an assume-unchanged covered file with altered contents still passes a candidate receipt, or normal clean checkout becomes unusable. No change to Discovery Engine / STATE from a single Git-worktree finding.
