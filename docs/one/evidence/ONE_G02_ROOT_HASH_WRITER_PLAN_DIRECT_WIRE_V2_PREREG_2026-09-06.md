# ONE-G0.2 root-hash writer plan-direct wire v2 preregistration — 2026-09-06

## Mission lock

The first plan-direct writer candidate at exact source `9083603dff3cb311340b3c56429e0165cc2ec34e` is permanently invalidated as submitted: it failed byte-identical canonical semantics on `fragmented_every96` at 256 KiB even though its emitted Program decoded/evaluated exactly.

The independent diagnostic lane (`12b67d6d64fec3e2a913e6e2c61e236f7f78f26e`, run `34043042180`) localized a single deterministic defect. In a hierarchy deeper than one concat level, the v1 candidate reused the known reconstructed span as the serialized `Ref.length` for references to intermediate concat nodes. The canonical Program uses `Ref(node)` there, i.e. `length=None`, while retaining the span only as creator-side knowledge used to compute the parent declared length. This produced four extra control bytes in the first failing 256 KiB fragmented row. Plan, node count, hierarchy depth, reconstruction and root semantics otherwise matched.

V2 tests one causal repair only: **separate serialized reference length from creator-only known span in hierarchy bookkeeping**. No benchmark threshold, matrix, reader behavior, Law, admission policy, segmentation policy, root digest, or canonical wire rule may change.

## Falsifiable hypothesis

If Python `Program`/`Node`/`Ref` materialization is a material writer cost and the v1 failure was only the hierarchy bookkeeping defect above, then a corrected direct-plan serializer will emit byte-identical canonical ONE0 bytes on every frozen row and still achieve the original preregistered speed gates.

## Disproof

Reject/invalidate V2 if any row differs in canonical bytes/stats, admission, native plan, oracle, relation traffic, segments, hierarchy depth, node count, decode/evaluate output, or malformed-plan rejection. If semantics pass but the original performance gates fail, reject it as a speed path. Do not tune thresholds after results.

## Frozen matrix and gates

Inherit the v1 frozen harness unchanged:

- sizes: 4/8/16/32/64/128/256 KiB;
- productive and control cases from the authoritative root-hash direct-emitter writer;
- 31 paired rounds with alternating A/B–B/A order;
- mature productive median `<= 0.85x`;
- at least 12 mature productive rows `<= 0.90x`;
- no mature productive row `> 1.03x`;
- mature control median `<= 1.03x`;
- no mature control row `> 1.08x`;
- full `tests/one` green;
- byte-identical canonical wire and exact reconstruction on every row.

## Builder constraint

The V2 harness may reuse the frozen v1 measurement/audit machinery, but the candidate emitter is independent. Hierarchy entries carry four creator-side fields `(node, start, serialized_ref_length, known_span)`. Only the first three are serialized. Intermediate concat references must set `serialized_ref_length=None` while retaining `known_span=declared_length` for parent arithmetic.

## Decision

- semantic mismatch: `invalidate_plan_direct_wire_writer_v2`;
- semantics exact but speed gates fail: `reject_plan_direct_wire_writer_v2`;
- all gates pass: `advance_plan_direct_wire_writer_v2` for the same bounded writer-compiler claim only.

No result here changes the v0.29/v0.30 comparator freeze or claims CMPCT1 supremacy.
