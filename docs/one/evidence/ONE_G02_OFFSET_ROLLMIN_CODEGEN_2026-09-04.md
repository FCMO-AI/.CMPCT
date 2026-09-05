# ONE-G0.2 — Rolling-min generated-code discriminator

**Branch:** `research/cmpct1`  
**Exact source:** `8ce30a30625ce8bb9b1b9af1e75e425b31582ac9`  
**Workflow run:** `33942651377`  
**Result-bearing job:** `101242914898`  
**Artifact:** `9962327359`  
**Artifact ZIP SHA-256:** `8ffe68ddbc949bbfc54aba4093b60ad8a104b97d1537bdb3a62b2a8ba909fb59`  
**Experimental version:** `ONE-G0.2`

## Question

The rolling-min Builder cut the source-level suffix-build `derived_state_reads` counter from roughly 2.09 million to 1.04 million on 1 MiB rows but moved cross-large elapsed only to 0.986734x. Does the compiler actually emit materially less machine work for that source-level reduction?

This diagnostic was frozen after the dynamic inconclusive result and before generated-code inspection. It compiles baseline and rolling-min sources with the same `cc -O3 -std=c11 -S -masm=intel` settings and counts whole-function decoded instruction lines, memory-operand instructions, jumps and calls. Static evidence cannot promote an implementation.

## Result

**Interpretation: `generated_shape_near_equivalent`.**

Baseline `one_g02_minimizer_offset_only_kernel`:

- instructions: **326**;
- memory-operand instructions: **150**;
- conditional jumps: **42**;
- unconditional jumps: **14**;
- calls: **9**.

Rolling-min candidate:

- instructions: **326**;
- memory-operand instructions: **148**;
- conditional jumps: **42**;
- unconditional jumps: **14**;
- calls: **9**.

Candidate/baseline ratios are therefore **1.000x instructions** and **0.986667x memory-operand instructions**. This matches the dynamic result: halving the source instrumentation counter did not halve generated machine work.

## Causal conclusion

The source `derived_state_reads` counter is not a useful optimization objective for this recurrence under current `-O3` compilation. The compiler already collapses much of the apparent source-level redundancy. Further work aimed only at reducing that same counter is retired unless new hardware-counter or disassembly evidence shows a distinct machine-level bottleneck.

The unchanged query-side suffix candidate stream remains materially different: mature 1 MiB rows still perform roughly **1.043 million** `suffix_value_indirect_loads`, one for nearly every eligible query window. That stream is not removed by rolling-min construction and is now the better causal target, provided any event gate pays for its own branch/control cost under paired elapsed measurement.

No implementation is promoted. No reader, Law, wire, stored-byte, product-speed, comparator or release authority is created.
