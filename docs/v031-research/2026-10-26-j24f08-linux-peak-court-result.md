# J24F08/J24F08b — Linux kernel peak RSS attribution repaired and measured

Date: 2026-10-26 UTC. **Status: RESULT-BEARING RESEARCH, NOT PRODUCT PROMOTION.** Released CMPCT is still v0.30.0 / physical r24. No CMPCT Reader/Builder/codec/format or release comparator was changed.

## Original hypothesis and authentic provenance

- Primary preregistration `202a13484ee567e3cb6cac97d776bbd08e7f3535` preceded the instrument. Historical J24F04 whole-chunk Reader **blob `8b5910725260e7b4db155ee0b393eb48a42f7efa`**, J24F05 immutable-64KiB-window Reader **blob `41efeb9d3301fc06b1df56ab6bd42d9ee91f6d5e`**. Parent J24F06 #543 exact base `dd01be99ec33e820517f7e54b9beead416b20e19`; J24F05 #540 product parent `1885cb0658cacd34a50d05e45b541ecb76fc8497`.
- Hypothesis: on the exact same physical genuine Builder-independent r24 archive, a fresh separate Linux child `/proc/self/status VmHWM` meter will measure >=32MiB lower 64MiB Reader extraction high water in **both** S_CHUNKS and S_CDC. Four sizes/modes, ABBA×2 fresh processes per mode, same source/candidate installed CMPCT package. Exact whole-file SHA and stored bytes unchanged. No startup included in timed CPU/wall.

## Two initial failures preserve important negative science

