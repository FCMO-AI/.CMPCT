# ONE-G0.2 fused-cache admission rehabilitation result

Date: 2026-09-07  
Branch: `research/cmpct1`  
Experimental version: `ONE-G0.2`  
Result source SHA: `227d6977afaf35514b79b4d3345615f938c09a59`  
Workflow run: `34171191837`  
Job: `101891796077`  
Artifact: `one-g02-full-ingest-fused-cache-admission-227d6977afaf35514b79b4d3345615f938c09a59` (`id 10035878309`)  
Artifact digest: `sha256:eb6bd87809c469c442b55f1c798267de7fe15c28a1db0cfbe7f2515bf1606bc8`

## Decision

`ADVANCE_CACHE_ADMISSION_REHABILITATION`

A bounded eight-position SHA-256 identity probe with the preregistered 25% minimum match fraction repaired the unconditional fused-cache carrying-cost failure on the frozen research-writer matrix. All semantic, admission-classification, productive and hostile performance gates passed without moving a threshold.

This result rehabilitates **conditional writer-side use** of the current positional fused-observation cache against the current Python fresh-observer baseline. It does not yet justify broad promotion because that baseline is itself a Python per-byte implementation whose optimized native transfer is now an explicit falsifier.

## Exact matrix

15 paired alternating A/B-B/A repetitions per row. Ratios are admission candidate / fresh-observation whole research-writer baseline.

| Size | Case | Probe matches | Admitted | Wall | CPU | Reused / recomputed blocks | Gate |
|---:|---|---:|:---:|---:|---:|---:|---:|
| 64 KiB | exact repeat | 8 / 8 | yes | 0.076140x | 0.076136x | 16 / 0 | <=0.95 PASS |
| 64 KiB | one-block edit | 7 / 8 | yes | 0.156673x | 0.156718x | 15 / 1 | <=0.98 PASS |
| 64 KiB | eight-block edit | 4 / 8 | yes | 0.758519x | 0.759943x | 8 / 8 | <=1.02 PASS |
| 64 KiB | shift +1 | 0 / 8 | no | 1.016861x | 1.016335x | 0 / 0 | <=1.05 PASS |
| 64 KiB | independent random | 0 / 8 | no | 1.018005x | 1.018345x | 0 / 0 | <=1.05 PASS |
| 256 KiB | exact repeat | 8 / 8 | yes | 0.065863x | 0.066071x | 64 / 0 | <=0.95 PASS |
| 256 KiB | one-block edit | 7 / 8 | yes | 0.083421x | 0.083433x | 63 / 1 | <=0.98 PASS |
| 256 KiB | eight-block edit | 7 / 8 | yes | 0.223334x | 0.223441x | 56 / 8 | <=1.02 PASS |
| 256 KiB | shift +1 | 0 / 8 | no | 1.003192x | 1.003343x | 0 / 0 | <=1.05 PASS |
| 256 KiB | independent random | 0 / 8 | no | 0.999453x | 0.999644x | 0 / 0 | <=1.05 PASS |

## Causal result

The prior whole-writer experiment showed a stable ~1.32x slowdown when unconditional cache observation found zero reusable positional blocks. The bounded probe removes almost all of that debt by falling back to fresh observation before the expensive cache path. The remaining rejection overhead is approximately 0-1.8% in this matrix while productive rows retain most of the cache's large speed advantage.

The probe reads/hashes exactly 32 KiB on all >=8-block rows. That cost is deliberately paid twice on admitted rows: sampled blocks are hashed once by admission and again by the cache's independent validation. Despite that duplicated work, productive timing gates passed strongly against the current baseline.

## Semantic / representation truth

- cached/admitted and rejected/fresh observations matched the fresh opportunity oracle;
- baseline/candidate canonical ONE wire bytes and encoding stats matched;
- relation classification matched;
- native segment plans matched the independent Python plan oracle whenever relation admission was enabled;
- ordinary ONE decode/evaluate reconstructed previous/current roots exactly;
- no reader-visible cache, opcode, format or canonical-version change occurred;
- no stored-byte, decode-throughput or selective-read advantage is claimed here.

## Resource truth

When admitted, the fused cache retains the previously measured 16.650390625% persistent payload ratio: 10,912 B at 64 KiB and 43,648 B at 256 KiB. Rejected rows intentionally return no new fused cache and therefore retain zero next-cache payload in this falsifier.

That last point is real debt: immediate hostile carrying cost is repaired partly by declining to maintain cache continuity after a rejected update. A production incremental policy needs explicit re-seeding economics rather than silently assuming the next version again has a usable cache.

Actual process peak RSS remains unmeasured for this admission candidate; the persistent-payload figures are not Python object RSS authority.

## Strongest hostile review

The more important confound is now the baseline itself. Fresh `observe()` owns roughly 98.5-99.1% of the current research-writer envelope and executes its byte scan/FNV/index operations in Python. The large conditional-cache win could therefore be substantially implementation leverage rather than durable architectural leverage.

Accordingly, this result does **not** close ONE-07. The next authority is `ONE_G02_NATIVE_FRESH_OBSERVER_PREREG_2026-09-07.md`: transfer the same fresh-observer semantics into a native bulk kernel and then rerun the cache/admission comparison against that optimized baseline before broad promotion.

## Comparator boundary

No Genesis comparator score changes. Frozen v0.29 `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d` and deferred v0.30 `f4b158a55a08b9b18b50e4e4abe4b9251048c772` remain untouched. This writer-compute result cannot substitute for the September 11 same-input 15-workload decision.
