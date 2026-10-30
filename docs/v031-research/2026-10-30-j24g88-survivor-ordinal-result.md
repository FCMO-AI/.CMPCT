# J24G88 — result: ordinal survivor map clears the O0 byte gate; simpler signed deltas remain a stronger product control

**2026-10-30 UTC. DRAFT scientific evidence only. No new legal r24 archive, product Reader/Writer change, CI-gate relaxation, release, version bump, or shipped acceleration claim.**

## Immutable question and source
The prospective [freeze](2026-10-30-j24g88-survivor-ordinal-prereg.md) landed at `490ed1f4f1cadda901a2e8b83f1384d3027a23c2` **before** the J24G88 instrument and results. Parent #839 exact `6992ecc83af1824cf7a0bfcbb627a26dabfa2024`. It inherits #838 full-index and #839 factorized-row negatives without softening their frozen 5%/2x O0 gate.

The **original physical** #833 J24G83 Actions artifact #12978714378 (run [41061290836](https://github.com/FCMO-AI/.CMPCT/actions/runs/41061290836), hosted ZIP SHA256 `f8e21fdb7d7f52eb230ef2abdb0c06b24ae56ee165b3763c651128cf1460bc5a`) contains three source-identical physical variants per case. Its detached enclosing ZIP has SHA256 `6d0542f0938740a0d82acb0e3f1a57a46fffc9ecafcc6c4bea79187cc607e016`.

The actual exact physical input SHA256s were checked before arithmetic:
- 8,192 files, 1,017,260 bytes: `5e10557902c3bfe33f1136e4b99819eec0f6e9e98df3db1270c2d05cea37e26a`.
- 32,768 files, 4,084,062 bytes: `8402712cb12b53faf7868f60c27fb6c79b97272c76e5808d54c4b8aa623f8f81`.

Each source has 65 SHA256-bound footers, genuine 63 DELETE deltas and one generation64 full checkpoint; original base index and final non-file planes were equal. The prior binary referee verifies original CMA4 source bytes, CRC32, SHA256 and exact rollback. This experiment uses the same already-authenticated source, not an invented clean fixture.

## Fully charged O0 result

Checkpoint K32 is a *hypothetical future-format Writer substitution for the existing generation32 DELETE delta*, not an append to or rewrite of the immutable r24 original. Original 68-byte signed footer is counted on both sides, so it cancels in the net **new compressed descriptor bytes minus displaced existing compressed delta bytes**. Original header, base index, old earlier generations and all physical blobs remain retained and paid.

| Real physical source | Original generation32 delta body | New bitmap Zstd1 body | Bitmap net bytes | Whole-archive bitmap overhead | Simpler deleted-ordinal-gap net bytes |
|---|---:|---:|---:|---:|---:|
| 8,192 entries / 1,017,260 B | 29 B | 173 B | **+144 B** | **+0.01416%** | **+136 B** |
| 32,768 entries / 4,084,062 B | 29 B | 173 B | **+144 B** | **+0.00353%** | **+137 B** |

The bitmap data plane is 1,024/4,096 raw bytes, with actual MessagePack descriptor, 16-byte grammar tag, 32-byte root digest, explicit 8-byte original-index offset, original count and generation charged; Zstd levels 1/3/19 were measured. The simpler gap-varint plane is 33/34 bytes. At K32, logical maximum applied delta count before K64 would change **63 → 31** (2.032×), but this is only a theoretical count: no installed Reader full cold-open is measured, and any old footer-chain verification or root auth must be counted.

**Frozen decision: `SURVIVOR_BITMAP_O0_BYTES_PASS` on both authentic histories.** It is NOT a complete stored-byte win: the original archive still uses fewer bytes than either added representation. The O0 triage budget is permissive by design, not a release-performance threshold.

## Adversarial and stronger control evidence

The new [reproducible court](../../research/j24g88_ordinal_checkpoint_o0.py) uses the *independent* J24G86 physical wire parser, not the installed CMPCT package, and checks exact 32-generation reconstructed ordered rows and non-file planes. It rejects changed original-root digest, root offset, row count, bitmap length, tampered bitmap with stale signed-footer SHA, and non-canonical trailing bits when the base has a nonmultiple-of-eight number of rows. It also compares first32, last32, alternating32 and deterministic SHA256-ranked32 synthetic deletion choices on **authentic bases but counterfactual histories**; these are not evidence of four additional real archived workloads.

