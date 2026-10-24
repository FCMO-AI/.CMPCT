# O15b — authenticated index order independence, pre-result preregistration

Date: 2026-10-24 UTC. **Prediction, not a result.**

The first O15 public-C inode-tree court succeeded on original source `8a3d8c33e111ddb2490626a6f54c6eb6b8801b1d`, hosted [Actions 40094327272](https://github.com/FCMO-AI/.CMPCT/actions/runs/40094327272) with 128 verified batched members and correct source inode partitions across a/b variants. However, Builder naturally places ordinary owners before the aliases in these two trees, making the consumer's claim of order-independence incompletely challenged.

## New narrow question
Does the *same* public-C client still faithfully reconstruct real POSIX inodes and symlinks when **a signed valid r24 index lists an alias before its terminal regular owner**, without changing any logical bytes, names, storage refs or physical blobs?

## Cheap independent perturbation
Reuse the fully source-validated O15 a-owner archive; independently reauthenticate the fixed physical data with the O14 `rebuild` helper, which reconstructs both header and footer compressed-index fields and SHA-256 after swapping exactly the two complete member tuples `a.bin` and `y_alias.bin`. Verify (1) modified archive SHA differs, (2) alias ordinal < owner ordinal in signed parsed index, (3) unchanged physical record bytes and all logical entries, (4) extract via unchanged public-C O15 binary into a fresh private root and independently compare every actual regular SHA-256, symlink target, *inode equivalence classes*, and batch_count > 0 to the unchanged original source tree.

## Hypothesis and simpler control
The terminal owner ordinal is an index-backed graph relation, not a publication-order directive. A byte-copy alias control is insufficient: it would pass file SHA-256 but fail inode equality. If Rust graph resolution, PACK owner grouping or C publication implicitly assumes owner index precedes alias, the experiment will fail on same-source input.

## Disproof / kill condition
Any native open rejection, misidentified owner ordinal, missing/degraded batch grouping, byte/namespace or inode graph mismatch, or physical-record/hash/provenance drift falsifies this specific order-independence claim. Never change source tree or evaluator to rescue the test. This is research evidence only: no product or release credit.

No implementation edit to Rust, Builder, Reader, Writer, codec, on-disk format or release gates. The new adversarial index remains valid only within the explicit signed revision-24 test; do not generalize to arbitrary malicious on-disk index attacks from this one perturbation.