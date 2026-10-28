# J24B08b — Extend quantized Win32 CPU rule to 100k-row component micro

Date: 2026-10-28 UTC. Follow-up to [J24B08a](2026-10-28-j24b08a-win32-cpu-quantization-addendum.md), **before** referee-only correction. All original experiments and threshold semantics preserved.

## Newly observed second surface
Exact HEAD `548ffb1bcc8b673c30866f17bc20db013ae24334` again produced complete Windows performance receipts but failed the independent audit, now specifically `research/j24b08_budget_guard_referee.py:123`: 100,000-row **component micro** CPU samples were asserted strictly positive. [Original #40746690944](https://github.com/FCMO-AI/.CMPCT/actions/runs/40746690944), Windows job `123022995058`, original artifact [#12842396827](https://github.com/FCMO-AI/.CMPCT/actions/runs/40746690944/artifacts/12842396827), ZIP SHA-256 `78bb9495d8a298585147067f4d85f6f6063b4a5d4de0123599ed922ea1495b67`.

Third-root inspection of original raw receipt shows base `12/16` and candidate `10/16` `micro.raw[*].cpu_ns=0`, but every corresponding monotonic wall time was **positive (~4–7ms)**. Windows CPU process timer jumps in 15.625ms increments; this is an observed clock-resolution limitation in the **secondary component control**, not missing measurement data or Reader semantic failure. The installed full-extraction comparisons completed and printed a valid quantitative receipt.

## Narrow repair
Apply the already preregistered J24B08a metrology rule **consistently** to secondary micro receipts: `cpu_ns` must be a nonnegative exact `int`; `wall_ns` remains a strictly positive exact `int`. Preserve all median recomputations and all six forged-receipt falsifiers, source archive byte identity, physical checks, experimental inputs, timing boundaries, critical 5% AND 3ms gate and release law. Do not substitute CPU clock zeros with guessed values or declare Windows micro CPU speedup; report wall micro and CPU-quantized limitation separately.

The original two failed Windows jobs remain failed; repaired HEAD must pass independent source-exact rerun on three hosts. This is metrology evidence repair, **not** product hardening, an evaluator relaxation to accept incorrect output, or successful benchmark retroactively.
