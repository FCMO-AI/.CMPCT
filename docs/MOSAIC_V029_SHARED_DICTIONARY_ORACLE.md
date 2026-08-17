# Mosaic v0.29 — Shared Dictionary Record Context oracle

Status: **detached contingency / no reader grammar / no v0.29.0 claim**.

## Why this is the next byte pool

The closed residual experiments bound the entire residual-program opportunity far below the remaining
hostile structural gap:

- attempt #7 causally mixed all **186** packed recipes and saved only **1,303 B**;
- the columnar oracle measured **64,492 B** of canonical residual recipe bytes across 12 accepted groups;
- those 12 residual records occupy only **30,315 physical B** in attempt #5;
- every reversible columnar layout was larger, with **0/12 improved groups**;
- the hostile attempt-5 archive has **134 physical records**, so all 53-byte physical headers together
  are only **7,102 B**.

The remaining ~84 KiB deficit therefore cannot be solved by residual recipes or framing alone. The next
meaningful pool is the compressed payload of the large direct/root records.

## Hypothesis

Keep attempt #5's exact physical record boundaries and logical graph, but let profitable direct/root
zstd records share one small archive-global trained dictionary. Zstandard's dictionary API is explicitly
designed to improve independently compressed small/medium records by supplying useful history at the
start of each frame; unlike making root packs larger, this can add cross-record context without merging
random-access units.

The oracle trains candidate dictionaries at **8, 16, 32, 64, 96 and 128 KiB** from deterministic bounded
head/tail samples of existing direct/root records. For each dictionary it:

1. recompresses every eligible direct/root record with the real level-19 zstd dictionary API;
2. immediately decompresses every candidate payload with the same dictionary and requires exact bytes;
3. keeps only records whose physical payload actually shrinks;
4. charges the dictionary itself as a new raw authenticated physical record plus **512 B** reserved
   metadata/descriptor cost;
5. preserves the existing <=8x materialization envelope; and
6. charges a cold target the dictionary once, rejecting any target where dictionary-only overhead exceeds
   **2.0x** its logical size.

The produced `.cmpct` file remains the exact attempt-5 archive. This is a size/locality ceiling only.

## Frozen gate

A reader-visible shared-dictionary design is worth considering only if one candidate produces all of:

- >= **128 KiB net archive saving** after dictionary storage + metadata charges;
- >= **8** independently profitable, locality-admissible direct/root records;
- exact dictionary compression/decompression round-trip for every measured record;
- weighted direct-pack materialization <= **8x**;
- maximum dependent-node materialization <= **8x**; and
- additional cold dictionary materialization <= **2x** per target.

The 128 KiB requirement deliberately exceeds the current structural crossing gap. A new decoder
dependency must have enough headroom to pay for native-reader work, recovery metadata, CPU, and any
format bookkeeping that the oracle still approximates.

## Non-goals

- Do not merge records into larger solids; record boundaries remain frozen.
- Do not omit dictionary storage cost.
- Do not assume a warm process cache; cold random access pays the dictionary once.
- Do not dictionary-code Preflate records.
- Do not change canonical revision 24 or attempt #5 output bytes.
- Do not lower the gate after seeing results.

## If this rejects

The next high-leverage context oracle should use **existing direct records as bounded raw-content
contexts** rather than storing a new global dictionary. Context records must remain ordinary/non-context
records to keep dependency depth one, and their full decode cost must count against locality. That path
can test cross-pack context reuse without paying dictionary storage, but should only be attempted after
this simpler global-dictionary ceiling is measured.
