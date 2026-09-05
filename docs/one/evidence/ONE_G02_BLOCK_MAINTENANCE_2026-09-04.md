# ONE-G0.2 — block-minimum maintenance result

**Source:** `4b2c60b139d09606ad7499ff736158dd11fdb9f4`  
**Workflow:** `33934157435`  
**Job:** `101218708556`  
**Artifact:** `9959767313`  
**Artifact SHA-256:** `e50725d5abb0682a8f58971f0d8c551d6286274887d47995366aff55e2f3b13f9`  
**Schema:** `cmpct-one-g02-minimizer-block-ab-v1`  
**Tests:** `50 passed` in `tests/one`

## Mission lock

Test whether a predictable block prefix/suffix sliding-minimum algorithm can preserve the exact rightmost-minimum Gear anchor sequence while materially reducing the compiled cost of the masked monotonic deque. Gear identity, 64-byte Gear window, 4,096-position minimizer span, rightmost tie rule, proof semantics and reader representation were frozen.

Promotion was frozen before execution: exact anchor-position sequence on every case; exact final Gear state and considered-position count; block elapsed <=0.70x masked-deque on every large case; <=1.10x on every tested case; reserved discovery state <=1.25x masked-deque.

## Result

The frozen decision is **`retire_block_maintenance_candidate`**. The decision may not be rewritten after seeing the result.

The failure is narrow and causal. Exact anchor-position traces matched on every case, final Gear state and considered-position counts matched, no source-byte rescan was introduced, and reserved state was 75,776 B including the shared Gear table versus 67,584 B for the masked deque (**1.1212x**, inside the 1.25x cap).

On every 1 MiB large regime, the block algorithm materially exceeded the frozen 30% improvement requirement:

| regime | masked deque | block minimum | block/masked | speedup |
| --- | ---: | ---: | ---: | ---: |
| random 1 MiB | 8.377 ms | 3.590 ms | 0.4286x | 2.33x |
| zlib-random 1 MiB | 8.379 ms | 3.606 ms | 0.4304x | 2.32x |
| exact pair | 8.308 ms | 3.591 ms | 0.4322x | 2.31x |
| shifted pair | 8.498 ms | 3.679 ms | 0.4329x | 2.31x |
| repeated 64 KiB basis | 8.247 ms | 3.563 ms | 0.4320x | 2.315x |

Mid-size hostile/repetitive cases also improved: shifted-starvation 16,385 B was 57.421 us -> 52.668 us (0.9172x); repeated 128 B, 256 B and 4 KiB bases at 65,536 B improved to 0.5631x, 0.5553x and 0.5226x respectively.

The disproof was the first just-enabled boundary. At 4,160 B the block implementation paid its full first 4,096-state suffix construction but had almost no mature windows over which to amortize that work: **9.850 us -> 12.411 us, 1.2600x / +26.0%**, violating the frozen 1.10x no-regression bound. At 4,159 B, before the minimizer is enabled, block was slightly faster (5.149 -> 4.853 us).

## Interpretation

This is a formally rejected candidate with a reproducible high-upside core. Per Breakthrough Rehabilitation, the large-case gain must not be tuned away merely to make the old gate green. The exported debt is startup/amortization behavior near minimizer enablement plus 12.12% extra reserved derived-state capacity.

The result also narrows the causal model: unpredictable monotonic-deque maintenance is a major cost owner. Replacing it with predictable derived-state block work cuts sustained large-input elapsed by about 57%, whereas isolated ring-address changes recovered only single-digit percentages.

The block kernel still does **not** solve ONE's speed problem. Roughly 3.6 ms per 1 MiB is around 278 MiB/s, still far below the approximately 2.0 GiB/s Gear-only recurrence. This microkernel excludes proof, extension, Law selection, wire emission and reader cost and therefore is not product-speed evidence.

## Reopening / next decisive test

Do not alter the frozen result or post-hoc choose a dispatch threshold from the single failed case. First map the causal break-even curve with a diagnostic sweep around the 4,096-state setup boundary and into steady state, across random and adversarial/repetitive content. The sweep must preserve exact anchor traces, charge derived-state reads and reserved state, and perform no source reread.

Only if that curve demonstrates a stable structural crossover may a **new superseding preregistration** test a hybrid maintenance implementation (cheap deque for short inputs, block for sufficiently amortized inputs). Such a hybrid remains encoder-only implementation choice for one identical selector, but its code/maintenance complexity is carrying cost and must be charged.
