# J24G29 — signed ZIP DOS upper-calendar result

**Scope:** bounded candidate correction, not a CMPCT release or format change. `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains v0.30.0 / revision 24. This is a continuation of J24G28 PR #722 stacked on ZIP publication owner #492; no parallel ZIP writer or discovery-state mutation.

## Frozen prediction before implementation

Preregistration: [J24G29 upper-calendar prereg](2026-10-29-j24g29-zip-dos-upper-calendar-prereg.md), committed at `49809ba08d86e10c81000c0ca5fa8c0a70c1188c`, before Reader patch `93ef1f25de74a5ffa8fb080974e3677eab05ac61`. J24G28's inherited upper-year clamp was known to potentially produce 2107-02-29 from leap day 2108-02-29; this is not a newly invented family.

**H1:** published-logic year-only clamp encodes an impossible Gregorian date while original CMPCT member metadata/read/verify are otherwise valid. **H2:** full local-year saturation to 2107-12-31 23:59:58 repairs it without changing ordinary ZIP output, J24G28 signed-before-1980 behavior, native mtime, payload or format. **Kill:** any loss of exact content/metadata, any candidate impossible calendar date, same-host 2020 or upper-2107 byte difference, or inherited safety regression.

## Product-court evidence, prior exact head

Product Reader blob candidate: `71a3d56567f7f3eceaaf1d0334857e2c32e04316`; historical parent Reader blob: `496e70bdc06ddc17aa90e4fc0e9f10a6bc5c5332`.

[GitHub Actions #40805906755](https://github.com/FCMO-AI/.CMPCT/actions/runs/40805906755) on exact source `815e6f49a31abc77f6a2a32be8f97887a0485491`: **4/4 specialized jobs SUCCESS**, one genuine first-party physical revision-24 vector generator plus independent installed-source old/new Reader comparisons on Ubuntu 24.04, macOS 14 and Windows 2022. Each host reads the *same generated physical archive bytes* twice per engine; both Readers read/verify every input and rebuild exact contents. Raw artifacts: fixed physical `12868008147`, Ubuntu `12868770269`, macOS `12867534907`, Windows `12867584790`. J24G28 historical result remains [#40801934592](https://github.com/FCMO-AI/.CMPCT/actions/runs/40801934592).

| Physical r24 case | Original inherited ZIP calendar (UTC runners) | Candidate ZIP calendar |
|---|---|---|
| 2108-02-29 12:00 UTC | **2107-02-29** (invalid Gregorian date) | **2107-12-31 23:59:58** (valid, max DOS) |
| 2108-03-01 12:00 UTC | 2107-03-01 (incorrect year substitution) | 2107-12-31 23:59:58 |
| 2107-12-30 UTC | Exact ordinary local DOS | Same-host byte-identical ZIP |
| 2020 ordinary | Exact ordinary local DOS | Same-host byte-identical ZIP |
| Signed pre-1980 cases | Host-dependent historical acceptance | Candidate 1980-01-01 00:00:00 |

An **independent** external ZIP-wire inspection downloaded all four original hosted artifacts, parsed *both* central-directory and local-header DOS words from physical ZIP bytes without importing CMPCT or its test code, cross-checked Python standard-library exact content/CRC, source SHA and original receipts. **524 checks passed** across the three hosts. Both headers agreed; all candidate ZIP calendars are Gregorian-valid. Three deliberately corrupted/forged artifact controls were rejected even after recalculating the claimed ZIP SHA: conflicting central/local DOS bytes, corrupted ZIP payload with CRC failure, and a forged calendar receipt. The local supplementary pure-arithmetic oracle tested 56,048 timestamp/timezone combinations across UTC, Mexico City, Tokyo and Auckland: candidate zero invalid calendars and zero changes for inputs whose *local year* was <=2107; baseline produced impossible leap-calendar values. This oracle is mechanism evidence, not product evidence.

The mature Python `zipfile.ZipInfo.from_file(..., strict_timestamps=False)` explicitly saturates timestamps beyond 2107-12-31 to the ZIP limit (Python [standard library documentation](https://docs.python.org/3.13/library/zipfile.html)). This external comparison is a design reference, not an independent CMPCT product test.

## Product promotion boundary / concurrent CI

The full candidate source remains the Reader blob above; the *current branch HEAD may advance for additive CI ownership and this result note*. The owner updated the branch-scoped workflow to rerun the unchanged O149 failure-atomic ZIP, O140 nonregular output and O135 source-alias product tests using explicit candidate-installed package/environment on Ubuntu and macOS, without rewriting their historical source-exact workflows. **Do not claim those inherited checks have passed until their final exact-head CI actually completes.**

All preexisting O149/O140 workflows pinned to historical Reader blob identities still report FAILURE when invoked on a later source; this is an **integration/source-fingerprint mismatch**, not automatically a product regression and not a green historical court. Generic tests have had real harness-attribution failures; preserve them as failures. Full parity, no-regression, memory, crash/race and complete ZIP chain admission remain unmeasured. No release, no merge and no modification to frozen evaluators or the public Reader.

## Decision and debt

The upper-year-only ZIP date clamp is **falsified** as a valid calendar transformation. The full-date saturation survives the scoped three-host physical and independent ZIP-wire tests. It remains a **draft integration candidate**: actual merge requires inherited safety tests to pass under exact current source, broader product gates and owner #492's complete staged ZIP chain. No discovery-policy self-modification is earned from one boundary case; J24G28 and J24G29 research results remain separate from released product authority.
