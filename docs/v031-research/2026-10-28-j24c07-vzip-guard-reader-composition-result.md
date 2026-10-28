# J24C07 / J24C07b — VZIP physical projection on source-pinned guarded Reader

**2026-10-28 UTC. Status: source-exact focused integration PASS, source-exact preflight economics screen PASS, product/release promotion PENDING.** Research branch remains draft PR [#638](https://github.com/FCMO-AI/.CMPCT/pull/638) stacked on [#630](https://github.com/FCMO-AI/.CMPCT/pull/630), not merged into main. Published CMPCT remains v0.30.0 / physical revision 24.

## Primary question and prospective evidence
The prospectively preregistered [J24C07](2026-10-28-j24c07-vzip-guard-reader-composition-prereg.md) asked whether source-exact #624 VZIP guards can compose with #630 signed S_BLOB/BHDR, fixed/CDC/sparse and FD-publication guards without weakening their independent semantics. The separate prospective [J24C07b](2026-10-28-j24c07b-vzip-preflight-economics-prereg.md) asked whether those bounded recipe checks materially affect full strict preflight on numerous valid recipes, against unchanged #630 on identical authenticated archives. Both preregistrations preceded their implementations/instruments.

Immutable owners:
- #630 J24C03: commit `0a128ff55c7ae0f14c6bdf019a81b40f0d894eff`, Reader blob `b37b786966ac1506a0439567d4a58eea472d85f8`, validator `fbcf6e9c108799dc8b6f5c19e95bcb0618cf41e8`, codec `29526db4203723d83523fc95d074c346b63d7587`.
- #624 J24K05: commit `a4b54266f7cb09e03f9d8704155774b10d6351ab`, exact recipe validation and range primitive owners.
- Resulting validation blob `0614723549403f398a43552a7c5ad3f00fbec688`; resulting codec blob `05fa46ee3cad6116c3579d14a3d86e234b9d92a0`; unchanged Reader source.
- Source auditor `research/j24c07_source_custody.py` verifies the complete candidate files equal the base plus *only* two owner-specified method transfers and the one necessary recipe argument adaptation, and the candidate positive/negative court equals #624 original bytes.

## J24C07 — exact composed Reader correctness on three hosts

[Actions #40625299274](https://github.com/FCMO-AI/.CMPCT/actions/runs/40625299274), original code-bearing source `dafe552edb0b7b8f83f14bfd262a53073f332315`: **SUCCESS for macOS 14, Windows Server 2022 and Ubuntu 24.04**; logs independently inspected. In every host:
- `J24C07_SOURCE_EXACT_TWO_OWNER_COMPOSITION_PASS`; installed site-package Reader, validator and codec bytes matched Git source, not an editable checkout.
- **84 pytest assertions PASS plus 9 unittest subtests PASS per host**: 252 pytest cases and 27 inherited unittest subtests across the matrix, not to be confused with a general full-suite release gate.
- Included 19 unchanged J24K05 VZIP positive/negative cases on each host: source-independent frozen STORED, canonical Deflate mode0 and retained Deflate mode1 genuine revision-24 archives with authenticated index/physical SHA, ZIP validity, full SHA-256 content fidelity, exact ranges; fully reauthenticated logical +1/−1, skeleton +1 and payload +1 contradictions rejected; and no short selective response without preflight.
- Inherited unchanged #630 direct Deflate/BHDR and RAW control-bit guards, O215 fixed chunks, O212 sparse, O214 CDC and missing-fchmod extraction courts passed on the **same combined installed Reader**.

This is **scoped integrated correctness**, not a proof of signed-journal recovery, source races, hardlink alias topology, full POSIX/Windows filesystem semantics, native Rust ABI or mode2 physical reconstruction behavior. Deflate mode2's compressed output length is not derivable from raw blob size; only a component-level compatibility check runs.

## J24C07b — independently preregistered and audited full preflight economics

[Actions #40625299329](https://github.com/FCMO-AI/.CMPCT/actions/runs/40625299329), original source `dafe552edb0b7b8f83f14bfd262a53073f332315`: **SUCCESS** with actual `FOCUSED_ECONOMIC_SCREEN_PASS` and independent `J24C07B_REFEREE=PASS FORGERIES_REJECTED=5`. 48 fresh subprocess workers, 480 timed complete strict `preflight_archive()` calls, two ABBA cycles per six shapes, 32/512/4096 distinct authenticated file/recipe records and two genuinely valid STORED/retained-Deflate geometries, same exact archive bytes per parent/candidate, CPython 3.11 Ubuntu. No changes to screening threshold (1.25×).

| Valid files/recipes | STORED candidate / #630 wall | STORED candidate / #630 CPU | Retained Deflate candidate / #630 wall | Retained Deflate candidate / #630 CPU |
|---|---:|---:|---:|---:|
| 32 | 1.0035× | 1.0035× | 1.0138× | 1.0139× |
| 512 | 1.0308× | 1.0302× | 1.0360× | 1.0358× |
| 4096 | **1.0355×** | **1.0353×** | **1.0270×** | **1.0270×** |

All additional cost is **positive** (up to ~3.6% in these shapes). The small measured regression is explicitly preserved, not described as free or as a compression-speed gain. The extra arithmetic is linear in recipe entries; whole-Reader open, read/extract, 64-bit adversarial scaling, peak RSS outside Linux, selective-read CPU and release benchmark parity are **not** credited. Source artifact [ID 12789017415](https://github.com/FCMO-AI/.CMPCT/actions/runs/40625299329/artifacts/12789017415), SHA-256 of ZIP `e8f4d7a0cc117cc8580eb39df124aa24c6f56ac5691f4afdf5d7f87772d05392`.

## Negative and contradictory evidence

The *inherited original owner* #630 J24C03 source-custody workflow was also automatically invoked on the **new child branch**. It failed its intentionally frozen exact-source assertion `validation changed source outside named J24C03 guard methods`, because adding an independently validated VZIP recipe guard is **outside the original #630 allowed mutation surface**. The #630-dependent J24C04 economics workflow also fails a literal equality check requiring #630's *old* validator SHA `fbcf6e9c...`. These are genuine evidence-instrument **scope/custody failures for composing a child**, not evidence of a changed direct BLOB behavior; neither frozen source audit was weakened or modified. Dedicated J24C07 source custody now explicitly validates BOTH old and new source ownership, while the candidate's actual inherited behavior tests passed. A future owner must reconcile generic CI topology and supersession before merge, rather than treating two old red checks as green or deleting them.

The full general tests, continuous fuzzing, release numeric benchmarks and native exact-head checks are independent gates; even when green or skipped they are not automatic permission to merge. Historical J24K04 *observational* tests deliberately assert the original vulnerability and are preserved unchanged, so they must not silently become repaired-regression expectations.

## Decision, counterfactual, and next action

**Integration-candidate PASS, not product promoted.** Source-exact body reuse allowed a small decisive combined proof instead of a fresh VZIP parser and avoided intersecting #637 ABI3 performance research. Discovery state under [#574](https://github.com/FCMO-AI/.CMPCT/pull/574) remained unchanged. Counterfactual: the first validation audit needed to inspect *both* source-owner deltas; applying single-PR source audits to a stacked composition predictably produces false blocker attribution. A dual-owner source witness can be preregistered and run before any expensive full product benchmark. One observation cannot justify modifying CMPCT-wide discovery policy.

Most valuable next: hand this composed source and scoped 3-host evidence to #630/#569 owners for independent integration with #615 hardlink alias admission, #613/#620 sparse verification, #624 VZIP, signed-journal recovery and optional ABI3 #637, then tackle inherited #569 27–28× cold-open debt while retaining strong signed-index safety. No main rewrite, format bump, release or merge is authorized by this result.

## J24C07c — decisive new negative after first focused success

**Later evidence supersedes any claim that this branch is generally VZIP range-safe.** The additional prospectively preregistered [J24C07c](2026-10-28-j24c07c-vzip-deflate-mode2-prereg.md) exercised *genuine* Deflate mode2 regeneration, which the original #624 fixed test only checked via metadata algebra.

The first hosted J24C07c attempt had an **instrument error**: it passed the encoded CMPCT archive to Python's native ZIP parser. It was fixed by deriving the independently frozen raw member from its documented SHA and verifying a byte-identical zlib level-6 stream, without changing expected rejection or the candidate code.

In the second [three-host scientific run #40626003178](https://github.com/FCMO-AI/.CMPCT/actions/runs/40626003178), macOS, Ubuntu and Windows each observed a **valid mode2 positive PASS** (exact ZIP reconstruction, SHA, `verify()`, strict preflight and range equality). The signed mutated mode2 negative then **FAILED prospectively required runtime rejection**: `read()` detected the 14→15-byte compressed-stream contradiction, but `read_range(original_end=130,1)` returned a full-length *wrong last-skeleton byte* rather than rejecting. The final returned-length guard alone cannot detect a shifted virtual coordinate; preflight also cannot infer regenerated Deflate's actual compressed length solely from raw metadata. On **each** of macOS, Ubuntu and Windows: **85 passed, one failed, nine unittest subtests passed**, with the same sole failure `Failed: DID NOT RAISE OSError` in the original hostile mode2 test. This is a **3/3-host confirmed correctness negative**. No green mode2 promotion claim. The live runner link is source-bound to executable HEAD `74456587c861fd76cc4c20328a90e9c9489ac662`. Earlier three-host focused original 84+9 PASS and independent complete-preflight cost court remain valid **for their narrower tested cases**, but do not resolve this new counterexample.

New issue: [#640](https://github.com/FCMO-AI/.CMPCT/issues/640) — scoped signed regenerated-Deflate mode2 physical-position discrepancy, **research/compose source, no published-product claim**. Product fix pending. For any requested range after a mode2 payload, validate the *actual regenerated stream length* before trusting `csize` to advance subsequent literal offsets. Preserve pre-stream selective laziness, valid mode2, exact source ownership, and measure exported CPU/wall/RSS when requests cross large regenerating payloads. Do not mark the failing regression xfail/green, weaken the J24K05 source audit or silently promote this PR.

**Scientific decision is split:** #638 integrated mode0/mode1/STORE physical projection and direct/CDC/sparse composition with strong three-host evidence; J24C07b confirmed small bounded preflight overhead. **Mode2 suffix selective correctness is unproven/negative and blocks promotion.** This is new decision-changing evidence, not a failure of the earlier independent source controls.
