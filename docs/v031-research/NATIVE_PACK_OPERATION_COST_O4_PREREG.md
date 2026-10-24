# v0.31 native S_PACK O4 — incremental CPU and kernel read-traffic evidence

Date: 2026-10-24 UTC. **PREREGISTERED BEFORE ADDITIVE O4 INSTRUMENTATION; NO O4 RESULT YET.**
Parent: O3 candidate #322 at `c8f3091e08c068e55a655f29da84571a91ade1d5`, hosted O3 PASS run `40058670450`, artifact `12546009906`. O3 fixed law and result are immutable. O4 is a separately labeled cost-accounting extension, not retroactive O3 measurement or a new mechanism.

## Question

For one input/source-equal Zstd physical S_PACK, does opt-in single-batch Rust C ABI reduce **process CPU work and userspace kernel read() byte traffic** alongside the demonstrated wall-time improvement, without creating an output or source-integrity discrepancy? Is any apparent gain merely elapsed time scheduling/noise?

## Strong controls / prospective design

Use unchanged `tests/native_pack_batch_abi.py` Builder-created >=2-owner, 512 × 768-byte corpus; select one >=256-member Zstd physical PACK, request the *same* byte ranges N={1,16,128,256}, and preserve the seven alternating ABBA blocks and all exact byte/hostile tests. Add additive process-CPU nanoseconds (`time.process_time_ns()`) in the same clock-bound measurement window and Linux `/proc/self/io` `rchar` counters with an explicit note that reading proc itself incurs a small symmetric read cost and that `rchar` is not physical disk I/O. Preserve original wall observations. Record an independent child-process RSS peak as a future gate; **do not** call existing process-global `ru_maxrss` incremental overhead.

Add the release Rust library SHA and Python source context to the JSON custody. Do not adjust O3 data, thresholds, source generation, order, release baseline, byte budgets or evaluator acceptance. Alternate paired CPU and wall samples under the existing labels and preserve full raw arrays. Include the original packet/source fingerprint for disproof.

## Kill/narrow

If batch's CPU measurements do not materially improve even though wall does, classify O3 as scheduler/OS bottleneck or instrumentation discrepancy, not as a universal work-removal win. If CPU improves but rchar does not, the physical I/O-saving claim is unsupported; investigate buffered IO. O3's N=1 negative remains real. If measured rchar changes by only a few bytes, do not inflate a claim. If any output identity, damage rejection or artifact input SHA changes unexpectedly, stop rather than rationalize.

## Limits and unmeasured

`rchar` counts logical read() character transfers, **not filesystem blocks or actual disk traffic**; it cannot prove disk bandwidth or page-cache misses. `process_time_ns` is process CPU, not per-thread or hardware counters. All results remain Linux x86-64, one runner/host, one Zstd pack synthetic family, and no native CLI/Android caller. Real disk I/O, memory incremental, multi-owner admission, platform portability, full end-to-end create/extract and promotion remain unmeasured.

## Concurrency

Same isolated O3 PR #322; PRs #307/#314/#316/#321 remain untouched. Existing source-exact O3 artifact and negative/positive records are preserved; only additional instrumentation is added under new O4 prereg. Scientific credit must be scoped to what these counters actually measure.
