# J24X01 — Prospective sparse extraction integrity / destination-custody falsifier

Date: 2026-10-27 UTC. **Preregistered before experiment code or result observation.** Science-only, independent of active sparse-geometry owners O212/O214 and Linux fd-publication owner J24F11. Baseline shipping `main@80c358f8824ec1b20d349c92ed94c898090969b0`; exact released Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8` and validator blob `51c2849061f99a4afeddb7666956b24566ce7de0`. r24 format, v0.30.0 release, main product/benchmark unchanged.

## Why now / PARETOBONK

Prior J24P03/P04 already retire unsafe name-stage overwrite and delimit namespace guarantees. O212 guards sparse *geometry* at Reader admission, not extraction integrity or destination atomicity. O216 is separately studying strict fixed-chunk reference validation cost. This experiment attacks a different high-consequence storage kind and evidence boundary, without duplicating those owners. Search of currently open issues/PRs finds no specifically claimed sparse logical-SHA extraction and destination preservation falsifier. Cheapest decisive evidence rung is two tiny builder-independent authentic r24 archives and an unmodified installed Reader. No large corpus, product patch or threshold needed.

## Baseline/source inspection

Released `CMPCT.read()` on S_SPARSE builds a logical byte string and compares SHA-256 to indexed logical digest. `CMPCT.verify()` calls read. `CMPCT.extractall()` instead branches on S_SPARSE to `os.open(destination, O_TRUNC)`, `os.ftruncate`, and write individual extents without an observed whole-logical-file SHA comparison. S_CHUNKS/S_CDC extraction uses verified temporary staging instead. This is a **static hypothesis**, not yet an observed product defect.

## Primary question and prospective predictions

Can the released ordinary Reader accept an authenticated r24 sparse index and then report extraction success for a logical file which its own read/verify rejects; and can corrupted physical sparse payload destroy a preexisting destination before detecting corruption?

- **Case A (logical commitment mismatch).** Build a *fully correctly checksummed* primary + footer index and valid RAW physical blob, correct extent shape and size, but intentionally put the SHA-256 of different bytes in the logical file row. Predict strict preflight accepts geometry and physical header; `read`/`verify` reject; `extractall(metadata=False)` exits successfully while the published target digest differs from row[5]. This tests logical consistency only, not adversarial signatures.
- **Case B (physical payload corruption).** Construct valid archive and mutate exactly one RAW payload byte *without* changing the indexed/recorded CRC; predict Reader `read` fails `blob integrity failure`; extracting into a destination holding an exact canary triggers the same error but destination has already been truncated/overwritten and canary is lost. The original source and corrupted payload offsets must be confirmed.
- **Controls.** Valid sparse logical file with leading/interior/trailing holes reconstructs exactly; `preflight_archive`, `read`, `verify`, `extractall` all agree; unrelated S_BLOB remains unaffected; original archive bytes and logical digests persisted.

**Kill / narrow:** If extractall fails closed with preexisting destination preserved in B or refuses wrong logical SHA in A, retire predicted defect and preserve negative. If source installation/provenance, archive parsing, or controls fail, classify *infrastructure/fixture failure* rather than product result. If the mismatch occurs, open a scoped issue and preserve the independent raw measurements without claiming a full-security attack, release credit or rate of real-world occurrence.

## Alternative explanations and safeguards

- Indexed SHA is metadata authenticated by the archive footer, not a signature; a malicious archive author may choose any digest. The significant property is **within-reader operation disagreement**, not third-party signature trust.
- `verify()` may be the only documented strong-logical-file authentication requirement; do not falsely assert that `extractall()` guarantees `verify()` semantics universally. Report exactly what occurred, contrast existing chunked transactional path, and leave an explicit product contract question.
- Explicit source-corruption scenario changes physical bytes while leaving header/CRC intact. This is not same-inode concurrent mutation or race, and says nothing about inode ownership.
- Source is unmodified. Release, on-disk revision, frozen fixtures, thresholds, comparators, public site and discovery policy stay unchanged.

## Evidence and future decision

Run the test on independently installed source (outside checkout) under Ubuntu and macOS where available; retain JSON, stdout, source hashes, platform, output bytes/hash and canary. Audit independently against preregistered outcomes, retaining any surprise. A positive result warrants a concrete separate fix/rehabilitation proposal that charges SHA for sparse holes (constant memory, potentially O(logical bytes) CPU), temporary I/O, RSS, atomicity, portability and 4GiB sparse economics. No current product claim or publication is earned by this experiment.
