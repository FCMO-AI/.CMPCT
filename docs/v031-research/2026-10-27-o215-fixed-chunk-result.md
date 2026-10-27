# O215 — Fixed-chunk effective-index admission result

As-of 2026-10-27 UTC. Published v0.30.0 / revision-24 unchanged. Product candidate, **not merged or released**.

## Exact source and preregistration

Parent: O214 #564 `d90dab60d2fe646dbda9e61de3b5080ca83c7b7e`. Independent stacked draft PR #568 `agent/phased3-v031-o215-fixed-chunk-same-index-admission-20261027`.

Original prediction [`2026-10-27-o215-fixed-chunk-prereg.md`](2026-10-27-o215-fixed-chunk-prereg.md) committed as `c5a1acd71db3f37972caa46f83563ceee916f0c7` **before implementation or a result-bearing test**. It wrongly expected `verify()` success for a chunk-total size mismatch. Exact Reader source inspection before execution showed `read()` compares reconstructed length with advertised size; an immutable correction [`2026-10-27-o215-prereg-source-correction.md`](2026-10-27-o215-prereg-source-correction.md) was committed at `a84fde9aa8f456eb4c4d5ee834be79098dc85804`. The earlier prediction was preserved.

## Genuine negative on unchanged installed Reader

Original 3-host tests-first CI [40445636811](https://github.com/FCMO-AI/.CMPCT/actions/runs/40445636811), at exact test-only HEAD `2982d9567c038cd278b47aee964d35f32231af45`:

| Host | Positive controls passed | Invalid descriptors wrongly accepted by Reader | CI classification |
| --- | ---: | ---: | --- |
| Ubuntu 24.04 | 5 | 6 | FAIL, genuine product defect reproduction |
| macOS 14 | 5 | 6 | FAIL, genuine product defect reproduction |
| Windows 2022 | 5 | 6 | FAIL, genuine product defect reproduction |

The six failing acceptance assertions cover overdeclared logical size, underdeclared size, a repeated physical blob with incorrect total, absent reference, boolean reference, and invalid authenticated later generation. The strict preflight **already rejected all six**, while ordinary Reader admitted them. Site-installed Python source was byte-identical to GitHub source; these are fully framed revision-24 archives with root `v:24`, SHA/CRC-correct physical RAW records, compressed authenticated primary/tail indexes and footer, not monkeypatched Reader objects.

An independent exact-parent Linux probe, included in the subsequent candidate CI, directly confirms the narrow defect: archive with one physical `ABCD` blob (4 B) and declared file size 5 B; ordinary parent `read_range('fixed.bin',4,1)` returned **empty bytes** without raising, despite the requested interval being within its declared size. Strict preflight, full `read()` and `verify()` each rejected it. The hostile archive SHA-256 was `675841d8df7dfcad7278e22fc09852d67e52398ef141aa285c7373f322c56cce`. **Never relabel this as post-verification corruption**.

## Smallest candidate mechanism and direct positive evidence

Source commit `5e98f89497f17eae59315843ea0675f594a9f708`, Reader blob `73e4bfdab49af8c3302a313793ed594a8272b51d`, adds `S_CHUNKS` to existing same-effective-index O212/O214 `_validate_storage` call in `CMPCT.__init__`, *before mmap*, and clarifies names/comment. The validator itself is **unchanged**: `51c2849061f99a4afeddb7666956b24566ce7de0`. No separate filename preflight, format changes, Builder/ZIP changes or parser weakening.

Candidate 3-host CI [40445891394](https://github.com/FCMO-AI/.CMPCT/actions/runs/40445891394) on that exact source:

| Host | New O215 tests | Unmodified O212/O214 regression | Result |
| --- | --- | --- | --- |
| Ubuntu 24.04 | 11/11 PASS | 25 tests + 9 subtests PASS | SUCCESS |
| macOS 14 | 11/11 PASS | 25 tests + 9 subtests PASS | SUCCESS |
| Windows 2022 | 11/11 PASS | 25 tests + 9 subtests PASS | SUCCESS |

New positive controls retain byte-exact valid single, distinct and repeated chunk refs, zero-length list, and **immutable independent three-codec fixed-chunk revision-24 conformance vector**. New negatives now reject at Reader admission and do not alter original archive SHA.

Linux reran a separately installed, source-exact O214 parent on exactly the same r24 hostile semantics, producing `PARENT_SELECTIVE_IN_BOUNDS_SHORT_READ`, while the candidate refused the archive before exposing ranges. Raw per-host logs and SHA-tagged uploaded CI receipts remain in the run above; this document does not replace them.

## Held-out 4096-reference confirmation and final-head custody

Follow-up test commit `705302acf354110ee2acb32019c07138de50bd0e` added a **4,096-reference** valid fixed-chunk member (16,384 logical bytes, one physical four-byte RAW blob referenced repeatedly) and explicit early/middle/end range checks plus a malformed declared-size control. This was not included in the initial 11-case run.

**Documented final test-and-result HEAD:** `483520c35b4c0cc31616bc53296ea082dcf8f0b3`. Result-bearing [GitHub Actions #40446255537](https://github.com/FCMO-AI/.CMPCT/actions/runs/40446255537) completed **SUCCESS on Ubuntu/macOS/Windows**. Exact HEAD was checked in source checkout and verified against independently installed Reader/validation bytes. All three hosts recorded **12/12 O215 tests** and the **unchanged 25 inherited O212/O214 tests + 9 subtests** PASS. The Linux job additionally reinstalled the genuine parent Reader and reproduced `PARENT_SELECTIVE_IN_BOUNDS_SHORT_READ`. CI uses a synthetic PR merge SHA in artifact filenames; `EVIDENCE_HEAD` and checkout bind the actual tested branch HEAD `483520c...`, not that synthetic SHA.

Original provider ZIP receipts at this result-bearing run have the following GitHub artifact SHA-256 digests:

| Host | SHA-256 of original provider evidence ZIP |
| --- | --- |
| Ubuntu | `f7c452a7037ad95d270b269b61fce25f49ee5607a28ae37d71cc9f1259f1555a` |
| macOS | `5ab45dd202a55ed802aca9779599831bb4117c0f76d39e196192a6be179599f3` |
| Windows | `1ad0051bea830d8df6bf1367666113e5cdce98af0e3b5d5ca8115a35acc4db36` |

**CI at that source HEAD:** specialized, Engineering Evidence, Version Discipline, CI Topology, R36 Attribution, Native Core, and workflow performance gate reported SUCCESS. The performance workflow success does **not** replace a new numeric cold-open CPU/RSS benchmark. General CMPCT tests and continuous fuzzing had not finished at the last recorded inspection. The present documentary commit occurs after the result-bearing source HEAD, so its own status must be reconciled separately.

## What changed scientifically

The original source-inspection correction eliminated a false stronger claim before experiment. The remaining defect — metadata-authenticated, selectively exposed, in-bounds *short read* that a full-file operation would refuse — was reproduced and stopped by reusing one canonical validator. The counterfactual cheaper discriminator is the comparison `sum(blob_us[idx] for idx in refs) == row.logical_size` at the same effective index, plus one final in-bounds range. It is prospectively recognizable for other indexed representations. This is an evidence-backed **local testing lesson**, not grounds for changing the global Discovery Engine or release policy.

## Debt, losses and nonclaims

- Malformed archives are constructed adversarially; no evidence canonical Builder creates them.
- `verify()` on the original Reader already rejected the shape; this is **not** a verified-file hash failure.
- Native C ABI and full materialized multi-GiB ZIP64/export parity are not directly measured by O215.
- Admission cost becomes O(number of fixed-chunk references) additional traversal. No direct base-vs-candidate large-index open wall/CPU/RSS or complete release-parity comparison has been earned.
- Same-inode source mutation, extraction publication custody, historical journal recovery, resource ceilings and other index representations remain separate obligations.
- Draft stacked PR only; coordination with O214 #564 and J24C01 #567 is required before merge.

**Decision:** narrow product correctness candidate supported by 3-host source-exact positive/negative evidence. Promotion remains blocked by source-owner integration and all applicable exact-head gates. No change to frozen tests, format revision, version, benchmarks, discovery policy, or historical negative receipts.
