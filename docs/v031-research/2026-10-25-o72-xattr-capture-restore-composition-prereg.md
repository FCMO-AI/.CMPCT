# O72 preregistration — one coherent xattr capture → authenticated archive → strict restore contract

Date: 2026-10-25 UTC. Status: prospectively frozen BEFORE implementation or result inspection.

## Authority and exact baseline

- Canonical development: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; released product v0.30.0; on-disk format revision 24.
- O65 Builder source: PR #420, `314c5bcc4d555e894cf5024918da3b5358e726b8`, Builder blob `7f222458adc1c4aae65fa24650a8fc0c7b0c1b18`. It rejects observed-but-unreadable xattrs while retaining explicit unsupported-enumerator and reproducible-mode policies.
- O69 Reader source: PR #425, `8fe424ac8575da10bf5ecfdb9660d4b5831f638b`. It adds opt-in `require_xattrs=True` and a Windows timestamp-restoration compatibility fix.
- This branch starts on O69. Neither owner PR is modified. No on-disk schema/version change is permitted.
- Discovery Engine and release gate remain unchanged; this is a distinct *cross-boundary composition* question, not a third isolated xattr-policy variant.

## Primary question

Can exact O65 source capture and exact O69 opt-in restore operate together as one coherent product flow, preserving regular-input complete archive bytes while refusing both classes of silent metadata loss (capture side and restore side)?

## Hypothesis and predicted observable

A minimal verbatim transplant of O65's `_capture_fs_meta` error classification onto the O69 Reader source will:

1. Produce an authenticated r24 archive containing binary xattr values; on a supporting Linux filesystem the Reader will apply those exact values in strict mode and an independent OS readback will agree.
2. Reject a listed-but-unreadable source xattr BEFORE publishing or clobbering an existing output archive, with the untouched sentinel output as observable.
3. Allow a genuine `ENOTSUP/EOPNOTSUPP/ENOSYS` enumerate failure to retain the existing no-xattr policy; `reproducible=True` still never probes xattrs.
4. Preserve opt-in Reader failure transparency: injected denial of `setxattr` raises with preserved cause, while default best-effort extraction still succeeds on the SAME archive and payload.
5. Preserve complete archive identity for an unchanged, source-exact ordinary tree compared to the O69 parent; no test may retrofit loss by mutating the workload.
6. Remain portable: each platform must run the injected xattr read/write negative courts against installed CMPCT; native xattr roundtrip is a Linux-only positive, not falsely counted on other hosts.

## Stronger simpler controls and disproof

- Strongest control: O69 Reader alone plus its own seven tests and O65 Builder alone plus its own tests. If these independent results already entail the combined property, O72 should remain a small compatibility court; **do not invent another xattr API or format**.
- Counter-hypothesis: integration is mechanically safe but a shared test fixture cannot preserve the actual POSIX xattr system call semantics; a green mock-only court must NOT receive physical reconstruction credit.
- Material falsifiers: Builder publishes a loss despite observed read failure; strict Reader reports success after injected target denial; any identical-input archive-byte discrepancy; missing/unchecked test on a host; unexpectedly changed default; Linux readback differs; any existing O69 tests regress; a candidate silently changes existing r24 grammar.
- If the simple exact transplant already passes a strong held-out court, stop this local family; promote only after separate full CI, economic gates and ownership review.
- If more than one surgical code hunk is required in the Builder beyond O65's proven policy, reframe and re-preregister rather than improvising.

## Evidence plan and cost

First compare parent/candidate Builder source fingerprint; then use actual CMPCT installed wheel or `pip install .` on Ubuntu/macOS/Windows. Run an isolated focused six-or-more-case test on real revision-24 archives and verify JUnit counts and skip identities. For baseline size control, execute both sources on the *same* input snapshot on the *same* host. Preserve exact raw logs and CI URLs. No economic/release credit without valid full-product ABBA: native build, archive bytes, create/extract wall+CPU/RSS, xattr/metadata semantics, exact historical comparator, all inherited gates.

## Concurrency and decision boundaries

Open PRs #420 and #425 own their original changes. #303/#305 own structural fsmeta preflight and Reader publication, and #259/#246 own inherited historical fingerprint failures. No shared owners' branch, frozen benchmark, release lock, Discovery Engine STATE or threshold is modified by O72. Any alternate branch now claiming this precise O65↔O69 union must be reconciled before late writes.

## Alternative actions PARETOBONKed

- VZIP throughput/information research: active #423/#424/#426/#427 and #418, overlapping owners; no duplicate.
- Historical fingerprint/root-release CI: #246/#259 and prospective custody owner already exist; no lock rewrite.
- Reopen O40 micro-PACK threshold: physically diagnosed, low product information gain; not chosen.
- This bounded O65↔O69 union: two proven cross-OS correctness changes with a previously unmeasured end-to-end property and low format risk. Productization question dominates the cost of another nearby speculative mechanism for this activation.

Decision credit is deliberately limited to demonstrated cases. Keep the branch draft and do not merge or release on focused results alone.
