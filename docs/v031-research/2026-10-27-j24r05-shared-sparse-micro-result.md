# J24R05 — Shared-iterator sparse reconstruction: cheap falsifier and non-promotion

**Date:** 2026-10-27 UTC. **Decision: DO NOT IMPLEMENT / DO NOT BUY HOSTED ABBA ON THIS EVIDENCE.** No Reader/product code mutated.

## Authority, question and provenance

Preregistered before experiment at `d042371e21d6c19f038659a77f7f7119f65fcee9`. Stacked scientific branch from J24R04c #596 HEAD `c83baa1868b24a3cc74373a495db938c224b4621`, actual Reader blob `cd85d54710205ce0ba3d5dcf401451643aed1814`. Production release remains v0.30.0 / format r24, and #584/#596 remain owners. Proposed one shared reconstruction loop using `iter(extents)` for E<=4 and a constant-memory generator over indices after `bisect_right` for E>4; no mutated format or storage index. The objective was to remove the duplicate two-loop body of #596 and overcome its confirmed +5.514% E=4 scientific median debt vs #569.

## Cheap lower-rung evidence (not installed Reader)

A standalone source-shaped loop implementation in [research/j24r05_shared_sparse_micro.py](../../research/j24r05_shared_sparse_micro.py) preserves the extent arithmetic, chunk slicing and early-stop tests; it replaces actual `_blob` calls with immutable in-memory 4-byte values and uses no archive parser. Environment: Linux x86_64 6.18.55; CPython 3.13.5. Eight deterministic E profiles (1,2,4,5,16,129,4096,65536), 256 same late one-byte reads per observation, ten randomized arm-order rounds for E<=129, six for larger E. Both arms returned the same `b'D'` and equivalent full-span bytes in the micro. This is **mechanism-only** evidence, not product throughput, cold open, CPU parity, SHA verification, portability, memory equivalence or archive-size evidence.

First local unasserted-in-timer micro (included a third `range` control) gave these medians, ms per 256 requests:

| E | Existing #596-shaped two-loop | New shared-iterator proposal | Shared / existing |
|---:|---:|---:|---:|
| 1 | 0.147358 | 0.146557 | 0.995× |
| 2 | 0.164318 | 0.180853 | 1.101× |
| 4 | 0.177423 | 0.199968 | **1.127×** |
| 5 | 0.265911 | 0.287088 | 1.080× |
| 16 | 0.246383 | 0.385102 | 1.563× |
| 129 | 0.312958 | 0.373384 | 1.193× |
| 4096 | 0.418792 | 0.439273 | 1.049× |
| 65536 | 0.528148 | 0.528052 | 1.000× |

A second local cross-check inserted identical `assert output == b'D'` work into both timed loops. At E=4 it returned 0.222040 ms existing vs 0.233313 ms shared (1.051×); at E=4096, 0.488052 vs 0.582734 ms (1.194×). Other cells changed materially with scheduling, including E=65536 favoring shared in that second run. **Do not combine these micro medians with the genuine hosted 3.11 product numbers.** Local CPU noise / Python version / extra assert do not support a universal slowdown claim. The reliable scoped conclusion is simply: this proposed shared iterator failed to show a robust cheap-rung E=4 benefit; the large-E advantage also was not decisively superior. A high-cost installed 3-way ABBA has low expected decision value without a stronger, qualitatively different mechanism.

## Decisive scientific distinction and alternatives

This is **not** a falsification of J24R04c's real 53.56×/767.19× high-E gains. Its hosted E=4 +5.514% failure remains frozen and cannot be retrospectively repaired by process noise or a new threshold. The proposed shared generator can simplify maintenance, but iterator construction and generator dispatch themselves export Python work. The alternative single `range(start,len)` loop adds per-extent indexing on the small vector and also showed variable negative micro behavior; precomputing a persistent O(E) end index shifts costs to cold open, memory and ownership. A near-source short-loop predicate reorder likewise produced unstable mixed effects across E and locality. None deserves an immediate full-product implementation.

## Counterfactual and handoff

The prospective and cheap discriminator should have been `E=4` iterator/setup dispatch measured *before* writing a new Reader branch. This test prevented implementation and duplicate CI with no real positive evidence. No discovery policy revision is earned from one local noisy probe. No `STATE.json` mutation: separate owner #574. No concurrency collision or unrelated repo change.

**Action:** preserve the winning high-E read algorithm with its E=4 research debt in #584/#596; stop the short-vector threshold/iterator family for now. Next operator should prioritize a substantially different execution/ownership frame (or a higher-impact S_CHUNKS open bottleneck), check existing O216–O219/O221/O224 owners before claiming it, and never call a 5%-relative sub-millisecond research signal the official release gate without also applying its 3 ms absolute term. Host, recovery, whole-system parity, and release promotion are unmeasured and not credited. Scientific outcome is **NARROW / PARK**.
