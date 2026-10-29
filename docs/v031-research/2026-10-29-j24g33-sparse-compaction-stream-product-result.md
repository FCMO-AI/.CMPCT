# J24G33 — actual installed sparse-compaction candidate: source-bound result

Date: 2026-10-29 UTC  
Classification: NARROW PRODUCT-CANDIDATE EVIDENCE + CONVERGENCE; NOT RELEASE.

## Exact-source evidence
The candidate is stacked on #723 `52d51b9446dc8876319f7bd1e6ca2b7f54681de8`, published main `80c358f8824ec1b20d349c92ed94c898090969b0` unchanged (v0.30.0, r24). The complete Reader blob `b2b7774c13a5c8235ff89786d171b7ea3ff20710` is **byte-for-byte identical to original donor #613**, not a duplicate verifier. Builder/transactions remain #723 blobs `387192edd783e02bf7a44a38945214bf9d6c183e` / `8d1e46e1fdf408c1d95ce9091e25fa159f0e6264`. The unchanged donor frozen/hostile test blob is `dc31bd4a46c117e6621a76a91b7bdeef85579ebf`.

**Actual installed-wheel hosted experiment:** [Actions #40830587099](https://github.com/FCMO-AI/.CMPCT/actions/runs/40830587099) SUCCESS, exact HEAD `8778c0899ab712dff90697765bdc418f3f21f7ae`, Ubuntu 24.04 / Python 3.11. Real installed site-packages were independently compared byte-for-byte with the exact checkout Reader, Builder and transactions. Original [physical artifact #12878820861](https://github.com/FCMO-AI/.CMPCT/actions/runs/40830587099/artifacts/12878820861) retains source/output r24 archives, two child JSON receipts per size, original owner regression and donor test logs. Physical artifacts were produced by the genuine Builder, signed `append_update` and `compact_archive`, not simulated or AST-transplanted functions.

| Actual installed logical sparse case | Source bytes | Compacted bytes | Peak RSS, two fresh children | Compaction wall, two fresh children | CPU, two fresh children |
|---|---:|---:|---:|---:|---:|
| 2 MiB | 1,470 | 1,294 | 25,320 / 25,128 KiB | 7.313 / 7.022 ms | 7.080 / 6.772 ms |
| 128 MiB | 1,466 | 1,290 | **25,596 / 25,596 KiB** | **191.464 / 187.695 ms** | **191.153 / 187.212 ms** |

These times exclude the separate parent fixture creation and process startup. Memory is subprocess `ru_maxrss`, not a general memory bound for arbitrary archives. Both input cohorts have one committed delta; output generation depth is zero. Two independently run output archives per cohort had identical SHA-256. All indexed file rows, logical file hashes and authenticated metadata match input; source archive SHA was unchanged. The 2MiB physical data corruption negative was rejected while preserving existing output bytes. The entire imported donor frozen/hostile/256MiB test suite: **2 PASS**. Unmodified #723 eight-case compaction court: **PASS**, with source/destination semantics, hardlinks/symlinks, xattrs, data corruption and destination invariants as originally asserted.

## Comparative baseline and limits
Earlier separate scientific #734 [Actions #40827365924](https://github.com/FCMO-AI/.CMPCT/actions/runs/40827365924) A/B/B/A (128MiB) reported exact #723 historical Reader **279.125/279.270 MiB** peak RSS versus donor AST transplant **27.250/27.508 MiB**, same physical output per cohort. The current actual integrated candidate measured **25 MiB**; this is compelling causal transfer but those are **different runs/fixtures and cannot be treated as direct exact-input product speedups or a release benchmark**. An official source-identical product base/candidate performance gate was NOT run. No new storage-format or codec ratio credit is asserted. The journal-stripping source→compacted byte decrease is expected product behavior, not compressor domination.

The first candidate custom workflow run [#40830290900](https://github.com/FCMO-AI/.CMPCT/actions/runs/40830290900) failed configuration before any job because job-level `env` used disallowed `runner.temp` context; remedied with permitted `github.workspace` in commit `8778c089...`. The first Engineering Evidence run on `43d1ff52...` was RED for missing required PR dossier headings. Full, truthful PR evidence dossier was added; a subsequent exact-head Engineering Evidence run #40830687464 completed **SUCCESS**. Preserve those initial negatives, do not relabel them as passing evidence.

## Hypothesis disposition / governance
**Primary prediction supported on genuine installed Ubuntu for 2/128MiB sparse with physical custody.** Existing #613 mechanism is now an actual product-code candidate on #723 rather than a runtime-only research AST transplant. The local added tests show functional integrity, metadata, output determinism and bounded RSS in this finite regimen. It **does not** prove cross-platform, 4GiB sparse, sustained workload, complete performance, hardlink-sparse alias behavior or security against concurrent stage path rebinding.

#726's independently reproduced stage-name race is a **hard release blocker** regardless of this memory result. The current #723 inherited CI includes deliberate original-Reader source fingerprint; it is expected to reject this child until reconciled *under its owner*, without weakening original historical acceptance. Do not merge on this court alone. Native/General/Fuzz and official parity checks remain separately authoritative. No change to `docs/discovery/STATE.json` or frozen evaluators.

**Next unclaimed cheapest action:** owner #723 can adopt this exact Reader donor on an integrated, descriptor-bound stage/destination candidate after #726 race is fixed, then rerun this small physical court and source-identical larger held-out/performance/portability gates. No new sparse-verification implementation is justified.

Counterfactual: the earlier cheap 128MiB source RSS discriminator #731 and single exact donor #734 A/B would have saved duplicate mechanism design; both were consulted before this productization. No evidence-backed global Discovery Engine policy mutation earned.
