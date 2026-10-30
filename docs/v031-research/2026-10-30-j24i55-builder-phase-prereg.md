# J24I55 — Builder phase-ownership / page-fault fork (prospective)

**Date:** 2026-10-30 UTC. **Status:** PREREGISTERED BEFORE IMPLEMENTATION / UNMEASURED.
**Source parent:** #821 branch `agent/phased3-v031-j24i54-builder-prefix-read-control-20261030` at `444401e36fcd27558c13702ad01c01cfa206cf7f`. **No product, comparator, threshold, release, format, or ABI change.**

## Frame review and question

J24I52–J24I54 repeatedly attacked the same #807 full-matrix binary/library/create red via codec A/B, Builder-context A/A, and READ-only history. Codec was neutral, BUILD-prefix overhead replicated, READ-only >5% AND >3 ms CPU+wall sufficiency failed independent replication. Another READ-prefix variant is saturated. **Change frame from treatment-level timing to ownership of exclusive full-Builder stages and kernel page-fault counters.**

Question: Does a prior real tiny/source/media BUILD history (versus an otherwise equivalent FRESH process) shift downstream binary Builder time principally into its candidate-encoding/worker stage, or into scan/packing/dictionary/index-materialization and/or measured fault pressure?

## Prospective hypotheses / controls

- H1, *encode-owner*: in both reversed-order groups, median BUILD-FRESH **process CPU** and **wall** increase is positive and at least 3 ms, and the *measured stage* `ordered_encode` accounts for >=60% of positive total CPU delta; its own CPU delta is >=3 ms. This identifies a scoped encode-stage candidate, not native codec codegen (already falsified).
- H2, *non-encode owner*: total penalty is positive >=3 ms CPU+wall in both groups, but encode-stage CPU contribution is <=30% and a different exclusive stage or residual dominates. This narrows H1 without deciding host mechanism.
- H3, *not stable / distributed*: contradictory group signs, no material total, stage attribution gaps, significant sham drift, or no single credible component. Record AMBIGUOUS, **not** a successful causal explanation.
- Strong simpler controls: identical Builder source and native library for both labels, same one corpus generated **once** on one runner, one immediate binary warmup in *every child*, two reversed treatment orders, FRESH/FRESH sham, equality of full archive SHA/bytes and source tree fingerprint before/after, raw repeated stage CPU/wall plus self rusage minor/major page faults.
- Alternative causes: warm CPU/thermal state, allocator, page cache, thread scheduling, Python imports and output I/O; stage attribution alone cannot prove a unique cause or explain candidate/base official results. Linux process fault counters cannot by themselves identify cache state.

## Measurement and anticipated decision

Instrument existing source via **research-only wrappers**, not product edits: `scan`, `_build_micro_packs`, `_prepare_deflate_reuse`, `_train_dictionary`, `ordered_worker_pull` (encoding and scheduling), plus remaining build/index/write residual. For each build measure process CPU and wall, and `ru_minflt/ru_majflt` at full call boundaries. Capture stage count, exclusive stage sum, negative residual guard (with small clock resolution tolerance), full output checksum **after** timing, original native SHA, and per-sample raw observations. Keep the unmodified official r24/ZIP gate distinct.

Cheapest material rung: one hosted exact-source phase court using 12 child processes × 3 timed builds, with physically retained sample archive/native and raw JSON. If decision-changing, independently reproduce on another hosted attempt before advancing an owner. If no credible attribution, **retire further short repeated Builder-context microvariants** in favor of full-harness chronology/evaluator correction with stronger evidence.

## Kill / invariant / release boundary

Kill H1 on no stable encode ownership, significant label sham, differing source/archive hashes, inconsistent phases, or broken prereg/source ancestry. No automatic reruns until desired evidence appears. Keep both official #807 FAILs (+16.18%/+14.55%) binding. J24I55 cannot earn product/release credit; no old archive, security/recovery, reader, version or format law changes. Store provider run/job/artifact identities and the scoped result in a later append-only outcome note. If pending, leave decision unlocked.

## BONK / alternative actions

Productize #788/#807? Stronger native verification already has open owner PRs, and unchanged formal gate debt plus Python generation identity preclude blind promotion. New read-only variant? #821 independent replication already narrowed it. Generic new representation? No current oracle headroom justifies sacrificing the product correctness/performance bottleneck; maintain it as separate frontier. Chosen phase ownership test is low-cost, does not duplicate an owner implementation, and can kill this whole timing-explanation family.
