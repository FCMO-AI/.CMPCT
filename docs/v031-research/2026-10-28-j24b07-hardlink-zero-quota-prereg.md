# J24B07 — nonnegative hardlink alias-size undercount against J24B06-R1 extraction quota

Date: 2026-10-28 UTC
Status: **FROZEN prospective scientific question, before implementation or measurement**. No product, merge, benchmark, release, version or format credit.

## Authority and claim coordination
Released source: `main@80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0 / on-disk revision 24). Exact experimental *product candidate* parent: [J24B06-R1 #690](https://github.com/FCMO-AI/.CMPCT/pull/690) `adcf38cb5be022567c1faf6538aefeef2f6b72de`; its current patch checks `type(row[4]) is int` and `row[4] >= 0` before accounting. J24B04 [#610](https://github.com/FCMO-AI/.CMPCT/pull/610) already proves signed K_HARDLINK alias-size inconsistencies under published Reader; J24B03 [#609](https://github.com/FCMO-AI/.CMPCT/pull/609) owns direct S_BLOB size consistency; J24B06 #688/#690 owns signed-negative quota cancellation. Do not duplicate any implementation owner or quietly extend #690.

## Primary scientific question
Can a **nonnegative, exact-integer** but falsely small K_HARDLINK `row[4]` pass the new #690 admission scan, causing `extractall(max_bytes=N)` to publish a logical tree whose two visible regular-file paths have combined sizes greater than N? This is a potential *remaining quota-contract hole*, not another proof of negative-size cancellation. Model a genuine first-party 8192-byte file plus a hardlink alias of the same owner. An authentic physical archive uses both lengths = 8192 and has a logical expansion sum of 16384. Modify only the alias size to 0 and 1 respectively, recompute complete main/tail index SHA-256 without altering physical blob bytes; on Windows, if Builder recorded the alias as independent K_FILE, explicitly convert that one row to a K_HARDLINK descriptor before the size mutation (distinct declared-portability boundary).

## Prediction before seeing results
1. Actual installed source for #690 accepts mutant 0 under `max_bytes=8192` and mutant 1 under `max_bytes=8193`; both produce two 8192-byte logical file paths containing the unchanged payload. Both mutants pass ordinary `read/verify`, which delegates hardlink aliases to their owner.
2. Untampered first-party archive refuses `max_bytes=8192`, and accepts `max_bytes=16384`.
3. Mutants refuse tighter `max_bytes=8191+declared_size`, proving the scan is active but trusts unauthenticated *semantic* size claims despite SHA-valid metadata.
4. The physical record region and all nonalias metadata are unchanged between control and mutants (except the explicitly declared Windows Builder exception). Independently parse wire indexes/footers and verify original SHA-256, data identity and undercount.
5. Ubuntu 24.04, macOS 14 and Windows 2022 actual installed-wheel courts should agree where OS file-hardlink support permits. Preserve per-host factual outcomes, including any skips/failures.

## Falsifier / kill conditions
Any nonnegative mutated alias rejected before publication by #690, a normal control failing, unequal output bytes, hardlink not actually materializing, physical source not preserved, independent referee failure, or divergent platform semantics narrows or kills the claim; no test weakening. A `SUCCESS` workflow only establishes a measured defect on candidate code, **not** a product improvement. If the candidate does allow publication, #690 cannot be claimed to provide a complete maximum *logical* expansion guard without an additional alias-owner consistency invariant. The narrower signed-negative fix may remain valid independently.

## Stronger control / alternatives / bounds
Source-level arithmetic already predicts undercount: fixed guard only checks int and sign. This cheap source inspection is not hosted proof of materialized filesystem behavior. Stronger durable controls: same-format Builder archive, exact bound, complete SHA-constrained two-index artifact, independent parser and three-host installed run. An O(1) per-hardlink owner-size equality proof with memoized ancestry is a possible future composition under #569/#610, *not* implemented here. A final decoded-byte-metering/staged publisher would catch other contradictory size geometries but is a substantially different owner. Hardlinks usually share physical inode bytes, so the claimed breach is **aggregate logical member sizes**, not >N unique disk blocks or CPU amplification.

## Scientific cost, evidence and release
Measure source SHA, physical sizes, extracted logical bytes, actual cap used, verify count, source/modified wire SHA, process elapsed for reproduction, and peer referee result. No compression or speed claim. No release gate, historical test, evaluation threshold, Reader code, Builder code, Writer code, public website, policy or shared Discovery STATE mutation. Keep PR in Draft. Discovery cache is stale and owned by #574; reference exact source and owner PRs instead.

## Counterfactual discriminator
If evidence confirms, the cheapest transferable precursor is checking whether every counter used in a resource budget has an independent relationship to actual reconstructible output; checking only numeric type/sign never establishes that relationship. Record this as a candidate research lesson, not policy law, until independently reproduced.
