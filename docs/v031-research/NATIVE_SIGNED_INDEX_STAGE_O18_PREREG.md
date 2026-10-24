# O18 — Public-C authenticated stage-before-publication: preregistration

Date: 2026-10-24 UTC. **FROZEN BEFORE IMPLEMENTATION / RESULTS.** Research-only, not product or release authority.

## Current authority and independently held inputs
Canonical CMPCT v0.30.0 is released, format revision 24, v0.31 unmerged. Parent PR #359 / exact source `c2b61c5290382c3df5eb92c6381b83b1ba0e02d0` contains a signed-index logical SHA query, terminal hardlink owner query and authenticated S_PACK batch. PR #351 separately owns the Linux flat-tree extractor; we DO NOT modify its sources. PR #340's O12 proved that direct RAW often lacks a logical row digest. No format, Reader, Builder, Writer, ABI, benchmark, policy or release mutation is authorized in this experiment.

## Primary scientific question and prediction
Can a deliberately scoped native C consumer use only the existing public C ABI and a 64-KiB caller buffer to reconstruct a *real Builder-produced CDC file* in a **private staging inode**, compare SHA-256 of the exact staged output to the existing authenticated-index logical SHA, and create the visible final name **only after equality**, while leaving no published file on a genuine contradictory signed-index commitment?

Predict: (A) ordinary CDC succeeds, staged and published contents exactly match the original; (B) a separately reconstructed/resealed r24 archive with **unchanged physical bytes** but a wrong authenticated index logical SHA opens and streams, yet fails at the digest barrier with *no final file and no stage file*; (C) a genuine Builder direct RAW entry without the row SHA rejects *before writing*; (D) pre-existing destination symlink/root contents reject before publication, without modifying external canary. The native consumer never trusts Python's index parser for these decisions.

## Stronger simpler controls and alternative explanations
Reference Python Reader + SHA-256 of original is the independent content oracle; merely writing the CDC bytes and hashing after publication is simpler but violates fail-closed publication. A native range-read error or Rust internal hash rejection rather than an O18 digest mismatch may explain a failed negative; preserve exact exit cause and narrow scope if so. Another simpler control is eager buffering of the entire file; its RSS bound is worse by design, but the court must **not** claim whole-process RSS without measurement.

## Safeguards / resource law
- Linux/POSIX only, single regular file with safe flat name, empty private directory. O_EXCL/O_NOFOLLOW stage and linkat no-replace final leaf anchored by open directory fd. File output <=4 MiB. Caller scratch <=64 KiB, EVP SHA-256 state, constant extra content state; no complete output buffering in the consumer.
- Refuse entries lacking an existing row SHA; NEVER pretend direct RAW is fully verified using a physical blob header or source-independent data.
- On digest mismatch, delete the private staging leaf before reporting failure. POSIX process interruption or adversarial concurrent mutation is NOT covered; fsync semantics, rollback of full filesystem, symlinks/hardlinks, platform parity, XATTR/ACL, source signer trust are NOT claimed.
- Negative r24 index constructed independently from actual Builder output, retains records byte-for-byte and reseals BOTH matching compressed indexes and footer. Confirm valid SHA and physical payload identity, fail closed on unintended format error.

## Decisive tests and kill/narrow criteria
Require actual source SHA on runner, compiled unchanged Rust native reader/header, OpenSSL EVP streaming implementation compiled -Wall -Wextra -Werror, real CDC `S_CDC`, row SHA present and independent source match, published file byte/SHA match, optional source size/peak RSS and complete CMPCT bytes recorded. Reject if any wrong-digest published leaf/staging survives, any RAW without row SHA can publish, any canary changed, or a native read fails for a nonintegrity reason. If C/ABI invalid, classify infrastructure/test defect; do not report product gain.

## Evidence, portability and release boundaries
A dedicated PR-triggered GitHub Actions run will record exact HEAD, case-level stdout/stderr/exit codes, source/corpus SHA, complete archive bytes, and an independent Python oracle. No historical comparator, official ABBA, memory ceiling of Rust engine, portable publication, crash safety, generic archive extraction, external-signature authenticity or release credit is earned. This is an intermediate research rung intended to decide whether signed-row authenticated CDC staging is a viable ingredient of the product extractor, **not** to justify adding more bespoke ABI functions.

## Concurrency / claim and counterfactual
Distinct mutation surface from #351's flat POSIX inode extractor and #359's Rust ABI, which are treated as read-only ownership. No shared `docs/discovery/STATE.json` edit; #240 owns cache reconciliation. Inspect fresh competing PRs before late writes. A cheaper early discriminator is merely query SHA applicability on the chosen CDC/RAW members; if absent, kill without implementing staging. Policy change is NOT preregistered or presumed.

**Pre-result status:** unmeasured.