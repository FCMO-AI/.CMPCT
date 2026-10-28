# r25 Shifted G0-G4 graph-kernel attribution v1 execution result

Status: **INFRASTRUCTURE_INVALID / SUPERSEDED BY V2 / ZERO PRODUCT OR RELEASE CREDIT**

Source commit: `3ac4439333ba312ded0a84b371aa4fa4022a68b0`  
Workflow run: `33796553954`  
Result-bearing job: `100785586053`

## What executed

The frozen v1 instrument compiled, built the deterministic Shifted fixture, entered the three-repetition attribution loop, and completed the first v0.28 worker. It then failed in the first attempt-5 worker before a complete repetition pair or terminal receipt existed.

The failure was mechanical rather than scientific: the attempt-5 timer list requested the preregistered inherited `V028._choose_pack_plan` boundary through `module.V028`, where `module` was `accepted.BASE.A4`. That module has no `V028` attribute. The accepted wrapper exposes the inherited v0.28 module as `accepted.V028` / `accepted.BASE.V028` instead.

Exact exception:

`AttributeError: module 'cmpct_entropygraph_v029_attempt4_for_residual' has no attribute 'V028'`

Because the worker aborted before all three alternating repetition pairs, no JSON receipt was emitted and no terminal decision in the frozen grammar is valid. Partial timer observations receive zero scientific decision credit.

## Custody decision

`SHIFTED_G04_GRAPH_KERNEL_V1_INFRASTRUCTURE_INVALID`

The v1 preregistration and instrument remain immutable. V2 may supersede it only by correcting the module owner used to observe the already-preregistered inherited `V028._choose_pack_plan` boundary. Corpus, timestamp normalization, child identities, three-repetition order, primitive timer set, 0.20 materiality band, decision grammar, and interpretation law remain unchanged.
