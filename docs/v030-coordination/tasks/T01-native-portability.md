# T01 — Native r25 / portability completion

- **Owner:** slot-01
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-coop-native-portability`
- **Dependencies:** may implement against bootstrap integration head; final evidence must be rerun/rebased after T00 reconciliation.
- **Working integration base observed:** `ae8d3b91e74ca8e60653208f5b3bd1055d1b5b55`

## Objective

Make every representation that the final v0.30 selector can publish independently readable and verifiable through the shared native/portable surface, with the same recovery/resource semantics as Python and with no second incompatible parser architecture.

## Scope

- canonical r25 G0–G4 Geometry native/shared reader parity;
- canonical r25 PrefixGraph native/shared reader parity;
- exact r24 fallback delegation to the mature existing core;
- deterministic builder-independent golden archives/vectors;
- primary/tail recovery parity and hostile metadata/resource checks;
- single-member/selective read parity and <=8x policy observability;
- ZIP/export interoperability for new profiles;
- native ABI/CLI integration using the repository's shared memory-safe core design;
- platform/Android acceptance infrastructure required by existing policy.

## Owned paths

Prefer `native/**`, native-specific tests/vectors, `docs/NATIVE_CORE.md`, `docs/PORTABILITY.md`, and narrowly necessary canonical profile adapters. Do not change compression-selection thresholds or benchmark floors.

## Must not regress

- r24 reader compatibility and ABI;
- exact canonical archive bytes unless an intentional format-profile correction is documented and rebenchmarked;
- bounded MessagePack/resource admission;
- recovery semantics;
- Python/native tree and member identity.

## Completion evidence

1. Python writer -> native verifier/read/extract golden parity for each promoted r25 profile.
2. Builder-independent committed golden archives decode identically in Python and native implementations.
3. Primary-damaged/tail-valid and tail-damaged/primary-valid recovery parity; both-corrupt fails closed.
4. Hostile/fuzz/resource/path cases green.
5. Native CLI/ABI selective member reads demonstrate the same logical bytes and locality contract.
6. ZIP export from each selected representation round-trips through stock tooling.
7. Existing native/core regression suite remains green.
8. Relevant portability/format/native docs are accurate, not aspirational.

## Handoff

Set `REVIEW` with exact source head, commits intended for import, golden-vector paths, Cargo/Python test commands actually run, known platform gaps, and any conflicts expected with T00/main.
