# ONE-G0.2 trusted-prior chain lifecycle — preregistration

Date: 2026-09-10  
Experimental version: **ONE-G0.2**

## Mission lock

The already-promoted trusted-prior-root experiment proves that one adjacent-version writer call can reuse an independently authenticated immutable previous-root digest instead of redundantly hashing the previous bytes again. The system-level question is whether that advantage survives a **multi-generation version chain** when trust establishment is charged rather than treated as free.

This experiment does not change ONE representation, discovery, admission, canonical wire, reader semantics, integrity, recovery, or the September 11 gate substrate.

## Falsifiable hypothesis

For a deterministic chain of adjacent 1 MiB versions whose transitions remain within the existing relation-admission contract, establishing the first root digest once and then promoting each newly computed current-root digest as the next trusted prior should:

1. produce byte-identical canonical ONE output and identical Law/admission decisions at every generation relative to a control that hashes both previous and current bytes on every ingest;
2. reduce aggregate CPU and wall time across the chain because exactly one redundant previous-root SHA-256 is removed from every transition after initial trust establishment;
3. retain the advantage after the initial trust-establishment SHA-256 is explicitly charged once to the candidate lifecycle;
4. never require caller-supplied unauthenticated identity or mutation-sensitive reuse.

The expected mechanism is incremental changed-cone work, not a compression mechanism: immutable prior identity is durable state and unchanged information should not be reprocessed merely because a new generation arrived.

## Frozen matrix

- logical version size: **1 MiB**;
- chain transition counts: **2, 4, 8**;
- relation families:
  - clean `shift_plus1` chain;
  - `fragmented_every96` chain, preserving sparse deterministic damage while retaining admissible relation structure;
  - independent-random chain as a rejection/control family;
- repetitions: **9** complete lifecycle measurements per chain/family, alternating candidate/control order by repetition;
- control lifecycle: hash previous + current root on every transition;
- candidate lifecycle: hash generation zero once to establish trust, then hash only current root on each transition and promote that verified digest to trusted prior for the next transition.

All writer work other than prior-root identity handling must use the same existing ONE-G0.2 writer path in both arms.

## Frozen gates

Semantic/integrity gates are absolute:

- every transition reconstructs exactly;
- candidate/control canonical wire bytes and semantic signatures are identical at each transition;
- admission/rejection decisions remain identical;
- each promoted prior digest equals an independently recomputed SHA-256 oracle for those bytes;
- any semantic divergence => **INVALIDATE_TRUSTED_PRIOR_CHAIN_LIFECYCLE**.

Economic gate is evaluated at the 8-transition chain, where lifecycle amortization is meaningful:

- clean shift candidate/control median CPU <= **0.90x**;
- fragmented/96 candidate/control median CPU <= **1.00x**;
- random-rejection candidate/control median CPU <= **0.85x**;
- every 8-transition wall ratio <= **1.02x**;
- initial trust-establishment hashing must be included in candidate measurements.

Decision:

- all semantic gates + all economic gates => `ADVANCE_TRUSTED_PRIOR_CHAIN_LIFECYCLE`;
- semantics exact but any economic gate fails => `HOLD_TRUSTED_PRIOR_CHAIN_LIFECYCLE`;
- semantic/integrity divergence => `INVALIDATE_TRUSTED_PRIOR_CHAIN_LIFECYCLE`.

## Disproof interpretation

If the chain does not retain the single-pair advantage once initial trust establishment is charged, the prior result remains valid only as a narrow warm-call optimization and must not be treated as lifecycle evidence. If the fragmented family is neutral, that is acceptable only within the frozen <=1.00x CPU gate because segmentation can dominate hashing. Random rejection must show a strong saving because hashing should be a large fraction of a cheap rejection path.

## Hostile boundaries

This experiment does **not** authorize trusting arbitrary caller hashes. Prior identity may be reused only when derived from an authenticated immutable generation/state record. Any mutation, missing provenance, or trust discontinuity requires identity re-establishment.

This is independent transfer evidence and does not execute or inspect the frozen 15-workload Genesis scoreboard before September 11.
