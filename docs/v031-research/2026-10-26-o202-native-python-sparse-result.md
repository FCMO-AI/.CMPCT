# O202 — independent native/Python sparse-geometry admission differential (2026-10-26)

**Status:** HOSTED RESEARCH RESULT; PRODUCT REPAIR NOT IMPLEMENTED; no merge/release.

## Scientific question and authority
Given a revision-24 checksum-consistent archive with a correct **root version field**, does the ordinary Python Reader accept inconsistent declared sparse extent lengths while CMPCT's existing strict Python preflight and independently compiled Rust C ABI reject them? O198/#532 and issue #533 own the prior Python finding, O193/#521 owns the Reader product code, and O201/#534 independently examines CDC. This branch does not modify any owner product code.

The exact product reference is scientific parent O198 HEAD `16bfcf12adcb6cb1025896c4ece0f8aab7c79646`; canonical release remains v0.30.0 / r24 with v0.31 experimental frontier.

## Preregistration and custody
The experiment preserved its evidence-change history in order:
1. O202a initial prereg `5a594f4986cad99955deacab6d03fdec1a2186f9`, before any instrument was written.
2. O202b **superseding** prereg `f59a6ca5d5a777a018db0cc1944fc2f436b5474c`, written after discovery that the original O198 index lacks mandatory root `v:24`, and **before** the instrument introduced separately SHA-authenticated schema-normalized archives. The original O198 wire and its hashes are retained unchanged as explicit negative controls.
3. O202c **classification-only** prereg `efec0b5a3b6fcb6bf9dd05b24ae493be90484300` after observing the first hosted raw outcome and before correcting a too-narrow research label requiring the same message for two distinct forms of geometry rejection. The first raw result and classifier outcome remain retained.

**First hosted run:** [40389675515](https://github.com/FCMO-AI/.CMPCT/actions/runs/40389675515), evidence-source HEAD `d9a306fbf7269c84998915d4d1bfc2256b51a57b`; raw artifact `12683175050`, archived digest `sha256:098c403800fa609e127ca7223edf67af3328c180f907285b23bc34db01ee585b`. Hosted scientific job succeeded, but initial research classification was `UNEXPECTED_OR_CONTRADICTORY_DIFFERENTIAL_REQUIRES_REVIEW` solely because length=5 was correctly rejected by **bounds check** before the later length-equality check.

**Confirmed corrected run:** [40390449781](https://github.com/FCMO-AI/.CMPCT/actions/runs/40390449781), exact research source HEAD `bcfa6a19a3b17ddf687bf6f86d279022feb211db`; hosted substantive job SUCCESS; raw artifact `12682685934`, digest `sha256:aa9379bc66d1a9495fdec2398b62b2d5af11a5bd823061a099c28469c6846658`. Result label: `EXISTING_STRICT_VALIDATORS_REJECT_GEOMETRY_ORDINARY_READER_GAP`. Job inspected installed Python package and a real `cargo build --release --locked` Rust dynamic library through `ctypes`, with exact Git HEAD/prereg/source identity and unchanged-product diff. Workflow SUCCESS is **research classification**, not correctness certification of ordinary Reader.

## Observed four-way result on distinct version-normalized archives

| Sparse declared extent length; physical RAW logical length 4 | Ordinary Python `verify()/read()` | Ordinary Python `read_range(2,2)` | Existing `preflight_archive` | Actual Rust `cmpct_open` |
| --- | --- | --- | --- | --- |
| 4 (valid) | PASS, `ABCD` | `CD` | PASS | 0 (PASS); native selective `CD` |
| 1 (mismatch) | PASS, `ABCD` | **`00 00` WRONG** | `ValidationError: length mismatch` | -3 (FORMAT), no handle |
| 2 (mismatch) | PASS, `ABCD` | **`00 00` WRONG** | `ValidationError: length mismatch` | -3 (FORMAT), no handle |
| 5 (> member boundary) | PASS, `ABCD` | `CD` on this range | `ValidationError: overlaps or exceeds file` | -3 (FORMAT), no handle |

The new archives are not the old O198 byte streams: the original primary/tail index was reserialized with only an additional authenticated `"v":24` root field, recomputed index hash and footer, and **identical copied physical RAW blob record**, payload, logical hash and declared extent geometries. Each new SHA is recorded in the uploaded JSON. All 4 original O198 archives (even length=4) were rejected by both strict validators for absent `v`; ordinary Reader accepted them. Calling those original files fully schema-conformant would have been incorrect. The new indexed archives remove that confound.

## Decision
**Confirmed independently on native Ubuntu C ABI and installed Python:** the geometry rejection mechanism already exists in both `src/cmpct/validation.py` and `native/cmpct-core/src/lib.rs`. Ordinary Python `CMPCT.__init__` does not enforce the same index-level contract and can silently return different bytes on a versioned malformed sparse archive. This is an **admission/consistency gap**, not a lack of any geometry validator.

No second Python Reader algorithm was created, no production code modified, no benchmark/release rule altered, and `docs/discovery/STATE.json` left untouched because owner #440 maintains it.

## Counterfactual and strongest self-critique
Cheap source inspection of the root-schema requirement would have identified O198's missing `v` before the initial O202a prereg; inspecting the bounds-before-equality order would also have avoided O202b's over-specific reason matcher. In both cases, preserve the negative and show a preregistered updated question/control instead of retroactively rewriting results. This is a **local experimental-design lesson**, not evidence sufficient to self-modify global Discovery policy.

Four artificial, 4-byte members cannot establish prevalence, exploitation, full malicious-input safety, strict-platform generality, or product performance. The Rust result is from Ubuntu; prior Python O198 runs span three OSes but had the missing-root confound. Normalized synthetic archives remain hand-authored adversarial valid-root inputs, not proven Builder-generated. Full release-size/time/CPU/RSS, recovery semantics, ZIP64 4GiB regression and integration gates remain unmeasured here.

## Next cheapest engineering action
Within **current Reader owner #521**, examine reuse of the existing `_validate_storage` geometric contract at a bounded ordinary-open admission boundary rather than adding another on-every-`read_range` scan; preserve exception/fallback/recovery semantics. The existing preflight is broader than geometry (index, blobs, footer), so blindly invoking entire `preflight_archive` during open may duplicate parsing and extra I/O and alter salvage behavior. Measure valid large sparse index open CPU/RSS, full inherited exact-archive and 4GiB ZIP64 parity, and native/Python conformance before any merge. Keep CDC #534 and mmap/pub issues #528/#531 separately owned.

**Promotion:** none. **Format:** r24 unchanged. **Release:** v0.30.0 remains the last released checkpoint. **Research decision:** confirmed for the normalized sparse geometry cases; ordinary Python repair remains open in #533.
