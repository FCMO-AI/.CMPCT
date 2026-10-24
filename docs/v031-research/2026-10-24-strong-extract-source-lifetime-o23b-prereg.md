# O23b preregistration — cross representation against the 2 MiB cache boundary

Date: 2026-10-24 UTC
Status: SECONDARY PREDICTION, committed **after** initial O23 success and **before** any O23b implementation or hosted observation.
Inherited scientific evidence: O23 PR #376 / run 40125737167 / head 962a86ef938745f4a4da6e42b96319d101f138e8 / artifact 12572856738. Original narrow result: same-handle 128-byte S_PACK yielded ORIGINAL_VERIFIED with cached owner [0]; same-handle 4-MiB direct RAW yielded MUTATED_UNVERIFIED with no cached owner. Both controls retained original index/SHA, repaired CRC, same inode/size, fresh SHA rejection and exact pristine extraction.

## New causal question

Was this contrast caused by PACK-vs-RAW representation or by the inherited **decoded owner <=2 MiB cache policy**, which was confounded with representation and size in O23?

## Prospective crossed prediction

Keep all O23 tests unchanged and add two new cases with the same independently constructed revision-24 fixture, the same same-inode post-verify mutation, and the same validation obligations:

- **128-byte direct RAW**: small direct owner should be cached by `verify()`, so same-handle `extractall()` should publish original verified bytes despite subsequently CRC-repaired source mutation.
- **4-MiB S_PACK**: large shared physical owner should not be cached; after verification, mutate the stored record on the same inode and retain original physical SHA. Subsequent same-handle `extractall()` should publish the modified physical bytes.

Thus the four-cell prediction is that cache size, not S_PACK/S_BLOB label, determines the outcome for this scoped Reader implementation:

| Valid fixture | 128 B (cached) | 4 MiB (not cached) |
|---|---|---|
| Direct RAW | ORIGINAL_VERIFIED | MUTATED_UNVERIFIED |
| S_PACK | ORIGINAL_VERIFIED | MUTATED_UNVERIFIED |

The S_PACK 4-MiB fixture is a valid independently assembled revision-24 Reader image, **not** an assertion that the canonical Builder would choose a 4-MiB micro-PACK. This differentiates parser/read contract from Builder admission.

## Adversarial controls and disproof

Both new cells must retain the preregistered original-plus-mutant full-archive SHA comparison, unchanged authenticated index and physical SHA, repaired CRC, unchanged source st_dev/st_ino/st_size, valid preflight, pristine positive `verify(); extractall()` and fresh-reader SHA rejection caused specifically by physical hash inconsistency. Any unexpected behavior in either new cell falsifies/narrows the cache-size explanation rather than being fixed by threshold tuning or excluding a case. A scientific validator failure or provenance failure is **INVALID** rather than an explanatory result. Keep original O23 run and artifact immutable.

## Opportunity and boundaries

This is the cheapest structural perturbation that separates the confounded factors in O23; no product fix, new format/codec, shifted release criterion or external corpus is justified. Four synthetic fixtures are still not a general mutable-source security guarantee. Even if the cache threshold predicts all four, extraction is not a transaction and must be described only under the local source-modifier trust model. Do not change cache size to make the prediction true.

## Persistent evidence plan

Add two fixture calls and result assertions only after this preregistration is committed; rerun the exact-head GitHub court, preserve raw JSON/host/source SHA and classify O23b separately. Update the result document with both the initial O23 and crossed O23b, citing actual run IDs without replacing the first observation. Do not modify the product owner, test criteria or source-fingerprint checker.
