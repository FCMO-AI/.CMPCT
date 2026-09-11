# ONE-G0.2 observer-compatible relation band nomination — result receipt

**Status:** ADVANCE to fused-observer/native-cost integration; research-only  
**Branch:** `research/cmpct1`  
**Experimental version:** `ONE-G0.2`  
**Frozen instrument:** `benchmarks/one/one_g02_relation_band_nomination.py`  
**Frozen instrument commit:** `1ca9d71a824817924f25ad38856ab3f04160a1f2`  
**Result-bearing source:** `be433618f84aae9d25e8a004787d68cf774a3ee5`

## Question

The previously promoted sparse relation gate removes exact-proof work only after a candidate source/target relation pair is already supplied. That leaves pair identity as gifted discovery work.

This experiment asks whether a tiny content-derived signature can nominate useful relation pairs without an all-pairs search and without losing any relation the exact safe dispatcher would have accepted.

The writer-only instrument divides sixteen deterministic interior sample positions into four four-byte bands. Prior objects are indexed by their zero-shift band signatures. Each later object queries the same bands under the four bounded shifts already owned by ONE's exact relation proof (`-2`, `-1`, `+1`, `+2`). A matching band only **nominates** a pair. The sparse falsifier and exact safe dispatcher remain authoritative.

No reader operation or stored representation changes.

## Frozen corpus and gate

Each size row (4, 8, 16, 32, 64, 128 and 256 KiB) contains 24 objects:

- one deterministic random basis;
- three productive shifted derivatives;
- the frozen every-32-byte relation-like negative;
- nineteen generator-distinct random distractors.

The all-pairs exact safe dispatcher is the control/oracle. Its productive pair+best-shift set is discovered rather than assumed.

Advance requires at every size:

- 100% retention of all productive all-pairs pair+shift results;
- nominated pairs <=20% of the 276-pair universe;
- sampled feature bytes <=2% of logical object bytes;
- total nomination + sparse gate + exact proof elapsed <=1.05x all-pairs.

Across all seven rows, median candidate/all-pairs elapsed must be <=0.50x. The experiment was frozen before result-bearing execution.

## Exact CI evidence

- workflow run: `33968385002`;
- result-bearing job: `101312433907`;
- exact source: `be433618f84aae9d25e8a004787d68cf774a3ee5`;
- ONE semantic/hostile preflight: **PASS**;
- frozen nomination experiment: **PASS**;
- artifact: `9970172108`;
- artifact: `one-g02-relation-band-nomination-be433618f84aae9d25e8a004787d68cf774a3ee5`;
- artifact digest: `sha256:663ecb9dd3b313aeed4c104f714e3fae1f945f04cdf253f6b03c5c9090175a85`.

Artifact schema: `cmpct-one-g02-relation-band-nomination-v1`; decision: **`advance_band_nomination`**.

## Measurements

Every row had the same search-quality result:

- all-pairs universe: **276 pairs**;
- productive exact-safe-dispatch relations: **3**;
- content-nominated pairs: **4**;
- candidate fraction: **0.0144927536 = 1.45%**;
- productive relations retained: **100%**;
- productive pair+best-shift set: **exact**;
- sampled feature bytes: **1,920 B** per 24-object row;
- sparse-gate compared bytes over the four nominees: **640 B**.

| relation bytes/object | feature read fraction | all-pairs median | nomination+gate+proof median | candidate/all-pairs |
|---:|---:|---:|---:|---:|
| 4 KiB | 1.953125% | 966,966 ns | 474,732 ns | **0.490950x** |
| 8 KiB | 0.9765625% | 1,028,040 ns | 455,536 ns | **0.443111x** |
| 16 KiB | 0.48828125% | 1,118,318 ns | 455,366 ns | **0.407188x** |
| 32 KiB | 0.244140625% | 1,399,210 ns | 449,365 ns | **0.321156x** |
| 64 KiB | 0.1220703125% | 2,045,410 ns | 455,115 ns | **0.222506x** |
| 128 KiB | 0.06103515625% | 3,167,404 ns | 485,011 ns | **0.153126x** |
| 256 KiB | 0.030517578125% | 5,305,205 ns | 502,994 ns | **0.094811x** |

Cross-size median candidate/all-pairs elapsed: **0.321156x**, about **67.88% lower elapsed** than exhaustive all-pairs proof on this frozen 24-object regime.

The large-row trend is causal and expected: nomination cost is nearly flat because it samples a bounded 80 bytes/object, while exhaustive proof work grows with relation bytes. At 256 KiB the measured chain is ~90.52% lower elapsed than all-pairs.

## Interpretation

This result closes the most obvious gifted-cost objection to the sparse relation gate **within the tested regime**. Useful shifted relationships can be surfaced from content with a very small candidate set, then safely handed to the already-proven sparse gate and exact proof. The writer no longer needs the frozen experiment to hand it pair identities.

The result is also structurally compatible with ONE: the signatures are writer-only observations. Surviving relationships still compile into the same generic Law+Surprise representation; there is no relation codec or reader-side search.

## Strongest hostile review

This is not yet product-speed authority.

1. The band index is implemented in Python and measured as a research instrument. Its favorable result is strong enough to justify native/fused work, not to claim final creation throughput.
2. The frozen 24-object regime deliberately contains a small number of true shifted relatives among unrelated distractors. Adversarial signature collisions, very large object populations, tiny objects and heterogeneous sizes still need explicit candidate-explosion/resource tests.
3. The 1,920 sampled feature bytes are charged, but the experiment does not yet prove those samples have been fused into the already-required ONE source pass with zero extra memory traffic.
4. The all-pairs control is the correct no-gift oracle but intentionally expensive. Beating it does not establish superiority over a mature production resemblance index.
5. Stored bytes, decode throughput, selective access, integrity, recovery, v0.29/v0.30 and release authority remain outside this result.

## Decision and next decisive action

**ADVANCE band nomination as the current relation-discovery hypothesis.**

The next experiment must pay the exported integration debt rather than invent another signature threshold:

- gather the same band features during the fused ONE observation pass;
- bound index payload/candidate fan-out under collision-heavy and false-pattern inputs;
- implement the nomination hot path natively or otherwise remove Python dispatch from the cost claim;
- charge total source traffic, nomination/index work, sparse-gate work, exact proof, peak/retained state and elapsed time;
- compare against both the current fused observer and the mature relation/resemblance discovery evidence where semantics align.

Promotion from research instrument to encoder-discovery primitive requires preserving the exact productive set while demonstrating that the feature/index work remains a marginal-information-yield win after fusion. Do not reopen quadratic pair enumeration as the product design.
