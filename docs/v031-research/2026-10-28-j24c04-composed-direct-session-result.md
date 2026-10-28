# J24C04 — source-exact #569 vs #630 direct RAW whole-session economics

**Date: 2026-10-28 UTC.** **Decision: `NO_PREREGISTERED_MACRO_DEBT_SIGNAL`, with real nonzero selective-read tax.** Scope: one Ubuntu 24.04 / Python 3.11 same-input actual Reader ABBA court, *not* release-wide performance parity. No product/source/format changes.

## Authority, preregistration and immutable source

Prospective preregistration commit `6aa2445637972a25ec55d419316f0671205a704f` predated any court workflow or measurement. The exact frozen source #569 parent is `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`; composed guarded #630 Reader Git blob `b37b786966ac1506a0439567d4a58eea472d85f8`, validator blob `fbcf6e9c108799dc8b6f5c19e95bcb0618cf41e8`. Original J24B03-M experiment and independent referee, unchanged from #609 `45e7d24600f3e9a79e0ac99c9e28624f01418584`, were source-locked at Git blobs `3e9dad748ead32cfe306064b0b4ddd9f5706b17b` and `e3a93d6ef5cc1a0b4a727b6277b4740dea01a74b`.

The workflow independently checks baseline/candidate Python source import paths and SHA-256, actual archive SHA, checksum, all raw per-process measurements and their ABBA order. Each profile comprises 12 fresh workers (3 cycles × baseline,candidate,candidate,baseline) with startup/import excluded from timer; N=1,4096,65536 valid signed S_BLOB logical members share one 128-byte physical RAW owner. Source/archives identical **within** each paired workload. The independent referee rejected three intentionally falsified receipts.

## Hosted decision-changing measurements

[Source-exact GitHub Actions run #40617545329](https://github.com/FCMO-AI/.CMPCT/actions/runs/40617545329) **SUCCESS**, HEAD `b0297e6ba9166bfb8f88bbe64e5fe19e1d2c654f`, 36/36 independent worker observations, unchanged independent referee **PASS**, three forged receipts rejected. [Original provider artifact #12785657111](https://github.com/FCMO-AI/.CMPCT/actions/runs/40617545329/artifacts/12785657111) ZIP SHA-256 `dc6697af651524303a1072bcd659968be466e237de3525990c8c146e322b76ce`, including raw JSON, source identities, exact bytes/archived inputs, diagnostics and referee output.

| Logical direct members | Parent whole-session wall (ms) | Composed whole-session wall (ms) | Delta (ms) | Ratio | Selective-read delta (ms) |
|---:|---:|---:|---:|---:|---:|
| 1 | control only | control only | -0.005751 | 0.976593× | +0.001052 |
| 4,096 | not quoted as release comparator | not quoted as release comparator | +1.325785 | 1.116467× | +1.207048 |
| 65,536 | 187.324203 | 205.556513 | **+18.232310** | **1.097330×** | **+17.363374** |

For N=65536, the direct-range work itself increased **79.8142485 → 97.177622 ms** (+21.75%), while cold open was 107.500159 → 107.156997 ms (-0.343162 ms, no credible improvement claim), standalone strict preflight 215.794171 → 216.155802 ms (+0.362 ms), and process peak session RSS 50,444 → 50,374 KiB (measurement noise/no material increase). Whole-session CPU rose 187.308832 → 205.543930 ms (+18.235098 ms). Full-session overhead is real even though prereg veto did not fire.

The **unchanged frozen discriminator** requires both median whole-session CPU and wall ratio >=1.10 AND both absolute deltas >=25ms (or +8MiB RSS) on 4,096 or 65,536, with a distinct preflight veto at >=1.15x and +50ms both. No scale met the complete conjunction; 4,096 exceeded the relative threshold but not absolute cost, 65,536 was +18.23 ms / 1.09733x. Conclusion **`NO_PREREGISTERED_MACRO_DEBT_SIGNAL`** is narrow: **not zero overhead, not broad performance parity, not a release gate**.

## Preserved infrastructure negatives (not product losses)

[Original run #40616581425](https://github.com/FCMO-AI/.CMPCT/actions/runs/40616581425) failed before any matched worker observation because the pinned parent checkout lacked its package-owned native `cmpct_core` binary. [Diagnostic run #40617270930](https://github.com/FCMO-AI/.CMPCT/actions/runs/40617270930) independently exposed baseline `RuntimeError: package-owned cmpct_core codec library is missing`, while candidate worker passed; not a compression or Reader correctness failure. The parent native library was then compiled via an actual editable package install, mirroring the historical original workflow; exact parent/candidate Reader source blobs and the original J24B03-M evaluator/criteria remained unchanged. The first two red runs remain red, not retrospectively rewritten.

## Strongest self-critique, next decision and concurrency

The 27–28× high-reference S_CHUNKS cold-open loss of #569 (relative to its own #567 parent) is much larger and completely **unresolved** by this study; a direct-S_BLOB session court cannot claim to rehabilitate that. One hosted CPU/dedup workload does not establish arbitrary-filesystem size, cold filesystem cache, throughput across codecs, host-platform parity, source lifetime under concurrent mutation, hardlink alias validity, transactional recovery, complete archive authentication, or release economics. The actual direct guard tax may compound with #569's independent admission overhead; the baseline is allowed to win.

**Next high-value action:** hand exact result to owner #569/#609, then prioritize eliminating the O215 repeated-reference interpretation cost *without weakening signed geometry*, using their existing #627/#628 native admission route or a bounded equally rigorous alternative, with full Reader cold-open CPU/wall/RSS and original hostile controls. Separately close installed Linux fd publication using J24C05 #634 and pursue existing-target extraction security #528. No source mutation to other owners, no Discovery STATE/policy change (#574 owns it), no merge/release.
