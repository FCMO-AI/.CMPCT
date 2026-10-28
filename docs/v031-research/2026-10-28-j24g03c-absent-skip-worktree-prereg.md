# J24G03c — Absent skip-worktree source evades selected-row index validation

**Status: prospective adversarial amendment, before J24G03c implementation.** 2026-10-28 UTC, same PR #643 owner.

## New direct negative
A fresh real Git temporary repository with committed `a.py` and `b.py` proves: `git update-index --skip-worktree a.py`, followed by deleting `a.py`, leaves `git diff --name-only HEAD` **empty**; `git ls-files -v` retains `S a.py`; a filesystem-glob fingerprint sees only `b.py`. J24G03b currently checks flags only for `rows`, so it would miss this hidden *absent optional* source. This is a stronger adversarial case within the already preregistered index-trust surface, not a change to product release or a fictional remote exploit.

## Hypothesis / controls
The lowest-cost sound correction for CI custody is to reject **any** non-normal Git index trust flag in the checkout (instead of just the discovered `rows`), because an index-marked source may be hidden from `rows` by that same flag. Prefer one fail-closed uniform condition over attempting to infer glob coverage from missing filesystem paths. This deliberately rejects a sparse or flagged checkout that cannot prove complete Git-to-worktree source attribution; ordinary full checkouts remain eligible. Use the already available NUL-delimited index listing and error messages without adding subprocesses.

## Falsifier
Prerecord a new real Git test: omit an *optional* tracked source after `--skip-worktree`; `fingerprint()` sees fewer rows, `git diff HEAD` is empty, but `assert_git_head_custody` must refuse the receipt. Ensure normal clean checkout passes, clearing the flag restores acceptance, and original tests remain unchanged. A successful receipt after such omission disproves the fix. Full-platform CI must provide evidence. No policy/Discovery Engine edit from one narrowly scoped test.
