# ONE-G0.2 bounded hierarchical concat — terminal result

Date: 2026-09-05
Experimental line: ONE-G0.2

## Exact CI receipt

Frozen authority: `docs/one/evidence/ONE_G02_BOUNDED_HIERARCHICAL_CONCAT_PREREG_2026-09-05.md`.

- branch source: `80ceab5cbffb5294938c0947159f867962ab96f7`
- workflow run: `33982125348`
- job: `101349099752` (`bounded-hierarchical-concat`)
- conclusion: **success**
- artifact: `9974076803`
- artifact name source: `one-g02-bounded-hierarchical-concat-19a873683f53473eb56e82c9861aeb7876bfecd2`
- artifact SHA-256: `0fe07ebd8535309bab61f00de74bbe5162c66b068f27deedbbdeaba64d81f9b2`
- artifact metadata binds the run head to `80ceab5cbffb5294938c0947159f867962ab96f7`
- ONE semantic/hostile tests: **83 passed**
- decision: **advance_bounded_hierarchical_concat**

## Result

Every frozen row reconstructed the previous and current roots byte-exactly after hierarchical encode -> bounded decode -> evaluate. Surprise bytes were unchanged, no operation outside the existing six-op ONE grammar appeared, and rows already legal as one flat concat retained byte-identical wire form.

The decisive hostile case was 256 KiB `fragmented_every96`:

- ideal flat concat references: **5,463**
- declared per-concat hard cap: **4,096**
- flat bounded decode: **rejected**, as required by the falsifier
- hierarchical depth: **2**
- hierarchical program nodes: **2,737**
- maximum concat fanout: **4,096**
- flat ideal wire bytes: **297,483 B**
- bounded hierarchical wire bytes: **297,504 B**
- added wire: **21 B** = **0.007059%**
- Surprise bytes: **264,876 B** in both forms
- ideal flat reference-VM work: **1,837,740 B**
- hierarchical reference-VM work: **2,362,028 B** = **1.285287x**
- hierarchical reference-VM materialized bytes: **789,164 B**

All other frozen rows required no hierarchy and therefore incurred zero wire overhead.

## Causal interpretation

The resource-semantic failure is not a reason to add a shift opcode or raise a reader cap. Existing generic concat can express the relation within the declared bound with effectively negligible storage overhead. The remaining tax is reader execution: the reference VM materializes the intermediate concat, adding about one extra large reconstruction cone on the only hierarchy-required row.

That makes **generic concat Law fusion** the next causal owner. The format has already paid only 21 bytes; changing the representation again would optimize the wrong layer.

## Claim boundary

This establishes bounded representation for the tested fragmented adjacent relation only. It does not establish arbitrary pair discovery, writer admission cost, native writer speed, authenticated selective reads, or superiority over frozen v0.29/deferred-v0.30.
