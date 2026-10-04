# F-01 / O0.1 frozen instrument contract

This is a **pre-result instrument supplement** to
`docs/v030-rnd/REVERSIBLE_STRUCTURE_COMPILER_O01_PREREG.md`. It records concrete choices the
preregistration deliberately left to implementation. It does not grant product/release credit and must not
be edited in response to the result of the decisive pass.

## Frozen implementation boundary

Scientific grammar/search implementation: `9cbbed9b264e84cebcc0352f7f7878f5cad90f65`  
Decisive evidence-accounting wrapper: `c3ef298bcc3fb7f95a65245c9341f112581aa175`

The exact first admissible result is defined in `F01_O01_EXECUTION_STATE.md`.

## Research serialization and charged grammar

Every candidate is an actual self-delimiting research program. The comparator is its real serialized byte
length, not a modeled payload estimate.

Frozen opcodes:

- `R`: raw terminal;
- `Z`: Zstd-19 terminal, selected only when smaller than the raw terminal payload;
- `W`: existing exact Lattice fixed-width lane transform, widths `{2,4,8,16}`;
- `D`: existing exact Geometry delimiter transform, using only content-derived candidates from the existing
  bounded `_delimiter_rank` implementation;
- `S`: one exact two-child split/concatenation node.

For every operator, opcode bytes, logical sizes, parameters, child lengths, transformed terminal streams and
all other bytes needed by the research decoder are serialized and charged. Exact inverse reconstruction is
executed before a candidate can become evidence.

No cross-object reference, edit program, learned transform, benchmark identity, path/name dispatch, arbitrary
code, or new transform family is available in O0.1.

## Frozen bounds

- maximum target size: `256 KiB`;
- split locations: every `4096` bytes strictly inside the target;
- maximum research-program decode depth: `4`;
- split children independently minimize the same one-stage `DIRECT/LANE/DELIM` candidate set;
- search uses no heuristic pruning;
- exact optimistic pruning is permitted only when the already-serialized best child programs are themselves
  no smaller than the incumbent before positive split framing is added.

Within that grid grammar, the search result is exact: every eligible split is either fully priced or rejected
by an additive lower bound that cannot hide a winning split.

## Frozen manual control

For each target the manual comparator is the smallest fully charged whole-target candidate among:

1. direct `R/Z`;
2. one existing Lattice lane transform followed by `R/Z`;
3. one existing Geometry delimiter transform followed by `R/Z`.

Literal/raw fallback is also reported independently.

This is intentionally a **one-stage manual frontier**, matching the O0.1 question. A win against it is
composition headroom, not yet proof against every historical CMPCT research representation.

## Frozen materiality rule

A split composition counts as a **material composed win** only when it saves both:

- at least `128` serialized bytes; and
- at least `0.5%` of the exact manual-control program size.

These values are an instrument-level witness threshold, not a future release threshold. They were fixed before
an admissible decisive result existed. They must not be relaxed after observing the result.

## Discovery / hostile / transfer structure

The decisive wrapper fingerprints the complete discovery + hostile manifest before search. Discovery includes
both mixed lane+record geometry and a causally distinct adjacent mixed-lane-width case. Hostile controls include
random bytes, tiny structured input, and separator-rich false structure.

Transfer cases are generated only from the exact public source commit after the grammar and discovery/hostile
instrument are fixed. One transfer generator uses a different matrix/row construction path from the discovery
helpers.

## Fail-closed positive interpretation

`ADVANCE_COMPOSITION` or `DISCOVER_PRIMITIVE` is admissible only if:

- at least two normalized, causally distinct material composition signatures survive discovery;
- at least one material composition win survives post-freeze transfer;
- hostile false wins are zero;
- all winning bytes include their complete research-program charge;
- exact reconstruction succeeds;
- the Oracle Gift Ledger remains explicit.

Otherwise the wrapper may only return a non-positive preregistered state. A green workflow by itself is not a
positive thesis result.
