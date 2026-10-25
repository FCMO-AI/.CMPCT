# O57 — Confirmed focused Win32 NTFS named-stream refusal; full release debt remains

Date: 2026-10-25 UTC. **Status: product candidate validated within focused court, DRAFT / NOT PROMOTED.** Original prospective research/prediction/preregistration in [O57 prereg](2026-10-25-o57-win32-ads-failclosed-prereg.md) commit `8e2d6804fdccb28792df5c60e9d0bb7016640299`, before product modifications.

## Inherited exact scientific failure and honest baseline

The immutable O50 Builder [#405](https://github.com/FCMO-AI/.CMPCT/pull/405) at `17c96603e33b02b3f2f9e0079eec2b128f293be8` / Git blob `21a9ec696df13961c25301654feb607a7e161a4c` silently archives NTFS regular files with **4,096 default-stream bytes and an additional 331-byte named $DATA stream**, produces an authentic SHA-verifying revision-24 file, but restores only the default stream. Original independent [O56 #411](https://github.com/FCMO-AI/.CMPCT/pull/411), source-exact actual Windows [run #40164441760](https://github.com/FCMO-AI/.CMPCT/actions/runs/40164441760), **3/3 genuine tests PASS, no skips**, provides a hardlink variant and ordinary no-ADS positive. [Issue #412](https://github.com/FCMO-AI/.CMPCT/issues/412) records the scoped product defect. O52/O54 active-source mutation is a separate open correctness problem.

## Smallest candidate change and mechanism

O57 adds `src/cmpct/ntfs_streams.py` and one Windows-only regular-source admission call from `src/cmpct/builder.py`. The helper uses real Win32 `FindFirstStreamW/FindNextStreamW` through ctypes, allows only `::$DATA`, and raises `OSError` if any other named stream is discovered, or if enumeration fails. No colon-filename heuristic, fixture-specific marker, decoded representation or format revision was introduced. POSIX is a no-op. Original O47 Win32 physical hardlinks, O48 unsupported special-file refusal and O50 composition remain inherited unchanged.

Exact product source measured at executable HEAD `f765a2b48fe5224943d28c9d0ce77d096de8a829`:

- Builder Git blob **`7a13545c7dc22ea973f90930fae6cf053f13f1f2`**; diff from O50 consists of one import, explanatory comment and one admission call.
- New Win32 helper blob **`23207ac06797fb21322cf327e97928fdbb5241c2`**.
- O57 source test blob **`abd88c8c7394fac15d4d98a5f3cca0844bd8dff6`**.
- Original O47, O48, O50 science test blobs all source-locked unchanged by hosted workflow.

## Real installed product result

Source-bound three-platform [GitHub Actions run #40164888267](https://github.com/FCMO-AI/.CMPCT/actions/runs/40164888267) on executable HEAD `f765a2b48fe5224943d28c9d0ce77d096de8a829` ran Python 3.11 **installed outside checkout** and checked exact Builder/helper/test Git blobs, whole inherited O47/O48/O50 focused tests and O57 source tests.

| Platform | True JUnit tests | PASS | Expected classified SKIP | FAIL/ERROR |
| --- | ---: | ---: | ---: | ---: |
| Windows 2025 | 14 | **9** | 5 (POSIX-specific originals) | **0** |
| macOS 14 | 14 | **12** | 2 (Windows NTFS cases) | **0** |
| Ubuntu 24.04 | 14 | **12** | 2 (Windows NTFS cases) | **0** |
| **TOTAL** | **42** | **33** | **9** | **0** |

Original retained evidence:
- [Windows JUnit/log artifact #12587816637](https://github.com/FCMO-AI/.CMPCT/actions/runs/40164888267/artifacts/12587816637).
- [Ubuntu artifact #12587209895](https://github.com/FCMO-AI/.CMPCT/actions/runs/40164888267/artifacts/12587209895).
- [macOS artifact #12587139983](https://github.com/FCMO-AI/.CMPCT/actions/runs/40164888267/artifacts/12587139983).

Confirmed focused behaviors: authentic Windows NTFS named-stream regular file is rejected before a new output appears; same for a hardlinked source while a preexisting destination sentinel remains unchanged and source hardlink persists. A genuinely ordinary no-ADS hardlink tree restores exactly, retains independent equal-byte nonlinks and produces identical complete archive bytes across two reproducible builds. Original O47/O48/O50 focused controls continue to pass.

## Exact-head CI and inherited provenance collision

The three-platform **O57 specialized** court is substantive PASS for product candidate only. The original **O47 and O50 workflow identity locks reject the modified Builder Git blob**; they are source-specific historical owner checks and should not be weakened or relabeled as passing. The new O57 court executes their original test assertions with the new source, but does not abolish the need for future source provenance composition. Engineering Evidence and Version Discipline passed at executable HEAD; the r24/ZIP workflow may be administratively green with its benchmark substantive step skipped. No release-performance credit is claimed from skipped work. Full General Tests, Native Core and Fuzz statuses must be rechecked separately on exact HEAD before promotion.

## Main negatives and criticism

- **Portability/availability debt:** on Windows filesystems whose FindFirstStreamW enumeration is unsupported or fails, the new guard rejects even otherwise ordinary source files. This is intentional fail-closed safety but may be an unacceptable product compatibility tradeoff until volume support and error classification are measured.
- **Unpriced performance debt:** one extra kernel enumeration for **every Windows regular entry including hardlink aliases**. No same-runner paired large-small-files CPU/wall, peak RSS, syscall count or full ZIP performance comparison yet; no assertion of neutral Windows economy.
- **Completeness limit:** named streams on directories, other reparse/object kinds, root metadata, ACLs, EFS, remote SMB/ReFS, mutation after check and concurrent same-inode content changes are not covered. The **source archive cannot claim all Windows filesystem structures exact**. Existing live source custody [#408](https://github.com/FCMO-AI/.CMPCT/issues/408) and O54 are independent.
- **Version/release:** r24 unchanged. No numeric version, merge, release or publication authorization. The product candidate is valid only for the tested static NTFS regular-file admission predicate.

## Decision / next action

The original silent-loss defect is conclusively supported by native NTFS witnesses. O57 is the first *product candidate* to reject it while preserving the inherited focused platform tests. Promote only after owner reconciliation and a broader Windows platform/volume and directory-stream admission audit plus paid full release metrics. If per-file enumeration is too expensive, consider a rigorously verified capability-gated inventory strategy **without returning to silent failure**, and measure the full cost. The low-cost control remains O50 with unmodified source; do not tune benchmark thresholds or workloads.

## Discovery Engine counterfactual

A native stream enumeration check of the source inode, before treating `stat/read` as a complete source object, would have detected the omission without a compression benchmark. This prospective observation transfers as a *question* across platform metadata models, but a global discovery-policy change is not earned from one defect family. There was no concurrency collision requiring shared-state mutation, no change to `docs/discovery/STATE.json`.

**Result classification: focused product evidence positive; generality/Windows compatibility/whole-product economics unresolved; release/product-published credit zero.**
