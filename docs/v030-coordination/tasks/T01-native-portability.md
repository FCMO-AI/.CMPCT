# T01 — Native r25 / portability completion

- **Owner:** slot-01
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-coop-native-portability`
- **Dependencies:** may implement against bootstrap integration head; final evidence must be rerun/rebased after T00 reconciliation.
- **Working integration base observed:** `ae8d3b91e74ca8e60653208f5b3bd1055d1b5b55`

## Objective

Make every representation that the final v0.30 selector can publish independently readable and verifiable through the shared native/portable surface, with the same recovery/resource semantics as Python and with no second incompatible parser architecture.

## Immediate native parser blocker — preflight declarations before `rmpv` allocation

Slot-00 adversarial review found that `native/cmpct-portable/src/format.rs::parse_msgpack` currently calls `rmpv::decode::read_value` first and only then applies `validate_value` node/depth/container checks.

Bounding `raw.len() <= 8 MiB` is **not** sufficient. A small hostile MessagePack stream can carry a huge array/map/string/bin declaration; a general decoder may reserve/allocate from that declaration before the post-decode validator ever sees the object. This violates the repository's established hostile-input invariant: declaration bounds must be checked before general MessagePack allocation.

Required correction:

- add a zero-/low-allocation MessagePack declaration preflight over the encoded bytes **before** `rmpv::decode::read_value`;
- enforce nesting depth, total node count, map/array element counts, string/bin/ext declared lengths, integer marker completeness and input bounds during preflight;
- reject reserved/unsupported markers and truncated length bodies without relying on the second decoder;
- keep the post-decode semantic validator as defense in depth rather than replacing it;
- reuse/adapt the mature r24/native or Python guarded-reader declaration semantics where possible instead of inventing a weaker independent policy;
- add hostile tests with tiny byte strings declaring enormous array/map/bin/str containers and prove they fail **before** general decode/allocation;
- fuzz the preflight and require no panic/overflow;
- preserve the 8 MiB metadata raw/decode ceiling and all existing semantic limits.

Footnote: a parser that rejects a giant container *after* allocating for it is not resource-bounded, even if it eventually returns an error.

## Cross-lane canonical-profile dependency

Your `native/cmpct-portable` architecture is accepted in principle because r24 delegates to the mature `cmpct-core`; do not replace that with a copied r24 parser.

However, the current native dispatcher still recognizes research identities `CMPNXG4` / `CMPNXP1`. Slot-03's provisional canonical product surface has selected fixed revision-25 profile identities `CMP25G4\0` and `CMP25PG\0`, with real canonical r24 fallback rather than relabelled research bytes.

Until T03 reaches REVIEW:

- keep r25 grammar implementation/recovery/resource work moving;
- do **not** treat research magics as final ABI/golden-vector authority;
- isolate profile identity constants so the canonical identity reconciliation is surgical;
- do not commit final builder-independent r25 goldens or release receipts against research magics;
- final native evidence must run after the T03 canonical profile decision is imported/reconciled.

If T03 changes actual reconstruction semantics rather than only profile identity/fs metadata framing, mark the affected native work `BLOCKED` and identify the exact semantic delta instead of silently accepting a byte mismatch.

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
4. Hostile/fuzz/resource/path cases green, including pre-allocation MessagePack declaration bombs.
5. Native CLI/ABI selective member reads demonstrate the same logical bytes and locality contract.
6. ZIP export from each selected representation round-trips through stock tooling.
7. Existing native/core regression suite remains green.
8. Relevant portability/format/native docs are accurate, not aspirational.

## Handoff

Set `REVIEW` with exact source head, commits intended for import, golden-vector paths, Cargo/Python test commands actually run, hostile preflight tests/fuzz results, known platform gaps, and any conflicts expected with T00/main/T03 canonical profile identity.
