# Mosaic v0.29 — Columnar Residual Program oracle

Status: **detached contingency / no reader grammar / no v0.29.0 claim**.

## Question

Attempt #5 solid-packs canonical delta recipes, but every recipe interleaves low-entropy control fields
(opcode, literal length, COPY offset, COPY length) with literal bytes. Before designing any new grammar,
measure whether separating those fields into reversible columns creates enough physical compression gain
to justify the parser and recovery burden.

## Exact oracle representation

For each already-accepted attempt-5 residual group, the oracle writes a temporary logical payload:

1. `CRP1` marker;
2. member count and per-member operation counts;
3. one opcode byte per operation;
4. all literal lengths;
5. all COPY base offsets;
6. all COPY lengths;
7. all literal bytes.

Counts implied by opcodes make extra column tables unnecessary. The oracle decoder reconstructs each
canonical interleaved recipe and requires byte-for-byte equality before a group can contribute evidence.
The same real physical compressor used by attempt #5 measures the temporary columnar payload.

The oracle does **not** emit a columnar CMPCT archive. Its output archive remains exact attempt #5 bytes.

## Conservative accounting

A candidate columnar group must remain <=256 KiB and <=2.0x materialization relative to every target. In
addition to its measured physical record bytes, the oracle charges **32 B per group + 8 B per member** for
future grammar/descriptor transition cost. This intentionally overprotects against a favorable oracle
that ignores the metadata needed to make the representation real.

## Frozen gate

A reader-visible implementation is worth considering only if the hostile aggregate shows all of:

- exact recipe round-trip for every measured group;
- >= **128 KiB** aggregate saving after transition charges;
- >= **4** independently improved residual groups;
- <=256 KiB columnar logical records;
- <=2.0x per-member materialization.

The 128 KiB threshold is intentionally above the current ~101.5 KiB structural crossing requirement for
attempt #7. A new grammar must have headroom; merely squeaking past ZPAQ is not enough to justify more
reader/recovery surface.

## Disproof

If the oracle misses, preserve the result and reject columnar residual coding. Do not weaken the threshold
or combine it post hoc with another mechanism until each mechanism's independent ceiling is known.
