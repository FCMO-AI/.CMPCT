# CMPCT v0.30 release receipts

This directory is intentionally empty of passing receipts until the corresponding release gates are genuinely green.

The mandatory release command is:

```bash
python -m experiments.entropygraph_v030_release_lock_strict
```

`experiments/entropygraph_v030_release_lock_strict.py` is the hostile-input front door. It rejects non-standard/non-finite JSON, symlink/escape evidence paths, and stale evidence from a different release-critical fingerprint before delegating evidence binding, thresholds and task-state policy to `tools/check_v030_release_lock.py`. The core tool is an implementation module; **do not use it directly to authorize promotion**. The manifest is `docs/V030_RELEASE_LOCK.json`.

## Single-executor evidence workflow

1. Finish the relevant T00–T04 implementation obligation on `agent/v030-authoritative-integration`.
2. Reconcile current `main` and ensure every release-critical implementation change is already represented on the authoritative branch before final evidence.
3. Run:

   ```bash
   python -m experiments.entropygraph_v030_release_lock_strict --print-fingerprint
   ```

4. Run the corresponding release gate on that frozen source. The durable **strict JSON** evidence must record the exact printed fingerprint in a stable field, normally top-level `candidate_fingerprint`, before it is committed under `benchmarks/history/` or the appropriate conformance/evidence path. `NaN`, `Infinity` and `-Infinity` are not release evidence.
5. Generate the receipt skeleton:

   ```bash
   python -m experiments.entropygraph_v030_release_lock_strict --template <receipt-id>
   ```

   The strict template includes `candidate_fingerprint_source`, which points to the JSON evidence field that proves the artifact was produced for the current fingerprint. Do not remove it.
6. Replace placeholders only with measured facts. Every `evidence[].sha256` must be the SHA-256 of the committed evidence file named by `evidence[].path`.
7. For every normative `facts.*` field, fill its `fact_sources` binding with the exact evidence index and dotted JSON path that contains that value. The lock reads the hashed evidence itself and requires exact agreement before it applies the threshold.
8. Save the receipt as `docs/v030-release-receipts/<receipt-id>.json` and run the strict release lock again.
9. Move the relevant task to its required terminal state only after its implementation and evidence obligations are actually complete. The final unlock reads task files directly; a receipt cannot self-report that work is done.

## What a receipt means

A receipt is a compact, machine-checkable evidence index. It is **not** the underlying evidence and cannot replace it. The strict lock checks:

- standards-compliant JSON only and finite numeric values;
- repository-contained ordinary evidence/task files with no symlink component;
- exact receipt schema/id/task association;
- `status: pass`;
- the current release-critical content fingerprint;
- an exact evidence JSON path proving that the hashed artifact itself records that same current fingerprint;
- existence and SHA-256 of every referenced durable evidence file;
- exact `facts.*` equality with the bound JSON path inside already-hashed evidence;
- the immutable numeric/safety assertions in `docs/V030_RELEASE_LOCK.json`;
- the actual task states required by the release manifest.

Evidence files may not point into this receipt directory. A receipt cannot use another receipt—or itself—as the thing that proves a release fact.

Footnote: the fingerprint deliberately excludes this receipt directory. A receipt cannot include itself in a commit SHA without circularity; instead it binds to the content of every implementation/native/benchmark/test/workflow/policy/public-surface file that can affect the result. The strict front-door implementation itself is under the fingerprinted `experiments/entropygraph_v030_*.py` surface, so weakening it invalidates old receipts. The evidence-fingerprint binding separately prevents an old green artifact from being paired with the new fingerprint. Task states are checked separately and directly.

## Final task-state rule

The release lock currently requires:

- T00 main/reconciliation + final regression: `DONE`;
- T01 native/portability: `DONE`;
- T02 evidence/performance: `DONE`;
- T03 graph/productization: `DONE`;
- T04 final-release preparation: `REVIEW`.

T04 intentionally stops at `REVIEW` before unlock because the lock is what authorizes its irreversible final actions: version/site publication, merge to `main`, tag/release, and live-surface verification. Requiring T04 `DONE` before unlock would be circular.

## No synthetic greens

Do not write a passing receipt from local intuition, terminal prose, a queued workflow, an old branch's artifact, or a manually transcribed headline number. The receipt must be backed by durable strict-JSON evidence for the same release-critical fingerprint and every normative fact must resolve back to that evidence. If a gate is red, preserve the red evidence and leave the receipt absent.
