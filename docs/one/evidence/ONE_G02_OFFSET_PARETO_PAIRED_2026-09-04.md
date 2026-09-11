# ONE-G0.2 — Offset-only paired Pareto replay

**Branch:** `research/cmpct1`  
**Exact result-bearing source:** `3f5742a44b7a20b0a2b41d93f7f72e56cc6af9c4`  
**Workflow run:** `33941395348`  
**Result-bearing job:** `101239411086`  
**Artifact:** `9961939886`  
**Artifact ZIP SHA-256:** `fc6c6e25e0ebd415d4c13ec944fa6cba09c90f377e00361f6432adf303d97f18`  
**Experimental version:** `ONE-G0.2`

## Frozen question

Can the lower-state offset-only suffix representation replace the promoted counter baseline without material elapsed debt under order-neutral timing?

The preregistered replay used 17 warm-started counter-offset-offset-counter rounds, batching small inputs, and required exact Python-oracle anchor traces plus identical final Gear state and considered-position counts. The lower-state representation had to remain <=0.85x counter state. Promotion additionally required every enabled median <=1.03x counter, every large-case p90 <=1.05x, and cross-large median <=1.02x. Any large median >=1.05x would reject it for elapsed debt.

## Result

**Frozen decision: `offset_only_pareto_inconclusive`.**

The state result is exact and strong: **41,056 B vs 49,248 B**, ratio **0.833658**, a **16.63% reduction** in enabled reserved discovery state.

The timing result is a clear size-regime split rather than a broad regression:

- exactly at enablement (4,160 B): median **1.04660x** counter, p90 **1.09247x** — this alone blocks the frozen unconditional promotion gate;
- hostile shifted 16,385 B: median **0.85206x** counter;
- random 1 MiB: median **0.79231x**, p90 **0.83809x**;
- zlib-random ~1 MiB: median **0.80298x**, p90 **0.84692x**;
- exact pair ~1 MiB: median **0.79410x**, p90 **0.80021x**;
- shifted pair +1 B: median **0.79482x**, p90 **0.80468x**;
- repeated 64 KiB-basis 1 MiB: median **0.79252x**, p90 **0.79944x**.

The cross-large median offset/counter ratio is **0.794097x**, or about **20.59% lower elapsed** than counter on that tested large regime. No large case reaches the preregistered rejection boundary.

## Interpretation

Do not average the tiny-boundary loss into the large win and do not retroactively promote the representation. The result says something more useful: **the offset-only representation is simultaneously lower-state and substantially faster once the workload is large enough, while fixed/startup costs dominate at exact enablement.** This is evidence for a size/opportunity gate, not for unconditional replacement.

The next experiment therefore freezes the existing geometric size ladder and paired timing across random, repeated and already-compressed-like regimes. It mechanically selects the smallest size from which the offset representation is consistently non-inferior. A later separately frozen dispatcher A/B is required before changing the research baseline.

No reader, Law, wire, stored-byte, product-speed, v0.29/v0.30 or release authority is created.
