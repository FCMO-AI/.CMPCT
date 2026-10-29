# J24G48 — authentic revision-24 Reader metadata rekey cost

Date: 2026-10-29  
Evidence status: **HOSTED RAW PRODUCT-SOURCE MEASUREMENT; RESEARCH ONLY; NO RELEASE CREDIT**  
Research PR: #775, independent child of correctness owner #773

## Primary question and frozen prospective decision

Does #773's metadata-identity repair impose a material extra Reader-open/CPU/RSS cost on real signed archives with lexical insertion? The prospective [preregistration](2026-10-29-j24g48-physical-rekey-economics-prereg.md) preceded the instrument and CI. The defective #770 source is a **semantic negative**, not a fair product-performance competitor. A >20 ms **and** >10% added wall time at 2,048 files, or >5 MiB additional RSS, would mark research debt for structural profiling; these are NOT release thresholds.

## Source, runner and physical custody

- Corrected Reader/Writer source: `893aac3f6b7b54e89d71af6970405ff5fc71aef7` (#773).
- Defective original Reader source: `78b9dd2d148350898c95a0cdbeefe760de2e567e` (#770).
- First complete substantive run: [Actions #40931290242](https://github.com/FCMO-AI/.CMPCT/actions/runs/40931290242), artifact [#12923166188](https://github.com/FCMO-AI/.CMPCT/actions/runs/40931290242/artifacts/12923166188).
- Artifact ZIP provider SHA-256: `c7ec358a24e373db6fc7e4c04fac77a0c41ee73f1142d49df69f83f1fe7ff117`.
- Ubuntu 24.04 Python 3.11; wheel-owned compiled Rust codec SHA copied identically into both pinned source trees solely for source import. The experiment checks original source Git SHA, module path/content and physical artifact SHA in every subprocess.
- Real Builder produced signed r24 originals (256 or 2,048 members), each copied once and appended via real Writer with lexically early `0000-inserted.bin`. Binary Linux xattrs were physically written and independently read back before Builder. Both Readers read exactly the **same bytes**.
- 7 cycles, alternating ABBA source order and original/journal order; 14 measurements per source/generation/case; **224 independent subprocess observations** across four fixtures. Import time and Reader lifecycle with metadata map are separated. Repeated wall, CPU, process VmHWM and SHA are retained in `raw-results.json` of the provider artifact.
- This is fresh-process but NOT a cold-disk/page-cache benchmark. Source-import and memory mapping are not proof of full Reader extract cost.

## Observed measurements, exact-head hosted raw result

Times below are medians of 14 wall measurements per cell, in milliseconds. Original archive is a no-rekey control; shifted is the actual lexical insertion where path ordinals change.

| Real fixture | Original defective | Original repaired | Shifted defective | Shifted repaired | Repair extra on shifted | Changed attribution |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 256 files; xattrs 1/32 | 0.703 | 0.714 | 0.760 | 0.886 | **+0.126 ms** | defective wrong; repaired correct |
| 2,048; no xattrs | 3.759 | 3.731 | 3.925 | 4.933 | **+1.008 ms** | both correct (no xattrs to rebind) |
| 2,048; xattrs 1/32 | 3.798 | 3.803 | 3.986 | 4.976 | **+0.989 ms** | defective wrong; repaired correct |
| 2,048; xattrs 1/2 | 4.956 | 4.963 | 5.211 | 6.619 | **+1.408 ms** | defective wrong; repaired correct |

Selected 2,048-file shifted CPU medians: defective/repaired no xattrs 3.922/4.930 ms; sparse 3.983/4.972 ms; dense 5.208/6.613 ms. Process peak VmHWM in each respective case was 33,222,656 B, 34,967,552 B and 37,941,248 B, **identical between source versions at this coarse level**. No claim of lower memory or absence of heap churn follows from that equality.

The same-runner apparent added time is **~0.99–1.41 ms** at 2,048 files (+~25–27% relative to the wrong implementation's 3.9–5.2 ms). This is not an equivalent-semantics speed regression claim. Difference-in-differences adjusted by original-open control is ~1.04 / 0.98 / 1.40 ms for no/sparse/dense metadata respectively.

## Falsification, negatives, competing explanations

The **expected negative** reproduced: #770 maps an existing owner's xattrs to the inserted lexical predecessor even though physical content integrity passes; #773 correctly binds all tested source xattrs to their original path. The stable original archive gave equal attribution under both. No selection was made after seeing a favorable subset.

The first hosted instrument attempt, [#40930942366](https://github.com/FCMO-AI/.CMPCT/actions/runs/40930942366), failed before testing because an unbuilt Git source checkout lacked its wheel-owned `cmpct_core` codec library. Both source trees were subsequently furnished identical hashed copies of the compiled library. That is an infrastructure correction, not product improvement.

The physical result does **not** settle runtime at 10k+ members; the abstract helper court #773 already observed 18.6–40.7 ms at 10k, and this case is only 2,048. Other contributors include index sorting, import cost, Python allocation, page cache and sparse-density effects. The comparison intentionally uses an invalid prior version and cannot be substituted for official released-base vs candidate parity.

## Decision and counterfactual replay

**Scoped decision:** correction still deserves integration priority; its measured incremental cost on 2,048-file physical r24 data does **not** cross the prospective absolute >20 ms threshold. No speculative extra metadata micro-optimization is justified by this result alone. Larger corpus, inherited general tests, parent #773 integration, full release parity and real peak-memory measurements remain required before product promotion.

**Counterfactual:** the earlier 10k abstract helper number looked substantial but could not establish an archive-scale product regression. The cheapest real signed Reader same-input court would have distinguished the actual 2k cost and semantic negative earlier. The transferable method is to benchmark true lifecycle inputs and preserve semantic disqualification of the old control. This single episode does not justify editing Discovery policy.

## Independent referee boundary

The first table originates in successful run #40931290242, not a separately downloaded audited ZIP. A new source-free referee `research/j24g48/audit_raw_cost.py` was subsequently landed and executed against an **independent repeated hosted run on a different source HEAD**, as described below; it does not retroactively claim to have independently audited the first artifact. The frozen earlier measurement remains traceable at its original HEAD.

## Product/release handoff

- Owner #773 remains OPEN/DRAFT and the canonical repair locus. J24G48 modifies only research documents, instrument, independent referee and workflow; no reader/writer code, format, benchmark gate, evaluator, version, discovery state, merge or release.
- General tests, broad portability/Windows, privileged UID/GID, exact sparse verification, collision/race safety, cold page-cache, real 10k workloads and full archive economics remain inherited debt.
- Next highest-leverage action: if final referee passes, hand raw evidence to #773 owner, prioritize correctness integration rather than further 2k micro-tuning, then require canonical full-product parity. If large-scale physical costs emerge, isolate rekey vs index sorting instead of gardening thresholds.

## Second hosted court — independent raw referee, and evidence of run-to-run variation

[Actions #40932031052](https://github.com/FCMO-AI/.CMPCT/actions/runs/40932031052) at source HEAD `fbf03c74e235c1e59b37d9b3fb27f8dae99e78aa` completed **SUCCESS** including the new independent source-free auditor. This HEAD changes only research/instrument/CI, not either tested Reader source. The original measured heads of defective and repaired Readers remain byte-identical to the first hosted court. [Original second-run artifact #12922129850](https://github.com/FCMO-AI/.CMPCT/actions/runs/40932031052/artifacts/12922129850) has provider ZIP SHA-256 `d8a35b5b95b0f86765d5a38a4e53f56bfc46c6c0f6bb62280a79fa097fb46ac6` (2,687,037 B).

The referee checked all 224 raw observations, 16 groups × 14 measurements, all original/journal physical SHA-256 digests and prefix-byte custody, source identities, 7-cycle distribution, expected xattr counts, signed baseline negative, repaired identity preservation, process RSS records and recomputed medians **without importing CMPCT**.

| Physical fixture | Shifted defective median | Shifted repaired median | Added wall | Diff-in-diff vs original | Defective semantic control |
| --- | ---: | ---: | ---: | ---: | --- |
| 256 files, 1/32 xattrs | 0.453 ms | 0.528 ms | +0.075 ms | +0.076 ms | wrong |
| 2,048, no xattrs | 2.254 ms | 2.752 ms | +0.497 ms | +0.504 ms | not applicable |
| 2,048, 1/32 xattrs | 2.289 ms | 2.821 ms | +0.532 ms | +0.539 ms | wrong |
| 2,048, 1/2 xattrs | 2.967 ms | 3.740 ms | +0.773 ms | +0.755 ms | wrong |

**Contradiction/uncertainty preserved:** these second-run wall medians are materially *lower* than the first run's 0.99–1.41 ms added on 2,048 members, despite identical tested Reader source and nominal case families. The physically generated archive bytes are guaranteed identical *within* each run and between candidates; they are **not claimed identical across runs** because non-reproducible source timestamps and host environment may vary. Do not pool the two campaigns into a fictitiously precise microsecond conclusion. Both hosted observations nevertheless support the same bounded decision for the tested scale: roughly **0.5–1.4 ms additional Reader open+metadata-map**, below the prospective absolute 20-ms research triage threshold, with wrong-Reader metadata misbinding independently established and corrected-Reader path identity preserved.

The second referee verifies its own measurements; no third-party download/re-run of either ZIP is claimed. Both results leave 10k-file physical scaling, cold cache, full extraction/CPU/RSS, portability and release parity unresolved.
