# J24G58 preregistration — shared signed-journal replay ownership and cost

**Status:** prospective scientific candidate, not product/release credit. **Base** `FCMO-AI/.CMPCT` PR #795 at `1935c14c76f1bb39fd218d73cdbee93d3c2b76a1`. The inherited single source of truth is `src/cmpct/journal_replay.py`. It is currently used by Reader, bounded preflight and transaction checkpoints. No shared discovery-state changes.

## Baseline and controlling prior evidence

Current `_apply_journal_ops` scans every row for each `put` or `ren`, and rebuilds the full list for every `del`. On unique-named `N`-member indexes with `N` independent operations, the algorithm's lookup work is Θ(N²). `#344` measured older real signed preflight 4096-renames at 370.877 ms vs equivalent checkpoint 7.952 ms (historical source, not the current shared helper). `#346` and `#358` researched positional indexing and faster ordinary Reader replay, but neither is proven to cover the newer shared logical-name xattr/owner lineage of #789/#795. `#775` measures a different rekey cost and cannot be treated as a fair equal-semantic competing implementation. Do not re-invent earlier indexed work.

## Hypothesis, alternatives and disproof

**Question:** Can a cheap collision-aware indexed execution path for accepted simple r24 transactions preserve *exactly* the current shared journal results while materially reducing large-index replay CPU, without weakening signed metadata identity, resource caps, malformed-operation refusal or recovery?

**Selected mechanism (candidate only):** preserve the existing full-list linear implementation as a fallback. Admit the indexed route only if original names are unique and a complete dry-run of the operation name graph has no rename-to-existing collision. Use a per-name row-position table, tombstones for deletes, and compact once at the end. Keep the existing grammar check *before* mutations and existing lineage metadata rekey unchanged. Preserve `max_files` checks at the insertion instant. A single replacement put remains on the current fast path.

**Simpler control:** keep the original shared replay unchanged if the extra name preflight/index costs more than it saves. Earlier indexed replay #346/#358 is the relevant implementation donor; no broad rewrite. No priority or threshold adjustment based on benchmark identity.

**Disproof conditions:** any result/exception semantic difference against original #795 on seeded mixed operations, transient duplicate/collision names, delete-then-recreate identity, xattrs or owner overrides, invalid ordinals, resource-ceiling inserts, malformed and unknown tags; any higher stored bytes/changed r24 format; >20% stable overhead on small inputs; or lack of meaningful benefit on large accepted transactions. The fast route must never bypass the current signed grammar. Revert/fallback on failure, do not edit the evaluator.

## Evidence ladder and accounting

1. Static source and exact parent Git-blob/commit identity (only a complexity prediction).
2. **Unmodified parent source** vs candidate in the *same* Python runner on synthetic states, ≥5 alternating A/B and B/A batches at 64, 512, 2048, 4096 rows and proportional put/ren/del operations; preserve raw process CPU, wall, allocations/peak RSS and output/exception identity. Slow exact-parent source is reference, not a semantically weaker baseline.
3. Deterministic seeded state-machine differential including hostile and repeated names, and truly physical Builder/Writer committed r24 multi-generation tests at current source.
4. Hosted exact-head CI, independently source-bound product/portability and full release gate if stage 2 survives. No product credit before real end-to-end create/extract/verify, selective access, recovery and memory are measured.

The benefits may evaporate after Reader import, footer decode, index sort, MessagePack and compression. An O(N) metadata rekey sort remains. A transient tombstone dictionary has nonzero memory cost, may exceed slow cost at small N, and does not prove a bounded hostile-processing total. The release performance floor remains unchanged.

## Concurrency and decision

Related owners: #789 (shared signed replay), #795 (fail-closed signed grammar), #346/#358 (historical indexing), #775 (metadata rekey economics) and #574 (Discovery state). Work on a **stacked isolated branch** from #795; do not modify owner branches or frozen evidence. No claim to ownership of the main release/integration. If any owner has already implemented this exact indexed transfer, retire duplicate work and adopt its evidence. This preregistration deliberately occurs **before** any test or implementation mutation.