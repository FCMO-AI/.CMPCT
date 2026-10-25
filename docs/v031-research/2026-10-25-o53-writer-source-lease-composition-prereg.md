# O53 — Source-descriptor admission × serialized Writer/salvage composition (preregistration)

Date: 2026-10-25 UTC. Classification: product-correctness composition candidate; no merge/release/version authority.

## Frozen inputs and ownership
- Base: existing PR #311, branch `agent/phased3-v031-salvage-writer-cross-owner-composition-r265-20261023`, exact base HEAD `c1e75370281ca6b721ef10edf1ed15e6c5ef48f7`, Writer source blob `a3b9c3375ed19f0b37d40ee47ead7b5d5b8905ee`.
- Independent original O51 owner: PR #406, Writer source blob `130638744d26dbf71a3ddd49b2545db9eb933ed4`, installed cross-platform control run `40159802389`; original tests blob `b6e7a75f900171b85647a6d7ef06bd765101e041`.
- Historical adversary: O49 PR #404, real no-writer FIFO source hangs the old ordinary `Path.read_bytes` path (run `40157632143`).
- O53 owns **composition only**. It does not change #311, #406, #407, canonical development, release law, Reader, Builder, format, benchmarks, or shared Discovery state.

## Primary question and falsifiable prediction
Can O51's O_NONBLOCK + descriptor fstat/read source admission be composed *inside* #311's one-owner serialized Writer, while preserving the existing locked archive identity, physical salvage interpretation, transaction footer and cross-platform update fidelity?

Prediction: the combined real installed Writer rejects a genuine unwritten FIFO or a replacement FIFO path before doing any unbounded blocking read, and does not change the target archive at all on error; ordinary files, symlink-to-regular sources, descriptor post-open path pivots, existing serialized multiwriter tests and the salvage stream remain exact. For stable sources, a same-runner identical-input baseline #311 versus combined candidate should emit byte-identical r24 archives. Linux/macOS genuinely execute POSIX assertions and Windows legitimately skips only POSIX-specific cases. The original O51 test source is reused without weakening it.

## Strongest simpler control and alternative explanation
A pathname preflight `lstat` then existing `Path.read_bytes` is cheaper but can race at the actual blocking open; O51's exact-source hosted controls already established this limitation. Merely testing O51 without #311 is insufficient because archive locks, context-local owner identity and Reader/salvage composition could collide. Main alternative explanation: descriptor admission works alone yet import/lease/context interactions or metadata capture under serialization change update bytes/recovery behavior.

## Minimal experiment and evidence ladder
1. Source-only merge: copy **only** O51 helper `_read_regular_update_source` into #311, replace only the source `read_bytes(); stat()` expression; retain `@_serialized_writer`, `_checked_writer_reader`, `_locked_archive_size`, `_checked_append`, salvage scanner and all previous types.
2. Code identity and import checks: exact parent ancestry, Reader/CLI/hardening blobs, unchanged inherited O51 original test blob, and new combined Writer blob.
3. True pip-installed 3-host CI with original O51 tests and inherited #311 tests, plus explicit interaction tests: FIFO under cooperative lock with unchanged footer + blob candidates; supported-source two-generation SHA and salvage view; independently spawned contention test where useful. Never count administrative success/skips as evidence.
4. Stronger A/B with same corpus/tree and exact historical source reconstruction; separate physical complete archive bytes from logical data and metadata.
5. Full release comparator and platform/CPU/RSS are **not** earned by focused CI.

## Kill / narrow / debt
- KILL if any true inherited #311/O51 test regresses, FIFO update blocks beyond bounded child timeout, footer/complete archive bytes change after failure, regular archive byte parity breaks, or the combined source fails package-custody/host proof.
- NARROW if Windows POSIX tests skip or a held-out filesystem differs: state the actual host contract, do not claim universal portability.
- Any extra open/fstat syscall cost, whole-file materialization memory, network-filesystem blocking, hostile in-place ABA, and transaction-wide adversaries remain explicit exported debt; do not weaken frozen metrics.
- Inherited source and benchmark failures stay visible. No fake release credit or format bump.

## Concurrency and append-only outcome
Treat this file as immutable prediction. Add a separate dated result only after genuine execution; do not rewrite prediction to fit the result. Before late file writes re-read target branch source and reconcile with concurrent owners. O51, #311 and the independent O52 Builder pivot #407 remain separately owned.
