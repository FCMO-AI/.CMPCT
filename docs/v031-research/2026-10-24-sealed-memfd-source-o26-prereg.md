# O26 — sealed Linux memory snapshot preregistration

Date: 2026-10-24 UTC. Research only; preserve v0.30.0 and r24 semantics.

## Source
Parent #377 commit 73120e0fd4ac4d01fc2526f3fb59b6ce30417d4e. Independent adjacent experiment; no product or shared discovery-state writes. O23 #376 documented post-verification archive changes; O24 #377 established the correctness and cost of full private disk snapshot. O19b showed an anonymous temporary file alone does not prevent other same-user writes.

## Question
Can copying a complete CMPCT archive to a sealed Linux memfd, opened read-only through its proc descriptor, bind the bytes read by the existing Reader during verify and extract, including when the original archive changes after copying?

## Prediction and controls
Use original O23/O24 authentic r24 fixtures: direct RAW and compressed PACK, 128-byte and 4-MiB logical members. Copy in bounded chunks and apply write/grow/shrink/final seals. Confirm copied archive digest and seals; attempt ordinary same-user writes to the sealed snapshot; change the original source in place after snapshot; verify snapshot, extract and hash outputs independently. A fresh Reader of the changed original must reject its stale physical SHA. A later snapshot of changed source must also reject. Include the original private disk snapshot as simpler baseline. Repeat fresh-process A/B timings for full copy+verification+extraction with wall, CPU, RSS and number of copied bytes. Source code, source SHA and unmodified validators are required.

## Disproof and limits
Fail the claim for an allowed write to a sealed snapshot, any output mismatch, Reader inability to open descriptor paths, or acceptance of a modified original under strong verification. Unsupported Linux features are inconclusive, not success. This does not guarantee consistency during copying, secure output publication, protection against process-control privileges, signed provenance, bounded global memory or cross-platform support. The memfd may consume physical memory comparable to the full archive; charged cost must include it even if process RSS does not.

## Promotion
No format, product, release, validator, threshold, benchmark, or shared-state changes. Preserve all observations, including losses, and do not infer release credit. Reconcile concurrency and exact CI head at handoff.
