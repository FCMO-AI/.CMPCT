# O198 — Authentic r24 sparse extent-length/read_range consistency falsifier (prospective)

Date: 2026-10-26 UTC. **Status: PREREGISTERED BEFORE instrument and result.**

## Authority, scope, claims
Released CMPCT v0.30.0, r24. Exact experimental Reader source O193 PR #521 at `392112ce859db5a7f85be593c82d1cabc1f5131f`; no product source, frozen benchmarks, format, validator, numeric release, or other agents' branches may be changed here. O194/#522 and O195/#524 established sorted-index guard requirements and measured metadata scan opportunity, but *not* whether the real Reader accepts a self-consistently checksummed index with a declared sparse extent length unequal to its referenced blob length. This new question is independent from bounded scan optimization and ZIP64 full-product throughput. Current #522 production owner remains O193; no duplicate patch.

## Single question / falsifiable mechanism
A sparse file index encodes `[off, ln, blob_ids]`. `CMPCT.read()` and `extractall()` traverse the blobs and write their decoded actual sizes without using `ln` as a bound, while `CMPCT.read_range()` first filters by `extent_end=off+ln`. Hypothesis: a **wire-real** revision-24 archive with authentic index SHA, blob header CRC/SHA, and whole-file SHA can have `ln < actual referenced blob bytes` and pass `verify()`, yield correct full `read()` and `extractall()`, but return incorrect bytes in a selective `read_range()` beyond its declared `ln`.

Build **two independent, fully serialized r24 files** with the exact canonical header+Zstd-MessagePack-index+RAW blob+tail-index+footer grammar, not a monkeypatched in-memory Reader:

- valid control: four-byte raw payload `ABCD`, row logical size 4, declared extent length 4; expect read/full verification/extraction/range all agree.
- semantic hostile: identical four-byte payload, same logical size, identical whole-file SHA, *only* declared extent length 1, and independently recomputed primary/tail index SHA+compressed bytes; predict `verify()==1`, `read()=='ABCD'`, extracted bytes `ABCD`, but `read_range(2,2)==b'\\x00\\x00'` rather than `b'CD'`.

All four bytes are public deterministic synthetic input. A separate independent Python SHA checks file bytes. Verify original source and installed package identities. Run identical court on Linux, macOS and Windows where infrastructure supports; no false universal claim from missing host evidence.

## Baseline, alternatives, and decision rules
Baseline is ordinary valid sparse grammar; the strongest simpler control is `ln==sum(blob sizes)`. Alternative explanations: real Reader rejects malformed extent at open; `verify()` independently enforces lengths; the serializer's footer rejected; or Reader range uses actual decoded spans and therefore agrees. If any occurs, classify **NOT_REPRODUCED** or **INCONCLUSIVE** rather than modify tests. A mismatch that survives an authentic installed Reader, positive control, full SHA, unchanged file content and separate range probe earns **REPRODUCED_SOURCE_CONTRACT_GAP**, research/safety evidence only. Do not label index "cryptographically signed by a trusted origin": its digest is an integrity check, and an author can create an internally self-consistent malformed archive. This is not a demonstrated remote exploit.

## Safety, product costs, and prospective correction hypotheses
A future fix should validate each sparse extent's declared `ln` against referenced decoded blob lengths, integer/offset bounds, sortedness/non-overlap or defined overlap law, before serving ranges or extracting; alternatively define and consistently enforce a different grammar. New eager validation costs open/list CPU on large extent tables; bound and charge that cost, and preserve old valid archives. No production implementation is authorized in this falsifier branch. The evaluator and the real inputs cannot be weakened. If the result is negative, retire the concern and return to the larger ZIP64 resource/safety frontier.

## Evidence ladder and handoff
Source derivation → authentic small wire file & verified installed Reader (cheapest decisive rung) → hostile/held-out near-boundary perturbation if decisive → independently scoped owner integration. Cross-platform runs leave complete raw JSON with repository HEAD and Reader blob, primary/tail SHA, original archive SHA and actual bytes/exception. Hosted workflow success denotes a correctly classified experiment, not product success. No projected total-product speed or archive-byte savings.
