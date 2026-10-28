# v0.30 reactivation frontier reconciliation — 2026-09-11

Status: **durable research handoff; diagnostic evidence only**  
Primary near-term line: `agent/v030-authoritative-integration`  
Frozen Genesis v0.30 comparator: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`  
ONE/CMPCT1 remains preserved on `research/cmpct1` as a secondary research line.

## Mission lock

Genesis established a real reason to reactivate v0.30: on the same 265,969,714 logical bytes, authenticated stored bytes were 275,219,901 for ONE-G0.2, 137,499,525 for accepted v0.29, and 150,055,575 for the frozen v0.30 product. v0.30 beat v0.29 on 9/15 density rows and all 15 creation-CPU rows, but its six density losses left a 12,556,050-byte aggregate deficit to v0.29. Office and analytics alone account for 13,748,754 bytes of gross v0.30 deficit and therefore dominate near-term density work.

This handoff asks which already-developed predictive structures explain that deficit and which remaining gap is productization/framing rather than missing compression theory. It does not alter the frozen Genesis verdict or award release credit to research-only grammars.

## Referee hypothesis and disproof

Initial hypothesis:

> The dominant missing structure in both office and analytics is v0.25-style stream federation / derived reconstruction; therefore stream-backed recipes should conservatively cover a strict majority of logical bytes on both workloads, while a known non-stream control should remain stream-free.

Disproof test:

1. rebuild the frozen repaired neutral corpus;
2. normalize the exact office, analytics, and developer-repository trees;
3. build unchanged EntropyGraph-v0.25/CMPNX5 artifacts;
4. strong-verify and extract exact trees;
5. account every physical archive byte into stream packs, ordinary packs, or authenticated metadata/recovery/framing;
6. conservatively mark only `zipstreams`, `inflate_stream`, and inherited `decode_file` recipes as stream-dependent (do not over-credit hybrid `splice` recipes);
7. require developer-repository to remain stream-free.

The diagnostic is `benchmarks/v030_v025_physical_attribution.py`.

## Hosted exact-source result

Exact-source hosted measurement head: `861a4f34083c85d5ce331d2b66da9b6852c4fa5c`  
Workflow run: `34620744567`  
Measurement job: `103333798411`  
Artifact: `10271559413` (`v030-v025-physical-attribution-861a4f34083c85d5ce331d2b66da9b6852c4fa5c`)

The scientific measurement and independent JSON/accounting validation both passed. The run itself was red only because the first workflow version violated the repository deep-lane topology policy; the artifact was uploaded after that policy check. Workflow topology was subsequently repaired separately. Do not relabel the workflow red as a product or measurement loss.

### Exact attribution

| workload | logical bytes | exact v0.25 archive | stream-pack physical | ordinary-pack physical | metadata/recovery/framing | conservative stream-dependent logical | stream logical fraction |
|---|---:|---:|---:|---:|---:|---:|---:|
| office | 16,063,798 | **5,954,026** | 3,792,128 | 2,159,404 | 2,494 | 13,175,408 | **82.0193%** |
| analytics | 31,265,767 | **6,135,172** | 3,557,017 | 2,577,097 | 1,058 | 7,396,979 | **23.6584%** |
| developer repository (control) | 2,624,373 | **744,337** | 0 | 699,795 | 44,542 | 0 | **0%** |

Physical accounting is exact in all three rows.

Single-run diagnostic creation times (not a speed claim):

- office v0.25 build: 0.4728 s reported / 0.4730 s wall; strong verify 0.0474 s; extraction 0.0201 s;
- analytics v0.25 build: 7.7946 s reported / 7.7958 s wall; strong verify 0.1367 s; extraction 0.0590 s;
- developer-repository v0.25 build: 0.9810 s reported / 0.9823 s wall; strong verify 0.1656 s; extraction 0.0803 s.

These timings are diagnostic-only: one hosted process, no fresh-process repetition, and no direct product comparator in this lane.

### Causal result: the initial hypothesis is **falsified**

- Office is genuinely stream-dominant: 13.18 MB / 16.06 MB of logical file bytes are conservatively stream-dependent.
- Analytics is **not** stream-dominant: only 7.40 MB / 31.27 MB are conservatively stream-dependent. Its recipe accounting is 23,868,788 B `plain`, 3,840,128 B `inflate_stream`, and 3,556,851 B `zipstreams`.
- Developer-repository is correctly stream-free, so the attribution is not simply labeling all v0.25 savings as federation.

Therefore “productize stream federation and office+analytics are solved by the same mechanism” is rejected. Stream federation remains a high-value Office mechanism and a material Analytics component, but Analytics needs separate accounting of its large ordinary/plain representation.

## Stronger result: exact v0.25 equals the accepted v0.29 byte floor on both dominant targets

The repaired exact-source diagnostic landed on:

- office: **5,954,026 B**, exactly the accepted v0.29 floor `5,954,026 B`;
- analytics: **6,135,172 B**, exactly the accepted v0.29 floor `6,135,172 B`.

This is stronger and cleaner than the earlier approximate fallback figures. It confirms that accepted v0.29 is effectively preserving the full v0.25 representation on these two rows; the missing shipping-v0.30 density is not evidence that the mature predictive structure disappeared from repository history.

The immediate research problem is now **productization without paying away that floor**, plus identifying which v0.25 substructures are safe/general enough to admit broadly.

## Reconciliation with the existing federated research family

Hostile review found that v0.30 already contains substantial federated productization work. This prevents a circular campaign that would merely rediscover an old idea.

Historical all-15 federated evidence attempted all 15 workloads and preserved failures as failures. In the strongest broad diagnostic recovered here:

- office federated candidate: **6,428,050 B** vs genuine r24 **15,445,236 B** — large win vs r24, but still above accepted v0.29;
- analytics: **7,096,243 B** vs r24 **10,392,442 B** — large win vs r24, but still above accepted v0.29;
- logs: **3,908,777 B** vs r24 **5,260,145 B** — admitted structurally, still above accepted v0.29;
- many other workloads correctly rejected on size and/or locality, including developer repository, media, backups, incompressible, tiny-files, ML, mixed binary, shifted versions, false neighbors, boundary churn, and resemblance incompressible.

The all-15 selector hypothesis was therefore a useful negative result, not a product success. Current `v030_federated_generalization_admission_v3.py` explicitly preserves that rejection as valid evidence.

### Important CI self-correction

Do **not** infer product proof from a top-level green workflow when the deep exact-head job was skipped. At commit `e2acef892168e6ea08c50cd3af5721051b992435`, the later productization and all-15 workflow invocations had successful latest-head classifiers while their deep evidence jobs were skipped. Those greens are scheduling receipts, not new compression evidence.

This distinction matters because the current candidate/productization workflow source contains stronger accepted-v0.29 assertions than some older executed artifacts. Source policy describes the gate; only a deep exact-source run can prove that a candidate crossed it.

## Current canonical-filesystem level-1 frontier

The present canonical-filesystem budget oracle (`v030_v025_canonical_fs_level1_oracle.py`) is narrower and more promising than the old broad federated selector. Its current independent enforcement says:

- both office and analytics remain strict complete-byte + verified-create winners over ZIP/Deflate-9 and solid Zstd-19 after paying the canonical filesystem tax;
- office is required to clear accepted v0.29 `5,954,026 B` and is recorded as productization-prerequisite green;
- analytics is deliberately retained as negative evidence: it remains above accepted v0.29 `6,135,172 B`, so productization prerequisite is false.

This makes **Analytics canonical product tax / ordinary-pack structure** the highest-value unresolved target. Office should not be treated as solved for release yet—the representation is still research-only CMPNX5—but its remaining problem is primarily canonical reader-visible productization rather than discovering another large density mechanism.

## New follow-up experiment

Two new diagnostic-only files now exist on the reactivated branch:

- `benchmarks/v030_v025_canonical_fs_tax_attribution.py`
- `.github/workflows/v030-v025-canonical-fs-tax-attribution.yml`

They compare, on the exact same normalized Office and Analytics trees and the exact same v0.25 engine with every internal Zstd request capped at level 1:

1. raw level-1 v0.25;
2. canonical-filesystem-staged level-1 v0.25.

Both variants are independently strong-verified and physically accounted. The output reports:

- exact canonical-minus-raw byte tax;
- raw-level1 minus accepted-v0.29;
- canonical-level1 minus accepted-v0.29;
- filesystem manifest bytes/entries;
- stream/ordinary/metadata physical attribution for both variants;
- build and verification wall time as diagnostic context.

This is designed to decide whether Analytics is now a small bounded framing/manifest problem or still a material representation problem. It does not change a selector or product.

## Next decisive actions

1. Obtain a deep exact-head receipt for the canonical-filesystem tax attribution lane; do not count a skipped classifier as evidence.
2. If Analytics residual over accepted v0.29 is small and mostly canonical manifest/framing/ordinary-pack overhead, attack that general bounded tax first; avoid inventing another compression mechanism.
3. If the residual remains material, break the 2,577,097 B ordinary physical payload and 23,868,788 B `plain` logical region into pack family / file family / entropy / reuse causes, with a held-out non-Analytics control.
4. Re-run the narrow candidate only after the mechanism changes; preserve Office, Analytics, creation cost, locality <=8x, max decode unit, recovery, integrity, and canonical filesystem semantics simultaneously.
5. Only then expand back to the 15-workload admission matrix.

## Claim boundary

Nothing in this handoff changes v0.30 release status, canonical version, selector authority, native/Android authority, or public benchmark claims. Research-only CMPNX5 remains research-only. The Genesis v0.30 result remains the frozen product comparator, and accepted v0.29 remains the mandatory no-regression floor. ONE evidence remains preserved and its efficiency lessons remain inputs to v0.30 discovery/productization work.