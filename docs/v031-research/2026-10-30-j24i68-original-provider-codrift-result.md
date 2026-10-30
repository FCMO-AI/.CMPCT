# J24I68 — Frozen-source r24 ZIP co-drift is **not** a reliable per-cell CMPCT timing surrogate

**Date:** 2026-10-30 UTC. **Evidence class:** independent secondary analysis of pre-existing GitHub Actions physical ABBA artifacts; not new product execution, a benchmark gate modification, or a release milestone. **Preregistration:** [2026-10-30-j24i68-zip-drift-proxy-prereg.md](2026-10-30-j24i68-zip-drift-proxy-prereg.md) committed first at `f4e59ffd67f8a8ca78b1c0ec5fc72ffeecbbae94`. Source baseline released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/r24.

## Primary decision (prospective H1 falsified)

Original provider artifacts verified against the independently established SHA-256 digests, exact declared comparison HEADs, original `corpus.json` SHA, eight corpus labels, four original A/B snapshots and zero deterministic CMPCT archive-byte differences. The independent Python 3.11 referee in [research/j24i68_zip_proxy_referee.py](../../research/j24i68_zip_proxy_referee.py) parses original ZIPs with standard library only, recomputes both baseline and candidate medians over each of their A/B groups, and measures 32 matching CMPCT/ZIP timing cells **separately per hosted run**.

| Original provider ZIP | Both effects exceed 1 ms | Same-sign pairs | Spearman (all 32 absolute ms deltas) | CMPCT official >5% AND >3ms reds | H1 survives? |
|---|---:|---:|---:|---:|---|
| #835 artifact `12981944713` (FAIL) | 10 | 8/10 (80.0%) | **+0.255** | 2 | **NO** |
| #835 artifact `12986955317` (FAIL) | 22 | 18/22 (81.8%) | **+0.626** | 5 | YES |
| #837 artifact `12988780098` (PASS) | 6 | 4/6 (66.7%) | **+0.137** | 0 | **NO** |

**Result:** preregistered H1 requires >=75% sign concordance among simultaneously >1ms pairs **and** rank correlation >=+0.50 in **each** of the three original source-identical runs. Two of three fail; the universal ZIP co-drift per-cell proxy is **retired for this evidence family**. This is not evidence that ZIP is a poor competitor, that host drift does not matter, or that a specific official timing red is false.

For #835 first failing original, `tiny/library/create` CMPCT changed **+4.879 ms** while the matched ZIP control changed **−0.279 ms**; `nested/cli/create` CMPCT changed **+7.634 ms** while ZIP changed **+1.120 ms**. The former is a sign disagreement, the latter co-directional but much smaller; subtracting ZIP deltas from CMPCT would not give a universal causal correction. The second #835 run has five official CMPCT reds all co-directional with ZIP, demonstrating a useful *context observation* without satisfying generality across runs. The #837 run has no official CMPCT reds but unstable, low-amplitude co-drift.

## Block stability and hostile alternative

On the same 32 cells, the sign of candidate-minus-base changed across A versus B blocks in respectively **17, 8, 18 CMPCT cells** and **21, 10, 12 ZIP cells** for the three artifacts. These are within-run observations, not independent statistical replicates. The leave-one-corpus-out Spearman range was:
- #835 first: +0.186 to +0.357 (all below +0.50).
- #835 second: +0.459 to +0.714 (removing `combined` drops below +0.50).
- #837: −0.028 to +0.232 (all below +0.50).

An attractive pooled correlation would mask these incompatible per-run decisions and host CPU/chronology differences. The independently tested full-product gate retains **all** historical red outcomes; source-identical code is evidence of *attribution ambiguity*, not permission to override the official evaluator.

## Post-result exploratory mechanism split (not part of preregistered H1)

A separate **post-hoc** stress check on the same original cells splits CREATE and EXTRACT, retaining the same 16 corpus/mode pairs per operation (no newly collected observations). Spearman of raw millisecond effects and meaningful-pair sign agreement are:

