# CMPCT v0.30 Lattice campaign

Status: exploratory breakthrough campaign. This document does **not** declare v0.30 released.

## Mission Lock

### Requested outcome

Continue the Opus-5/Mosaic direction under the repository's breakthrough-rehabilitation doctrine and do not consume a numeric release until a material, reproducible CMPCT improvement survives the promotion gate.

### Observed frontier

Accepted v0.29 attempt #5 improves the exact v0.28 portable frontier by 48,601 bytes across 15 inherited workloads, with 2 improvements and 13 exact fallbacks. The newly measured exact-tree category frontier also exposes an important weakness: current CMPCT still loses stored bytes to solid tar+Zstd-19 on several categories, especially ML artifacts and some resemblance-hostile cases.

The dominant representation tension is no longer simply "find more resemblance." Two specific costs remain visible:

1. the inherited root-pack planner stops at 2 MiB even when larger members could safely tolerate a wider bounded context under the existing <=8x read-amplification law;
2. general-purpose Zstd sees interleaved byte lanes as one stream, so fixed-width numeric-like data can hide low-entropy high-order lanes behind high-entropy low-order bytes.

### Invariants

- byte-exact losslessness;
- authenticated physical records and logical SHA-256 identity;
- maximum dependency depth remains <=1;
- maximum logical physical decode unit remains <=8 MiB;
- any newly widened pack must keep **every directly addressable logical member** at <=8x decoded-bytes/logical-bytes amplification, not merely pass a weighted average;
- no transform is selected from an extension or private corpus identity;
- transform admission is determined by complete stored-byte cost;
- accepted v0.29 remains an exact workload-level fallback during exploration;
- canonical revision-24 grammar remains unchanged unless a later promotion explicitly earns a new on-disk revision.

## Hypothesis: Lattice Packing

Lattice is a post-graph physical compiler. It does not change Mosaic candidate discovery or logical resemblance assignments.

### Primitive A — measured byte-lane transform

For eligible direct logical members, audition reversible byte-lane transposition at bounded widths (initially 2/4/8/16 bytes). For width `w`, bytes are laid out lane-major: all byte-0 positions, then byte-1 positions, and so on, with a bounded tail copied verbatim.

This is a generic lossless transform. It is related to mature shuffle / byte-stream-split ideas used in scientific and columnar storage, but CMPCT admission remains content-driven: the transform is kept only when the final physical representation is smaller after descriptor charge.

### Primitive B — elasticity under the *existing* locality law

The current research planner auditions root packs only through 2 MiB. Lattice may fuse eligible pure-direct physical groups up to the existing 8 MiB physical decode ceiling, but only if the resulting group obeys <=8x amplification for **every** member.

This changes the model from "2 MiB is the locality boundary" to "8x amplification and the 8 MiB decode ceiling are the locality boundary." A 5 MiB group containing multi-megabyte objects can be legal even though a 5 MiB group containing a 4 KiB object is not.

### Primitive C — complete-cost greedy fusion

Start from authenticated v0.29 physical records. Only records whose payload slices are owned exclusively by direct nodes are eligible in the first oracle. Every candidate fusion pays:

- one complete replacement physical record;
- transform descriptor charge;
- all unchanged archive metadata/framing assumptions conservatively;
- the exact baseline physical bytes of every source record it replaces.

A fusion is admitted only when it reduces that local complete physical cost and satisfies the locality bounds. This makes any aggregate gain a sum of independently non-regressive local replacements rather than an average that can hide a losing group.

## Competing solution classes considered

1. **Turn Zstd level up / use a stronger generic codec.** Rejected as the primary idea. It exports creation CPU and does not explain why current bounded context loses to solid compression.
2. **Another global trained dictionary.** Already measured in v0.29: the detached shared-dictionary oracle saved only about 6.3 KiB after charges, far below its frozen gate.
3. **Larger fixed solid packs.** Rejected. A global 4/8 MiB pack size repeats the historical fixed-frame mistake and can destroy small-file locality.
4. **Lattice: member-safe elastic packs plus measured reversible lane transforms.** Retained because it attacks both remaining context fragmentation and a generic entropy-layout defect while keeping the reader rule explicit and bounded.
5. **Zstd prefix/diff graph edges.** Retained as a second independent v0.30 hypothesis. Official Zstd supports raw-content prefix/dictionary compression that behaves like a fast diff. It will be auditioned only after Lattice's causal ceiling is measured so two mechanisms are not conflated.

## Disproof tests

Lattice is rejected as a breakthrough seed if any of the following occurs on the fixed public frontier:

- no workload saves at least 64 KiB versus accepted v0.29 after conservative charges;
- the 15-workload aggregate saving is <128 KiB;
- any admitted group violates the <=8x per-member amplification bound or 8 MiB decode-unit bound;
- the gain depends on extension-specific admission rather than measured bytes;
- exact inverse-transform checks fail;
- the gain disappears when the candidate is computed from the accepted attempt-5 archive rather than from a detached approximation.

A seed that passes the size/mechanism disproof test may still carry creation-time debt. Under `docs/BREAKTHROUGH_REHABILITATION.md`, that debt must remain visible and be repaired before numeric promotion.

## Initial evidence before repository execution

A local reconstruction of the deterministic public ML generator produced the expected 18,172,774 logical bytes. On its `scales.npy`, byte-lane width 2 reduced a Zstd-19 payload from roughly 940.7 KiB to 833.6 KiB (about 107 KiB). Packing transformed scales with the tokenizer and training log reduced their combined independent Zstd payload by about another 91 KiB. The resulting raw group is about 5.59 MiB, so its cold-read amplification is approximately 4.7x for scales, 2.0x for tokenizer data and 3.5x for the training log—inside the inherited 8x law.

These numbers are **hypothesis-generation evidence only**. They are not a CMPCT claim because they do not include accepted attempt-5 framing, record ownership, exact archive metadata or the CI toolchain. The first committed oracle must reproduce or falsify the mechanism against real v0.29 artifacts.

## Evidence ladder

1. detached accepted-archive oracle on all 15 public workloads;
2. exact Lattice archive emitter/reader with independent inverse-transform vectors;
3. hostile malformed-descriptor/resource tests;
4. full generalization matrix with accepted v0.29 exact fallback;
5. creation/extraction/selective-read/memory accounting;
6. direct-base release gate and durable public benchmark record only if all promotion debt closes.

## Promotion boundary

Do **not** call this v0.30.0 until the repository contains a material complete-artifact gain, accepted v0.29 is not regressed per release contract, timing debt is closed, and the normal release/version/evidence gates pass unchanged.

Footnote: the campaign deliberately preserves a second hypothesis—bounded Zstd prefix/diff edges—because Lattice and reference compression attack different costs. If Lattice is real but insufficient, the correct next move is a counter-invention, not tuning the Lattice gain back out.
