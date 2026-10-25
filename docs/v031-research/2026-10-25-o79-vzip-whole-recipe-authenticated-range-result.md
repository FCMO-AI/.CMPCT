# O79 result — original complete-recipe SHA as a fast verified VZIP range proof

Date: 2026-10-25
Status: **SCIENTIFIC HEADROOM CONFIRMED, PRODUCT UNCHANGED, NO MERGE/RELEASE**
Last materially updated: 2026-10-25

## Source and prospective custody
- Preregistered BEFORE instrument and measurements: `5dcb373565c84bba10a859ab1efb974eed2005e5`, [frozen hypothesis](2026-10-25-o79-vzip-whole-recipe-authenticated-range-prereg.md).
- Original result-bearing source: `ddcc723dc497f931e8cc1e130f52323f8bc162e3`, standalone installed-product GitHub Actions [run 40190864002](https://github.com/FCMO-AI/.CMPCT/actions/runs/40190864002), **SUCCESS** (actual test job, not administrative workflow green).
- Original uploaded [artifact 12598101341](https://github.com/FCMO-AI/.CMPCT/actions/runs/40190864002/artifacts/12598101341), ZIP SHA-256 `188746575365007f8ee5dab0cea82d8f1217eb49e268866fb864be87fd4ace2c`. Contains `o79-evidence.json` and `o79-run.log`, independently inspected by a separate raw-JSON consumer with SHA, sample-length and mutated rejection checks.
- Parent O76 exact source `d654c54da1a0351721318f1d365b45e54ae232d7`; authentic unchanged Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`, Reader `e716233403dabd0966863c45635e18fa5ac6afb8`, Codec `29526db4203723d83523fc95d074c346b63d7587`.
- Actual installed CMPCT checked outside checkout under CPython 3.11 / Ubuntu 24.04. Format r24 and published v0.30.0 unchanged.

## Mechanism and proof scope
The signed/index-hash-protected VZIP recipe already includes the SHA-256 of the original *physical ZIP byte sequence*. On mode-0 retained Deflate, the compressed stream is exactly the original stream and is recoverable directly. A standalone research function copies every original compressed segment and the reconstruction skeleton once, checks exact total length and whole logical ZIP SHA-256 **before returning selected copied bytes**. It authenticates the entire virtual ZIP without inflating/recompressing the 2–8 MiB expanded Deflate contents. More bytes of compressed ZIP are hashed than the selected 64-byte range; this is **not sublinear-range work**. This is integrity against accidental/physical corruption given trusted index metadata, NOT a digital signature authenticating who created the archive. Full independent `verify()`, `read()` and selected-range originals pass on both arms.

## Hosted original result — 6 fresh-reader samples per arm, each case
| Source family | Mode2 regular median 64B wall | Mode0 whole-SHA median 64B wall | Verified speed ratio | Mode0 unchecked (weaker control) | Mode2/mode0 complete archive bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2 MiB repeated | 10,674.49 µs | 38.69 µs | **275.884×** | 25.21 µs | 1,278 / 3,281 (+2,003 B) |
| 8 MiB periodic | 39,757.79 µs | 56.30 µs | **706.171×** | 28.14 µs | 2,246 / 34,101 (+31,855 B) |
| 2 MiB mixed entropy | 10,340.57 µs | 60.94 µs | **169.687×** | 28.46 µs | 34,424 / 39,141 (+4,717 B) |
| 2 MiB independent random | 106.74 µs (both mode0) | 1,449.70 µs | **0.074× — NEGATIVE** | 105.82 µs | 2,099,021 / 2,099,021 (+0 B) |

These are medians on a single warm-hosted Ubuntu runner with separate fresh Readers per call (open/startup excluded from timing). They are not repeat-independent hardware estimates, cold disk throughput, complete create/extract product benchmarks, or release measurements. Full CPU/wall raw samples, complete archive SHA, physical bytes and source SHA remain in the original receipt. The random control is a genuine unfavorable result: hashing a ~2 MiB original compressed stream instead of returning a 64-byte unchecked slice is materially slower. An admission model must select when a verified proof is worth that scanning cost and cannot silently make unchecked normal ranges an equal-strength control.

## Adversarial result and scientific decision
Each of the four source cases had **three independent corrupted-CMPCT copies**, physically flipping one stored byte in the selected Deflate stream, in another part of that same compressed stream, and in the skeleton. On all **12/12** such mutated inputs, the SHA-verified oracle refused the selected range without returning silently wrong bytes. For the three eligible mode2 cases, existing `CMPCT.read_range` also rejected a separate true mode2 CRC-flipped blob — **3/3 positive comparator controls**. The original mode0 unchecked code can still return data from a corrupted file: its historical weakness is preserved, not hidden.

The prospective test (≥2 structurally different eligible families ≥8× SHA-verified read advantage at ≤64 KiB complete archive byte debt and fail-closed selected/out-of-selected corruption) is **PASSED, scientific tier**. Three eligible families exceed it; no threshold, input or historical result was changed. The original clean-archive O76 magnitude (265–1064× without SHA) is NOT misrepresented as this stronger, slower but still significant verified claim.

## Strongest negative and self-critique
- SHA authentication is over *all physical ZIP bytes* in the recipe, so random/incompressible ZIPs and many-member/large ZIPs can lose significantly; 2MiB random shows 13.6× slower than its original unchecked range.
- Mode2 requires costly recompression when present; the fast proof is only viable for truly retained streams. No adaptive product admission, shared-member reuse or mixed ZIP topology is proven in this original one-member experiment.
- The general Reader's `S_BLOB/CODEC_RAW` path remains a separate known weaker range tier owned by other work; O79 does not repair it.
- A mutable underlying mmap can change over time; copying parts once binds the output to what was hashed during this call, but a live filesystem mutation during segment collection could cause read inconsistency/rejection, not a transactionally immutable archive or source snapshot.
- No full product size/create/extract/reader complexity tradeoff, peak native RSS, actual physical I/O, other OS/platform, corrupt-index signing, official parity, packaging or release gate is credited.

## Counterfactual and next actionable question
O76b's cheapest early negative was a one-byte corruption flip. Instead of adding new per-chunk integrity metadata as an initial solution, inspecting the existing VZIP recipe's original full ZIP SHA would have identified a smaller existing-source proof path immediately: **reuse authenticated reconstruction identity before inventing additional proof machinery**. The discriminator was prospective and transferable. No Discovery Engine policy edit is earned from one example.

The next cheapest high-value falsifier is a genuinely different *multi-member* VZIP with mixed STORED and Deflate streams, corruption only in an **unselected different member**, and an honest accounting of whether whole-recipe scanning is still affordable. Then consider owner-reviewed opt-in, explicitly SHA-verified range semantics and generic admission; any such product must pass source-lifetime adversaries and exact-head release/portability gates. No merge/format/release.
