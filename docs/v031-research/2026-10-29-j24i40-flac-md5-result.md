# J24I40 — real Builder FLAC internal-MD5 discrepancy; logical CMPCT SHA-256 preserved

Date: 2026-10-29 UTC. **DECISIVE SCIENTIFIC RESULT, NOT A PRODUCT DEFECT / SPEEDUP / MERGE AUTHORITY.**

## Source and evidence custody
- Scientific draft [PR #779](https://github.com/FCMO-AI/.CMPCT/pull/779), stacked on [J24I39 #776](https://github.com/FCMO-AI/.CMPCT/pull/776) at exact `0047e45e92793ca58a50251847e3cf1adb9c6d90`. Published `main@80c358f8824ec1b20d349c92ed94c898090969b0` = v0.30.0, revision-24.
- Prospectively pinned primary hypothesis, alternatives and negative outcomes: commit `26decb9dac7f2fe5952b3b8ef979d0119d15a9d9`, before the code/measurement.
- Source-exact instrument HEAD `03f8939418837b83e4e3d12be21a64d2fa43b275`; [GitHub Actions #40943497098](https://github.com/FCMO-AI/.CMPCT/actions/runs/40943497098), job `123692681787`, **SUCCESS** with checkout, source-pin check, genuine Builder generation, detached independent archive audit, Rust compilation, **all three actual comparisons**, fail-closed evidence packaging and artifact upload completed.
- [Original hosted artifact #12927298973](https://github.com/FCMO-AI/.CMPCT/actions/runs/40943497098/artifacts/12927298973); provider outer ZIP SHA-256 `d8981a0bdcf421bfdb7967fcfdc2db8aabe730ae2b7e1daebc1df2b3b159f890`; inner `j24i40-flac-md5-evidence.tar.gz` SHA-256 `61e83a0f6e0bceaae009314378b4b9abf682c669f13efd4c5e5d7914a3c65500`. Provider retention 30 days (through 2026-11-28); compact original-result custody in [`research/j24i40/hosted_md5_result.json`](../../research/j24i40/hosted_md5_result.json).
- All WAV/FLAC outputs originated with unchanged CMPCT Builder 8MiB PCM16 WAV and unchanged, independently audited revision-24 archive. Archive SHA-256 `9250964815f67891c3e106c9d87aadc67d4f2c3dce8b3e4e1873813a13a6fac7`, extracted original FLAC `d2126c870dcba10ad7f9d7b6caf83ca0c0df2815b9e47be343f3ed3b3b1355e8`, 3,982,561 encoded bytes.

## Actual pre-registered fork

| Identical-frame encoded FLAC | Physical change | Xiph `flac -t` | Compiled Claxon sample iterator + CMPCT logical SHA/CRC |
|---|---|---|---|
| Genuine original | None | **PASS** exit 0 | **PASS** exit 0 |
| `md5_flip` | Exactly 1 bit, byte offset 26 of STREAMINFO PCM-MD5 | **FAIL** exit 1, "MD5 signature mismatch" | **PASS** exit 0 |
| `md5_zero` | Only sixteen MD5 bytes set to zero | **PASS** exit 0, warning signature is unset | **PASS** exit 0 |

All PCM frame bytes remained **byte-identical** in all three streams; no modifications to authenticated CMPCT index, CMA4 or Builder source occurred. The original STREAMINFO MD5 was `0dedd25a319eefdf6fc912ff1b021645`, contradictory mutated value `0cedd25a319eefdf6fc912ff1b021645`. Precise mutant SHA-256 values, changed offsets and observed status codes are durably recorded in `hosted_md5_result.json`.

The **positive** is a narrow, real implementation difference: J24I39's Claxon sample iterator does **not validate the optional codec-private STREAMINFO MD5**; the reference FLAC test does. The primary prediction survived. **The negative that limits the finding** is equally important: the pinned Claxon oracle still computed exact original CMPCT **logical WAV SHA-256 and CRC32** and exact length, so this is **not a bypass of the CMPCT integrity identity**. A logical byte mutation would fail the stronger CMPCT SHA-256 comparison. No product Reader on a reconstructed mutant CMPCT archive was executed here.

## Primary standards/control and implications

[RFC 9639, STREAMINFO](https://www.rfc-editor.org/rfc/rfc9639.html) defines the 128-bit MD5 signature of unencoded audio. [Xiph `flac -t`](https://www.xiph.org/flac/documentation_tools_flac.html) describes checking that signature in test mode even when the compressed bitstream is decodable. The zero MD5 control matters: accepting an *absent* optional internal signature is not itself a defect; validity depends on which guarantee is actually promised. [Claxon API documentation](https://docs.rs/claxon/latest/claxon/struct.FlacReader.html) exposes a streaming sample iterator, but the decoder's returned PCM must be judged separately from the codec's internal metadata verification policy.

**Engineering decision:** Do **not** insert a second MD5 checksum pass, reject zero-MD5 streams or call this a product integrity vulnerability by default. Native owner #765/#759 should first decide whether the CMPCT strong-verify contract requires codec-private MD5 parity in addition to the already stronger logical SHA-256. If it does, a **single streamed pass** can update SHA-256, CRC32 and MD5 together, provided the additional CPU/memory/complexity cost is measured; source-FD and encoded-frame bounds still need independent proof. The lower-cost next target with larger product leverage remains original authenticated archive-FD-backed bounded FLAC consumption, not redundant hashing for its own sake.

## Limitations / strongest self-critique
- The mutation is an **independent split FLAC payload**, not a physically reconstructed CMPCT archive. This test does not cover archive-source mutation custody, index authenticity, CMA4 internal CRC header handling, partial range decoding, recovery, ABI, platform behavior or an exact-head product benchmark.
- The reference and Claxon have **different contracts**: `flac -t` tests FLAC's codec-internal MD5; the J24I39 Claxon oracle tests stronger CMPCT logical WAV SHA/CRC. Comparing exit codes demonstrates a **semantic policy difference**, not a fair all-system winner.
- File byte counts, hashes and experiment-source pins were checked; this court measured **no reliable create/extract CPU, RSS, cold-open or reader I/O**. Do not report zero cost.
- The scientific result applies to a true Builder PCM16 WAV + codec-2 file; more formats, source descriptors, malformed metadata and alternate FLAC variants remain untested.
- If canonical specification chooses decoded-logical integrity as the authority, this candidate is a scientifically useful **nonblocking difference** rather than a patch request. Do not grow product complexity merely to match `flac -t`'s broader codec test.
- No Discovery Engine policy change or shared state overwrite is earned: one source-exact decision does not justify a global process mutation.

## Counterfactual discriminator and future leverage
The prospective discriminator was *the original FLAC STREAMINFO field* rather than a synthetic tail: a single bit flipped in an otherwise byte-identical encoded audio stream. It distinguishes metadata-signature validation from frame decode without touching logical content, whereas tail corruption simultaneously affects parser termination and framing. Future decoder-integrity research should separate **encoded-carrier consistency**, **decoded logical identity**, and **signed/archive provenance** before calling one mechanism a missing proof.

The next dependency-safe material experiment is bounded **original archive-FD** FLAC decoding with full CMA4/index/source identity and true payload-limit enforcement, owned by Native Core. The scientific branch stays **DRAFT / NO MERGE / NO RELEASE**.
