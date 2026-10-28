# J24B03-H2 — RAW BHDR metadata-offset custody, 3-host source-exact decision

**Date:** 2026-10-27 UTC. **Result:** `HOSTILE_BYTE_OFFSET_CUSTODY_CONFIRMED`. This is a supplemental scientific/product-candidate *safety* court, **not** general Reader correctness, performance parity, merge or release authority.

## Why H2 exists and what was left false

Original J24B03's three-host 24-wire equality guard court [Actions #40546227217](https://github.com/FCMO-AI/.CMPCT/actions/runs/40546227217) succeeded. Later **J24B03-H's frozen stronger claim was falsified** [Actions #40554574952](https://github.com/FCMO-AI/.CMPCT/actions/runs/40554574952): it incorrectly assumed that a released RAW `read_range` would always return the **unchanged** original eight-byte payload under *every* corrupted physical BHDR field. The failed assertion is intentionally preserved. It is not reclassified green and neither instrument nor prerecorded condition was weakened.

[J24B03-H2's separate prospective contract](2026-10-27-j24b03-bhdr-offset-diagnostic-prereg.md) was committed at `2e60d5cfc7222adb5d48e44c1e69dfdd648fe69a` **before** H2 implementation (first script commit `3d2374e5ad9b426515367499a62549e4b225f68b`). H2 recorded the real historical outputs rather than asserting that they must be unchanged.

## Executed 3-host result

Source-exact [H2 Actions #40563840185](https://github.com/FCMO-AI/.CMPCT/actions/runs/40563840185) **SUCCESS on Ubuntu 24.04, macOS 14, Windows 2022**. Actual candidate checkout HEAD `b39009ffc029f9c98d91e494d2ca4fabaf71285a`, with original released source `main@80c358f8824ec1b20d349c92ed94c898090969b0`. Both installed their own package/native build. Candidate Reader git blob `33deb74e196f7e40aa8351b6ec426a24255d5eec` vs historical blob `e716233403dabd0966863c45635e18fa5ac6afb8` on all hosts. The process-file SHA-256 differs on Windows from POSIX because of checkout newline representation; the Git blob identities and exact-wire content stay fixed.

Each host consumed **twelve** Builder-independent immutable signed-index r24 images: two valid RAW K_FILE/K_SYMLINK controls plus ten corrupt physical headers (five independent fields × two logical kinds), with one-field changes and unchanged hashed logical primary/tail index, unchanged payload, all source wire SHA-256 checked. Referee uses stdlib only, independently reopens images, checks exactly one physical field changed, identical content outside BHDR, physical payload equality, source identities and all receipts, without importing CMPCT.

| Physical BHDR fault | Historical RAW selection | Guarded selection |
|---|---|---|
| `magic` | original 8 bytes, **ACCEPT** | **REJECT** |
| `codec` | original 8 bytes, **ACCEPT** | **REJECT** |
| `usize` | original 8 bytes, **ACCEPT** | **REJECT** |
| `csize` | original 8 bytes, **ACCEPT** | **REJECT** |
| `metadata length (rml)` | **one-byte-shifted** 8 bytes, **ACCEPT** | **REJECT** |

This table applies to **both** direct file and symlink kinds and reproduced on all three hosts. At `start=7, length=8`, the real published Reader returns `726765742d303132` (`rget-012`) under the first four faults, but `6765742d30313233` (`get-0123`) for `rml=1`. The guarded candidate rejected each with `OSError`. Historical strict preflight separately rejected all corruptions; the stronger issue is ordinary fast range read incorrectly accepting them.

Across three hosts: **30/30 historical corrupt frames accepted by selected read; 30/30 candidate corrupt frames rejected; six valid controls accepted with exact expected bytes; independent auditor PASS 3/3**. This closes the precise cause behind H's historical wrong-byte prediction without rewriting H.

## Original audit artifacts / exact hashes

- [Ubuntu original artifact #12762077921](https://github.com/FCMO-AI/.CMPCT/actions/runs/40563840185/artifacts/12762077921) ZIP SHA-256 `f78281ac551cbad2ddf49c10331abf68c7eec7821b78233b89151bd25433046b`.
- [macOS original artifact #12762670673](https://github.com/FCMO-AI/.CMPCT/actions/runs/40563840185/artifacts/12762670673) ZIP SHA-256 `952fbb7afd69987b4f06e2811158be9deb31697896db75938d26c0245ebff665`.
- [Windows original artifact #12762118125](https://github.com/FCMO-AI/.CMPCT/actions/runs/40563840185/artifacts/12762118125) ZIP SHA-256 `d67ef675dcc0529b0fd24d89cd4a86ab2e8fc51a649807b8753f04d949651bb0`.

All three host ZIPs independently re-opened and hashes/manifest/readout recomputed, confirming `mechanistic_rml_shift=CONFIRMED`, `historical_gap=PRESENT`, `candidate_rejections=10`, `valid_controls=2`.

## Strongest negative and scope

- This new H2 PASS **does not retroactively make H PASS**. H's specific eight-byte historical expectation was wrong and must remain an explicit failure. H2 demonstrates that physical metadata length actually changes historical data identity, a stronger causal understanding.
- It does not establish valid physical payload strong SHA on every selected request; with valid BHDR, mutation behind the header still needs separate integrity checks. An apparently unchanged selected range under some BHDR fault is still invalid physical archive input.
- These are **two 128-byte direct RAW logical owners**, not every codec, chunked/sparse/PACK/virtual member, mutable inode, hardlink alias, or filesystem attack. The original direct size court already covers valid RAW/Zstd/Deflate; H2 only adds orthogonal RAW header-field coverage.
- H2's candidate source is the isolated #609 draft; #569 owns full Reader composition and retains the measured 27–28× cold-open debt on many chunk references. Hardlink alias size #610 is separate. No project-format/release mutation.
- The separate [J24B03-P result](2026-10-27-j24b03-direct-range-cost-result.md) measured a real +135.47 ns/RAW-selected-call overhead (+37.94%) against released Reader but **did not** trigger its preregistered >=500 ns absolute materiality veto. No full-system parity claim.

## Decision and next authorized work

Retain the guarded candidate as a strong, bounded direct-owner metadata/physical-header safety repair. The previous false historical `rml` premise is decisively replaced by a **new, separately preregistered and measured** byte-offset fact. Tell Reader composer #569 not to duplicate this exact-wire experiment. Integrate only after composing the relevant current Reader owners and proving general, native, portability, extraction/recovery, cold-open, and full parity gates. No merge or release at this stage.
