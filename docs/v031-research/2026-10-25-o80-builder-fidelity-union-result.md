# O80 — Installed three-platform Builder fidelity composition: result

**Date:** 2026-10-25 UTC. **Status:** FOCUSED PRODUCT-CORRECTNESS CANDIDATE PASS; NOT MERGED; NOT RELEASED; NO OFFICIAL PERFORMANCE CREDIT.

## Problem and baseline

Three independently implemented Builder source-fidelity guarantees were not exercised together: PR #419 O64 (O47/O48/O50, NTFS regular/root/nested-directory named-stream rejection), PR #420 O65 (xattr enumeration/value read fail-closed), and PR #421 O67 (selected-root hardlinked-symlink inode guard). Owner code came from different parents. Copying O65's complete Builder onto O64 would erase Windows physical hardlink, unsupported special-entry, and NTFS ADS protections.

The prospective hypothesis, alternatives, kill conditions, source identities and test obligations were **committed before implementation** at `dc3c93630372b486f1d27842611141c95914b2d9` in `docs/v031-research/2026-10-25-o80-builder-three-family-source-fidelity-prereg.md`.

## Exact source/implementation identities

- O64 product parent: `9de342226bfbce3690ef1c8cabb1fdf229dbf003`; parent Builder Git blob `b02a30d4ad1b26ea8eea49e11159113caebd6006`.
- O65 owner Builder blob `7f222458adc1c4aae65fa24650a8fc0c7b0c1b18`; exact unchanged owner test blob `a1fea48b62b53f417afa19fbbba805fee090736e`.
- O67 owner Builder blob `636cacef95c518b5ad67c101a5430de5b68d45c6`; exact unchanged owner test blob `71f6013453b350b9c13e47138c57d0d977e16a25`.
- Integration Builder blob **`37833f09dee4671b8ca6f3f3690a7fdebfbc4c70`**, implementation commit `ed61bf50c756d00a6225caf247e1d2b4b606ef68`. No Reader, Writer, codec, native, format, fixed corpus/comparator changes.
- Corrected source-exact evidence HEAD: **`cce361d4563695084069454d8037ab153796e994`**. Product Builder source stayed byte-identical during both JUnit custody corrections. Workflow source SHA guard executes on all hosts.

## Direct hosted scientific/product evidence

**Exact-head GitHub Actions O80 [run #40191958541](https://github.com/FCMO-AI/.CMPCT/actions/runs/40191958541): SUCCESS — all three installed-wheel jobs actually executed and passed.** JUnit was parsed and required exact platform-specific collection/skip counts with zero failures/errors; actual `cmpct.builder`, `cmpct.reader` and `cmpct.ntfs_streams` were asserted to import from installed package outside the checkout.

| Host | Actual collected | PASS | Classified SKIP | FAIL/ERROR |
| --- | ---: | ---: | ---: | ---: |
| Ubuntu 24.04 | 36 | **29** | 7 | 0 |
| macOS 14 | 37 | **29** | 8 | 0 |
| Windows 2025 | 37 | **26** | 11 | 0 |
| **Total** | **110** | **84** | **26** | **0** |

Linux's `errno.ENOTSUP` and `errno.EOPNOTSUPP` are aliases, so O65's parametrized owner suite collects one fewer case on Linux. The first O80 hosted job [run #40191620630](https://github.com/FCMO-AI/.CMPCT/actions/runs/40191620630) exposed this *strict evidence-counter false red*: all actual test cases passed, but the workflow expected 36 on all OSes. Second attempt expected 37 on all OSes and failed despite 29 PASS/7 SKIP on Linux. The final workflow asserts the actual **36/37** by platform and **7/8/11** classified skips without loosening or deleting a single product assertion. This is custody calibration, not an engineered product win.

Evidence artifacts of final result (public GitHub uploads, retained 30 days):
- Windows [#12598661351](https://github.com/FCMO-AI/.CMPCT/actions/runs/40191958541/artifacts/12598661351), SHA-256 `105fcc12aa8aa007b8ce9a069345d7e64eb91f41c44b385e46eaae75d8a96286`.
- macOS [#12598491559](https://github.com/FCMO-AI/.CMPCT/actions/runs/40191958541/artifacts/12598491559), SHA-256 `31f930585766d6f7eaccfeedd227a94adb4cebe0bcf91f2106a4bf95d2decf3f`.
- Ubuntu [#12598276840](https://github.com/FCMO-AI/.CMPCT/actions/runs/40191958541/artifacts/12598276840), SHA-256 `0be0c97e9f64f2c7355a65af5c57361d40f0dd3b8a764ea89c621231fffb1c59`.

The new mixed-case POSIX test uses real selected symlink-inode hardlinks and ordinary file hardlinks, verifies no-clobber refusal on unrepresentable topology, then removes the unsupported selected alias and verifies authentic Builder→CMPCT Reader extraction, physical regular-file hardlinks, symlink destination and a real xattr when supported.

## Strongest negatives, exact-head CI and unmeasured debt

- Historical O47/O50/O57 workflows are **source-locked to earlier Builder blobs**. They fail on this intentionally modified Builder before product comparisons; do not weaken their historic code fingerprints. O80 executes their unmodified original test files against the exact composed product, and O64's successor court passed again at this HEAD.
- At measured O80 HEAD `cce361...`: Engineering Evidence, CI Topology, Version Discipline, Native Core, Continuous Fuzzing and O64 installed court **SUCCESS**. General Tests still **IN PROGRESS** when this result was written. Official r24/ZIP gate reports administrative SUCCESS but its substantive `performance` job was **SKIPPED** due latest-head-only workflow-impact routing. This is **NOT** an official performance clearance.
- Additional tests are focused safety/semantic checks, not comprehensive filesystem snapshot or concurrency evidence. O52 path pivot and live source mutation remain unresolved. O75 atomic output publication, O60/O63 VZIP work, and Writer/Reader integration are separate owners.
- O65's xattr-error tests use fault injection where native OS APIs are missing; macOS/Windows do not gain demonstrated native POSIX xattr roundtrip. Win32 directory ADS results apply to actual Windows NTFS fixtures; no ReFS/SMB/volume-general claim is made.
- No fresh complete archive size, end-to-end create/extract CPU/wall, RSS, temp I/O, selective-read cost or official direct-base A/B was measured by O80. Added map memory is proportional to qualifying hardlinked symlinks; O64's Win32 enumeration costs remain.
- Zero release credit, zero invented compression gain; original successful encoding semantics unchanged in the tested cases. Release promotion requires broader integration and measured gate.

## Decision and handoff

**O80 focused three-owner Builder integration candidate PASS** on three actual installed hosts. The question 'can O64/O65/O67 coexist under their inherited asserted semantics?' is answered **yes for this source/test intersection**, not for all hostile filesystems. Comments were posted to original owner PRs #419/#420/#421, preserving their isolated branches and future authority. Next action is to review the exact union, classify generic tests and route a true direct-base official performance gate when the relevant candidate/ownership surface is ready; do not repeat source-locked owner CI as if its expected historical fingerprint had changed.

No Discovery Engine policy change or cache rewrite earned by this isolated positive composition. The transferable lesson already expressed in source-bound tests is to distinguish actual tests executed from parametrization counts, and to preserve historical exact-blob controls while proving integration with unchanged assertions.
