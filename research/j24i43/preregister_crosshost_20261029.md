# J24I43c — prospective cross-host product-integrity court (2026-10-29 UTC)

Status: **PREREGISTERED; no macOS/Windows outcome has been observed for this court.** Parent: PR #788 source HEAD `4b7991344cfe149353c072fd12371a600f051ffb`. Existing Ubuntu native-core / 2-size complete-verifier A/B and authentic physical evidence are separate results; do not transfer their green status to other platforms.

## Question and falsifier

Can the same source-owned `Archive::verify_complete()` codec-2 streaming path compile and correctly authenticate original revision-24 Builder WAV/FLAC records on macOS arm64 and Windows 2025, and reject independent one-bit physical mutations in CMA4 CRC, mid-FLAC payload and the encoded FLAC magic, *without* weakening either reader or examiner semantics?

A single incorrectly accepted mutated record, rejected authentic Builder archive, platform-specific build/import failure, missing evidence artifact, changed metadata/header/index/frozen fixture semantics, or different source SHA in the checkout is a **red**. Infrastructure failures are not product corruption evidence; classify independently and preserve logs. Existing Ubuntu results are not a substitute.

## Instrument and inheritance

Use unchanged `research/j24i38/generate_builder_wav.py`, `audit_builder_wav.py`, J24I39/J24I42 exact physical-span instruments and `research/j24i43/physical_mutants.py` (one bit only). Compile the exact current candidate Rust `native/cmpct-core` source into `j24i43_probe` on each host; two files (8/32 MiB) must pass `verify_complete() == 1`, six separately hostile files must fail. Source identity, platform, raw stdout/stderr and file checksums must be uploaded per host; do not use a simulator as cross-platform product evidence.

This court is an *integrity/portability* discriminator. It does not assert equal process RSS or wall cost across heterogeneous runners and does not prove selective read parity, arbitrary valid FLAC profiles, concurrent in-place mutation safety, format evolution, native ABI integration or release qualification.

## Cheapest decisive controls

The strong simpler control is the existing Ubuntu product court at HEAD `4b799134...` with successful real artifact custody: run 40970496111 / artifact 12940297204. This new court asks only whether those guarantees survive different host runtimes and Rust build targets. No new codec or format implementation is warranted merely to obtain a green test.

Do not relax reject classes, archive identity, thresholds, source pinning or artifact requirements to rescue a result. If transport/setup fails, classify as infrastructure evidence and switch to a dependency-safe task. If it passes, record the exact SHA/host/artifact and scope, then seek inherited release/ABI evidence before promotion.

## Concurrency and ownership

PR #788 remains the Phased3 native WAV streaming owner; #765 owns native CRC integration, #759 the historical symlink verifier; other active phases own journal/fsmeta restoration. This test makes only a research/CI mutation on the existing candidate branch. It does not change v0.30 publication, numeric version, release format, Native Core ownership, or the repository discovery cache.
