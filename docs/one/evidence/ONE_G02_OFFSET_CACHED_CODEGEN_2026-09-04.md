# ONE-G0.2 — Cached suffix recurrence codegen diagnosis

**Branch:** `research/cmpct1`  
**Exact source:** `930d1118b9f760e392eb7508de31d40a000a77d8`  
**Workflow run:** `33941197068`  
**Result-bearing job:** `101238841505`  
**Artifact:** `9961869334`  
**Artifact ZIP SHA-256:** `1ce39cdaa02d95269cc3cadb10bf905c96b0b5a25c54af0b727fe9baf1b73e79`  
**Experimental version:** `ONE-G0.2`

## Causal question

Paired A-B-B-A timing showed that replacing the old offset-only suffix recurrence's explicit `block_values[next_argmin]` reread with a scalar-carried minimum did not produce the large elapsed win suggested by all-A/all-B timing. Did the modeled logical-read reduction survive `-O3` as materially different machine work?

## Same-compiler result

Both implementations compile to **337 instructions** in the target function and **66 branch/call/return instructions**.

Static memory-reference instruction counts are:

- old offset-only: **160**;
- cached recurrence: **159**;
- delta: **-1 instruction**.

The normalized instruction fingerprints differ, so the functions are not byte-identical, but the compiler turns a modeled ~2:1 C-level derived-read count into only a one-instruction difference in the whole generated function.

## Interpretation

This supports the hostile-review explanation from the paired timing result: the instrumentation's `derived_state_reads` counter described source-level logical accesses, **not physical memory operations after optimization**. It was therefore an invalid proxy for expected elapsed savings in this case.

Combined with paired large-case medians around parity (`~0.997x--1.008x`), the correct causal conclusion is that merely carrying the suffix minimum in C does not currently provide a proven speed benefit. The offset-only representation's **41,056 B** state footprint remains valid; only the claimed speed owner is retired.

## Research constraint

Future ONE discovery-cost accounting must distinguish algorithmic/logical work counters from generated machine work when compiler optimization can erase or fuse the counted operation. A large reduction in an abstract counter is not sufficient evidence of marginal-information-yield improvement without paired elapsed evidence or lower-level generated-work evidence.

Do not reopen cached suffix recurrence as a primary speed strategy under the same selector/layout/compiler regime without new evidence that materially changes generated work, cache behavior, or the surrounding loop.

This is static codegen evidence only. It creates no product-speed, format, reader, stored-byte, v0.29/v0.30 or release authority.
