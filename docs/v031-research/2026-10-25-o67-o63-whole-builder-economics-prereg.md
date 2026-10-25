# O67 — Genuine full-Builder economics of O63 transaction rollback vs O60

Date: 2026-10-25 UTC. Status: PREREGISTERED BEFORE INSTRUMENT/RESULTS.

## Source and scope
Canonical release v0.30.0 revision 24; development v0.31. Unchanged inherited owner O60 PR #415 at exact Git SHA `c88a6bc29b9ec8738e23aab788b7c09ab0390e79`, Builder blob `bda9d7f8005e276ba891aac75ae50eabe67bd431`. O63 PR #418 exact head `18e32cae012f5dca9fc47f10d194f8b81005c85c`, Builder blob `382e60983bf1e8e7595ea7112f3a5553dc33dcc0`. Shared codec blob `dc3446b0eed82edfba9380e3885a20aa45577899`; all other product sources unchanged in this independent **research-only** branch. This is not the release gate.

## Primary scientific question
Under actual complete Builder creation on identical directory trees and genuine ZIP streams, does O63's reversible per-candidate journal eliminate complete stored bytes in late failed virtual ZIP fallback, and how much actual creation wall/CPU/RSS/verify work does that cost on success, opaque fallback, and unrelated ordinary trees?

## Controls, advance predictions and kill
- Freeze one host (Ubuntu Linux) and independently installed **actual historical O60** + **actual O63** packages from their exact Git source; verify product Builder SHA and paths outside source checkout. Use same interpreter version/dependency versions.
- Create deterministic source trees once and reuse same physical inputs, metadata and clock throughout paired comparisons. Cases: *accepted ordinary VZIP*, *late valid unsupported fixed-Huffman ZIP with prior virtualizable members*, *early valid unsupported fixed-Huffman ZIP*, *ordinary non-ZIP multi-file tree*, and, if cheap, *multiple separate later-failing ZIP objects*. No fixture-specific admission code.
- Validate stdlib ZipFile inputs and exact CMPCT round trips; confirm that candidate and base are semantically comparable (file content SHA and logical manifest); record full `.cmpct` sizes and SHA, distinct from extracted-data equality. If zip recipe already failed before candidate speculative work, zero-byte savings is an honest result, not an instrumentation failure. No change to seed after seeing outputs.
- Each run is a fresh independent Python process. Use at least 4 ABBA repetitions per case on the same runner, preserving raw order/timestamps, CPU/wall, peak RSS, disk blocks where available, read/verify wall and full bytes for both engines. Separate process startup from timed Builder.
- Predict O63's late-fallback physical archive is no larger than O60 and may be smaller due to rollback; predict accepted ZIP and non-ZIP archives remain exactly byte-identical. CPU/RSS effect unknown, must be measured. Failure of parity, verification, source identity, full log retention, or material overhead without byte benefit narrows/retire the mechanism economically; no threshold moved.
- Classification: micro/full-Builder research evidence on Ubuntu, **not** three-host performance, not official r24/ZIP release ABBA, not cold-cache guarantee, not general compression score.

## BONK / alternatives / coordination
- Original O63 only measured 4096-candidate journal bookkeeping, +1.55ms micro, not full archive cost; official benchmark was skipped. A gigantic broad matrix before cheap same-input A/B is premature.
- Testing only synthetic in-memory Candidate operations does not charge Builder/ZIP/Reader costs; skip. Reimplementing the comparison engine instead of executing true O60/O63 source is prohibited.
- This branch is independent of O66 historical source-custody court. It does not modify O60, O63, O59/O62, other agent branches, frozen benchmark, format, release or `STATE.json`.
- Before an economic conclusion, check for imported modules from repository, source mutations during execution, unsynchronized workload copies, missing JUnit/receipt or output discrepancies.

## Decision
If results demonstrate material saved archive bytes and bounded whole-product cost, O63 can be considered for *further* product integration; if the benefit disappears under whole-product charged accounting, preserve O63 correctness win but classify byte-economic argument as unsupported. This experiment cannot authorize release or upgrade. Preserve all negatives and raw measurements.
