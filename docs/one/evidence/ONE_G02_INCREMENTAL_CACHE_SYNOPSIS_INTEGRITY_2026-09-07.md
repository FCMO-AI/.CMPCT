# ONE-G0.2 incremental cache synopsis integrity finding

Date: 2026-09-07
Branch: `research/cmpct1`
Experiment: ONE-07 writer-only discovery cache

## Mission lock

Hypothesis: current-block SHA-256 identity plus policy/block-size compatibility is sufficient to make reuse of cached observation synopses equivalent to fresh observation.

Disproof: construct cache state whose block digest and length still match the current bytes but whose derived synopsis fields are corrupted. If the incremental path reuses those fields, the cache has become correctness-authoritative despite the intended writer-only acceleration contract.

## Hostile-review result

The original seed was vulnerable to this exact case. Reuse checked current SHA-256 block identity and length but did not authenticate the cached derived fields themselves. Therefore a cache entry could retain the correct digest/length while carrying a stale or damaged `byte_sum`, transition count, zero count, or min/max value, and the incremental result could diverge from a fresh observation.

This is a correctness issue in the research accelerator, not an archive-reader or on-disk-format issue. Canonical ONE bytes and reader semantics are unchanged.

## Repair

Each `BlockSynopsis` now carries a domain-separated SHA-256 seal over:

- current block digest;
- block length;
- byte sum;
- transition count;
- zero-byte count;
- min byte;
- max byte.

Reuse requires:

1. compatible policy and block size;
2. structurally valid cached fields;
3. semantic numeric bounds;
4. a valid synopsis seal;
5. current block digest equality;
6. current block length equality.

Malformed numeric cache state fails closed to recomputation rather than reaching `struct.pack` or becoming reusable state. Added hostile tests cover feature corruption with a still-valid current digest, seal corruption, digest corruption, and oversized malformed numeric fields.

The seal is an integrity checksum for writer-owned cache state, not a MAC. An actively malicious party able to rewrite both cache fields and their checksum is outside this seed's cache trust model. The archive never requires this cache for decode. If future productization accepts cache state across a hostile trust boundary, keyed authentication or full recomputation is required.

## Cost accounting change

Persistent payload lower-bound accounting rises by 32 bytes per cached block for the synopsis seal. With the current fields this changes the modeled payload from 66 B/block to 98 B/block. This cost is explicit regression debt for the cache experiment and must be charged in any usefulness result.

A local exploratory Python diagnostic on sparse one-byte edits over 64 KiB, 256 KiB, 1 MiB and 4 MiB random inputs showed seal verification overhead was noisy and size-dependent rather than uniformly free. Median sealed/plain update-time ratios from that non-authoritative local diagnostic were approximately 0.994x, 1.094x, 0.968x and 1.171x respectively. These numbers are causal guidance only, not hosted promotion evidence; they strengthen the requirement to benchmark real expensive observation features rather than claim a win from reduced recomputation bytes alone.

## Decision

Advance the correctness repair. Do not yet promote the cache as a compute optimization.

The next result-bearing experiment must replace/augment the toy synopsis with useful expensive ONE observation features and compare fresh vs incremental creation while charging:

- full validation read traffic;
- feature recomputation/reuse bytes;
- wall and process CPU;
- cache payload and RSS;
- exact fresh-vs-incremental equivalence;
- exact repeat, sparse edit, append, shifted insertion, tiny, incompressible/media-like, policy-change and damaged-cache controls.

Retire or reform the seed if SHA-256 validation + synopsis-seal verification + cache lookup costs erase the saved real observation work. In that case the next changed-cone authority should reuse an already-required authenticated hierarchy or trustworthy changed-range provenance instead of adding another full-source tax.