The originally recorded 21-sample in-memory Python micro included *recomputing SHA256 over the entire original index every time* in the bitmap/gaps materializer, so it is **not** an honest direct timing comparison to a Reader that already verified the header. An independent 101-sample preverified-root micro removes that asymmetric cost and compares all three candidates after the same root boundary:

| Original base | Simple 32-delete set replay median | Bitmap filter median | Sparse-gap decode+filter median |
|---|---:|---:|---:|
| 8,192 rows | 0.378 ms | 0.853 ms (**2.25× slower**) | 0.404 ms (**1.07× slower**) |
| 32,768 rows | 1.520 ms | 3.586 ms (**2.36× slower**) | 1.580 ms (**1.04× slower**) |

These are isolated CPython reconstruction measurements, not physical Reader, process startup, compression or IO timing. The full raw samples from the [independent micro](../../research/j24g88_independent_decode_micro.py) are persisted by the hosted CI artifact. The simpler gap list is **7–8 bytes smaller** than bitmap on the two original histories and close to the strongest simple CPU control. Neither has shown meaningful end-to-end superiority over the Reader with existing deltas.

A second codec-mode check using standalone `/usr/bin/zstd --ultra -19` found 3–4-byte discrepancies versus ctypes libzstd on the full descriptors. Preserve this genuine codec-mode difference; it cannot reverse either research byte gate or the stronger sparse-list ordering. The named format and source digests are data-specific research evidence, *never* generic admission keyed to fixture identities.

## Decision, constraints, next executable discriminator

- **Scientific:** the full-index and member-row K32 checkpoint byte floor was representational, not intrinsic to a new authenticated-root checkpoint. A bounded ordinal bitmap meets this permissive O0 research budget, but **simple sorted deleted ordinals are smaller** and preserve reconstruction exactly.
- **Product economics:** no observed installed Reader speedup; bitset is slower than ordinary set replay in the clean micro, and both descriptor variants increase complete archive bytes. An optimized Reader (owner #823) and the experimentally much faster stateful Writer (#829/#836, unresolved multiwriter safety) are stronger competing interventions.
- **Scope/compatibility:** deletion-only authentic histories with immutable original file rows and non-file fields. Changed paths, PUTs, metadata/fsmeta, hardlink ownership, blob descriptors, nested references, crash cuts, Windows, actual signed physical alternative grammar, hostile inputs/resource caps, RSS, selective IO, and writer/reader interoperability remain unproven. Refuse/revert to r24 semantics or a full new-format checkpoint in those regimes; do not add new format yet.
- **Next cheapest decisive action if product work is justified:** profile the installed optimized Reader's *per-footer* decompression/authentication/replay split on these exact archives. Compare a bounded signed-ordinal shortcut with the actual installed Reader and a simpler no-checkpoint skip/fast-delta method. If the original signed deltas are already cheap, **retire** this checkpoint family as product overhead rather than promoting an attractive 2.03× operation-count scalar.
- **Counterfactual:** the sorted deleted-ordinal control is simpler and wins bytes by 7–8 B; including it at the O0 stage avoided premature bitmap-engineering investment. This single result warrants a local design preference, **not** a self-modifying discovery policy.
- **Concurrency:** search of current open CMPCT PRs found no owner of the exact ordinal-map instrument; #838/#839 parent, #834 frontcoding, #836 lease, #574 Discovery Engine STATE remain separate owners. `STATE.json` not changed.

## Execution evidence

Original hosted exact-head script run [#41087903048](https://github.com/FCMO-AI/.CMPCT/actions/runs/41087903048) succeeded on source HEAD `6c6bc8ac088fd37513e6ca75166442e40113858f`, and published artifact [#12992632623](https://github.com/FCMO-AI/.CMPCT/actions/runs/41087903048/artifacts/12992632623) containing two input fingerprints plus the full result. The follow-up independent preverified-root micro/CI was added in a later commit; re-evaluate against its **exact** branch HEAD before treating that later check as green. Engineering Evidence initially failed because the PR body missed two exact section headings; the body was corrected without altering the evaluator. General and other branch checks must likewise be read from their exact HEAD; no release authorization.

**quality-ratchet:** scientifically positive byte-budget bound, decisive negative on simple control/CPU, untouched published r24 and all hard invariants.
