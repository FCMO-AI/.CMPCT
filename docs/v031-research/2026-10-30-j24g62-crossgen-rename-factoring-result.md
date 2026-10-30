# J24G62 — no-added-byte cross-generation rename factoring, hosted three-host result

Date: 2026-10-30 UTC. Status: **RESEARCH MECHANISM SEED — NO PRODUCT MERGE / RELEASE / END-TO-END PERFORMANCE CLAIM**.

## Source and provenance

- Repository: `FCMO-AI/.CMPCT`; [Draft #804](https://github.com/FCMO-AI/.CMPCT/pull/804) stacked on #800 exact `fb5d96cdb8855fe3e01868792e65b79d3d61661d`, inheriting #795 fail-closed signed journal helper.
- Prospective prediction and kill criteria committed at `13bfa4574fd56af39475f3cb9e3bd5f64e06e148` before research implementation.
- **Actual result-bearing source HEAD**: `e3948f6dee571b7b682f72ae5016caf4b6e95d83`. [Hosted three-OS run #41001063304](https://github.com/FCMO-AI/.CMPCT/actions/runs/41001063304) **SUCCESS** for Ubuntu 24.04, macOS 14, Windows 2022; physical source pins validated for Builder, Reader, Writer transactions, shared replay, preflight.
- Current published `main@80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0, r24) untouched. This document is appended after result-bearing source, so any later documentary HEAD must not be substituted for actual measured SHA.

## The real question, not the seductive old headline

The ordinary public Writer emits **one operation per committed r24 generation** and a full checkpoint at generation 64 (#798). #797's 33.27× helper result required >=16 operations **inside one generation**; it is not a shipping Writer performance improvement. #800 isolated a material real Reader-open penalty on public one-operation 63-depth history versus an *extra* same-state synthetic checkpoint that added **12,659 physical bytes (+4.3294%)**. #801 attributed most excess to repeated replay on Ubuntu/Windows; macOS attribution was **inconclusive** against its predeclared perturbation cutoff. None of those experiments constitutes this one's measured speedup.

J24G62 compared the exact #795 helper applied successively to all 63 real physical one-op signed generations against a **single factored path→row map and one final sort**, with no emitted archive bytes. Both routes operate on independent deep copies of the same authenticated checkpoint index and chronological payloads. Fast-path admission rejects all non-one-rename generations, collisions, missing sources, duplicate base names and *any* sparse positional fsmeta entries. These cases use the inherited original helper without altering its semantic result or error.

## Source-exact measurements: replay-only, not Reader-open

The hosted source ran 8 alternating ABBA/BAAB blocks of four operations (32 raw samples per platform; 16 observations each arm). Each physical chain was built with genuine Builder + 63 public Writer renames, checked against Reader and preflight, original r24 footer and index SHA, exact member bytes, full MessagePack final-index byte equivalence and unchanged original physical archive SHA.

| Host | Original replay median | Factored replay median | Observed replay-only wall speedup | Worst paired 4-phase block speedup |
|---|---:|---:|---:|---:|
| Ubuntu 24.04 | 29.984458 ms | 5.366869 ms | **5.587×** | 5.447× |
| macOS 14 | 60.021000 ms | 8.144563 ms | **7.369×** | 4.988× |
| Windows 2022 | 64.996000 ms | 12.570750 ms | **5.170×** | 4.870× |

Unrounded medians and **all 96 raw wall/CPU observations** are in the original provider `j24g62-result.json` artifacts. Host CPU medians (original vs factored): Ubuntu 29.980115 vs 5.365286 ms; macOS 59.881500 vs 8.089000 ms; Windows 62.500000 vs 15.625000 ms. These are process CPU, not total archive creator CPU.

The measured `tracemalloc` peak was 1,283,872 B in **both** variants in all three hosted runs, reported as +0 B traced peak. This reflects the common deep-copy allocation dominating the traced maximum, **not** zero additional memory or an RSS result. No physical archive writing is performed by either replay algorithm. The real 63-delta archive was 292,396 B and the separately constructed synthetic checkpoint control was 305,055 B. That +12,659 B is fully charged to the checkpoint comparison, **not** a purported saving of the new factoring algorithm.

## Safety/adversarial evidence

Exactly 2,200 deterministic mixed-history scenarios per host passed differential parity (not 6,600 independent random distributions; repeated identical seed):

| Disposition per host | Count |
|---|---:|
| Admitted, factored, exact parity | 481 |
| Fallback: duplicate base path | 200 |
| Fallback: missing source | 194 |
| Fallback: not single rename | 372 |
| Fallback: positional xattr/owner metadata | 400 |
| Fallback: rename collision | 172 |
| Matched inherited error | 381 |

The original function's result/exception and lack of caller-input mutation were the oracle. Physical Reader/strong verify/preflight and independent SHA-authenticated footer parser came from the **inherited #800 court**, not a newly implemented second archive decoder.

Each hosted workflow executed an **in-repository standard-library-only raw receipt auditor**, which recalculated median/CPU/counts/decision and rejected **8/8 mutations**. All **three original provider ZIPs** were then downloaded and their SHA-256 verified independently; a separately authored offline standard-library auditor rederived the 96 observations, source/head/phase/identity/costs and rejected **10/10 hostile receipt changes per host** (30 total). This establishes independent *receipt arithmetic*, **not** a second physical archive execution.

Original artifacts and SHA-256 ZIP values:

- [Ubuntu artifact #12953313065](https://github.com/FCMO-AI/.CMPCT/actions/runs/41001063304/artifacts/12953313065): `e258ac87806ba9ffc10e4de1e951fcf2c04b812b0428b85da440500a856bca5d`.
- [macOS artifact #12952923002](https://github.com/FCMO-AI/.CMPCT/actions/runs/41001063304/artifacts/12952923002): `326131923706b98526731538d5bd821ceabf2a353d4c8950f59099215598198e`.
- [Windows artifact #12953278215](https://github.com/FCMO-AI/.CMPCT/actions/runs/41001063304/artifacts/12953278215): `9095e5605e866b0cf69501b466c2ecf24c6b6b8d857dbfb9fb38555825a8dac8`.

## Scientific decision, important negative and future action

**Research-only decision: BOUNDED_RENAME_FACTORIZATION_SEED on 3/3 hosts.** The preregistered >=3× and <=2 MiB extra traced peak hurdles passed in this narrowly admitted workload. The exact product-wide consequences remain **unmeasured**. The eligible class excludes sparse per-file xattrs/owner overrides, cross-generation put/del mixes, rename conflicts and richer hostile-history recovery; passing fallback tests does not make them fast. The helper is **not wired into Reader**. No end-to-end Reader cold-open, storage selectivity, full CPU/RSS, temp I/O, recovery, create/extract, native ABI, mixed real filesystem metadata, three-host installed package or strict official same-runner release parity has been measured for a candidate. Publication safety #749 remains independent. Baseline is allowed to win after full carrying cost.

Next highest-value executable action belongs to #795 owner: design a bounded **mixed-op, sparse-fsmeta-capable cross-generation replay architecture** preserving all signed grammar, logical identity, hardlinks, base-index offsets, recovery/rollback and 64th checkpoint semantics; apply existing #800 same-state physical court with installed Reader, measure actual cold-open, peak RSS, temporary cost, full archive bytes, and hostile recovery before promotion. Avoid merely transplanting this deliberately narrowed script into product.

Counterfactual lesson supported by #797→#798→#800→#801→#804: establish public operation geometry and instrument the actual cost owner **before** productizing synthetic helper speed. This is a local transferable lesson, **not** sufficient to modify the Discovery Engine's normative policy. There was no overlapping product implementation claim. Shared `docs/discovery/STATE.json` remains owned by #574 and was not overwritten.

**No merged product code, no format change, no release, no weakening of any evaluator or historical benchmark.**
