# J24D04 prospective falsifier — direct staged extraction and metadata=False umask custody

**Registered 2026-10-27 UTC, before writing/running the scientific instrument.** This is research-only, subordinate to existing J24D02/J24D03 owners. No product, release, benchmark, threshold, format or governance mutation.

## Frozen source and authority

- Released source-exact control: `main@80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0 / revision-24).
- Staged candidate: `PR #588@1778085a1ff5278fadf5f3a12b5f950008a8d939` (stacked on #585).
- Original complete direct-source defect: issue #582, original scientific reproduction #581.
- Known publication/symlink/hardlink limitations remain separate: issues #528, #265; PR #294 owns static external hardlink policy, and is **not** modified by this test.
- Existing conformance `tests/conformance/v24-direct-codecs.json` is immutable, builder-independent and carries SHA256-checked signed-r24 framing.

## Primary question

Does J24D02's move from direct `os.open(O_CREAT|O_TRUNC, mode)` to `tempfile.mkstemp + fchmod/chmod + os.replace` change the **actual permission bits** of a legitimate extracted direct file when `metadata=False` and process umask is restrictive?

### Predicted outcome (must NOT adjust after data)

Under POSIX umask `0o077`, a clean destination file extracted with `metadata=False` historically receives `archive_mode & ~0o077`, while candidate may receive the archive mode itself because it changes permissions on the staged inode after creation, bypassing the caller's umask. This divergence is material **only if** the golden fixture mode grants any group/other bit. Otherwise record `NOT_IDENTIFIABLE_ON_GOLDEN` rather than rewriting the oracle.

For a pre-existing ordinary destination with restrictive mode `0o600`, the historical `O_TRUNC` write preserves its inode and permission bits; staged `os.replace` changes inode and may apply the archive mode despite `metadata=False`. This is an independent, stronger discriminator if the archive fixture mode differs from `0o600`.

When `metadata=True`, both sources should apply archive mode and exact bytes (POSIX control), so mode differences only under `metadata=False` are attributable to the publication ownership change.

### Stronger alternative and hostile checks

- Clean output and preexisting output use same authentic archive/source bytes; check complete SHA256 and actual modes, umask, inode/link count and no residual `.cmpct-part-` stages.
- External hardlink alias: historical in-place overwrite modifies the alias, while candidate staged replace preserves alias but detaches the existing leaf. **Neither is assumed universally right**; record as a semantic tradeoff, not a scored security bug.
- Symlink pivots and concurrent hostile writers are *not* claimed fixed. No path-following metadata tricks or relaxed archive checks.
- On Windows, use only exact-byte and no-crash controls: POSIX mode/umask/inode interpretations are not portable release claims.
- Never mutate the frozen direct conformance file, comparator or original products.

## Cheapest decisive rung / kill

Use real installed Python CMPCT packages from two exact Git commits in independent external site directories, one immutable RAW direct vector and the same process umask. Evaluate both `metadata=False` and `metadata=True`, fresh/existing dest, normal output and external hardlink alias. A clean POSIX metadata=False mode widening (especially on new files under 077) changes promotion decision: owner must preserve umask or explicitly adopt/document a different and safer contract with adversarial tests. If no divergence occurs with mode-sensitive goldens and destination setups, falsify the hypothesis.

**No product credit:** The court measures permissions, bytes, output inode and alias effects. It does not measure full CPU/wall/RSS/temp I/O, same-UID concurrency, entire archive transactions, Windows ACL parity, compression, or release readiness.

## Concurrency protocol

Product implementation belongs to PR #585/#588; this branch adds ONLY research instrument/CI/evidence. Before late writes, re-read owner source/HEAD and do not rewrite its findings. Do not edit discovery STATE; its active reconciliation owner is #574. Pass/fail GitHub Actions in this court represent successful *diagnostic classification*; a detected real regression must remain visible as a product negative.
