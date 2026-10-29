# J24G31 — independent physical ZIP-wire audit of J24G30

**Status:** scientific/evidence-only, exact tested product source unchanged; no merge/release/format/benchmark credit.  
**Question:** did J24G30's three-host success preserve authentic, independently decodable ZIP local/central records, physical checksums, signed calendar and unchanged normal-case bytes, beyond its own Reader/stdlib assertions?

## Prospective discriminator and source

An independent parser should reject any local/central mismatch, invalid Gregorian date in a **candidate** ZIP, corrupt raw Deflate stream, physical CRC, incompatible expanded logical SHA, malformed offsets/lengths/EOCD, or receipt inconsistent with original artifact bytes. A valid candidate should decode the same independently fingerprinted payload without importing CMPCT. A counterexample defeats a claim of ZIP-wire compatibility; absence of counterexample is limited to the seven tiny sampled artifacts.

Inherited source PR [#727](https://github.com/FCMO-AI/.CMPCT/pull/727), exact product HEAD `8581f1dee427e9ca7359e3c05bd514499471c357`, candidate Reader blob `cd6a2971396d6fe02a1d7f460d850107b3dcc397`, O149 parent Reader blob `496e70bdc06ddc17aa90e4fc0e9f10a6bc5c5332`. Hosted [Actions #40812726789](https://github.com/FCMO-AI/.CMPCT/actions/runs/40812726789) 4/4 SUCCESS; direct archived inputs and outputs came from GitHub, **not** reconstructed with the candidate Reader.

Original artifact ID / original GitHub archive SHA-256:
- physical archive+manifest: `12871265991` / `856777ebf5dcc1c2a7e85a4bb7b0fd5e7a15b3dbcbf6f94ab8eb4ddf68a7082a`
- Ubuntu: `12871102381` / `9a25d1ed4cf94c01b575d9cb21d0e91bc7632d86ceee4ac779a7e7d5743c840e`
- macOS: `12871166981` / `989b9cba84c1555d208a9864e63778ce5c47e08d8358025fc355a2b509767f8c`
- Windows: `12870519614` / `c13352d9f9c7e4ac88073888c40b20ce4cbb09770e07f2a3bc8a45771dbc84d0`

## Method and result (repeated observations are not independent products)

Read each original artifact ZIP as a **transport container only**. Independently parse each exported ZIP's raw LFH, central-directory header and EOCD using `struct`; check offsets, entry counts, method, bit flags, names, central/local equality, compressed-region ownership, terminator, expanded length, CRC32 and independently decompressed raw-Deflate payload SHA-256 against the original physical-input manifest. Check Gregorian validity and exact DOS dates without reading the Reader's output object; reconcile both original JSON repeats and installed source blob. Assert per-platform original-vs-candidate **byte identity** on ordinary 2020 and in-range 2107, candidate ZIP **byte identity across three hosts** for all seven cases, and that original Windows 1969 fails while candidate succeeds. No CMPCT import in independent parser.

**Direct local audit result (2026-10-29 04:28 UTC): 1,240 explicit assertions passed (including exact SHA-256 checks of all four original GitHub Actions transport archives); 41 independently parsed physical ZIP exports (14 Ubuntu, 14 macOS, 13 Windows); 7/7 candidate ZIP SHA identities across hosts; 4 source receipts per host; two original Windows signed-negative OSError observations.** All candidate parsed ZIP dates were valid Gregorian dates and matched the expected floor/ceiling and ordinary controls. The inherited POSIX baseline ZIP for 2108 leap day *actually contains invalid 2107-02-29*; this expected historical negative was preserved rather than relabeling it valid. All four original-transport artifact digests were revalidated as a hard precondition before parsing any claimed result; four separately altered provider ZIP envelopes were rejected by this check.

A detached adversarial suite altered the authentic 2020 candidate ZIP: local/central signatures, versions, flags, method, times, sizes, name, stream bytes, CRC, central offsets, EOCD/count, truncation/trailing bytes and a **paired local+central invalid leap-day** manipulation. **24/24 physically mutated inputs were rejected; clean control accepted.** Mutation-suite check is against the independent auditor itself, not proof of universal CMPCT/ZIPSafety coverage.

### Independent r24 custody and adversarial falsification (04:29 UTC)

`research/j24g31_cmpct_physical_oracle.py` is independent of the product Reader. It cross-checks the original provider digest; primary index, signed metadata, physical record header, payload, size, CRC and SHA; footer-authenticated tail index; and logical identity for every one of the seven original archive files. The externally invoked CLI `zstd` and third-party MessagePack decoder are dependencies of the **audit**, not of the candidate's reader.

`research/j24g31_r24_adversarial_tests.py` deliberately changes 19 source-wire fields in an original authenticated CMPCT specimen (header, compressed index, Zstd physical record/data, CRC/SHA, footer and truncation/trailing-byte checks). **19/19 mutated inputs were rejected by this detached strict physical envelope oracle; clean input passed.** This is **not evidence that the published Reader must reject every mutation**: its recovery law permits fallback from a corrupt index/footer to other valid generations. A strict forensic parser and a recovery-capable Reader have deliberately different acceptance semantics. Never substitute this oracle for the Reader's recovery regression suite.

`research/j24g31_transport_controls.py` flips one byte in each of the four outer GitHub Actions artifacts: all **4/4 source-provider tamper tests** fail the pre-parser artifact-digest check; clean originals pass. Overall separate negative tests: 24 physical ZIP, 19 strict CMPCT wire and 4 transport mutations. These are bounded reliability checks on the investigators, not a substitute for a corpus-scale security product court.

Reproduction from GitHub's original retained artifacts (IDs and hashes above, filenames `j30-physical-original.zip`, `j30-linux-original.zip`, `j30-mac-original.zip`, `j30-win-original.zip`):
```sh
python research/j24g31_independent_zip_wire_audit.py --artifacts ./downloaded
python research/j24g31_adversarial_tests.py --artifacts ./downloaded
python research/j24g31_transport_controls.py --artifacts ./downloaded
python research/j24g31_cmpct_physical_oracle.py --physical-artifact ./downloaded/j30-physical-original.zip
python research/j24g31_r24_adversarial_tests.py --physical-artifact ./downloaded/j30-physical-original.zip
```

**Exact original-host CI:** J24G30 physical hosted run #40812726789 completed 4/4 SUCCESS on source HEAD `8581f1d`. These J24G31 scripts executed independently in a Linux audit environment on original artifacts; **they do not represent a newly green exact-head three-host CI for the later research-only commits**. The candidate Reader blob stays `cd6a2971`. The prior generic General Tests job on original source HEAD #40812726901 definitively returned **816 PASS / 40 FAIL**: 36 missing attribution/fixture-provision requirements in generic invocation plus 4 pre-existing fingerprint/public-surface assertions. These remain real red CI; source-pinned historical O149/O140 jobs also remain red. No release, merge or full-product benchmark credit.

## Negative / costs / admission

This verifies **tiny, single-member, normal ZIP32 outputs** only. A second, separately implemented r24 byte parser now also verifies all **seven original CMPCT archives**, using `struct` for HEAD/blob/footer, external `zstd` for the physical Zstd streams, `msgpack` for independent primary/tail index reconstruction and own SHA-256/CRC32. This audit obtained **148 explicit successful checks**, confirmed one real 833-byte physical payload per archive and authenticated the signed nanosecond timestamp, physical blob and matching index/footer; its payload hashes match the producer manifest. That removes reliance on the Reader for the seven inspected physical content identities, but remains a narrow single-member r24 grammar check, not a general CMPCT decoder or a universal product claim. It does not evaluate >4GiB ZIP64 fallback, large file counts, generalized Deflate/STORE portfolio, full metadata/xattr/permissions, concurrent path swaps, crash durability, full-product CPU/RSS/I/O, or release promotion. These debts continue under their existing owners. The 1,240 ZIP-wire plus 148 CMPCT-wire assertions are internal checks, **not 1,388 independent experiments**.

The cheapest decisive control was inspecting the 188-byte physical ZIP wire objects already produced by #727 rather than authoring another ZIP exporter, editing source or re-running an expensive matrix. Result: extra confidence in the narrow calendar composition claim, **no change to product-selection policy or shared `docs/discovery/STATE.json`**.

### Independent mature ZIP consumer (04:31 UTC)

A third, externally rooted consumer path uses **Info-ZIP UnZip 6.00** (Debian build; 20 April 2009), not CMPCT and not Python's ZIP reader. `research/j24g31_external_zip_interop.py` extracts each original 188-byte ZIP directly from the four original Actions transport archives; runs both `unzip -tq` (physical CRC acceptance) and `unzip -p` (logical reconstruction) against the actual ZIP file; checks the reconstructed bytes with independent SHA-256 against the separately audited r24 physical payload identity. **All 41/41 physical ZIP exports passed Info-ZIP and reconstructed exactly the original 833-byte logical member** (14 Ubuntu, 14 macOS, 13 Windows; original Windows negative-epoch ZIP does not exist and is properly excluded). The consumer test does not claim preservation of future extreme ZIP filesystem mtimes; Info-ZIP's 2107 restoration limitation remains a distinct compatibility issue, nor does it certify ZIP64, directories, links or large archives.

```sh
python research/j24g31_external_zip_interop.py --artifacts ./downloaded
```

### Independent signed-r24 → ZIP filesystem-metadata continuity (04:33 UTC)

`research/j24g31_fs_metadata_parity.py` independently decompresses the *signed, authenticated original r24 primary index* with external `zstd` + MessagePack, extracts the true original file path/mode/size/timestamp and compares each actual ZIP central-directory field via raw `struct` parsing (without CMPCT or Python's inner ZIP reader). On the **41 original successful physical ZIP exports**, path, regular-file kind, Unix permission bits `0o644`, logical length and UNIX creator-system marker were **41/41 exact matches**. The separate calendar auditor already proves the candidate's bounded DOS-date transformation; this check does not equate DOS dates with signed nanoseconds. These seven samples contain one ordinary regular file, so it provides **no coverage** for symlink/hardlink tree semantics, ACL/xattrs, uid/gid restoration, filesystem writes, or unknown path encodings.

```sh
python research/j24g31_fs_metadata_parity.py --artifacts ./downloaded
```

## Handoff

Keep #727 DRAFT, the Reader source unchanged. Check actual inherited generic CI reds separately (they are not erased by this positive wire audit). For a decision-changing next experiment prefer real ZIP64 >=4GiB or a distinct adversarial filesystem path-custody experiment owned by its existing integration PR. Do not fork another calendar algorithm or infer release readiness.
