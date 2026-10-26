# O164 prospective decision: isolate Windows ZIP namespace semantics from inherited metadata failure

Date: 2026-10-26
Status: PREREGISTERED BEFORE INSTRUMENT / WORKFLOW

## Authority / exact source
This is a dependent, **diagnostic-only** child of O160 PR #499 at `03a82b5c1227ed37733d45c8ebe661dd871f5236`, Reader Git blob `f29885574c892a2c2dd819f13b7595d1af59a903`. Do not mutate this Reader, the original O160 test, the independent v24 golden blobs, or historic v0.30 contracts. Released v0.30.0 / physical revision 24 unchanged.

## Baseline and question
O160's exact-head Windows job `40280705125` verifies installed Reader custody successfully, then fails **before ZIP export** when the original O160 court calls `CMPCT.extractall` and Windows raises `NotImplementedError: utime: follow_symlinks unavailable`. Linux and macOS O160 jobs passed. Prior O102 PR #457 independently documents the Windows metadata-fidelity family. The direct-extraction failure is not evidence that ZIP canonical member-name serialization itself failed.

**Question:** for independent fixed revision-24 RAW/Zstd/Deflate goldens, does the unchanged installed O160 Reader export canonical ZIP member names/content on Windows through both fast and forced stdlib writers without depending on the separately red Windows direct-extraction metadata path?

## Prediction, controls, disproof
Prediction: 3 source-authenticated codecs × (unchanged, slash, backslash) × (fast, forced stdlib) = **18** ZIP-only name+byte+physical-archive-extraction cases pass on Windows. Three separately authenticated slash-vs-backslash canonical collisions are rejected *before creating output*. Strong controls: frozen source/index physical spans, installed Reader byte identity from Git SHA, external Python `zipfile` extraction, logical content SHA and exact extracted relative paths, both serialization routes.

**Falsifiers:** any ZIP member name retains a literal backslash, mismatch between independent source payload SHA and ZIP extracted bytes, unexpected extra files, unadmitted collision, wrong source Reader blob, invalid ZIP checksum, failed normal export, or setup/provenance failure. Never reclassify a setup/OS failure as a product win. Keep all raw observations.

## Alternative hypotheses and scope
- Original Windows red is genuinely caused by inherited direct-extraction timestamp API, not ZIP serialization (supported by original traceback).
- ZIP serialization may still fail independently on Windows after direct extraction is removed from this *new separate* question.
- Simple string-level `_zip_member_name` checks are weaker than creating an actual archive and extracting through independent `zipfile`; do not substitute them.

This does **not** turn O160's original Windows 3-host court green, prove physical direct-extraction parity, fix timestamps or xattrs, establish release acceptance, repair O157 stage-custody races, or prove Windows reparse/ACL fidelity. The stricter O160 `extractall(metadata=True)` failure must remain visible as a distinct unresolved platform gate. Do not modify the original comparator to obtain green.

## Execution / decision
Implement the smallest diagnostic instrument using the original O160 `rename_authenticated` and unchanged immutable golden; run on Windows 2022 with source SHA custody and CI evidence. If ZIP-only passes, release neither branch: tell O160/O102 owners the Windows ZIP-path decision was narrowed, with inherited metadata red intact. If ZIP-only fails, preserve exact source-backed failure and route to O160 owner.
