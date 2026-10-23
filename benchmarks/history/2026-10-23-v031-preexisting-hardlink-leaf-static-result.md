# v0.31 static destination hardlink leaf alias — O1 bounded result (2026-10-23)

## Question, source identity, concurrency

Can the authentic CMPCT revision-24 Reader refuse a pre-existing **physical hardlink alias** into a caller-selected destination before truncating a file *outside* that destination, without falsely rejecting storage types whose extractors already atomically replace leaves?

This is the narrow complement to draft owner [PR #269](https://github.com/FCMO-AI/.CMPCT/pull/269), exact source head `0273c628872dce672936aa0ddd555ed10a900bf7`, original Reader blob `43fd462535495b0c3c80c95751a20d9c261b94ed`. One isolated stacked draft [PR #294](https://github.com/FCMO-AI/.CMPCT/pull/294), no mutation to #269 or other owner branches. Related broader destination safety [Issue #265](https://github.com/FCMO-AI/.CMPCT/issues/265). Prospective prediction and alternatives were committed as `ded8f5a8efde49bb4e9041938c4674035cca29fe`, before tests and Reader changes.

## Exact prior failure (unmodified source)

Original Reader, installed authentic package with native Rust component:
- [Actions run 40030991505](https://github.com/FCMO-AI/.CMPCT/actions/runs/40030991505) on candidate-history SHA `d125879c8d1a5b2b217927720ddde95e3cc0334d` with original Reader Git blob `43fd462...`, **FAILURE as preregistered: 2 failed / 3 passed**.
- `S_BLOB` and genuine `S_SPARSE` preexisting destination leaves both failed to raise. They were physical hardlinks to outside sentinels; the existing direct-truncate path can corrupt the underlying outside inode.
- Prior atomic `S_CDC` replacement, ordinary single-link reuse, explicit `safe_symlinks=False` opt-out: three controls passed.
- Negative evidence is retained and not reinterpreted as infrastructure failure.

## Implementation and source-exact positive

Candidate Reader Git blob `66b1f84d849cc2a8470467e75e478f6dc5927c75`, a localized extension (+13/-3 source lines) of parent existing `lstat` preflight. When `safe_symlinks=True`, reject a pre-existing **regular** destination leaf with `st_nlink>1` before any archive member write **only for K_FILE paths whose current materialization directly truncates that inode**. Preserve atomic-replacement `S_CHUNKS`/`S_CDC`; keep original single-link, symlink replacement and opt-out semantics.

- Exact-head focused [run 40031894923](https://github.com/FCMO-AI/.CMPCT/actions/runs/40031894923) at `a3ecd8e8ac78c782982965ddba7fad004e83e2c2` succeeded: **8/8 authentic Builder/Reader tests PASS** in 0.14s, including genuine `S_BLOB`, sparse, Builder cohort `S_PACK` (8 ZIP archives), `S_VZIP` (stored nested ZIP), atomic CDC, ordinary overwrite, unsafe opt-out and a deliberately preserved benign alias negative. On all protected cases the outsider's file content/SHA, size and inode remain unchanged and an earlier archive member is not materialized.
- Source-bound workflow asserts Reader blob `66b1f84...`; performs editable genuine native install rather than a mock Reader.
- Independent POSIX microcourt in the **same run**, **5/5 structural observations**: parent-symlink rejection via no-follow directory fd; no-follow hardlink truncation alters outside inode; new-inode publication preserves outside; a one-link preflight can be bypassed by a later hardlink substitution; a moved-ancestor directory FD can publish beneath the moved inode outside the former root pathname.
- Current exact head will advance only for this decision-complete result and CI workflow path; re-run must be checked on final source+docs head. All prior runs remain immutable provenance.

## Strong negatives and surviving boundaries

1. **Compatibility false positive:** if both hardlink names are benign and inside the caller-selected destination, `st_nlink>1` still rejects. This is deliberate fail-closed policy, not a solution to preserving all destination reuse.
2. **TOCTOU falsified:** POSIX microcourt observed a leaf at `st_nlink==1`, then atomically swapped it to a hardlink of an outside file before an `O_NOFOLLOW|O_TRUNC` write; outside inode changed. Thus the static guard is **not race safe**. No malicious thread is needed to reproduce the legal interleaving.
3. **Root-path identity:** a held dirfd names its *inode* after that directory is renamed. A Linux x86_64 isolated `openat2` microcontrol additionally confirmed that both `RESOLVE_BENEATH` and `RESOLVE_IN_ROOT` can create a file through such a moved dirfd: they protect resolution under the FD, **not confinement under its former absolute pathname**. This is **local research**, linked as an independent result on Issue #265, not CMPCT product CI.
4. **Cross-owner future composition:** PR #255/#270 sparse path publishes a new inode atomically; when integrated, the direct-truncate predicate must be recomputed from actual selected extractor rather than a storage-kind guess. Owners informed via PR #270.
5. **No promo economics:** only the focused product tests are positive. No same-runner complete r24/ZIP performance proof, memory or portability runs; code-level reasoning predicts no extra `lstat` syscall but full CPU/wall/RSS/temp I/O is UNMEASURED. Released v0.30.0 and revision 24 are unchanged.

## Decision and future executable action

**CONFIRMED STATIC HARDLINK ALIAS DEFECT → NARROW INTERIM FIX VALIDATED IN FOCUSED PRODUCT CI → NO RACE-SAFE OR FULL-COMPATIBILITY PROMOTION.** Preserve this bridge as draft, never remove negative tests or waive inherited Public Proof, source provenance and timing gates. Cheapest next materially different frame: compare **conditional new-inode staging on `st_nlink>1`** against static refusal for legitimate in-root aliases and external victims, charging extra temp bytes/syscalls/mode/xattr/inode semantics. Independent cross-platform and concurrent security architecture remains a larger separate owner task.

Counterfactual prospective lesson: inspect both *how a leaf is published* (in-place truncate vs new inode) and *whether an existing physical inode has other names*, before attempting symlink-only or purely lexical extraction safety. No general Discovery Engine policy change earned from this one case.
