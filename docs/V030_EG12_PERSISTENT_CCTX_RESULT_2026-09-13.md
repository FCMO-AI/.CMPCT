# v0.30 EG12 persistent-CCtx result — 2026-09-13

Status: **negative evidence; family retired under the preregistered mission lock; no product/release credit**

Measured head: `d8904770b7de62dd5f612f9ffc67f9d9b067ba2d`

Hosted run: `34767733310`

Artifact: `10320133807`

Artifact digest: `sha256:e56cc6925cd463d4ba2f5199ecc12c92bc6c5f861ce6adaedacf3e64ac7146ee`

Verdict: `EG12_PERSISTENT_CCTX_INVALID`

## Preregistered question

Could the exact EG11 effort ladder reuse one libzstd `ZSTD_CCtx` across independent `ZSTD_compressCCtx` calls, preserving every inherited `ZSTD_compress` frame while removing repeated context setup cost?

The mission lock required exact direct-frame equivalence, exact complete-archive bytes, unchanged geometry, strong verify/tail recovery, no positive RSS delta, no confirmed per-workload CPU/wall regression, and material aggregate CPU improvement of at least 3% or 0.5 s.

## Result

The nine-surface referee completed and preserved several product-level invariants:

- 9/9 complete EG12 archives were byte-identical to EG11;
- aggregate archive byte delta was `0 B`;
- all rows preserved locality geometry;
- all rows strong-verified and tail-recovered;
- maximum positive RSS delta was `0 KiB`;
- no confirmed per-workload CPU or wall regression was observed.

However, the hypothesis failed both preregistered promotion requirements that matter here:

- direct frame equivalence failed on 8/9 workloads across the sampled inherited effort ladder;
- aggregate creation CPU moved only `32.022869121 s -> 31.707971554 s`, saving `0.314897567 s` (`0.990166x`, about 0.98%), below both materiality bars;
- aggregate wall moved `32.043450661 s -> 31.725593520 s` (`0.990080x`).

The direct-frame probe performed `720` checks. Mismatches were observed on Office, Analytics, Logs, ML artifacts, Large Mixed Binary, Shifted Versions, False Neighbors and Boundary Churn. The hosted candidate executed `5,517` persistent-context compression calls.

## Interpretation

Complete-archive identity does not rescue the hypothesis. The independent probe intentionally prices losing/intermediate ladder frames as well as selected output. A persistent CCtx can therefore leave the final winner unchanged on these nine surfaces while changing frames that remain part of the encoder's proof/search surface. The mission lock explicitly forbids inheriting trust from unchanged final bytes when those direct frames diverge.

The speed signal is independently too small to carry a second compressor-state path even if exactness had held. This closes the proposed setup-overhead explanation for a material fraction of current EG11 creation cost.

Do **not** follow this result with buffer-size, timing-boundary, context-reset, or nearby API variants whose only purpose is to recover the missing percentage. Reopening this family requires a genuinely different mechanism that proves exact selected/search semantics before result-bearing execution.

## Research allocation consequence

Encoder micro-optimization is deprioritized. Forge work returns to exported read-cost/composition debt and the dominant Genesis density deficits, especially Office and Analytics, while preserving the large creation-speed advantage of the v0.30 line. The corrected Office physical-economics referee already executes the frozen Genesis v0.29 research product (`experiments/entropygraph_v029_residual_strict.py` at `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`) under a fail-closed source seal; future Office attribution must use that semantic comparator rather than the shipping r24 `Builder`.

Genesis/ONE evidence is unchanged. `research/cmpct1` remains an active secondary research line.