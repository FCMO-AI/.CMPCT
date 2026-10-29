# J24M01b — follow-up context discriminator (2026-10-29 UTC)

**Prospective addendum, after J24M01 stage observations and before correcting CI invocation.** Do not erase the original first-protocol error.

## Actual first observation
Exact-source Ubuntu Actions [#40889149120](https://github.com/FCMO-AI/.CMPCT/actions/runs/40889149120) returned successful instrument stage court in all three install modes (editable-full, wheel-full, wheel-minimal). Original three artifact ZIP SHA-256 values:
- editable-full #12903917141: `90ea8a977f0a89dafc0419d28c4e53742147843cbf108f562cab6bc66332985d`;
- wheel-full #12902849584: `4afdd00afda42e24ec7e50d109ed72a8f0caf55f5d059652948358703d05005f`;
- wheel-minimal #12904366366: `23eb613e862cbab7d420fccca90a4596f7913fa5d7b4893e03a43b3ecda57219`.

Across 27 actual fresh-process measurements, `VmHWM` remained within 23,904–24,140 KiB for 2/128/256 MiB S_SPARSE archives, each with two 4,096-byte encoded extents, 8,192 decoded bytes and per-archive physical byte charge ~1.2 KiB. Therefore the #738 same-version general-suite 180,416 KiB failure **did not reproduce** on these host contexts and input shapes. No proof of fix, no product credit. The original CI test remains unmodified.

## Instrument boundary discovered
The J24M01 CI invoked the inherited default-conftest probe from `$RUNNER_TEMP`. That failed **before the test executed** because `tests/conftest.py` imports `experiments` via the checkout root. A `--noconftest` probe in the same directory PASSED on each host. Therefore the old default-conftest 4 exit code was a **harness working-directory error**, *not* a sparse resource failure. Preserve raw original artifact/log, do not count it as a contradictory product test.

## New prospective discriminator
Repeat the unchanged inherited 256-MiB test from `$GITHUB_WORKSPACE` (the original full-suite working directory), once with `--noconftest` and once with normal `tests/conftest.py`. Capture both original exit codes/logs and verify that the expected package Reader Git blob is unchanged. The test is not modified. **Prediction:** both isolated full-cwd invocations pass if the 180,416 KiB outlier requires full-suite order, process environment leakage, or an anomalous physical fixture; otherwise a failure under default conftest isolates a narrower import/environment interaction.

A default-conftest PASS from root narrows but does *not* prove which earlier test altered runner environment/source state, because the original full-suite CI has many preceding tests; future same-runner execution-order bisection must preserve historical order and physical SHA. A root-cwd failure must be investigated with exact source and artifact. Do not weaken the 131,072 KiB RSS threshold. Do not use J24M01 to bypass publication or other inherited safety checks.
