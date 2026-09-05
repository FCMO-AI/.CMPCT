# ONE-G0.2 — temporal-adjacency writer integration preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Status: frozen before result-bearing execution

## Mission lock

The amortization-safe known-pair turnstile has proven that the existing sparse exact-shift falsifier pays where its fixed 160-byte information bill can amortize, while direct exact proof is the correct path below 16,000 relation bytes. That evidence still receives relation-pair identity for free.

This experiment asks whether the execution law survives one natural ONE writer context where pair identity is not a discovery expense: **adjacent versions of the same logical object**. No global resemblance index, certificate zoo, new reader opcode, or second discovery pass is allowed.

## Falsifiable hypothesis

For adjacent versions already presented to the writer as `(previous, current)`, using the frozen amortization-safe turnstile before exact bounded shift proof will:

1. preserve every productive exact relation accepted by the baseline exact dispatcher and preserve the same best shift;
2. preserve byte-exact reconstruction after compiling accepted relations into the existing generic ONE grammar (`surprise` + `concat` + ranged `Ref`), with no relation-specific reader operation;
3. preserve identical emitted ONE wire bytes between baseline and candidate whenever both choose the same accepted relation or literal fallback;
4. reduce median **complete research-writer elapsed time** by at least 8% across the frozen mixed temporal stream while no individual size class exceeds 1.03x baseline;
5. leave stored bytes, reader work, and selective reconstruction semantics unchanged relative to the equivalent baseline decision because only writer-side admission changes.

Failure of (1)–(3) retires the integration immediately. Failure of (4) means the turnstile remains a valid micro-optimization but is not promoted into this writer path. No timing threshold or relation corpus will be changed after result.

## Frozen inputs

Sizes: `4, 8, 16, 32, 64, 128, 256 KiB`.

For each size, create a deterministic temporal stream with five adjacent transitions:

- exact `+1` shifted version;
- `+1` shift with a quarter damaged (expected relation acceptance under the existing proof-led semantics);
- `+1` shift fragmented every 96 bytes (expected relation acceptance);
- mutation every 32 bytes / false-pattern control (expected fallback);
- independent random next version (expected fallback).

The same source/target pairs used by the frozen relation-transfer corpus are reused so this experiment changes integration context, not relation semantics.

## Writer compilation

The baseline and candidate writers both receive adjacent-version identity from the caller. They differ only in relation admission:

- baseline: existing exact safe relation dispatcher for every adjacent pair;
- candidate: frozen amortization-safe dispatcher (`<16,000 B` direct exact proof; otherwise sparse gate then exact proof on a fire).

If a relation is accepted at shift `+1`, compile the current version using generic ONE structure only:

- previous version as an ordinary `surprise` node;
- current version as `concat(Surprise-prefix, ranged Ref(previous))` for the exact shift-only case when byte-exact;
- if the accepted proof-led relation contains damage that cannot be represented by that simple concat without changing semantics, fall back to literal Surprise in this integration experiment rather than inventing a relation opcode.

This means the speed experiment may find useful admission even when the current minimal generic compiler cannot yet turn every accepted damaged relation into density. That gap must be reported, not hidden.

All produced programs must round-trip through `encode_program -> decode_program -> reconstruct` and match the target bytes exactly.

## Frozen measurements

Per size and aggregate:

- baseline and candidate total writer elapsed time, including dispatch, Program construction, wire encoding and semantic round-trip verification outside the timed region;
- candidate/baseline timing ratio;
- productive relation opportunities retained and best-shift equality;
- candidate gate bytes and gate/direct counts;
- exact-shift relations compiled generically versus accepted-but-not-yet-compiled damaged relations;
- emitted wire bytes and Surprise bytes;
- decoded/reconstructed byte equality;
- node count and modeled retained writer state added by the turnstile (zero persistent state beyond call-local gate state).

Timing uses interleaved baseline/candidate order and medians over 31 rounds. Semantic verification is excluded from timing equally for both paths because reader execution is not part of writer creation cost; wire encoding remains inside timing.

## Frozen gates

Advance this integration only if all are true:

- exact relation classification and best shift match baseline on every row;
- every emitted program round-trips and reconstructs exactly;
- same semantic decision => byte-identical wire between baseline and candidate;
- every size-class candidate/baseline elapsed ratio `<= 1.03`;
- aggregate median mixed-stream candidate/baseline elapsed ratio `<= 0.92`;
- candidate adds no persistent writer state and no reader-visible operation;
- no stored-byte regression relative to the same semantic baseline decision.

## Hostile-review boundary

A pass would establish an efficient **adjacent-version known-pair writer path**, not arbitrary object-pair discovery. It would also expose how much of the proven relation opportunity the current minimal ONE grammar can actually compile into density without adding a new opcode. Accepted-but-uncompiled damaged relations are explicit compiler debt and may become the next Law-expression target.

A pass does not establish product speed, v0.29/v0.30 superiority, general resemblance discovery, or a canonical format change.
