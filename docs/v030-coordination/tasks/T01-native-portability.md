# T01 — Native r25 / portability completion

- **Owner:** v0.30 sole executor
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-authoritative-integration`
- **Dependencies:** final authority must run on the same exact reconciled candidate used by T00–T04.

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

## Preferred implementation area

Prefer `native/**`, native-specific tests/vectors, `docs/NATIVE_CORE.md`, `docs/PORTABILITY.md`, and narrowly necessary canonical profile adapters. Because one executor owns the full release, adjacent product code may be changed when required to close a proven interface defect, but compression-selection thresholds and benchmark floors remain frozen unless the release policy itself explicitly requires a stricter gate.

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
9. Android/platform acceptance required by repository policy is tied to the exact release candidate, including the shared portable dispatcher rather than an independent parser.

## Current exact continuation state

The canonical implicit-v4 filesystem-control seam is already implemented in the shared portable reader and Android instrumentation. The remaining boundary is evidence/productization, not a second parser implementation.

The authoritative branch now contains a stronger `tests/native_v030_implicit_manifest.py` recovery matrix. For both builder-independent G04/PrefixGraph implicit-v4 goldens it independently damages primary metadata, tail metadata, both copies, and payload bytes. A single valid metadata copy must still reconstruct the exact public tree; both metadata copies or payload corruption must fail closed. The live canonical writer's admitted implicit-v4 archive is subjected to the same matrix so fixed goldens cannot hide writer/framing drift.

The native-authority workflow now emits a fingerprint-bound strict JSON artifact after the full Python/Rust/golden/recovery/selective-read matrix succeeds. That artifact records only the facts this lane proves (`g04_native_parity`, `prefixgraph_native_parity`, builder-independent goldens, native/implicit-v4 recovery, r24 fallback verification and shared-core use). Logs-specific parity/recovery facts remain owned by their separate evidence and must not be inferred from the native artifact.

Hosted Android evidence now uses exact-head preserved-running custody plus a newest-commit classifier. This repairs the observed failure mode where unrelated commits on the long-lived integration PR cancelled a 60-minute emulator run mid-build. Its durable artifact explicitly records canonical-r25 and implicit-v4 portable dispatch alongside Logs inverse and compact-control dispatch. The physical ARM64 lane will accept hosted evidence only when all four dispatch facts, candidate SHA and release fingerprint match exactly; it still requires a real non-QEMU ARM64 Android device and cannot synthesize that receipt.

These changes are **not yet completion evidence merely because they are committed**. Do not move T01 to `DONE` until the substantive current-fingerprint native authority, hosted Android, ZIP portability, recovery/fuzz/resource and required physical ARM64 receipts are genuinely complete and machine-checkable. Classifier-only greens, queued jobs, cancelled runs and historical fingerprints earn zero completion credit.

## Current continuation rule

Work directly on the authoritative branch. Preserve useful earlier implementation/evidence provenance where it still applies, but rerun every normative native/platform receipt on the final reconciled fingerprint. Historical or pre-fingerprint greens prove mechanisms only.

Move T01 to `DONE` only when the implementation and all release-lock evidence obligations are durably closed on the authoritative branch.
