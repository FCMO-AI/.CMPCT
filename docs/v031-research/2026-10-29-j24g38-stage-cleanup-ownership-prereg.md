# J24G38 — Fail-closed compaction stage cleanup must not delete unowned leaf

Date: 2026-10-29 UTC. Prospective **product-candidate repair**, not a release.

## Parent/evidence

Parent #741 exact `a2f4804c203caeb5d4b81c24456517fa2f398349` (unmerged POSIX FD-owned compaction). Scientific child #744, original source-exact run [#40841958209](https://github.com/FCMO-AI/.CMPCT/actions/runs/40841958209), completed SUCCESS in Ubuntu/macOS for a **negative-witness** product court: a pre-open `os.open` substitution with actor-created `payload.cmpct` is correctly rejected, yet the failure cleanup deletes the actor's preplanted payload even though CMPCT never opened/created it. Same-UID 0700 directory impersonation was accepted (distinct identity not proved); symlink and bad-mode replacements were rejected. Local Linux cross-UID POSIX primitive model additionally demonstrated that a 0777 attacker-owned replacement directory can lose an attacker-owned leaf on failure and a 0555 directory may raise PermissionError during unlink and leak the parent+stage FDs. The cross-UID model is NOT installed-CMPCT evidence.

## Primary question and preregistered prediction

Can POSIX compaction cleanup remove *only* a stage leaf tied to an explicitly opened/owned `write_fd`, and close both directory FDs even if cleanup raises, while leaving the original #741 success path, physical archive identities, and after-open ancestor-rebind protection intact?

Expected: a stage directory substituted **before `write_fd` creation** containing a foreign `payload.cmpct` is never unlinked by CMPCT. Symlink/bad-mode/preplanted cases reject without destination/source/sentinel alteration; same-UID matching mode substitution may still be accepted because this repair does NOT prove the original stage directory identity. On ordinary successful compaction, POSIX Builder/Reader and fd-relative publish remain unchanged.

## Mechanism/control/kill

Strong control: unchanged #741 ordinary compaction with source SHA + logical member metadata/digests and the original after-open ancestor attack court, including inherited tests (do not edit those tests). Surgical fix: gate cleanup of a staging pathname on actual `write_fd` ownership; if a leaf exists, compare its `lstat` dev/inode with the `fstat` of the owned FD before unlink; always close stage and parent dirfds via nested finally. Avoid deleting or rmdir-ing an unowned substituted stage if no leaf was successfully created. Tradeoff: a failed pre-open attempt may leave an empty stage dir; do not conceal that cleanup debt. A same-UID actor can still rebind between stat and unlink: this patch **does not** assert complete same-UID adversarial security.

Falsifier: any foreign leaf removed on preopen failure, destination/source/sentinel modified on a rejected case, invalid or wrong archive on accepted case, inherited after-open protection regression, FD leak on explicit hostile failure, or failure to keep the original physical semantics. No Windows, power-loss, full performance or general-format certification anticipated.

## Alternative frames

Avoiding cleanup entirely eliminates unlink races but accumulates temporary files; using random names only does not prove ownership; an unnamed Linux O_TMPFILE route is not portable to macOS/Windows. This bounded correction is useful without claiming to solve all staging custody.

## Evidence rung and promotion

Implement smallest diff confined to `src/cmpct/transactions.py` on an isolated child of #741; transfer #744's installed physical court with reversed *foreign leaf preservation* expected outcome, plus unchanged original #741 court. Run source-locked Ubuntu/macOS CI. Preserve exact-head evidence and negative controls; do not touch benchmarks, release gates, native code, format, version, `main` or Discovery STATE. No merge until full owner and release reconciliations.
