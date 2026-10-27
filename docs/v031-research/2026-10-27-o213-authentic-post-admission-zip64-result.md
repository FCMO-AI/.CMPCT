# O213 — genuine 4GiB ZIP64 after same-index sparse admission: product-composition result

**Scope:** independent exact-source v0.31 research against unmerged O212 Reader candidate; **not a canonical release**, not a new codec, and not a format change. **Evidence UTC boundary:** 2026-10-27. Preregistration committed first as `b75c10889934d669fc258a7a0ebd4885dcd01554` before the harness/workflow were written. Owner: O212 [PR #560](https://github.com/FCMO-AI/.CMPCT/pull/560); original O193 [PR #521](https://github.com/FCMO-AI/.CMPCT/pull/521). This research [PR #563](https://github.com/FCMO-AI/.CMPCT/pull/563) is stacked *without any new product-code edit*.

## Primary question and actual hosted source

Does O212 same-effective-index validation preserve full genuine Builder-generated 4 GiB sparse ZIP64, and what does that validation add to open cost? O212's previous source-exact 45 hosted tests measured signed-wire geometry and a synthetic 4 GiB selective-only exercise, not an actual Builder-produced full ZIP64 after the fix. O196/O197 were authentic on historical O193, not O212.

**Original substantive run:** [GitHub Actions #40440398139](https://github.com/FCMO-AI/.CMPCT/actions/runs/40440398139). **4/4 SUCCESS**: one Linux Builder producer + independent Ubuntu 24.04, macOS 14, Windows 2022 installed Readers. All ran exact source/head `0829f0b307915f1dce5d36c2872bd62a0153e3a5`; O212 unchanged Reader Git blob `ee598eec46531c4da44d90d37b67f783b0ab3299` versus O193 control blob `d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44`.

### Real producer (not simulated)

The existing O196 instrument was source-authentically adapted with attribution (original scientific blob `47f3ce4d4a1ef61f89748e3699e863e2ab104e0e`). An ordinary Linux sparse file of **4,294,967,296 logical bytes** held **4,096 independently addressed 4 KiB physical extents**, **16,777,216 physically allocated bytes**. A genuine CMPCT Builder created an authentic revision-24 S_SPARSE member and its source SHA. Archive size **533,464 B**; full archive SHA-256 `392fbe2ca03b9dea5daa25bc331ef70dee0e5c5422964e1b1b8d15c2a7827769`; exact logical SHA-256 `aa8eab1213de329104d81b6ea925c8455e55ccdd47b0457fa6abe9c1f65cf1c3`. Producer observed Builder wall 2.20597s, CPU 2.20579s; no cross-host size/create performance comparison is earned.

**Original archived evidence** under #40440398139:
- One immutable Linux producer archive/manifest [artifact #12705488294](https://github.com/FCMO-AI/.CMPCT/actions/runs/40440398139/artifacts/12705488294), GitHub artifact ZIP SHA-256 `4cb28db7ad2fb3cae0d264aa62a983a8186bca496261e9d6be824598b8ad2f33`.
- Producer receipt [#12705288401](https://github.com/FCMO-AI/.CMPCT/actions/runs/40440398139/artifacts/12705288401), SHA-256 `a4c0fccd8c4a13fbee8b7ff811b2cf6f942ba849701747c491a7ef5e20668f64`.
- Ubuntu [#12706261071](https://github.com/FCMO-AI/.CMPCT/actions/runs/40440398139/artifacts/12706261071), ZIP SHA-256 `857d87074c244021d5e3f263b4c3f639c45a3c0eacde0b531a8bac7a7eab9552`.
- macOS [#12705583344](https://github.com/FCMO-AI/.CMPCT/actions/runs/40440398139/artifacts/12705583344), ZIP SHA-256 `6c374f30dbd16860f5aae043d7fa49c7d6742c051d41f4a00bb0eea9b65f5b6f`.
- Windows [#12705458541](https://github.com/FCMO-AI/.CMPCT/actions/runs/40440398139/artifacts/12705458541), ZIP SHA-256 `fa535af7a14cf729050cf99907bfcc57d934fa9103d22d0078ff777baab7c967`.

### Decisive cross-host result

All three installed Readers received exact **byte-identical CMPCT source** and issued exactly **4,096 logical 1 MiB read_range requests**. Each exported a physical ZIP64 of **4,415,465 B**, SHA-256 `57d9048e5d593a61f2263c45e1c1054f8f80bbee9e9723ecfebc01f71441d406` (**ZIP files binary identical across three hosts for this input**). Each independent stdlib ZIP consumer verified **4 GiB complete logical SHA/CRC at EOF** and a differently rooted `struct` parser confirmed authentic ZIP64 local 64-bit size fields. The source CMPCT original SHA was unchanged after read/export.

| Installed receiver | Export wall | Export CPU | Observed peak RSS |
|---|---:|---:|---:|
| Ubuntu 24.04 | 23.892350 s | 23.890037 s | 69,959,680 B |
| macOS 14 | 23.816243 s | 23.390325 s | 140,656,640 B |
| Windows 2022 | 15.236165 s | 15.234375 s | 67,600,384 B |

These **non-equivalent hosted machines cannot establish relative OS speed**; process RSS is not a bound on physical decoder memory for arbitrary inputs. Linux independent Info-ZIP UnZip 6.00 `unzip -t` CRC PASS (19.35127 s), `unzip -p` full streamed 4,294,967,296 B SHA PASS (22.46743 s); fully external consumer, not CMPCT/stdlib's reader.

### Direct same-input admission economics (Ubuntu)

On the *same* original CMPCT input and runner, original O193 and O212 candidate installed separately with independently verified Reader Git blobs; eight paired ABBA independent-process alternations, import/setup excluded from timed constructor+4-byte range. Raw observations retained in Ubuntu receipt.

- Median baseline open + tiny read wall **3.4834175 ms**.
- Median O212 candidate wall **12.473311 ms**.
- Incremental median wall **8.9898935 ms**; median incremental CPU **8.9905425 ms**.
- Direct *paired* wall deltas span **8.803764–9.402887 ms**, paired median **9.035629 ms**.
- Observed process peak RSS median delta **0 KiB resolution** (does **not** prove zero extra allocations).
- Preregistered 30 ms incremental wall and 16 MiB observed RSS feasibility discriminators **MET** for this scenario.

The exercise does not include fresh-process startup in the timed constructor and is **not** a general cold-cache benchmark, universal corpus performance credit or a release gate. O205's prior separate-preflight ~17ms is inherited science, not an O213 measured value.

### Independent original-binary physical oracle and receipt audit

In addition to hosted source-created full SHA, the original CMPCT artifact was independently parsed in a separate local Python oracle **without importing the CMPCT package**. Standard binary `struct` parsed original r24 header, index and all physical blob headers; system libzstd C ABI decoded **4,096 physical Zstd blocks**; every physical CRC32 and SHA-256 was recomputed; signed sparse extent geometry was independently verified, with full **4,294,967,296 B logical SHA-256** reconstructed by streaming exactly the 16 MiB physical data plus zero hole ranges. This produced the same logical SHA `aa8e...` and **CRC32 2222394619**, independently matching the actual Ubuntu/macOS/Windows ZIP receipts. Decoded index **101,348 B**, physical record span **479,232 B**, one S_SPARSE member/4096 extents, 4096 physical Zstd blobs. Oracle result: `PASS_INDEPENDENT_4096_PHYSICAL_BLOB_INTEGRITY_AND_FULL_4GIB_LOGICAL_SHA`.

A separate independent five-artifact ZIP/receipt auditor recomputed the GitHub artifact SHA-256, ZIP CRC, all source/host/file hashes, ZIP64 metadata, output byte identity, full SHA, Info-ZIP, and all 16 raw ABBA observations, including median values; result `PASS_SOURCE_EXACT_SCOPED_COMPOSITION`. Artifacts themselves remain on the official Actions run and are not replaced with hand-written status labels.

## Negative/ambiguity preservation

The result closes the **specific O212 authenticity + 4 GiB full ZIP64 composition gap** for this valid Builder-produced sparse representation, plus a bounded hosted admission-cost result. It **does not fix or prove** same-inode mutability/truncation protection (O208/O209), raw extraction publication race (#528), malicious physical resource policy, all filesystem semantics, complete official size/create matrix, general CI, or canonical release. No additional Reader implementation, no format/ABI/benchmark/evaluator/release-policy alteration. If the specialized science is green while inherited general CI is red, preserve both without reinterpretation.

## Decision and next handoff

**Scientific question: resolved positively for tested genuine 4GiB S_SPARSE + ZIP64 composition.** The guard's measured ~9ms admission increment is below the preregistered 30ms research viability discriminator; other workloads may differ. O212 owner #560 should use this independent positive as evidence for an integrative Reader review, reconcile #521 streaming parent and security-custody stacks before any merge, run inherited general/native/fuzz and same-source mutation guards, and keep release parity gates unchanged. No discovery-policy lesson requiring a normative change was earned. `docs/discovery/STATE.json` intentionally unchanged (stale cache, not lock).

This research file is added **after** the source-bound scientific execution; its HEAD necessarily differs from `0829f0...`. A new exact-final-head CI check is required before asserting the documentation HEAD itself passed; the immutable original source-exact experiment remains correctly attributed.
