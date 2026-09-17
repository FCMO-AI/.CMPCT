# R42 ML shipping extraction owner diagnosis — 2026-09-17

Authority substrate: `agent/v030-authoritative-integration` @ `94dd456ff508ae4e60ba9230bc071fdc9cc4708d`.
Diagnostic source head: `566f5202a178d790f9a8cc1064a45d1ea13533f0` (workflow-only instrumentation over that authority substrate).
Workflow run: `35251368048`.
Artifact: `10508644667`, digest `sha256:112661d87f0b471eb9554087f0442936347e547e32a3da0a8743fe9c900f3e70`.
Claim boundary: research/causal evidence only; `release_credit=false` throughout.

## Direct shipping-front-door profile

On `neutral_hostile_v1/09_ml_artifacts`, exact shipping extraction median was `0.1308416105 s` versus genuine r24 `0.0254932515 s`: **5.1324x r24** on this diagnostic run. The shipping archive was `329,367 B` smaller than r24.

The dominant cProfile self/cumulative owners were:

- `release_single_buffer_delimiter_inverse`: `45.432 ms` self / `88.743 ms` cumulative;
- OpenSSL SHA-256 constructor calls: `33.142 ms` self;
- SHA-256 update calls: `23.032 ms` self;
- `_get_varint`: `21.273 ms` self / `25.299 ms` cumulative.

The delimiter inverse therefore remains a large real owner even after its already-proven improvement over the prior reviewed bulk implementation. Reverting it is not supported: prior corrected evidence showed the shipping single-buffer inverse materially beats that predecessor.

## Exact no-DGO1 counterfactual

The exact-head counterfactual reached the private shipping owner and rejected the selected delimiter transform while preserving exact source-tree verification.

Shipping DGO1 archive:
- `13,674,823 B`;
- median extract `0.1305457400 s`.

No-DGO1 rebuild:
- **+52,189 B / +0.38164%** archive cost;
- median extraction improvement **40.488 ms**;
- extraction ratio **0.68986x** shipping / **1.44958x speedup**.

The no-DGO1 build-wall number is context-only and not product-creditable because the diagnostic must disable the preserved G04 process-pool eligibility seam to make the parent-process semantic counterfactual observable.

Same-byte guarded-banded-v2 was decisively worse than the installed shipping inverse: `0.278497 s` median, **2.1333x slower** than shipping. Do not reopen that family.

## Derived bound

Against the same-run r24 median, the shipping absolute extraction debt is about **105.05 ms**. The exact no-DGO1 gift removes **40.49 ms**, or only **38.54%** of that debt. Even after surrendering DGO1 entirely, extraction would remain about **3.533x r24**. Therefore delimiter selection alone cannot retire the release-performance blocker.

The no-DGO1 archive would still be **277,178 B / 1.98% smaller than r24**, so a representation fallback remains a technically valid emergency Pareto point if implementation repair fails. It is not the preferred next action because it gives back an already-earned 52,189 B and still leaves most of the extraction debt intact.

## Decision

DGO1 currently buys only about **52 KiB / 0.38%** on this ML archive while owning about **40.5 ms** of complete extraction wall versus the exact no-DGO1 counterfactual. That is a real representation/product tradeoff, not a microbenchmark artifact. However, deleting DGO1 would still leave extraction far above r24, so DGO1 alone is not the whole residual owner.

The next intervention should change implementation/ownership class rather than keep polishing Python delimiter loops. The repository already contains an independent Rust `cmpct-portable` r25/G04 reader. R42 has therefore launched a same-archive, exact-tree, symmetric fresh-process Python-vs-native extraction oracle to determine whether moving the hot reconstruction/verification path across the existing native boundary has enough headroom to change the product decision. If native wins materially, prioritize a bounded shared-native product path or native primitive with Python fallback; if it does not, profile the remaining hashing/record-verification ownership before changing representation.
