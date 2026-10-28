# J24G20 — cold signed Reader RSS floor: result and causal resolution

**Date:** 2026-10-28 UTC. **State:** decisive scientific result; DRAFT, research-only, no product merge/version/format/release credit. **Primary owner:** J24G20 [PR #694](https://github.com/FCMO-AI/.CMPCT/pull/694), independent child of J24G19 [#691](https://github.com/FCMO-AI/.CMPCT/pull/691) at exact `e15553bf409f4bb3b339af2ec1af83062af2926a`. Published Reader v0.30.0 / revision24 at `80c358f8824ec1b20d349c92ed94c898090969b0`, blob `e716233403dabd0966863c45635e18fa5ac6afb8`; inherited and projected experiment source keeps Reader blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b` unchanged.

## Question, preregistration, evidence

J24G19 #691 reported *the same process-wide ru_maxrss* (68,912 KiB) for a tiny checkpoint and a signed 200,000-object delta, across both original and projected Readers. The J24G19 original **>=16MiB 200k RSS hypothesis did not pass that hosted measurement and remains an honest historical negative**.

The prospective J24G20 question was whether a new fresh-worker, **stage-separated VmHWM** comparison would distinguish the true full-Reader temporary allocation from an inherited process peak, and if a large 800k authenticated delta would save >=16MiB. No inference of benefit was permitted from the component alone. Preregistered at `f2ea80858d5042a9c8a640f8455db64488e8e6c2` **before new instrument/results**, no threshold changes.

- [First hosted source-exact court #40744100635](https://github.com/FCMO-AI/.CMPCT/actions/runs/40744100635), instrument/head `c82cff4046ff2d6f93b71bce491affb8f084ff54`, **SUCCESS**, original ZIP artifact `12839809203`, SHA256 `a81d1093f255db5c8c6bc2ee6d74a6cc9d7b97944d344ad9454f21f3d2678af6`.
- [Independent causal replay and repeated court #40745030939](https://github.com/FCMO-AI/.CMPCT/actions/runs/40745030939), exact code/head `b615a453a1ed060543f884e2b8cbb3f8b75bf4cc`, **SUCCESS**, ZIP artifact `12841906110`, SHA256 `35a77912c6e40bf0f57f8f9237e179f7102db91bf1d31f30251139e3f930cef1`.
- Both Ubuntu 24.04, Python 3.11.17, msgpack 1.1.2. Three fresh workers per arm/case; all arms receive the **identical physical archive** within an execution. Physical r24 Builder/Writer checkpoint and exact SHA-signed linked deltas with 200k, 400k and 800k repeated small objects. Full `CMPCT()`, `read`, `read_range`, `verify`, footer position and SHA agree across actual published historical Reader, inherited parent, and research projected Reader. Reader/Builder/Writer are unchanged. Components imported before measured Reader open.

## Product-context physical Reader measurements (not released product)

Median **final process VmHWM in KiB**, original head `c82cff40`:

| Authenticated input | Published actual | Inherited #691 | Projected research |
|---|---:|---:|---:|
| Small checkpoint | 26,504 | 23,928 | 23,824 |
| Linked, 200k objects | 66,728 | 64,736 | **25,608** |
| Linked, 400k objects | 107,052 | 105,028 | **27,932** |
| Linked, 800k objects | 187,312 | 185,208 | **29,648** |

At 800k, the projected candidate reduces median **absolute peak HWM by 157,664 KiB (~154 MiB)** versus published and **155,560 KiB** versus inherited. It also reduces the 200k peak by **41,120 KiB** versus published. Source data preserve all three raw repeated CPU and memory samples; 800k same-run median full-open/read/verify CPU is 118.619 ms published vs 12.297 ms projected, **~9.65x speedup for this one synthetic regime**. Actual physical 800k archive = **3,201,088 bytes**, authenticated delta = **3,200,055 bytes**. This is no compression/complete-product domination claim.

Independent **repeat** at `b615a453` measured published/parent/projected HWM **187,204 / 185,024 / 29,488 KiB** on 800k, giving savings **157,716 / 155,536 KiB**; on 200k, **66,736 / 64,616 / 25,628 KiB**. In the repeat 800k CPU was 168.341 ms published vs 20.108 ms candidate. *Absolute times varied across runs; compare only matched same-run/same-host samples.* Both runs satisfy the original >=16 MiB **800k prospective** discriminator.

### Contradiction resolved: `ru_maxrss` can inherit supervisor high water

After obtaining the first physical result, an **independent post-result** 70-MiB allocation/fork-or-spawn control targeted the unexplained old HWM. It is an explanatory falsifier, **not part of frozen H2**.

On exact-head hosted Ubuntu/Python 3.11, the parent intentionally touched 70 MiB, then freed it: parent `VmRSS` fell back to **15,940 KiB** while `ru_maxrss` remained **87,568 KiB**. Three ordinary `subprocess.run` children each showed fresh `/proc/self/status` `VmHWM` around **10,800–10,916 KiB**, but **all returned `resource.ru_maxrss=87,568 KiB`**, inheriting the parent's earlier high water. Forcing fork+exec via `preexec_fn` produced fresh child `ru_maxrss` approximately **10,712–10,924 KiB**, matching physical child HWM. A separate CPython3.13 local control showed the same qualitative result.

That reproduces the mechanism of an **instrumentation contamination**, and source inspection of J24G19 shows it constructed the 200k metadata in the supervisor and recorded only `ru_maxrss` in the child. It strongly explains J24G19's equal 68,912-KiB figures. The earlier measurement was **not evidence of zero candidate incremental savings**, but its reported historical H2 result must not be retrospectively rewritten or counted as a success.

For contrast, in first J24G20 hosted run published at 800k `after_open VmRSS` was **28,768 KiB** while its **transient VmHWM** was **187,312 KiB**. Measuring retained after-open RSS alone also misses large temporary allocations.

## Independent referee and negatives

A completely separate external auditor (stdlib + system libzstd + msgpack, no CMPCT import or certificate) downloaded first ZIP, reconstructed the physical checkpoint index and its Zstd blob, checked SHA256 + CRC32 + all physical r24 signed footer hashes and exact MessagePack payloads, every original Reader observation, and rederived CPU/HWM medians and hypothesis. **690/690 checks PASS**, plus five deliberately falsified receipts independently rejected (wrong member SHA, wrong selected footer, forged RSS median, falsified saving, forged payload SHA).

Research scope remains limited: only one repetitive certifiable ignored-field shape; threshold on new 800k does not revise prior 200k requirement; C code dependency and subset scanner are not generally guaranteed portable; synthetic large metadata does not establish benefit on natural representative archives; fallback must preserve *all* original accepted MessagePack semantics; global memory/bounded resource guarantees are not established. Normal tiny-checkpoint median HWM was close to baseline and only modest CPU overhead observed, but full heterogeneous load economics, updates and platform gates are **unmeasured**.

## Decision, counterfactual and handoff

**Primary decision changed:** reject the old inference that certificate/projection lacks RSS potential; retain certified ignored-field projection as a credible **research seed with genuine physically measured temporary-memory savings**. Investigate native deployment and generality before proposing product change. Do not merge or grant v0.31/1.0 credit.

**Prospective discriminator:** for any experiment whose controller constructs large objects before child launch, collect a fresh **child VmHWM snapshot before and after the measured phase** and compare with `ru_maxrss`. This simple first-principles process-memory control would have identified the J24G19 false negative a cycle earlier. That is a **transferable method lesson** backed by independent hosted causality; change no Discovery Engine policy or benchmark gate here. Another agent owns stale `docs/discovery/STATE.json` at #574; preserve ownership.

**Next cheapest executable product fork:** certify/skip large *natural* ignored metadata in heterogeneous real revision-24 archives under fully charged native dependency + memory/CPU, then prove Windows/macOS and accepted-malformed/duplicate-key fallback; compare simpler direct full decode on small cases. If common metadata never benefits enough, retire default integration and preserve J24G20 as a scoped structural proof. Other independent candidate lanes (e.g. #692/693 signed hardlink/extraction safety) remain unaffected.

**CI truth:** specialized two exact source heads **SUCCESS**. At the time of this scientific record, final post-record HEAD CI has not yet run; check GitHub on its exact final SHA, and do not claim general tests are green until measured. No product mutation, no format change, merge NO, release NO.
