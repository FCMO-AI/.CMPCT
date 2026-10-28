# J24C09 — Installed optional ABI3 selective-session result
Date: 2026-10-28 UTC
Status: DECISION-COMPLETE RESEARCH / THREE HOSTED PLATFORMS / NO PRODUCT MERGE OR RELEASE

## Authority and exact source
- Prospective preregistration: `docs/v031-research/2026-10-28-j24c09-installed-native-session-prereg.md`, first child commit `dcb89eb3049b53d23c32a12e9ad970c2c0ab4ce1` before instrument and result.
- Source-executed CI HEAD: `4158c810fedb60ab1fb555450a46ebbbb8693033`. [Hosted J24C09 tribunal #40634835335](https://github.com/FCMO-AI/.CMPCT/actions/runs/40634835335): Ubuntu/macOS/Windows jobs all SUCCESS.
- Exact product Reader Git blob `9bca5d1047f9c78984b945d7ca90e3149fe429ab`, admission `432e86f73f3f1751c04ccbb0e45858c18531da1d`, scanner `308598c42f2060a93d8c41ae8733faf4f18ec968`, `setup.py` `676c156740ead7c0673e16f9f9b9f47b5704bd8a`: unchanged from parent J24C08 #641. Windows installed Python source uses CRLF checkout transport; Git-blob normalization is limited to reversing CRLF->LF while raw SHA-256 is independently retained.
- Original artifacts (include all four signed physical .cmpct inputs, raw process-level samples, decision receipt and actual installed wheel):
  - [Ubuntu #12793700103](https://github.com/FCMO-AI/.CMPCT/actions/runs/40634835335/artifacts/12793700103)
  - [macOS #12793450840](https://github.com/FCMO-AI/.CMPCT/actions/runs/40634835335/artifacts/12793450840)
  - [Windows #12793486009](https://github.com/FCMO-AI/.CMPCT/actions/runs/40634835335/artifacts/12793486009)
- External replay independently downloaded the three artifacts and recomputed 12 median-of-worker-median rows, checked 4 original archived wire SHA-256 per host, matched 48 process records per host (144 total) and six returned-range byte digests per individual session; all agreed with the hosted referee. The original referee also rejected 4 deliberately forged receipts.

## Question and baseline
J24C08 proved that optional ABI3 yields a 10.98–14.98x installed Reader *constructor* gain versus unchanged strict Python on large S_CHUNKS maps. Does that translate into a complete selective session that also reads actual bytes? Stronger simpler control: identical installed wheel with only `_chunk_admission._scan_refs=None` in strict workers. Real native workers use the original callable with an untimed engagement probe, restored before measurement. Same signed input for both arms, identical standard Reader; no change to Reader/validator/r24.

## Result — wall milliseconds / complete session, median of process medians
Each actual session opens one Reader, lists its member, reads six separately positioned 16-byte ranges at head/middle/tail, then closes. The 4,096-reference control *also* performs full read + strong verify, deliberately not extrapolated to the large profiles. All six read results equal independently constructed expected slices.

| Host | References / owners | Strict Python total ms | Optional ABI3 total ms | Full-session wall speedup |
|---|---:|---:|---:|---:|
| Ubuntu 24.04 | 4,096 / 1 + full verify | 84.09 | 72.89 | 1.154x |
| Ubuntu 24.04 | 65,536 / 1 | 30.33 | 12.12 | **2.502x** |
| Ubuntu 24.04 | 65,536 / 256 | 31.16 | 12.67 | **2.459x** |
| Ubuntu 24.04 | 262,144 / 1 | 119.11 | 48.79 | **2.441x** |
| macOS 14 | 4,096 / 1 + full verify | 59.04 | 50.96 | 1.159x |
| macOS 14 | 65,536 / 1 | 29.94 | 12.75 | **2.348x** |
| macOS 14 | 65,536 / 256 | 42.28 | 15.19 | **2.784x** |
| macOS 14 | 262,144 / 1 | 139.36 | 52.95 | **2.632x** |
| Windows 2022 | 4,096 / 1 + full verify | 108.675 | 99.874 | 1.088x |
| Windows 2022 | 65,536 / 1 | 45.309 | 17.035 | **2.660x** |
| Windows 2022 | 65,536 / 256 | 46.669 | 17.511 | **2.665x** |
| Windows 2022 | 262,144 / 1 | 182.743 | 70.487 | **2.593x** |

The preregistered 1.50x floor on *both one-owner large profiles* is met on Ubuntu and macOS. Peak-RSS growth on those profiles remains below the frozen +8 MiB ceiling, according to OS high-water observations (Ubuntu -84 KiB/-64 KiB; macOS -288 KiB/+1,504 KiB, respectively). **Windows RSS is UNMEASURED**, not zero: its verdict is `SELECTIVE_SESSION_WALL_GAIN_RSS_UNMEASURED`, not the fully qualified RSS decision. Ubuntu/macOS verdict `SELECTIVE_SESSION_PRODUCT_HEADROOM_CONFIRMED`.

## Attribution and strongest negatives
- The gain is **almost entirely constructor/admission time**, not faster selective reads: for Ubuntu 65,536 / 1, open ~19.38 -> 1.61 ms while six ranges stay ~10.50 -> 10.49 ms. Windows 262,144 / 1, open ~121.21 -> 8.55 ms while ranges stay ~61.52 -> 61.78 ms. Therefore do **not** claim native S_CHUNKS range access itself was accelerated.
- The bounded 4,096-reference full-read + strong-verify sessions deliver only ~1.09–1.16x, not the preregistered large selective-session 1.50x floor. This is a real negative regarding broad workload extrapolation; verification dominates and ABI3 admission is only one part.
- Physical signed r24 fixture sizes are **474 B, 482 B, 19,374 B, 516 B** (profiles in table order); the tiny one-owner archives are highly redundant, synthetic, and not representative of arbitrary filesystems. Same physical bytes/hash across all three hosts; correct response hashes and original input wire preserved.
- 3 ABBA/BAAB cycles, 4 profiles, 12 fresh workers/profile/host, 3 timed sessions/worker: 48 workers and 144 timed sessions per host, **144 workers / 432 timed sessions** total. Original full process wall and per-phase CPU/wall measurements are in the artifacts. Process startup is separately recorded, not silently added to Reader constructor.
- Source and false-green controls remain unchanged from the preregistration; CI enablement failures were faithfully retained (relative fixture path under subprocess cwd, Windows newline transport, and a CI topology/PR evidence policy mismatch) and corrected in subsequent commits without weakening benchmarks.

## Counterfactual and next action
An early discriminating measurement would have been *complete session wall*, not the constructor scalar. Here that was prospectively observable: it proves meaningful native gains at Q=6 but not at the small full-verify workload, indicating an admission-vs-reconstruction split. Earlier O221 [#583](https://github.com/FCMO-AI/.CMPCT/pull/583) already proves fully charged Q64 checkpointed range indexing has high upside and Q4 lazy policy failed: do not duplicate its implementation. Next, source-exact composition with #641 optional ABI3 should investigate selective-range crossover, fallback, actual whole-product extraction/verification/updates, binaries/wheel distribution and release corpus before any merge or publication. Do not change the format/CI/frozen gates or Discovery policy from one experiment.

**Scientific conclusion:** `PRODUCT_SELECTIVE_SESSION_HEADROOM_CONFIRMED_ON_LINUX_MACOS`; `WINDOWS_WALL_GAIN_CONFIRMED_RSS_UNMEASURED`. This is research on a currently unmerged Reader candidate, **not** shipped CMPCT v0.31 product credit, an official 15-workload benchmark, or a release decision.
