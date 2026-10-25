# O55 — One captured-buffer VZIP reference oracle, source-coherent and byte-identical on fixed inputs

Date: 2026-10-25 UTC
Status: **RESEARCH/ORACLE POSITIVE ON 3 HOSTS; NO PRODUCT IMPLEMENTATION OR RELEASE CREDIT**
Preregistration: [O55](2026-10-25-o55-vzip-single-buffer-oracle-prereg.md), committed at `771941a104e9783cc6cebae8e46da24ff15b7d85` before oracle tests.
Result-bearing tested SHA: `999334c87b0e28b40063c894259dff7f009efdba`.
Exact O50 product Builder blob: `21a9ec696df13961c25301654feb607a7e161a4c` unchanged.
Hosted combined O54+O55 run: [40163684148](https://github.com/FCMO-AI/.CMPCT/actions/runs/40163684148).
Draft research PR: [#410](https://github.com/FCMO-AI/.CMPCT/pull/410).
Builder source-custody owner: [Issue #408](https://github.com/FCMO-AI/.CMPCT/issues/408), product PR #405.

## Primary question and result
Can the physical one-time `original` ZIP bytes **already loaded by the codec** serve as the sole authoritative byte sequence for ZIP metadata parsing and compressed stream slicing, avoiding multi-open temporal inconsistencies without changing archive output for immutable inputs?

**RESULT: YES, as a detached test-only reference, within three authentic ZIP representation classes and three host platforms.**

The reference function consumes `original: bytes` once, parses with `zipfile.ZipFile(io.BytesIO(original))`, reads raw member stream spans directly from the same `original` bytes, and reproduces `make_vzip_recipe`'s existing skeleton/recipe/stream ownership. It is injected into the unmodified real Builder through a test monkeypatch; actual original Builder, codecs, r24 archive materialization, Reader and integrity verifier remain in the installed CMPCT package.

### Source-exact independent hosting

| Host | Total O54+O55 cases | Immutable ZIP stored | Immutable ZIP deflated | Immutable ZIP mixed | After-capture same-inode mutation | Raw artifact |
|---|---:|---|---|---|---|---|
| Ubuntu 24.04 | **7 PASS/0 FAIL/0 SKIP** | exact whole-r24 bytes | exact whole-r24 bytes | exact whole-r24 bytes | exact original A reconstructed, SHA verified | `12587397699` |
| macOS 14 | **7 PASS/0 FAIL/0 SKIP** | exact whole-r24 bytes | exact whole-r24 bytes | exact whole-r24 bytes | exact original A reconstructed, SHA verified | `12587053300` |
| Windows 2025 | **7 PASS/0 FAIL/0 SKIP** | exact whole-r24 bytes | exact whole-r24 bytes | exact whole-r24 bytes | exact original A reconstructed, SHA verified | `12587402673` |

Each immutable class contained **3 ZIP members**, verifying real `S_VZIP` admission, complete unchanged CMPCT archive bytes from the original path-based codec versus one-captured-buffer reference, and actual Reader.read/verify against the original source content. Original ZIPs are built independently per host; **cross-host complete archive byte identity is not claimed**.

The after-capture mutation test maintains the same ordinary source `(st_dev,st_ino)`, pathname and physical byte size (13,441 bytes); exactly one regular-file in-place A→B overwrite fires *after the source snapshot was captured* but *before the reference recipe parsed it*. On all three hosts, the detached one-buffer reference emits a fully readable/verifiable real r24 archive of **exact original A**, while the physical source now contains B. The ordinary original O50 codec under the analogous O54 split-read produces an unverifiable r24 artifact. For O55, the oracle archive SHA equals that of the original stable A path-based Builder in its own environment.

### Genuine observed host example receipts

Ubuntu stable STORED r24 archive SHA `a9290157c527573f1522238ef70f559e308e7c2810967de68b7d945cef7b804c`, O55 same; DEFALTED SHA `f401b4f8221a822a887b8c956f4caba0399c412e45a937782e027f2f047be204`, O55 same; MIXED SHA `ab553efbb3e34babb967d6fa8942a261bb129ae3a654bd65f92f233c19b25b22`, O55 same. Ubuntu source captured A SHA `06cbd577eeea6a546d4169c3c3d83dbbf8c2ea98ff887cf7050544fbde5c65f3` and current B SHA `dda1e9934846de2e7be41666f6588b5c3a7d1b6a6095ba9f695d29e3e2a47d9f` differ; output SHA of original capture equals A.

Hosted artifact ZIP checksums from GitHub original CI logs:
- Ubuntu `31067e09d5f3cfaf499ac69ab3b9fa5ff2c670e0ec9d575f7889e48170e37630`;
- macOS `a7a87b789fb9e298c0cf9b9819643c175a4316823f645f903658b0d8d05b12dc`;
- Windows `2ab05a5651821b338460ddc5148d547d43965a5e38807b4098008192fa24b732`.
All three original artifacts contain JUnit and stdout scientific JSON; in the mutation case, `o55-result.json` is additionally emitted. A separate independent download-and-rehash audit of the artifact ZIP contents has **not** been performed; hosted logs and original artifacts are the direct evidence.

## Interpretation and cautions
1. **Scientific mechanism survived** a cheap decisive reference with full archive byte parity for the three hosted ZIP classes; avoids the *specific* split-open hazard while content is held in already-required memory.
2. **Does not yet fix CMPCT product.** This research function is present only in `tests/`, never in `src/`; product owner #405 must assess a real implementation, root containment O52, source-FD ownership, other representations, fallback paths and release gates.
3. **No guarantee of snapshot atomicity.** A mutable file can change during the initial `read_bytes()` or other files can change before/after. We only establish coherent use of captured bytes once the capture finishes.
4. **Potential future efficiency:** current codec executes several independent opens and reads despite holding `original`; reference eliminates source-file reopens **within the VZIP recipe**. However no measured syscall/CPU/wall/RSS improvement and no complete 15-row or r24/ZIP release benchmark. New memory views/copies and the later separate Builder `rawsha=p.read_bytes()` require explicit accounting before promotion.
5. Three positive ZIP families are not an exhaustive VZIP/WHL compatibility matrix. Deflate-level re-derivation, malformed metadata, ZIP64, extraction ratio, multi-entry paths, xattrs, deferred cohorts of 8+, and broad filesystem semantics remain product-grade test obligations. The oracle does not imply any decoder or format change.

## PARETOBONK decision and transfer
O54 first established a hostile source-data coherence loss that a **same-FD identity boundary alone cannot close** against same-inode content changes. O55's cheapest available remedy was a test-only single captured-byte frame, which produced exact parity and integrity on three hosts. This **changes the design preference** for the owner toward *one captured-byte authority per deferred ZIP encoding transaction*, before considering costly full physical snapshots. The counterfactual discriminator (each internal re-open despite owning a full buffer) is prospectively recognisable in code and transferable to other multiple-pass representations. It is a local scientific lesson; no unsupported normative Discovery Engine policy edit is earned.

No concurrent implementation collision with O50/#405 and O52/#407; product untouched; no release/version/format/comparator/evaluator change. O54 original negative remains preserved separately. Next cheapest owner action: implement/measure this narrow byte buffer seam under a descriptor-rooted original-source contract; test immutable whole-r24 parity and mutated-source case, then deferred cohorts/WHL/ZIP64, CPU/wall/RSS/temp-I/O, complete inherited gates. Research PR should remain draft and unmerged.
