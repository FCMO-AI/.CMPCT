# ONE-G0.2 — 8 KiB size-dispatch Builder rejection

**Branch:** `research/cmpct1`  
**Exact source:** `562ef81deea97775667d3a0e74ab4d17e81b4f1a`  
**Workflow run:** `33941583669`  
**Result-bearing job:** `101239945675`  
**Artifact:** `9961997250`  
**Artifact ZIP SHA-256:** `91418d2e8e828ac0026cb0a7906d8641233ced03cb1f4c155368c21d4de0edda`  
**Experimental version:** `ONE-G0.2`

## Frozen Builder

The paired crossover map selected 8,192 input bytes before this Builder existed. The C dispatcher used the promoted counter selector below 8 KiB and the 41,056-byte offset-only selector at/above 8 KiB. The A/B charged the actual wrapper branch and result-copy surface against direct counter calls over 13 warm-started counter-dispatch-dispatch-counter rounds.

Promotion required counter-region median <=1.03 / p90 <=1.05, offset-region median <=0.98 / p90 <=1.03, and cross-large median <=0.95. Any counter-region median >1.05 or large median >=1.03 was a frozen rejection condition.

## Result

**Decision: `reject_8k_dispatch_for_elapsed_debt`.**

Correctness survived: **50/50 ONE tests passed**, and dispatcher/counter traces, final Gear state and considered-position counts matched the independent Python oracle. The selected path and reserved-state accounting were exact. No source rescans were introduced.

The useful large-region signal remained positive but weaker than the freeze demanded:

- cross-large median dispatch/counter: **0.958699x** (~4.13% faster), missing the <=0.95 promotion requirement;
- 262 KiB regime medians: about **0.9532x--0.9581x**;
- ~1 MiB regime medians: about **0.9593x--0.9652x**;
- selected large-region state remained **41,056 B vs 49,248 B** (16.63% lower).

The wrapper also exported small-path debt despite selecting the unchanged counter algorithm. The clearest frozen reject row was repeated-basis 4,159 B: median **1.07424x** counter, with p90 **1.19104x**. Other small counter-path medians were much closer to parity, showing that the extra dispatch/call/result-copy surface is small but not reliably free at tiny scales.

At the 8 KiB boundary itself, the offset branch did not repeat the earlier crossover's strong win in this end-to-end wrapper: medians were roughly **1.006x, 1.021x and 1.017x** for random, repeated and zlib-random cases. That reinforces the requirement to validate the actual integrated path rather than infer product behavior from isolated component timings.

## Causal interpretation

Do **not** relax the 8 KiB threshold or the timing gate. The failure is an exported integration debt: the Builder wraps an already-exported kernel call in another function, copies a result struct field-by-field, and then returns. That is avoidable work unrelated to the selector principle.

The next rehabilitation is therefore structural and frozen separately: preserve the exact 8 KiB opportunity rule but make the common result prefix ABI-compatible, set the path bit before dispatch, and tail-return directly into the selected selector so the compiler can eliminate the result-copy loop and potentially the extra return path. Static codegen must verify whether a tail jump is actually produced; paired timing then decides whether this pays the exported debt.

If that lower-overhead integration still fails, the 8 KiB dispatcher is retired for this regime and the counter selector remains the research baseline while the offset-only state/speed evidence stays as a scoped opportunity result.

No reader, Law, wire, stored-byte, product-speed, v0.29/v0.30 or release authority is created.
