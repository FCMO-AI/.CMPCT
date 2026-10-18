# v0.31 bounded strong verification — branch evidence and promotion debt

**Date:** 2026-10-18 (UTC). **Status:** experimental branch; not canonical product, release or CI proof. This note records a decision boundary, not a second project-state database.

## Source and ownership

- Base owner: `agent/phased1-v031-pack-physical-sha-integrity@37ad27cb4a5808666935dec14a491d934e665d97`.
- Candidate branch: `agent/phased2-v031-bounded-strong-verify-20261018`.
- Exact candidate Reader Git blob: `426f36cd9048e79007778e2413e9c4c4f2baca83`. Changes are confined to `CMPCT.verify()`; revision-24 grammar/encoding is unchanged.
- The source blob exactly matches the independently tested candidate of the prior bounded chunk/CDC local research court. Recheck current branch HEAD and CI when interpreting this note; neither is frozen by prose.

## Falsifier / mechanism

Prior strong verification authenticates whole physical objects but then calls `read()` for all logical files. A valid >4-GiB sparse/chunked/CDС logical file cannot be verified below a 512-MiB address-space cap, although a 1-MiB reusable physical owner suffices to represent it. `read_range()` can also diverge from `read()` when CDC declared chunk lengths disagree with authenticated physical lengths; mere file-level SHA does not prove chunk geometry.

Candidate verifies RAW record SHA-256/CRC32 by mapped 1-MiB windows and hashes sparse holes, `S_CHUNKS`, `S_CDC`, and hardlink owners incrementally with independently committed logical SHA-256. It refuses mismatched CDC chunk lengths, bool-as-int wire identities, missing logical commitments and malformed reference bounds.

Strong simpler control: `preflight_archive()` rejects contradictory CDC geometry but does not replace cryptographic physical+logical verification or solve full-member materialization. An oracle given the expected hash without processing logical bytes receives no credit.

## Local experimental evidence, not release proof

On 2026-10-18, the candidate SHA-identical to this branch passed 20/20 focused Builder-independent tests and 36/36 inherited hostile sparse/physical controls. Under Linux `RLIMIT_AS=512 MiB`, exact SHA verification of separate valid 4,296,015,872-B `S_CHUNKS` and `S_CDC` members passed with about 100 MiB peak RSS (2.57/2.64 s in a combined local Reader integration), while the previous materializing verifier failed at this limit. Sparse and chunk/CDC hardlink controls also passed.

Eight fresh-process ABBA samples per arm on **the exact owner/candidate Reader blobs** at 32-MiB logical size, 2-GiB AS cap:

| Map | Owner median wall | Candidate median wall | Owner median RSS | Candidate median RSS |
| --- | ---: | ---: | ---: | ---: |
| S_CHUNKS | 65.393 ms | 33.556 ms | 137,490 KiB | 101,242 KiB |
| S_CDC | 58.894 ms | 33.449 ms | 137,170 KiB | 101,340 KiB |

This is local *verify* performance, including fresh process/import, not end-to-end archive create/extract throughput, a statistical product-speed guarantee, or general compression advantage. Raw results and reproducible >4-GiB generation must be regenerated through the tests and `tools/cmpct_bounded_verify_court.py`; local run receipts do not substitute for committed hosted evidence.

A separately constructed local ZIP64/POSIX + bounded-verification three-way merge had **zero textual conflicts** and passed 39 focused tests, 500/500 extraction decisions (350 rejects, with premature destination creation reduced from 350 to zero), 36 inherited hostile verification cases, 10 ZIP export decisions and independent ZIP reconstruction of 65,537 entries with a >4-GiB file. **That merged Reader is not committed on this branch.** Do not transfer its cross-lane credit to product or current CI.

## Negative and unmeasured boundaries

- A single huge compressed blob still goes through materializing `_blob()`; no universal bounded-memory claim.
- `S_PACK` lacks a separately authenticated digest per logical slice in some r24 archives; the inherited semantics remain.
- Full `S_VZIP` streaming, native parity, Windows, ABI, crash recovery, concurrent archive mutation, general hostile resource limits, release parity and complete competitor/full-product benchmarks are **not established here**.
- Exact-head hosted CI was absent on initial branch-push inspection. Re-query; never infer green from clean local tests.
- PR creation was blocked by platform safety on 2026-10-18; no review/merge/promotion follows from having commits on this branch.

## Next decision

First obtain an authorized stacked review/PR and exact-head Python/native/security/release gates for this source. Reconcile with the physical-SHA owner, ZIP64/POSIX work and newer branches instead of reopening duplicate narrow implementations. A failed performance, portability or integrity gate is promotion debt, not reason to weaken it. Preserve the test fixtures and 4-GiB resource harness as a cheap decisive future control.
