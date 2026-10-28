# J24C22 — full 16MiB owner sweep: published Reader floor and physical-work transfer

**2026-10-28 UTC. SCIENTIFIC RESULT; DRAFT PR #692; NO PRODUCT MERGE/RELEASE/FORMAT/VERSION CREDIT.** Frozen [prospective preregistration](2026-10-28-j24c22-full-owner-sweep-prereg.md) commit `c1ae6462c77936e1864dcd0167d5472c9c6e66b6`, before instrument commit `b43f03090555a3dae434dc301768c77cf3be3d32`, independent referee `20d2a0d54c2c52bf479380c5e5f8bbbb9be9991b` and workflow `c37758d428f6cce18facb1ac82361cdae87feccd`.

## Exact original evidence and authentication

- Hosted **source-exact** [J24C22 Actions #40738454008](https://github.com/FCMO-AI/.CMPCT/actions/runs/40738454008) completed **SUCCESS**, measured code and workflow HEAD `c37758d428f6cce18facb1ac82361cdae87feccd` on Ubuntu 24.04, CPython 3.11.
- Original [GitHub artifact #12838282371](https://github.com/FCMO-AI/.CMPCT/actions/runs/40738454008/artifacts/12838282371), ZIP SHA-256 `ef0b8fc6e681ac54be09d888dd2505c5b40b731d980d183689079a2f5c15bd8a`, contains the original signed fixtures, 3 wheels, exactly **54 child-process observations**, prospective query workset, science decision, 8 forged-receipt refusals and logs. Never replace this original by hand-transcribed medians.
- Exact independently installed source SHAs: released v0.30.0/r24 `80c358f8824ec1b20d349c92ed94c898090969b0` (Reader SHA256 `83be3f08f7fafb1fd638fda6140bbe1af6676c261be10acc9ea8f8b633beefff`); original unsafe fused #662 `a66fd593a83cc4c71556d3d86d835c51abd20a96` (Reader SHA256 `b9d7c86d021f26a252d2d8cb4d2ba6cbf4613b9fb743abf1a8264a2343a4ecfe`); sealed #676 `3b6a73f9205f40f11124cd9ff332407e52cebb93` (Reader SHA256 `ccb5dfcd45bbef16c880a85b2f66cd91a8b48fa5f42ddab8c506205404f66a5b`). The #662 control is not safe to promote after J24C16.
- Same **unchanged original** J24C21 authentic r24 archive `large_distinct_8k.cmpct`: SHA256 `eb695e0236db6d8d7e7896fcc8d3a2b69a47a66f601e47c8c333879176f58067`, **17,072,796 stored bytes**, 81,234 raw index bytes, 16,650-byte Zstd primary index, **4,096 independently authenticated RAW blobs**, **16,777,216 owner payload bytes**, **8,192 references**, **33,554,432 logical bytes**. Same physical file consumed by all three arms.
- **Separate external audit, independently executed:** original ZIP downloaded and SHA verified; every ZIP CRC; extracted installed wheel Reader SHA; a standalone stdlib+system-libzstd+MessagePack parser decompressed both equal signed r24 indexes, checked index SHA, 4,096 BHDR CRC32/SHA256 owners, regenerated SHAKE bytes and the full logical digest, reconstructed every query answer, recomputed all 54 raw-process medians and every decision with **zero discrepancy**. Audit JSON SHA-256 `029b1cc9f0a5a4d2bea231414e66022bb989e905da12239db0a64a8366969615`. This check does not import CMPCT or either J24C22 evaluator. Earlier independent offline reconstruction using ctypes/libzstd + msgpack regenerated the identical 17,072,796-byte signed archive SHA before inspecting trial timings.

## Measured installed Reader sessions

**Median complete in-process wall times (ms), six genuinely separate subprocesses per arm/shape; lower is better.** Open+list+all reads+close, not process startup. Raw CPU medians independently agree with each disposition.

| Exactly identical signed input / operation | Released v0.30 | Unsafe fused #662 | Sealed #676 | Sealed / released | Frozen material gain? |
|---|---:|---:|---:|---:|---|
| Q1 early, single 8KiB | **1.816** | 2.001 | 1.987 | 1.094× (9.4% slower) | Q1 control, **no >=3ms veto** |
| Q16 front, 16×1MiB = 16MiB, 4,096 owners | 44.151 | **41.680** | 42.005 | 0.95138× (4.86% faster) | **NO**: only -2.146ms and <5% |
| Q16 tail, 16×1MiB = 16MiB, 4,096 owners | 48.674 | 41.662 | **41.611** | 0.85490× (14.51% faster) | **YES**: -7.063ms and >=5%+3ms both wall+CPU |

Phase decomposition (medians, ms): published front open **1.741**, read **23.739** versus sealed open **1.899**, read **21.366**; published tail open **1.738**, read **28.256** versus sealed open **1.895**, read **21.017**. The full suite retains absolute work: each full-owner Q16 reads/returns **16MiB**, and Reader decode/copy remains dominant. The sealed/published ratio for CPU: front **0.951404**, tail **0.854998**, Q1 **1.094271**. Six of six per-repetition matched wall comparisons favored sealed on each Q16, but that does **not** erase front's failed preregistered materiality threshold. All six Q1 early processes favored published. RSS research debt >8MiB **did not trip**; coarse process peak RSS is not a transient allocation or I/O trace.

Independent and hosted conclusion: **`FULL_OWNER_PARTIAL_TRANSFER`**. The win is specific to **tail-biased 16MiB full-owner reads**, not material on front-biased reads. This is *not* a general 4–49× performance statement. The previous J24C21 broad-physical wording is further narrowed; its separate Q32 selective win remains real for its own narrower workset.

## Causal control and surprising structural property

The owner map `(i*2053+17)%4096` is a full permutation because `gcd(2053,4096)=1`; each contiguous 4,096-reference half touches all 4,096 unique owners. In fact the two halves are periodic copies, yielding the **same exact 16MiB decoded byte stream and SHA256 `3b59311629871889a631f35d07da124fb64d237e0209e580a1f66c18b7f07323`**. Their only deliberate difference is the **logical start position** and consequently the published Reader's prefix walk.

From the **actual published** `S_CHUNKS` read loop (`p=0`, visit each ref until end), 16 aligned 1MiB ranges imply the following source-derived reference-visit counts, independent of timing:
- Q16 front: `256 * (1+...+16) = 34,816` visits;
- Q16 tail: `16*4096 + 34,816 = 100,352` visits;
- sealed checkpoint path, 256-ref aligned anchors: **4,096** descriptor visits in either case, plus one-time O(N) native admission and tuple conversion at open.

The additional **65,536** baseline prefix visits for tail relative to front explain why full physical bytes can be identical yet late windows yield a material incremental win. These counts are a derivation from the shipped loop; they are not measured CPU instructions, disk bytes or cache misses.

## Strongest negative and scientific restraint

- **Front failed the preregistered combined 5% AND 3ms gate in both CPU and wall**. Its observed 4.86% gain is real in six repeated matched observations but is not a material transferable win under the frozen standard.
- Q1 on this 8k-reference profile adds only ~0.171ms and does not meet the 3ms joint veto; **the previously observed severe 262k Q1 regression (+179% / +7.312ms in J24C21) is still a promotion veto**, not waived by this narrower control.
- This is a warm, regular, synthetic RAW owner population of only 16MiB, not independent cold disk-cache profiling, heterogeneous codecs, CDC, full extraction, recovery or whole-product gains. Physical unique payload bytes != measured physical I/O.
- Different historical Readers do **not** have identical hostile-archive semantics. Signed valid file comparison measures normal economics only; original #662 retains the demonstrated mutable-public-refs wrong-byte counterexample, and #676 retains possible public list-to-tuple compatibility debt and nonindexed mutable blob records.
- Only Ubuntu CPython 3.11 was measured. No Windows/macOS/Android/native Rust implementation or full frozen release matrix was executed. No product integration is justified.

## PARETOBONK / counterfactual / coordination

**Primary science decision changed:** J24C21's “large-owner selected Qmany” research headroom narrows to **late-position full-owner** when the entire 16MiB actual distinct-owner population is decoded. It does not extend to equally broad early-position work. The simplest published control wins the early Q1 and remains the shipping baseline.

The counterfactual earlier discriminator was a static cardinality/projection check of physical owner touches plus an early-versus-late fully matched byte-stream comparison. Both were prospectively detectable from the original fixture mapping. Preserve this lesson as **local prospective evidence-design guidance**, not an unearned normative Discovery Engine policy rewrite.

No collision with #662/#676 Reader owner, #574 Discovery state, #690 signed negative-length extract, #255/#270/#573 sparse, #691 MessagePack or #683/#685 representation. This branch only adds independent research/CI/documentation; it never rewrites the original #687, product, frozen tests or comparator. `docs/discovery/STATE.json` remains untouched and staleable.

**Highest-value next safe fork:** assess whether any proposed Reader ownership architecture can keep signed exact validation while avoiding Q1 upfront cost, or change the on-disk/reader proof architecture if existing O(N) semantic admission cannot meet selective one-shot reads. Do not resume saturated Python tuple-conversion variants (#679/#682). Orthogonal existing released-P0 safety work may deserve priority over more narrow checkpoint optimization. A material code proposal still requires stronger full-product correctness, public API, portability, hostile input, RSS and promotion evidence.

## Exact-head CI boundary

This research result was obtained from source HEAD `c37758d428f6cce18facb1ac82361cdae87feccd` in GitHub Actions run `40738454008`, not from the present documentation HEAD. Version Discipline, CI Topology and R36 attribution were SUCCESS on the measured HEAD; Engineering Evidence initially FAILED solely because the PR description lacked mandatory dossier section headings. The PR description was subsequently expanded with those headings; a later exact-head run must be checked, not inferred. Generic suite CI on the measured HEAD is not declared green until verified. This documentation commit triggers a new head, so **no exact-head hosted completion is claimed for the final documentation SHA until observed**. No merge/release and no version/format change.
