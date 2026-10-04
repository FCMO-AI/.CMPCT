# R37 — Regenerable-Deflate Wait-Once Scheduling Builder Result

Status: **TERMINAL — `WAIT_ONCE_RUNTIME_OR_RSS_REGRESSION`**

Frozen preregistration: `R37_REGENERABLE_DEFLATE_WAIT_ONCE_BUILDER_PREREG.md`.

Exact result-bearing evidence head: `549345313b80a09e1d0392a0af021e826bceabd8`.

GitHub Actions run: `33848396291`, result-bearing job `100945670074`.

Immutable artifact: `v030-r37-wait-once-549345313b80a09e1d0392a0af021e826bceabd8`, artifact ID `9927520353`, ZIP SHA-256 `5aa8a16c9b7047a2bbc1acc99599b7699b07d8014126e3d28be05a3e6fa1b136`.

## Terminal decision

R37 emitted **`WAIT_ONCE_RUNTIME_OR_RSS_REGRESSION`** under the frozen law. The wait-once scheduling primitive is rejected for productization in the tested regime.

The intervention preserved exact candidate bytes, strong verification, deterministic output, 1.0x measured virtual-member locality, and unchanged median peak RSS on both protected targets. It also made the candidate slightly faster than the current ordered-map control on both targets. However, the recovery was far below the preregistered threshold and the byte-winning candidate remained materially slower than `release-all-exact` on both targets.

## Exact measured evidence

| target | release-all-exact | map control | wait-once | wait-once vs map | wait-once vs release |
| --- | ---: | ---: | ---: | ---: | ---: |
| full-backups | 0.487481343 s | 0.528985213 s | 0.525251169 s | **-0.003734044 s (-0.706%)** | **+0.037769826 s (+7.75%)** |
| nested-only | 0.316854150 s | 0.374928557 s | 0.372801508 s | **-0.002127049 s (-0.567%)** | **+0.055947358 s (+17.66%)** |

The frozen nested recovery floor was >=0.010 s; observed recovery was only 0.002127049 s. The existing material-runtime law (>5% relative **and** >3 ms absolute) marks the wait-once arm as materially slower than release on both targets.

Byte/correctness evidence remained lawful:

| target | release bytes | candidate bytes | candidate saving | candidate SHA identity |
| --- | ---: | ---: | ---: | --- |
| full-backups | 8,088,577 B | 8,056,167 B | **32,410 B** | wait-once == map control |
| nested-only | 2,231,156 B | 2,197,416 B | **33,740 B** | wait-once == map control |

Median peak RSS was 474,516 KiB for all three arms on both targets. Maximum measured virtual-member amplification was 1.0x. The wait-once arm observed exactly one patched Builder map call in each of all six fresh-process builds.

## Scoped negative constraint

Under the R32-R37 frozen Incremental Backups substrate, **collapsing the ordered `ThreadPoolExecutor.map` consumer into one aggregate wait followed by ordered result collection does not explain or repair the material runtime debt of the byte-winning candidate**.

R36's excess `Condition.wait` attribution therefore must not be interpreted as evidence that the number or placement of `Future.result()` waits is the dominant cause. R37 shows that removing repeated consumer-side waits while preserving the same work recovers only ~2-4 ms and leaves a 38-56 ms material gap to release.

This retires the specific `submit -> wait-all -> ordered result()` family for this regime. Do not reopen it via worker-count/chunksize tuning, executor substitution, threshold changes, or alternative names without new causal evidence.

## Causal interpretation

The strongest surviving explanation is that the waits observed by R36 are predominantly **symptoms of additional/longer candidate-encoding work on the critical path**, not avoidable waiting overhead in the ordered consumer. The next lawful diagnostic should therefore attribute per-candidate encode work and critical-path completion under the unchanged map-control semantics, rather than continue scheduler-call tuning.

## Reopening predicate

Reopen wait-aggregation only if a materially different substrate produces evidence that consumer-side synchronization itself, independent of candidate work duration, contributes >=10 ms on the protected nested target while exact bytes, worker policy and candidate set remain fixed.

## Strongest surviving self-critique

Three fresh processes provide a disciplined A/B but remain a small runtime sample. Nevertheless, the rejection does not hinge on a marginal noisy sign: the observed nested recovery (2.13 ms) is roughly one-fifth of the frozen 10 ms minimum, and the candidate remains ~55.95 ms slower than release. More repetitions could move the estimate but would not justify rewriting this frozen result; a new experiment would require a new freeze.

## Required next action

Return to diagnosis at the same CMPCT-owned Builder boundary. Freeze a per-candidate encode/critical-path attribution that preserves current map-control scheduling and records which candidate work sits behind the observed waits. A subsequent Builder is warranted only after that attribution identifies a bounded project-owned computation with enough Addressable Opportunity Mass to close a material share of the 38-56 ms remaining gap without sacrificing the 32-34 KiB byte win, exact reconstruction, <=8x locality or RSS.
