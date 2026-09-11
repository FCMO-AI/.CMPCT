# CMPCT1 / ONE Genesis week gate — preregistration

Date: 2026-09-09  
Execution embargo: **do not adjudicate before the first activation on or after 2026-09-11 America/Mexico_City**

## Mission lock

`docs/CMPCT1_GENESIS.md` requires the first qualifying activation on/after 2026-09-11 to compare the best CMPCT1 / ONE state against frozen v0.29 and the strongest already-developed deferred v0.30 line with **same input and same semantics**, preserving the full 15-workload matrix plus speed/access/resource evidence.

This preregistration exists to prevent a historical-ledger mismatch from turning into benchmark theater at the gate.

Frozen authorities:

- v0.29 branch authority: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30 authority: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`
- ONE authority: **the exact best `research/cmpct1` source selected at gate time**, bound in the result artifact before execution.

## Historical-ledger mismatch that must not be papered over

The frozen v0.29 authority retains `benchmarks/history/2026-08-17-mosaic-v029-generalization-v2.json`, whose 15-row aggregate is:

- logical input bytes: represented by the exact tree identities below;
- v0.28 embedded baseline: `137,556,533 B`;
- v0.29 candidate: `137,507,932 B`;
- 2 improved rows, 0 regressed;
- attempt-5 creation / embedded-v0.28 creation ratio: `2.195267x`.

The deferred v0.30 evidence line separately recognizes the later repaired accepted-v0.29 frontier identity `137,499,525 B` under its repair-v6 shipping/frontier substrate, with 9,253 files and 265,969,714 logical bytes. That repaired historical aggregate is valid for v0.30 custody, but it is **not byte-identical to the frozen `02b8...` v0.29 ledger**.

Therefore the Genesis decision may not compare ONE against `137,507,932 B` and v0.30 against `137,499,525 B` as if those totals were one symmetric experiment. All three engines must consume one regenerated/frozen tree manifest at the gate, or a row must be marked not-comparable rather than silently substituted.

## Canonical 15-workload identity set

The gate preserves the v0.29 15-row workload taxonomy and deterministic tree identity checks:

| # | suite / workload | frozen tree SHA-256 |
| --- | --- | --- |
| 1 | `neutral_hostile_v1/01_developer_repository` | `ddcdf1ae1b61042634aae40b1b12da629feb98cb45db23c56d1da15334b74645` |
| 2 | `neutral_hostile_v1/02_office_workspace` | `aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57` |
| 3 | `neutral_hostile_v1/03_media_library` | `1966d025d334e4bf6ea38656188708d400f26b6ca53bb581b497357dcdbf869a` |
| 4 | `neutral_hostile_v1/04_analytics_and_database` | `6d0854fe058a95258588b89dca653ac8f00c61f815c6127b179e86cc58b1789d` |
| 5 | `neutral_hostile_v1/05_logs_and_telemetry` | `7356b866d7b99bfce2dd1fc6ef86d61d09c9d8a38a2ff3fec7d9a92e46020931` |
| 6 | `neutral_hostile_v1/06_incremental_backups` | `a823728d98e5882542645e3ab0f777894479cfb3de4dedcec14341fedbb11a05` |
| 7 | `neutral_hostile_v1/07_incompressible_and_encrypted_like` | `da4f37ac1d7a6751c4adcaabb50cc2cd6f2ffbed7bd2100d34b9ef597f7d1d80` |
| 8 | `neutral_hostile_v1/08_many_tiny_files` | `a62a03735deaaaebadacb961326c760aff09c1a4e031a44df02a9e95f8f5093f` |
| 9 | `neutral_hostile_v1/09_ml_artifacts` | `efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d` |
| 10 | `neutral_hostile_v1/10_large_mixed_binary` | `9373f96626c7f463b4112bf138ac5db766e7e71def9b209c7ba28fe44f0878d3` |
| 11 | `resemblance_hostile_v1/01_shifted_versions` | `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd` |
| 12 | `resemblance_hostile_v1/02_false_neighbors` | `3427fd306a10a7c293d4303323d64948ee74d4065353bf99310cfed34dc73d0e` |
| 13 | `resemblance_hostile_v1/03_boundary_churn` | `3238446efaef2a70a5c08d722bdc9dac3ac7c1c99ae3cde8093fae1481ad4b3d` |
| 14 | `resemblance_hostile_v1/04_deflate_family` | `527a9e356e923e5bcc26566a8f677a7f7277af1577493e09c2bdca1b6d17154a` |
| 15 | `resemblance_hostile_v1/05_incompressible` | `1efe49fb1adb16ef911f64f44d41629db599dbeef264d72fd8f26e40515130e4` |

If the repaired deterministic corpus generator intentionally yields a later accepted tree identity for one of the three historically repaired rows, the gate artifact must show both identities and explain the migration. It may not silently relabel a new tree as the frozen one.

## Same-semantics comparison law

For each row, every credited engine must reconstruct the exact same user-visible tree. Comparisons must distinguish:

1. **stored bytes** — complete self-sufficient artifact size with all metadata/authentication required by that engine;
2. **creation** — same-runner CPU and wall time from immutable input tree to final artifact, including hashing, discovery, proof, validation and emission;
3. **whole-read/extract** — exact full-tree reconstruction with integrity semantics enabled;
4. **selective access** — the same selected regular member/range where an engine supports the semantic operation; charge decoded/reconstructed bytes, proof/auth work and temporary state;
5. **peak memory / retained state** — creation and reader/open state separately where available;
6. **integrity/recovery/safety** — no engine receives credit by disabling verification, resource floors, malformed-input rejection, recovery framing or portability requirements.

A missing capability is not a free zero. Mark it explicitly and adjudicate whether that gap prevents supersession.

## ONE representation boundary

ONE may use any promoted writer discovery knowledge available at the gate source, but final credited artifacts must compile through the same ONE Law + Surprise representation principle. The gate may not introduce a fallback to reader-visible v0.29/v0.30 mechanisms merely to improve a row.

Likewise, ONE's current mechanism-level add8/XOR relation wins are **not automatically 15-workload product wins**. If a workload does not yet have a complete ONE ingest-to-artifact path with equivalent semantics, record that honestly.

## Decision law

After all 15 rows and resource/access ledgers are visible:

**Keep CMPCT1 primary** only if the evidence shows a materially stronger path than both frozen v0.29 and deferred v0.30, including a credible route to supersede their mature whole-product capabilities without weakening semantics.

**Reactivate v0.30 as the primary near-term line** if ONE has not outperformed or credibly superseded both after the Genesis week. Preserve all ONE evidence and continue it as a future research line rather than manufacturing a win.

No single aggregate byte total may overrule a severe speed, locality, integrity, recovery, memory or portability regression. No threshold, workload or comparator setting may be changed after the result is visible.

## Execution checklist for 2026-09-11

1. bind exact ONE HEAD and repository status;
2. regenerate/verify the 15 input trees once and freeze their fingerprints;
3. execute frozen v0.29 and deferred-v0.30 comparators from exact source authorities against that same substrate where technically compatible;
4. execute the best complete ONE path against exactly the same substrate;
5. preserve per-row artifact bytes, creation CPU/wall, full decode/extract, selective operation, peak/retained state and integrity truth;
6. preserve failures and unsupported rows rather than substituting historical numbers;
7. emit one machine-readable matrix plus a human adjudication tied to exact source SHAs and hosted artifacts.

Execution before 2026-09-11 is prohibited by the Genesis window; this document freezes custody only.
