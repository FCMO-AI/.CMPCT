# J24K12 — authentic installed VZIP BHDR batch transfer: negative product economics

Date: 2026-10-28 UTC. **Research outcome / no product, release, or format promotion.**

## Authority, source and prereg

- Recovered main `80c358f8824ec1b20d349c92ed94c898090969b0`, published v0.30.0 / revision 24, active research base #660 `fed0ac7fff533dc66b56f5e39f7c6f64c4ee6d7a`, guarded Reader owner #653.
- J24K12 prediction recorded at commit `aeff783c6a0ea04d9017bedc54562224c6ae91f0` BEFORE this instrument: **>=1.20× complete Reader-open+Q64 signed STORED-session improvement in both wall and CPU on each hosted OS** for >=512 physical streams. Q1 losses, RSS/package burden and actual ZIP byte equality also matter.
- Original scientific source `3c0432585a7c01d43a731debcad6ff3efeef9c07`; original [Actions #40661616005](https://github.com/FCMO-AI/.CMPCT/actions/runs/40661616005). Ubuntu and macOS science/independent referee PASS. Windows ran all 120 authentic measurements but failed a **receipt source-hash audit** due CRLF-vs-LF, not a Reader correctness failure.
- Append-only [J24K12a repair addendum](2026-10-28-j24k12a-windows-source-normalization-addendum.md) committed **before** instrument fix. Corrected scientific source `ee9afd0b5d3606fe71a2935c93b2fbe2cb19f65b`; [hosted source-exact Actions #40662118843](https://github.com/FCMO-AI/.CMPCT/actions/runs/40662118843) **SUCCESS on Ubuntu, macOS and Windows, each with independent stdlib receipt audit PASS**, 12 scientific cells/120 fresh worker observations per OS, 5/5 forged receipts rejected per OS. The original two-host scientific result is retained, not overwritten.
- Real physical signed r24 Builder archives with 64/512/4096 original ZIP STORED members, full Reader `read`/ `verify`/preflight, exact original ZIP byte truth, Q1 early/tail, Q8 mixed and Q64 tail, per-host unmodified safe #653 vs native projected batch on same archive, both fresh subprocesses, constructor and reader session plus separately measured process startup and native compilation. The source ZIP SHA for the 4,096-stream case is `dacd8c674ec5dcd3c060bc6b38ab6f9d7ba75c5cb6ea77aaffccbd0210d1bfa1` across ALL five independently audited host receipts. The original and repeated macOS artifacts use exactly the **same signed physical CMPCT bytes**: SHA-256 `82064e9a55bdb63fdfb24748bb7f3a915a34f305b42b85e4ae59dcd6ff67d299`.

## Decisive measurement: Reader constructor + 64 late byte-reads + close

| Host / hosted run | Safe original Reader | Projected native batch | Control / native wall | Control / native CPU |
|---|---:|---:|---:|---:|
| Ubuntu original #40661616005 | 300.365 ms | 338.919 ms | **0.886×** | **0.886×** |
| macOS original #40661616005 | 322.267 ms | 357.734 ms | **0.901×** | **0.911×** |
| Ubuntu corrected #40662118843 | 390.992 ms | 423.074 ms | **0.924×** | **0.924×** |
| macOS corrected #40662118843 | 475.726 ms | 430.699 ms | **1.105×** | **1.060×** |
| Windows corrected #40662118843 | 453.989 ms | 472.543 ms | **0.961×** | **0.967×** |

*Higher than 1.00 favors the native batch. Ratios are only within-host/source-run; never infer cross-host absolute speed rankings.*

**Decision: preregistered hypothesis FALSIFIED.** None of the five independent host/run observations reaches the >=1.20× BOTH-AXIS outcome, and the Ubuntu/Windows fully audited source-exact runs clearly favor the safe original Reader. Original macOS also favors baseline.

**Critical contradiction preserved:** corrected macOS flips the sign and favors the native batch by ~10.5% wall and ~6.0% CPU, while original macOS favors baseline by ~11.0% wall, ~9.7% CPU, **on the exact same signed archive and same Python/Reader source**. We do not cherry-pick the winning macOS run, average the contradiction away or claim a universal observed slowdown; uncontrolled hosted-run timing variation and workload sensitivity remain plausible alternative causes. The result nonetheless rejects the stronger prospective >=20% cross-host win. This is a saturation signal for per-query projection, not evidence that *all* native execution approaches lose.

Source compilation alone (not included as a free session operation) took ~0.56s on corrected Ubuntu, ~0.69s corrected macOS and ~8.09s corrected Windows. DLL/wheel distribution, full release suite, product peak RSS, mutating same-inode source, Deflate mode0/mode1/mode2, and release-v0.30 baseline comparison are outside this experiment and NOT credited.

## Exact lossless / adversarial controls

All five independently audited host artifacts contain 12 real signed Reader scenarios and 120 raw worker observations each, totaling **600 raw observations** across two scientific rounds excluding the Windows original unrefereed source receipt. The same signed mutation (reauthenticated one-byte `csize` lie) is rejected by strict `preflight_archive` and both Reader candidates on tested hosts. All legitimate query answers are compared to original ZIP bytes and SHA; no accepted mismatch was observed.

Each hosted second-root audit independently recomputes medians, exact source Git blob hashes, fixture ZIP/original CMPCT SHA and query digests and rejects five falsified receipts. A further out-of-workflow stdlib-only archive audit re-read original *physical artifacts* from all five valid host receipts, verified ZIP CRC and all 64/512/4096 ZIP members against deterministic contents, checked same ZIP bytes across hosts, recomputed raw medians/digests and confirmed 600 legitimate scientific worker observations. The outside audit did **not** separately execute CMPCT or prove arbitrary partial SHA authentication. Windows CPU clocks quantize short samples to zero; those readings were preserved and are not speedup evidence. Long Q64 CPU samples are positive but lower precision.

## Engineering diagnosis, controls and counterfactual

J24K11's ~2.8× model C scan win did not include the **unchanged second Python `range_vzip` loop**, its actual logical-coordinate bookkeeping and fresh per-call tuple projection inside the installed Reader. J24K12 charges both. Even a fast native BHDR scan can lose if the Reader now walks nearly the same payload prefix in Python a second time. The correct baseline is #653's strict, same-mmap Reader, **not** unsafe no-proof reads or merely modeled C/Python predicates. The original Reader is an admissible Pareto winner.

A prospectively recognizable cheaper discriminator would have counted full Reader traversal and fresh projected tuple construction BEFORE treating the model speedup as a likely product improvement, then run one genuine signed Q64 Reader session instead of repeating microbenchmarks. This is a transferable prospective method lesson; it does not justify changing normative discovery policy from a single episode. Discovery STATE belongs to #574 and is not edited.

## Product / science / infrastructure separation

- **Product evidence:** no new product feature or release improvement; `src/`, `native/`, format r24, released v0.30.0, frozen validators, benchmark gates and main unchanged. No merge.
- **Scientific evidence:** installed safe-vs-C batch on authentic signed r24 files. The prospective acceleration failed on the full charged Reader; the small contradictory macOS result is preserved as ambiguity, not promoted.
- **Infrastructure/evidence:** Windows LF source-receipt normalization and deterministic ZIP host metadata repair (J24K12a) landed; original audit failure remains documented, corrected independent three-host court passes.
- **Unmeasured:** Deflate modes, mixed codec owner permutations, in-process source-index mutation/lifetime proof, same-inode concurrent modifications, read/write/recovery full product parity, physical owner SHA authentication on partial reads, official release benchmark and native binary distribution.

## Verdict and next executable route

**Retire default productization of per-query Python-projected BHDR-native scanning.** It adds a second logical traversal and a per-call projection, does not deliver the required full-session win, and inherits C packaging debt. Any renewed candidate must change ownership/execution materially: fuse physical proof and logical coordinate reconstruction into a *single bounded traversal*, or avoid repeated prefix work through an independently justified immutable-source/format proof. Before implementation, reject any design that duplicates the already necessary Python coordinate walk. Coordinate with #653/#660 and avoid overlapping #662's distinct S_CHUNKS fused-index lane. Existing guarded Python source remains the safe control; all negative cases stay permanent. No release authority or performance gate changed.
