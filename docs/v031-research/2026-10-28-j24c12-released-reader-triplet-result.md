# J24C12 — Published vs strict vs ABI3 installed Reader: decisive economic result

Date: **2026-10-28 UTC**. Status: **decisive research/economic negative for 262,144 reference profile; draft only**. No product edit, merge, release, format or version change. This document is subordinate to original immutable receipts and [preregistration](2026-10-28-j24c12-released-reader-triplet-prereg.md).

## Primary question and answer

Does the optional native ABI3 scanner recover strict-admission overhead *relative to actual published CMPCT v0.30.0/r24*, not just relative to the much slower guarded Python Reader?

**Answer:** Much of the strict admission debt is removed, but two independent same-Runner/source/fixture exact-code experiments still trigger the **preregistered material published-floor debt** at 262,144 one-owner references, in **both CPU and wall**. The valid-file Reader session is **~8.85–15.0% slower** than published. **No release or product-economics promotion** is earned. The 65,536-reference profiles are slower relative to published by ~8–9% but their ~1.1–1.3ms absolute penalties do **not** trigger the frozen dual criterion.

These results **do not** compare safety-equivalent versions: the published source fails some hostile-input admissions that the strict/native source preserves. This is economic accounting on valid *identical* r24 archives, not an invitation to remove guards. The code and release remain v0.30.0/r24.

## Immutable source and original GitHub witnesses

| Arm | Actual independent installed source | Reader Git blob |
|---|---|---|
| Published | `main@80c358f8824ec1b20d349c92ed94c898090969b0` | `e716233403dabd0966863c45635e18fa5ac6afb8` |
| Guarded strict | `#630@0a128ff55c7ae0f14c6bdf019a81b40f0d894eff` | `b37b786966ac1506a0439567d4a58eea472d85f8` |
| Guarded optional ABI3 | `#641@a639570c1e9f9b36decae3893265be74a6d185b0` | `9bca5d1047f9c78984b945d7ca90e3149fe429ab` |

Preregistered **before experiment code** at `94db7659d1cc5dc504d2c668086f90e438b4d1c9`. All arms installed into separate noneditable virtualenvs in the *same* Ubuntu 24.04/Python 3.11 hosted runner. Same Builder-independent O215 generator, current fixture-generator blob `a8efaebd9fff8b3203cfd55304d365c309ff394b`. The native candidate must really enter the C scanner; otherwise the experiment fails.

Two source-exact runs with full original assets, three arms, four profiles, 3 ABBA cycles, **72 processes/216 Reader sessions per run**, complete raw phase CPU/wall and resident high-water, six independently expected 16-byte ranges per session, strong complete-read+SHA verification for 4096 refs only:

