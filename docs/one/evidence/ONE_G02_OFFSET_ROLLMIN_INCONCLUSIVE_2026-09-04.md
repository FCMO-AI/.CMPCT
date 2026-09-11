# ONE-G0.2 — Rolling-min suffix fusion: read-count win, elapsed inconclusive

**Branch:** `research/cmpct1`  
**Exact result-bearing source:** `ce435923c16dd0d53f5c94c6468957a9f725d828`  
**Workflow run:** `33942573560`  
**Result-bearing job:** `101242699760`  
**Artifact:** `9962305507`  
**Artifact ZIP SHA-256:** `5da685034dfb62ebf814318e42948df3f38d5f3767b49916528bbc4bd36840f8`  
**Experimental version:** `ONE-G0.2`

## Frozen hypothesis

The promoted offset-only selector stores a dense `uint16` suffix-argmin table plus retained raw Gear states. During backwards suffix construction the source implementation reloads `block_values[next_argmin]` at every step even though that value is the running minimum already established by the recurrence.

The preregistered Builder carries the running minimum value and argmin in registers. It preserves the same state layout, exact rightmost-min tie semantics, query path, source traffic, 8,192-byte dispatch law and reader boundary. Promotion required exact oracle equality, identical suffix lifecycle/state/query load count, derived-state reads <=0.55x baseline, every selected-case median <=1.03x, every large p90 <=1.05x, and cross-large median <=0.97x. A large-case median >=1.05x would reject for elapsed debt; otherwise the result is inconclusive.

## Result

**Frozen decision: `offset_rollmin_inconclusive`.**

All **50 ONE tests passed** before the result-bearing experiment. Independent Python anchor traces, final Gear state, considered-position counts, suffix block lifecycle, enabled reserved state and query-time indirect-load counts remained exact.

The intended mechanical reduction was achieved almost perfectly:

- enabled-state baseline suffix-build reads at 4,160 B: **2,047**;
- candidate: **1,024**;
- ratio: **0.500244x**;
- 1 MiB baseline examples: about **2.088–2.090 million** derived-state reads;
- candidate: about **1.044–1.046 million**;
- ratio remains **0.500244x**;
- enabled reserved state remains **41,056 B**;
- source-byte rescans remain **0**.

But elapsed time did not follow the nominal traffic reduction strongly enough:

- cross-large median candidate/baseline: **0.986734x** — only about **1.33% lower elapsed**, missing the frozen 0.97x promotion requirement;
- random 1 MiB: median **0.986734x**, p90 **1.007646x**;
- zlib-random ~1 MiB: median **0.986211x**, p90 **1.032955x**;
- exact pair ~1 MiB: median **0.982671x**, p90 **1.017856x**;
- shifted pair +1 B: median **1.006993x**, p90 **1.037252x**;
- repeated 64 KiB basis: median **1.005886x**, p90 **1.042760x**;
- hostile shifted 16,385 B: median **0.982456x**, p90 **1.023528x**.

No large-case median reached the 1.05x rejection boundary, so this is not evidence that rolling-min logic is intrinsically harmful. It is evidence that halving this source-level suffix-build read counter is **not sufficient** to claim a meaningful compute win.

## Causal interpretation / scoped negative

Do **not** spend another activation merely reducing the same suffix-build read counter. The mechanical counter moved by ~50%; elapsed moved by ~1%. Therefore those counted accesses are not a reliable proxy for the dominant machine cost under the current `-O3` kernel. Likely explanations include cache residency and/or compiler reduction of the source recurrence to similar machine work; static/generated-code inspection is the correct next discriminator.

The unchanged query-time indirect-load count is also conspicuous: mature 1 MiB rows still perform roughly **1.043 million** suffix-value indirect loads. The Builder removed construction-side redundant reads but did not change that selection-side stream. That is consistent with the paired residual evidence treating suffix construction and selection as a co-dominant cluster rather than allowing a source-counter-only optimization to stand in for real fusion.

**Reopening predicate:** revisit rolling-min construction only if disassembly or hardware-counter evidence shows the baseline still executes materially more memory work and a revised implementation can remove it without shifting cost into query selection. Otherwise target work that eliminates machine instructions/memory traffic across the suffix+selection boundary itself.

No implementation is promoted by this result. It creates no reader, Law, wire, stored-byte, product-speed, comparator or release authority.
