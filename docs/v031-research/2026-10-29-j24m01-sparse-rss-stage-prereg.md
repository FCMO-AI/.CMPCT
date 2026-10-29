# J24M01 — preregistered sparse RSS source/stage court

**2026-10-29 UTC — scientific/evidence-only. No product, format, release, evaluator or threshold changes.**

## Source and exact baseline
Released main v0.30.0/r24 at `80c358f8824ec1b20d349c92ed94c898090969b0`. This branch is based solely on J24G34 product owner #738 at `ec112a87ea34349b63885f3f0bea4689f192bd2f`, Reader blob `f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f`. The exact-head full-suite [Actions #40836830773](https://github.com/FCMO-AI/.CMPCT/actions/runs/40836830773) failed `test_real_256m_sparse_verification_does_not_materialize_holes` with `verified=1, peak_kib=180416`, above its unchanged 131072-KiB limit. Separate 128-MiB fresh-process #738 results had ~25-MiB peak, but use distinct physical inputs.

The failing suite test already executes verification in a **fresh child**, so parent pytest high-water contamination alone cannot explain its peak. It does not report exact imported Reader SHA, physical extent bytes or stage-by-stage kernel RSS.

## Primary question and predictions
Which stage first owns the excess RSS on authentic revision-24 256-MiB sparse verification: dependency import, Reader/index open, logical SHA verification, encoded extent decode, or installed-environment discrepancy? Do not assume 128/256-MiB cases have equivalent physical work.

**H_import:** high `VmHWM` appears by import. **H_open:** it rises on archive open. **H_verify:** it rises only while verifying despite tiny physical extent bytes and decoded payload. **H_physical:** materialized physical extents/record bytes explain it. **H_environment:** same archive/source under editable vs installed wheel changes the answer. Strong simpler controls: source-exact 2/128/256-MiB sparse shapes, uninstrumented repeat child and physically identical input; compare installed Reader Git blob, logical SHA, archive SHA, `VmRSS/VmHWM/ru_maxrss`, process CPU/wall, decoded bytes and cache.

## Kill/decision gates
Wrong source blob, non-sparse encoding, differing source SHA within an A/B, incorrect verify count, missing kernel counters or mismatched logical SHA invalidate that arm. A repeatable >128-MiB peak first arising during verify with small physical extents is genuine verification-stage debt; high before verify narrows to import/open/physical layout. A fresh-host non-reproduction remains non-reproduction, **not** historical test fixed. Preserve the general test and its cap exactly, never reinterpret a diagnostic pass as promotion credit.

Alternatives: do nothing (leaves release-critical CI ambiguity); clone another sparse verifier (duplicates owned code); reduce cap (forbidden); cheap source+stage attribution (chosen). Predictions are frozen **before** the instrument. Existing #738 remains product owner. This lane adds diagnostic code, dedicated CI and honest result only; no shared Discovery STATE write, merge or release. Hosted CI/provider run IDs and raw receipts must be attached before scientific decisions.
