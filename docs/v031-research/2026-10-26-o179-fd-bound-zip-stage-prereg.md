# O179 — ZIP stage file-descriptor custody (preregistration)

Date: 2026-10-26 UTC. **Prospective: committed before O179 product code or result-bearing run.**

## Authority and baseline

Published CMPCT v0.30.0; on-disk revision 24. Owner O149 PR #492 at exact `ca01d885fedc8ffc343b9c3c624eddd134158452`, source Reader blob `496e70bdc06ddc17aa90e4fc0e9f10a6bc5c5332`. O143 #489 proved regular-target failure atomicity was absent before O149. O157/O157b #497 independently demonstrated a distinct exposed close/reopen stage pathname race on the original O149/O150 reader in both symlink and hardlink variants. The same-UID or directory-writer adversary can replace the newly created staging pathname before the writer's next `open(..., 'wb')`, so an unrelated inode gets truncated.

## Scientific question

Can the existing O149 ZIP generator write both fast and ZIP64-fallback output through the *original exclusively created staging file descriptor*, with a separate conservative identity check before publication, while retaining O143/O149 failure atomicity and O140 destination admission? No change to ZIP encoding, CMPCT revision 24, direct Deflate identity or the user's existing output on failure.

## Competing mechanisms / PARETOBONK

1. Original O149 close/reopen: proven victim mutation (O157), though ordinary failure atomicity works.
2. `O_NOFOLLOW` on stage reopen: inadequate to block O157b ordinary hardlink pivot.
3. Verify `lstat(stage)==fstat(original)` but continue *writing by path*: inadequate against swaps between check and reopen.
4. Chosen: write the ZIP to the exclusively-created open fd; use that stream for both fast and `zipfile.ZipFile` fallback; retain the descriptor until final identity verification, reject a mismatched stage entry before `os.replace`. This prevents the writer from writing to a substituted victim even if the pathname is replaced during production. The final pathname check is **not** a full atomic compare-and-rename primitive and cannot rule out swaps *after* the check.

## Predictions, kill/narrow conditions and costs

Predictions: clean fast and fallback ZIPs remain exact; corrupted early and late member plus injected partial writer failure still leave prior ZIP bytes/inode; O157-style deterministic symlink and hardlink swaps occurring after exclusive stage creation but before stream write do **not** modify an unrelated victim, and the identity check refuses to publish the substituted entry; no leaked stage files when recovery is possible. Reuse original O149/O140 tests unchanged plus a distinct positive O179 adversarial suite. On Windows, descriptor-based `zipfile.ZipFile` and direct fast-path must remain correct, although POSIX inode checks are stronger than Windows identity evidence. If exact-output semantics, cleanup, prior-target preservation, or source attribution fails, the hypothesis is **not** accepted.

Cost accounting: no full ZIP bytes copied; same staging disk footprint as O149; potentially one `fstat/lstat` pair and a stream wrapper; fast path retains binary file handle; ZIP64 fallback may use Python `ZipFile` seek/tell. Opening the stage fd once eliminates one stage name reopen; full throughput/RSS/temp-I/O and metadata/cross-platform/correctness must be measured before promotion. Same-UID races after identity check, output-directory ancestor pivots, power loss, remote FS, malicious intervention in permissions and inode metadata, and platform-specific metadata remain unproven. No universal TOCTOU or safe ZIP release credit is claimed.

## Ownership / concurrency

This is an isolated stacked research+repair candidate; do not touch PR #492/#497/#491 owners, historical negative tests, frozen benchmark/comparator or discovery STATE.json. Before late mutations reconcile current branch and owners. Preserve source exact-head, negative witnesses, and CI artifacts. The decisive result is the first authentic installed-reader POSIX/Windows suite, not code inspection or a green job that skipped tests.
