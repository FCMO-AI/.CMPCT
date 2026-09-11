# ONE-G0.2 parallel root-hash pair — terminal result

Date: 2026-09-06  
Branch: `research/cmpct1`  
Experimental line: `ONE-G0.2`

## Exact evidence

- source/head: `2b1c31d9244e8c285e2e96a1d19fee9445c01f62`
- workflow: `ONE-G0.2 parallel root hash pair`
- run: `34053218713`
- job: `101540418883`
- artifact: `9995207799`
- artifact digest: `sha256:b5c189abf213bf61e0d2a95c93081bb2af18d81b35c1b63dd460981dc181df90`
- rounds: `63` paired A/B-B/A after cold observation + warmup
- CI truth: project install PASS; full `tests/one` semantic/hostile suite PASS; hash falsifier intentionally FAIL under frozen performance gate; evidence upload PASS.

The source includes the Hostile Reviewer single-flight hardening: a `busy` state remains asserted from dispatch until the submitting caller has observed worker completion, so a second caller cannot overwrite target/output pointers after the helper has picked up its job.

## Correctness / resource truth

- semantic failures: **0**
- previous digest: exact canonical SHA-256 on every row
- current digest: exact canonical SHA-256 on every row
- deterministic repeated calls: PASS
- helper threads: **1**
- configured helper stack: **65,536 B**
- cold candidate call: **141,673 ns** vs serial baseline **52,067 ns** = **2.72097x**
- cold startup <1 ms: PASS
- resource guard: PASS

No hash algorithm, root byte, wire field, reader behavior or integrity obligation changed.

## Performance result

Frozen mature (>=16 KiB per root) candidate/serial baseline:

- median: **0.8655754199x**
- worst: **1.5608509889x**
- 128/256 KiB median: **0.6332855040x**
- worst across all tested rows: **3.2709605775x**

The size trend is explicit and content-insensitive:

| bytes/root | shift_plus1 | independent_random | repeated | periodic |
|---:|---:|---:|---:|---:|
| 16 KiB | 1.526x | 1.553x | 1.561x | 1.558x |
| 32 KiB | 1.175x | 1.211x | 1.201x | 1.195x |
| 64 KiB | 0.795x | 0.862x | 0.869x | 0.874x |
| 128 KiB | 0.664x | 0.672x | 0.692x | 0.692x |
| 256 KiB | 0.596x | 0.603x | 0.602x | 0.594x |

The preregistered gate required mature median <=0.75x, every mature row <=0.90x, every tested row <=1.10x and 128/256 KiB median <=0.65x. Only the large-file median and resource/semantic guards pass.

## Decision

**`reject_parallel_root_hash_pair`** as a universal per-call root preparation strategy.

Do not rescue it by serializing small inputs and parallelizing large ones. The crossover is exactly the post-hoc size dispatcher forbidden by preregistration.

## Mechanism-level interpretation

SHA-256 remains the largest isolated simple-relation owner (~57.39%), but the cost of waking/synchronizing a helper dominates at 16–32 KiB and still leaves too little breadth at 64 KiB. The negative does not imply parallel creator work is useless; it falsifies *fine-grained two-hash parallelism as its own per-call primitive*.

The next preregistered line therefore attacks the second owner instead: exact native Segment scanning (~28.88% of mature simple-relation full elapsed) with word-at-a-time uniform-run proof. A future broader executor may revisit overlap only if it amortizes synchronization across already-existing creator work rather than adding a per-call thread barrier solely for two hashes.

## Claim boundary

No writer promotion, stored-byte authority, reader change, product use, v0.29/v0.30 comparison or Genesis-gate claim.