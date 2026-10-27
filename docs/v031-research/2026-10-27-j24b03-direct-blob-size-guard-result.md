# J24B03 — Three-host direct-blob size custody verdict (exact-head science)

**Recorded:** 2026-10-27 UTC. **Status:** VALIDATED NARROW SAFETY FIX / DRAFT, not product promotion.
**Repository authority:** shipped `v0.30.0`, r24, `main@80c358f8824ec1b20d349c92ed94c898090969b0`. Proposed Reader/source exact head tested: `f9e95633db832b6c2ab95de8d7aaaf80c4b3ece8` in [PR #609](https://github.com/FCMO-AI/.CMPCT/pull/609). Historical J24B01/J24B02 [#604](https://github.com/FCMO-AI/.CMPCT/pull/604) and issue [#605](https://github.com/FCMO-AI/.CMPCT/issues/605) are preserved.

## Primary result — source-exact three-host admission

[Actions #40546227217](https://github.com/FCMO-AI/.CMPCT/actions/runs/40546227217) **SUCCESS** on Windows 2022, Ubuntu 24.04 and macOS 14, CPython 3.11. All three job logs independently show:

- unchanged `main` Reader source loaded from `frozen-baseline/src/cmpct/reader.py`;
- candidate loaded from `src/cmpct/reader.py`;
- 24 byte-identical Builder-independent signed-index r24 file/codec cases on each side, six valid geometries preserved, eighteen over/under/zero-length contradictions rejected by the candidate at every designated boundary;
- 2 original RAW reads spilling into the following encoded index are reproduced by the unchanged released Reader, with the candidate rejecting them;
- 2 malformed physical RAW-header controls rejected before candidate selective range access, including while released preflight already rejects;
- 2 valid empty-owner controls and three Builder-independent frozen direct-codec vectors accepted on both sources;
- stand-alone stdlib receipt referee reports `J24B03_SIGNED_DIRECT_BLOB_SIZE_GUARD_CONFIRMED_IN_COURT`, `referee=PASS` on all three OSes.

Hosted raw job artifacts from that run: Ubuntu `12751869077`, Windows `12752917767`, macOS `12753247788`. These are research/conformance receipts, **not** full product release or benchmarking evidence. The exact historical J24B01 preregistration prediction that preflight would reject the oversized file remains falsified.

## Distinct inherited/general CI debt

At exact head `f9e95633...`, [General CMPCT Tests #40546228047](https://github.com/FCMO-AI/.CMPCT/actions/runs/40546228047) yielded **782 passed, 4 failed**. The failures were:
`test_historical_native_materializer_is_release_fingerprinted`,
`test_surface_revision_records_attribution_campaign`,
`test_authoritative_v2_classifier_is_release_fingerprint_driven`, and
`test_release_fingerprint_covers_r25_oracle_and_android_custody_inputs`.

The four test-file blob SHAs and the two relevant `SURFACE_REVISION` and `experiments/entropygraph_v030_release_lock_strict.py` blob SHAs are **identical on published main and on the tested candidate** (verified with source fetches on 2026-10-27 UTC). The failures concern old fingerprint/surface expectations rather than the two J24B03 Reader/validator mutation surfaces; however, absence of an independent full main-job replay means the failures are best described as *inherited source-level gate debt*, **not** an exact historical baseline-run differential result. They are not silently waived.

[Native authority #40546227584](https://github.com/FCMO-AI/.CMPCT/actions/runs/40546227584) also **FAILED** during a `set -e` multi-command authority precheck. The logs print the full shell script but **do not identify the particular command that returned exit code 1**; it is therefore invalid to assign the failure specifically to `git ls-files`. Independently, the `native/cmpct-portable/Cargo.lock` blob is present with identical SHA `82c1bf519312492aab839bd572af9807c887be1d` in both released main and candidate. This check remains RED, cause undetermined without command-level tracing or a controlled replay. Native Core, the J24B03 three-host tribunal, version discipline, CI topology and engineering evidence passed. Exact product promotion remains blocked by full applicable gates, regardless of whether these preexisting red checks are unrelated to this patch.

## New prospectively charged performance discriminator

A separate [J24B03-P preregistration](2026-10-27-j24b03-direct-range-cost-prereg.md) was committed at `1118618fdd52933522e1813b709e0ffb882fb5a2` **before** the new [ABBA instrument](../../research/j24b03_direct_range_cost.py) and [independent referee](../../research/j24b03_direct_range_cost_referee.py). It isolates fresh-process source-exact repeated RAW read-range CPU/wall and fixed offset/correctness on the same physical images, plus diagnostic Zstd/Deflate. Its comparison is **not** a replacement for canonical same-corpus full Reader performance and release parity. Consult the resulting exact-head run/artifact before drawing a performance conclusion.

## Scope, negatives and handoff

This repair enforces authenticated direct `S_BLOB` logical/physical size equality for ordinary files and symlinks and bounds RAW BHDR reads. No Builder, index, codec, archive byte, ABI or format-revision mutation; no additional logical full-file SHA on ordinary RAW ranges. It does **not** prove immunity against mutable backing files, signed hardlink alias-size inconsistencies, other storage modes, all hostile parser inputs, or release parity. Adjacent hardlink alias-size work is already claimed by [J24B04 PR #610](https://github.com/FCMO-AI/.CMPCT/pull/610); do not duplicate it.

**Next:** decide raw-guard measured CPU/wall; if material, seek an equally safe cheaper physical ownership proof rather than deleting the guard. Coordinate a minimal composition into multi-owner [Reader #569](https://github.com/FCMO-AI/.CMPCT/pull/569), itself blocked by independently measured 27–28× cold-open structural validation debt. Preserve current draft until relevant safety, portability, extraction, fingerprint and official promotion gates are genuinely discharged.
