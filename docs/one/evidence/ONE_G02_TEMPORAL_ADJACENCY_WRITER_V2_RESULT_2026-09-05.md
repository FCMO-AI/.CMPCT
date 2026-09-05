# ONE-G0.2 — corrected temporal-adjacency writer v2 result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **HOLD temporal writer gate**

## Evidence identity

- branch head under test: `8daf2f117c6874b42c6d7b9dc7e69cd72e9b0822`
- PR merge SHA executed by Actions: `0b62c944d2cb3eeddc1bcaf840504658c4ca6c69`
- workflow run: `33980138562`
- job: `101343783604`
- artifact: `9973507711`
- artifact name: `one-g02-temporal-adjacency-writer-v2-0b62c944d2cb3eeddc1bcaf840504658c4ca6c69`
- artifact SHA-256: `d199a8fab8f8f4ac48943370df8a076dcf9381c8829259400d0d69c9d897413c`
- ONE semantic/hostile suite: `83 passed in 0.72s`

The v2 harness exists because hostile review found the original integration harness exceeded the original frozen compiler boundary by compiling damaged relations. V2 preserves the original corpus, rounds, and timing gates while restricting generic relation compilation to byte-exact `+1` shift structure. Accepted damaged relations remain literal and are counted as compiler debt.

## Frozen timing result

Aggregate mixed-stream baseline median: `102,422,057 ns`.

Aggregate candidate median: `102,607,926 ns`.

Candidate / baseline: **`1.001814736x`**.

Frozen aggregate promotion gate: `<= 0.92x`.

Median of the seven size-class ratios: `1.001218904x`.

| relation bytes | candidate / baseline | row gate <=1.03x |
|---:|---:|:---:|
| 4,096 | 1.003336445x | pass |
| 8,192 | 1.001222366x | pass |
| 16,384 | 1.001218904x | pass |
| 32,768 | 1.001055946x | pass |
| 65,536 | 1.000692751x | pass |
| 131,072 | 1.003858374x | pass |
| 262,144 | 0.999471153x | pass |

Every individual size remained inside the 1.03x guardrail, but the aggregate speed objective failed decisively. The earlier dispatch-only ~0.78x result therefore does **not** survive complete research-writer Program construction and wire encoding at this abstraction layer.

## Semantic and representation result

Classification remained exact and equivalent wire decisions remained byte-identical. All produced programs round-tripped through ONE decode/evaluate exactly.

Across the 21 productive relation rows (three productive relation cases at each of seven sizes):

- generic exact `+1` relation compiled rows: **7**;
- accepted-but-literal damaged rows: **14**;
- therefore **2/3 of accepted productive relation rows currently remain compiler debt** under the deliberately minimal frozen compiler.

Exact-shift storage over two literal inputs approached 0.5x as size increased:

- 4 KiB: `0.515747x`;
- 16 KiB: `0.504089x`;
- 64 KiB: `0.501022x`;
- 256 KiB: `0.500256x`.

Literal fallback rows approached 1.0x but retain small control/integrity overhead (for example `1.014282x` at 4 KiB and `1.000231x` at 256 KiB).

At 16 KiB and above the candidate paid the frozen 160-byte sparse gate; below 16 KiB it correctly used direct exact proof with zero sparse reads.

## Referee decision

**Do not promote the amortization-safe turnstile into the current Python research-writer integration on speed grounds.** The complete writer path erases the isolated dispatch gain.

This does not retire the turnstile micro-result: it remains exact and useful as a lower-level admission optimization. It does establish that optimizing dispatch alone is currently below the dominant writer cost owner.

The result also identifies a larger representation opportunity than the speed micro-optimization: 14 accepted damaged-relation rows are recognized but deliberately left literal. The next material experiment should measure whether expressing those damaged relations through the existing generic ONE grammar (ranged Ref + Surprise islands under concat) produces enough stored-byte benefit to justify its control bytes, node count, reader work, and creation cost. That experiment must be separately preregistered; the original over-capable v1 harness is not admissible as its result.

A parallel phase-decomposition experiment may quantify how much complete writer time belongs to relation dispatch versus Program construction and wire encoding, but it should be causal diagnosis, not a route to threshold tuning.

## Claim boundary

This is research adjacent-version known-pair evidence only. Python object/wire timing is not product-speed authority. Arbitrary pair discovery remains outside scope. No v0.29/v0.30 superiority claim follows.
