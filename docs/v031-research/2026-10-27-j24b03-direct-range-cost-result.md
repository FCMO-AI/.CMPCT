# J24B03-P — source-exact direct range guard cost result

**Date:** 2026-10-27 UTC. **Status:** measured source-exact micro-ABBA science, **not** integrated product parity or release authorization.

## Authority, actual instrument and custody

Prospective contract: [J24B03-P preregistration](2026-10-27-j24b03-direct-range-cost-prereg.md), committed before instrument. Actual hosted [GitHub Actions run #40555542073](https://github.com/FCMO-AI/.CMPCT/actions/runs/40555542073), Ubuntu 24.04 / CPython 3.11, status **SUCCESS**; original [artifact #12755539300](https://github.com/FCMO-AI/.CMPCT/actions/runs/40555542073/artifacts/12755539300), **SHA-256 `2b930d0fe760af86af8f643a7bf1aa4b1edbbad148487daf425444219e88b404`**. Archive contains all 36 subprocess raw observations, immutable signed-wire input images, source refs and stdlib independent referee `PASS`.

The actual checkout inside the runner was candidate HEAD `86c1930ab07906d94cc8681551c620819b40ff71`; candidate Reader git blob `33deb74e196f7e40aa8351b6ec426a24255d5eec`. Historical original is released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Both separately native-installed original source trees were used, not merely Python monkeypatches. Full corpus SHA/input identity and reader-file SHA-256 were checked by the independent referee.

Each of RAW, Zstd and Deflate used the same Builder-independent 128-byte signed r24 corpus across both arms. Each profile ran **three independent ABBA rounds**, 6 fresh processes per arm, 30,000 calls per process, five offset positions and 16-byte answers. Process startup excluded; open was measured separately. Hash/answer checksum and per-arm source identity checked.

## Actual medians and preregistered decision

| Valid direct blob | Released ns / range | Guarded ns / range | Candidate/base wall | Candidate/base CPU | Added wall ns / range |
|---|---:|---:|---:|---:|---:|
| RAW | 357.055 | 492.523 | **1.37940×** | **1.37942×** | **135.467** |
| Zstd | 369.952 | 401.742 | 1.08593× | 1.08592× | 31.790 |
| Deflate | 371.213 | 396.396 | 1.06784× | 1.06785× | 25.183 |

RAW per-process wall ns/call: historical `[342.54,351.47,351.03,362.64,369.21,364.36]`; candidate `[491.00,461.50,477.87,502.58,494.05,496.75]`. Thus the relative RAW penalty is not imaginary or equivalent to a zero-cost guard, but it is *well below* the prospectively required 500 ns **absolute** addition.

The original *conjunctive* threshold required BOTH wall and CPU >=1.20× **and** >=0.50 microseconds additional per call. **Result: `NO_PREREGISTERED_RAW_DEBT_SIGNAL`**, independent referee `PASS`. Never change or reinterpret that threshold after observation. No guarantee of full-system parity follows.

Open-time medians, original vs candidate: RAW 140,991.5 vs 135,704.5 ns; Zstd 127,907.5 vs 131,663 ns; Deflate 129,585 vs 135,439 ns. RAW median process high-water RSS (VmHWM): 23,480 KiB original vs 23,462 KiB candidate. One original RAW worker peaked at 26,076 KiB, so neither uniform-zero-RSS-difference nor a meaningful causal memory improvement is established.

## Strongest critique

- This is deliberately a **micro** court of 128-byte direct members and 16-byte requests, not a full library, extractor, hostile filesystem or release-parity comparison.
- Per-call CPU/wall differences may become relevant at very high query counts even when preregistered absolute materiality does not fire. Do not narrate the 37.94% relative RAW cost as "free".
- It tests the real unchanged release and candidate reader code, but the process/package dependency installs share a host runtime; only the Python `Reader` selection and archived wire are source-separated and asserted. This is appropriate for this narrow Python RAW fast-path contrast, not cross-platform performance proof.
- J24B03-H remains **falsified** in its separate historical "unchanged returned bytes" prediction; its original workflow red is scientific truth, not an inherited product red nor reason to weaken a guard.
- The 27–28× chunked cold-open regression belongs to the independent compounded Reader #569 and is entirely outside this test. Hardlink alias size #610 and existing-target rollback are also unaddressed.

## Decision and next executable target

Keep the authenticated O(1) direct-owner equality and RAW BHDR geometry guard as a legitimate safety candidate with measurable but sub-veto micro cost. Complete the source-exact H2 hostile offset diagnostic under its *own prospective rules* before composition. Then owner #569 must reconcile all Reader safety and performance gates, including same-head cross-platform and complete archive/extraction evidence; no merge, release or format/version claim from J24B03-P alone.
