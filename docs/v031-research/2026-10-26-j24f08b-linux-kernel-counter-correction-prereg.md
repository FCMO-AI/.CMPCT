# J24F08b — amend invalid Linux VmHWM monotonicity control using independently observed kernel behavior

Date: 2026-10-26 UTC. Status **NEW PROSPECTIVE INSTRUMENT PREDICTION, COMMITTED BEFORE J24F08b REVISED INSTRUMENT**. The original [J24F08 prereg](2026-10-26-j24f08-linux-vmhwm-prereg.md) and two original negative/invalid hosted runs remain immutable evidence. This note **does not retroactively change their acceptance criteria or turn their failures into PASS**.

## Decisive new evidence behind changed measurement model

- Exact-head original J24F08 scientific run [40417637504](https://github.com/FCMO-AI/.CMPCT/actions/runs/40417637504) FAIL: the original court assumed per-process sampled VmHWM must be monotone and rejected during the second child, before any complete A/B verdict. Its failure message lacked samples.
- Separately instrumented unchanged science on [40417951791](https://github.com/FCMO-AI/.CMPCT/actions/runs/40417951791) FAIL again, this time preserving exact counters: window child 16MiB S_CHUNKS recorded VmHWM stages **[26,255,360; 26,255,360; 42,500,096; 42,475,520] bytes**. After Reader close the reported kernel high-water was **24,576 B lower**, while VmRSS dropped from 42,500,096 to 25,718,784 bytes. Output/correctness was not evaluated past this instrumentation exception. This is a **measurement assumption failure**, not evidence of wrong archive bytes.
- Independent *local Linux* falsifier constructed without CMPCT (anonymous 16MiB, mapped 8MiB, copy, release, independent 12 subprocesses) saw kernel VmHWM decrease in **12/12** subprocesses after memory releases, max observed single reduction **323,584 bytes**. These are local control observations, not a CMPCT host benchmark or Linux standard guarantee. The script/JSON can be preserved separately.

Kernel `VmHWM` is an approximate report of high water. Its displayed snapshots in this environment cannot be treated as strictly monotonic. Therefore, keeping the original monotonicity assertion would repeatedly prevent the exact economic question from running, not raise correctness strength.

## New prospective measurement rule / primary hypothesis unchanged

**Keep ALL** raw phase `VmHWM`, `VmRSS`, `RssAnon` and diagnostic `ru_maxrss`; enforce each snapshot `VmHWM >= VmRSS` and positive required fields. Use the **maximum observed VmHWM among before-open, after-open, after-extract, after-close** as a conservative observed kernel peak, and separately record final counter and maximum backward step for honesty. A counter decrease **must remain a visible observation**; no silent clamping of raw values and no claim of exact unconstrained physical RSS peak.

Keep original source SHA, inputs, 16/64MiB two S_CHUNKS/S_CDC modes, ABBA×2 and 32 fresh separate processes unchanged. Preserve the original preregistered economic decision threshold: **>=32MiB lower median measured max-of-sampled-VmHWM for both 64MiB modes**. If this fails, decision is `NO_CONFIRMED_BOTH_MODE_MEMORY_WIN`. `VmHWM` comparison remains Linux-only research evidence, not official benchmark/release or a proof of OS-global memory dominance.

## Falsification, alternatives, scope

Mark **INVALID** for missing VmHWM/VmRSS, VmHWM below VmRSS within any one snapshot, unsigned output mismatch, identity drift, non-independent process, incomplete ABBA, unexpected subprocess exit or failed 20MiB positive memory probe. Continue to report contradictory timing, inherited J24F06 ru_maxrss invalidity, all RAW write-amplification debt and all safety/publication limitations. A fuller /proc poller could capture transient peaks missed by fixed sample points, but adds overhead and potential perturbation; use only if these 4-point observations cannot decide. Do not weaken anything about the actual Reader, frozen release tests, source integrity or output SHA.

**Counterfactual lesson:** validate a kernel metric's observed semantics before making an intuitively plausible monotonicity property a science precondition. This repair changes a *false harness assumption*, not CMPCT product/evaluator strength.
