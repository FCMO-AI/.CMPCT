# J24P01 — installed cross-host fixed-wire S_PACK conformance, preregistration

**Freeze:** 2026-10-28 UTC. This document is committed **before** the J24P01 executable court or workflow. Science only, not a Reader fix, format change, merge, benchmark credit or release.

## Authority, ownership and collision scan

CMPCT `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains v0.30.0 / r24; this independent replication starts from the unchanged #307 fixed-golden PR HEAD `256a263748b9f65b4bc00dd572799e4f00ae06e7` (v0.31 integration base). #307 owns creation and Linux Python/native testing of two immutable Builder-independent S_PACK archives. #314 owns authenticated hostile native index tuples; #598/#601 own ordinary Python malformed PACK selective-range semantics; #322/#325 own native batching. Do not implement/duplicate any of those mechanisms or touch their files. This activation changes **only** an independent read/verification harness, hosted workflow and science record.

No `docs/discovery/CONCURRENCY_PROTOCOL.md` exists at the inspected main HEAD. `docs/discovery/STATE.json` is stale relative to the published release and owned for reconciliation by PR #574; do not write it.

## Primary question and strong controls

**Question:** Can the actual installed CMPCT Python Reader on Ubuntu 24.04, macOS 14 and Windows 2022 decode the **same original immutable #307 archive bytes** with identical logical contents, selective offsets, independent digest identities, complete extraction, and strict preflight handling of an authenticated malformed S_PACK extent?

Original #307 Ubuntu 24.04: six Python tests PASS in GitHub Actions #40047670471 at exact HEAD `256a263748b9f65b4bc00dd572799e4f00ae06e7`; Rust C ABI also passed on Linux. Those are source controls, **not** evidence of Windows/macOS behavior.

## Mechanism and alternative explanation

No representation change. The mechanism is **portable Reader semantics** for the same physical on-disk RAW and Zstd packed owner records. One shared blob contains four member rows including an exact duplicate slice and a nonaddressable interstice; a second archive uses compressed physical ownership.

A superficial three-host PASS may be an invalid import from the source checkout rather than the installed package; the court must establish installed path outside the checked-out source, exact source SHA binding, and frozen wire SHA identities **before** credit. A runner-native platform codec could vary without format drift, but frozen archives are immutable; never regenerate them for a green result.

## Preregistered decision and kill criteria

For **each** of the two original immutable archives, require:
1. exact `archive_sha256`, `archive_bytes`, magic and codec identity from #307 manifest before install;
2. full manifest member enumeration and independently checked logical SHA-256;
3. all full reads, all frozen nonzero ranges, zero-length EOF slices, one nonzero-offset duplicate-slice range, shared physical PACK descriptor equality, and `verify()` count match;
4. exact extractall(`metadata=False`) contents and no unexpected names;
5. one physical payload corruption causes an authenticated read rejection (never substituted with a mere wrong-byte output);
6. one index-rehashed physically unchanged out-of-bounds PACK tuple is rejected by `preflight_archive`, without weakening the ordinary `read_range` known-negative #598 contract.

**PASS** only if all six requirements complete on **all three** installed OS at one source SHA, without skips. **FAIL** if any mismatch, silent early truncated bytes, wrong member, corruption accepted, installed/source mismatch, absent platform, or untraceable evidence. Infrastructure install failures are **BLOCKED**, not product failures. If no all-host court is available, leave decision PENDING and never extrapolate from Ubuntu.

## Evidence costs and limits

One deterministic iteration per OS of 2 tiny archives (777 B and 764 B). Record SHA, Reader actual import location/source, all case-level booleans and artifact names; include a second independent manifest/receipt auditor (pure stdlib; no Reader import), and perturb at least one fabricated receipt to prove the auditor rejects it. This is compatibility correctness and evidence-enablement, **not throughput/RSS/performance or safety promotion**.

Unmeasured: native Rust ABI on macOS/Windows; source-file races and in-place changes; resource exhaustion; Windows special paths; wide Unicode aliases; concurrency; release/full general test parity. Maintain negative findings, especially authenticated malformed `read_range` defect #598, separately.

## Cheapest decision and future leverage

Avoid new encoder/reader logic. Reuse actual independent #307 bytes; run a direct Python installed cross-host court and detached receipt verifier. If red, report exact source/host defect to #307/#314/#601 owners. If green, attach bounded portability evidence to #307 and leave its existing release gates untouched.

**No policy change** is authorized from this single replication. A verified source-exact three-host result may inform future conformance/Reader promotion decisions, not grant promotion.
