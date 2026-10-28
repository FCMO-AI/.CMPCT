# v0.30 bounded pack-plan compression reuse

Status: **preregistered product experiment; no product/release credit**.

Authority parent: `86b416868aaef7d4a77de06e99d8d902efa04f36`.

Research provenance: PR #154. Profile run `35444760791` found exact Zstd compression at ~84–85% of both co-critical ML child profiles. Corrected exact-byte oracle run `35445150350`, source `7f0c439ebc8d07f039c5594c4be3a33e9cf8c524`, artifact `10584423516`, measured v0.28 **33.475%** (`28.737 -> 19.117 s`) and attempt-5-neutral **42.775%** (`29.383 -> 16.814 s`) while preserving byte-identical child archives. Both saw 200 misses plus 316/335 repeat hits. The oracle retained ~90.1 MB raw + ~69.9 MB compressed and is therefore not a product design.

## Product hypothesis

Preserve the exact six-way pack-plan search and exact compression level, but separate audition from payload materialization:

1. During pack-plan trials, identify each group structurally by `(level, tuple(group_node_ids))`.
2. On first sight, perform the historical exact compression, retain only its exact packed length, and discard the temporary compressed payload.
3. On repeated groups, reuse only that exact packed length for plan pricing.
4. Select the winner using the unchanged byte objective/tie law.
5. Materialize the selected plan exactly once using the historical compressor.
6. Consume the selected packed payloads already returned by `_choose_pack_plan` during final emission instead of recompressing them again.

No approximate compression, lower level, changed candidate set, threshold, selector or archive grammar is allowed.

## Falsification / quality ratchet

Kill or narrow if plan identity or final archive SHA differs from inherited output; if both co-critical children do not materially improve; if cache metadata/RSS erases the wall win; or if unchanged r24/runtime gates regress. Preserve exact compression level, benchmark corpus, byte objective, tie semantics and release thresholds.

## Evidence ladder

- [ ] unit/hostile proof that cached and uncached exact lengths agree for repeated/nonrepeated groups;
- [ ] exact plan identity + archive SHA for v0.28 and attempt-5;
- [ ] balanced fresh-process child A/B with CPU/wall/RSS and cache hit accounting;
- [ ] whole-product ML create A/B proving both-child acceleration transfers through the parallel tournament;
- [ ] unchanged r24/ZIP and exact-head CI;
- [ ] authoritative runtime owns release credit.
