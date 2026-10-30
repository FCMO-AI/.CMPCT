# J24G56b — nonzero footer flag/reserved bits can select a physically inadmissible generation

Date: 2026-10-30 UTC. **Confirmed negative research on experimental #789 lineage; NO product fix/merge/release.** Distinct prospective preregistration committed BEFORE the J24G56b tests at `e3607b276be6d3a2bae67a67aa976e8869d15d47`. Published v0.30.0/r24 not separately tested.

Exact test-and-referee HEAD: `2d413ff76f96e97ca97082b89d3b3096ecef8b4c`. Exact parent product #789: `83e9f2eb277f023186b646f667cd443b7108f268`.
Result-bearing [Actions run #40980303984](https://github.com/FCMO-AI/.CMPCT/actions/runs/40980303984) completed **Ubuntu 24.04 SUCCESS (7/7), macOS 14 SUCCESS (7/7), Windows 2022 SUCCESS (7/7)**. The independent Zstandard/MessagePack/stdhash referee ran without importing CMPCT. Every host preserved original byte specimens, source-equality receipts, JUnit and an independent physical proof record; all three independent referees reported **11/11 physical invalidity/tamper controls rejected** (33/33 combined).

## Prediction and observed behavior
`reader._decode_generation_payload` unpacks `<8sBBBBQQQ32s>`, but does not validate the packed `flags` and `reserved` footer bytes. `validation._decode_footer` explicitly rejects any nonzero value. The footer SHA-256 covers *decoded payload bytes*, not the unkeyed footer header: a single-byte nonzero mutation at offset `footer+10` (flags), separately `footer+11` (reserved), leaves a SHA-consistent otherwise ordinary signed-in-format `del a.bin` delta. **Reader selects the invalid newest footer, strong-verifies one surviving member, and reports success; preflight recovers the older valid footer and reports two members.** Both accept a genuinely valid delete and both recover an intentionally corrupted SHA footer. The independent referee proves the header mutation and physically authenticated payload are separable.

## Original provider evidence
- Ubuntu [artifact #12945165262](https://github.com/FCMO-AI/.CMPCT/actions/runs/40980303984/artifacts/12945165262), provider ZIP SHA-256 `cf3bc72278deed53a93745647791c7406909d40843070becc31aa8d6d9ea5afe`.
- macOS [artifact #12944965977](https://github.com/FCMO-AI/.CMPCT/actions/runs/40980303984/artifacts/12944965977), provider ZIP SHA-256 `b51b5fea8e799714f9c3b5231e27d3cc5d21ce27c5c5027dc2551494e77fda24`.
- Windows [artifact #12944339039](https://github.com/FCMO-AI/.CMPCT/actions/runs/40980303984/artifacts/12944339039), provider ZIP SHA-256 `d2d51b5f096b1bdc310dbf744f938be2186c4bc67591e5caa2d3de68670d20af`.

No second independent download/re-hash of ZIPs was performed; per-host referee is independent of Reader/preflight and validates original in-action sample bytes.

## Negative and disproof boundaries
No incorrect logical file bytes, keyed digital-signature fraud, published-wheel repro, native-Rust parity, complete operation families, fully bounded resource recovery, full-product RSS/CPU/throughput, power-loss, or external benchmark claims. The feature is header-admission/recovery consistency, **not archive authenticity of origin**. Both physical mutations are intentionally crafted; normal Writer emits zero flag/reserved bytes. Reader's identical recovered content on a different footer must never be confused with accepted malformed-footer semantics.

## Owner and next corrective action
Existing #789 is sole implementation owner of shared replay/Reader/preflight. The cheapest correction must make the Reader footer decoder reject unsupported kind/codec/flags/reserved and impossible backward-pointer geometry (the current preflight already checks those fields), while preserving legitimately committed r24 footer recovery. Acceptance requires both J24G56 unknown-op cases and new nonzero-header physical cases; do not weaken validator or suppress archived negative controls.

## Exact general CI for source head
The specialized 3-OS **research** court succeeded. The ordinary [CMPCT tests run #40980304142](https://github.com/FCMO-AI/.CMPCT/actions/runs/40980304142) finished **870 PASS / 2 SKIP / 5 FAIL**: four inherited historic v0.30 fingerprint/surface-epoch tests, plus one **expected obsolete J24G52 negative-reproduction predicate** that asserts an ordinal failure repaired in #789. This fifth is a historical negative oracle, not an unrelated new regression, but it remains a genuine red until source/historical test custody is legitimately reconciled; never delete/disable to claim green. Exact head Engineering Evidence, Version Discipline, Native Core, CI Topology, Fuzzing, R36 and Darwin fidelity all SUCCESS; administrative ZIP job SUCCESS does not constitute a new full-product performance benchmark.

The original J24G56a confirmed defect is [issue #792](https://github.com/FCMO-AI/.CMPCT/issues/792), [source head `01a5acc...`](https://github.com/FCMO-AI/.CMPCT/commit/01a5acc04ea376a3d38f345479630e11b42bf323) and [Actions #40979665726](https://github.com/FCMO-AI/.CMPCT/actions/runs/40979665726) (15/15 tests, 27/27 tamper controls). This b result is a distinct second parser-admission mismatch discovered afterward. The best prospective control is to compare accepted footer fields/opcode vocabulary across all parsers before costly physical experimentation. Do not self-modify Discovery Engine from one local discovery lesson.
