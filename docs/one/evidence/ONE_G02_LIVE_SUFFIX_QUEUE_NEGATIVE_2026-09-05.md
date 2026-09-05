# ONE-G0.2 live suffix-queue fusion — negative result — 2026-09-05

Status: **RETIRE under the tested regime**

## Frozen hypothesis

The promoted >=8 KiB offset-only selector keeps four raw Gear-state blocks plus four dense uint16 suffix-argmin tables. The Builder exploited a lifetime alignment: while block `q` overwrites the same slot that held block `q-4`, the only required suffix query on the old block advances left-to-right in the same order. The hypothesis was that one live monotonic uint16 offset queue could replace all four dense suffix tables, preserving the exact rightmost-min selector while cutting state and elapsed work.

Frozen disproof gate before result-bearing execution:

- exact independent-oracle anchor trace, final Gear state and considered-position count on every case;
- zero source-byte rescans;
- reserved state <=0.90x promoted offset-only state;
- every large-case elapsed <=0.95x baseline;
- no tested case >1.05x baseline.

## Exact execution

- source: `73fb7dc184ee73c1c311543c578ccff8412b97af`
- workflow: `33957936485`
- result-bearing job: `101284542731`
- artifact: `9966985037`
- artifact ZIP SHA-256: `2699f8ecfb9e72e9581504e9926a22940ca0839fa712127ebf5ea24bc0ce222b`
- `tests/one`: **76/76 passed**
- result schema: `cmpct-one-g02-minimizer-live-suffix-queue-ab-v1`
- terminal decision: `retire_live_suffix_queue_fusion`

## Result

The semantic idea was valid:

- every tested anchor trace matched the independent Python rightmost-min oracle;
- final Gear state and considered-position counts matched;
- source rescans remained **0**.

It also achieved the intended state reduction:

- promoted offset-only state: **41,056 B**;
- live queue state: **34,928 B**;
- ratio: **0.850740x**, a **14.93% reduction**.

But elapsed cost failed decisively:

| Case | live / offset elapsed |
|---|---:|
| 4,160 B enablement boundary | **1.24860x** |
| random 1 MiB | **3.90388x** |
| zlib-random ~1 MiB | **3.72233x** |
| exact pair 1 MiB | **3.89661x** |
| shifted pair ~1 MiB | **3.99057x** |
| repeated basis 1 MiB | **3.98964x** |
| hostile shifted 16,385 B | **2.92529x** |

The large rows performed about **1.043–1.044 million queue pushes** and roughly **1.036 million back-pops** per MiB. Derived-state reads also increased rather than decreased: for random 1 MiB, **3,115,156** versus **2,087,940** in the dense offset baseline.

## Causal interpretation

The lifetime observation is correct, but this particular representation converts cheap regular dense construction into an irregular branch/dependency chain. On entropy-dense and ordinary inputs the monotonic queue spends almost one back-pop per pushed state. The state saving therefore does not represent a marginal-information-yield win: roughly 6 KiB of retained state is saved at the cost of a 3.7–4.0x large-case encoder slowdown.

Together with the earlier sparse-record suffix and event-driven dense-selection losses, this strengthens a scoped causal constraint: **reducing nominal writes/state/events is not useful when the replacement introduces per-state data-dependent control and pointer/index dependencies into this hot selector path.** The current hardware/compiler strongly rewards the regular direct-indexed dense representation.

This does not prove that suffix+selection fusion is impossible. It falsifies the `build one live monotonic queue per expiring block` family under the current 4,096-position rightmost-min selector, four-segment layout, C/O3 implementation and standard ONE-G0.2 corpus.

## Reopening predicate

Do not reopen this queue family merely with a smaller queue, a different queue capacity, or threshold tuning. Reopen only with new causal evidence that removes the per-state irregular queue-control bill—for example a genuinely bulk/SIMD/branchless formulation, a mathematical block summary that composes the exact rightmost-min result without per-position back-pop chains, or an alternative selector representation that provably performs less total dependency work while preserving the same opportunity trace.

## Decision

**RETIRE** live monotonic suffix-queue fusion. Keep the promoted offset-only 8 KiB tail-return baseline. The contemporaneous rolling-min experiment also halved derived suffix reads but was timing-inconclusive (`0.999781x` cross-large median and a `1.04419x` random-1MiB median), so the next Builder should target a more structural regular-data formulation rather than another local count reduction.
