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
