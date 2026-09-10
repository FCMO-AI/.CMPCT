# ONE-G0.2 general candidate-boundary hostile economics prereg — 2026-09-10

Status: **PREREGISTERED BEFORE HOSTED OUTCOME**

Claim boundary: transfer/synthetic evidence only. This experiment MUST NOT import, generate, read, encode, compare, score, or infer any of the frozen 15 Genesis workloads.

## Mission lock

Determine whether the current automatic arbitrary-tree ONE Law + Surprise builder is safe enough to be considered a product-boundary candidate with respect to the most basic Crystallization invariant: accepting a discovered Law must not make the complete authenticated archive larger than the same tree represented by the authenticated Surprise-only seam.

This is not a density promotion test. It is a falsifier for a necessary candidate-boundary property.

## Hypothesis

For independently constructed transfer trees, including deliberately tiny exact relations, the current automatic general-Law builder will produce byte-exact deterministic authenticated ONE archives and will never exceed the complete persistent bytes of the authenticated Surprise-only archive for the same tree.

## Disproof

The hypothesis is disproved by any row where:

1. whole-tree semantics are not exact;
2. the wire is nondeterministic;
3. the reader-visible algebra contains anything outside the generic ONE operations already defined by the experimental IR;
4. the general-Law complete authenticated wire is larger than authenticated Surprise-only complete wire; or
5. the builder relies on benchmark hints rather than receiving only a source-tree path.

Any size regression is a HOLD for general candidate-boundary certification even if other rows save many bytes. A mature product boundary must be able to decline uneconomic Crystallization rather than average the mistake away.

## Transfer rows

The falsifier uses only deterministic synthetic trees unrelated to Genesis:

- `tiny_add8_1b`: two one-byte files related by ADD8 constant;
- `tiny_xor_2b`: two two-byte files related by XOR constant;
- `tiny_fill_1b`: one one-byte constant file;
- `beneficial_add8_4k`: a high-entropy 4096-byte base followed by an exact ADD8 constant target;
- `beneficial_exact_reuse_4k`: a high-entropy 4096-byte file followed by an exact copy;
- `incompressible_pair_4k`: two unrelated deterministic high-entropy files;
- `mixed_hostile_tree`: tiny relation opportunities, unrelated bytes, empty file, directory, executable mode, and safe symlink in one arbitrary tree.

File names are descriptive to the falsifier, but the candidate builder receives no relation labels, constants, source/target pairing, or expected operation. It receives only the tree root.

## Accounting

For every row build both:

- current `build_general_law_archive(tree)`;
- current `build_authenticated_archive(tree)` Surprise-only control.

Count `len(wire)` for each side. These are complete ONE Program wires containing file roots, Surprise payloads, canonical filesystem metadata, integrity hashes, persisted authentication trees/index material, limits, and root table.

Do not substitute payload-only accounting.

## Semantic checks

Open both wires through `open_authenticated_archive` and independently compare every source entry:

- regular-file bytes and digest;
- regular-file mode;
- directory mode;
- symlink target and mode.

Run the general builder twice and require byte-identical wire.

Reader-visible operations must be a subset of `{surprise, concat, repeat, fill, xor, add8}`.

## Decision

`ADVANCE_GENERAL_CANDIDATE_BOUNDARY_ECONOMICS_PREFLIGHT` requires all rows to satisfy every semantic/determinism/ontology gate and `general_wire_bytes <= surprise_wire_bytes`.

Otherwise emit `HOLD_GENERAL_CANDIDATE_BOUNDARY_ECONOMICS` and preserve each losing row plus its exact byte delta.

A HOLD is a useful result. The next action must be to add economic opportunity rejection inside the same ONE representation, not to hide the losing case behind a separate codec or weaken the row.

## Explicit exclusions

This prereg does not measure or claim:

- Genesis performance;
- comparison with frozen v0.29 or v0.30;
- CPU/wall/RSS promotion;
- selective-access promotion;
- canonical CMPCT release status;
- winner selection.

`genesis_inputs_executed`, `genesis_comparison_executed`, `genesis_scoring_executed`, and `genesis_winner_selected` must remain false in the resulting receipt.
