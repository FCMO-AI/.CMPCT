# ONE-G0.2 bounded Surprise pooling — fan-in hostile review

Date: 2026-09-08
Scope: research/cmpct1, ONE-G0.2

## Mission lock

Bounded Surprise pooling may advance only if it preserves the generic ONE Law + Surprise grammar and remains representable under the reader's existing hard resource envelope. Bounding Program node count alone is not sufficient if one retained node can contain an oversized control vector.

## Falsifiable hypothesis

For every pooled Program admitted by the research compiler, canonical encoding and decoding must agree on validity under the same declared `Limits`. In particular, no emitted concat may carry more references than the wire reader accepts (`limits.max_nodes`), even when the discovered plan fragments at byte granularity.

Disproof case: a target whose already-discovered plan alternates one-byte `ref` and one-byte `surprise` pieces. With default limits, an 8 KiB target fits inside one output-local pool group but contains 8,192 plan pieces, exceeding the reader's 4,096-reference per-node cap.

## Negative result found before promotion

The pre-review pooling compiler bounded `len(program.nodes)` but did not bound `len(concat.refs)`. `Program.validate_shape()` likewise has no per-node ref-count check, while `wire.decode_program()` explicitly rejects concat/xor/add8 reference counts above the encoded `max_nodes` limit.

Therefore a sufficiently fine fragmented plan could be accepted by the in-memory compiler and encoder yet rejected by the canonical wire reader. The existing `fragmented_every96` benchmark did not expose this because its per-group fan-in stayed well below the reader cap.

This invalidates any broad claim that the original pooling geometry alone established complete hard-resource validity.

## Builder correction

The compiler now treats over-fan-in as a selective-Crystallization boundary:

- ordinary groups continue to pool Surprise bytes and ranged refs with no density change;
- if one group's discovered piece count exceeds the reader's existing reference envelope, that output-local group is stored as explicit Surprise;
- no new opcode, legacy codec, reader discovery, fallback decoder, or reader-visible mechanism is introduced;
- the existing node geometry remains conservative because one crystallized group consumes fewer nodes than the former pool+concat worst case.

New stats expose `crystallized_groups`, `crystallized_bytes`, and `max_group_refs` so later density/resource evidence cannot hide this fallback.

## Hostile regression

`tests/one/test_bounded_surprise_pool.py` now includes an 8 KiB every-byte alternating plan. It requires:

- the discovered group fan-in to exceed the 4,096 reference cap;
- at least one selective Crystallization event;
- every emitted node to remain within the reader reference envelope;
- canonical encode/decode round-trip;
- exact reconstruction of both roots.

The geometry test also computes expected grouping with independent arithmetic rather than using `pool_geometry()` as its own oracle.

The bounded-pooling benchmark now carries the same fine-fragment control as a strengthened hostile gate and reports crystallization/fan-in explicitly. Frozen productive rows still require unchanged Surprise payload; the new density sacrifice is permitted only for the over-fan-in hostile condition that was previously not representable by the reader.

## Claim boundary

This correction is representation/resource hardening, not a size or speed win. It earns no v0.29/v0.30 comparator point. It does not establish optimal Crystallization policy: the current trigger is the existing wire safety boundary, not an information-yield optimum. A later writer should consider crystallizing earlier when control bytes or dispatch work cost more than the Law/reuse they preserve.

## Next falsifier

The next useful question is economic rather than merely safe: for increasingly fragmented groups below the hard 4,096-ref ceiling, measure control bytes + reader dispatch work against the bytes saved by retained reuse. The optimal ONE policy should Crystallize when marginal Law value becomes negative, before hitting a hard reader limit.