# J24G101 — Hosted exact-head physical old-root lifetime result

**Research-only / no product, release, format, benchmark or merge credit.** Owner: [draft PR #876](https://github.com/FCMO-AI/.CMPCT/pull/876), stacked on [PR #869](https://github.com/FCMO-AI/.CMPCT/pull/869) at parent `281bf0332709b3de2ec2cb676753c44ac9e7eb2e`. Preregistered before experimental code in parent [comment #6537678039](https://github.com/FCMO-AI/.CMPCT/pull/869#issuecomment-6537678039) and immutable commit `05904b367f845e84a37ecfcda7df0dc47e3b627b`. Shipped v0.30.0/r24 main `80c358f8824ec1b20d349c92ed94c898090969b0` unchanged.

## Hosted result and exact source
- Source-exact physical Linux runner: [Actions #41159737669](https://github.com/FCMO-AI/.CMPCT/actions/runs/41159737669), **SUCCESS** on commit `194e0fac07e8e82ef848ee01b0f9d600a502ab29`.
- Original provider artifact: [#13026088827](https://github.com/FCMO-AI/.CMPCT/actions/runs/41159737669/artifacts/13026088827), 6,578,072 bytes, SHA-256 `34d6e991be6d4f8be0facaeb84a94cc0d5417b8141252f9d57294a9137a0f7e5`. Archived run receipt `j24g101_hosted.json` SHA-256 `842992905e5848a43f3aa245ce1cf6e14250a73ea1995957c3b4d571ad51796d`.
- Authentic physical inputs: PR #853 original exact `129edec976efe8bb604584517de39553487fec34`, Ubuntu-origin ZIP SHA `19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b` and Windows-origin ZIP SHA `c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab`. These are **different input origins, not separate execution platforms**.
- Each of 4 files has 64 signed revision-24 footers: checkpoint + 63 original public Writer deletes. All 12 physical ownership outcomes match preregistration (4 input archives × 3 modes): **tail-only pathname base: wrong old snapshot, detected and failed closed**; **root+tail FD pinned before gate release: exact earlier physical archive**; **versioned immutable root: same exact earlier archive**. New published generation also matches the original final archive bit-for-bit.
- The same-inode/in-place byte mutation hostile control, on a held shared advisory lock, was **detected 4/4** by SHA. FD+flock is not an immutability proof. Detached referee recomputed physical footer/delta/source SHA and rejected **7/7 receipt forgeries**. CI producer and auditor both completed successfully.

## Whole-system physical allocation counters
These are Linux `st_blocks * 512` at the moment **one old reader overlaps the new base**, including the currently selected root+tail+HEAD plus retained old root and old tail. They are **not bytes written to storage hardware**, and omit transient stage, directory and inode metadata.

| Genuine source | Current root+tail+HEAD | Old retained root | Old tail | Retained/current ratio |
|---|---:|---:|---:|---:|
| Ubuntu-origin 4,096 | 483,328 B | 466,944 B | 8,192 B | **1.9831×** |
| Ubuntu-origin 8,192 | 950,272 B | 933,888 B | 8,192 B | **1.9914×** |
| Windows-origin 4,096 | 450,560 B | 438,272 B | 8,192 B | **1.9909×** |
| Windows-origin 8,192 | 884,736 B | 868,352 B | 8,192 B | **1.9907×** |

The unsafe pathname-only strategy has a lower ephemeral allocated ratio **1.0086–1.0182×**, precisely because it does **not** retain the old root and therefore **cannot complete the historical Reader request**. A current-file-only byte counter makes this liveness loss invisible. The overlapping old-root ratio is a *differently priced ownership state* than J24G99's 1.004–1.019× current-only tailpack study. Single observed publish wall was 3.84–7.12ms by scenario; not a trustworthy performance comparison or benchmark.

## Important distinction and strongest objections
The proved failure is a **controlled, cooperative root rebase** causing a stale Reader to reject after checking the hash against its original manifest; **not silent acceptance of corrupted bytes** and not a confirmed defect of the **published** revision-24 CMPCT Reader (this architecture remains an out-of-tree research model). The previous original filesystem signed history is physically real, but the base/tail experimental layout is hypothetical. A held FD preserves old bytes against *rename*, not against an uncooperative in-place overwrite of its inode. A SHA in a same-UID writable HEAD file is not a trusted provenance root.

Publishing root bytes and HEAD in separate renames is **not crash-atomic as a pair**. The experiment models neither power loss nor multiwriter CAS nor hostile same-UID namespace churn. POSIX Linux only; no Windows/macOS runtime evidence; no complete Writer create/extract/CPU/RSS, release comparator or fixed-format integration.

## Architectural decision and cheapest next action
**Decision `ROOT_REBASE_TAIL_ONLY_READER_FAILS_CLOSED; ROOT_PLUS_TAIL_OWNERSHIP_SURVIVES` (O0 only).** If an archival representation adds physical immutable roots, a selected historical Reader must pin all referenced immutable components under a shared publication/GC handoff, or decline to promise historical reads. That requirement consumes ~2× active allocation even on these very short overlap tests if blocks are not truly shared. Do not equate source identity or held FD with immutability or trust. No change to Discovery Engine policy is justified by one study; #574 retains state ownership.

The highest-leverage route is convergence: existing contiguous append + optimized Reader [#823](https://github.com/FCMO-AI/.CMPCT/pull/823) avoids this extra storage/protocol altogether. Important independent product safety debts remain committed ancestry [#857](https://github.com/FCMO-AI/.CMPCT/issues/857), cooperative multiwriter CAS [#290](https://github.com/FCMO-AI/.CMPCT/issues/290) and verified publication [#749](https://github.com/FCMO-AI/.CMPCT/pull/749). Do not start a further rolling-tail threshold variant without decision-changing product evidence.
