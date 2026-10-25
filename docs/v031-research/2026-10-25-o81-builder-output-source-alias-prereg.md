# O81 — Builder source/output identity boundary: preregistration

Date: 2026-10-25
Status: PREREGISTERED / NO PRODUCT CREDIT
Owner: agent/phased2-v031-o81-builder-output-source-alias-20261025
Canonical base: agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b
Format: revision 24; pre-1.0 version unchanged.

## Primary question

Can a successful Builder publication overwrite an actual source member by following a destination hardlink, or recursively ingest a previous archive when its output lives inside the source root? Does a bounded output/source disjointness preflight prevent both without modifying ordinary outside-root archives?

## Prospective mechanisms and predictions

* External hardlink: source root contains a regular file; the output path is outside the root but links to the same physical inode. The historical Builder scans the source, then opens the output using write/truncate and thereby clobbers the source member **even on success**. A reject-before-scan policy must preserve BOTH original names and bytes. This is distinct from O75's interrupted-write failure atomicity.
* In-root output: when output lives at or below the scanned root, a repeated build may capture its own previous archive as a logical member, making the source tree depend on the last output. The proposed candidate explicitly rejects this layout before doing work, rather than silently excluding a source member and falsely claiming a complete snapshot.
* A symlinked output path or parent that resolves inside the root should receive the same rejection.
* For an external output whose identity is independent of every source member, candidate and historical Builder should produce complete identical r24 archives, exact reconstruction and unchanged source contents.

## Stronger simpler control and causal alternatives

The O75 staged-replace Builder avoids truncating the old inode when successful, but changes symlink, hardlink, xattr and permission semantics (O78). This O81 policy is a logically orthogonal **admission** safety boundary and must not claim it replaces O75. Rejecting every existing external destination would also avert the hardlink problem but would unnecessarily forbid a standard safe rebuild; the narrow control is filesystem identity comparison against already-observed source inodes. Case equality and realpath containment are cheap early screening controls, not a race-free kernel capability model.

## Evidence and costs

1. Exact historical Builder negative with a real external hardlink and independent payload hash / inode check; no synthetic compressor.
2. Candidate fail-closed on that same fixture, plus lexical in-root and resolved symlink-root paths.
3. Same-input successful outside-root A/B whole-archive byte equality, Reader strong integrity/reconstruction and user source hash invariance.
4. Three-host installed-package court where possible; POSIX-only tests must be explicit skips elsewhere.
5. Count extra syscall and per-entry comparison work; full release CPU/wall/RSS/temporary-I/O gate remains unmeasured unless executed.

## Kill / narrow conditions

If the negative cannot be reproduced on original code, this is a rejected mechanism. If the candidate silently excludes source members, weakens exactness, modifies r24 bytes, blocks otherwise independent external output, or exports unacceptable scan cost, do not promote. If hardlink semantics differ by host, narrow to verified hosts; do not claim universal prevention. The preflight is not atomic source custody under adversarial concurrent rename/link changes, and no result may claim that.

## Concurrency and authority

Independent narrow source/output-identity boundary; do not overwrite O75/O78 physical-publication PRs, O80 source-fidelity union, or Discovery Engine shared state. Reconcile those owners before promotion. Negative/positive outcomes are append-only. No release or merge is authorized by this preregistration.
