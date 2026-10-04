# Roadmap to CMPCT 1.0

## 1.0 graduation target — strict 15/15 domination

The benchmark objective that previously gated v0.30 is now explicitly a **CMPCT 1.0** target.

Under equivalent semantics and controlled same-input measurement, CMPCT 1.0 should strictly beat both
ordinary ZIP/Deflate-9 and solid Zstd-19 in complete archive size **and** creation wall time on
**15/15 frozen serious workloads, with no ties**.

This target does not gate v0.30, v0.31 or other 0.x checkpoints. Pre-1.0 releases are rolling material
checkpoints under `docs/PRE1_RELEASE_POLICY.md`. Their losses remain visible and feed the next line.

The 1.0 target may not be obtained by weakening correctness, selective access, filesystem fidelity,
integrity, recovery, resource bounds, portability, timing boundaries or benchmark semantics.

## P0 — make the prototype defensible

- Maintain golden conformance archives and byte-exact round-trip vectors.
- Property/fuzz test parser bounds, corrupt indexes/records, malicious paths and recovery.
- Keep optional accelerators optional and portable.
- Keep the universal benchmark reproducible in CI.

## P0 — format completeness

- Freeze codec/transform registry and deterministic mode.
- Finish ownership/timestamps/xattrs/ACLs/path normalization contracts.
- Define encryption, split volumes, streaming/non-seekable creation and remote range access.

## P1 — size frontier

- Pursue licensed audited reversible compressed-stream preprocessing where economically justified.
- Generalize exact preprocessors only when complete product economics survive.
- Improve content-driven admission so expensive losing codecs are not built unnecessarily.
- Explore optional global stores without sacrificing self-contained archive defaults.

## P1 — performance frontier

- Move material hot paths into the shared memory-safe native core where evidence supports it.
- Reduce speculative candidate/search work.
- Improve parallel create/extract/verify deterministically.
- Continue zero-copy/range-backed and scalable CDC work.

## P1 — ecosystem

- Stable CLI/library API, mounts, platform integrations and import/export endpoints.

## Rule for new features

A new feature must be evidence-backed, content/structure driven, bounded and honest about exported costs.
Pre-1.0 releases need not win every workload; losses remain visible.
