# ONE-G0.2 compact validation certificate V2 — preregistration

Date: 2026-09-09

## Mission lock

V1 demonstrated that a dense immutable uint64 validation certificate can reduce large-graph retained Python preflight state to about 0.223x incumbent while preserving median open/read economics, but it HOLDed because a tiny add8 graph paid 1.794x repeated-read CPU. The current hot lookup uses `Struct('<Q').unpack_from(...)[0]` per node-length access.

V2 changes **only the packed lookup representation/access path**. It does not change Program validation, accepted logical-length domain, reader semantics, benchmark rows, request geometry, or promotion thresholds.

## Falsifiable hypothesis

On little-endian machines, exposing the already-immutable packed bytes through a read-only native uint64 memory view will remove enough Python unpack/temporary-return overhead that the V1 worst repeated-read regression disappears, while preserving the large-graph retained-state win. On non-little-endian machines, explicit little-endian decoding remains authoritative so portability is unchanged.

Disproof: any semantic mismatch, any weakening of the >uint64 fallback, retained-state regression outside the frozen V1 limits, or failure of any V1 CPU gate.

## Frozen matrix

Unchanged from V1:

- families: add8, XOR
- requested root: 128 KiB
- requested range: first 4 KiB
- unrelated valid nodes: 0, 64, 256, 1,024, 4,096
- 15 warmed CPU measurements per cell
- ordinary validated certificate remains the comparator

## Frozen promotion gates

Unchanged from V1:

- exact semantic parity on every row;
- at 4,096 unrelated nodes, compact retained Python preflight bytes <= 0.40x ordinary;
- compact retained state <= 12 B/node + 256 B;
- median repeated-read CPU <= 1.15x ordinary;
- **every** repeated-read row <= 1.30x ordinary;
- median one-time open CPU <= 1.25x ordinary.

No gate may move after evidence exists.

## Implementation constraint

The certificate remains an optimization *after* complete ordinary validation. Any validated node length greater than uint64 must continue to retain the ordinary certificate rather than fail validation or truncate. The immutable Program snapshot and resource proof remain the authority.

A V2 ADVANCE promotes a lower-overhead in-memory proof representation only; it changes no ONE wire or reader-visible mechanism.
