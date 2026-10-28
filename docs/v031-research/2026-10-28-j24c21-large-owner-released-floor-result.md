# J24C21 — source-exact large physical owner floor: hosted result and independent audit

**2026-10-28 UTC. DRAFT SCIENCE, NOT MERGED / RELEASED / PROMOTED.** Prospective [preregistration](2026-10-28-j24c21-large-owner-released-floor-prereg.md) was committed at `414cad71702528abd34a2a4b94785aadb2d70105` **before** instrument implementation `48b0c23ad223c4ff3eb86e0e75a31a54b5510304`, independent referee `36051f3d10523144e8ba0f46bf025e60d3c85fa5`, and the measured evidence-head `99441bdf3f000ad1db634076bc780349b6af13a8`. Historical sources were read from exactly pinned SHAs, installed noneditable as separate wheels. All comparisons consume the same signed, deterministic RAW revision-24 archive for a given profile; no Builder-generated artifacts or data regeneration per control.

## Direct installed evidence: source-exact successful scientific court

- [Hosted original exact-head run #40730019573](https://github.com/FCMO-AI/.CMPCT/actions/runs/40730019573): **SUCCESS** (Ubuntu 24.04, CPython 3.11) on `99441bdf3f000ad1db634076bc780349b6af13a8`.
- [Original GitHub Actions artifact #12833769309](https://github.com/FCMO-AI/.CMPCT/actions/runs/40730019573/artifacts/12833769309), ZIP SHA-256 **`d6fdec8119bf1d84847070a582a3da9dd7212bffd141478234a061742d7009ae`**, original file IDs, 3 installed wheels, signed archives, manifest, raw 162 processes, first-party referee and decision receipt.
- Historical comparator source commits: published `80c358f8824ec1b20d349c92ed94c898090969b0`; unsafe fused #662 `a66fd593a83cc4c71556d3d86d835c51abd20a96`; corrected sealed #676 `3b6a73f9205f40f11124cd9ff332407e52cebb93`. Installed Reader SHA-256 respectively `83be3f08f7fafb1fd638fda6140bbe1af6676c261be10acc9ea8f8b633beefff`, `b9d7c86d021f26a252d2d8cb4d2ba6cbf4613b9fb743abf1a8264a2343a4ecfe`, and `ccb5dfcd45bbef16c880a85b2f66cd91a8b48fa5f42ddab8c506205404f66a5b`.
- **Independent artifact audit:** downloaded exact original ZIP; SHA-256 matched GitHub artifact; ZIP CRCs passed; each installed wheel's actual `cmpct/reader.py` SHA-256 matched the receipts; an external Python 3.13 verifier using **independent MessagePack parsing, system libzstd through ctypes, hand-unpacked r24 header/footer/BHDR, direct physical CRC32 and SHA-256 and deterministic SHAKE owner reconstruction** verified all 3 archives, all 3 logical SHA-256 digests, all 117 expected query digests, and recomputed every per-arm/profile median from all 162 raw process records. **Zero discrepancies.** This external audit does not import CMPCT's Builder, Reader, fixture generator or referee.
- The repository's independent hosted referee additionally rejected **7/7 altered receipts** and produced research decision `RETAIN_Q6_LARGE_OWNER`. Its raw observations, not this summary, are authoritative.

## Valid signed-archive identities and owner charge

| Synthetic input | Logical bytes | Physical RAW payload bytes | Stored r24 bytes | Archive SHA-256 |
|---|---:|---:|---:|---|
| 65,536 × 1-byte refs, 2 owners | 65,536 | 2 | 556 | `6b0f7fbf5434bf0c007359d0b2beb567b11d7fd4517da944c42bf8174446eec5` |
| 262,144 × 4KiB refs, 2 owners | 1,073,741,824 | 8,192 | 8,812 | `09b60f510f553d1d720d86e69fe58e8b5560dfdce2b2b989d7056fe5d404e792` |
| 8,192 × 4KiB refs, 4,096 distinct owners | 33,554,432 | 16,777,216 | 17,072,796 | `eb695e0236db6d8d7e7896fcc8d3a2b69a47a66f601e47c8c333879176f58067` |

Distinct external logical SHA-256 values: tiny `6c5795303a9a3445f1996ada35cf59217ca31540ee29dcabe2a724580cc6a545`, repeated large `6eb86eb43ba61cb021c817d859f73e2bbd9ef16aaf1593b33d773781ebc8e32f`, distinct large `f7dae87fe58779221ddffe02540d6ae7ea573eb15127ee9cebac161e47721477`. The 1GiB logical archive contains 8KiB physical RAW payload, so **its speed gain is selective reference traversal evidence**, never general 1GiB physical decoding/compression evidence.

## Session medians; genuine installed execution

All numbers below are **median full in-process session wall milliseconds** (Reader open + enumerate + Q operations + close), six separate processes per arm/shape on one Ubuntu hosted runner. CPU provides near-identical decisions; raw distributions remain in artifact. Lower is better.

| Profile | Regime | Published v0.30.0 | Unsafe fused #662 | Sealed #676 | Sealed / published |
|---|---|---:|---:|---:|---:|
| 65k, 1-byte repeated | Q1 early | 6.963 | 8.389 | 8.744 | 1.256× (loss) |
| 65k, 1-byte repeated | Q6 spread | 38.840 | 30.967 | 31.378 | 0.808× |
| 65k, 1-byte repeated | Q32 spread | 211.192 | 164.319 | 160.686 | 0.761× |
| 262k, 4KiB repeated | Q1 early | 4.085 | 9.808 | 11.397 | **2.790× (veto)** |
| 262k, 4KiB repeated | Q6 spread | 46.841 | 9.839 | 11.498 | **0.245× (4.07× faster)** |
| 262k, 4KiB repeated | Q32 spread | 233.916 | 10.055 | 11.731 | **0.050× (19.94× faster)** |
| 8k refs, 4,096 distinct owners | Q1 early | 2.338 | 2.551 | 2.517 | 1.076× (loss <3ms) |
| 8k refs, 4,096 distinct owners | Q6 spread | 4.185 | 2.722 | 2.662 | 0.636× (absolute -1.52ms) |
| 8k refs, 4,096 distinct owners | Q32 spread | 11.363 | 3.414 | 3.413 | 0.300× (3.33× faster) |

The **preregistered 262k Q6 research threshold passed**: both wall and CPU medians improve by over 5% and over 3ms versus actual published. The early Q1 large-repeated case simultaneously fails the unchanged promotion veto: sealed adds **7.312ms / +179%** versus published (both CPU and wall). This result cannot be averaged with Q6/Q32.

The distinct-owner Q6 improves 36.4% but saves only 1.52ms; a time-sensitive 3ms materiality threshold would not pass on that profile. Distinct-owner Q32 is faster with an absolute 7.95ms saving, showing that the reference traversal mechanism can survive 16MiB independent physical payloads when enough queries reuse the admission work. The 8MiB RSS research-debt threshold did not trip in measured profiles (262k sealed peak ~27.7MiB vs published ~25.7MiB), though peak-RSS telemetry is coarse and does not measure transient allocation accurately.

## Held-out workload bias discovered in post-result adversarial replay

**Important narrower scope:** a new independently calculated physical-owner-touch oracle reveals that the deterministic *spaced* query distribution does **not** exercise the entire 16MiB population of independent owners. For the 8,192-reference/4,096-owner archive, the six Q6 ranges touch **18 distinct 4KiB owners = 73,728 physical payload bytes, 0.44% of the 16MiB stored physical payload**; the 32 Q32 ranges touch **only 32 distinct 4KiB owners = 131,072 physical payload bytes, 0.78%** of the population. The Q32 positions recur modulo the owner-selection permutation, yielding a nonrandom set despite 4,096 different signed archive owners. These quantities are modelled distinct physical *owner references*, **not measured filesystem bytes or cache traffic**. The Q1 range touches 3 owners / 12,288 bytes.

This limits the previously phrased distinct-owner generality: J24C21 validates physical archive size and correct signed answers across a large distinct-owner population, but the **measured read workload is still selective and actually touches only tens of physical owners**. It does **not** establish non-reused physical decode performance on 16MiB of actual reads, general large-file extraction, or broad random-query cache economics. The correct next cheap held-out falsifier would choose a source-independent pseudorandom, nonperiodic query set with explicitly tracked unique physical owner count and physical bytes touched, plus a genuinely broad cold-decode workload; keep the unchanged published floor and all original Q1 negatives. Do not retune original J24C21 queries or count this later oracle as part of its preregistered win. This is a transferable counterfactual lesson: before asserting generality from the size of the signed owner *population*, calculate the actual distinct owner *working set* for the preregistered query workload.

## Decisions and negatives

- **Advance a narrowly scoped performance seed:** reducing repeated fixed-chunk reference walks remains valuable for many late/spread reads on actual large physical owners, including a nonrepeated owner population. Keep no general compression, CDC, Zstd or full extraction performance claim.
- **Retain published-Q1 veto:** exact early reads over 262k refs cost ~2.79× the published Reader. Closing this admission debt without weakening signed semantic validation, and retaining checkpoint speedups, is a required architectural task before promotion.
- **Retain #662 correctness veto:** a mutable public reference list plus cached prefix returned a wrong byte in J24C16. The unsafe control's fast timing cannot authorize it as product. #676 contains that specific issue but introduces list-to-tuple API risk and ~13–24% overhead versus #662 in earlier paired tests.
- **Retire nearby per-element tuple/list tinkering:** #679/#682 are prospectively falsified. A truly different owned index representation or public API boundary merits an independent architectural compatibility proof only after its whole-product economics are defensible.
- **No benchmark/release claims:** synthetic valid RAW indexes, one Linux CPython3.11 host, bounded selective windows. Published v0.30.0 offers weaker hostile-input validation; the three timing arms have different malformed-input trust guarantees. No full release gate, interoperability, native Rust/Android, Windows/macOS or hostile mutation equivalence proved. Stored archive sizes and physical blob bytes were accounted, not optimized by this experiment.

## Concurrency, evaluator and handoff

This is a separate isolated evidence-only branch stacked on #676. No edits to #662, #676, #574, #255/#270/#573, #684/#686 or #683/#685. Discovery STATE is a staleable cache owned by #574 and was not edited. This experiment reinforced the prior prospective lesson that full published Q1 and physical owner costs matter; it does **not** earn a reversible normative discovery-policy change from one run.

The next highest-value safe action is a **contract-only** falsifier of a privately owned validated chunk descriptor with an explicitly reviewed mutable-public-view compatibility boundary: verify the existing aliases `index/files/by` and transaction generation mutations, then derive whether a single immutable native-backed representation can eliminate post-validation O(N) conversion without sacrificing full semantic validation and short-query economics. Alternatively prioritize existing #572 sparse integrity owners to retire a real released-product correctness defect. Do not implement another tuple-first variant before that discriminator.

Original exact-head J24C21 result is SUCCESS. This result note itself is documentation-only; if it changes the PR HEAD, fresh exact-head general CI and additional job status must be checked separately. No merge or release.
