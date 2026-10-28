# Mosaic v0.29 — One-Hop Reference Context Frames (contingency)

Status: **detached preregistration only / run only if the stored shared-dictionary oracle REJECTs / no format implementation**.

## Motivation

A small stored trained dictionary may fail because the hostile direct/root records are individually large:
Zstandard dictionaries mainly replace missing history near frame starts. A much stronger context source is
an already stored *similar sibling record* whose exact byte sequences can act as raw-content dictionary
history without adding dictionary payload bytes.

This mechanism is deliberately more expensive in random-access materialization, so its dependency and
locality rules are frozen before any project measurement.

## Representation hypothesis

A target physical direct/root record may be compressed with zstd using at most the final **128 KiB** of
one other independently stored direct/root record as raw-content dictionary context.

The context record remains an ordinary attempt-5 record and is decoded first. The target frame remains a
separate frame and keeps its exact existing logical bytes. No record boundary is merged.

## Bounded candidate discovery

1. Build one `similarity_sketch()` per direct/root physical record.
2. Use the existing `lsh_candidates(..., max_candidates=8)` bounded discovery; no all-pairs fallback.
3. For each candidate edge, compress the target with the candidate context's final <=128 KiB and measure
   exact payload bytes at the same zstd level used by the current direct/root record path.
4. Keep only positive edges after a **32 B per-target transition charge**.
5. Feed `(target_record, context_record, measured_saving)` edges to the existing
   `choose_central_bases()` depth-1 selector.

`choose_central_bases()` makes context anchors and encoded targets disjoint: a record assigned as a target
cannot later become a context anchor, preventing physical context-on-context chains.

## Additional anti-chain rule

A physical record is ineligible as a context-coded **target** if any direct logical node inside that
record is already referenced as a base by an attempt-5 `delta`, `delta_pack`, `mosaic`, or `pack_mosaic`
node. This prevents a logical delta from becoming an implicit two-hop transform through a context-coded
base record.

Context anchors themselves may contain logical base nodes because they remain ordinary independently
decodable records.

## Locality accounting

For a cold request of a direct member in a context-coded target record, materialization includes:

- the full decoded context record;
- the full decoded target physical record; and
- no assumed warm cache credit.

A context-coded assignment is admissible only if **every direct member** of the target physical record
remains <= **8x** total materialization and the context record alone contributes <= **4x** the requested
member's logical bytes.

The ordinary target and context frames retain their existing physical authentication. A future format
would additionally authenticate the context record id and context slice bounds in metadata before zstd
decode.

## Frozen gate

The one-hop reference-context mechanism survives only if the hostile aggregate shows all of:

- >= **128 KiB exact net payload saving** after 32 B/target transition charges;
- >= **8** context-coded target records;
- exact dictionary decompression round-trip for every selected target;
- no context-coded target is a context anchor;
- no context-coded target contains a logical base node;
- context slice <= **128 KiB**;
- total cold direct-member materialization <= **8x**; and
- context-only materialization <= **4x** per direct member.

The attempt-5 archive remains the emitted artifact. A PASS authorizes an implementation experiment only.

## Disproof and next move

Reject if the frozen size/locality gate misses. Do not increase context depth, expand to all-pairs search,
or allow context-coded logical bases after seeing the result.

If both stored global dictionary and one-hop reference context fail, cross-record compression history is
not the missing structural byte pool under acceptable locality. The campaign should then move away from
zstd context and inspect large-payload representation choices (for example transform-aware pack classes
or a different bounded backend) rather than tuning record metadata or residual programs again.
