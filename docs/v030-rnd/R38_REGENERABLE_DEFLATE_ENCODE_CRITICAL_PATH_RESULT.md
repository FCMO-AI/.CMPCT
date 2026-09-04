# R38 — Regenerable-Deflate Encode Critical-Path Attribution Result

Status: **TERMINAL — `ENCODE_FAMILY_DISTRIBUTED`**

Frozen preregistration: `docs/v030-rnd/R38_REGENERABLE_DEFLATE_ENCODE_CRITICAL_PATH_PREREG.md`.

Execution authority:

- workflow run: `33852378791`
- result-bearing job: `100957984887`
- exact evidence head: `eee03e4db0cba73cf46bb018f2c106c28a04a7c0`
- frozen substrate head: `0d0173f01bb48b12c96c2b20db5acc5636162e1c`
- immutable artifact: `v030-r38-encode-critical-path-eee03e4db0cba73cf46bb018f2c106c28a04a7c0`
- artifact ID: `9928922357`
- artifact ZIP SHA-256: `d412573cabf48ae0d0fc2b33f952196bad3ab527852d40538835cc13fa11ce90`
- exact-head binding: **PASS**
- frozen substrate / instrument binding: **PASS**
- frozen completeness / decision-law guard: **PASS**
- CI-topology self-check: **PASS**

## Frozen terminal decision

`ENCODE_FAMILY_DISTRIBUTED`

The residual R32/R37 create-time debt does not belong to one cross-target encode straggler. Per-candidate timing localizes nearly all positive encode-task excess to a broad, structurally coherent family: the 180 small `.txt` candidates that carry one exact-Deflate alternative, are no longer retained as canonical Deflate blobs under the byte-winning arm, and therefore select dictionary-Zstd as their stored content representation.

This is a stronger diagnosis than R36/R37. R36 correctly localized the observed wait symptom to the ordered parallel encode boundary, while R37 proved that collecting those same futures only once did not remove the runtime debt. R38 now shows why: the candidate genuinely performs materially more encode work across many tasks before the ordered consumer can finish. There is no single task whose removal can lawfully rehabilitate the path.

## Exact protected-target evidence

All repetitions strongly verified, remained deterministic within each arm, exercised exactly one inherited `ThreadPoolExecutor.map` call, and kept selected-member decoded-context amplification at **1.0x**.

### Full Incremental Backups

| Arm | Complete bytes | Median build | Median encode makespan | Peak RSS | Encode tasks |
| --- | ---: | ---: | ---: | ---: | ---: |
| `release-all-exact` | 8,088,345 B | 0.426427 s | 0.080180 s | 474,952 KiB | 198 |
| `no-ordinary-zstd` | 8,055,929 B | 0.436889 s | 0.124569 s | 474,952 KiB | 198 |

The candidate remains **32,416 B smaller**. Its median build is +10.461 ms (+2.45%) on this instrumented run; the encode makespan itself is +44.390 ms.

R38 observed 194 positive per-key candidate-minus-release encode deltas summing to 207.502 ms. The 180 `.txt` / one-Deflate-alternative / candidate-codec-3 / release-codec-4 rows account for **201.953 ms = 97.33%** of that summed positive excess and 980,226 raw bytes. No single row dominates: the largest positive row is the `.cmpct-pack` candidate at only 5.425 ms / 2.61% of summed positive excess.

### Isolated `snapshot_2.zip`

| Arm | Complete bytes | Median build | Median encode makespan | Peak RSS | Encode tasks |
| --- | ---: | ---: | ---: | ---: | ---: |
| `release-all-exact` | 2,231,158 B | 0.269189 s | 0.003515 s | 474,952 KiB | 194 |
| `no-ordinary-zstd` | 2,197,416 B | 0.303769 s | 0.051852 s | 474,952 KiB | 194 |

The candidate remains **33,742 B smaller**. Its median build is +34.579 ms (+12.85%); the encode makespan is +48.337 ms.

R38 observed 193 positive per-key deltas summing to 199.239 ms. The same 180 `.txt` / one-Deflate-alternative / candidate-codec-3 / release-codec-4 rows account for **199.113 ms = 99.94%** of summed positive excess, again spanning the same 980,226 raw bytes. The largest single row contributes only 2.857 ms / 1.43%.

## Causal interpretation

The byte-winning arm changes the economics of these 180 candidates in a precise way:

1. `release-all-exact` retains the chosen exact Deflate stream and `_encode_candidate` returns that stream directly as `CODEC_DEFLATE` with essentially no fresh codec tournament for the candidate.
2. The R30/R32 byte-winning retention grammar deliberately does **not** retain those small exact Deflate streams. Their ZIP reconstruction can regenerate the stream, so retaining it would spend bytes solely to avoid encode work.
3. Once the stream is not retained, the raw text content still needs a physical CMPCT representation. Under the frozen candidate, all 180 select `CODEC_ZSTDDICT`.
4. Dictionary compression is therefore selected work, not an output-dead audition. Across the isolated target its per-task excess sums to ~199 ms; with the inherited parallel worker pool this appears as ~48 ms of additional encode makespan, closely matching the remaining product-runtime debt.

The causal owner is therefore a **distributed selected-representation family**, not executor waiting and not another speculative ordinary-Zstd audition.

## Scoped negative constraints

Within the frozen R30-R38 regime:

- do not pursue a single-straggler optimization; no single candidate owns a meaningful fraction of the cross-target excess;
- do not reopen executor collection/wait-order tuning without new evidence; R37 already falsified sufficiency and R38 observes real distributed encode work upstream;
- do not remove dictionary compression as if it were output-dead. It is the selected content representation for the dominant 180-candidate family and therefore pays for part of the byte win;
- do not infer that every dictionary-coded text candidate is globally expensive. The tested regime is the exact-deflate-backed, non-retained `<64 KiB` family in the repaired Incremental Backups targets.

Reopening any broader claim requires transfer evidence outside this frozen semantic regime.

## Forge decision

Diagnosis advances to **D2/D3 selected-codec effort debt after speculative-work retirement**.

Terminal decision: **`RETIRE_SINGLE_OWNER_SEARCH; CLUSTER_SELECTED_DICTIONARY_FAMILY`**.

The next lowest-sufficient intervention must obey the R38 preregistration: freeze a content/representation-derived family before changing behavior, then run one bounded family-level codec-effort Builder. The family must be derived from properties visible without workload/path identity: exact-Deflate-backed candidate, canonical stream not retained, small raw candidate, text-like hint, and dictionary-coded selected output. The Builder may reduce dictionary encode effort only for that family; it may not change the archive grammar, Deflate retention threshold, worker count, corpus, release/locality/RSS thresholds, or other candidate policies.

A productizable result must keep the protected byte win, exact reconstruction, <=8x locality, inherited RSS law and the existing material runtime law. Any byte/runtime trade must be reported explicitly rather than hidden by aggregate improvement.

## Strongest surviving self-critique

R38 measures per-task wall duration inside a shared thread pool, so individual elapsed values include contention and scheduler interference and must not be read as CPU profiles. The evidence is persuasive because the same structural 180-row family owns 97.33% and 99.94% of summed positive excess on two nested protected targets, and the aggregate encode-makespan increase matches the remaining wall-time scale. The next Builder must nevertheless use **uninstrumented fresh-process product timing** for credit; R38 itself grants diagnosis only.
