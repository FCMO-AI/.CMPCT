# ONE-G0.2 growable direct canonical emitter — terminal gate result

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`
Frozen authority: `docs/one/evidence/ONE_G02_GROWABLE_DIRECT_CANONICAL_EMITTER_PREREG_2026-09-05.md`

## Exact CI receipt

- branch source: `8017e8c5f4d1bf616d0b1e971eae7523a979d5f9`
- pull-request merge test SHA / benchmark `EVIDENCE_HEAD`: `c25efec18f43ee414427dc34d5162c38b196eb04`
- workflow run: `33992597245`
- job: `101377359758` (`growable-direct-canonical-emitter`)
- conclusion: **failure by frozen performance gate**
- artifact: `9977073178`
- artifact ZIP SHA-256: `c822bd712cd363716503d09e7b728f216a599b80f65496e861c89751cae0f500`
- ONE semantic/hostile tests: **93 passed**
- semantic gates: **pass**
- benchmark timing order: alternating A/B-B/A, 51 paired rounds
- terminal frozen decision: **`retire_growable_direct_canonical_emitter`** under the preregistered broad-transfer promotion law

## Result

The candidate retained byte-for-byte canonical ONE0 wire, identical `WireStats`, ordinary decode compatibility and exact reconstruction on every row. The direct semantic suite covers all six ONE operations, canonical multi-root ordering, uvarint boundaries and the unchanged public validation boundary.

Most of the performance envelope strongly supports the small-allocation/copy hypothesis:

- productive median candidate / baseline: **0.3699278651x** (~63.01% lower prevalidated emission elapsed);
- productive rows <=0.95x: **20/21**;
- control size-class medians: **0.5396x–0.7086x**, all comfortably below the 1.03 ceiling;
- productive size-class medians excluding no row were 4 KiB **0.4256x**, 8 KiB **0.4090x**, 16 KiB **0.3851x**, 32 KiB **0.3698x**, 64 KiB **0.3602x**, 128 KiB **0.3551x**, 256 KiB **0.3699x**.

The frozen gate nevertheless fails because one productive row is a severe outlier:

- 256 KiB `shift_plus1`: baseline **40,614 ns**, candidate **111,798 ns**, ratio **2.752696x**;
- the same case at 128 KiB: **0.558059x**;
- at 64 KiB: **0.502265x**;
- the other 256 KiB productive cases remain fast: quarter-damaged **0.369928x**, fragmented/96 **0.354544x**;
- both 256 KiB literal controls also remain fast: fragmented/32 **0.686156x**, independent-random **0.731095x**.

The decisive control-heavy 256 KiB fragmented/96 Program improved from **6,832,044 ns to 2,422,260 ns**, while retaining the exact **297,504 B** wire, **264,876 B** Surprise and 2,736-node representation.

## Causal interpretation

The universal growable-direct emitter is **not promotable from this run** because the preregistered no-regression law is absolute and the 256 KiB exact-shift row exceeds it dramatically.

At the same time, the shape of the failure does not support simply declaring direct in-place control emission ineffective. Twenty of 21 productive rows and every control size class improve materially. The failure is isolated to a three-node, blob-heavy Program at one size boundary, while more complex Programs at the same byte size improve strongly. That is compatible with a Python `bytearray` growth/reallocation/copy discontinuity or another size-dependent runtime effect, but this is a hypothesis, not a diagnosis.

Do **not** rescue the candidate with a `size < 256 KiB` or workload-name dispatch. The next allowed experiment is a causal boundary diagnostic: sweep exact-shift/literal Programs around the discontinuity, record output/blob sizes and repeated paired timing, and compare one-pass growable direct emission against baseline plus causally different buffer-growth shapes. The question is whether a reproducible allocation/growth transition explains the isolated loss. If it does not, retire the direct emitter family more broadly.

## Claim boundary

This remains Python research-harness prevalidated-emission evidence only. No ONE representation, stored bytes, reader operation, validation/integrity contract, product writer path or format revision changes. No v0.29/v0.30 superiority authority is created.