# J24M01c — full-suite, same-command physical archive custody (2026-10-29 UTC)

**Prospective continuation after J24M01b.** Exact product source unchanged; prior negative results never overwritten.

## Prior evidence and decision
Original full suite [Actions #40836830773](https://github.com/FCMO-AI/.CMPCT/actions/runs/40836830773) on product owner #738 HEAD `ec112a87ea34349b63885f3f0bea4689f192bd2f` failed its inherited 256-MiB sparse threshold: `verified=1, peak_kib=180416` vs `131072` KiB. The exact same Reader Git blob `f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f` in fresh stage-scoped children (Ubuntu hosted run #40889149120 and corrected-root #40889955744) measured 23.8–24.2 MiB with only two 4096-byte physical sparse extents. Corrected checkout-root isolated inherited test with default conftest passed under editable-full and wheel-full; wheel-minimal default conftest lacked optional `zstandard` and failed before execution. The first root-**outside**-checkout default-conftest import error was explicitly a harness defect, not an RSS failure.

## One unresolved question
Does the **unchanged full-suite test order**, under the **same installed editable-full dependency set and same invocation** `python -m pytest -q`, still recreate the 180-MiB outlier? If so, is the archive physical sparse extent layout actually different, or does full-suite-import/environment custody change the child Reader/code/runtime? Need to preserve the exact failing physical bytes; verbal claims of environment differences are not enough.

## Preregistered method and controls
A dedicated job invokes the exact full suite under checkout root after `pip install -e '.[test,audio]'`, records pytest stdout and exit code without waiving failures, and after test completion inspects the retained `tmp_path` corresponding to `test_real_256m_sparse_verification_does_not_materialize_holes`. Do not modify test, Reader, Builder, threshold, error messages or original CI. Record archive SHA256 and byte size; source logical SHA256, `st_blocks`, source size; source Git blobs; Reader-exposed member row, `S_SPARSE` extent lengths and blob headers; report **post-suite re-verification in a fresh subprocess only as a separately labeled diagnostic**. Upload actual physical CMPCT archive if below a safely bounded 10-MiB limit, original full-suite log and all receipts whether the suite passes or fails; never upload 256-MiB sparse source logical bytes.

## Predicted fork and kill conditions
If unchanged full suite reproduces >131072 KiB and the physical archive contains large allocated extents, prioritize Builder/input physical ownership; if it has only 8192 encoded extent bytes, prioritize child import/dependency/env or post-suite source mismatch. If full suite does not reproduce the failure, classify run-to-run **ambiguity** and preserve the original negative without waiving CI. If the retained archive is absent, classify missing evidence, not zero/healthy RSS. A positive same-archive re-verification after suite is evidence only for post-suite context, not what child imported during the original failure.

This is a single bounded full-suite evidentiary discriminator, not a release rerun on behalf of the product owner. Repo owner #738 retains source and promotion authority. No Discovery STATE write or benchmark gate adjustment.
