# v0.30 exact-head external frontier — b2260db

Status: **RESULT-BEARING PRODUCT EVIDENCE — EXTERNAL FRONTIER RED**

This note preserves the first result-bearing strict external-competitor receipt after the merge-classifier blind spot was forced through exact-head authority. It is product evidence, not a Foundry thesis and not release authority by itself.

## Authority and provenance

- candidate source: `b2260db745e61e8b15463c1be4387c30b5ac8ef2`
- candidate fingerprint: `a7ce3cb23cc6c1f7d737b7e962eb7298916b36f9d34210625efac22eac5c51c4`
- workflow: `CMPCT v0.30 external competitor frontier`
- run: `35285383961`
- result-bearing job: `105417365534` (`external-frontier`)
- artifact: `10525242273`, `v030-external-frontier-b2260db745e61e8b15463c1be4387c30b5ac8ef2`
- artifact ZIP SHA-256: `73449c5351018fea98208b0751acb52836459b17a4a45977bb9ee0e7fb2a3748`
- runner: GitHub-hosted Ubuntu 24.04; CPython 3.11.16
- external tools observed in the job: Zstandard CLI 1.5.7, 7-Zip 23.01, ZPAQ 7.15
- benchmark entrypoint: `benchmarks/v030_external_competitors_canonical.py`

The job bound checkout to the exact candidate SHA, completed the 15-workload matrix, verified all CMPCT and ZIP trees before credit, uploaded the result JSON, and failed because the product contract was red. This is not an infrastructure failure.

## Aggregate bytes

| format | all 15 bytes | delta vs CMPCT |
|---|---:|---:|
| CMPCT v0.30 | 149,956,581 | — |
| ZIP / Deflate-9 | 188,073,217 | CMPCT smaller by 38,116,636 B |
| solid tar + Zstd-19 | 143,849,013 | CMPCT larger by 6,107,568 B |
| 7z LZMA2 max solid | 139,911,068 | CMPCT larger by 10,045,513 B |
| ZPAQ method 5 | 138,169,739 | CMPCT larger by 11,786,842 B |

The strict scoreboard is:

- ZIP size wins: **15/15**;
- Zstd-19 size wins: **7/15**;
- ZIP create-time wins: **5/15**;
- Zstd-19 create-time wins: **5/15**;
- strict joint size+create wins: **5/15**, target **15/15**.

Therefore the external release gate is red even though CMPCT strictly beats ZIP size on every row.

## Zstd-19 size-loss decomposition

The eight rows where CMPCT is not smaller than solid Zstd-19 are:

| workload | CMPCT B | Zstd-19 B | CMPCT excess B |
|---|---:|---:|---:|
| office workspace | 15,445,236 | 8,312,879 | **7,132,357** |
| analytics/database | 10,392,442 | 9,337,546 | **1,054,896** |
| many tiny files | 666,272 | 446,811 | **219,461** |
| developer repository | 854,476 | 737,982 | **116,494** |
| incompressible/encrypted-like | 10,206,503 | 10,199,302 | 7,201 |
| shifted versions | 1,700,594 | 1,694,674 | 5,920 |
| deflate family | 17,610 | 14,252 | 3,358 |
| boundary churn | 75,981 | 73,097 | 2,884 |

Gross losing-row excess is **8,542,571 B**. Winning rows claw back **2,435,003 B**, leaving the observed aggregate deficit of **6,107,568 B**.

The key causal allocation fact is stronger than the aggregate headline: **office workspace alone loses 7,132,357 B to Zstd-19, which is larger than CMPCT's entire 6,107,568 B aggregate deficit.** If all other 14 rows remained byte-identical, merely matching Zstd-19 on Office would move the all-15 aggregate from a 6.11 MB loss to about a 1.02 MB win. That does *not* satisfy the strict 15/15 contract, but it proves Office owns the aggregate size decision and deserves first representation-level diagnosis.

Analytics is the only other >1 MB Zstd size loss. Tiny-files and developer-repository are meaningful but an order of magnitude smaller. The four residual losses below 8 KB are poor primary targets while Office/Analytics remain unexplained.

## Strong positive controls that must be preserved

The matrix also proves that CMPCT's structural mechanisms are not globally broken:

- incremental backups: CMPCT **8,081,635 B** vs Zstd-19 **8,384,906 B**, 7z **8,394,102 B**, ZPAQ **8,328,124 B**;
- logs/telemetry: CMPCT **3,550,294 B** vs ZIP **5,442,141 B** and Zstd-19 **4,358,684 B**;
- false neighbors: CMPCT **34,643,102 B** vs Zstd-19 **34,660,112 B**;
- large mixed binary: CMPCT **12,590,162 B** vs Zstd-19 **12,591,881 B**;
- ML artifacts: CMPCT **13,674,830 B** vs Zstd-19 **13,704,258 B**.

Any Office/Analytics repair must retain these wins and the existing exactness/locality/recovery contract rather than flattening the product into a generic solid codec.

## Diagnosis and next decisive question

This receipt narrows the primary byte problem from “CMPCT loses aggregate size to mature solid codecs” to a concentrated question:

> Why does the canonical product pay ~7.13 MB above Zstd-19 on the Office workspace, and how much of that gap is (a) current portfolio/admission choosing a dominated representation, (b) container/member boundaries preventing cross-member context reuse, (c) metadata/framing overhead, or (d) an entropy-coding floor not reachable by the current representation family?

The next size experiment should be an **Office charged oracle**, not another threshold tweak. On the exact frozen Office tree, measure at minimum:

1. current canonical selected representation and its complete-artifact bytes;
2. every already-implemented generic candidate that can legally represent that tree, charged exactly as a decoder/product would need it;
3. an optimistic but fully charged solid/container-aware ownership bound that preserves exact reconstruction;
4. Zstd-19 and 7z controls under the same input/semantic boundary;
5. create cost for every candidate, because a byte-only rescue that worsens the already-red create frontier is not product rehabilitation.

Decision law:

- if an existing candidate or legal portfolio combination closes a material fraction of 7.13 MB, the owner is admission/selection and Forge should productize the cheapest generic predictor;
- if a charged container-aware bound closes the gap but existing candidates cannot, escalate to R4 representation/ownership repair;
- if even the generous charged bound remains far above Zstd-19, retire local Office portfolio tuning and identify the missing codec/context primitive instead;
- do not spend primary budget on the <8 KB residual Zstd losses until the large owners are retired or repaired.

## Create-time debt remains independent

This note does not infer per-row timing causes from the size table. The exact receipt independently proves only **5/15** strict create wins against ZIP and **5/15** against Zstd-19. That is a broad product red and remains governed by `docs/V030_EFFICIENCY_RECOVERY.md`. Office size diagnosis must expose candidate/build timing so a representation win cannot hide additional execution debt.

## Promotion consequence

v0.30 remains merge/tag/version/publish locked. This receipt is valuable precisely because it is a fair loss: it turns the external frontier from missing evidence into a measured product problem. The correct response is to attack the concentrated owners, not weaken the evaluator or average them away.
