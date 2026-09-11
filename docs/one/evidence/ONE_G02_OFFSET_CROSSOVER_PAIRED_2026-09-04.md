# ONE-G0.2 — Paired offset/counter crossover map

**Branch:** `research/cmpct1`  
**Exact source:** `bd9c3ec9ecb8b91f3cfa3b92779787a87f287979`  
**Workflow run:** `33941483133`  
**Result-bearing job:** `101239663334`  
**Artifact:** `9961963412`  
**Artifact ZIP SHA-256:** `21d314592a254b22e08f22390c37e91bec5131313d71699a56e89c37eff44ed1`  
**Experimental version:** `ONE-G0.2`

## Frozen question

Given the paired Pareto regime split, is there a stable input-size region in which the lower-state offset-only selector is consistently faster than the promoted counter selector across random, repetitive and already-compressed-like data?

The preregistered map reused the existing geometric size ladder and ran 9 warm-started counter-offset-offset-counter rounds per size/regime. Before seeing results, the candidate dispatch law was fixed as the **smallest enabled requested size T such that every tested row at T and above has median offset/counter <=0.98 and p90 <=1.03**. The map itself cannot promote a dispatcher.

## Result

**Decision: `candidate_dispatch_from_8192`.**

At 4,160 B the offset-only representation is consistently slower across the three regimes: regime medians are approximately **1.040x, 1.047x and 1.047x**, with worst regime p90 **1.097x**.

At 8,192 B the sign flips cleanly:

- random: median **0.9425x**, p90 **0.9552x**;
- repeated 4 KiB basis: median **0.9573x**, p90 **0.9667x**;
- zlib-random: median **0.9136x**, p90 **0.9295x**.

Every tested regime at every larger frozen size also satisfies the 0.98 median / 1.03 p90 selection law. Median-of-regime-medians by requested size is approximately:

- 16 KiB: **0.8941x**;
- 32 KiB: **0.8908x**;
- 64 KiB: **0.8921x**;
- 128 KiB: **0.8979x**;
- 256 KiB: **0.8935x**;
- 512 KiB: **0.8950x**;
- 1 MiB: **0.9120x**.

The lower-state path remains **41,056 B vs 49,248 B** whenever enabled. No source byte rescans are introduced.

## Interpretation

The crossover is not a content classifier; it is a simple compute-efficiency gate on input size. The causal explanation is consistent with the measured data: fixed/startup cost dominates at exact enablement, while avoiding the duplicated suffix-value state wins once enough selector work amortizes startup. This is precisely the sort of cheap opportunity gate allowed by ONE's speed law.

The next Builder is therefore frozen at **8,192 input bytes**: use the existing counter implementation below that boundary and offset-only at/above it. A separate end-to-end dispatcher A/B must charge the branch/wrapper itself, recheck the independent anchor oracle, and prove that the combined path does not export a new small-file regression before the research baseline changes.

This evidence creates no reader, Law, wire, stored-byte, product-speed, v0.29/v0.30 or release authority.
