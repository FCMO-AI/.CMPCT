# J24G01 — preregistered independent committed-generation golden vector

**Date:** 2026-10-25 (CDMX) / 2026-10-26 UTC. **Research-only conformance evidence.**
**Exact baseline:** `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; shipped v0.30.0, revision 24. No on-disk revision, test threshold, benchmark, or release changes authorized.

## Question and baseline
`docs/HARDENING.md` identifies an independently frozen *committed transaction generations* fixture as a missing conformance court. Existing `append_*` tests derived from Writer execution cannot independently establish Reader semantics: the Writer and Reader may agree on the same bug. The canonical Reader's `_latest_generation` scans signed commit footers and `_index_from_footer` replays delta operations over a base checkpoint. A stable byte-for-byte fixture independent of Builder/Writer can attest intended generation selection and fallback. Check open PRs before implementation; journal implementation owners remain untouched.

## Falsifiable hypotheses
- **H1:** A hand-assembled revision-24 initial checkpoint and one authenticated delta commit are parsed by the shipping Python Reader without invoking Builder or Writer. The *latest* committed logical tree and exact byte slices match independently fixed expectations.
- **H2:** A byte-identical committed archive with an appended **incomplete** or **invalid** attempted newer tail still opens the last fully authenticated generation and returns the same tree and content. A merely present magic string must not become a commit.
- **H3:** The physical archive bytes and their hashes remain frozen in the repository; the test fails if a fixture is regenerated from the current implementation. A separate hand-decoder of structural framing verifies provenance/offsets and exact independent raw bytes.

## Strong simpler control
A single-index fixed RAW archive checks only codec/header correctness; it is insufficient to prove journal replay or latest-valid-commit fallback. Ordinary Writer-built append tests remain regression evidence but not independent conformance.

## Cost / decision
The smallest honest evidence is a static base64 vector with explicit SHA-256, expected full member bytes, expected names and authenticated generation hashes, consumed by a tiny Python test. Avoid architecture changes and any native support claim. If current code cannot consume the hand-built vector, preserve the genuine failure before deciding whether the mistake is the vector, misunderstood format law, or a Reader product gap. No performance, native, platform, or release credit from this experiment.

## Scope and concurrency
Only new fixture/test/docs files may be written on this independent branch; do not touch another owner's Reader/Writer/Discovery Engine/STATE. Native journal owner PRs (#346/#358/#364) and Reader security compositions remain separate. This question is whether a *fixed independent oracle* exists and passes, not whether those implementations should be merged. No duplication of a specific existing journal-golden PR was found in initial PR search; recheck before late shared writes.

## Decision condition
H1/H2 validated only after running actual installed `CMPCT` against the exact frozen bytes. Passing an independent Python framing parser alone is lower-rung evidence, not product evidence. Preserve negative evidence and never weaken the test to force a green CI.
