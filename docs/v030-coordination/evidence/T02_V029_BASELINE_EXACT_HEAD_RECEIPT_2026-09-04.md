# T02 v0.29 accepted-baseline exact-head custody receipt — 2026-09-04

Status: **BASELINE CUSTODY ONLY — grants no v0.30 release authority**

This receipt records a substantive exact-head reproduction of the accepted repaired v0.29 benchmark identity on the authoritative v0.30 integration branch. It exists to prevent the repaired historical baseline from remaining implicit in transient CI. It does **not** satisfy compression-generalization, runtime/RSS/selective-read, shared-build, external-competitor, CI-topology, strict-release-lock, or any other missing v0.30 release gate.

## Exact source and run

- PR: `#56`
- branch: `agent/v030-authoritative-integration`
- source commit: `83673bcab08b80d7146151f4a16c49206bade507`
- workflow run: `33877773601`
- result-bearing job: `101038850900` (`shipping-vs-frontier`)
- workflow result: substantive job `success`
- artifact id: `9939147214`
- artifact name: `cmpct-v029-shipping-vs-frontier-83673bcab08b80d7146151f4a16c49206bade507`
- GitHub artifact digest SHA-256: `fcb4fd4254fbe94c76311e39dcdf91591dfa41d4326572081795717d81e1fc56`
- instrument schema: `cmpct-v029-shipping-vs-frontier-v1`
- instrument-reported date: `2026-09-04`
- project version under test: `0.29.0`

## Exact accepted-baseline result

- files: `9,253`
- logical bytes: `265,969,714`
- shipping bytes: `181,499,370`
- accepted repaired frontier bytes: `137,499,525`
- frontier saving vs shipping: `43,999,845 B`
- frontier smaller vs shipping: `24.2424229902%`
- frontier row wins: `13`
- shipping row wins: `2`
- ties: `0`

Accepted identity migration represented by the instrument:

- prior aggregate identity: `137,501,815 B`
- repaired accepted identity: `137,499,525 B`
- identity delta: `-2,290 B`
- inherited v0.30 absolute saving hurdle: `687,783 B`
- hurdle lowered: `false`

The repaired Developer Repository row reproduces at `744,337 B` accepted frontier bytes.

The two rows where the v0.29 frontier remains larger than the shipping baseline are preserved rather than hidden:

- Media Library: frontier larger by `1,271,214 B`
- Incremental Backups: frontier larger by `194,273 B`

## Custody interpretation

This result establishes only that the repository's accepted repair-v6 v0.29 identity reproduces end-to-end on one exact PR-head tree while preserving the inherited v0.30 hurdle. It is historical/baseline custody evidence, not a v0.30 product win and not competitor, runtime, locality, recovery, integrity, native/platform, or release-lock evidence.

A green classifier or a green workflow shell with its result-bearing job skipped must not inherit authority from this receipt. Release authority remains fingerprint-specific and fail-closed.
