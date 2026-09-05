# ONE-G0.2 post-segment control cost owner — terminal result

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`
Frozen authority: `docs/one/evidence/ONE_G02_POST_SEGMENT_CONTROL_COST_OWNER_PREREG_2026-09-05.md`

## Exact CI receipt

- branch source: `0af3e306252810a8e4c61c502557e0719cfdcbd3`
- pull-request merge test SHA: `f8bb8a65737b7b3352f1df5d94fa20f3dc51f5b3`
- workflow run: `33991674157`
- job: `101374903105` (`post-segment-control-cost-owner`)
- conclusion: **success**
- artifact: `9976832534`
- artifact ZIP SHA-256: `013895493f3b1fc45f5c4293b117273e4dc609cc85388704a708cd0b49ccc57b`
- ONE semantic/hostile tests: **84 passed**
- frozen decision: **`advance_bulk_canonical_emitter`**

## Result

After relation/segment discovery was removed from the timed region, canonical `Program` encoding dominated graph construction on every one of the 21 productive relation rows and every one of the seven tested size classes.

Aggregate ownership:

- median canonical-encode share of post-segment time: **0.7166622209788754**;
- median Program-graph construction share: **0.2833377790211246**.

Inside the canonical-encode boundary, the hostile-review split between validation and byte emission was decisive:

- median prevalidated canonical-emission share: **0.7854046845044594**;
- median validation share: **0.21459531549554056**;
- emission was the majority owner on **21/21** productive rows and **7/7** size classes.

The 256 KiB hierarchy-required `fragmented_every96` row made the cost shape concrete:

- graph construction: **6,289,578 ns**;
- full canonical encode: **12,987,096 ns**;
- prevalidated canonical byte emission: **9,989,326 ns**;
- validation: **2,905,218 ns**;
- canonical wire: **297,504 B**;
- Surprise: **264,876 B**;
- Program nodes: **2,736**;
- concat references: **5,466** total, maximum **4,096** in one concat;
- hierarchy depth: **2**;
- transient native segment-plan model carried forward from prior evidence: **5,464 segments / 65,568 B**.

## Causal interpretation

The remaining Python post-segment writer bill is not primarily the already-repaired segmentation scan and is not primarily validation. Canonical byte emission is the stable measured owner in this envelope. The encoder repeatedly creates and copies many small temporary bytearrays/bytes for uvarints, refs and node encodings before appending them into the final output.

This result does **not** authorize weakening validation. Validation remains a separate measured safety cost and must be preserved. It authorizes experiments that reduce emission allocation/copy work while producing exactly the same ONE0 bytes.

The subsequent exact-sized single-buffer experiment and growable-direct experiment are governed by their own preregistrations/results and may falsify particular implementations without invalidating this ownership result.

## Claim boundary

Python research-harness post-segment attribution only. It does not establish native/product writer throughput, arbitrary discovery cost, stored-byte superiority, authenticated selective access, recovery/portability authority or v0.29/v0.30 supremacy.