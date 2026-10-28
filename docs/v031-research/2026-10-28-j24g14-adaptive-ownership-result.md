# J24G14 — Adaptive ancestry lifetime: positive O1 with explicit high-depth and portability debt

Date: 2026-10-28 UTC. Research-only draft [PR #675](https://github.com/FCMO-AI/.CMPCT/pull/675), child of #674 (J24G13). Preregistered **before** instrument at `8bb541f3746ca1c766b86d559488c4de726c15be`; inherited product Reader Git blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b` unchanged. Release remains v0.30.0 / r24.

## Exact hosted result and controls

[GitHub Actions #40688205093](https://github.com/FCMO-AI/.CMPCT/actions/runs/40688205093), source-exact experimental HEAD `04e37d93db57631b619301254fefa758f1cf72b0`, **SUCCESS**. Original GitHub Actions artifact ID `12815338118` with provider-reported digest `sha256:5205a0f0275de349bdf15283bc84921c7a2cf27d8fd1c4d9932c95acc7df8bbe`. Host Ubuntu 24.04/Python 3.11. Three genuine Reader source-derived arms, original eager, prior guarded and new adaptive; one identical physical Builder/Writer archive for all arms in each case. Three fresh-child untraced repetitions per case/arm except signed malformed 1 each. No tracer or per-call monkeypatch overhead in measured operation; CPU/wall include open/full-and-range read/verify, exclude import/process startup and receipt SHA.

Median process CPU (milliseconds); Linux total fresh-child peak RSS (KiB):

| Same physical case | Eager CPU | Guarded CPU | Adaptive CPU | Adaptive / eager CPU | Eager → adaptive RSS |
|---|---:|---:|---:|---:|---:|
| First-party Writer rename | 0.412 | 0.434 | 0.435 | 1.054x | 32,036 → 32,036 |
| Valid depth 64 | 2.219 | 2.516 | 2.331 | 1.050x | 32,036 → 32,036 |
| Valid depth 512 | **15.371** | 16.917 | **15.766** | **1.026x (+2.57%)** | 33,464 → 34,100 |
| Valid depth 2048, crosses budget | 65.476 | **64.520** | 71.681 | **1.095x (+9.48%)** | 46,368 → **38,912** |
| Invalid linked depth 4096 | 93.222 | **59.071** | **65.569** | **0.703x (-29.66%)** | 62,808 → **48,716** |
| Invalid 4096 independent tails | 50.333 | 57.248 | 51.408 | **1.021x (+2.13%)** | 48,740 → 48,740 |

The adaptive Reader switched exactly once at depth 2048 and linked-orphan depth 4096, with **1,048,330 B** maximum retained raw delta payload (below preregistered 1,048,576 B cap), while it never switched on depth 64, valid512, independent4096 or normal Writer rename. These are factual diagnostic results, **not** a whole Reader memory cap (nested Python objects, proofs and ancestry offset sets still grow).

It preserved exact selected footer and generation depth, full member content, both ranged reads, and verification. The SHA-authentic **malformed MessagePack** control raised an exception in all three arms; naive skip from #671 remains semantically disqualified. The fixed case design and precommitted kill criteria were not weakened.

## Preregistered decision

The narrow O1 gates were: adaptive valid512 slowdown no more than +10% and >0.05 ms relative to eager; linked-invalid4096 total process RSS saving at least 15%; linked-invalid CPU no more than +20% overhead; exact semantics. Observed valid512 +2.57% CPU and invalid linked **-22.44% total RSS** and **-29.66% CPU**, with all stated semantic cases passing. **O1 retains adaptive ownership as a promising research seed**. It does not establish a general product Pareto domination.

The **stronger unconditionally guarded control is faster at deep valid2048 and linked-invalid4096**, and matches adaptive memory in those specific cases. The adaptive trade is to preserve shallow/flat eager economics: it improves valid512 CPU relative to guarded (15.766ms vs 16.917ms) and flat invalid4096 CPU (51.408 vs 57.248ms), but still loses +2.57% and +2.13% against the simplest eager. This remains legitimate regression debt even if below the prereg threshold. More fixtures or adjusted thresholds cannot turn it into release credit.

## Independent audit and evidence limits

The stdlib-only `research/j24g14_independent_receipt_audit.py` reported **817 raw/source/median/physical-hash-consistency checks** and rejected **6 deliberately forged receipts**: false CPU, physical SHA, median, erased malformed error, false threshold switch, and fake release claim. It checks original Git blob/source SHA on the tested HEAD, source authenticity and equal archive hashes per case. It **does not** perform a second independent physical decoding of the archived bytes, and CI artifacts carry receipt hashes rather than the complete physical archive files. Raw fresh-child repeated measurements are preserved in the original Actions artifact.

No independent Windows/macOS, in-place same-inode mutation, real-world workload prevalence, physical temp-I/O/RSS amplification outside the child RSS snapshots, full product parity/codec competitor, cold-process startup or security gate was measured.

## Strongest source-level adversary / causal gap

The adaptive prototype counts **raw payload length** but retains both a parsed Python object and the raw payload bytes until its switch; the 1MiB raw limit therefore need not cap decoded Python memory and may duplicate retention. It also keeps one Python `seen` set and one offset/SHA tuple for each deferred delta. On a *valid* long chain, it must re-decode/reverify, exporting work and source-mutation assumptions, even when the original eager is faster. In-place same-inode archive mutation remains an unresolved consistency case under #654. These cannot be repaired by merely calling the 1MiB cap a resource policy.

A future product-worthy hypothesis would eliminate redundant payload-copy ownership while charging parsed-object memory, or use a generically discoverable capped-memory checkpoint plan that avoids long successful replay. Both must defeat the simplest eager Reader and the fully guarded model, preserve signed malformed error decisions, and measure actual total memory, CPU, RSS, temp I/O, recovery, cold-open and multi-host conformance.

## Scientific handoff / Discovery Engine

**Primary question changed:** we can avoid unconditional double replay for shallow valid deltas while retaining much of the deep-invalid resource advantage in the measured exact case. **No concurrency collision:** #675 is explicitly stacked on #674; #671 and #668 remain unchanged, while #669/#673 own disjoint mechanisms. Existing discovery state is a stale v0.30 cache with a separate owner (#574); do not alter it from this single isolated research experiment.

**Counterfactual:** J24G13's matched tracer-off CPU plus the extra long-valid crossing-budget case immediately exposes that a generic raw-payload threshold is a partial ownership policy, not a global resource bound. A strong early admission court needs both deep invalid and deep legitimate ancestry, plus independent flat tails; no new discovery-policy change earned.

**No product-source change, release change, format change, frozen-benchmark modification, merge, or release credit.** The HEAD containing this result document differs from the first result-bearing HEAD; repeat exact-head CI must be judged separately.
