# J24F07 — Authentic bounded RAW + Windows fd-mode composition result

Date: 2026-10-26
Status: **SCOPED THREE-HOST SCIENTIFIC PASS — DRAFT, NOT RELEASE**
Question preregistered before source change: `docs/v031-research/2026-10-26-j24f07-raw-win32-prereg.md`, commit `1da186ce326e37331b4af0d46d0a59e0885ff5e1`.
Scientific source HEAD: `d440b9da7548f8535e1e0532f882d51fc369ea4c`.
Source Reader Git blob: `a29421456c7c8d46157490fa03594a4c620a483d`.
Parent J24F05 #540: `1885cb0658cacd34a50d05e45b541ecb76fc8497`.
Independent Win32 control J24W02 #536: `7973dbf904ff0660971d2e112d9f77b38f37019a`.
Repository: `FCMO-AI/.CMPCT`; published v0.30.0, r24 unchanged.

## Problem and discriminating mechanism
J24F05 passes authentic immutable 64KiB RAW source-pwrite controls but invokes `os.fchmod` unconditionally, which is absent on Windows Python. J24W02 contains the narrow descriptor-bound capability check but not J24F05's mmap-hash/write ownership repair. J24F07 composes just the existing `getattr(os,'fchmod',None)` check into the bounded Reader; **the RAW transfer, SHA, length and publication path remain byte-identical to J24F05**. No general catch or stage-path reopen is allowed. Candidate patch modifies only `src/cmpct/reader.py` under `src/`.

## Original hosted proof
[Exact-source GitHub Actions scientific run 40404584164](https://github.com/FCMO-AI/.CMPCT/actions/runs/40404584164): 3/3 completed SUCCESS (Ubuntu 24.04, macOS 14, Windows 2022), installed Python 3.12 package **outside checkout** and authenticated reader SHA equality to exact HEAD. `fchmod_available=false` observed on Windows; true on Ubuntu/macOS.

### Material decision-bearing observations
- **33/33 inherited standalone J24W02 checks:** eleven per host from unchanged frozen-wire `S_CHUNKS` and `S_CDC` archives plus authentic Builder chunked archive. Native and absent fd-mode, proper POSIX chmod, both `OSError` suppression and unexpected `ValueError` propagation, corrupted destination preservation and complete SHA.
- **6/6 newly constructed genuine r24 large RAW cases:** independent `S_CHUNKS` and `S_CDC` each of logical length **8,617,989 bytes** on three hosts, indexed source content and extracted output SHA256 `dfd8aa2e2d0e0ebc1b5aa2df47f25564b5ed356a5595dc3f361c4c7acaea76e5`. Exactly **132 private stage writes per case**; max write **65,536 bytes**. Bytes/archived SHA identical across hosts for each representation.
- **16/16 adversarial source-pwrite scenarios:** eight original inherited J24F05 tests per POSIX host; same source-mutation/test conditions and original pass/fail assertions, only Reader fingerprint switched. Already-copied-window alteration published exact indexed SHA; future-window alteration failed closed and preserved pre-existing destination. An independent external process changed the original archive inode content by design.
- **Independent standard-library audit: 210/210 checks PASS** on the three *downloaded original* hosted artifact ZIPs; reconstructed deterministic SHAKE-256 original input and independently validated checksum, source identity, mutation, coverage, write bounds, negative behavior, SHA and cross-host fingerprints. Audit file `j24f07_independent_artifact_audit.py`, full JSON `j24f07_independent_artifact_audit.json` kept as supplemental local receipt; mechanism/artifact evidence is native GitHub authority.

| Host | Original artifact | ZIP SHA-256 |
| --- | --- | --- |
| Ubuntu | [12691515494](https://github.com/FCMO-AI/.CMPCT/actions/runs/40404584164/artifacts/12691515494) | `d696874e1eb8db86a1daad9e3479161e750f0b1f895d00bf2954bad0ec15d8ee` |
| macOS | [12690601312](https://github.com/FCMO-AI/.CMPCT/actions/runs/40404584164/artifacts/12690601312) | `2c7a606d6bec540ff32e7b014dab9bef8c1c124361e5193a8912eb17cb09865b` |
| Windows | [12690440734](https://github.com/FCMO-AI/.CMPCT/actions/runs/40404584164/artifacts/12690440734) | `449b6474dfd8436df5b2c81053c0c886e250930487b7e0952402e97c94c802e4` |

## Exact scientific HEAD CI truth, not promotional claims
At `d440b9da...`, scientific J24F07, Native Core, Continuous Fuzzing, CI Topology, Version Discipline, R36 Attribution all **SUCCESS**. General Tests **782 PASS / 4 FAIL** (v0.30 historical release-fingerprint/native-materializer custody, stale surface revision, release-fingerprint event/topology coverage; existing historical check files), not a green suite. Engineering Evidence **FAIL** at the original run because the initial PR body lacked explicit required evidence-section headings; subsequently added those headings to the PR metadata without modifying code. Historical J24F04 and J24F05 exact-Reader-blob scientific workflow jobs **FAIL** their frozen identity checks on the child source as designed; those original real test assertions were independently rerun by J24F07 with the new Reader fingerprint. Performance workflow has administrative SUCCESS but numerical performance job **SKIPPED**; therefore **no same-input ABBA performance result** exists for J24F07.

Any new doc-only commit after `d440...` advances Git HEAD but does not retroactively make the old scientific CI exact-head for the new commit. New checks must be observed separately, not guessed.

## Strongest negative and boundaries
No proof of **complete Reader process RSS** or CPU/wall: J24F06 PR #543 owns identical-archive full-process J24F04/J24F05 comparison. The J24F05 inherited tracked Python heap peak ~0.20 MiB for large source-mutation controls **is not RSS**. No protection against independently proven post-SHA stage-path/inode substitution [#528](https://github.com/FCMO-AI/.CMPCT/issues/528), same-inode mmap truncation SIGBUS [#460](https://github.com/FCMO-AI/.CMPCT/issues/460), or entire directory tree transaction. A writer must still have permission to mutate the source inode to exercise the modeled threat. Windows metadata/ACL restoration not proven. Release gate and general identity reds remain unresolved; do not merge/release.

## Decision and next executable frontier
**Mechanism composition is supported on three installed hosts** and no narrower direct program bug was observed in this court. Preserve this minimal candidate, reconcile historical CI authority rather than weakening it, complete J24F06 physical economics/official numerical parity, and coordinate separate verified-inode publication fix (#528) and source lifetime contract (#460) before a broad safety/release claim. Owner handoffs were posted to PRs #540 and #536. No `docs/discovery/STATE.json` modification; no discovery-policy lesson earned beyond existing identity-before-credit practice.

Counterfactual: after J24F05 passed Ubuntu/macOS, a single installed Windows source-exact minimal-API test would immediately have exposed missing `fchmod` and the disjoint J24W02 correction; composing existing independent fixes is lower-maintenance than designing another extractor. This transfers as a prospective early capability-admission and source-custody check, not a modification to release policy.
