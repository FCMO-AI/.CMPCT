# O227 — operation-local physical-owner scatter: charged authentic result

Date: 2026-10-27 UTC. **Prospective decision: `NO_MATERIAL_HEADROOM` — RETIRE this scatter implementation family.** No Reader/product promotion. Parent/preregister freeze `f34fe69211fe07e09a368fda9ade7c7233a77520`, before instrument commit `774d4fddd6aa6699406fb64c0881c6f614d26112`. Source-exact hosted scientific HEAD `8c4e913d014ef7a38377f252c46ca79fe4afe462`.

## Original evidence and independent audit
[GitHub Actions run #40506643323](https://github.com/FCMO-AI/.CMPCT/actions/runs/40506643323) **SUCCESS**, artifact [#12734384684](https://github.com/FCMO-AI/.CMPCT/actions/runs/40506643323/artifacts/12734384684). Original artifact ZIP SHA-256 `008b7eac49010e75087ac389ea02cb95c2ddd5ff88ee5289c503f99bd8bca7f5`; `results.json` SHA-256 `a1c12d129a464d16a5812cb15db3c13d8c006e4a9d7df9f07e9fe416987600e7`. Source `Reader` original Git blob `dbd4ac576a05a47eae97e1e40de89cf1de440516` retained unchanged, from owner #569. The court installed CMPCT outside checkout, validated installed-source byte equivalence, used authenticated Builder-independent wire revision-24 fixtures, source-bound preflight, Reader.verify, same-wire A/B.

The stand-alone second-root auditor `research/o227_independent_owner_scatter_audit.py` reported **PASS** over 108 samples/108 fresh child processes, six SHA-positive mixed-codec cases, six physically referenced corrupt-CRC rejects, 2,000 randomized independent range controls and three deliberately mutated evidence receipts independently rejected. A separate out-of-repository independent auditor downloaded the original provider artifact and revalidated its SHA/ZIP CRC, HEAD, receipt hash, sample identities and fresh PID cardinality, regrouped medians from raw rows and reproduced the frozen verdict (PASS).

## Measured authenticated complete-session medians
All values are **milliseconds**, Ubuntu 24.04 / CPython 3.12, including Reader.open, full reconstruction and Reader.close. Full-session CPU criterion is shown as fastest-control CPU divided by scatter CPU. `ratio` is **fastest of original eager and serial** divided by scatter; >1 means scatter faster. `RSS+` is candidate own VmHWM minus *lower* of controls (MiB). Negative/marginal cells remain intact.

| Family | Storage | Eager | Serial | Scatter | Wall ratio | CPU ratio | RSS+ |
|---|---|---:|---:|---:|---:|---:|---:|
| Zstd entropy twice | fixed | 145.357 | 147.631 | 124.590 | 1.167× | 1.185× | +5.883 |
| Zstd entropy twice | CDC | 146.363 | 146.763 | 124.304 | 1.178× | 1.181× | +5.949 |
| Deflate entropy twice | fixed | 147.546 | 146.027 | 124.298 | 1.175× | 1.175× | +6.027 |
| Deflate entropy twice | CDC | 149.049 | 146.117 | 123.820 | **1.180×** | 1.180× | +5.965 |
| Zstd patterned twice | fixed | 127.498 | 137.586 | 117.833 | 1.082× | 1.168× | +6.137 |
| Zstd patterned twice | CDC | 128.098 | 137.994 | 117.670 | 1.089× | 1.173× | +6.176 |
| Deflate patterned twice | fixed | 131.624 | 140.678 | 118.643 | 1.109× | 1.186× | +6.102 |
| Deflate patterned twice | CDC | 132.630 | 139.696 | 118.518 | 1.119× | 1.179× | +5.938 |
| Zstd entropy once | fixed | 82.930 | 77.687 | 75.225 | 1.033× | 1.033× | +5.922 |
| Zstd entropy once | CDC | 83.034 | 77.668 | 75.054 | 1.035× | 1.035× | +6.145 |
| Deflate entropy once | fixed | 84.912 | 77.564 | 74.296 | 1.044× | 1.044× | +5.867 |
| Deflate entropy once | CDC | 82.395 | 77.242 | 74.533 | 1.036× | 1.037× | +6.039 |

**Preregistered scientific gate:** >=1.20x simultaneous full-session wall and CPU versus BOTH eager and serial on at least 2 reused cells. **Result: ZERO/8 reused cells** pass. Wall maximum `1.18008×`, CPU maximum `1.18568×`; original oracle already reported `NO_MATERIAL_HEADROOM`, confirmed independently. Even though some wall gains reach ~18%, they are not promotion/science acceptance under this frozen question.

**Exported-cost gates:** none of four once-only cells shows >10% wall regression; own process RSS delta +5.867 to +6.176 MiB stays below +8 MiB. This bounds the *measured* debt without converting a subthreshold result into a product win. Ordinary Reader accepts exactly the same valid fixtures and rejects the six hostile physical CRC controls. All rebuilt bytes and SHA match.

## Causal explanation and negative
The operation-local scatter adaptation converts one authenticated logical reference sequence into postings indexed by physical owner and calls the inherited decoder only once per unique 3 MiB owner. Reused logical sources avoid half the uncached physical decoded-unit requests (12 instead of 24), but computing postings, materializing a mutable full-sized output, scattering and copying it to an immutable result still costs enough to leave <1.20× advantage versus the strongest inherited comparator. `Reader._blob`'s cache only admits <=2 MiB, so these 3 MiB owners are genuinely outside the cache; the mechanism is not a cached small-block artifact.

A strong simpler control already existed (straight serial), and the original eager Reader was sometimes faster than serial on patterned repeated data. The correct baseline is the **faster** of those two per identical input, not only eager and not a weak synthetic no-validation implementation. The run was not biased toward a winner by changing order, thresholds, codec settings, source, output integrity or benchmark borders after observing results.

**Additional independent causal decomposition (same immutable original samples):** recomputing READ-ONLY medians from the 108 source-exact receipts shows the best-control/read-scatter ratio also remains subthreshold in every cell: largest \`1.1821×\` (Deflate entropy twice / CDC), versus the identical 1.20× prospective materiality requirement. The observed complete-session negative is therefore **not solely an artifact of the ~1.3–1.9 ms Reader.open baseline** diluting an otherwise qualifying read-only win. No new measurements, workload or acceptance changes were introduced for this calculation.\n\n## Counterfactual discriminator and next allocation
Before a future similar experiment, charge the immutable-output copy separately and compare against actual strongest inherited serial/eager control. A nominal factor-of-two reduction in physical decode requests does not imply a 1.20× full-session gain; both output movement and hashing dominate some cells. This discriminator is prospective, transferable to owner-fanout and other materialization architectures; do not treat it as a self-modification of Discovery Engine policy from one run.

Retire this particular `physical-owner scatter` family as an independent Reader candidate. Preserve as bounded O0/O1 research, not product. The only credible reopening would remove a measured complete-output copy/retained metadata boundary or materially different output representation, with new independent benchmarks and memory/read semantics. Otherwise highest-value work moves to #569's structural validation/open regression and existing extraction/recovery correctness PRs (#572/#582/#528), preserving released v0.30.0/r24 and strict publication law.

## Validity, portability and release debt
This is Ubuntu/Python3.12 exact Reader science, not a three-host/4 GiB/native/XATTR/case-alias/recovery/ZIP64 result. The experiment cannot establish global compression ratio, create throughput, cold list/read, random access, selective I/O, failure recovery, multi-platform binary ABI or complete official release parity. No change to Builder, Writer, Reader, codecs, checksums, archive bytes, native core, frozen evaluators or public website. The scientific runner SUCCESS does not imply `CMPCT General Tests` passed; exact-head CI is separate and cannot be inherited from predecessor release.

**Decision: `NO_MATERIAL_HEADROOM`. No merge, no release and no numeric version.**
