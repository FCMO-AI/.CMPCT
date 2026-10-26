# O146 — Installed O137 × unmodified O131 owner tests: three-host result

**Date / evidence boundary:** 2026-10-26 UTC. **Scientific status:** DECISION-CHANGING PASS within focused host/namespace/FIFO scope. **Product release status:** NOT PROMOTABLE.

## Source identity and preregistration

The preregistration was committed **before** this workflow was written: `29eaf4b000aeeea97c75b1ba77c0ad942bba62cf`.

Exact result-bearing source HEAD: `0fab14127c41019bb77fcacf7491113cfaa2af7b` (O146 workflow implementation on top of O137 source). Parent O137: `b5901b9d6b5a23c98bd6a74939f5df82a7d1bd56`. Installed Reader Git blob: `e5301ccf24a63577cfbfa169be9c1e452a0d14bd`. Unmodified path policy Git blob `91fc335eea8fb18c3899511f416c8abe96c48f80`. Exact original source blobs for every O131 owner test and original O137 physical FIFO test were asserted before running; installed `cmpct.reader` and `cmpct.path_policy` imports were verified **outside** the checkout.

Source-bound GitHub Actions: [O146 run 40266337758](https://github.com/FCMO-AI/.CMPCT/actions/runs/40266337758), three original host jobs **SUCCESS** (Ubuntu 24.04, Windows Server 2022, macOS 14).

## Original owner suites + FIFO behavior on one Reader

The O131 original workflow source-binds the previous Reader SHA, so its authentic *behavior* can only be assessed on the new Reader by running its **unmodified owner tests** against a separately installed current O137 package. The original O131/O124 source-exact historical workflows have **not** been edited or reinterpreted.

| Host | All actual testcases PASS | SKIP | FAIL / ERROR | Domain exclusion | Installed Reader |
|---|---:|---:|---:|---|---|
| Ubuntu 24.04 | **53** | 21 | **0 / 0** | none | yes |
| Windows Server 2022 | **54** | 9 | **0 / 0** | none | yes |
| macOS 14 | **59** | 14 | **0 / 0** | **one unchanged O131 Windows-only case-sensitive POSIX positive excluded** | yes |
| **Total** | **166** | **44** | **0 / 0** | **one unchanged Mac domain deselection** | all three |

Both Ubuntu and macOS include the **11 original unchanged O137 FIFO testcases**, *not additional invented tests*. The rest exactly reproduce the O131 platform-owner test selections. Original O131 ran **144 PASS / 44 SKIP**; including O137 adds **22 PASS**, giving the observed **166 PASS / 44 SKIP**, with zero extra skip or exclusion.

A separate parser audited **every individual JUnit testcase**, enforced zero failures/errors, exact expected JUnit file count and **11/11 non-skipped O137 FIFO testcases** on both POSIX hosts. Neither an empty report nor a quietly skipped FIFO test can earn SUCCESS.

Durable raw receipts:
- [Ubuntu artifact 12626632147](https://github.com/FCMO-AI/.CMPCT/actions/runs/40266337758/artifacts/12626632147) — ZIP digest `sha256:480f8551f7eb7e014c37d29e70b93733427705a0bb9b01371fbb417f4fc886cc`;
- [Windows artifact 12626945259](https://github.com/FCMO-AI/.CMPCT/actions/runs/40266337758/artifacts/12626945259) — ZIP digest `sha256:43926b0619e12b34d4679920da257b360c2b58a346739aff6d70ca4bebe1d06a`;
- [macOS artifact 12626760549](https://github.com/FCMO-AI/.CMPCT/actions/runs/40266337758/artifacts/12626760549) — ZIP digest `sha256:32e99e632cdd5569e6128abd959735e9548d55ecf65cd4b80c9817484c8679af`.

## Decision and scientific limitations

**Primary hypothesis ADVANCED:** the implemented static O137 direct-leaf FIFO guard coexists with the prior O131 Windows/APFS namespace/symlink/hardlink and Reader-own-source-inode protections **within their unchanged original tested domains**. No duplicate source-admission implementation is justified by these results. This is product-functional evidence, not standalone release evidence.

**Strongest negative / inherited external gates:**
1. Original O124 unchanged source-exact workflow still rejects O137 because its frozen Reader SHA names earlier implementation. The separately documented O124 macOS sparse fixture test still FAILS, not turned green by O146.
2. The actual O137 source exact official r24 performance run [40261741459](https://github.com/FCMO-AI/.CMPCT/actions/runs/40261741459) is **FAIL** on `combined/cli/create_s_median`: 446.459 -> 469.910 ms, **+5.25%/+23.451 ms** (official >5% and >3ms gate). All 8 × 2 CMPCT archive-size comparisons remain identical. First-run two BASE medians differ 23.224 ms; plausible noise is *not proof*. One preregistered exact-code re-run was launched separately; at initial O146 scientific conclusion **quantitative decision pending**.
3. Neither O131 nor O137 exercises a concurrent post-preflight namespace pivot in its protected static scope. The current Reader remains vulnerable to classes of TOCTOU/resource/recovery debt not measured here.
4. No improvement in general compression size, creation/extraction throughput, RSS, temp I/O, integrity under hostile concurrent mutation, Windows FIFO semantics or new format support is claimed.

## Counterfactual and next action

One prospective discriminator was sufficient: run the **original owner tests unchanged on installed final source**, instead of re-writing old source identity assertions or implementing another equivalent guard. The evidence distinguishes **historical source identity** from **functional continuity** across a subsequent source revision without diluting either requirement. This lesson is local unless more independent incidents justify updating discovery doctrine.

Next: read the rerun’s actual ABBA result and preserve both contrary outcomes; determine whether the official create red replicates before debating causal optimizations. Follow up general installed CI and O124 Mac fixture separately; no merge/release without fully honest promotion gates.

No `docs/discovery/STATE.json` mutation is warranted: separate active PR #440 owns the shared staleable frontier index and this result is entirely linked here.
