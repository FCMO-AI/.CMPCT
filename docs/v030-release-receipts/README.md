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

4. Run the owning release gate and commit its durable **JSON** machine evidence under `benchmarks/history/` or the appropriate conformance/evidence path.
5. Generate the receipt skeleton:

   ```bash
   python tools/check_v030_release_lock.py --template <receipt-id>
   ```

6. Replace placeholders only with measured facts. Every `evidence[].sha256` must be the SHA-256 of the committed evidence file named by `evidence[].path`.
7. For every normative `facts.*` field, fill its `fact_sources` binding with the exact evidence index and dotted JSON path that contains that value. The lock reads the hashed evidence itself and requires exact agreement before it applies the threshold.
8. Save the receipt as `docs/v030-release-receipts/<receipt-id>.json` and run the release lock again.
9. Move the owning coordination task to its required terminal state only after its implementation and evidence obligations are actually complete. The final unlock reads task files directly; a receipt cannot self-report that work is done.

## What a receipt means

A receipt is a compact, machine-checkable handoff. It is **not** the underlying evidence and cannot replace it. The lock checks:

- exact receipt schema/id/owner;
- `status: pass`;
- the current release-critical content fingerprint;
- existence and SHA-256 of every referenced durable evidence file;
- exact `facts.*` equality with the bound JSON path inside already-hashed evidence;
- the immutable numeric/safety assertions in `docs/V030_RELEASE_LOCK.json`;
- the actual Git coordination task states required by the release manifest.

Evidence files may not point into this receipt directory. A receipt cannot use another receipt—or itself—as the thing that proves a release fact.

Footnote: the fingerprint deliberately excludes this receipt directory. A receipt cannot include itself in a commit SHA without circularity; instead it binds to the content of every implementation/native/benchmark/test/workflow/policy/public-surface file that can affect the result. If one of those files changes, old receipts fail closed. Coordination task states are checked separately and directly.

## Final task-state rule

The release lock currently requires:

- T00 main/reconciliation + final regression: `DONE`;
- T01 native/portability: `DONE`;
- T02 evidence/performance: `DONE`;
- T03 graph/productization: `DONE`;
- T04 final-release preparation: `REVIEW`.

T04 intentionally stops at `REVIEW` before unlock because the lock is what authorizes its irreversible final actions: version/site publication, merge to `main`, tag/release, and live-surface verification. Requiring T04 `DONE` before unlock would be circular.

## No synthetic greens

Do not write a passing receipt from local intuition, terminal prose, a queued workflow, an old branch's artifact, or a manually transcribed headline number. The receipt must be backed by durable JSON evidence for the same release-critical fingerprint and every normative fact must resolve back to that evidence. If a gate is red, preserve the red evidence and leave the receipt absent.
