# ONE-G0.2 — Promoted minimizer marginal information-yield map

**Branch:** `research/cmpct1`  
**Exact result-bearing source:** `ad19118a614037c2304c74ace0371a28dff68da6`  
**Workflow run:** `33942873207`  
**Result-bearing job:** `101243528522`  
**Artifact:** `9962403656`  
**Artifact ZIP SHA-256:** `34616fb842afaa2edc580697163f4897a0814d7724ff40178cb4521aa367dbba`  
**Experimental version:** `ONE-G0.2`

## Question

After promoting the tail-return 8 KiB selector and falsifying two local operation-count optimizations, does the selector recover enough *additional* reusable structure per unit of charged compute/state/proof traffic to justify paying its cost generally?

This instrument maps opportunity economics; it does not promote or reject ONE. Opportunity bytes are exact-proven nomination headroom and **are not stored-byte savings**. The existing Python opportunity oracle provides the numerator. The promoted native tail-return selector is paired against the same compiled Gear recurrence for selector-only incremental cost. Index/proof traffic and modeled state are reported rather than gifted.

## Exact semantic boundary

All **50 ONE tests passed** before measurement. The native promoted selector was independently compared with the Python rightmost-min trace, final Gear state and considered-position count for every mapped case.

## Main result — opportunity is highly conditional

`positive_marginal_cases` contains only:

1. `shifted_version_pair_1byte_insert`;
2. `starved_shifted_basis_8k_insert1`.

Every other frozen case had **zero marginal reuse opportunity** versus the cheap fixed observer, including random 1 MiB, zlib-random ~1 MiB, zeros, the aligned 64/128/256/512 B bases, aligned 4 KiB/16 KiB/64 KiB repetitions, the exact 512 KiB pair, and the aligned zero-anchor 8 KiB adversary.

The two positive cases are exactly the insertion/phase-shift regime that motivated content-derived selection:

- ordinary shifted version pair: fixed **0 B**, minimizer **524,288 B**, marginal **+524,288 B**;
- zero-sparse-anchor shifted 8 KiB adversary: fixed **0 B**, minimizer **8,192 B**, marginal **+8,192 B**.

## Charged selector cost

On 1 MiB rows the promoted selector adds roughly **3.73–4.19 ns/input-byte** beyond the already-formed Gear recurrence. Representative paired medians:

- random 1 MiB: Gear **0.664 ms**, selector **4.622 ms**, incremental **3.967 ms**;
- zlib-random: Gear **0.663 ms**, selector **4.639 ms**, incremental **3.983 ms**;
- exact pair: Gear **0.663 ms**, selector **4.617 ms**, incremental **3.946 ms**;
- shifted version pair: Gear **0.661 ms**, selector **4.589 ms**, incremental **3.928 ms**.

On the ordinary shifted pair the marginal opportunity yield is therefore about **133,464 opportunity bytes per incremental selector millisecond**. On the 16,385-byte shifted starvation case the incremental selector cost is about **0.0621 ms**, yielding about **131,989 marginal opportunity bytes/ms**.

Negative random/compressed rows pay the full ~4 ms/MiB selector increment for **zero** marginal opportunity. This is the important carrying-cost result.

## State/read accounting

The promoted offset path reserves **41,056 B** of selector state. With the global/local nomination index charged, modeled discovery state on representative 1 MiB rows is roughly:

- random: **50,304 B**;
- zlib-random: **50,288 B**;
- exact pair: **46,192 B**;
- shifted pair: **46,144 B**.

Random/compressed negative cases add no proof rereads. The shifted relation intentionally pays an additional exact proof: total source-read accounting becomes **2,097,153 B** for a 1,048,577-byte input because the fixed observer had no corresponding candidate.

## Causal interpretation

The selector is **not** a generally productive second-stage cost on the tested matrix. Its value is concentrated in phase-shift/insertion relationships. This changes the optimization target more substantially than another 1–5% kernel tweak would: ONE should try to avoid paying the full minimizer maintenance cost when cheap observation already explains the input or provides no evidence that shift-robust global reuse is addressable.

The next research question is therefore sparse opportunity gating, not another local minimizer micro-optimization. A successful gate must be content-derived or otherwise honestly charged, must preserve the known shifted relationships it claims to address, and must not simply rename workload labels. It may use already-formed Gear/fixed-observer evidence, but reader discovery remains forbidden and any surviving relation still compiles to the same generic reuse Law.

The zero-sparse-anchor shifted adversary remains the hard falsifier: ordinary sparse Gear can flag/recover the friendly shifted pair cheaply but starves on this constructed basis. Any gate that depends only on observing ordinary sparse anchors must say explicitly whether it loses this relation or how it rescues it without restoring full per-byte minimizer cost.

## Decision boundary

No implementation is promoted by this map. It does, however, retire the implicit assumption that the minimizer should be paid uniformly across general inputs merely because its opportunity semantics are strong. The next Builder must demonstrate **conditional compute avoidance with opportunity preservation**, or quantify the exact opportunity mass it elects to surrender.

No reader, Law, wire, stored-byte, product-speed, comparator or release authority is created.
