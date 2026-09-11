# ONE-G0.2 generic concat Law fusion — terminal result

Date: 2026-09-05
Experimental line: ONE-G0.2

## Exact CI receipt

Frozen authority: `docs/one/evidence/ONE_G02_GENERIC_CONCAT_LAW_FUSION_PREREG_2026-09-05.md`.

- branch source: `36c1a0fcc7212cb47c708824753a8adae0e19a72`
- pull-request merge test SHA: `5c3649c4d1c2d6a275ba457a647ce312e314ee16`
- workflow run: `33982517600`
- job: `101350156417` (`generic-concat-law-fusion`)
- conclusion: **success**
- artifact: `9974187447`
- artifact SHA-256: `487cbd7adfe76554b2b6fb6afb4059bbd154acf1a18871cf64bdadc803ab6b3a`
- ONE semantic/hostile tests: **83 passed**
- decision: **advance_generic_concat_law_fusion**

## Result

Every frozen row reconstructed byte-exactly, left the encoded Program byte-for-byte unchanged, obeyed the declared work/depth limits, and retained the existing six-op ONE grammar.

The decisive hierarchy-required witness remained 256 KiB `fragmented_every96`:

- stored wire bytes: **297,504 B** (unchanged)
- Surprise bytes: **264,876 B** (unchanged)
- ordinary hierarchical range work: **786,432 B**
- fused range work: **524,288 B**
- ordinary hierarchical materialization: **786,432 B**
- fused materialization: **524,288 B**
- fused / hierarchical work: **0.666667x**
- fused / hierarchical materialization: **0.666667x**
- fused result equals the ideal flat-graph accounting exactly
- fused traversal maximum depth: **3**
- fused nodes touched: **2,736**

Rows that did not require hierarchy retained exactly the same modeled work and materialization as the ordinary range evaluator.

## Causal interpretation

The 4,096-reference hard cap can be preserved without exporting a reconstruction-work tax. Nested concat is associative for execution: a bounded reader may traverse nested concat nodes as one reconstruction cone and materialize only the requested outer concat result, while still validating the stored graph and all resource limits.

The representation therefore does not need a shift-specific opcode, a raised fanout cap, or a special fragmented-relation reader. The remaining task is implementation consolidation: move the proven fusion rule into the generic range evaluator itself and pin it with independent tests, rather than leaving the result only in a benchmark-local evaluator.

## Claim boundary

This is modeled reference execution evidence, not native decoder throughput authority. It does not establish authenticated selective reads, arbitrary pair discovery, writer speed, or superiority over frozen v0.29/deferred-v0.30.
