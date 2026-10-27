# O214 result — S_CDC exact admission / corrected source-identity differential

**Status:** confirmed narrow product candidate on O212 (#560), **not merged, not released**. Source-exact substantive CI and raw host artifacts on code/test HEAD `968436ad6634124cff6986211f3b643c31da9588` (2026-10-27 UTC). No release version or format revision change: v0.30.0/r24 remains shipping and v0.31 experimental.

## Question, controls and inherited evidence

Can the existing strict `_validate_storage` on O212's *same effective Reader index* reject malformed CDC chunk length descriptors before selective reads silently return incorrect bytes, without breaking valid CDC, the immutable three-codec r24 vector or inherited S_SPARSE admission?

Prospectively preregistered at `9c7efbd301ef6dd45eead413360857216e9d2c9c` **before** Reader edit `fe19b19e6be3bfc48f5226a88a314c79bf0aec35`. Parent O212 SHA `3249a7d6d09a9890cfa65b03e239a7973bf92614`, Reader blob `ee598eec46531c4da44d90d37b67f783b0ab3299`; candidate Reader blob `4d651674adfa39068e8faa1aaa44107776342a52`, validator unchanged blob `51c2849061f99a4afeddb7666956b24566ce7de0`.

Historical O201 #534 had a CDC range/full-read gap in Linux/macOS but its source fixture omitted root index `v:24`; Windows positive extraction was separately blocked by absent `os.fchmod` (#536). O202 had already identified the same missing-version confounder in older sparse research. O214 therefore separately authored **root-v:24 authenticated indices** and a frozen preexisting CDC fixture rather than inheriting that original evidence as fully schema-conformant.

## Product implementation and stronger alternative

One ordinary Reader admission conditional now applies existing `validation._validate_storage` to both `S_SPARSE` and `S_CDC` during O212's existing file-index traversal, before mmap, and closes the same source FD on exception. The validator is the existing canonical Python strict parser; it verifies CDC pair shape, positive integer length, valid blob reference, equality to blob logical size and sum to file size. There is **no new parser, source re-open, physical codec, archive grammar, benchmark threshold, Builder, native ABI or release change**.

Rejected simpler alternatives: two-pathname preflight has O208 source-identity gap; new CDC validation loop duplicates proven strict semantics; ignoring declared CDC length in `read_range()` leaves contradictory authenticated metadata accepted. Existing Rust native core's `STORAGE_CDC` parser independently requires blob-length equality and whole-file total (source inspection only; **not a newly executed native differential**).

## Hosted decisive results

[Exact code/test scientific court #40442474444](https://github.com/FCMO-AI/.CMPCT/actions/runs/40442474444) at source HEAD `968436ad6634124cff6986211f3b643c31da9588`:

| Host | New root-v:24 CDC tests | Unmodified O212 S_SPARSE tests | Result |
| --- | ---: | ---: | --- |
| Ubuntu 24.04 | 10 / 10 | 15 / 15 | SUCCESS |
| macOS 14 | 10 / 10 | 15 / 15 | SUCCESS |
| Windows 2022 | 10 / 10 | 15 / 15 | SUCCESS |

**75 passing test methods in all** (many new tests contain multiple hostile subcases). The new corpus authenticates head/blob/footer/index physical hashes, checks every possible small valid byte range, distinct and repeated blob references, early and later effective index, S_CDC descriptor under/overcounts/invalid types/indices/size, preserves source SHA, and consumes an **unchanged existing mixed RAW + Zstd + Deflate fixed CDC wire vector** from `tests/conformance/v24-chunk-maps.json`. Linux/macOS positive CDC extraction passes; Windows extraction remains intentionally unclaimed because #536 separately owns the preexisting `os.fchmod` fault, but Windows admission, full/range reads, verification and inherited sparse controls are exercised.

### Stronger causal A/B — distinct installed source, same authenticated bytes

The Ubuntu job separately installed genuine historical O212 and candidate CMPCT from exact Git commits into distinct site targets. The independent-process control verified actual installed source byte identity. It created two **real 452-byte root-v:24** files with the same valid RAW payload `ABCD`, one valid descriptor length 4 and one malformed declared length 1; original **same bytes** passed to both readers, with exact source SHA compared after runs.

- Valid archive SHA: `7357d55c81aa87e1a49f40c5eb56c30d8ba9de7d525294ab019adcb334114bdb`: both Readers' `verify/read/read_range(2,2)` pass and return `ABCD` / `CD`.
- Malformed archive SHA: `7aa563fbc4bff4bd77623d0c73c15c577c9f44012f13ebf19adee01a123eb627`: original O212 Reader **admits** and verifies `ABCD`, but `read_range(2,2)` silently returns empty; candidate refuses opening with `ValidationError: CDC chunk 0 length disagrees with blob`.
- Unchanged independent strict `preflight_archive` rejects the malformed file in both source environments.
- Installed historical Reader SHA-256 `7a7234be1974e2bb76ba8b8f7656c803e9932c5129da05074d53c44ebf2e6b95`; candidate `1d4740ee79a27c0647d3b4f761ca2636a940bad6e9c945077ae83d32b14a8be3`.
- Hosted machine-readable decision: `O214_DIFFERENTIAL=PASS`, `ROOT_VERSIONED_CDC_WRONG_RANGE_REJECTED_BY_CANDIDATE`. No source file was mutated by a Reader.

## Raw evidence custody

The exact-code-head original CI run `40442474444` produced three artifacts:

- Ubuntu ID `12706314290`, SHA-256 `68169120726e4ff058a380c7019daebff333cd532097f5eca4ddfda5a6032426` (includes full parent and candidate JSON).
- macOS ID `12707540681`, SHA-256 `e10cbfdb8a852a2870536e5089d4af8ee792b68aefa38c97d93d0f2759e0c920`.
- Windows ID `12707222140`, SHA-256 `1d1e2938f975df43d2dc8692690ab62e74d23b61d1e1a095b0821b05b604e04c`.

The three original artifact ZIPs were separately downloaded and checked against GitHub's SHA-256 digests, ZIP CRC, exact HEAD, actual Reader/validator/test blobs, complete test logs and independent same-input A/B JSON fields. The generated independent audit JSON SHA-256 is `8f70052968a255a257a96796f4c8d4c511730fe3313194f20dda337735653f9b`. This artifact audit establishes custody and reported-scoped semantic outcomes, not universal correctness.

## Negative evidence, alternative explanations and scope

Historical parent on the same root-versioned malformed archive **really returns wrong selective bytes despite full-read success**. Windows historical CDC extraction was red for an independent missing `os.fchmod`; no Windows extraction claim here. The new guard rejects malformed previously-permitted indexes by design, but does not prove that every unusual valid archive is compatible. The frozen three-codec CDC fixture and inherited S_SPARSE suite are meaningful compatibility controls, not an exhaustive corpus.

The current source-path two-read issue has been avoided, but **same-inode mutation after opening** (O208), mmap/SIGBUS, staged-publication identity (#528), large physical decoder RSS (O209), general parser hardening, complete hostile-source race safety and total product-resource bounds are not fixed. This is an admission guard, not byte-level source immutability. It does not improve compression and exports O(number of CDC descriptors) Python validation work at open; **actual cold-open CPU/RSS and product-size/throughput parity are unmeasured**. Administrative performance-workflow SUCCESS with substantive performance job SKIPPED does not count as a numerical release gate.

## Discovery lesson and outcome

**Primary question decided:** root-versioned CDC descriptor geometry can be rejected at O212's existing effective-index admission boundary using an existing strict validator; independent same-input parent/candidate experiment falsifies the simpler alternative that the original Reader was already safe. Counterfactual: an early root `v:24`/strict-preflight control on O201 would have exposed the fixture-schema confounder before cross-host experiments. This occurred in both O198 and O201: a reusable prospective research lesson is to validate *every mandatory format-root field* before treating independently hand-built wire data as fully conformant. The lesson remains recorded here; no evaluator, comparator, Discovery Engine policy or `STATE.json` mutation was earned in this narrow PR.

No duplication of O213's genuine 4GiB ZIP64 post-sparse-admission research; no changes to O212 parent, O193 owner, J24W02 extraction, or other concurrently active branches.

## Promotion debt / precise handoff

Reconcile [#564](https://github.com/FCMO-AI/.CMPCT/pull/564) (CDC sibling) with #560 (S_SPARSE owner) and O193 #521; obtain owner review and test the **combined** Reader against the already-owned O213 true 4GiB post-guard Builder/ZIP64 court, strict/native conformance, Windows composition, cold-open CPU/RSS with realistic CDC-index sizes, recovery, hostile archive resources, and official same-input release-parity benchmarks. General CI/format/release truth must be taken from the exact new HEAD after this documentary commit, not projected from the earlier source-head run.

**Scientific outcome: CONFIRMED narrow improvement. Product status: STACKED DRAFT, NOT MERGED, NO RELEASE.**
