# J24I47 — full-member integrity and sublinear range observation: an exact contract boundary

Date: 2026-10-30 UTC. **DERIVATION + TOY WITNESS + FULLY CHARGED METADATA FLOOR ONLY. NOT A PRODUCT WIN OR FLAC-INTEGRATION RESULT.**

- Source authority: released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, revision-24, v0.30.0; active native candidate #788 at `2a6dbd5407731c5660faf71d04a4ef5de2d431bd`; preceding source-exact FLAC experiment #796 at `6d8fe62c9fecdd5c75cb1fc38387d9e20c6d894d`.
- Prospective prereg: [J24I47 preregistration](2026-10-30-j24i47-selective-integrity-prereg.md), committed before this instrument at `394957b32edeec33af3a896e6c9fcc2a3a95a8b5`.
- Reproduce locally using only Python standard library:
  `python research/j24i47/j24i47_integrity_bound.py --manifest research/j24i47/source_j24i46_generation.json --out /tmp/j24i47-result.json`.
- Original J24I46 creator metadata was copied as immutable research input (SHA-256 `72af642c6193587ca226e2be40e9fc05d7e042fbe125069cad1261b6972d9111`) from physical receipts. It names two **different measured compressed inputs**, not two different candidate product implementations. Research-only code generates *new synthetic byte-array controls*; it does not decode these FLACs or rebuild a CMPCT archive.

## The distinct proof question

J24I46 showed a 4KiB early FLAC seek could return correct bytes when a late compressed frame had changed, while full decoding rejected. A fresh exact-source inspection of #788's `native/cmpct-core/src/lib.rs` narrows this to the **direct compressed WAV/FLAC read path**: `decode_wav_flac_blob` authenticates the entire decoded WAV, then `read_blob_range` slices it. The public native `Archive::read_range` does **not** universally promise full-member validation: its RAW path reads only requested physical bytes, and chunked/sparse paths decode intersecting physical regions. This asks a strictly narrower foundational question **before** building FLAC islands, range-Merkle records, seek maps or a new API:

> Can a per-query range operation guarantee that *any* corruption anywhere in the addressed member is detected, if the physical member is mutable and untrusted and a proper subset of it can remain unobserved?

**Answer under those exact assumptions: no.**

Let the original physical member be an N-byte string `B`, metadata/commitments `M` fixed from `B`, and a deterministic verifier `A(B,M,q)`. Suppose on a clean member and query `q`, A accepts after observing proper subset of payload byte positions `S`. Pick `j` outside `S`. Construct `B'` differing from B *only at j*, with M unchanged. The verifier's entire adaptive transcript on B' is identical to its transcript on B: each requested position, every observed value, its control flow and final decision match by induction. Thus A accepts B', contradicting the asserted detection of any changed member byte. This holds even when M contains a checksum for **every segment**, a Merkle root, or a valid authenticated index, because the altered payload position j is never inspected.

For randomized zero-false-negative algorithms, condition on any fixed random tape whose clean execution skips a byte; the same adversarial trace defeats guaranteed detection. Sampling may offer probabilistic detection, not the exact fail-on-any-corruption contract.

This is an **observation/assurance lower bound**, not a theorem that seeks or Merkle proofs are useless. A Merkle proof can authenticate the *touched* leaf. It does not say whether a separate untouched leaf has been corrupted *since* the commitment. A trusted **immutable** previously fully validated source, a genuinely charged whole-file scan at open, or a different explicitly weaker local-integrity API can change the assumptions; an in-archive root or signature alone does not observe later changes in unread bytes.

## Executable independent witness

The script constructs two distinct 32MiB synthetic members (periodic and fixed-seed pseudorandom), a 4KiB request at 25%, a one-bit mutation at 85%, and a separate one-bit mutation inside the request. For each 4KiB, 64KiB and 1MiB chunk size it builds a complete per-segment SHA-256 commitment table from the clean source.

**6/6 observed executions** had: original accepted under both local and full SHA; late corruption accepted by *selected-segment* SHA but rejected by *full-member* SHA; selected-region corruption rejected by both; late-corrupt requested bytes still identical. The precommitted digest-table root is unchanged in the late-corrupt control. No positive product-integrity credit: this model does not parse FLAC, CMPCT, CMA4, index, or footer. The general claim rests on the proof above, not the toy sample count.

The script returns a structured JSON with complete source hashes, queried interval, late-mutation position, coverage, controls and cost rows. Original local output SHA-256: `ccd9d1f164805935f0b355b7a81bdce8d96753979005ee98e0c6e99933326ab5`. Verify the **GitHub-hosted exact-HEAD result independently** before promoting this SHA as cross-host evidence; successful local results alone are not hosted CI success.

