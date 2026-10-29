# J24G50 — signed-fsmeta × encoded-empty Zstd composition result

**Date (UTC): 2026-10-29. Scientific stage: installed-product integration evidence, not merged/released product evidence.**

## Question, preregistration, identity

A single installed package must preserve two independently demonstrated correctness fixes: the #773 path-identity journal remapper and #767 physically authenticated zero-output Zstd codec. The prospective control was committed first at `05fcd9c23ee6ef897168468941e61162ca46de04`. Parent Reader and Writer source blobs remain, respectively, `84f1c0602c7a9679cd79a0a5de984b169a467903` and `3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11`. The donated native codec is exact #767 blob `1dd853c111410726e051adc48ee59392a4cbd5fb`. No parent/donor branches modified.

## Direct hosted evidence and independent physical witness

Source-exact initial composition HEAD: `4206d128ace8d752966349c455971f54e51a8cce`.

- [J24G50 installed physical CI #40940531876](https://github.com/FCMO-AI/.CMPCT/actions/runs/40940531876): **SUCCESS Ubuntu 24.04 + macOS 14 + Windows 2022; 20 passed per host** (60 test executions, including inherited Owner/Donor/frozen conformance and new integrated test).
- Exact checkout SHA and actual installed Reader/Writer/native codec SHA-256 were printed per host and matched checkout bytes. On all three hosts the external Zstandard auditor reported **`COMPOSED_WIRE_VALID_AND_ONE_BYTE_CORRUPTION_REFUSED`**, and unchanged donor independent audit reported `PASS: signed valid Zstd empty accepted; corrupt encoded magic rejected by independent decoder`.
- The integrated archive is a genuine Builder r24 empty RAW member subsequently re-encoded via independently installed Zstandard as signed valid empty Zstd; a synthetic xattr row is added to its checksum-bearing index. A real Writer `append_update` inserts lexically prior `a-new.bin`, and the Reader maps the xattr from ordinal 0 to ordinal 1 while exactly verifying the empty original and nonempty inserted member. Linux/macOS then genuinely restore and read native xattrs; Windows intentionally claims no native xattr positive.
- The tampered specimen differs by exactly one physical frame-magic byte, not by a modified metadata hash; both installed CMPCT and an independent Zstandard decoder reject it.
- Exact run artifacts: [Ubuntu #12927535622](https://github.com/FCMO-AI/.CMPCT/actions/runs/40940531876/artifacts/12927535622), [macOS #12927630444](https://github.com/FCMO-AI/.CMPCT/actions/runs/40940531876/artifacts/12927630444), [Windows #12926327822](https://github.com/FCMO-AI/.CMPCT/actions/runs/40940531876/artifacts/12926327822). Provider SHA256 ZIP hashes (not independently re-downloaded): Ubuntu `c3202018608c22f2093a0a453f50939d5f7c6ae6727afa797f32bb599d096374`; macOS `0a7f4f9c1886e2bb293365c1f4685d4d9df3928b4fd7d74b43b52502e17479e4`; Windows `28a568cf42656d07dd2248e8f49f3b6b7996eadc982e126a41b2a1d573e13364`.

### Platform-specific physical specimen fingerprints

| Host | Valid after journal SHA-256 | One-byte corrupt SHA-256 | Corrupt encoded offset |
|---|---|---|---:|
| Ubuntu | `c28c94fd5ecba6732bac0f5334ce96f1c8ca6cb047d697a7f1f8596f58e9b085` | `7648debda257bbef2cf454c16597d027f48d4c90d52e77db251ec95be43b78ad` | 502 |
| macOS | `0e08a75a1a43872debd886726c4f40c717c104110d9460443c30d2f376494fe8` | `049edbc10672d7f97bda4a9ee44b8764d01eb36b688eef5fc5414dbab22df8f8` | 506 |
| Windows | `600a192134b270df78889f4a0a689a315b2643f783b079161ffcc2edfbf32bfe` | `e6823d83b6042ddbcfbf4d2d0a5461deedcc0d219f15137b3e4a8112757d7a44` | 503 |

Different archive SHA across hosts is real and **not** evidence of reproducibility parity; metadata and platform-dependent encoded index values differ. The finding is per-host causal accept/reject and path-identity correctness, not same-archive-byte cross-host equality.

## Other exact-head CI: measured versus pending

At ~19:32 UTC for initial `4206d128`, Version Discipline, CI Topology, R36 Attribution, Native Core, Continuous Fuzzing, J24G41 native xattr checks and the administrative ZIP gate had SUCCESS. General Tests remained **IN PROGRESS**. Engineering Evidence failed twice because first the PR body lacked the validator's explicit section headings, and then the exact textual markers `disproof` and `quality-ratchet` were absent. The body was augmented with substantive headings, falsifiability and quality-ratchet explanation at 19:33 UTC, without editing validator/test semantics; a fresh check must run on the new PR event/commit. A green administrative performance workflow is not a complete release parity benchmark.

## Decision, red limits, transfer

**Decision:** The specifically preregistered two-owner integration hypothesis survived the initial installed, independent physical three-host falsifier. This removes one composability uncertainty; it does not close release gates.

No whole-system archive byte economy, create/extract/read throughput, process RSS, temp storage, native Rust complete verifier, privileged UID/GID, hostile directory races, full filesystem semantics, or external ZIP/Zstd fairness was measured in this child. Signed index hashes are internal self-checks, not external authentication of origin. Direct source xattr capture is shown by inherited #773 physical tests, not the new synthetic-base signed fixture. Full General Tests and future release parity remain blocking for promotion; no release credit.

**Next:** reconcile latest general tests and any outstanding check, inform #773 and #767 owners, then integrate only via authoritative product/release owner if all hard gates are met. Avoid extending this satisfied narrow integration into an unbounded micro-optimization family. Separate #777 state-space falsification, #775 Reader economics and #574 Discovery state reconciliation retain ownership. No Discovery policy lesson/change earned.
