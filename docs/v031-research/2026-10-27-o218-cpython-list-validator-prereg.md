# O218 — CPython list-native fixed-chunk admission oracle (prospective)

Date: 2026-10-27 UTC. This prediction precedes implementing the instrument or observing O218 timings.

## Source and coordination
Base: O216 research PR #570 exact `6989b25640be2c82436bb77ec545dd15816f698b`, existing J24C02 owner #569 and scientific Counter attempt O217 #575. This experiment is **independent lower-rung research only**; it does not modify Reader, validator, CI gates, release, format, comparator or other agents' branches. GitHub open-PR/title search found no separate CPython-list native reference-scan owner. No CONCURRENCY_PROTOCOL.md is present on released main (404), so preserve normal branch isolation and reread conflicting PRs before late writes.

## Exact question
Can a small CPython C-extension iterate **already decoded Python list objects directly** (no list -> array copy, no uncharged data transformation), check every fixed-chunk reference and its blob length, and return a safe "ordinary fast path validated" flag, materially reducing interpreter dispatch cost compared with O216's strict exception-only Python loop?

## Historical baseline
O216 #570 / hosted Actions #40451829700: ~6.3633 ms at 65,536 refs and ~25.1282 ms at 262,144 refs for the *entire installed Reader opening*, which is not directly comparable to a primitive C-extension microbenchmark. O217 #575 showed Counter's slower/noisy 1.080x/1.069x gain over the O216 fast path on repeat profiles and 0.789x on 4096 fully distinct. Counter is retired as a full repair. **Never add microbenchmark savings to Reader wall without a direct product A/B.**

## Mechanisms
- A: strict direct Python loop mirroring O216's exception-only validity checks and accumulation over exact `list[int]` and physical `blobs[idx][1]` lengths;
- B: compiled CPython API function directly reading `PyList_GET_ITEM`, `PyLong_CheckExact`, and bounded size conversion. It scans all refs, rejects boolean aliases, negative/out-of-bounds/overflow/non-integer input, and totals represented lengths. On any anomalous case, return a slow-path sentinel and delegate to the *original strict validator* for complete semantic and exception identity.
- C: deliberately unsafe bypass control as lower bound ONLY, not a product candidate or evidence of correctness.
- Strong alternative explanation: the O216 4x fastpath has already consumed most interpretable overhead, leaving little for native help; C extension ABI, installation, portability and source ownership impose unreasonable maintenance debt.

## Scope and disproof
Cheapest rung: same-process micro timed repetitions on 4096/65,536/262,144 references, both high-repeat and high-distinct, plus hostile type/range/total mismatch tests. Raw times, medians, CPU/process startup separated. Preregister >=3x speedup of native vs strict Python for 65,536 and 262,144 high-repeat and high-diversity cases to warrant investigating a *fully charged* Reader integration. Any false accept, unexpected exception, unverifiable physical bytes, or material slowdown vs Python on high-diversity kills. Even a micro win receives **no product credit** until honest installed full-Reader ABBA including compilation/packaging portability, RSS, 3 OS, exact semantics, corruption, and all release gates.

## Portability/correctness caveats
CPython-only ABI changes cross-platform wheel burden and PyPy compatibility. Native code must not trust unbounded Python objects/metadata. Overflow must fail closed or fall back to original; all known adversarial outcomes must match the unchanged validator. Native oracle may only estimate headroom; no release/version changes.

## Decision
Pending instrument. Preserve negatives. Counterfactual: decide whether Python-loop cost dominates before buying an integrated native reader build.
