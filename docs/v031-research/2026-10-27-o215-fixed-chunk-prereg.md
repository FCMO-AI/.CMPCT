# O215 — fixed-chunk logical-size admission contract (preregistered)

Timestamp: 2026-10-27 UTC. Owner: independent Phased3 v0.31 fixed-chunk invariant. Parent: O214 #564 at `d90dab60d2fe646dbda9e61de3b5080ca83c7b7e`; derived branch `agent/phased3-v031-o215-fixed-chunk-same-index-admission-20261027`. Released v0.30.0 / r24 remain unchanged.

## Primary falsifiable question

Does the ordinary Python Reader accept an authenticated revision-24 `S_CHUNKS` descriptor whose *declared file size* differs from the sum of its referenced physical blob logical sizes, even though `cmpct.validation._validate_storage` rejects it? If so, can the O212/O214 same-effective-index admission gate be extended to `S_CHUNKS` without duplicating validation or reopening the pathname?

The O214 Reader checks `S_SPARSE,S_CDC` only. `S_CHUNKS` uses the physical blob lengths for `read_range`; `verify()` hashes the reconstructed bytes and may not compare the declared size. Predicted hostile: one real RAW blob `ABCD` (4 bytes), valid root `v:24`, declared logical size 5, logical SHA-256 of `ABCD`, a correctly SHA/CRC-authenticated index and records. Parent is expected to accept, `verify()` to return one success and `read_range(name,4,1)` to return `b''` despite an in-bounds request; strict preflight should reject. A contradictory shorter size 3 and repeated physical blob references are further hostile controls.

## Strongest simpler control / alternatives

- Correct positive: identical wire grammar and physical blob with declared size 4; complete read, every legal range, verify, and Linux/macOS extraction must remain exact.
- Independent existing frozen `tests/conformance/v24-chunk-maps.json` fixed-chunks vector, retaining committed bytes and hashes, must pass unchanged. Legitimate 0-length chunked regular member and valid repeated-blob references should be allowed when the format and reference validator permit them.
- **Alternative explanation:** `verify()` already validates the declared length; reject the hypothesis if a genuinely authenticated root-versioned archive cannot pass. Another alternative: only exotic manual wire is affected, not Builder output; then this remains hostile-input safety evidence, not a claim of normal output corruption.
- Choosing a new `S_CHUNKS` validator would duplicate authoritative `_validate_storage`. Calling `preflight_archive(path)` separately would reopen source and inherit O208 pathname race. Broad unconditional whole-index preflight would import unrelated compatibility/performance debt. One bounded `S_CHUNKS` addition to the *existing* O214 admission condition has the strongest control, if and only if the failure reproduces and positives survive.

## Kill/narrow conditions / evidence rung

1. First produce authenticated Builder-independent r24 hostile and positive archives. Execute on **unchanged parent** to prove a real defect, not an invented need. Retain actual `read/verify/read_range` and preflight results.
2. If reproduced, make the narrow one-line admission extension and test genuinely installed Python Reader on Ubuntu/macOS/Windows, running inherited O212 + O214 regression tests and untouched frozen S_CHUNKS conformance vector.
3. Require rejection before mmap and no leaked initial fd for bad input. No format/ABI/codec/evaluator modification, and no duplicated validator.
4. Held-out variants: truncated declared size, longer declared size, repeated physical reference, empty list, invalid ref, authenticated latest generation. Keep unchanged valid baseline and exact logical byte ownership.
5. Do not claim full-product release, ZIP64 parity, cold-open performance, mutable-inode immutability, or native parity from this focused court. General CI and performance gates remain independent.
6. On parent failure to reproduce, **do not implement**; record negative and retire the narrow proposal.

Evidence is *product-candidate testing* only after implementation, otherwise scientific observation. This PR is stacked on O214 #564; J24C01 #567 owns separate Linux publication composition. Reconcile owners, no force pushes or uncoordinated merge. Discovery STATE.json is stale relative to current PR evidence; no edit unless decision-changing frontier truth requires it.
