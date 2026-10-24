# O7 preregistration — one canonical authenticated delta replay for Reader and preflight

**Date:** 2026-10-24 UTC. **Status:** PREDICTION LOCKED BEFORE PRODUCT EDIT. **Credit:** research until real same-runner source-exact product evidence; no release.

## Authority, baseline and concurrency
- Canonical released floor: CMPCT v0.30.0, on-disk revision 24; development is unreleased v0.31.
- Exact O7 starting head: PR #355 `5f6c1462e30686687ea13cc2507c9702f13df116`; Reader blob `604f6a81bf03bd97a4defb4ad7a1393d01ed491f`; strict validator blob `2bb3f53c918ae93efb105364e2b93ea46aeca034`.
- O6b original source/execution: `benchmarks/v031_reader_signed_delta_open_o6.py` blob `e3b6d61a124377db36e070a6628ab4ef777c195d`; source-exact authentic r24 case creator `benchmarks/v031_signed_delta_replay_o0.py` blob `02c5f506c9294130db6b0eb9c36c0a61460c3b35`. PR #355 observed Reader delta/checkpoint constructor-wall ratio 72.56x at 4096 operations on its runner, whereas preflight indexing is already proven.
- Existing independent replay reference cases: `tests/test_v031_delta_replay_indexed_o1.py` blob `4e442f329051235950a4de7aef12ef9990658d35` with 10,000 seeded sequences. Preserve it unchanged.
- Concurrent Reader mutation: PR #356 owns prewrite symlink-target admission in `reader.py`; do not overwrite or merge its owner branch. O7 owns only journal replay in `_index_from_footer`; integrate later against a single current owner head. PR #345 owns Writer/Reader safety and base.
- `docs/discovery/STATE.json` is a staleable cache of older research; current PRs and source/Actions override it. No separate state database and no release law changes.

## Primary question and mechanism
Can the ordinary Reader eliminate quadratic authenticated rename/put/del scans **by reusing the already authenticated and independently tested** `cmpct.validation._apply_delta` operation owner, without changing valid archive semantics, footer recovery, final index identity, write semantics, or release format?

**Hypothesis:** one shared existing replay function, invoked from the Reader at each authenticated generation, retains first-match put/rename and all-match delete, append-order and sorted per-generation rows, while replacing expensive repeated scans with the proven bounded positional index when its input meets the existing threshold. This is a simpler owner-sharing alternative to copying a second indexing algorithm into Reader. Prediction: lower delta-open constructor CPU/wall vs the exact pre-edit Reader on the *same authenticated files* and host, with checkpoint-open and byte reconstruction unchanged.

**Strong simpler control:** leave Reader historical scans, optimize only preflight; fails to address independent O6b Reader latency. **Alternative:** copy indexed algorithm into Reader to avoid a validation import, at cost of duplicated logic/drift. **Alternative explanation:** most open cost might be index decode/sort rather than scan; ABBA with identical files and same checkpoint is intended to discriminate.

## Disproof, risks, and complete-cost law
1. Any valid index divergence, first-match/all-match rule drift, broken multi-generation recovery or raw physical-byte difference kills product claim.
2. Retain strict MessagePack duplicate-map refusal, current Reader constructor cleanup, source-signed hashes, per-generation sort and all inherited preflight, hardlink, Win32, APFS and PACK tests. Do not weaken the evaluator, source, workload, comparator, limits, or recovery rules.
3. Explicitly distinguish historical lenient acceptance of malformed operations (if any) from strict validator rejection; fail-closed safety may be reasonable but must not be mislabeled exact behavioral equivalence. Test old and new valid sources independently.
4. Charge validation dependency/import latency, checkpoint-open wall/CPU, parsing, temporary allocation/RSS when measured, complete archive bytes, and Reader open/list/read. No compression ratio claim and no new format.
5. If source-exact ABBA fails, is missing, or provides no decision-changing CPU evidence, do not promote; retain old Reader and evidence.
6. O7 keeps draft status even after focused green until actual full-product, multi-platform, hostile recovery and official release parity evidence passes.

## Cheapest evidence ladder
- First inspect exact code paths and hand-prove shared operation semantics using existing O1 10,000-sequence oracle.
- Surgical Reader-only production change; no change to validator or Builder.
- Genuine on-disk Builder + SHA-committed r24 journal vs identical final-checkpoint controls at 512/2048/4096; same-runner alternation of the **actual historical Reader module** and candidate Reader module with source identity pinned to O7 baseline.
- Separately run unchanged O1/reference, O6 source-exact union, and hostile signed topology/hardlink tests. Then current exact-head CI and portability. Retain raw measurements, including losses.

## Decision if successful
Offer a narrow graft to #345/#355 Reader owner instead of a new format/version. Investigate cross-platform exact-head and worst-case memory/recovery before any merge. Independent symlink-prewrite #356 remains separate and must be reconciled.
