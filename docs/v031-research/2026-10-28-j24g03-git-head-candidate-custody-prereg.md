# J24G03 — Git-HEAD-to-worktree source custody: prospective falsifier

**Status: prospective preregistration only, preceding implementation.** Created 2026-10-28 UTC on separate child of PR #639. DRAFT research/infrastructure; no product release, version/format mutation or evaluator waiver.

## Source-locked starting state

- Recipient owner: PR #639 at exact `00d8f27e82c9bcaf216c653b9915fd0cd7b2c67b`, Reader Git blob `fe0706ce00a425edb6572ff6cd2032f9be413468`. Owner #266 stays untouched.
- Last terminal exact-HEAD [tests #40627418805](https://github.com/FCMO-AI/.CMPCT/actions/runs/40627418805): 808 PASS, 1 SKIP, candidate-source SHA `00d8f27e`, fingerprint `5ba32a70110603811928c4ca3b94e3b861d82e8086ccf36bd801db3ecca86e45`, 2,329 covered paths and no Cargo target output.
- Last [r24-core/ZIP same-runner ABBA #40627418883](https://github.com/FCMO-AI/.CMPCT/actions/runs/40627418883): all eight candidate CMPCT sizes equal #636 base, 2×7 repetitions; not full r25 product promotion.
- Historical v0.30 lock Git blob `988a7b05ad4e0833fac0453de74133b38f890f87` is immutable. Revision 24 and v0.30.0 remain unchanged.
- Worktree source walker `tools/check_v031_candidate_fingerprint.py` currently builds rows via recursive filesystem globs, then reports `git rev-parse HEAD` as `source_sha`. It does **not** require every selected path to exist in that HEAD or fail on modified tracked source. Build outputs under `native/**/target/**` are already excluded. Cross-owner #641 added a material root `setup.py` build definition omitted from the recipient's optional source globs.

## Primary causal question and falsifiable prediction

Can two worktrees with **the same HEAD** emit *different successful* source receipts because an untracked, glob-matching Python file or dirty tracked source changes the bytes being fingerprinted? Under existing code, yes: `fingerprint()` reads filesystem files, while `main()` stamps HEAD without Git-object binding. This is a **source provenance claim defect**, not a way to forge Git SHA, an archive-integrity failure or proof of a malicious runner.

Predicted cheaper falsifier: in a clean temporary Git repo, a normal source identity succeeds; adding untracked `research/probe.py` should alter the digest while HEAD remains fixed; editing/deleting a tracked covered source should likewise alter or omit source rows. Current CLI accepts these. A repaired CLI must reject each before publishing a source-SHA-bound receipt, preserve clean success, and ignore known generated Cargo target outputs. Commit root `setup.py` in another synthetic clean HEAD: its content must now change the candidate fingerprint when modified in a separately clean commit.

## Alternatives and BONK filters

1. **Silently ignore untracked matches**: rejected; test/compiler could execute untracked source while falsely claiming clean provenance.
2. **Hash Git blobs only, do not inspect checkout**: rejected for this incremental fix; Git identity alone can miss modified *executed* worktree bytes unless an additional checkout validation exists.
3. **Report a dirty flag but still mark receipt valid**: rejected; weakens the exact-HEAD evidence gate.
4. **Reject selected untracked and any tracked HEAD difference, preserve existing filesystem byte digest and filters**: selected smallest fail-closed correction; Git tree membership + Git diff clean check, after the fingerprint traversal.
5. **Add root `setup.py` to optional source globs**: justified by shipping build semantics in #641; do not add to mandatory paths before the PR #641 composition actually imports it.
6. **Broaden all globs / rewrite historical manifests**: rejected; expands scanning cost and authority without proof.

## Required independent acceptance and attack

- Pre-fix local or hosted falsifier proves same HEAD can emit different successful receipts due to untracked/dirty selected worktree paths; preserve this negative.
- Clean Git HEAD acceptance including tracked `src/a.py`, `research/episode.py`; HEAD membership and repo cleanliness checks use NUL-separated paths, fail closed for invalid metadata.
- Dirty *tracked* modification and deletion, staged/unstaged changes, and *untracked* matching source must each fail with no valid receipt.
- Untracked files outside source patterns, excluded `native/**/target/**` generated Rust/C/header, and legitimate clean synthetic tree remain accepted, without modifying the HEAD or pretending generated files are product source.
- Root `setup.py` is covered when present; adding it within a new commit or changing its committed bytes in a later commit changes the fingerprint, preserving optionality on recipient #639.
- Existing source mutation property tests remain unchanged. Historical lock blob, Reader, Writer, Builder, frozen tests, release policy and on-disk format stay byte-identical.
- Exact-head hosted General Tests, native/fuzz and full r24 core parity must not be misrepresented if pending or skipped. A pass on tests is infrastructure/evidence credit, not product security/release permission.

## Disproof / kill condition and transfer

Disprove proposed fix if dirty or untracked matching source still yields a valid `source_sha` receipt, generated Cargo output breaks clean execution, released/historical source changes, or the check is blind to staged/deleted files. If clean native build itself modifies tracked files and fails admission, preserve the negative; prefer a precise ownership correction over bypassing checks. The process-level transferable lesson would be that a *checkout-head label must be validated against the bytes used by its evidence producer*, not that all Git HEAD labels are inherently invalid. No Discovery Engine policy changes from one incident.
