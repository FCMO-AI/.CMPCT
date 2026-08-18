# CMPCT v0.30 release receipts

This directory is intentionally empty of passing receipts until the corresponding release gates are genuinely green.

`tools/check_v030_release_lock.py` is the authority. The manifest is `docs/V030_RELEASE_LOCK.json`.

## Specialist workflow

1. Finish the owned task on the exact implementation that is intended for integration.
2. Reconcile/import all release-critical implementation changes before final evidence.
3. Run:

   ```bash
   python tools/check_v030_release_lock.py --print-fingerprint
   ```

4. Run the owning release gate and commit its durable machine evidence under `benchmarks/history/` or the appropriate conformance/evidence path.
5. Generate the receipt skeleton:

   ```bash
   python tools/check_v030_release_lock.py --template <receipt-id>
   ```

6. Replace placeholders only with measured facts. Every `evidence[].sha256` must be the SHA-256 of the committed evidence file named by `evidence[].path`.
7. Save the receipt as `docs/v030-release-receipts/<receipt-id>.json` and run the release lock again.

## What a receipt means

A receipt is a compact, machine-checkable handoff. It is **not** the underlying evidence and cannot replace it. The lock checks:

- exact receipt schema/id/owner;
- `status: pass`;
- the current release-critical fingerprint;
- existence and SHA-256 of every referenced durable evidence file;
- the immutable numeric/safety assertions in `docs/V030_RELEASE_LOCK.json`.

Footnote: the fingerprint deliberately excludes this receipt directory. A receipt cannot include itself in a commit SHA without circularity; instead it binds to the content of every implementation/native/benchmark/test/workflow/policy file that can affect the result. If one of those files changes, old receipts fail closed.

## No synthetic greens

Do not write a passing receipt from local intuition, terminal prose, a queued workflow, or an old branch's artifact. The receipt must be backed by durable evidence for the same release-critical fingerprint. If a gate is red, preserve the red evidence and leave the receipt absent.
