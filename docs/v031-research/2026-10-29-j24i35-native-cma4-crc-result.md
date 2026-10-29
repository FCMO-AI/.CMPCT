# J24I35 — installed-source CMA4 CRC-only integrity discrepancy

**Result class:** O0 scientific/interop negative, not a repaired product, exploit demonstration, release claim, or compression gain.

## Exact baseline, preregistration and freeze

- Published `main@80c358f8824ec1b20d349c92ed94c898090969b0`: v0.30.0, format r24.
- Scientific parent PR #759 exact `e67ed337e78e021ba91f7bc6bdc271ae0ddd6b51`; native lib source `463c50633be74423e92a074b7d7577db6a4b0cf9`, native strong verifier `cd1a367761465cbba3e8054f743af551c1e560e1`.
- Original immutable J24I35 prospective hypothesis: `e5827df975393530ff9c61b6c5b2d555a0d80f41`, written before research instrumentation.
- First result-bearing J24I35 installed Ubuntu 24.04 run **[40876241771](https://github.com/FCMO-AI/.CMPCT/actions/runs/40876241771)**, exact candidate `a15d391feadf9e17f593147af8607e38188b183f`, scientific job [123455669733](https://github.com/FCMO-AI/.CMPCT/actions/runs/40876241771/job/123455669733) SUCCESS, original artifact [12898003292](https://github.com/FCMO-AI/.CMPCT/actions/runs/40876241771/artifacts/12898003292), 10,122 bytes. Source-head, generator/referee blob SHAs, full first-party `CMPCT` observations, detached physical referee, actual compiled Rust stdout and all wire bytes in artifact.
- This result references the observed exact head, **not** a blanket approval of subsequent documentation/rustfmt commits or of the full suite.

## Observed question and verdict

The **same 27 logical target bytes and unchanged CMA4 SHA-256** are accepted by the Rust native complete strong verifier when **only the separate physical CRC32 field is wrong**. Python strong `CMPCT.verify()` rejects it. The preregistered narrow native/Python inconsistency prediction is **CONFIRMED on this genuine r24 RAW symlink / Ubuntu host**.

| Exact observed property | Valid control | CRC-only mutation |
|---|---|---|
| Complete stored archive | 883 B | 883 B |
| Archive SHA-256 | `8a1767b49b15b9c86b7ca78f0828a018915491a53044ff656a0b153676c1ba37` | `2b860821ed6260b7b582cb202fb586cc21a125b6c08c1950a5eee0d94b86fcc2` |
| Single changed byte | — | offset **424**, in CMA4 CRC32 little-endian field |
| Physical CRC32 | 2508103211 (correct) | 2508103210 (incorrect) |
| Decoded 27-byte SHA-256 | `b85c585a22a4d66b59e0680dcdcffa47e3477a4c9ad7380525704499815efb4f` | identical |
| Independent physical CMA4 SHA-256 | matches payload | unchanged, still matches payload |
| Both SHA-authenticated index copies / footer | valid | unchanged/valid |
| Installed Python `CMPCT.verify()` | accepts; count 1 | **rejects** `OSError: blob integrity failure` |
| Compiled Rust `Archive::verify_complete()` | accepts; count 1 | **accepts; count 1** |

The source-exact comparator also changed **payload bytes rather than CRC** in the inherited J24I30 `physical-wrong.cmpct` control; compiled native correctly returned `MemberHash`. The native verifier is **not** generally blind to payload corruption: this is specifically a second physical-integrity-field consistency gap. The one-bit CRC mutation changes no user bytes and does not defeat SHA-256; a valid stronger checksum already certifies payload identity. No practical attack claim is justified.

The independent non-CMPCT J24I30 detached auditor, reused without rewriting its semantics, authenticated original vs altered index/footer, confirmed the exact one-bit field change and classified only the changed CRC as invalid. All observed measurements are on a 27-byte RAW symlink, not on Zstd, Deflate, sparse, large chunked, hardlink alias, other OS, or released end-user native packages.

## Causal diagnosis / competing hypotheses

In `native/cmpct-core/src/lib.rs`, `checked_blob_layout` validates magic/codec/lengths and returns SHA bytes 32..63 but does not compare the separate physical header CRC bytes 28..31. Native `verify_complete` hashes returned data against SHA. Python `src/cmpct/reader.py::_blob` explicitly checks `binascii.crc32(raw)` against the physical CRC. This explains the observed differential. The alternative that native inspects CRC in another layer was experimentally **falsified for this RAW case**.

This finding is about **verification semantics**, not compressed-size performance. Whether strong verification *must* fail on CRC-only mismatch is a product/format compatibility policy decision: the existing Python behavior and fail-closed malformed-header discipline favor explicit consistency, while SHA already guards exact payload bytes.

## Cost, scope, debts and decision

- Current native candidate is not repaired; neither Builder nor Reader/native product code was changed by J24I35.
- A future native fix that separately recomputes CRC can add a scan over decoded bytes; sensible design would fuse CRC with SHA inside existing streamed verification and make any fast RAW read policy explicit. Whole-system CPU/wall/RSS/I/O, codec parity, portability, recovery and format grammar remain **unmeasured**. Do not presume zero overhead or use this one small RAW archive as performance evidence.
- Inherited #759 symlink SHA candidate remains a separate verified gain (its own exact-head two-host court #40869880905). Its known `b''` native parser discrepancy is unrelated.
- This experimental source keeps original archives, frozen controls, sample semantics and release gates intact; never publish under a numeric version without later integration and the official gates.
- **Next cheapest decisive action:** coordinator #755 evaluates whether physical CRC is normative for native complete verify, then if yes, choose a bounded **CRC+SHA fused single-pass** candidate in the existing native owner branch and test ordinary RAW plus compressed codecs against Python and the authenticated physical header. Reject simplistic whole-archive rehash before profiling.
- **Counterfactual discriminator:** source-level inspection of `checked_blob_layout` vs Python `_blob` predicted the exact one-bit mismatch without an expensive matrix, but the installed compiled binary and detached independent archive evidence were still necessary to establish real accepted/rejected behavior. No global Discovery Engine policy change is earned from this one episode.

## Exact-head CI distinction

On experiment head `a15d391feadf9e17f593147af8607e38188b183f` the specialized **J24I35 hosted scientific court succeeded**. General native-core formatting gate and Engineering Evidence initially failed **because of new test rustfmt and missing required PR dossier headings**; these are harness/evidence defects and have distinct corrections, not evidence that the CRC hypothesis failed. Preexisting general tests/published-lock epoch-custody red checks must not be weakened or classified as product regressions without comparing inherited source.
