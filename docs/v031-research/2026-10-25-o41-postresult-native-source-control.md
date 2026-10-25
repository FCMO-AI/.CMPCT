# O41b — prospective stronger native byte provenance after O41 first hosted PASS (2026-10-25 UTC)

**Status before O41b code change: prediction only.** This is a scoped post-result adversarial review of evidence witness O41, not a rewrite of the original O41 preregistration or scientific O33 record. O41 original source-bound Actions #40147672182 already passed 96 original ABBA observations and 5/5 tamper controls, and its original artifact/receipt remain immutable.

## New causal gap
The first O41 witness checks that a reported child native module is any existing file under its verified source root. This does not reject a **same-source wrong file** such as `src/cmpct/native_codec.py`. The original O33 instrument itself loads a real `cmpct_core*` library and reports the path, so the original O41 evidence is useful; however the subsequent custody validator currently lacks a distinct suffix/name/file-hash check. It is therefore weaker than a statement about authenticated native binary *bytes*.

## Predicted repair and falsifier
For exactly the unique base and candidate loaded native module paths in original 96 records, require direct package `src/cmpct/` parent, `cmpct_core` prefix, a supported Linux native library suffix `.so` (current O41 workflow is Linux-only), and identical path across all child rows for each actual source. Hash each native module **after** measured subprocesses finish (outside timing), and store its SHA-256 and size in a source-bound witness. Bind historical O31 native path/SHA against the independently generated original `base-native.json` wheel-materialization receipt. Add sixth hostile mutation `wrong_native_same_source` (an existing non-library Python module under the same allowed source), which MUST fail. Retain original five hostile controls, archive SHA, Reader Git blobs, original O33 instrument and all thresholds, source group alternation, original raw measurements, platform bounds, product/format/release law.

## Decision / possible negative
O41b passes only if original plus sixth controls reject, actual native binary hashes exist and base witness matches the wheel receipt; if not, preserve error and no enhanced native-byte custody claim. No source changes to Reader/Builder/Writer/Rust/native, no release authorization. Ensure workflow classifier covers the new tool before invoking a deep CI run; do not count skipped jobs.
