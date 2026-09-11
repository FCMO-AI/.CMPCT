# ONE-G0.2 growable direct canonical emitter — preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`
Parent negative: `docs/one/evidence/ONE_G02_BULK_CANONICAL_EMITTER_RESULT_2026-09-05.md`

## Mission Lock / Referee

The post-segment cost-owner experiment established that prevalidated canonical emission is the dominant post-segment encode cost. The exact-sized single-buffer experiment then preserved every canonical byte and achieved a productive median of 0.779642x, but failed broad-transfer/no-regression gates: only 15/21 productive rows were <=0.90x, worst productive was 1.053195x, and worst control size-class median was 1.299110x. The universal two-pass `size -> allocate -> fill` shape is therefore retired.

This experiment isolates the remaining mechanism without reopening that implementation: preserve the baseline's single growable `bytearray` and one emission pass, but append uvarints, refs and nodes directly into that output rather than creating temporary bytes/bytearrays for every helper and node.

## Falsifiable hypothesis

The dominant useful signal in the retired bulk emitter came from eliminating many short-lived control allocations/copies, not from exact pre-sizing. A one-pass growable direct emitter should therefore preserve the control-dense gains while avoiding the unstable sizing-pass debt on simple/blob-dominated Programs.

## Hard invariants

- Existing `encode_program` bytes are the canonical authority.
- Candidate bytes and `WireStats` must be byte-for-byte / field-for-field identical on every row.
- Ordinary `decode_program -> evaluate` reconstruction must remain exact.
- Normal public candidate entrypoint performs the unchanged `Program.validate_shape()` boundary.
- Existing six-op grammar, root sort order, varint canon, limits, digest bytes and reader semantics remain unchanged.
- No format revision, no new operation, no project-version change.
- The timed comparison is prevalidated emission vs prevalidated emission; duplicate validation in the baseline is suppressed only inside the benchmark, exactly as in the accepted cost-owner methodology.
- Timing order is alternating A/B-B/A from the start.

## Frozen envelope

Use exactly the same transfer envelope as the retired bulk emitter:

- sizes: 4, 8, 16, 32, 64, 128, 256 KiB;
- productive: `shift_plus1`, `shift_plus1_damage_quarter`, `fragmented_every96`;
- controls: `fragmented_every32`, `independent_random`;
- 51 paired rounds per row;
- the 256 KiB hierarchy-required fragmented row;
- direct semantic vectors for all six ONE operations, canonical multi-root ordering and uvarint boundaries.

## Frozen promotion / retirement law

Semantic mismatch at any point => `retire_growable_direct_canonical_emitter`.

Performance promotion requires all of:

1. productive median candidate/baseline <= **0.85x**;
2. at least **18/21** productive rows <= **0.95x**;
3. every productive size-class median <= **0.95x**;
4. no productive row > **1.03x**;
5. every control size-class median <= **1.03x**.

The thresholds are deliberately broader than the retired exact-sized emitter's 0.80/0.90 aspiration because this Builder removes less work; its purpose is to establish a stable Pareto-safe mechanism, not maximize one microbenchmark headline.

If the candidate fails, preserve the result. Do not rescue it with size/corpus thresholds. If it wins only on control-dense graphs, the next question must be a mechanism-derived admission/cost model or native implementation, not benchmark-specific dispatch.

## Claim boundary

A pass would establish Python research-harness canonical-emission evidence only. It would not establish complete writer speed, arbitrary discovery cost, native throughput, authenticated selective access, recovery/portability authority or v0.29/v0.30 supremacy.