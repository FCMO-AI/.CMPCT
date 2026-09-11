# ONE-G0.2 Crystallization economics sweep — preregistration

Date: 2026-09-08
Scope: `research/cmpct1`, ONE-G0.2

## Mission lock

Selective Crystallization is not only a safety valve. In ONE, retaining a weak Law is justified only while the information it removes is worth more than its canonical control bytes and reader work. The writer must prefer explicit Surprise when a discovered relation has negative marginal information yield.

This experiment does **not** change canonical semantics, reader opcodes, comparator settings, or the frozen bounded-Surprise productive gates. It studies an already-discovered relation using the same generic `surprise` + ranged `Ref` + `concat` grammar.

## Referee hypothesis

For a fixed 50%-reuse temporal relation whose segments become progressively finer, there exists a representable pre-hard-cap region where preserving every reuse fragment becomes economically worse than Crystallizing the same current bytes as Surprise.

The causal mechanism is canonical control overhead: every retained fragment needs reference metadata even though the bytes it predicts become small. The hard 4,096-reference reader cap is a safety boundary, not an information-efficiency optimum.

### Disproof

The hypothesis is disproved for this matrix if every non-Crystallized candidate below the hard fan-in cap remains smaller on the canonical wire than the equivalent Crystallized current root, or if any apparent crossover depends on semantic mismatch or unequal root/source accounting.

## Controlled construction

For each target size, create deterministic source bytes and a current root made of alternating equal-width spans:

- even spans: exact ranged reuse from the previous/source root;
- odd spans: deterministic changed bytes carried as Surprise.

The source root is stored identically in both candidates, so its cost cancels.

Candidate A retains the discovered Law using bounded Surprise pooling.
Candidate B Crystallizes the entire current root into one Surprise node while retaining the identical previous/source root.

Both Programs must reconstruct `previous` and `current` byte-exactly and must use identical declared `Limits`.

## Frozen sweep

Target sizes:

- 64 KiB
- 256 KiB

Alternating span widths in bytes:

`8, 9, 10, 12, 16, 24, 32, 48, 64, 96, 128, 256, 512, 1024, 2048, 4096`

The very fine rows may trigger the already-established hard safety Crystallization fallback. Those rows are controls and may not be used as evidence of a *pre-hard-cap* economic crossover.

## Measurements

For both candidate Programs record:

- canonical wire bytes;
- Surprise payload bytes;
- control + integrity bytes;
- Program nodes;
- total encoded reference count;
- current-root full-range work/materialized bytes and nodes touched;
- exact reconstruction.

For retained-Law rows also record discovered maximum group fan-in and any safety-triggered Crystallization.

Derived quantities:

- `wire_delta = retained_wire - crystallized_wire`;
- `net_bytes_saved = crystallized_wire - retained_wire`;
- `control_cost_per_reused_byte`;
- `reference_count_per_reused_byte`.

## Decision

`PRE_HARD_CAP_CROSSOVER_FOUND` requires at least one row where:

1. the retained-Law Program did **not** trigger the hard fan-in fallback;
2. both Programs are semantically exact and canonically round-trip;
3. retained-Law canonical wire bytes are greater than or equal to the Crystallized canonical wire bytes.

`NO_PRE_HARD_CAP_CROSSOVER_ON_MATRIX` means all semantically valid retained-Law rows below the hard cap remain strictly smaller.

No production policy is promoted from one synthetic family alone. A crossover only earns the next experiment: derive a cheap local writer estimator and test it across structured, random, compressed-like, shifted, tiny and hostile plans without corpus-specific thresholds.

## Promotion boundary

This experiment is mechanism-level causal evidence only. It earns no v0.29/v0.30 scoreboard point, does not alter the 15-workload gate, and does not authorize a numeric CMPCT release.