1. [Original scientific run #40417637504](https://github.com/FCMO-AI/.CMPCT/actions/runs/40417637504) **FAIL** before completing A/B: incorrectly asserted Linux `VmHWM` snapshots must be monotonic.
2. [Diagnostic run #40417951791](https://github.com/FCMO-AI/.CMPCT/actions/runs/40417951791) **FAIL again**, but retained the kernel contradiction: a 16MiB S_CHUNKS window child reported per-stage VmHWM [26,255,360; 26,255,360; 42,500,096; 42,475,520] bytes, a **24,576-byte backward step** after extraction. The kernel's reported `VmRSS` fell 42,500,096→25,718,784. These runs had no complete decision-grade A/B; do not relabel them successful. A differently rooted 12-process local memory release falsifier independently observed backward VmHWM movements; this is a *meter-model error*, not a Reader corruption finding.
3. **Before repair**, independent [J24F08b prereg](2026-10-26-j24f08b-linux-kernel-counter-correction-prereg.md) `edc2cbc19dcf13659d2a275db2e7736ac693e936` fixed the prospective method. Preserve raw phase readings and any decreases; use **maximum of four sampled kernel VmHWM stages** as a conservative observed high-water, not final-stage VmHWM, while retaining same-input/source and original >=32MiB discriminator. This does not weaken physical SHA or the frozen official benchmarks.

## Decision-changing hosted result

[Result-bearing scientific workflow #40418306191](https://github.com/FCMO-AI/.CMPCT/actions/runs/40418306191) on **exact science HEAD `519a978eb84fd8e2fa9edf716579fad8b7bb0620`: SUCCESS**. Original [artifact #12696345890](https://github.com/FCMO-AI/.CMPCT/actions/runs/40418306191/artifacts/12696345890) SHA-256 of ZIP from GitHub API `efd3d795c517de95cd937f7e40c044bb9658410b0a7042703ae5935fb616da1a`. Provenance: authentic 16/64MiB RAW+1KiB, S_CHUNKS & S_CDC, **32** independently exec'd Reader extracts, complete per-trial CPU, wall, `VmHWM/VmRSS` and output SHA, separate 20MiB anonymous-residency positive meter test (+20,975,616 B).

| Linux case | Old whole-copy median observed VmHWM | New 64KiB-window median | Difference | Ratio |
|---|---:|---:|---:|---:|
| 16MiB S_CHUNKS | 59,172,864 B | 42,336,256 B | **−16,836,608 B** | 0.7155× |
| 16MiB S_CDC | 59,187,200 B | 42,219,520 B | **−16,967,680 B** | 0.7133× |
| 64MiB S_CHUNKS | 159,797,248 B | 92,620,800 B | **−67,176,448 B** | 0.5796× |
| 64MiB S_CDC | 159,815,680 B | 92,542,976 B | **−67,272,704 B** | 0.5791× |

**Decision: `VMHWM_MEMORY_WIN_BOTH_R24_MODES`.** All archive output hashes and sizes matched; positive RSS meter test passed. The original Linux `ru_maxrss` showed exactly zero delta across the same arms (16MiB 122,176KiB; 64MiB 351,920KiB for S_CHUNKS), confirming its inherited-peak non-discriminating character in this setup.

**CPU/wall at 64MiB were near parity only in this single hosted Linux run:** S_CHUNKS wall whole 65.363ms vs window 65.242ms (−0.18%); S_CDC 65.729ms vs 65.513ms (−0.33%). At 16MiB, window was +0.28%/+0.77% slower. Earlier J24F06 hosted Linux runs had **contradictory** results (~15% slower versus near parity), so **do not claim a universal speed improvement or cleared performance release gate**. Original 2 vs 257/1025 stage syscall amplification remains. Linux process RSS gain aligns with macOS inherited ~67MB advantage but is one synthetic workload / one Linux runner.

## Independent falsifier and audit

The original downloaded GitHub artifact was audited locally by a **separately coded standard-library Python auditor** (not importing the scientist or Builder), which verified all 32 child PIDs, exact Reader blobs, input/output SHA and sizes, phase metrics, backward step preservation, four 8-trial ABBA sequences, all raw medians/deltas/ratios, original prospective 32MiB decision and process-memory positive control: **611 checks PASS, 0 discrepancy**. To make future audits reproducible, `research/j24f08_independent_receipt_audit.py` has been added, and dedicated CI re-runs the same science and retains independent audit JSON on its own final HEAD; the final-head CI result must be checked rather than assumed from earlier success.

## Deliberate evidence boundaries / outstanding product debt

- Original `/proc/self/status:VmHWM` reporting can drop after a memory release: this report uses max-of-four **sampled** counters rather than pretending any final snapshot equals a global exact RSS peak. It is Linux-only, not per-page fault attribution. `ru_maxrss` remains a diagnostic with a known highwater inheritance defect (historical O92c #450/O95 #453).
- A single 64MiB synthetic RAW physical chunk per case, not real-world corpus or full mixed-codec extraction. Does not reduce archive bytes; no compression gain or new generic Reader format capability.
- The **critical integrity defects remain separate owners:** [#528](https://github.com/FCMO-AI/.CMPCT/issues/528) stage-path inode substitution after SHA, [#460](https://github.com/FCMO-AI/.CMPCT/issues/460) same-inode mmap truncation SIGBUS, [#535](https://github.com/FCMO-AI/.CMPCT/issues/535) Windows os.fchmod availability (J24F07 #544 owns composition). This research does NOT repair them.
- PR #549 is research-only and stacked on #543; PR #540 remains the Reader product owner. No `docs/discovery/STATE.json` write since it is a staleable cache. No merge, version, format or release authority.

## Highest-leverage handoff

A real Linux memory advantage is established for the studied 64MiB RAW chunks; stop expending scientific runs on inherited `ru_maxrss`. Product owners should prioritize authentic composed integrity: reader immutable windows **and** inode-verified publication #528, then source lifetime #460, and complete source-exact General Tests/full parity including Windows. If meaningful timing regression returns on controlled hosts, reduce Python syscall crossing while keeping each 64KiB authenticated byte object identical to the emitted byte object. The scientific question changed from ambiguous Linux peak to **positive bounded-window memory evidence with unresolved temporal and publication debt**.

**Counterfactual:** historical O95 Linux VmHWM knowledge could have prevented the first wrong-memory claim; a simple independent probe of monotonicity would have prevented the two J24F08 harness-only red runs. Transferable prospective lesson; no global discovery policy modified.
