# O64 — NTFS directory named-stream fail-closed product result

Date: 2026-10-25 UTC. **Result: INSTALLED FOCUSED PRODUCT COURT PASS on all three hosts; full release promotion NOT AUTHORIZED.** This is a source-specific improvement over O57 for stable NTFS directories, not a generic source-atomicity guarantee.

## Frozen provenance and scientific precedence

The independent O64 child PR [#419](https://github.com/FCMO-AI/.CMPCT/pull/419) has exact product parent O57 [#413](https://github.com/FCMO-AI/.CMPCT/pull/413) at `d9f9fa724c139c6281f0e2a92c66601bee912618`. O64 hypothesis [preregistered at `8d12adc537e77725fb32ba0c0174c32abaebd3d9`](2026-10-25-o64-ntfs-directory-admission-prereg.md), before editing Builder/helper. The independent O61-D/#416 native Win32 negative detected 676-byte nested-directory named stream omitted despite valid r24 archive; O61-D2 showed original regular-file guard returns ERROR_HANDLE_EOF=38 for a legitimate plain directory, so naive reuse is unacceptable. These negatives remain unchanged.

O64 implementation is source Git blob `b02a30d4ad1b26ea8eea49e11159113caebd6006` for `src/cmpct/builder.py` and blob `61d8cab1545c491da76b23ea89d4ca85d3030c5d` for `src/cmpct/ntfs_streams.py`. Executed exact source commit `722af3bda12962319c1046b7e6b9ff303d1d2e9a`; later commits only added new performance research infrastructure and this dossier, **not a change to these two product blobs**.

## Implementation

The existing `refuse_unsupported_named_streams(path)` keeps its regular-file contract. Optional `directory=True` recognizes native ERROR_HANDLE_EOF=38 **only when the directory's first stream enumeration is empty**, while refusing any named directory stream or unexpected enumeration error. The Builder checks source root before scanning, and nested directories before creating K_DIR records; existing O57 file-stream checks and O47 Win32 hardlink ownership remain intact. No change to r24 format, codec, Reader, Writer, native ABI, benchmarks or release comparison law.

## Actual result-bearing installed CI

Original GitHub-hosted exact-source [O64 court run #40171900048](https://github.com/FCMO-AI/.CMPCT/actions/runs/40171900048) completed successfully on **Windows 2025, macOS 14 and Ubuntu 24.04**. Repeated independent [push run #40171855864](https://github.com/FCMO-AI/.CMPCT/actions/runs/40171855864) also completed. True CPython package installed into `site-packages` outside Git checkout was asserted, not assumed. Both original O47/O48/O50/O57 tests and unchanged O61-D2 native false-remedy test were genuinely executed alongside new O64 tests.

| Host | Executed PASS | Platform-specific SKIP | FAIL / ERROR |
| --- | ---: | ---: | ---: |
| Windows 2025 | 14 | 6 | 0 |
| macOS 14 | 13 | 7 | 0 |
| Ubuntu 24.04 | 13 | 7 | 0 |
| **Aggregate** | **40** | **20** | **0** |

All 20 expected JUnit cases were enumerated per platform. Independent real Win32 stream API oracle confirmed **714 real bytes** on a nested directory; candidate refused before modifying a preexisting output sentinel. A distinct named stream on the **selected root directory** was also refused before publication. Empty root/nested/empty directories without streams were accepted. Hardlink identity was preserved, and independent equal-content file remained independent. Two complete supported archive builds were identical with SHA-256 `f502a1251c67e6ae020f337f509c7952bdc4d532fa9e7b03deb61e59c18e36b4`. Original O61-D2 confirmed the *unmodified* regular-file helper still rejects empty directories when incorrectly invoked without directory mode, while new mode admits them correctly.

**Scope:** these are candidate correctness and reconstruction controls, not complete Windows filesystem semantics, source-root ACL/xattrs proof, atomic snapshots, or official performance release evidence.

## Independent O64-E economics experiment and infrastructure negative

Prospective [O64-E preregistration](2026-10-25-o64e-directory-admission-economics-prereg.md) was written *before* its harness. O64-E is a separate same-host Windows 2025 comparison of historical O57 and O64 actual Builder, on one fixed tree per case (256 and 2048 empty dirs; 512 dir-plus-tiny-file entries), eight fresh-process ABBA observations/case, complete archive bytes/sha comparison, and wall/CPU/RSS accounting.

**Initial hosted O64-E attempts #40172222337 and #40172218232 failed before any valid observation.** Exact failure: using historical Python source directly via PYTHONPATH skipped its package-owned compiled native codec library, and importing the historical source raised `RuntimeError: package-owned cmpct_core codec library is missing`. This is **infrastructure/executable custody failure, not measured O64 product loss or a benchmark value**. The correction at commits `c2d9139d8331af69478bc1758132f6072d117039` and `6a69b3a7b4f5f12c13faca40eb8d3dc33747279f` builds two **separate native-bearing wheels from source-exact Git histories**, fingerprints each installed Builder/helper blob, and runs the same preregistered workload/order/comparators. No economic result or changed threshold is claimed until the new exact-head run completes. All original failed evidence remains preserved.

## Strongest negative, open debt and promotion law

- Static Win32 ADS enumeration is *not* a race-resistant snapshot. A path/stream can change after enumeration; the O52 source identity/TOCTOU defect is separately open.
- Non-NTFS volume, reparse/UNC behavior, Win32 failure classes and native directory ADS cross-filesystem capability are unverified. Unexpected enumerator failures reject and may reduce filesystem compatibility.
- The added API call per nested directory/root could materially impact huge tiny-directory trees. Until O64-E and full official ABBA complete, **performance is pending/unmeasured**. Do not count skipped official performance as approval.
- Inherited O47/O50/O57 source-pinned historic workflows reject changed Builder fingerprint as expected. Their failures are not grounds to weaken old validators or to declare successful end-to-end source composition. v0.30 stale fingerprint/surface historical CI obligations remain open.
- O64 is independent from owner O57 branch and other scheduled agents. Parent O57 retains authority; PR is DRAFT. No merge, version change, format change or release.

## Counterfactual and next action

The original independent source stream inventory would have caught O57's unreported directory ADS loss before archive hashing; the cheap O61-D2 valid empty-dir test would have prevented the naive guard regression. The successful candidate shows the smallest acceptable distinction: **file has a default stream; directory may have none**. No repeated systemic-process failure justifies editing the Discovery Engine law or STATE.json.

**Next executable:** finish/reconcile separately installed O57/O64 Windows ABBA economics at actual HEAD, then correlate with full inherited and official release gates. Promote only after source-ownership and performance obligations are met, respecting all preserved negatives.
