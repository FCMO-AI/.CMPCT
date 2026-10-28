# v0.30 r24 micro-pack extension-bucket ablation — 2026-09-12

Status: **research evidence; no release credit**

Exact measured head: `37d51d9030aa893c89949c4c53adfa748c810e3f`
Hosted run: `34737525832`
Receipt artifact: `v030-micropack-ext-ablation-extension-value-delta9969-losses1-wins1-37d51d9030aa893c89949c4c53adfa748c810e3f`
Scientific verdict: `EXTENSION_BUCKET_HAS_MEASURED_ECONOMIC_VALUE`

## Question

Does the current extension-specific bucket partition itself buy stored bytes, or can the same already-eligible candidates simply be merged in one path-blind size-ordered stream under the unchanged 8x smallest-member law?

This ablation removed only the bucket key. Eligibility remained the existing mature text-extension gate; size order, locality law, codec path and membership-v1 representation stayed fixed.

## Result

No invariant failures were observed. Path-blind minus extension-bucket stored-byte deltas were:

- origin Developer: **+10,954 B** (path-blind worse)
- origin Tiny Files: **0 B**
- hostile balanced structured text: **0 B**
- hostile skewed structured text: **0 B**
- hostile incompressible text-labeled: **0 B**
- hostile duplicate forest: **0 B**
- hostile singleton buckets: **-985 B** (path-blind better)

Aggregate path-blind delta: **+9,969 B**.

## Interpretation

The experiment rejects the simple claim that extension buckets are pure historical baggage: on Developer, separating families prevents a real 10,954-byte loss. But it does **not** promote filenames/extensions as product policy. It demonstrates that some notion of content family has economic value and creates a cleaner next question: can that separation be recovered from the bytes themselves at low cost?

The next referee therefore must not sweep extension replacements. It should use path-blind content evidence and exact economics, with no corpus/path/extension identity, while preserving the same 8x physical law and same-grammar complete-artifact comparison.
