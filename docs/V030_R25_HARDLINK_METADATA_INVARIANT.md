# v0.30 r25 hardlink inode-metadata invariant

Status: D5 Forge / Custody hardening record. This note changes no benchmark, promotion threshold, or release claim.

## Defect

Both canonical filesystem-v1 and implicit-v4 carry metadata for every public path. A hardlink alias and its regular-file owner are two names for one inode, so mode, uid, gid, mtime and xattrs are inode-owned state and cannot truthfully diverge between those names.

The Python filesystem-v1 decoder and implicit-v4 expander previously accepted an authenticated control that declared contradictory metadata for a hardlink alias and its owner. Materialization creates the hardlink first and then applies metadata by path; the later write therefore mutates the shared inode and silently makes one of the authenticated declarations false. The old builder-independent canonical and implicit conformance fixtures accidentally encoded this impossible state (different hardlink mtime/xattrs).

## Repair

The semantic owner now fails closed when hardlink metadata differs from the referenced regular owner. The implicit-v4 expansion applies the same invariant. Both independent conformance generators now emit physically realizable owner/alias metadata, and their committed vectors are regenerated rather than weakening reproducibility checks.

The invariant is structural and content-independent: it follows from hardlink inode semantics and does not inspect benchmark identities, paths, hashes, or workload names.

## Custody boundary

This repair is correctness/recovery evidence only. Changes in conformance-vector archive size are fixture changes and grant no compression, runtime, competitor, or release credit.

Shared-native malformed-control rejection is still a required parity boundary until the Rust semantic owner rejects the same contradiction and an exact-head native authority receipt proves it. Hosted Android and other exact-fingerprint release receipts must be regenerated as required by the release authority; physical ARM64 remains separately fail-closed where repository law requires it.

## Forge decision

Diagnosis: D5 productization/correctness parity. Intervention: lowest-sufficient fail-closed semantic validation; no information-ontology change. Decision: **PROMOTE_NEXT_PREREQUISITE** — carry the invariant through shared native parsing, hostile tests, platform parity and exact release authority before any v0.30 promotion.
