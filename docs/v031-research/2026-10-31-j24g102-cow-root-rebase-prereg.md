# J24G102 — Immutable COW block ownership under authentic r24 checkpoint rebase (prospective O0)

Date: 2026-10-31 UTC. Scientific preregistration **before implementing/running J24G102**. Research only; NOT a released CMPCT Reader, Writer, filesystem or wire-format change.

## Authority and collision avoidance

Published main is v0.30.0 / revision 24 at `80c358f8824ec1b20d349c92ed94c898090969b0`. Scientific parent #876 HEAD `a516199d8776115f56a3dad82c1071973a0514ec`; #869 owns trusted-head/tail families; #574 owns discovery state. J24G101 showed ~1.98–1.99x disk-block retention when a physical root is copied while an older reader retains its inode. That is an *implementation-specific* cost, not a lower bound on identical physical content. J24G99's base+rolling-tail is the strong simpler control on append-only updates and must not be ignored. This independent O0 tests a **different physical organization**, not another footers-only hash or root-lock policy. Do not modify those owners' code, state or CI.

## One falsifiable question

If an r24 archive that underwent **63 genuine Writer DELETEs** is rewritten into a single clean latest-index checkpoint, could a future copy-on-write **content-addressed fixed-block physical owner** retain the pre-rebase and post-rebase complete exact byte images without copying the almost-unchanged original physical blob area? Fully charge block identities, physical payloads and two independently pinned root manifests; measure scope and overhead. This is a block-addressed representation O0, not a claim that ordinary ext4, NTFS, APFS, reflinks or CMPCT can use this automatically.

## Exact sources and construction

Four source families from independent #853/J24G91 original Github hosted ZIPs: Ubuntu/Windows-created 4,096- and 8,192-member physical A (63 DELETEs) and B (same index + terminal zero-op signed checkpoint); exact provider ZIP SHA, source checkout SHA and each physical archive SHA must be checked. Construct the **old** image from actual initial checkpoint prefix of A. Construct the **new** clean-checkpoint image from the exact unchanged initial physical body plus B's exact final compressed checkpoint payload and a footer with predecessor zero. Do not invent or recompress any logical source row. A parser independent of CMPCT must decode and hash both signed indexes and independently replay the 63 DELETE payloads to verify the resulting new index equals the actual B latest index. Confirm physical CMA4 records unchanged. New image is a hypothetical repacked r24 snapshot: no installed Reader verification or crash-safe product rebase is claimed unless actually run.

## Precommitted decision tests

- H1 (storage headroom): for each of all four physical pairs, fixed 4-KiB, and independently 16-KiB, blocks with SHA-256 keys, **44 bytes charged per distinct stored block** for digest+offset+length, plus **32 bytes per referenced block per manifest**, plus 64 bytes per manifest, must produce live two-version physical storage <= **1.20x the larger single image**. If either size fails on any case, reject *universal H1* and preserve scoped positives.
- H2 (exactness): materialize each old and new image solely from block digest refs; require byte-identical reconstruction of both originals, SHA-256 equality, no unaccounted block collisions/duplicates; reject mutation of any block or root reference. One mismatch kills the scientific credit.
- H3 (generality screen): also test nonprefix physical 4-KiB rotation/1-byte insertion and random/incompressible control on the *same source-sized images*, without pretending these are genuine CMPCT archive semantics. If COW loses materially there, restrict to exact physical sharing rather than general content deduplication.
- H4 (stronger simpler controls): compare fully charged live bytes to (i) direct 2x full-copy two-version storage and (ii) J24G99's true base+rolling-tail approach, strictly acknowledging it solves a different **no-rebase** problem. If the simpler no-rebase option remains superior on delete-only update histories, never promote this O0 as the default.

## Anti-self-deception boundaries

Charge two manifests, any unchanged blocks as one physical owner (not as two zero-cost payloads), block store lookup records and nontrivial hash metadata. Separate logical archive bytes, physical allocated block counters, modeled transferred bytes, Python work and process startup; no optimistic inference about extent-level reflinks or kernel disk writes. File source identity, signed footer semantics, valid fsmeta, logical SHA and recovery remain independent obligations. This model has no authenticated external head and no cross-epoch CAS, garbage collection, malicious same-UID source safety, power failure, filesystem portability, Reader API or released format support. O0 data cannot be given product/release credit.

## Cheapest instrument, falsifier and handoff

One stdlib+system-libzstd+msgpack Python script, full source ZIP/HEAD/digest checks and repeatable JSON with raw per-case block counts and SHA/length. One independent differently rooted read-only referee of output receipts. Run locally on original provider ZIPs first; GitHub Actions is an optional subsequent independent host layer only if the O0 decision remains materially open. If H1 passes but H3 fails, preserve the exact sharing domain; if H1 fails relative to J24G99/no-rebase or overhead erases wins, retire the general COW claim rather than adjust thresholds. Do not update `docs/discovery/STATE.json` on this ownership branch.
