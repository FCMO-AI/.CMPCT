# ONE-G0.2 fused-cache whole-ingest result

Date: 2026-09-07  
Branch: `research/cmpct1`  
Experimental version: `ONE-G0.2`  
Result source SHA: `66829c1af37d164352046dcf29db2ffabc790ca3`  
Workflow run: `34170797807`  
Artifact: `one-g02-full-ingest-fused-cache-66829c1af37d164352046dcf29db2ffabc790ca3` (`id 10035658739`)  
Artifact digest: `sha256:28876991c892a9a067f74c6e89ffe97b118d894349af29efe6ab6a60e32ac345`

## Decision

`OPEN_CACHE_ADMISSION_DEBT`

The positional fused-observation cache **survives whole research-writer dilution strongly when positional identity exists**, but unconditional use is falsified because zero-reuse rows regress by about 32%. Preserve the cache mechanism; rehabilitate its admission policy before broader promotion.

All semantic/oracle gates passed. All productive positional performance gates passed. Hostile carrying-cost gates failed.

## Exact matrix

15 paired alternating A/B-B/A repetitions per row. Ratios are candidate fused-cache whole-writer / fresh-observation whole-writer.

| Size | Case | Wall | CPU | Baseline observe share | Reused / recomputed blocks | Cache payload / input | Gate |
|---:|---|---:|---:|---:|---:|---:|---:|
| 64 KiB | exact repeat | 0.064575x | 0.064612x | 98.946% | 16 / 0 | 16.650% | <=0.95 PASS |
| 64 KiB | one-block edit | 0.143797x | 0.143904x | 98.902% | 15 / 1 | 16.650% | <=0.98 PASS |
| 64 KiB | eight-block edit | 0.699944x | 0.699951x | 98.947% | 8 / 8 | 16.650% | <=1.02 PASS |
| 64 KiB | shift +1 | 1.323355x | 1.323580x | 98.526% | 0 / 16 | 16.650% | <=1.15 **FAIL** |
| 64 KiB | independent random | 1.326859x | 1.326378x | 98.959% | 0 / 16 | 16.650% | <=1.15 **FAIL** |
| 256 KiB | exact repeat | 0.062681x | 0.062786x | 99.105% | 64 / 0 | 16.650% | <=0.95 PASS |
| 256 KiB | one-block edit | 0.082604x | 0.082624x | 99.118% | 63 / 1 | 16.650% | <=0.98 PASS |
| 256 KiB | eight-block edit | 0.222233x | 0.221901x | 99.081% | 56 / 8 | 16.650% | <=1.02 PASS |
| 256 KiB | shift +1 | 1.322887x | 1.323064x | 98.732% | 0 / 64 | 16.650% | <=1.15 **FAIL** |
| 256 KiB | independent random | 1.320274x | 1.320267x | 99.083% | 0 / 64 | 16.650% | <=1.15 **FAIL** |

## Causal interpretation

This result resolves the earlier Amdahl objection for the frozen research-writer envelope. Fresh fused observation owns roughly 98.5-99.1% of baseline time on these rows; root hashing plus the current downstream relation/segment/Program/validation/direct-emission path is only about 1% here. Component cache wins therefore survive nearly intact at this system scope.

The hostile regression is equally clear. With no positionally identical blocks, the cache reuses zero feature blocks and recomputes every block after additionally hashing each block for cache identity. That extra SHA/integrity/cache framing sits on top of essentially the same fused feature work as fresh observation. The result is a stable ~1.32x whole-envelope slowdown at both sizes and both no-reuse controls.

This is mechanism-level evidence for **conditional** caching, not an argument to relax the hostile gate.

## Semantics / representation truth

- cached run/reuse opportunities matched fresh `observe()`;
- baseline/candidate canonical ONE wire bytes and encoding stats matched on every row;
- downstream relation classification matched;
- native segment plans matched the independent Python oracle whenever the relation path was enabled;
- ordinary ONE decode/evaluate reconstructed both previous/current roots exactly;
- no reader-visible cache/opcode/format change occurred;
- stored ONE bytes are not improved by this experiment; writer compute is the changed dimension.

## Resource truth

Persistent fused-cache payload was 16.650390625% of current input in every measured row: 10,912 B at 64 KiB and 43,648 B at 256 KiB. This remains below the earlier 20% component ceiling but is not actual Python peak RSS authority.

The candidate continued to charge full current-source block SHA validation. Exact-repeat reuse therefore eliminates the Python fused feature pass but does not make source validation proportional only to changed bytes.

## Strongest hostile review

The benchmark is a broader **research-writer cost envelope**, not yet a fully coupled automatic compiler. Observation is charged and independently oracle-checked, while the existing promoted relation admission/segmentation path remains the downstream Program authority. The result is valid for Amdahl/carrying-cost economics but does not establish that cached observation opportunities themselves already drive canonical Program selection.

The stronger engineering objection is unconditional policy: a mechanism with ~15.5x speedup on exact repeat but ~32% regression when it has zero usable positional state should not be globally enabled. The next step is sparse, bounded pre-admission, not threshold relaxation.

## Next action

Run `ONE_G02_FUSED_CACHE_ADMISSION_PREREG_2026-09-07.md`: at most eight stratified SHA-256 identity probes, 25% minimum match fraction, then cache-or-fresh observation. The repair must preserve positional gains while holding shifted/random rows within 1.05x fresh baseline. Rejected rows intentionally do not build the next cache; cache continuity/re-seeding remains explicit follow-up debt.

## Comparator boundary

This result changes no Genesis comparator score. Frozen v0.29 `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d` and deferred v0.30 `f4b158a55a08b9b18b50e4e4abe4b9251048c772` remain untouched. The September 11 same-input 15-workload decision remains authoritative.
