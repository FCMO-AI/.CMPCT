# J24G56 — authenticated unknown journal opcode versus Reader/preflight (prospective falsifier)

Date: 2026-10-29 UTC. Scope: independent negative research on unmerged candidate #789, **not published-wheel evidence**.
Parent: #789 exact 83e9f2eb277f023186b646f667cd443b7108f268; main published 80c358f8824ec1b20d349c92ed94c898090969b0 (v0.30.0, r24).
Owner: research-only child; do not change Reader, journal_replay, validation, #789 branch, frozen tests, version or format.

## Primary question, baseline and predicted failure
The new shared `_apply_journal_ops` dispatches `put`, `del`, `ren`, and lacks a final `else` rejecting unknown signed operation tags. Reader calls it directly during footer replay; preflight `_apply_delta` rejects unsupported tags before that call. A sufficiently authenticated r24 journal with unknown op may therefore be silently accepted and selected as latest committed by Reader, while preflight explicitly rejects it.

Prediction: for a genuine Builder-created archive, append a correctly SHA-256-authenticated r24 delta footer with an unsupported `future-op` and no blob changes. Reader opens the newest footer, reports the original members and `verify()==N` despite ignoring the opcode; preflight raises `ValidationError`. External/referee footer SHA and opcode must confirm the issue is semantic, not corrupt CRC/index or incomplete tail.

## Strong controls and alternatives
A signed known `del` op on the same baseline must advance latest footer and be recognized identically by Reader and preflight. An incomplete/physically SHA-corrupt footer must be recovered as the old generation, distinguishing intentional recovery from silently ignoring a *valid, committed but unsupported* operation. Reader may deliberately allow future op tags for format evolution, but preflight's r24 strict format contract says otherwise; if format law authorizes extension, narrow this to an API contract discrepancy rather than declare universal invalidity.

## Cheapest experiment and kill conditions
Before product changes, run an isolated physical sample on installed exact source using the existing Writer footer API, first-party Reader/preflight, and separate stdlib/msgpack/Zstandard wire validation. Only after the local physical result proves cause should a small GitHub Actions (Linux/macOS/Windows) evidence court be added. No compressor ratio, benchmark or release claim. KILL if Reader recovers rather than selects the unknown-op footer, if preflight accepts it, if the footer is physically unauthenticated, or if an existing format-compatible rule proves unknown ops must be no-ops.

## Consequences and owner handoff
A positive result justifies one shared fail-closed opcode parser/validator at the Reader replay boundary, preserving older committed-footer recovery and preflight limits, and explicit legacy-compatible treatment of known operations. Coordinate the narrow repair with #789 owner; do not implement it concurrently. Track actual file bytes, hash, source HEAD, CI artifact, negative controls, and any semantic contradiction. No modification to discovery STATE unless it changes project-level choices.
