# O83 — Exact-source O64→O80 Builder economics: hosted direct measurement

**Date:** 2026-10-25 UTC. **Disposition:** `BOUNDED_BYTE_PARITY_CONFIRMED; NO_MATERIAL_HOSTED_CREATE_DEBT_OBSERVED; RELEASE_GATE_UNMEASURED`. No code or format modifications, no merge/release credit.

## Authority, preregistration and source identities
The prospective question, controls and disproof conditions were committed **before** the instrument/measurement in [O83 preregistration](2026-10-25-o83-builder-union-economics-prereg.md) at `b81a98d92b3dbf6aba309c873bf14a8c8d4f2c66`. Exact base is O64 PR #419 `9de342226bfbce3690ef1c8cabb1fdf229dbf003`, Builder blob `b02a30d4ad1b26ea8eea49e11159113caebd6006`. Exact candidate is O80 PR #437 `4d65f1bcbc68f1ad770e706197ece8355dd10637`, Builder blob `37833f09dee4671b8ca6f3f3690a7fdebfbc4c70`. This branch modifies only preregistration, research-only bench and CI. Git verifies both source heads/Builder blobs, and two installed package source copies **outside checkout**. Reader/codec/Writer/native/packaging and frozen benchmarks match the ancestor/candidate comparison; no evaluator/source patch is part of either engine.

## Authenticated direct evidence
Two **independent genuine installed same-tree runs**, one push-triggered and one PR-triggered at executable head `c6aa6e85cf5c980ea6d4f176bb53043dd8d63ada`:

