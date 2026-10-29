# J24I39b — encoded-tail custody falsifier (before implementation)

2026-10-29 UTC. **Separate second scientific question within PR #776, not an amendment of its successful logical-byte O0 oracle.** Existing first positive is source-exact and immutable: CI #40933414714 @ `9c5ed1da6fb30fde5d5b4e010cabe780710202df`, derived from real Builder WAV #774. No product source/format/ABI/version changes.

## Hypothesis and two distinct truth claims
J24I39 demonstrates that the File-backed Claxon sample iterator can reconstruct signed *logical WAV bytes* cheaply. That does **not** necessarily mean it verifies the entire *encoded FLAC payload*. Hypothesis H: a syntactically nonempty tail that starts after a valid FLAC's final audio frame can be ignored by `samples()`, while the reference `flac -t` rejects the extra bytes as loss of sync. Alternative: Claxon itself rejects the tail. Either result is valuable; do not fit a test to the result.

## Preregistered material comparisons
From the unchanged 8-MiB builder-authentic FLAC extracted from its independently audited r24 CMA4, construct exact byte-preserving variants:
- `valid`: original bytes unchanged, expected both Claxon logical identity and reference FLAC acceptance.
- `trailer`: append one fixed 21-byte non-FLAC suffix; every original FLAC byte unchanged, signed WAV logical identity expected unchanged. Test whether Claxon accepts and whether reference `flac -t` rejects.
- `truncated`: drop final 64 encoded bytes; expected logical or frame error, not guaranteed but outcome observed.
- `concatenated`: append one full second FLAC stream, preserving original first; expected reference rejects second stream or decodes additional samples, but record actual behavior without assuming.
Use the unmodified J24I39 Rust instrument's `stream` mode (four iterations and exact logical SHA/CRC/size checks) as the *actual* Claxon path. Distinguish process exit success, panic/error, complete verified count; independently run installed reference `flac -t`. Record `sha256`, lengths and failure messages. PASS of the scientific workflow means the controls executed and results were captured, NOT that an invalid stream was rejected.

## Decision and kill/narrow criteria
If `trailer` is accepted by Claxon but rejected by reference FLAC, the current sample-iterator prototype is **NOT** a complete encoded-payload validator; productization needs strict byte/bit/frame-consumption proof beyond logical hashes. If both reject, this one trailer case narrows (but does not close) trailing/concatenation concern. If valid case fails, experiment invalid. Never mutate the original source file, frozen corpus, canonical verifier/evaluator or performance baseline. Inherited source pins and full archive integrity remain unchanged.

## Carrying cost and limitations
RFC 9639 / reference `flac -t` provide independent encoded-format control. Reference CLI error is not evidence of an authenticated CMPCT file without signed record reassembly. Only one PCM16 original and a small mutated family; neither codec universal proof nor exploitability. This adjacent falsifier is the cheapest decisive action ahead of a streaming product rewrite by #765/#759. Do not amend PARETOBONK process policy from one result.
