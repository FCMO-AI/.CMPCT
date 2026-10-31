# J24G96b — Preregistered late alternative: reuse existing digest slot

**Freeze:** 2026-10-31 UTC, after J24G96 additive-chain source and local O0 result; this is a **new prospectively frozen subexperiment**, not part of the original preregistration. Base for this hypothesis: J24G96 candidate branch `75b914d440a763a88c7c65f722c6af61d13a1972`; released main remains `80c358f8824ec1b20d349c92ed94c898090969b0` / revision 24. No production source, format or release modification.

## Question and stronger simpler control

The first candidate *adds* 32 bytes of cumulative digest per footer. Is the extra metadata **unnecessary**, given that the current revision-24 footer already dedicates an existing 32-byte field to SHA-256 of decompressed payload? A **different future grammar** could repurpose that same slot to authenticate the entire parent-linked chain and payload together:

`H_i = SHA256(domain-v2 || H_parent || LE64(physical_footer_position) || original_36_byte_footer_header || decompressed_payload)`.

A future Reader recomputes that digest on actual payload bytes and checks the stored 32-byte slot. A separately trusted 32-byte latest head remains mandatory to resist an actor who can rewrite and rehash the complete unkeyed archive. This reduces hypothetical additional *archive* bytes to **zero**, not security/trust complexity to zero.

## Experiment and disproof

Use exactly the original eight SHA-attested physical r24 archives from J24G96. First verify their original SHA/footer chain with the original research parser. In a **private in-memory variant**, overwrite only existing 32-byte footer digest slots, oldest to newest, with v2 chained hashes; preserve exact file length and every non-digest byte. An independent v2 test decoder must reproduce every slot digest and the final trusted external root. After one/two predecessor rewires, it must fail against the original fixed trust root. A modified archive plus recomputed local v2 digest may pass local validation, but must fail original externally trusted head. Corrupt decompressed payload or footer-header metadata must fail. The archived r24 Reader cannot read this hypothetical variant; **compatibility with revision 24 is not claimed**. No changes to original ZIPs or baselines.

## Controls, bounds, costs

- Original r24 archived bytes and original payload validation remain controls; do not overwrite their evidence.
- The competing +32B/footer model is the strongest additive control. The whole-file SHA streaming midstate from the posthoc J24G96 analysis is stronger in byte coverage and may make both footer-only mechanisms economically unattractive.
- Report exactly 0 **additional** archive bytes, unchanged file size, +32B latest separately trusted head, and at least one payload-hashing operation per footer. This is not a CPU speedup or product performance receipt.
- Maintain a source SHA, deterministic eight-case receipt, negative cases, independent referee when possible. Kill if any genuine history fails, any forged history accepted under original trusted head, original file length increases, or the new semantic proof needs uncharged bytes.
- Future format implementation would require new revision, backward-reader discrimination, bootstrap/old-version compatibility, recovery, external authority and atomic trust-head publication, on-disk crash hardening, full physical blob verification and all product gates.

**Decision:** if eight valid histories and all hostile controls pass, retire the **necessity** of +32B/footer metadata as an information bound while retaining both schemes as non-shipping research; prefer stronger trusted whole-file SHA where feasible. If not, preserve negative and no future-format claim.

**Scientific level:** O0 hypothetical format-recoding, no source/product integration. Pre-implementation prediction distinct from the already observed J24G96 O0 results; no discovery-policy change.