- [Actions 40196832604](https://github.com/FCMO-AI/.CMPCT/actions/runs/40196832604): **SUCCESS**, [raw artifact 12600337263](https://github.com/FCMO-AI/.CMPCT/actions/runs/40196832604/artifacts/12600337263).
- [Actions 40196897405](https://github.com/FCMO-AI/.CMPCT/actions/runs/40196897405): **SUCCESS**, [raw artifact 12599693098](https://github.com/FCMO-AI/.CMPCT/actions/runs/40196897405/artifacts/12599693098).

Each execution ran **30 actual fresh installed-Builder processes**: 3 physical source shapes × 2 independently installed exact-source engines × 5 paired repetitions/arm, alternating AB/BA, Ubuntu 24.04 CPython 3.11. Each shape was generated **once within its run**, physically shared between both arms. The full per-entry tree fingerprint (path, lstat mode/inode/link count/mtime, source bytes SHA, xattr values, symlink targets) was checked before and after every build. No source mutation occurred. Build wall and process CPU exclude process startup/install; RSS is whole-process peak. The instrument independently verifies the generated archive and extracts it to prove regular contents, symlink targets, physical regular hardlink equivalence and xattr restoration.

### Complete stored bytes and both-run medians

| Shape / original input | Run | O64 archive B | O80 archive B | Byte delta | O64 create wall ms | O80 create wall ms | O80 wall delta | O64 create CPU ms | O80 create CPU ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 192 tiny regular files | push | 10,185 | 10,185 | **0** | 10.187883 | 10.197802 | +0.097% | 10.183096 | 10.193666 |
| 192 tiny regular files | PR | 10,201 | 10,201 | **0** | 10.236385 | 10.061959 | −1.704% | 10.230591 | 10.057749 |
| 64 xattr-bearing regular files | push | 14,462 | 14,462 | **0** | 5.863057 | 5.882714 | +0.335% | 5.858583 | 5.877900 |
| 64 xattr-bearing regular files | PR | 14,462 | 14,462 | **0** | 5.781470 | 5.830933 | +0.856% | 5.777291 | 5.827154 |
| 96 regular + 64 physically out-of-tree-linked symlinks | push | 14,430 | 14,430 | **0** | 8.247590 | 8.277026 | +0.357% | 8.242989 | 8.271993 |
| 96 regular + 64 physically out-of-tree-linked symlinks | PR | 14,444 | 14,444 | **0** | 8.226200 | 8.151441 | −0.909% | 8.221973 | 8.146923 |

**Full archive SHA-256 identity also matched across all ten outputs within each source shape and run.** Source timestamps differ between the two *independently generated* CI runs, hence differing tiny/symlink byte totals between runs are expected and are **never compared as one source fingerprint**. Every within-run A/B uses exactly the same physical tree; both engines reconstruct all tested members. Actual 64 xattr values and 64 physical symlink inodes linked *outside* the selected root were asserted at experiment construction. This is a genuine-positive correctness control, not a synthetic stand-in.

Measured whole-process peak RSS stayed close in this bounded experiment: push medians O64→O80 (KiB) tiny 25,236→25,268; xattr 24,564→24,536; symlinks 24,944→25,128. PR medians tiny 25,260→25,300; xattr 24,488→24,548; symlinks 25,052→25,092. These are **total peaks**, not allocated-delta attribution. Verify+extract medians (ms) push O64→O80: 12.134849→11.933503, 5.115011→5.083392, 10.237275→10.234500; PR: 11.992246→11.884263, 4.998434→5.050251, 10.258808→10.175593. Those timings are descriptive, not noise-controlled Reader wins.

## Decision, negative evidence and limits
**No observed O80 creation regression clears both the documented +5% and +3ms dimensions in either independent run.** Absolute per-shape create wall differences are at most 0.175ms on this small family. The results support the *scoped* conclusion that selected successful-path O80 guards can coexist economically with O64; they do **not** prove equivalence across large real corpora, more complex xattr namespaces, wide symlink graphs, Windows NTFS, macOS, cold-cache pressure or all production modes.

Two strong alternative explanations remain: (a) small test cases and CI noise may obscure scaling/rare-path regressions; (b) the comparison measures O80 **relative to O64**, which already pays O47/O48/NTFS metadata costs, not relative to shipping v0.30.0. A zero-byte result on three relatively small controlled trees is not the official release-parity matrix. No claim of statistically significant speedup or broader product efficiency gain follows.

This independent court must not be used to promote O80; official `zip-parity.yml` direct-base ABBA size/timing, inherited CI custody, broader semantics and full release criteria remain outstanding. O52 mutable source, O75 atomic output and O81 output alias are distinct ongoing work and cannot be considered fixed by this measurement.

## Counterfactual and next executable decision
The cheap winning discriminator was direct base/candidate **same-tree** archived SHA and paired create wall/CPU rather than static claims that a small Python diff is free; it resolved whether a fresh full benchmark was justified before merging. Generalizes prospectively to additive Builder guards, but is not yet evidence of an improved Discovery Engine policy and does not authorize policy edits.

**Next:** compose this O80 candidate with O75/O81 only after their actual product fixes pass; then invoke the official direct-base release-parity gate on exact combined source. Do not spend additional activations on nearby symlink/xattr micro-variants without a scaling red or new regime. Promote only on a complete approved product result.


## Two additional exact-head independent executions — same scientific outcome

The documentary HEAD `fae93f6330416c30c1d30b226a8355c099466753` (identical original O64 and O80 Builder/instrument/workflow bytes) additionally obtained two independent SUCCESS hosted courts: [PR run #40197257827](https://github.com/FCMO-AI/.CMPCT/actions/runs/40197257827) and [push run #40197252146](https://github.com/FCMO-AI/.CMPCT/actions/runs/40197252146). **Four total successful courts × 30 fresh installed process observations = 120 actual source-exact product-process observations** across 12 run/scenario comparisons. Every same-run A/B has **0 full archive bytes delta and exact full artifact SHA**, authentic xattr and out-of-root symlink-hardlink support, and source fingerprint/read/verify/extract checks green. The latest doc changes are a readout, **not additional instrument changes**.

Additional PR-run O64→O80 create wall medians (ms): tiny `10.274187→10.142139`, xattrs `5.785682→5.801351`, linked symlinks `8.116677→8.223036`; archive bytes matched `10,181`, `14,462`, `14,484`, respectively. Additional push-run medians: tiny `5.810643→5.757534`, xattrs `3.510252→3.435518`, symlinks `4.816274→4.851057`; archive bytes matched `9,999`, `14,430`, `14,362`. Raw individual observations and descriptive RSS/CPU/verification costs are uploaded by each Actions workflow, not reconstructed from summary. Distinct runs have independently generated source timestamps, therefore cross-run absolute size variation must not be conflated with a same-input difference; within each run the physical source was identical and fingerprinted.

**Cross-run caution:** the final push run's baseline tiny-file timing (~5.81ms) differs materially from the final PR run (~10.27ms) despite equal shape; this is runner/process/environment variability and makes pooling absolute timings inappropriate. All run-specific paired O64/O80 differences are tiny, well below both release slowdown dimensions. This is useful negative evidence against claiming a measurable speedup. No full-product release parity, platform portability economics, large-scale asymptotic guarantee, or candidate-vs-shipping v0.30 win is established.
