# O214 preregistration — extend same-effective-index admission to S_CDC descriptors

Date (UTC): 2026-10-27. **This document is committed before code or a new experiment.**

## Exact baseline and ownership
- Released v0.30.0 / on-disk revision-24 unchanged.
- Stack on O212 #560 exact source `3249a7d6d09a9890cfa65b03e239a7973bf92614`, Reader blob `ee598eec46531c4da44d90d37b67f783b0ab3299`; O212 already calls existing strict `_validate_storage` for S_SPARSE on the effective index before mmap. Do not change O212 owner branch.
- Independent O201 research #534, Linux/macOS hosted run #40385117270: authentic *but root-v omitted* CBC/S_CDC fixture produced full read/verify success, wrong late range for descriptor lengths 1 and 2, and extraction rejection. Windows positive extraction was blocked independently by unavailable `os.fchmod` (J24W02 #536). O201 is not product promotion evidence; this study will independently authenticate root `v:24` to avoid the O198/O202 provenance confounder.
- Existing `cmpct.validation._validate_storage` checks S_CDC descriptor length equal to referenced blob logical size and sum to file size. This is a sibling representation contract, NOT a rerun of O212 sparse.
- O213 #563 owns genuine full 4GiB sparse ZIP64 post-O212 evidence; do not duplicate it. J24W02 owns Windows chunked extraction portability; do not change fchmod.

## Primary question and falsifiable mechanism
Will applying the **same strict existing geometry validator to S_CDC** during O212's *existing* effective-index member scan reject independently authenticated malformed descriptor sizes **before** the ordinary Reader can emit silently inconsistent `read_range()` data, while preserving valid CDC reconstruction and untouched sparse behavior on three hosts?

Predicted result:
1. On O212 baseline a root-v:24 checksum-coherent CDC file `ABCD` with descriptor 1/2 can still produce full read `ABCD` and wrong late `read_range(2,2)` empty; root-v:24 positive descriptor 4 remains exact.
2. On narrow candidate, valid single- and multi-blob CDC (including repeated refs) passes `verify/read/read_range` and POSIX extraction; malformed declared lengths 1,2,5/zero/bool/negative, wrong final sum and invalid references raise the existing `ValidationError` during `CMPCT(path)` *before mmap*.
3. Candidate must leave S_SPARSE O212 cases unchanged; archive files must be SHA-identical before/after attempts.
4. Rejected descriptors do not cause extra pathname opens or a second separately loaded index; validation uses the already admitted effective `self.index`.

Disproof: a positive valid-CDC control fails; any tested malformed descriptor is accepted; a wrong-byte result is returned; any SHA/physical source changes; any root-v confounder; valid existing S_SPARSE regression; CI source identity ambiguity. A Windows valid extraction failure due to independently owned `os.fchmod` is recorded separately and must not be mislabeled CDC geometry regression.

## Competing approaches and BONK
- Wait for O201 author: no open CDC admission implementation PR found at orientation (search included CDC geometry and S_CDC; existing branches predating O201 had unchanged Reader blob); an independently stacked sibling owner is low-regret but must notify #560/#534.
- Separate `preflight_archive(path)` + reopen: rejected (O208 inode identity gap, duplicated I/O).
- New CDC validation loop: rejected (strict `_validate_storage` is already normative and O212 uses it).
- Validate every S_* at open: might be more complete but broadens compatibility and cost; keep one sibling tag narrow.
- Change `read_range` to trust actual blob size: would paper over malformed metadata and keep native/Python format disagreement.
- Chosen: extend the existing conditional from sparse only to `S_SPARSE, S_CDC`, no new parser, format or resource policy.

## Evidence ladder / scope
1. Inspect historical O201 source/hosted logs and current O212 Reader/validator identities (done before prereg).
2. Add root-versioned signed r24 CDC controls with RAW blob CRC/SHA, full index SHA, latest-index footer and strong logical SHA, preflight comparator and complete expected bytes.
3. Test ordinary installed candidate on Linux/macOS/Windows, exact commit/source identities, and preserve positive/negative raw JSON receipts; no monkeypatch of Reader.
4. Run inherited O212 focused tests and available general CI; record substantive exact HEAD separately from frozen fingerprint/CI routing failures.
5. Measure open CPU/RSS only when additional validators' source-native cost can be isolated; O205/O213 numbers are inherited and cannot be reused as O214 measured product credit.

No archive-size claim, no universal resource bound or same-inode immutability guarantee. No release, format or benchmark change. Publish only evidence-backed result; if CDC turns out already fixed upstream, retire the patch and preserve the negative finding. Preserve append-only prereg/outcome history; Discovery STATE is not a lock and should only change if broader priority truth changes.
