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

## New held-out question / current evidence boundary

Follow-up test commit `705302acf354110ee2acb32019c07138de50bd0e` adds a 4,096-reference valid fixed-chunk member with repeated physical ownership and direct ranges crossing early, middle and final references, alongside one out-of-range declared-total hostile. This **new test was not part of the first successful 11-case run**. Its hosted result and exact final HEAD must be checked independently; do not count it as passed until then.

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
