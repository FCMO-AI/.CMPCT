# ONE-G0.2 general Law archive creation profile V2 — preregistration

Date: 2026-09-10
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Status: **PREREGISTERED BEFORE V2 RESULT-BEARING PERFORMANCE EXECUTION**

## Mission lock

Re-run the transfer-only creation/RSS falsifier after correcting one topology defect in the old `mixed-8x512k` fixture. V2 exists because the V1 mixed row derived XOR from an ADD8 Law predecessor, while the promoted product seam intentionally rejects nested relation predictors to preserve selective-read locality. V2 must exercise the same intended Law breadth without weakening that product invariant.

This is not a Genesis run and does not authorize candidate promotion by itself.

## Frozen comparator and thresholds

The comparator, measurement process, round count, and every numeric V1 gate remain unchanged:

- comparator: same-input `build_authenticated_archive` Surprise-only seam;
- 9 measured fresh-process rounds after one discarded sanity launch per arm/case;
- unrelated median CPU <= 1.15x;
- unrelated median wall <= 1.15x;
- unrelated worst paired CPU <= 1.30x;
- unrelated median peak RSS <= 1.10x;
- unrelated candidate wire byte-identical to comparator;
- unrelated exact relation proof bytes == 0;
- every productive case stored bytes < comparator;
- median productive stored ratio <= 0.70x;
- median productive build CPU <= 2.00x comparator;
- no productive case median build CPU > 2.50x comparator;
- median productive peak RSS <= 1.20x comparator;
- candidate authentication source reread == 0.

No threshold may be changed after observing V2 output.

## Frozen cases

Retain `unrelated-1m`, `exact-copy-1m`, and `add8-1m` byte-for-byte from V1.

Replace only the internal topology of `mixed-8x512k`, keeping eight 512 KiB regular files:

1. `00-base.bin`: deterministic high-entropy Surprise base;
2. `01-copy.bin`: exact reuse of `00-base.bin`;
3. `02-add.bin`: ADD8(+37) from `00-base.bin`;
4. `03-xor-source.bin`: independent deterministic high-entropy Surprise source;
5. `04-xor.bin`: XOR(0xA5) from `03-xor-source.bin`;
6. `05-fill.bin`: Fill('Q');
7. `06-random.bin`: unrelated deterministic high-entropy content;
8. `07-random.bin`: second unrelated deterministic high-entropy content.

The builder receives only the source-tree path. It receives no operation labels, source/target hints, constants, or expected roots.

## Added anti-vacuity semantic gate

Before any V2 performance decision is admissible, reader-side inspection of the produced candidate graph must prove on the mixed row:

- `01-copy.bin` shares the same root reference as `00-base.bin`;
- `02-add.bin` root operation is `add8`;
- `03-xor-source.bin` root operation is `surprise`;
- `04-xor.bin` root operation is `xor`;
- `05-fill.bin` root operation is `fill`;
- unrelated roots remain Surprise and are not silently crystallized as exact reuse/Fill/ADD8/XOR.

The same reader-side principle applies to the single-relation productive rows: exact-copy and ADD8 must actually exercise their named structure. A Surprise fallback cannot earn a favorable performance conclusion merely because it is fast.

## Decision law

`ADVANCE_CREATION_PROFILE_V2` requires:

1. exact semantics and deterministic wire;
2. all V2 reader-side structure gates;
3. all unchanged V1 resource/byte thresholds.

`HOLD_CREATION_COMPUTE_V2` applies when correctness and intended structure are intact but any unchanged performance gate fails.

`RETIRE_OR_REPAIR_V2` applies to semantic, determinism, reader-ontology, or intended-structure failure.

Preserve every raw sample and the strongest regression. V1 history remains immutable and must not be rewritten as though it had exercised V2 topology.

## Genesis exclusion

V2 must not import, generate, inspect, encode, compare, score, or infer any of the frozen 15 Genesis workloads. It does not compare ONE with frozen v0.29 or v0.30 and does not select a Genesis winner.
