# r25 Shifted G0-G4 graph-kernel attribution v2 execution result

Status: **INFRASTRUCTURE_INVALID / SUPERSEDED BY V3 / ZERO PRODUCT OR RELEASE CREDIT**

Source commit: `7baeb928d1057e8fe9788a721eba59633826007a`  
Workflow run: `33801275181`  
Result-bearing job: `100801148406`

## What executed

The frozen v2 instrument compiled, built the deterministic Shifted fixture and entered the unchanged three-repetition attribution loop. The first attempt-5 worker aborted before a complete repetition pair or terminal JSON receipt existed.

V2 corrected the v1 owner for inherited `V028._choose_pack_plan`, but exposed that the remaining attempt-5 primitive timers were also attached to the strict wrapper (`accepted.BASE.A4`) rather than the Placement Compiler module (`accepted.BASE.P`) that owns/imports those callables.

Exact terminal exception:

`AttributeError: module 'cmpct_entropygraph_v029_attempt4_for_residual' has no attribute 'delta_encode'`

The same owner mismatch applies to the v1 attempt-5 timer set for `mosaic_delta_encode`, `_compress_record`, and `_position_independent_candidates`; the Placement Compiler is `accepted.BASE.P` and exposes those primitives directly. No complete three-repetition receipt was emitted, so no frozen scientific terminal decision is valid.

The workflow additionally failed its CI-topology self-check because the newly created v2 automatic workflow lacked the required top-level concurrency group. That is custody debt, not scientific evidence.

## Custody decision

`SHIFTED_G04_GRAPH_KERNEL_V2_INFRASTRUCTURE_INVALID`

V2 remains immutable. V3 may supersede it only by:

1. attaching the already-preregistered attempt-5 primitive timers to `accepted.BASE.P` while retaining `accepted.V028._choose_pack_plan` for the inherited pack-plan boundary; and
2. adding the repository-required top-level exact-SHA preserved-receipt concurrency declaration.

Corpus, normalized timestamps, exact child identities, repetition order, primitive set, 0.20 materiality band, decision grammar and interpretation law remain unchanged.
