# O68 — Source-exact VZIP inflation economics: decisive hosted result

**Research conclusion:** `HIGH_RATIO_VZIP_DOMINATED_BY_OPAQUE_ON_TESTED_SYNTHETIC_FAMILY`. This is a **bounded research result**, NOT a general admission policy, release gate, product fix, or claim that all nested ZIPs should use opaque fallback.

## Exact input/source/evidence custody

- Prospective preregistration committed **before any instrument/results** at `abc4647d628939808278742712f490723fd7cda4`.
- Real product code parent O63 #418: `18e32cae012f5dca9fc47f10d194f8b81005c85c`.
- O63 Builder unchanged: blob `382e60983bf1e8e7595ea7112f3a5553dc33dcc0`.
- O63 codec unchanged: blob `dc3446b0eed82edfba9380e3885a20aa45577899`.
- Executable research HEAD: `204d615a426744c7523d7bfc565982f9af77161f`.
- [GitHub Actions #40175612000](https://github.com/FCMO-AI/.CMPCT/actions/runs/40175612000), Ubuntu 24.04, CPython 3.11, independently installed real CMPCT, 18 actual subprocess observations, all source hashes and r24 verification assertions PASS.
- [Raw artifact #12591853607](https://github.com/FCMO-AI/.CMPCT/actions/runs/40175612000/artifacts/12591853607), ZIP digest `sha256:4fa24b67227f3af28de8de3ddc79ad5483dc77b659fdd4cee73f05a2dbc5ccdc`. Contains `o68-raw.json` with **each** observation (not only medians), experimental log, source SHA and product/source/instrument Git blobs. JUnit was not required; CI expressly asserts 18 actual data points and complete output.
- The sole source member is a real deterministic Deflate ZIP, with fixed 1980 member timestamp and repeated letter payload; all same-tree observations use identical physical ZIP and SHA. Full archive output differs only by existing VZIP vs test-only forced opaque fallback. Strong `CMPCT.read` and `CMPCT.verify` passed in each arm and observation.

## Measured real complete-Builder results

Wall and CPU intervals include `Builder.build()` but **exclude** process startup. Each median comes from three fresh processes for each arm on an identical source; 18 observations total. Opaque is a research oracle, not an independently released engine. Real installed O63 virtual candidates produced actual `S_VZIP`, oracle produced actual `S_BLOB`. No frozen benchmark, comparator or evaluator was changed.

| Inner logical bytes | Physical ZIP bytes | Input expansion | VZIP median create CPU | Opaque median create CPU | CPU ratio | Complete VZIP archive | Complete opaque archive | VZIP byte debt |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 65,536 | 211 | 310.6x | 2.327511 ms | 0.506662 ms | 4.59x | 1,200 B | 980 B | **+220 B** |
| 4,194,304 | 4,213 | 995.6x | 45.874919 ms | 0.694097 ms | **66.09x** | 1,357 B | 982 B | **+375 B** |
| 16,777,216 | 16,443 | 1,020.3x | 162.981331 ms | 0.975314 ms | **167.11x** | 1,736 B | 1,034 B | **+702 B** |

The 16 MiB case also measured VZIP/opaque wall 162.980072/0.980053 ms. Runtime CPU was almost all on-CPU in this family. The result is **strictly dominated on both complete archive bytes and Builder CPU** by the simpler existing opaque control on all three chosen inputs. This confirms the prospective primary CPU-ratio hypothesis in the larger cases and strengthens it with a simultaneous real complete-archive byte loss.

## Causal scope and strongest negative critique

The O63 codec explicitly `z.read(zi)` fully expands every member, then `deflate_level_for(raw,stream)` recompresses the expanded payload at candidate levels until an exact stream match. A detached same-stdlib 16 MiB micro check separately measured about 38 ms ZIP decode plus 109 ms first-four-level recompression (on a different host); it supports causal plausibility, not a measured exact function-level attribution inside the hosted Builder. No profiler segregated each component in O68.

The synthetic fixture uses long runs of identical bytes, which substantially favors both ZIP input compressibility and Zstd opaque re-compression. Real documents, wheels and heterogeneous ZIPs may behave differently; a heuristic that merely rejects highly compressible ZIPs could lose legitimate VZIP wins. Research CI did **not** measure extraction CPU, memory allocation traces, nested ZIP byte-level random access, mixed-container batches, portable Windows/macOS economy, malformed ZIP or all Builder resource limits. The raw file contains per-process max RSS but this document does not claim a meaningful causal RSS delta from three trials.

Most important: the opaque arm is a **test-only selector** (monkeypatched `make_vzip_recipe` entrypoint returning `None`), not the original product and not an acceptable silent policy change. Only source-bound work/bytes within the tested family are demonstrated.

## Decision and next cheapest independent discriminator

**Scientific decision changed:** A valid high-inflation nested ZIP family has measured **negative** material VZIP admission value, not merely CPU debt. A bounded prospective selective-admission question is warranted. Strong candidate frame: use cheap, authenticated physical ZIP/candidate statistics to decide whether to spend large decoded/recompression work; require a held-out suite of structurally different ZIPs showing any admission shortcut preserves verified VZIP wins, complete archive bytes and source semantics. A metadata-only `ZipInfo.file_size` ceiling without validating declared-vs-actual content is insufficient as a general security proof. The expected cost of rejecting a beneficial family must be included.

**Counterfactual:** One 4 MiB valid high-ratio ZIP, tested with the same-tree opaque control *before building a 15-row matrix*, was enough to reveal the decisive 66x CPU and 375-B complete-archive loss. The prospective observable is member expansion ratio paired with physically measured opaque bytes, not a retrospective hand-tuned threshold. No discovery-policy mutation is earned from one synthetic family.

**Ownership:** Product VZIP/fallback belongs to O63 #418; its O67 #423 economic owner remains independent. This branch modifies no O63/other product code and will pass results to its owners. O68 remains DRAFT and cannot authorize merge or release.