## Independent current-code assurance matrix (source audit, not a new product test)

**Exact source controls:** native candidate #788 `2a6dbd5407731c5660faf71d04a4ef5de2d431bd`, [native `lib.rs` 464–540](https://github.com/FCMO-AI/.CMPCT/blob/2a6dbd5407731c5660faf71d04a4ef5de2d431bd/native/cmpct-core/src/lib.rs#L464-L540) and [638–706](https://github.com/FCMO-AI/.CMPCT/blob/2a6dbd5407731c5660faf71d04a4ef5de2d431bd/native/cmpct-core/src/lib.rs#L638-L706); released Python [`reader.py` 128–175](https://github.com/FCMO-AI/.CMPCT/blob/80c358f8824ec1b20d349c92ed94c898090969b0/src/cmpct/reader.py#L128-L175), [222–274](https://github.com/FCMO-AI/.CMPCT/blob/80c358f8824ec1b20d349c92ed94c898090969b0/src/cmpct/reader.py#L222-L274), and [483–489](https://github.com/FCMO-AI/.CMPCT/blob/80c358f8824ec1b20d349c92ed94c898090969b0/src/cmpct/reader.py#L483-L489).

| Current path | Bytes checked by partial read (source inspection) | Detect arbitrary corruption outside addressed range? |
|---|---|---|
| Native direct RAW | Requested RAW bytes, with authenticated-index/blob-header cross-check | **No**; unread RAW payload is not hashed by that read |
| Native direct WAV/FLAC codec 2 | Complete decoded WAV + stored SHA-256 before slicing | **Yes within the decoded member when complete strong check succeeds** |
| Native direct Zstd/Deflate | Complete decoded physical blob with expected SHA before slicing | **Yes for the decoded physical blob** |
| Native fixed/CDC/sparse | Only intersecting physical blobs, with per-blob checks; full-member logical hash when requesting the entire logical extent | **No** across unintersected chunks/extents |
| Python direct RAW | Direct `mmap` slice after reading physical header; no per-request CRC/SHA of that slice in `read_range` | **No**, even selected-byte digest is not asserted on this shortcut |
| Python direct compressed | Full `_blob` decode, decoded size + CRC32; `verify()` performs whole-file SHA separately | CRC32 of the addressed physical blob, **not strong SHA by that read alone** |
| Python fixed/CDC/sparse | Only overlapping `_blob` decodes, CRC32 per touched blob | **No** across unseen blobs |
| Python `verify()` / native `verify_complete()` | Complete logical member reconstruction and SHA-256 check | Distinct explicitly complete-verification operation |

This is a **source-inspection-only** matrix for named snapshots, not verified runtime coverage for every codec/form or every corruption class. In particular, the exact assertion "all `read_range` modes provide full SHA member integrity" is **false**. The meaningful engineering question is not how to circumvent an invented uniform guarantee; it is whether to retain direct codec-2's existing stronger incidental assurance, or deliberately expose a separately named and precisely specified local range contract. That distinction should be reviewed with the Reader owner before any architecture change. No source behavior was changed.

## Explicitly charged optimistic index-size floor

Using the J24I46 measured compressed sizes (stereo 12,164,541 B, mono 15,113,811 B, both 33,554,432 B PCM), charge per logical chunk **32-byte SHA-256 + 8-byte offset + 8-byte length**, plus a 32-byte root. No gifted free hash/index. This is a lower-bound *bookkeeping exercise*; a real decoder may need much more.

| Logical chunk | Records | Added bytes | % existing stereo FLAC | % existing mono FLAC |
|---|---:|---:|---:|---:|
| 4 KiB | 8192 | 393,248 | 3.232740% | 2.601912% |
| 64 KiB | 512 | 24,608 | 0.202293% | 0.162818% |
| 1 MiB | 32 | 1,568 | 0.012890% | 0.010375% |

**Uncharged and NOT proven:** the compressed-frame dependency span required to hash a logical segment; frame seektable; actual per-segment CPU/RSS/materialization; physical authentication/proof paths; codec capability and portability; index compression; update/recovery; correct original-source ownership; full Reader open/list/extract; cold cache. The storage floor alone **does not** show local-authentication product admission or equivalence to the inherited full-member guarantee.

## PARETOBONK decision and strongest self-critique

