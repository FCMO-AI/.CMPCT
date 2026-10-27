# J24D05 — Direct temporary-file mode ownership (prospective freeze)

Date: 2026-10-27 UTC. Status: **FROZEN before product mutation or result-bearing candidate test**.
Owner: Phased1, narrow stacked child of J24D03 #588 `1778085a1ff5278fadf5f3a12b5f950008a8d939`; inherited Reader blob `1273708b42d2164ac806eea9297ac6fc098104b4`. No modifications to #588, #585, #589 or shared discovery cache.

## Exact defect/opportunity
The inherited `_extract_direct_staged` calls `os.chmod(tmp, archived_mode)` when `os.fchmod` is unavailable. That uses a mutable pathname, inconsistent with J24W02 #536's proven fd-only/skip-optional-mode invariant for chunked output. If an attacker with namespace-write access substitutes that name, the chmod may act on an unrelated inode. No general same-UID output-name security is claimed, because the later `os.replace(tmp, full)` remains name-based (#528). J24D04 #589 independently owns umask/hardlink measurement; this slice does **not** change POSIX `fchmod` or choose a general metadata policy.

## Primary falsifiable question
Can the direct staged writer **omit optional mode changes entirely when fd-chmod is absent**, rather than touching the temporary pathname, while still preserving authentic direct RAW/Zstd/Deflate exact extraction, failure atomicity under a real short kernel write followed by ENOSPC, unchanged existing files/inodes after rejection, and POSIX fd-only mode semantics where available?

Prediction: under simulated `os.fchmod` absence, `os.chmod` is **never invoked by the staging helper** on clean or failed direct output when `metadata=False`; a `ValueError` from available `fchmod` propagates and leaves the old destination intact, while an `OSError` retains prior best-effort behavior. Clean final bytes must match independent revision-24 SHA-256 vector commitments; direct failure leaves sentinel bytes and inode and no stage. A source-exact three-host installed-package court must observe Windows without `fchmod`, Linux/macOS with it, and true absence simulation on all hosts. Unexpected `os.chmod` call, any wrong digest, skipped real short write, lost sentinel, unhandled known optional API absence, or new leftover temporary file **falsifies** the hypothesis.

## Alternatives and BONK
- Reopen/chmod stage by pathname: already identified unsafe ownership seam (#528); reject.
- Add Win32 handle-mode mapping: larger ABI/platform surface without evidence of need for correct `metadata=False` output; reject for this slice.
- Catch `AttributeError` around chmod: could hide unrelated code defects; reject.
- Chosen: `fd_chmod = getattr(os, 'fchmod', None)` and call **only** when it exists; same minimal principle as proven J24W02 chunked path.
- General umask, external hardlink, POSIX target-mode and ACL policy: material separate correctness/semantics debt measured by J24D04 #589. Do not conceal or claim solved.
- Even if mode-only optimization is positive, same-UID stage substitution, postpublication name changes, sparse #572, crash/fsync durability and whole-system performance remain unresolved.

## Controls and evidence rung
Lowest decisive rung: inspect actual Reader function and use an independent Python mechanism-level missing-API/chmod trap with real file-descriptor short writes; then installed-package source-exact GitHub Actions on Ubuntu 24.04, macOS 14 and Windows 2022 using unchanged Builder-independent `tests/conformance/v24-direct-codecs.json`. Preserve historical J24D02/J24D03 tests and thresholds, source/hash bindings and independent receipt checks; **do not** rewrite historical pinned courts to make them green. Run unchanged inherited five-vector behavior independently through a new source-bound court.

## Physical costs, limits and decision
No archive bytes, format revision, codec or Builder change. Mode API lookup changes one branch/file; complete wall/CPU/RSS/temporary I/O, Windows ACL fidelity, external aliases and release parity remain unmeasured. On Windows/forced-absent API, `mkstemp`'s restrictive mode may remain until optional final metadata restoration; this is a deliberate compatibility boundary, not an earned Windows-POSIX mode parity claim. Promote only after broader filesystem policies are reconciled. Green targeted CI earns **candidate evidence only**; no merge/release.