| Hosted attempt | CREATE rho; direction among both >1ms | EXTRACT rho; direction among both >1ms |
|---|---|---|
| #835 original first | **−0.165**; 2/4 | **+0.744**; 6/6 |
| #835 original second | **+0.524**; 7/11 | **+0.803**; 11/11 |
| #837 original pass | **+0.350**; 3/4 | **−0.053**; 1/2 |

These counts show the mixed **create/extract mechanism and chronology** likely matters to any future timing surrogate. In particular #835 first reverses direction between operations, so even a ZIP correction calibrated on extraction would not reliably explain creation. Extraction has too few meaningful pairs in #837 and only three correlated hosted attempts overall; **do not promote a new extraction-only proxy** from this post-hoc slice. The prospective cross-operation H1 remains falsified as originally defined; no retrospective goalpost adjustment. Arithmetic checked with a separate unrounded rank implementation on the original parsed J24I68 rows. This is exploratory secondary research evidence only.

## Provenance and adversarial controls

Original provider ZIP digests, as previously authenticated in J24I65 and checked again before parsing:
- `12981944713` SHA-256 `cf20ded12b7e5b6348a9fc272cadc7565dc4e76982e1760fce674b1b2e7e1598`;
- `12986955317` SHA-256 `aedd2d6150746f5c6bcef4b0e8a41af5ed5f5c9f9fbb0c3ba78b54da59bbd1ee`;
- `12988780098` SHA-256 `1d43e55fb359db5ec779607d9da25508efe61bbaa6d5ba5c5665d8819999490b`.

All three use corpus tree `b0cc877945eb66602e9ac5e3d7626d3935462aed616ac6011de1afd57858688f`; 7,713 files and 303,738,466 logical bytes. Each ABBA has 8 corpora x 2 operation boundaries (library/CLI) x 2 operations (create/extract) = 32 cells. The earlier J24I65 source custody assessment separately established exact relevant source-blob equivalence; this new instrument additionally checks original recorded base/candidate Git comparison HEADs but does **not** independently repeat the full tracked-blob genealogy audit.

The hostile test refuses altered ZIP bytes, mismatched corpus digest, mismatched baseline source HEAD and mismatched candidate comparison HEAD even when an adversary updates the outer ZIP SHA expectation; simple rank-order controls prove the Spearman arithmetic. Reproduction:
```bash
python tests/test_j24i68_zip_proxy_referee.py
J24I68_BUNDLE=/path/to/J24I65_original_provider_bundle.zip python tests/test_j24i68_zip_proxy_referee.py
python research/j24i68_zip_proxy_referee.py /path/to/J24I65_original_provider_bundle.zip --selftest --output result.json
```
The new workflow retrieves immutable original GitHub Actions artifact IDs using read-only `actions: read`, verifies exact SHA before parsing, and uploads its research result. If provider retention has expired, this is an **infrastructure blocker**, not a scientific disproof. Historic original J24I65 bundle remains an independent rerun route; no CI re-generation of the benchmark is authorized.

## Decision, self-critique and handoff

The best current next discriminator for unresolved create reds is **CMPCT-specific** source-identical sham and process/lifetime diagnosis, not per-cell ZIP timing subtraction. Existing owner #819 has separate positive evidence of Python process-prefix cost (+7–9%); that mechanism is not proven responsible for any specific #835 or #807 red. #835/#837 own official r24/ZIP workflows, and #574 owns the discovery cache; do not duplicate their implementation. This independent diagnostic cannot decide physical RSS, page cache, native image identity during timed sections, or original official release gate acceptability.

**PARETOBONK:** Instead of another costly CI/ABBA repetition, this reused three real exact-input source-identical hosted results and falsified a broad potential analysis shortcut. No scientific policy change was earned: the existing rule to preserve raw data and never use noise controls to relax gates already covers the lesson. No product files, benchmark evaluator, comparator, semantic contract, output format or version changed. Scientific result: negative, decision-changing for the proposed *per-cell ZIP proxy*. Product result: none. Release authority: unchanged.
