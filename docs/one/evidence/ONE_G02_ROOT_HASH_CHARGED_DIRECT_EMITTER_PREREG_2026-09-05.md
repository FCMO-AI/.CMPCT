# ONE-G0.2 root-hash-charged direct-emitter writer — preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`

## Mission Lock

The exact-head end-to-end relation-to-wire experiment advanced direct canonical writing at a 0.798386x productive median while preserving byte-identical ONE0. That A/B intentionally began after root identities were available.

Before escalating to a broader fused-observation/native-writer campaign, test one unavoidable missing cost explicitly: **compute SHA-256 identities for both the previous and current version inside each timed writer call**, then run the otherwise identical admission -> native segmentation -> bounded Program -> validation -> canonical-emission path.

This is a dilution falsifier, not a new optimization. It asks whether the direct-write gain is still material after charging root identity hashing, especially on simple exact-shift rows where hashing can become a large fraction of total work.

## Baseline / candidate

Identical to `ONE_G02_END_TO_END_DIRECT_EMITTER_WRITER_PREREG_2026-09-05.md` except both timed arms first compute:

- `sha256(previous)`;
- `sha256(current)`.

Those computed digests are then used as the actual Program root identities. No precomputed digest is reused inside the timed call.

Baseline emits via ordinary canonical helpers after one common shape-validation charge. Candidate uses the byte-identical growable direct emitter. Admission, segmentation, Program construction, reader semantics and wire bytes are identical.

## Falsifiable hypothesis

If direct emission removes enough real writer work to matter beyond its own serialization microboundary, the gain should remain visible after two full version hashes are added to every timed call.

## Frozen envelope

Reuse exactly:

- sizes 4, 8, 16, 32, 64, 128, 256 KiB;
- productive cases: `shift_plus1`, `shift_plus1_damage_quarter`, `fragmented_every96`;
- controls: `fragmented_every32`, `independent_random`;
- 31 alternating A/B-B/A repetitions;
- native one-pass segmentation and independent Python segmentation oracle;
- ordinary decoder/reference evaluator as byte-exact oracle.

## Frozen decision law

Advance only if all semantic/oracle gates remain exact and:

- productive median candidate/baseline <= **0.95x**;
- at least **18/21** productive rows <= **1.00x**;
- every productive size-class median <= **1.03x**;
- worst individual productive row <= **1.10x**;
- every control size-class median <= **1.05x**.

Hold if semantics are exact but any performance law fails. Invalidate on any wire/root/oracle mismatch.

## Cost honesty / claim boundary

This benchmark adds root hashing but still does **not** charge the promoted/future fused Gear observation path, arbitrary object-pair discovery, authenticated index/container placement, recovery/durability, filesystem metadata work or product-native integration. Passing it therefore means only that the direct-write gain survives one more unavoidable ingest cost.

Do not call this “full ingest”. The next broader experiment must actually include the fused observation/authentication/placement costs it claims to measure.
