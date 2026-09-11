# ONE-G0.2 — Offset-only cached suffix recurrence causal result

**Branch:** `research/cmpct1`  
**Exact result-bearing source:** `3b36c5e8e3357dab0080aeca34002770cca4587c`  
**Workflow run:** `33940951671`  
**Result-bearing job:** `101238152504`  
**Artifact:** `9961800292`  
**Artifact SHA-256:** `07ef45eb54d4bef7b34e7c71bf818503064e24e941e95490a895093776580b60`  
**Experimental version:** `ONE-G0.2`

## Mission lock

Test one causal claim only: after the offset-only dense suffix removed duplicated `uint64` suffix values, does rereading `block_values[next_argmin]` during every backward recurrence step materially own the remaining suffix-build elapsed cost?

The Builder retains the suffix minimum value and argmin in scalar recurrence state. It still stores the same `uint16` argmin table and the same four raw Gear-state blocks. Gear identity, selector, window/span, source pass, reader/Law surface, reserved state and query-time indirect work are unchanged.

The preregistered A/B and frozen thresholds are in `benchmarks/one/one_g02_minimizer_offset_cached_ab.py`. They were committed before result-bearing execution and are not rewritten here.

## Exact semantic and resource result

The exact-head job passed **50/50 ONE tests** and the independent Python anchor oracle on every A/B case. Final Gear state and positions-considered counts match. Suffix block build/skip lifecycle, query-time suffix-value indirect loads and reserved state match the prior offset-only implementation. Source rescans remain zero.

Enabled reserved state remains **41,056 B**, versus **49,248 B** for the promoted counter baseline: ratio **0.833658**, about **16.63% less**.

The causal traffic intervention worked exactly as intended. On enabled cases, cached build-time derived-state reads are about **0.500244x** the prior offset-only implementation. Typical 1 MiB examples move from about **2.088 million** derived-state reads to about **1.044 million** while query-time indirect loads are unchanged.

## Elapsed result

Cached/old-offset ratios from the result-bearing single-batch A/B:

| case | cached / offset | cached / counter | interpretation |
|---|---:|---:|---|
| below enablement, 4,159 B | 1.19008x | 1.32710x | no suffix work executes; frozen any-case gate blocker |
| at enablement, 4,160 B | 0.93579x | 0.92331x | faster |
| random 1 MiB | 0.84433x | 0.80629x | 15.57% faster than old offset |
| zlib-random ~1 MiB | 0.93415x | 0.86895x | 6.59% faster |
| exact pair ~1 MiB | 0.89940x | 0.88177x | 10.06% faster |
| shifted pair +1 B | 0.88016x | 0.82284x | 11.98% faster |
| repeated 64 KiB basis, 1 MiB | 0.91216x | 0.88020x | 8.78% faster |
| hostile shifted 16,385 B | 0.90614x | 0.89658x | 9.39% faster |

Large-case median cached/offset ratio is **0.899396x**. Worst large ratio is **0.934150x**. Thus every large case improved by at least about **6.59%**, and the median improved by about **10.06%**.

## Frozen decision

**Decision: `cached_offset_recurrence_inconclusive`.**

Do not retroactively promote this result. The immutable gate required no tested case above `1.05x`; the 4,159-byte below-enablement row measured `1.19008x`. That row performs no suffix maintenance at all, so it cannot causally refute the suffix-read mechanism, but it does block the frozen implementation promotion exactly as preregistered.

The scientifically supported statement is narrower: **redundant suffix-build derived-state reads materially own elapsed cost on the enabled tested regime, and scalar recurrence removes roughly half that traffic while preserving the lower 41,056-byte state representation.** Implementation promotion remains unresolved.

## Hostile review / next experiment

The strongest concern is timing/order sensitivity: historical single-batch replays have moved labels while preserving broad direction, and the sole current blocker is a tiny no-suffix path. A new, independently frozen paired A-B-B-A confidence instrument must determine whether the enabled speedup repeats and whether the below-enablement slowdown is stable compiled-function overhead or timing/order noise. That companion may justify a new superseding implementation freeze; it may not rewrite this result.

No reader, wire, stored-byte, product-speed, v0.29, v0.30, release or public-superiority authority is created by this receipt.
