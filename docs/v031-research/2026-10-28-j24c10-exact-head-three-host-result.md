# J24C10 — exact-head three-host outcome: strong late-range win, no promotion

Date: 2026-10-28 UTC. **Decision: NOT PROMOTABLE under unchanged preregistration.**
Evidence tier: installed-wheel signed revision-24 synthetic micro/product-operation research, **not** full CMPCT product/release evidence.

## Exact source, controls and immutable inputs

- Candidate: [PR #652](https://github.com/FCMO-AI/.CMPCT/pull/652), code-and-evidence **HEAD `1c2f0b8a0bc5a8b0361e39e7059dfb014af5aa2f`**.
- Parent / strict installed-Reader control: [PR #641](https://github.com/FCMO-AI/.CMPCT/pull/641) `a639570c1e9f9b36decae3893265be74a6d185b0`. Both A/B arms of each hosted experiment use the **same candidate wheel** with original optional ABI3 admission intact. Only the *new* read-time uniform-stride proof is disabled in the control.
- Preregistration: [2026-10-28 J24C10](2026-10-28-j24c10-lazy-uniform-range-prereg.md), commit `3b84eee7e812feae048173b279dc669b0a8de01b`, before product code.
- Hosted [exact-head run #40641105382](https://github.com/FCMO-AI/.CMPCT/actions/runs/40641105382): workflow **SUCCESS**, four jobs SUCCESS including Python 3.10 strict fallback; three native jobs reported 52/52 scoped pytest successes each, 5,960 independent geometry slices each, and independent receipt-referee arithmetic PASS. A green workflow is **not** a favorable scientific gate.
- Archive identity: signed synthetic r24, 65,536 and 262,144 S_CHUNKS references, one physical owner / 256 distinct equal-size owners / nonuniform three-owner control. Same source-wire SHA-256 and exact returned-byte SHA-256 within each paired group. Separate startup and Reader-open/read wall+CPU/RSS samples; six workers per arm/group = **144 fresh subprocesses per host, 432 across hosts**, all on the exact HEAD.
- Original artifacts, with validated archive SHA-256:
  - Ubuntu [#12795571679](https://github.com/FCMO-AI/.CMPCT/actions/runs/40641105382/artifacts/12795571679), `f2e8e07ad7b260303a22dd259e220ddac8a308f5e8b019e171528fe6ed9c99c0`.
  - macOS [#12795721960](https://github.com/FCMO-AI/.CMPCT/actions/runs/40641105382/artifacts/12795721960), `398e79411aca630bc07e01d16cba8ff99bc27c125375dbcb0a222001a5f2053b`.
  - Windows [#12795133663](https://github.com/FCMO-AI/.CMPCT/actions/runs/40641105382/artifacts/12795133663), `140e47ced4e50c34663bc3404a4cc50d26f3896f6422d4310da744e3e0951452`.
- Source-file verifier: `research/j24c10_range_referee.py` on this branch; a separate post-run cross-host raw-archive recalculation verified all 432 workers, source and same-wire/output SHA, 12 medians per host, RSS units, and all original gates. The verifier was **not** a second product execution.

## Results (wall ratio = original strict / new witness; higher is faster)

| Host | Minimum of four late uniform profiles | Early/ragged max-5% debt gate | Late CPU direction | Peak RSS bound | Whole preregistered decision |
|---|---:|---|---|---|---|
| Ubuntu 24.04 | **3.6185x** | PASS | PASS | PASS | **PASS** |
| macOS 14 | **4.2005x** | **FAIL** | PASS | PASS | **FAIL** |
| Windows 2022 | **5.6235x** | PASS | **INCOMPLETE** | PASS | **UNDECIDED CPU; not PASS** |

All twelve late **uniform** profiles clear the preregistered >=2.0x wall threshold across the three hosts. This is real research evidence for a bounded, generically verifiable uniform-stride representation on those signed fixtures.

**Two macOS negative controls fail the unchanged >=1/1.05 wall-ratio floor:**
- 65,536 refs, **one owner, early request**: 20,375 ns strict vs 23,604 ns witness, ratio **0.863201x**, +15.85% observed wall time for witness.
- 262,144 refs, **ragged, late request**: 13,779,667 ns strict vs 14,597,667 ns witness, ratio **0.943964x**, +5.94% observed wall time.

**Windows CPU is not a positive gate.** `time.process_time_ns()` had zero granularity/resolution on the short reads; the witness CPU median is zero for each late uniform profile. The code deliberately returns `cpu_ratio=null` rather than manufacturing a CPU advantage. Windows RSS is genuinely measured through `GetProcessMemoryInfo(PeakWorkingSetSize)`, not silently treated as zero.

RSS gate: the greatest *median group* candidate-minus-control difference was 0.0000 MiB on Linux, 0.265625 MiB on macOS, and 0.166016 MiB on Windows. This is a short-lived child-process peak metric, not full-product memory proof.

## Causal review and strongest self-critique

The exact `read_range()` code runs the uniform proof only if `length and start*2>=size and len(ids)>1`. All early requests have `start=12`, so **neither arm invokes the proof on the failing early control**. On the ragged 262,144-reference fixture, physical lengths repeat `[4,1,2]`; the three constant-time necessary-condition samples are unequal and **neither arm invokes the C proof**. Both controls therefore execute the same range traversal under the same installed package apart from the unused `_uniform_stride` module-global setting. This means the **causal attribution** of the negative to native proof work is *not established*, despite the **valid original preregistered negative gate**. This does NOT authorize erasing it.

The macOS early one-owner six matched wall ratios span approximately 0.566–1.652x (3/6 above 1, 3/6 below); the ragged late pair ratios are below 1 in 5/6 pairs. Cross-process microsecond-scale noise and chronological order are plausible alternative explanations for the former, while the latter still needs an independent robust investigation; neither is assumed away. Median-of-arms is the preregistered statistic and remains unchanged. Never substitute a favorable retrospective paired statistic, a host selection, or a different >5% bound.

The independent Windows CPU insufficiency is a **measurement resolution** problem, not a product speed loss. A follow-up may preregister a new paired high-resolution/aggregated CPU court, with its own decision and fixed Q=1 semantics; it cannot retroactively rescue J24C10.

Other unmeasured product costs: real heterogeneous corpora, full read/extract/recovery, source inode mutation, exported bytes/work, dynamic memory at scale, C extension cross-runtime maintenance, ARM/PyPy/free-threaded interpreters, complete 15-workload performance and release authority. No format/release/version change or merge.

## Counterfactual and next executable decision

A cheaper **pre-host static-path inspection** of the original early/ragged controls could have predicted that they were path-equivalent between arms and hence unusually vulnerable to noise at Q=1. A prospective next oracle should measure those already-known short controls with better CPU/time resolution and vary the representation boundary (e.g. a proof carried by authenticated metadata) rather than growing more C-loop variants or tuning late-query thresholds. The earlier O221b Q4 loss remains controlling for its own different index family. This finding is a local prospective lesson, **not** evidence to change the normative Discovery Engine policy.

**Outcome:** preserve J24C10 as a real *late-range research seed* with explicit failed no-regression debt; no promotion to the Reader owner, no merge, no release, and no claim of portable product speedup. Keep #641's optional installed ABI3 admission as a separate already-measured capability and do not weaken inherited safety or tests.

## Handoff

Re-read live #641/#652/#583 ownership, exact HEAD and CI before new edits. The lowest-cost next discriminator is an **independently preregistered paired same-source, same-wire short-control measurement** that makes early/ragged latency and Windows CPU observable without changing this experiment's thresholds, with possible retirement of the family if no robust bounded gain survives. The broader higher-leverage alternative is a representation/proof redesign that avoids one full read-time traversal and does not export per-member RAM or dependency cost.
