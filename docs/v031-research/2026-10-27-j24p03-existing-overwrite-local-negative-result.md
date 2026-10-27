# J24P03/J24P03b — authenticated anonymous inode does not secure a *named* overwrite

**Research result, 2026-10-27 (UTC).** Scope: Linux kernel primitive only, **not the CMPCT Reader, production deployment, or release evidence**. This is a decision on one tempting architecture for fixing Issue #528, not a theorem that all existing-target overwrite solutions are impossible.

## Exact source and prospective hypotheses

- Base J24F12 [PR #559](https://github.com/FCMO-AI/.CMPCT/pull/559): `dd723d128b5a020f154b4c9f7d37c6eedc929f24`, Reader Git blob `83c6600fa6cc951c1e6a136d239a39bb2c5d836b`; unchanged by this research.
- Preregistration **before implementation**: `9a73bbdeec998b117c62d02cbf35a141de4e2798`, `docs/v031-research/2026-10-27-j24p03-existing-leaf-rename-boundary-prereg.md`.
- Additional independent held-out parent-mode prereg **before extending instrument**: `5305a058dce7d874868ab63a8e61460d49dee669`, `docs/v031-research/2026-10-27-j24p03b-write-search-only-adversarial-prereg.md`.
- Instrument (Git blob `5c79325cdac7643854155eebdb5e03e730f5f0b0`): `research/j24p03_fd_replace_oracle.py`.
- Independent raw-receipt auditor (Git blob `d4d4b4cb95af8b504a679aa6723ad7a5d17871bb`): `research/j24p03_evidence_audit.py`.
- Dedicated source-ancestry gated GitHub Actions: `.github/workflows/v031-j24p03-existing-overwrite-boundary.yml`. Latest exact-head hosted scientific result is **PENDING** as this local-result record is written, not assumed green.

## Causal mechanism, authentic kernel operations

The parent creates an unnamed `O_TMPFILE` and writes known GOOD bytes; the fd stays open. It links that *same physical inode* into its output directory under temporary name `stage` with actual libc `linkat(AT_EMPTY_PATH)`. The prior `target` contains OLD bytes. An independent subprocess with the **same ordinary UID** renames `stage` to `quarantine` and writes a new regular inode containing BAD bytes at the old stage name. The original authenticated fd and quarantined inode still hold GOOD. The parent then executes the **real**, unmodified `os.replace(stage,target)` or `renameat2(RENAME_EXCHANGE)`. Each syscall looks up the then-current *name*, not the original fd. The destination therefore receives the unverified BAD inode, despite the authenticated fd remaining unchanged. The actor is synchronized to remove nondeterministic race probabilities; no fake rename function is used.

This directly probes whether a two-syscall substitution with a visible intermediate source name is a credible existing-target publication architecture. It does **not** claim to demonstrate the actual Reader code has performed this proposed implementation; J24F02 #527 independently established its historical named-stage vulnerability.

## Linux unprivileged local observations (non-hosted evidence)

Environment: ordinary uid 65534; independent child process also uid 65534; disposable Linux directory/filesystem permitting `O_TMPFILE`. Original deterministic payload digest values:

| Content | SHA-256 |
|---|---|
| GOOD, original authenticated fd | `046a596be6d6ec5b7ca86f5cd4bf7878549e2decd3dde3c56747ea21908ad3c5` |
| BAD, separate attacker inode | `82996bca8cd70f15318444bb66e6e897fd025d1283a643b2c2ba4dd17454af23` |
| OLD, previously existing destination | `08b4ab105dabfdf3d1b0256e500f91a7d5e651b7891490feb38d03569c611d3d` |

| Parent permissions | Publication | No attacker | Child substitutes visible stage |
|---|---|---|---|
| 0700 read/write/search | `os.replace` | GOOD fd inode published | **BAD foreign inode published** |
| 0700 read/write/search | `renameat2(RENAME_EXCHANGE)` | GOOD fd inode published | **BAD foreign inode published** |
| 0300 **write/search-only** | `os.replace` | GOOD fd inode published | **BAD foreign inode published** |
| 0300 **write/search-only** | `renameat2(RENAME_EXCHANGE)` | GOOD fd inode published | **BAD foreign inode published** |

**Eight direct replacement trials:** 4 unchallenged exact-fd SHA/inode controls, **4 hostile foreign-inode publications**, each with child process UID, dev/ino identities, preserved GOOD quarantine and post-publication SHA verified.

**Three additional direct controls:** `linkat(fd,...,absent)` published the authenticated inode; `linkat(fd,...,occupied)` returned EEXIST without altering OLD; directly renaming `/proc/self/fd/N` over `target` returned EXDEV on this filesystem without modifying OLD. In mode-0300 directories the original O_RDONLY directory open gave EACCES as predicted, while O_PATH parent capability permitted the operations. *Lack of directory-read permission does not prohibit an actor who already knows a stage filename from rebinding it.*

Raw locally recorded J24P03b JSON digest: `ab34e941cd50484010c64b6afc273eb1d0c6d0061c9b8af202a21c8a88064d16`. Regenerate with ordinary nonroot privileges, e.g. `python research/j24p03_fd_replace_oracle.py --output result.json`. Check with `python research/j24p03_evidence_audit.py result.json`: **11-case structural receipt consistency PASS**. The independent auditor additionally refused **6/6 deliberately mutated receipts**, including incorrect BAD SHA, falsified child UID, relabeled source inode, duplicated permission-case identity, duplicate JSON root member and JSON nonfinite number. This is receipt consistency, **not an independent kernel replay or 6 new product security tests**.

## Strong negative and disposition

**RETIRE:** `O_TMPFILE` → link authenticated inode to an attacker-mutable *visible stage name* → `os.replace` or `RENAME_EXCHANGE` into an existing destination **as a claimed physical-inode authenticity fix under same-UID parent-directory writer**. Swapping only the final rename syscall is insufficient. Even keeping the original authenticated file descriptor live does not bind the rename operand to that inode.

**PRESERVE:** J24F11/#557 and J24F12/#559 fresh-leaf Linux no-clobber linkat source ownership; the attacker cannot substitute a source stage pathname when no intermediate named stage exists and direct fd-to-final link either publishes the authenticated inode or returns EEXIST. Scope still excludes another actor mutating final files *after* publication and unsupported filesystems.

**DO NOT INFER:** An absolute impossibility of secure existing-target overwrites, a universal Linux/filesystem property from one local filesystem, safe/unsafe macOS or Windows behavior, a measured exploit probability, new CMPCT Reader regression, or a release candidate. The existing-target contract might require an ownership/permission boundary incompatible with equally empowered directory writers, explicit failure/refusal, or a different kernel primitive. In-place fd update loses atomic failure preservation and hardlink semantics; unlink-then-link creates a visibility gap. Do not substitute either without separate experiments and honest cost accounting.

## Next decision

1. Recover the **exact final-HEAD** GitHub Actions run and original artifact; distinguish genuine SUCCESS from queued/blocked/failed. Verify the structured original receipt with the independent auditor. If hosted infrastructure unavailable, preserve this local truth only.
2. Share the narrow negative with the existing-target issue #528 and J24F11/#557 + J24F12/#559 owners. Do not edit their branches or claim the issue is resolved.
3. For product work, compare a formally specified existing-target threat model and atomic-overwrite/inode-identity demands; pursue a new ownership boundary only if it avoids the proven two-step source-name vulnerability. Separately close the broader existing Reader and release/performance gates.

**No code under `src/`, `native/`, `tests/`, or `benchmarks/` was changed; revision 24 and v0.30.0 remain unchanged.**
