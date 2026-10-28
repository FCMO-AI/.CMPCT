# Mosaic v0.29 — Shared Dictionary Record Context oracle

Status: **REJECTED by frozen gate / durable negative evidence / no reader grammar / no v0.29.0 claim**.

Durable result: `benchmarks/history/2026-08-17-mosaic-v029-shared-dictionary-context-reject.json`.

## Why this byte pool was tested

The closed residual experiments bound the entire residual-program opportunity far below the remaining
hostile structural gap:

- attempt #7 causally mixed all **186** packed recipes and saved only **1,303 B**;
- the columnar oracle measured **64,492 B** of canonical residual recipe bytes across 12 accepted groups;
- those 12 residual records occupy only **30,315 physical B** in attempt #5;
- every reversible columnar layout was larger, with **0/12 improved groups**;
- the hostile attempt-5 archive has **134 physical records**, so all 53-byte physical headers together
  are only **7,102 B**.

The remaining structural deficit therefore could not plausibly be solved by residual recipes or framing
alone. The next meaningful pool was the compressed payload of the large direct/root records.

## Tested hypothesis

Keep attempt #5's exact physical record boundaries and logical graph, but let profitable direct/root
records—including a currently RAW record when profitable—use zstd with one small archive-global trained
dictionary. Zstandard's dictionary API supplies useful history at the start of otherwise independent
frames; unlike making root packs larger, this can add cross-record compression context without merging
random-access units.

The oracle trained candidate dictionaries at **8, 16, 32, 64, 96 and 128 KiB** from deterministic bounded
head/tail samples of existing direct/root records. For each dictionary it:

1. recompressed every eligible direct/root record with the real level-19 zstd dictionary API;
2. immediately decompressed every candidate payload with the same dictionary and required exact bytes;
3. kept only records whose physical payload actually shrank;
4. charged the dictionary itself as a new raw authenticated physical record plus **512 B** reserved
   metadata/descriptor cost;
5. preserved the existing weighted direct-pack <=8x materialization envelope;
6. required every dependent target touched by the new dictionary to remain <=8x; and
7. charged a cold touched target the dictionary once, rejecting dictionary-only overhead above **2.0x**
   its logical size.

Untouched attempt-5 nodes could not fail the mechanism's locality gate merely because their inherited
read economics use a different policy. The produced `.cmpct` file remained the exact attempt-5 archive;
this was a size/locality ceiling only.

## Frozen gate

A reader-visible shared-dictionary design was authorized only if one candidate produced all of:

- >= **128 KiB net archive saving** after dictionary storage + metadata charges;
- >= **8** independently profitable, locality-admissible direct/root records;
- exact dictionary compression/decompression round-trip for every measured record;
- weighted direct-pack materialization <= **8x**;
- maximum materialization among targets touched by the dictionary <= **8x**; and
- additional cold dictionary materialization <= **2x** per touched target.

The 128 KiB requirement deliberately exceeded the structural crossing gap. A new decoder dependency
needed enough headroom to pay for native-reader work, recovery metadata, CPU, and format bookkeeping
that the detached oracle still approximated.

## Measured result — REJECT

Workflow run **32010705186** completed green as an accounting/integrity experiment and produced artifact
**9281767803** (`sha256:b1df2292bcbd8f7cb0ab366b8bab001bfd92555f0c53981618219e479ed7de7f`).
The research hypothesis itself failed.

The best candidate was the **16 KiB dictionary**:

- eligible direct/root records: **118**;
- profitable before locality: **96**;
- locality-admissible profitable records: **95**;
- direct payload saving before dictionary cost: **23,289 B**;
- dictionary + metadata charge: **16,949 B**;
- exact net archive saving: **6,340 B**;
- frozen threshold: **131,072 B**;
- shortfall: **124,732 B**;
- gate fraction reached: **4.84%**;
- weighted direct-pack amplification: **6.254x**;
- maximum touched dependent-node amplification: **7.913x**;
- added cold dictionary amplification: **0.250x**.

The locality contract was therefore *not* what killed the idea; compression leverage was. Ninety-five
records remained admissible, yet each record typically gained only hundreds of bytes. Larger dictionaries
quickly became net-negative once their own storage cost was charged: 32 KiB lost **11,373 B** net, and
64/96/128 KiB lost **64,369 / 97,126 / 129,566 B** respectively.

This is useful negative evidence. A stored archive-global zstd dictionary is not the missing hostile-side
byte pool under the preregistered accounting. Implementing reader-visible dictionary context from this
result would add format/native/recovery complexity for only 6.3 KiB of measured headroom.

## Non-goals preserved

- Do not merge records into larger solids; record boundaries remain frozen.
- Do not omit dictionary storage cost.
- Do not assume a warm process cache; cold random access pays the dictionary once.
- Do not dictionary-code Preflate records.
- Do not change canonical revision 24 or attempt #5 output bytes.
- **Do not lower the gate after seeing this rejection.**

## Authorized next move

The preregistered **One-Hop Reference Context Frames** contingency is now active. It uses an already
stored similar direct/root record as bounded raw zstd history, so it tests cross-record context without
paying a new dictionary payload. Its rules remain frozen: bounded LSH <=8 candidates, one context hop,
context slice <=128 KiB, no context-coded logical bases, no target/context chaining, <=8x total cold
materialization and <=4x context-only amplification.

If that oracle also rejects the frozen >=128 KiB / >=8-target gate, stop tuning zstd cross-record context.
The next search must move to large-payload representation/backend choices rather than another dictionary,
residual-layout tweak, header shaving exercise or threshold relaxation.