- **Retire** “add Merkle/chunk hashes so *unchanged full-member-corruption semantics* can be checked with an isolated partial read of an untrusted, mutable, unvalidated physical member.” Exact same-contract sublinear read is excluded by the transcript proof, not by a tuning parameter.
- **Preserve** “add optional *selected-range integrity* under an explicitly different API, or introduce a separately provable immutable/pinned source / previously validated state.” Both require legitimate semantics, source-custody and holistic economics decisions. Avoid an unauthorized silent contract weakening.
- **Prefer convergence** of #788/#765 owned complete-verification work over creating an overlapping new native codec implementation. The old full-SHA route remains the safe default.
- **Source limitation and independent correction:** confirmed by direct source audit at #788 `2a6dbd5407731c5660faf71d04a4ef5de2d431bd`: `lib.rs` lines 328–354 (`decode_wav_flac_blob`), 464–504 (`read_blob_range`) and 638–702 (`read_range`). Codec-2 direct read checks complete decoded SHA; RAW only reads the selected bytes; fixed/CDC read only overlapping chunks. **Consequently global member integrity is not the uniform `read_range` contract across all representations.** The theorem excludes a *drop-in replacement of direct WAV/FLAC's existing stronger implementation behavior*, not legitimate locally authenticated range reads elsewhere. A carefully specified new codec-2 local-integrity API might align with general reader locality, but still changes codec-2 observed corruption behavior and needs explicit semantics and regression review. The toy witness is not a physical FLAC attack; recorded J24I46 seek speedups are not product speedups.
- **Counterfactual:** asking “must a query detect mutation of bytes it never reads?” immediately after the J24I46 negative would have falsified the strict-equivalence architecture cheaply, without another giant FLAC bench. No normative Discovery Engine policy change is earned from a single deductive observation.
- **Concurrency:** #788 owns production; #796 owns the independent seek experiment; #574 owns discovery-state reconciliation. No edit to any of those source/allocator surfaces. No merge, format, ABI, release, test threshold, or frozen benchmark changes.

## Next highest-leverage action

1. For existing strict read contract, close source-exact #788 full-verifier and installed-package gates, rather than pursuing a mathematically incompatible sublinear substitute.
2. Only if product strategy explicitly wants a *different* range-local assurance contract, preregister a realistic 64KiB-segment authenticated-seek prototype with fully charged physical decoding granularity and cross-platform proof/integrity semantics; require real archive traces and broad held-outs before changing any format.
3. Reconcile active PR/head/CI before any subsequent shared edit. The data cache `docs/discovery/STATE.json` is staleable and intentionally untouched.


## Hosted exact-source evidence and independent second-root audit

Hosted GitHub Actions [run #40993980828](https://github.com/FCMO-AI/.CMPCT/actions/runs/40993980828) completed **SUCCESS** on exact scientific head `4e13ff911bb17efc0f81c2938ab14d43a94cffdf`. The executed J24I47 Python producer, manifest, checksum control and independent mathematical receipt auditor all passed; GitHub retained the [source-exact artifact #12950900575](https://github.com/FCMO-AI/.CMPCT/actions/runs/40993980828/artifacts/12950900575) (7479 uploaded bytes). The program reported 6 local-vs-global witnesses, 6 fully charged optimistic metadata cost rows, and result SHA-256 `ccd9d1f164805935f0b355b7a81bdce8d96753979005ee98e0c6e99933326ab5`.

The physical GitHub ZIP was separately downloaded and audited outside the hosted workflow with `research/j24i47/j24i47_independent_artifact_audit.py`. Independent checks covered ZIP CRC, all expected ZIP members, complete nested tar source/input/result receipts, Git SHA source identity, the pinned J24I46 manifest, exact numeric recomputation, the six integrity controls and a clean-process **byte-identical reexecution of the producer source actually inside the artifact**. Full durable audit: `research/j24i47/independent_artifact_audit_result.json`, status `PASS`. ZIP SHA-256 `e699b6002407e9ae5d1fb2bc6edb28945a5a9ad74c1af99d644dad32b1946a6b`; nested tar SHA-256 `25729b1d1c453509e3a4e1b77913362cd1bba773a532bd2e0e5e41c27717f001`. The source exactness of later **document/auditor-only commits** does not turn this into a new product test; the scientific producer is unchanged, and any current-head gate is a separate CI claim.

The strongest negative survives intact: a small Merkle/hash metadata premium alone does not provide member-wide mutation detection on a mutable untrusted file if unread bytes never enter the query transcript. The source-level assurance matrix above restricts this statement to codec-2's current complete-per-read semantics, **not** every raw/chunked/sparse range method.
