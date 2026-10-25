# O81 — VZIP full-read CRC32/SHA-256 distinction (prospective preregistration)

Date: 2026-10-25 UTC. Status: PREREGISTERED, NO RESULT. Research only.

## Source and authority
Canonical released v0.30.0/r24 unchanged. Exact test parent `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Original `src/cmpct/reader.py` Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`; `codec.py` blob `29526db4203723d83523fc95d074c346b63d7587`. No released, frozen, evaluator or source changes authorized.

## One scientific question
Does regular `CMPCT.read(name)` for an authenticated `S_VZIP` row enforce that the **reconstructed ZIP's SHA-256 matches the indexed original**, as the current Reader comment claims? A code inspection suggests `rebuild_vzip` enforces reconstructed size and CRC32, but not `want_sha`, while `CMPCT.read` returns early for VZIP without comparing row[5]. Explicit `CMPCT.verify()` performs the SHA check. The next control must prove or falsify this on a real installed Reader, not merely infer it from code.

## Mechanism and stronger controls
Create two valid same-length ZIPs with different SHA-256 but **identical CRC32 over the complete original ZIP bytes** by changing bytes in the trailing ZIP comment and applying a 32-variable GF(2) correction to four trailing-comment bytes. Independently check that both archives parse and reproduce identical member payloads. Build a genuine CMPCT revision-24 VZIP archive from the first ZIP. After baseline `read` and `verify` PASS, inject the corresponding CRC-preserving changed VZIP skeleton bytes at the decoded-content boundary (`_blob`), retaining every other recipe/index/source structure unchanged. This is explicitly a **decoded-blob oracle**, not yet a physical-archive tamper claim. Validate that the injection keeps the exact skeleton size and CRC32 unchanged and that reconstructed original ZIP CRC32 remains unchanged while SHA changes.

Stronger direct physical artifact test, if feasible at low cost: if the skeleton blob is stored as RAW, mutate only those physical bytes on an independent copied CMPCT artifact without editing the authenticated index/header; same checksum means `_blob` CRC remains unchanged. The physical result, if successfully constructed, receives separate higher-tier evidence.

Control A: unchanged archive, original `read` exact and `verify` exact. Control B: corrupting a VZIP segment without a balanced CRC correction is rejected at the existing CRC gate. Control C: corrected collision must be recognized by independent `hashlib.sha256` and by product `verify()`; never weaken the comparator. Control D: source SHA/file identities and exact source ZIP member bytes are recorded.

## Prediction and disproof
Prediction: low-rung controlled decoded-skeleton substitution with CRC32 equality passes `read()` and fails `verify()` on an exact installed Reader. If `read()` itself rejects the mutation, the suspected gap is falsified. If no real VZIP or clean baseline cannot be produced, mark instrument invalid rather than calling it a product defect. The physical tamper escalation is optional and gets no credit unless independently validated. If `read` appears to accept mutated bytes only under a monkeypatch that breaks an invariant impossible for a physical archive, narrow to oracle evidence rather than a source-code vulnerability claim.

## Competing explanations and product economics
A deliberate contract distinction between fast CRC-protected `read` and whole-archive SHA-protected `verify` may explain the apparent mismatch; check documentation before proposing any API/semantic change. A naive SHA on every VZIP `read` could increase CPU for repeated/full ZIP workloads, and therefore requires a separate same-input full-product performance gate before promotion. Alternatives: leave fast `read` documented CRC-tier; add explicit opt-in authenticated `read_verified`; or enforce SHA-by-default with measured cost. No product choice is preauthorized by an oracle.

## Decision and handoff
A decisive clean/hostile pair changes the integrity-assurance map and may justify owner review of a narrow Reader API change. Preserve all negatives and actual CI status. Do not merge, release, bump version/format, or alter frozen thresholds. O79 PR #436 currently owns **selective** retained VZIP SHA-oracle research; O81 is independently scoped to the **full read** path and shall not duplicate the O79 implementation.
