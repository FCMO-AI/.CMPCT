# O7 — source-exact authenticated Reader replay: measured result and open debt

**Date:** 2026-10-24 UTC. **Candidate:** draft PR #358, stacked on #355 at `5f6c1462e30686687ea13cc2507c9702f13df116`. **On-disk:** revision 24 unchanged; **released floor:** v0.30.0. **No merge/release authority.**

## Decision and baseline
O6b independently measured the ordinary Reader's signed-journal open path against an equivalent final checkpoint: up to 72.56x ratio for 4096 operations in its inherited run, despite indexed preflight being efficient. This ratio is not a historical Reader vs candidate comparison.

O7 preregistration was locked in commit `33dfdbdf282c007431d420ba86ec75edc95bed99`, **before** the actual Reader edit in `971334ab1c89d07ab6f692344f173801d14efbc9`. The change replaces the Reader's private signed journal put/del/rename loops with a call to the unchanged strict validator's positional transaction replay. Each generation is still sorted separately; checkpoints still avoid importing validator. This is owner reuse, not another independent indexing implementation.

## Exact-source experiment — observed
Historical Reader source Git blob: `604f6a81bf03bd97a4defb4ad7a1393d01ed491f`; candidate Reader blob: `6de2edcf5b804e224a1c651ca77361af5667dc2e`; identical validator owner blob: `2bb3f53c918ae93efb105364e2b93ea46aeca034`. Both Reader classes were executed on the **same host, installed dependencies and independently Builder-constructed, SHA-committed revision-24 files**. A/B B/A source-exact alternation, actual Python Reader constructor only; read payloads were verified *after* timing. Five ABBA rounds per size, 10 observations per implementation/input type, checkpoint held as same-logical-result control.

[O7 first result run 40101351497](https://github.com/FCMO-AI/.CMPCT/actions/runs/40101351497), Ubuntu job **SUCCESS**. The old/new delta Reader constructor medians:

| Signed rename operations | Historical Reader | Shared Reader | Observed speedup |
|---:|---:|---:|---:|
| 512 | 3.8773675 ms | 1.2391750 ms | **3.13x** |
| 2048 | 53.3455500 ms | 5.0060430 ms | **10.66x** |
| 4096 | 240.8704180 ms | 10.1396565 ms | **23.76x** |

At 4096 the historical checkpoint open was **4.022276 ms** versus candidate **4.2122265 ms**; that 0.190-ms delta is within the declared 5%-AND-3ms timing envelope and cannot be claimed as a significant slowdown or speedup. Same-runner ratio of signed delta/checkpoint changed from approximately **59.88x historical** to **2.41x candidate**, but the correct central result is the exact-source **23.76x** delta-open A/B. Bytes of both archive controls, final logical indexes and sampled reconstructions matched. Receipt SHA-256: `55642dedeb975554d21be502e6d70eb3bce76c639d43e64e601e29c763e86820`. Raw per-sample CPU/wall, archive SHA256/bytes and independent `tracemalloc` allocation probe are in the run's uploaded artifacts.

**Independent correctness:** Ubuntu **18/18 PASS** and macOS **18/18 PASS** in that run. This includes unchanged O1 strict replay oracle with 10,000 deterministic randomized sequences and new genuine on-disk Reader cases (64/512/2048 operations, 2+ generations with transient name collisions, signed malformed unknown-op refusal, incomplete unsigned-tail recovery). Native/Win32/APFS inherited source is unchanged; separate global checks remain required.

## Negative/uncertain evidence — do not hide
- First and second Windows focused workflow executions stopped at the source-custody step **before installing CMPCT**. The originally compared Python strings were sensitive to Windows stdout/source newline transformations. No Windows product result was earned by these runs. The later CI oracle checks the cryptographic Git blob of the reviewed Reader (`6de2...`) on **every** host, while independently checking prefix/suffix unchanged segments on Unix and the one narrow replay segment on all hosts. This is a custody-method change, **not** relaxed Reader assertions or benchmarks. Windows result on the latest exact head must be rechecked.
- The historical Reader would ignore unrecognized authenticated operation tags; shared strict replay **rejects** these (the same as preflight). This is a conservative malformed-input acceptance change, not equivalence of every malformed archive. Check older committed fallback/recovery on corrupted but signed generation before promotion.
- The candidate's lazy first-use validator import is warmed by the authentic case builder in O7 A/B; **true fresh-process cold one-off signed open remains unmeasured**. Python temporary allocation in the receipt is not process peak RSS. No CPU/RSS/create/extract/full official release parity claim outside the signed journal Reader-open measurement.
- Different-host historic O6b runs reported different absolute wall times; only same-runner source-exact O7 medians support the new A/B speedup. Never combine unmatched hosted medians.
- PR #356 independently modifies `reader.py` extraction symlink admission; O7's `_index_from_footer` work is nonoverlapping conceptually but **has not been composition-proven** on one exact head. Parent #345/#355 and issue #265 retain separate release/safety debt.

## Counterfactual and mechanism disposition
A source-level comparison of strict preflight `_apply_delta` versus Reader `_index_from_footer` was enough to predict duplicate linear work without another discovery family. The cheapest decisive product discriminator was a single source-exact Reader-vs-Reader A/B on the **same authenticated delta and checkpoint**, not another preflight benchmark or new index algorithm. The correct shared owner preserves proven operation semantics while reducing duplicated maintenance. This observation does not justify modifying the Discovery Engine itself.

**Disposition:** indexed Reader replay is **ADVANCED / measured positive in the focused court**; full-product dominance, adverse failure acceptance, memory and release remain **UNPROVEN**. Preserve the old Reader source and actual negative/positive CI records.

## Highest-leverage next executable
1. Inspect latest exact-head O7 Windows court; if red, distinguish Git source transport vs actual product failure using pinned blob and raw job logs. Never count checkout-custody failures as product regressions.
2. Reconcile O7 with #356 and current #345/#355 owner heads without blind overwrites. Execute original signed prewrite symlink, recovery, native, host namespace, source-exact Reader and general tests on the same composite HEAD.
3. Run a fresh-process cold open and in-call RSS/CPU court. Obtain **substantive** official release parity, not a skipped administrative success, before any promotion. Preserve draft/revision-24 format until earned.
