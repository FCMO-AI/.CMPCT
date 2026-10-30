# J24I62 — Native complete verification must not certify a stale primary generation

**Preregistered 2026-10-30 UTC, before any code or test mutation.** Research/hardening child of J24I50 #807 exact `0b80ecb9b1742a6c20756f4c9e8e097103881cb4`. Canonical release remains v0.30.0 / revision 24; no format, ABI, official benchmark or release-gate changes. J24I51 #812 owns the original physical same-inode counterexample and is not overwritten.

## Baseline and falsifiable question

The experimental native `Archive::open()` accepts the primary authenticated r24 index and ignores later transaction generations; `verify_complete()` may therefore return success for a stale member set. Original J24I51 #812 produced an authentic signed PUT+DELETE sequence on one unchanged path/inode: Python latest verify SUCCESS on a different member while native verify SUCCESS on original primary. A native full-verification **success** must not be misconstrued as latest-generation success.

**Question:** can a bounded, read-only latest-checkpoint provenance gate in the existing same-handle native `verify_complete` return typed Unsupported on genuine later signed deltas and checkpoint generations, while retaining successful verification of valid single-generation original r24 archives and zeroing C ABI output on failure?

## Mechanism and controls

- **Simpler control:** refuse all files longer than their primary data span; this incorrectly rejects ordinary Builder r24 archives with an authenticated tail checkpoint and violates accepted baseline.
- **Preferred smallest gate:** use the held File descriptor to inspect the terminal r24 footer; require the terminal checkpoint to be a bound root with `prev=0`, and require its decoded index content digest to match the authenticated primary index digest. Any other kind/previous generation, malformed/partial terminal footer, unequal current index digest, unsupported terminal encoding or changed/mutated footer during the check must fail closed with typed Unsupported/format error, **before** counting verified members. Treat this as a conservative first proof, not full journal recovery.
- **Strong existing controls:** exact frozen r24 WAV/FLAC, direct RAW, one-owner hardlinks, invalid physical member SHA, null native C pointers, same-handle path rebinding. Keep all these green. New public Writer PUT/DELETE and 64-delta checkpoint case must not be reported as SUCCESS by native, while Python latest Reader still succeeds.
- **Alternative:** implement full native signed journal recovery. Larger semantic scope, cross-platform crash/recovery testing and more CPU/memory/work; defer to dedicated Reader/journal owners until this narrower false-success boundary is fixed.
- **Counter-mechanism:** if terminal footer alone cannot distinguish legitimate independently encoded primary/tail snapshots, decode the terminal index under the existing 256 MiB limit and compare canonical uncompressed index SHA, not compressed bytes.

## Decision and kill

Positive result requires a prepatch genuine J24I51 regression witness, no valid-archive false rejects across existing native vectors, exactly-zero C count and empty native CLI stdout on signed latest-generation rejection, no changes to `Archive::open` semantics for primary-only info/list/range, and successful exact-head Rust/installed package CI. No green-on-test-only source claims.

Kill/narrow if latest delta is accepted, a valid single-generation archive is rejected, any prior C ABI/CLI/member-verification test regresses, head/source custody is ambiguous, or the gate needs a format/threshold/evaluator rewrite. A missing terminal footer on a valid recovery case is not license to declare full native recovery; refuse until conformance.

## Full-system cost and limits

This runs **only on whole verification**, adds bounded tail-index authentication and at most 256 MiB controlled decode; capture additional verify wall/CPU/RSS when accepted. Creation/extraction size/performance unchanged by source semantics, but official frozen r24/ZIP parity must still run. Does not prove atomic snapshot against concurrent same-inode mutation, journal recovery, selective physical reads, Windows/macOS until hosted, or native replacement of Python Reader.

## Concurrency and carry-forward

#807 is the owned ABI and CLI surface; #812 is frozen evidence, #580 is primary-only CLI economics, #789/#795 own Python signed Reader safety, #843 owns pre-load codec loader. This branch changes only the narrow native *verify* integrity gate and its conformant tests. Do not edit any of their branches, Discovery STATE (#574), thresholds or published release. Source archive and exact-head receipts outrank this proposal.
