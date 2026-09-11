# ONE-G0.2 — compact rescue carrying-cost A/B

**Status:** result-bearing encoder-discovery evidence; seed advances with localized small-input debt  
**Exact source:** `647647b032e0bfb9726535873a941ff310a6277d`  
**Workflow:** `33946400742`  
**Job:** `101253166957`  
**Artifact:** `9963465662`  
**Artifact digest:** `sha256:91d185a3bbc59e29fcc6689040e97fd23159f61e1db0cca21ff73c59080f3243`  
**Experiment:** `ONE-G0.2`

## Referee freeze

The compact modulo-position rescue queue had already passed its internal representation gate at 47,104 B versus 71,680 B while preserving exact gated recurrence traces. That did not establish global value. The earlier unoptimized complete rescue path was 5.3-7.1% slower than the promoted 8 KiB tail-return selector on entropy controls and 3.77x slower on the tiny hard-rescue row.

This A/B therefore charged the complete compact rescue path — Gear signal, 4,096-byte history, activation replay and compact exact queue — against the promoted 8 KiB tail-return selector on the same native runner.

Frozen seed requirements were:

- exact gated trace/state/accounting against the independent Python recurrence on every row;
- candidate state <= 1.15x promoted state for every row >= 8 KiB;
- compact/promoted median <= 0.98x on random and zlib-random 1 MiB;
- median <= 1.02x on repeated and shifted large controls;
- any large ordinary row > 1.05x retires this implementation as a global carrying path;
- the 8,193-byte hard-rescue row is measured separately: >1.20x opens explicit small-input creation debt.

## Exact result

Artifact decision: `advance_compact_rescue_seed_with_small_case_debt`.

All rows preserved exact gated recurrence semantics. Candidate reserved state was **47,104 B** versus **41,056 B** for the promoted large selector: **1.147311x / +14.73%**, inside the frozen <=1.15x gate.

| Case | Input | Median compact / promoted | Promoted median | Compact median | State ratio |
|---|---:|---:|---:|---:|---:|
| random_1mib | 1,048,576 B | **0.972031x** | 4.861 ms | 4.724 ms | 1.147311x |
| zlib_random_1mib | 1,048,902 B | **0.949553x** | 6.140 ms | 5.830 ms | 1.147311x |
| repeat_64k_basis_1mib | 1,048,576 B | **0.846877x** | 4.815 ms | 4.102 ms | 1.147311x |
| shifted_512k_insert1 | 1,048,577 B | **0.924231x** | 4.863 ms | 4.492 ms | 1.147311x |
| transfer_starved_seed10_insert1 | 8,193 B | **2.965240x** | 30.236 us | 89.657 us | 1.147311x |

Thus the optimized complete rescue reverses the old ordinary-path compute debt on every large control tested:

- random: **2.80% faster**;
- already-compressed zlib-random: **5.04% faster**;
- repeated: **15.31% faster**;
- shifted/versioned: **7.58% faster**.

The large-path result is causally important because it closes the earlier interpretation that replay + rescue must inherently lose to the promoted selector once fully charged. The combination of linear activation construction and compact positions changes that conclusion.

## Remaining debt

The hard 8,193-byte transfer row remains sharply red at **2.965x**. In absolute terms the candidate adds about **59.4 us** (89.657 us vs 30.236 us). The earlier structural-transfer evidence shows this family exists because 4,096-byte shifted/starved cases can contain full-minimizer reuse opportunity absent from fixed/sparse cheap observers. Therefore the right response is not to delete the rescue path merely to erase the small-row timing red.

The next Builder must attack **small-input scheduling/work organization** while preserving the historical information required by the hard transfer. A promising causal direction is event-edge replay: retain the bounded byte history + seed, reconstruct a candidate only at starvation activation and episode exit/EOF, and avoid per-position queue maintenance when the remaining tail is short. That is a materially different reopening from rejected cold rescue because the historical state is now retained and replayed; all replay cost must remain charged.

## Hostile review / claim boundary

This is encoder-discovery research evidence only. It creates no stored-byte, reader, product, v0.29/v0.30 comparator, release, access, integrity, recovery or portability authority.

The largest unresolved scientific risk is now **opportunity quality**, not merely runtime: the compact gated recurrence has proven exact relative to its own independent oracle, but it has not yet demonstrated across a broad transfer corpus that the cheaper gated candidate set preserves the mature full-minimizer relation opportunity sufficiently to replace that observer. Speed superiority on four controls is therefore a seed result, not a promoted discovery baseline.

## Decision

**Advance the compact rescue seed, but do not promote it.** Preserve the current promoted 8 KiB tail-return selector as the authoritative discovery baseline until (1) small-input scheduling debt is attacked without losing hard transfer and (2) generator-distinct opportunity transfer demonstrates that the gated candidate set earns its global carrying cost.
