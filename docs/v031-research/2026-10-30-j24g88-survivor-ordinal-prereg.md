# J24G88 — Authenticated survivor-ordinal temporal checkpoint O0 preregistration

Date: 2026-10-30 UTC
Status: FROZEN PROSPECTIVE EXPERIMENT, RESEARCH ONLY. No source/reader/writer/format/release changes, no compatibility, speed or product claim.
Inherited parent: PR #839 @ `6992ecc83af1824cf7a0bfcbb627a26dabfa2024` (itself stacked on #838). Published baseline main@80c358f8824ec1b20d349c92ed94c898090969b0, v0.30.0/r24.
External original physical source: #833 detached ZIP SHA256 `6d0542f0938740a0d82acb0e3f1a57a46fffc9ecafcc6c4bea79187cc607e016`, embedded hosted artifact and two authentic 65-footer archives. Verify these hashes again.

## Why and alternatives
#838 ordinary complete checkpoints cost +7.368% / +6.882% at K32; #839 immutably factored member-row checkpoints cost +6.009% / +5.998%, both above the frozen O0 5% bound. Changing representation from stored member rows to a **survivor ordinal bitmap** anchored to an authenticated original index might radically lower checkpoint bytes. Strong simpler control: keep original signed delta log/Reader, or store just 32 deleted ordinals as a bounded sorted varint vector. Retained private Writer session #829/#836 already demonstrates much larger complete-Writer speed headroom without changing disk format, but has unresolved safety/memory debt; a cheap map is not automatically preferable.

## Frozen question / admissibility
For the two original delete-only 8192 / 32768 archives, can a K32 survivor-ordinal checkpoint substituted at generation32:
1. reconstruct exactly the full current ordered rows at generation32 from original authenticated root + bitmap, preserving all index planes;
2. cost <=5% extra complete archive bytes on BOTH original archive sizes, counting UTF-8 MessagePack keys/framing, explicit 16-byte representation type/flags, 32-byte root SHA256, 8-byte base offset, cardinality, bitmap bytes, actual libzstd compressed body and inherited 68-byte signed footer; original generation32 delta body is replaced, NOT physically appended to an existing immutable archive (research hypothetical future writer only);
3. reduce maximum number of **logically applied** deltas before next K64 checkpoint from 63 to <=31 (>=2.0x count reduction);
4. reject mutated root digest, out-of-range bits, wrong cardinality/length, and incompatible source/index fields without accepting or laundering data.
If #1–3 fail, retire bitmap checkpoint even as a delete-only O0 candidate. If they pass, this is **only a byte/operation-count seed** until real installed Reader wall/CPU/RSS/durability and recovery evidence exceeds the **stronger original optimized-Reader + delta-log control**.

## Frozen methods
- Primary bitmap: 1=survivor for each row in authenticated original root order, little-endian bit positions. Keep original physical blob metadata and all other root fields unchanged only if structurally identical. Use zstd level1 as low-create-cost primary; also report level3/19 as non-free alternatives. Count all encoded descriptor bytes.
- Simpler control: ascending sorted deleted ordinals as unsigned LEB128 *gap* sequence, similarly charged framing/root/offset/footer; reconstruct and compare. Do not silently select after observing which wins.
- Original full-index and factorized-row checkpoints are existing stronger real-archive controls. Original r24 deltas are immutable physical baseline.
- Structural transfer: predeclare hostile 32-delete selections (first32, last32, alternating 32, SHA256(seed=j24g88-hostile-v1) ranked 32), all on the same original physical base; these are synthetic held-outs, NOT genuine historical logs or product evidence.
- CPU micro: compare bitset and varint decoding and application with an explicit simple 32-delete replay on the same in-memory real base (not an installed Reader); include traversal/rebuild cost and initial root auth cost separately where possible. Report raw repetitions and use credible floor to reject premature decoder speed claims.
- Prohibit weakening any existing scientific/release gate, changing signed footer semantics or treating SHA256 (unkeyed) as a cryptographic signature. Do not rewrite historical data.

## Decision and counterfactual
Primary endpoint = `SURVIVOR_BITMAP_O0_BYTES_PASS` or `SURVIVOR_BITMAP_O0_FAIL`. Record separately whether the stronger sparse-ordinal control beats bitmap and whether CPU evidence supports moving to physical Reader implementation. A positive stored-byte bound cannot earn productization merely by reducing nominal delta count. Ask which earlier simple control could decide cheaper. Preserve failing/negative evidence verbatim.

## Independence, concurrency and law
Search of open PRs at ~2026-10-30T16:04Z found no other owner for the exact survivor-map question. #838/#839 own the parent full-index/factorized comparators; #834 owns frontcoded paths; #836 lease; #574 discovery STATE. No modifications to any of their scopes. Repo `docs/discovery/CONCURRENCY_PROTOCOL.md` and `tools/discovery_claims.py` not present on this parent; use PR/branch ownership and exact-head reconcile. Do not modify `docs/discovery/STATE.json` under #574. A result should go on this isolated branch, with raw numbers, source hashes and independent countercheck; no v0.31 release claims.
