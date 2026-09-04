# CMPCT v0.30 single-executor convergence model

This document is the active execution contract for completing CMPCT v0.30.

## Authority

`agent/v030-authoritative-integration` is the only active v0.30 engineering line. One executor owns implementation, evidence, reconciliation, release-lock closure, publication, and post-release verification end to end.

CI workflows, benchmark runners, and automation are execution/evidence infrastructure. They do not own tasks, make design decisions, waive gates, or substitute for engineering judgment.

## Mission

Finish v0.30 as one coherent release-quality system without duplicate promoted implementations, stale-branch overwrite, hidden regression debt, or benchmark claims borrowed from research artifacts that are not part of the exact release candidate.

Production remains v0.29.0 / r24 until the strict v0.30 release lock is satisfied on the exact frozen candidate.

## Work model

The task files under `docs/v030-coordination/tasks/` are a dependency-ordered checklist, not a labor scheduler. T00 through T04 are all owned by the same executor and may be interleaved when one task exposes a blocker in another.

- **T00 — reconciliation:** keep the authoritative line current with `main` and preserve every current-main hardening, CI, public-surface, and benchmark invariant.
- **T01 — native/portability:** close shared native r25 reader, recovery, ABI, ZIP/export, Android, and platform parity.
- **T02 — evidence/performance:** produce exact 15-workload, product-parity, runtime/RSS/selective-read, shared-build, CI-topology, and external-competitor evidence.
- **T03 — canonical productization:** finish one canonical r24/r25 API/reader/writer architecture with exact product-floor semantics and no process-global profile mutation.
- **T04 — release closure:** freeze source, bind final receipts to the exact fingerprint, satisfy the strict release lock, merge, tag, publish, and verify the live release.

The executor should work the highest-value blocking defect regardless of which task discovered it. A task becomes `DONE` only when its required implementation and durable evidence are present on the authoritative branch.

## Evidence hierarchy

Release authority, strongest to weakest:

1. durable benchmark/conformance record committed for the exact reconciled candidate;
2. successful CI artifact/run tied to that exact candidate fingerprint/SHA;
3. repeated controlled measurement with recorded environment and raw data;
4. focused unit/property/adversarial tests;
5. implementation or prose claims.

Historical green runs prove mechanisms, not the current release candidate.

## Frozen promotion invariants

The executor must not weaken these to make the release pass:

- exact repaired 15-workload accepted-v0.29 aggregate identity;
- at least **687,783 B** aggregate saving;
- at least **3 improved workloads**;
- **0 inherited archive-byte regressions**;
- genuine canonical r25 product bytes never larger than genuine canonical r24 bytes on the same original filesystem tree; exact ties keep r24;
- selected r25 per-member decoded-context amplification **<=8x**;
- max decode unit **<=8 MiB** and all existing hostile-input/resource bounds;
- exact fallback/tie semantics;
- create/extract/selective-read/RSS performance gates;
- native/shared-reader parity for every promoted representation;
- exact external competitor matrix with verified extraction semantics and fair losses preserved;
- version, public-surface, site-source, live-site, release-note, and release-lock gates.

## Implementation discipline

Before a material edit, establish the inherited behavior and the exact invariant being protected. Prefer fixing the mechanism rather than patching one fixture. Preserve comments and design footnotes; add concise nearby footnotes for non-obvious compatibility, safety, or measurement invariants.

Do not maintain competing promoted implementations for the same semantic responsibility. Research helpers may remain only when they are clearly non-canonical and still useful for ablation/history.

Do not use chat history as release authority. Any conclusion required to resume or verify v0.30 must be committed into this repository.

## Reconciliation

Only the authoritative branch is an active implementation line. Before final evidence, compare it with current `main` and resolve every overlapping semantic change explicitly. Never resolve promoted behavior with blind `ours`/`theirs` selection.

## Release procedure

1. Close T00–T03 implementation and evidence obligations on the authoritative branch.
2. Prepare canonical v0.30.0/r25 docs, release note, and site source from accepted durable facts.
3. Freeze the release-critical fingerprint with `python -m experiments.entropygraph_v030_release_lock_strict --print-fingerprint`.
4. Run every required final authority gate on that exact fingerprint and commit strict JSON evidence plus fingerprint-bound receipts.
5. Require `python -m experiments.entropygraph_v030_release_lock_strict` to report `UNLOCKED`.
6. Merge the exact candidate to `main`, create the v0.30.0 tag/release, deploy/verify the public site, and run post-release smoke against the released bytes/code.
7. Mark T04 `DONE` only after those irreversible actions and post-release checks succeed.

Footnote: single ownership removes coordination overhead; it does not reduce independent evidence requirements. CI, native implementations, stock archive tools, hostile fixtures, controlled benchmark runners, and live-site verification remain deliberately independent checks on the executor's conclusions.