1. [Original code-head run #40652371278](https://github.com/FCMO-AI/.CMPCT/actions/runs/40652371278), source `ce30703cc7895a89ec61001bedad709c04a7ba99`. All job steps (including source checks, three wheel builds, 72-worker court, independent auditor, upload) **SUCCESS**, but workflow ultimately **CANCELLED on subsequent branch push**. [Original artifact #12799334984](https://github.com/FCMO-AI/.CMPCT/actions/runs/40652371278/artifacts/12799334984), ZIP SHA-256 `b5f84db524ed909d2c80f54a0b56fb82fdbf939b9f19be2b6350251d39889c3f`, original JSON SHA-256 `90b61f078b14330c91db97875ca1a39521962fae9b297c660396b70a64800a0b`.
2. [Exact-head rerun #40652555448](https://github.com/FCMO-AI/.CMPCT/actions/runs/40652555448), source `84d81bfaeb22b955355046fe8ab75d2155647687`, **SUCCESS**, no test/criterion/Reader/source changes except workflow binding the O215 fixture-generator Git blob. [Original artifact #12799664388](https://github.com/FCMO-AI/.CMPCT/actions/runs/40652555448/artifacts/12799664388), ZIP SHA-256 `bbd69afa8e34b20f3b529eaa5bc7baa1cc1e21586da43abdeb4d9e6cf9aa00da`, raw JSON SHA-256 `d416f7c35119ee8551352fdf96afe9cda83c02eb946818fa28575a9b99778035`.

Both independent referee invocations passed and returned `MATERIAL_PUBLISHED_FLOOR_DEBT`. The original ZIPs were also independently extracted; raw receipts, SHA-256s, all 72-worker profiles, six source identities and exact-answer digests were inspected, with all median-of-worker-median economic ratios independently recalculated, not merely transcribed from the PR summary.

## Medians (ms); valid signed RAW fixed-reference archives

| Profile | Run | Published complete | Guarded strict complete | Guarded ABI3 complete | ABI3 minus published / ratio | Preregistered decision |
|---|---|---:|---:|---:|---:|---|
| 4,096/1, includes full verify | #40652371278 | 118.108 | 115.317 | 97.873 | -20.235 / 0.829× | Not a large-profile gate; noisy full read |
| 4,096/1, includes full verify | #40652555448 | 143.930 | 133.952 | 116.687 | -27.243 / 0.811× | Not a large-profile gate; noisy full read |
| 65,536/1 | #40652371278 | 13.411 | 38.394 | 14.494 | +1.083 / 1.081× | Below +3ms gate |
| 65,536/1 | #40652555448 | 13.706 | 39.305 | 14.774 | +1.067 / 1.078× | Below +3ms gate |
| 65,536/256 | #40652371278 | 13.852 | 39.668 | 15.108 | +1.256 / 1.091× | Below +3ms gate |
| 65,536/256 | #40652555448 | 13.949 | 40.490 | 15.205 | +1.256 / 1.090× | Below +3ms gate |
| **262,144/1** | **#40652371278** | **52.990** | **153.853** | **60.941** | **+7.951 / 1.150×** | **Wall and CPU debt** |
| **262,144/1** | **#40652555448** | **54.612** | **156.807** | **59.444** | **+4.833 / 1.088×** | **Wall and CPU debt** |

The CPU median has the same dual-threshold disposition. The second run's 262,144-profile Linux peak high-water: published 28,917,760 B versus native 28,995,584 B (+77,824 B, not a >8MiB RSS veto). First run +90,112 B. Treat VmHWM as coarse high water, not precise incremental allocation.

## Causal decomposition and self-critique

At 262,144 references, first run median **opening**: published **3.871ms**, strict **104.855ms**, native **8.228ms**. Second run: published opening ~4ms, native ~8.8–9.2ms; nearly all *stable* incremental overhead resides in **opening/admission**, not in an established different `read_range()` algorithm. The per-worker native **range** medians have significant scheduler/noise excursions in run 1 (49–67ms), while released read ranges remain near 49ms. Run 2 offers less range noise. The **full-session positive debt discriminator survives both runs**, but one must not attribute its entire 4.8–8.0ms to native scanning or claim it transfers to arbitrary codecs.

Strongest explanation alternatives: residual C list/Python crossing and duplicate in-memory admission work, archive index decoding, cold start/session scheduler contention, and marginal range scheduling noise. Independent tests of these owners are not yet run. Published omission of stronger safety can itself explain the remaining opening advantage; deleting that work violates the safety ratchet.

Counterfactual lesson: initial comparisons #641/#644 used **strict Python** as control, which accurately proved native headroom but could not answer published-floor economics. A direct three-arm valid-source full Reader session would have disclosed the residual baseline gap earlier. **This is a prospective comparator-selection lesson, not an earned change to the normative discovery policy**.

## Honest limits and handoff

This is single-host/single-Python-version, highly repeated four-byte RAW owners, fixed S_CHUNKS, warmed OS page cache, six ranges, no full verification on large profiles. No multi-codec, many real filesystems, full parity corpora, mutable source, extraction, recovery, hardlinks, ZIP interoperability, packaging lifetime, free-threaded ABI, creator CPU, or release-size gate was executed. Not a 15-workload product result. All frozen gates unchanged.

Next **decision-changing** work should first determine the minimum safety-preserving cost of full strict admission in a properly composed Reader, including whether some existing index/physical proofs can be safely reused, rather than threshold tuning or discarding the proven ABI3 speedup. Compare against the published floor *and* guarded strict, separately. PR #641 owner retains implementation authority; #574 owns discovery state; #583/#652 own alternative range representations. Maintain this PR as draft science until broader product gates are earned.
