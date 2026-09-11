# v0.30 R4 integrated tabular-owner result — 2026-09-11

Status: **falsified for productization in its current form; useful mechanism evidence preserved**.

This result evaluates the sparse tabular admission + authenticated binary owner as one end-to-end research archive across the frozen 15-workload Genesis matrix. The lane is diagnostic only. It changes no shipping format, selector, canonical version, comparator, ONE evidence, or release gate.

## Exact evidence

- branch line: `agent/v030-authoritative-integration`
- integrated recovery workflow run: `34653003573`
- job: `103439197371`
- evidence head: `e96c320adce70bef926cc11562d8ae81018105bd`
- artifact: `10285266582`
- receipt schema: `cmpct-v030-r4-tabular-integrated-archive-v1`
- frozen accepted v0.29 Analytics comparator: **6,135,172 B**

The workflow completed successfully as an evidence/integrity lane. That does not imply the research hypothesis passed.

## Matrix result

Across all 15 workloads:

| metric | ordinary v0.30 baseline | integrated R4 candidate | delta |
|---|---:|---:|---:|
| authenticated stored bytes | 150,060,545 | 147,905,238 | **-2,155,307 B** |
| parent-process creation CPU | 34.3695 s | 56.0155 s | +21.6460 s |
| extract CPU | 5.6274 s | 6.2869 s | +0.6595 s |

Exactly one relation was admitted, in Analytics. The other 14 workloads fall through to ordinary v0.30 and are byte-identical to their baseline in this experiment. There are zero non-Analytics byte regressions.

The parent-CPU row above is the experiment's recorded metric, **not total compute**: separate post-Genesis attribution has demonstrated that v0.30 can spend substantial CPU in descendant processes that `time.process_time()` does not charge. It is retained for receipt fidelity but must not be used as total process-tree cost.

## Analytics result

Frozen workload: `neutral_hostile_v1/04_analytics_and_database`

| metric | baseline v0.30 | integrated R4 | accepted v0.29 |
|---|---:|---:|---:|
| logical bytes | 31,268,131 | 31,268,131 | same input |
| authenticated stored bytes | 10,392,496 | **8,237,189** | **6,135,172** |
| R4 saving vs v0.30 | — | **2,155,307 B (20.739%)** | — |
| remaining deficit vs v0.29 | — | **+2,102,017 B (+34.262%)** | — |
| single-run create wall | 135.3471 s | 37.4938 s | not remeasured in this lane |

The R4 mechanism therefore recovers a large and real fraction of the frozen v0.30 deficit while also avoiding much of the expensive existing portfolio path in this single run. But the preregistered density requirement was strict: the integrated candidate had to beat the accepted same-input v0.29 artifact. It does not. `supported_for_productization_design=false` is therefore the correct result.

Do not convert the single-run wall reduction into a release speed claim. Timing was not repeated, total descendant CPU was not charged by this receipt, and the research wrapper changes which bytes reach the ordinary v0.30 base build.

## Discovery economics

The admitted relation is `events.csv <-> events.jsonl`.

- cheap observation: **57,349 B**, about **0.1834%** of Analytics logical bytes;
- observation CPU: about `0.0007 s`;
- exact proof: **20,546,932 B**, about **65.717%** of Analytics logical bytes;
- exact-proof CPU in the parent: about `0.303 s`;
- admitted relations: exactly 1.

This is a mixed result. The observation gate is genuinely sparse and cheap, but the exact proof is not sparse inside the positive workload: it reads nearly two thirds of Analytics. The current mechanism therefore demonstrates cheap *candidate discovery*, not cheap end-to-end proof.

That matters for the project's marginal-information-yield law. A future version should either prove the same relation incrementally/from already-produced summaries, or demand enough predicted physical benefit to justify a proof touching ~20.5 MB.

## Physical representation

Integrated Analytics bundle:

- `base.cmpct`: 7,945,100 B
- `owner.tcol`: 291,092 B
- `manifest.json`: 917 B
- `auth.bin`: 80 B
- wrapper manifest+auth overhead: **997 B**

The owner itself is compact; wrapper/auth overhead is negligible here. Reconstructed members are exact:

- CSV: 6,853,491 B
- JSONL: 13,693,441 B
- owner corruption control: rejected as required.

This is causal evidence that representing the duplicate tabular relation once is useful. It is not enough to explain the remaining ~2.10 MB gap to v0.29, so the mature comparator is exploiting additional structure outside this pair and/or a better physical base representation.

## Selective access boundary

The receipt's six 4 KiB owner probes report:

- maximum modeled cold stored amplification: **7.46045x**;
- maximum decoded member segment: **1,246,421 B**.

Those values remain below the experiment's <=8x / <=8 MiB modeled thresholds, but they are **not physical-I/O measurements**. `_open_bundle()` authenticates by reading/hash-checking complete components before range reconstruction, so the wrapper may touch much more storage than the segment model reports.

Therefore this experiment does not earn a random-access/locality claim. Actual file-backed reads, bounded authentication proofs and measured bytes touched are mandatory before any shipping design could use this result.

## Hostile Reviewer verdict

The current R4 tabular-owner combination is **not productizable** for five independent reasons:

1. it still loses Analytics density to accepted v0.29 by 2,102,017 B;
2. the exact proof touches 65.7% of the positive workload;
3. total process-tree CPU is not charged in this receipt;
4. selective-access amplification is modeled rather than physically observed;
5. the authenticated wrapper is research packaging, not the final r25 reader/recovery/native surface.

No threshold tuning on Genesis is authorized to change that conclusion.

## What survived falsification

Three useful principles survive:

- **relation detection is highly selective:** 14/15 workloads remain untouched;
- **the tabular owner is a real density mechanism:** it removes 2.155 MB authenticated without collateral byte regressions;
- **admission can redirect expensive work:** the candidate avoids a large fraction of current Analytics elapsed portfolio work.

The correct next question is not “how do we make this threshold pass?”. It is: **what additional predictive/physical structure accounts for the remaining ~2.10 MB, and can the tabular signal help avoid expensive losing auditions while that structure is pursued?**

## Next decisive work

1. preserve this R4 as a negative/ablation, not a shipping candidate;
2. attribute the remaining Analytics gap against the v0.25 stream/derived/pack structure and the current r24 base after the two tabular members are removed;
3. investigate whether the cheap observation signal can reject or reshape expensive r25 auditions before child-process work begins;
4. charge same-runner process-tree CPU and sampled process-tree RSS on any future Analytics contender;
5. only if density later crosses the 6,135,172 B accepted-v0.29 floor should actual file-backed selective I/O, recovery and native parity become promotion blockers.
