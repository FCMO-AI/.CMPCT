# J24K13 — source-exact single-pass physical VZIP proof: first three-host result

**Evidence date:** 2026-10-28 UTC. **Tier:** research on genuine installed revision-24 Reader; **not** product/release proof. Preregistered at `fb0ecc3beffcfe7f4f7f5cd63e867dffa2e5922a`, before instrument. Parent/source baseline #663 @ `ade56462ba6d2d3d053c4ba546ba9630c937f107`, strict VZIP physical guard inherited from #653. First result-bearing source HEAD **`8459257a7bc65d44b9fdb33548649d9cac9fb58d`**, hosted [J24K13 exact-head science #40669627917](https://github.com/FCMO-AI/.CMPCT/actions/runs/40669627917), all three OS jobs SUCCESS (Ubuntu 24.04, macOS 14, Windows 2022).

## Frozen question and direct observations

Replace #653's Python per-skipped-stream physical-header callback with an inlined physical BHDR check inside the existing logical VZIP offset/output traversal. No Native C, no global projection, no per-session cache, no copy. Control is the same installed signed-safe Reader, not an unchecked surrogate. Source-exact input built with original deterministic Builder. Three balanced fresh-process A/B pairs per 12 cells per OS (72 observations each; **216 total**, counting each process once), 4 query regimes × 64/512/4096 physical STORED streams, full archive ZIP bytes and selected bytes verified.

**Primary preregistered acceptance:** both complete-session wall and CPU >=1.20x on **each OS** for n=4096 with 64 tail 1-byte reads. Here **larger control/candidate ratio is better**.

| Host | n=4096 Q64 control total wall | inline total wall | wall ratio | CPU ratio | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Ubuntu 24.04 | 311.545 ms | 301.825 ms | **1.0322x** | **1.0320x** | Below 1.20x |
| macOS 14 ARM64 | 387.220 ms | 385.754 ms | **1.0038x** | **1.0044x** | Below 1.20x |
| Windows 2022 | 449.469 ms | 439.708 ms | **1.0222x** | **1.0357x** | Below 1.20x |

All three hosts returned **`SINGLEPASS_MATERIALITY_FALSIFIED`**, the source-independent receipt referee PASSed, and **18 forged receipts** (6 each host) were rejected. The +1 reauthenticated stream-size contradiction was rejected by strict preflight and both tested read paths on all three OS. No wrong byte on any valid observed selected read. This is evidence of equivalence on *tested* signed STORED cases, not a general semantic proof of all VZIP modes, or a fully authenticated partial-range API.

### Required controls and contradictions

- Ubuntu n=512 Q64 wall ratio 1.0010x; macOS n=512 Q64 1.2103x; Windows n=512 Q64 1.0132x. The isolated macOS gain does not generalize to the preregistered large case.
- Short-query measurements are noisy, particularly macOS n=64 Q1 early (~2.197x) versus Q1 tail (~0.540x), so neither is a robust global win. Windows submillisecond `process_time_ns` is quantized to zero in several observations and creates meaningless zero/huge ratio values; **do not use these for CPU claims**. The primary n=4096/Q64 CPU observations had nonzero medians, but cannot rescue the result.
- This negative result is consistent with #663 native batch failing to move complete installed Reader time, despite spectacular lower-rung C BHDR scan results #660.
- Unlike #663, this candidate eliminates the projection plus redundant second logical pass; *even that* fails to clear the materiality threshold. The cheap Python callback-inlining family is thus **retired as an unconditional productization route** for n=4096 Q64 STORED. Do not do threshold gardening or repeat another variation with the same causal frame absent new evidence.

### Separate source/CI custody

After the original hosted 3-OS scientific run, HEAD `753145e4122111fa5bac3fd4f7e82e531cd51d28` added a fail-closed member-level signed-size bound before the inline fast path; this changes the benchmarked code, and **the original timings cannot be represented as exact-head measurements of that later commit**. A new exact-head CI run must decide the modified source. The new guard is a strictly conservative fallback to the original Reader when member-size and recipe-size differ; nevertheless retain the temporal source distinction.

Generic tests at parent #663 exact final HEAD had 909 pass, 4 fail, 9 subtests pass; the four failing assertions are inherited release fingerprint/surface expectations with exact same six file blobs on main and parent, not a new native failure. See [#663 CI closure](https://github.com/FCMO-AI/.CMPCT/pull/663). The J24K13 general suite at any given HEAD should be reported independently and never claimed fully green without results.

## Frame review / counterfactual

The source-visible extra projection pass in #663 was a genuine design flaw; prospectively testing inline physical proof was a cheaper frame change to determine whether removing it was enough. **It was not.** A narrower core count of avoided function callbacks alone would have predicted at best a small gain; this negative three-host test is a stronger causal discriminator showing that traversal and required physical proof dominate whole-session cost.

The useful future frontier must eliminate or structurally change **whole traversals / ownership** rather than optimizing per-entry Python call overhead: e.g. one bounded native proof-plus-**coordinate computation** (not native proof plus Python replay), a generation-bound immutable physically authenticated index with a real source-mutability contract, or a different exact physical/logical organization that makes tail offsets directly provable with sublinear work. Full cost, source mutation, index bytes, admission, held-outs and fallback must remain charged. These alternatives are *unimplemented/unmeasured*. Product safely remains on #653 guarded path; no release/merge or format change.

No collision with #653/#663 owner branches, no update to stale Discovery STATE under #574, and no discovery-policy edit earned from a single local result. The prospective transferable lesson is to measure full installed source before crediting per-component speed and stop same-family variants when the whole-session ceiling is already falsified.
