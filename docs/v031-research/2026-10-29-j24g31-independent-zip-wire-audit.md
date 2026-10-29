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

**Direct local audit result (2026-10-29 04:21 UTC): 1,236 explicit assertions passed; 41 independently parsed physical ZIP exports (14 Ubuntu, 14 macOS, 13 Windows); 7/7 candidate ZIP SHA identities across hosts; 4 source receipts per host; two original Windows signed-negative OSError observations.** All candidate parsed ZIP dates were valid Gregorian dates and matched the expected floor/ceiling and ordinary controls. The inherited POSIX baseline ZIP for 2108 leap day *actually contains invalid 2107-02-29*; this expected historical negative was preserved rather than relabeling it valid. Four original-transport archive hashes matched GitHub Actions' own published artifact digests.

A detached adversarial suite altered the authentic 2020 candidate ZIP: local/central signatures, versions, flags, method, times, sizes, name, stream bytes, CRC, central offsets, EOCD/count, truncation/trailing bytes and a **paired local+central invalid leap-day** manipulation. **24/24 physically mutated inputs were rejected; clean control accepted.** Mutation-suite check is against the independent auditor itself, not proof of universal CMPCT/ZIPSafety coverage.

## Negative / costs / admission

This verifies **tiny, single-member, normal ZIP32 outputs** only. It does **not** independently decode revision-24 CMPCT archives or establish complete ZIP interoperability; trust in the first-party manifest's declared payload SHA remains. It does not evaluate >4GiB ZIP64 fallback, large file counts, generalized Deflate/STORE portfolio, full metadata/xattr/permissions, concurrent path swaps, crash durability, full-product CPU/RSS/I/O, or release promotion. These debts continue under their existing owners. The 1,236 assertions are internal audit checks, **not 1,236 independent experiments**.

The cheapest decisive control was inspecting the 188-byte physical ZIP wire objects already produced by #727 rather than authoring another ZIP exporter, editing source or re-running an expensive matrix. Result: extra confidence in the narrow calendar composition claim, **no change to product-selection policy or shared `docs/discovery/STATE.json`**.

## Handoff

Keep #727 DRAFT, the Reader source unchanged. Check actual inherited generic CI reds separately (they are not erased by this positive wire audit). For a decision-changing next experiment prefer real ZIP64 >=4GiB or a distinct adversarial filesystem path-custody experiment owned by its existing integration PR. Do not fork another calendar algorithm or infer release readiness.
