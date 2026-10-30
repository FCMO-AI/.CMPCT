# J24I58 — Compose existing #643 Git source custody into the J24I57 Windows hardlink / signed-journal stack

**FROZEN PRE-IMPLEMENTATION PREREGISTRATION.** 2026-10-30 UTC. No new product version, archive format, release gate, benchmark criterion, native ABI, Reader, Writer, Builder or historical release-lock mutation.

## Baseline / decision
J24I57 [#831](https://github.com/FCMO-AI/.CMPCT/pull/831) source head `a7a1c1b929e50e22fd7c8bcfebe14df3ed1b3171` earned **887 passed / 2 skipped / 0 failed** full General Tests [#41057565640](https://github.com/FCMO-AI/.CMPCT/actions/runs/41057565640), following #828's five historic failed assertions. Its #266 prospective fingerprint instrument observed 2366 filesystem paths, but prior independent #639 and #643 proved false-source-custody acceptance:
- Generated untracked native Cargo target build outputs matched `native/**/*.rs/.c/.h`, causing environment-dependent identity not bound by Git HEAD.
- Tracked modifications, untracked matching research source, and index assume-unchanged/skip-worktree flags can conceal discrepancies between asserted HEAD and hashed checkout.
- Windows CRLF checkout may legitimately differ from Linux/macOS in raw worktree SHA under the same clean HEAD; no raw cross-host SHA equality should be asserted.

Existing owner [#643](https://github.com/FCMO-AI/.CMPCT/pull/643) exact `50c1fd6b6c02c8f2a1ce8488dceb804645bb1bf7` contains already-proven additive fail-closed Git HEAD/worktree provenance check, Cargo target exclusion and source roster expansion, plus a three-platform targeted tribunal with hostile tests. **This child is distinct integration onto the newer #831 physical Windows hardlink and signed journal stack, not reimplementation or takeover of #639/#643.**

## Hypothesis
Transplant only exact #643 source tool, JSON source manifest, 10-case regression tests and source-custody workflow into a branch based on #831. H1 predicts Linux/macOS/Windows specialized hosted source-to-HEAD court passes on the new exact head, fails closed on untracked matched/research source and hidden Git index flags, and no longer hashes Cargo generated outputs. The current full General Tests remains green (887+ newly added case count) while product sources and historical release-lock remain bit-identical.

## Strong simpler controls / alternatives
Simply ignore generated target files without Git custody leaves an untracked matching research source loophole; copying only #639 isn't enough. Using Git blob hashes alone without checking checkout execution lets dirty sources evade detection. Inventing a new Git provenance method duplicates owner #643. Forcing identical raw worktree SHA on Windows breaks legitimate CRLF checkout. A complete worktree snapshot against concurrent active attacker processes is a stronger problem **not** solved here.

## Disproof / kill
Any missed dirty/index/untracked source, falsely rejected clean CI checkout, spurious Windows CRLF refusal, changed frozen v0.30 lock, product source drift, rewritten donor test assertions, leaked generated Cargo paths, or full General Tests regression rejects the composition. Targeted workflow dispatch without its real jobs is not evidence. No archive-performance claim is credited by this evidence-only PR.

## Whole-system charges
Full source glob/hashing + Git tree/diff/index scan adds bounded CI wall/CPU and Git process startup; no archive bytes, creation/extract CPU, read amplification, RSS or r24 wire changes. Cargo target should be excluded, not counted as canonical. Source SHA and checksum of scanned worktree bytes remain distinct proof layers; neither proves a full reproducible cross-OS artifact.

## Plan
1. Freeze this preregistration commit alone before donor file writes.
2. Transplant only four existing files from exact #643, verifying identical Git blobs. Preserve #831 previous historical and source files.
3. Targeted three-platform Git clean-worktree workflow and exact-head General Tests. Record concrete source/runs, any negatives, and independent prior controls.
4. Keep unmerged draft; owner #639/#643 and product line decide subsequent integration. Do not change `docs/discovery/STATE.json` owned by #574.
