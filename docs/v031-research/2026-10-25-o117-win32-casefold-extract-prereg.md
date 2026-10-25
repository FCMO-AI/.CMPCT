# O117 preregistration — host-case alias collision in exact archive extraction

Date: 2026-10-25 UTC. Branch: `agent/phased3-v031-o117-win32-casefold-extract-falsifier-20261025`.
Baseline: canonical `agent/v031-development` at `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, revision 24, released v0.30.0; no source modification authorized in this experiment.

## Question and motivation
The Reader uses `canonical_logical_path()` for an archive's logical keys; this intentionally does not implement host-specific case normalization. `extractall()` then creates files through host paths. Can an authentic archive containing distinct Linux-legal keys `Report.txt` and `report.txt` satisfy ordinary reader verification, yet extract to only one physical file on an ordinary case-insensitive Windows filesystem without raising an error?

## Pre-result prediction
Create both entries on Linux from different nonempty payloads, build a genuine CMPCT archive, and independently verify the two exact logical members. Linux extraction should preserve two different files. On standard hosted Windows NTFS, paths differing only by ASCII case should alias, so a successful extraction may leave only the last payload despite returning without error. If the Windows filesystem is configured case-sensitive, the experiment must report that environment distinction rather than claim a failure.

## Stronger/simpler controls
- Archive-native `CMPCT.read()` and `CMPCT.verify()` establish that compression/storage itself preserves both member bytes.
- Linux same-artifact extraction establishes that ordinary extraction can preserve two names on a case-sensitive destination.
- A Windows probe creates two named files in the target directory and checks whether they physically alias *before* interpreting the result.
- The output inventory, full-byte SHA-256 per name, and Reader success/failure are kept separate; a success return is not a preservation proof.
- A filename pair `one.txt`/`two.txt` verifies the same Windows destination can extract distinct names.

## Falsifier / kill conditions
If actual Windows extraction rejects the conflicting archive before modifying either output, does not alias, or preserves both logical payloads as separate physical files, the strong loss-of-fidelity claim is falsified/narrowed. If the archive cannot be built and read exactly on Linux, the scientific instrument is invalid. Any installation, provider or build failure is infrastructure debt, not evidence of product failure.

## Evidence rung and scope
Source-exact installed product, authentic archive, independent Ubuntu producer/consumer and Windows consumer on the *same uploaded archive bytes*. Frozen checksums bind the artifact between jobs. Failure modes are host filesystem namespace fidelity, not compression, representation or release performance. No benchmark, source patch, threshold or release credit is authorized. Preserve negative/contradictory outcomes. Do not mutate other PRs or `docs/discovery/STATE.json`; coordinate through this isolated research branch.

## Anticipated decision
A confirmed collision warrants a host-aware admission/namespace-fidelity contract and a genuine pre-write falsifier, rather than a silent filename transformation or only a post-hoc verification. A negative means no product patch is justified by this hypothesis.
