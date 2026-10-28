# J24B06 — fully signed logical-size cancellation against extractall(max_bytes)

Date: 2026-10-28 UTC
Status: FROZEN PROSPECTIVE RESEARCH QUESTION. No product, format, gate, version, merge or release authority.

## Canonical baseline and scope
Source is published `FCMO-AI/.CMPCT main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`, v0.30.0/revision-24. `CMPCT.extractall` sums signed index row[4] for all non-directory rows, then admits if `total <= max_bytes` (Reader lines 390-392). Symlink `read` returns the physical blob directly, ignoring its signed logical length (line 178), and `verify` computes the original blob SHA.

### Primary falsifiable question
Can an attacker make a **validly signed, fully physical, otherwise unmodified revision-24 archive** bypass a positive `extractall(max_bytes=4096)` budget by changing ONLY the logical size of a symlink row to a negative integer and re-signing/recompressing both copies of the index, while the archive contains a regular file with 8192 bytes? The alleged mechanism is negative signed size cancelling positive regular-file size in the unvalidated aggregate. It is NOT an unauthenticated wire-corruption exploit: this models an adversarial archive producer or signed malformed archive.

## Frozen test plan BEFORE implementation
1. Create a real source tree with `payload.bin` exactly 8192 deterministic pseudorandom bytes and `offset-link` a relative symlink pointing to `payload.bin`. Build the original with the **actual published Builder**, not a mock Reader.
2. Rebuild a second archive using the exact same original physical BHDR/blob records, but with one intentional signed logical change: `offset-link` row[4] becomes `-8192`. Repack the complete primary AND tail index using the actual package-native Zstd encoder, update HDR/FTR index SHA-256 and byte lengths, preserve all other file/physical records. A different first-party index SHA is expected and must be truthfully reported.
3. Control A: unchanged original `extractall(max_bytes=4096,metadata=False)` must reject before writing `payload.bin`; `verify()` on the original must succeed.
4. Candidate B: signed modified archive must pass `CMPCT` open and `verify()`, and `extractall(max_bytes=4096,metadata=False)` must either reject before a >4096-byte regular file appears (**hypothesis killed**) or write all 8192 payload bytes (**safety counterexample confirmed**). The output must exactly match independent hashlib SHA-256 of the original source. No symlink may escape the output root.
5. Independent referee must parse the raw HDR / index / BHDR / footer using struct, msgpack, and a separate Zstd executable or library, assert full signed index hash agreement in both copies, original physical-record byte identity, precisely one semantic row-size delta, identical file bytes and physical references, and that the trusted budget check is not confused with disk-block occupancy or the symlink's target length.
6. Negative/perturbation controls: ordinary positive-size symlink; zero and negative budget values (if the API accepts them, document rather than normalize); identical bytes/metadata with ordinary `max_bytes` refusal. Validate the test cannot pass by skipping the Reader call or accidentally constructing an unparseable index.
7. Record real source SHA, source-locked local/hosted results, test observations, complete source/fixture SHA-256, comparison outputs and independent referee verdict. No P0 publication claim if only local synthetic model is run.

## Stronger simpler controls and alternatives
Published current Reader is the primary control. Simple explicit nonnegative size admission would prevent cancellation; alternatively count only validated regular-file sizes or use a checked sum. A hypothetical general preflight might already reject negative size: if so, the attack is rejected and the proposed vulnerability is falsified. Do not weaken the real Reader, remove verification, or change budget semantics to force a result.

## Stop/kill and promotion law
A successful negative attack is a **correctness finding**, not a released product gain. A validated refusal ends the hypothesis. If confirmed, open a focused issue and share precise source-exact evidence; product fix must separately enforce nonnegative sizes and relationship integrity with no false acceptance, then pass genuine installed Reader, hostile cases, version/format and CI gates, portability and existing release parity. Leave owner PRs #609/#615 and other agents untouched. No new process-policy lesson from a single event.

## Concurrency and costs
Search on 2026-10-28 found no active J24B06 or explicit `max_bytes` signed-negative-budget PR. Related #609/#615 own direct physical-size/hardlink semantics and must not be modified. Scope limited to new research/test/workflow/document files on isolated branch. The test is tiny, deterministic, no secret/user data, and bounded local filesystem creation. An intentionally malicious signed index tests availability/quota semantics, not confidentiality, arbitrary code execution or a cryptographic forgery.
