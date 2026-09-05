# ONE-G0.2 end-to-end direct-emitter writer — terminal result

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`

Frozen authority: `docs/one/evidence/ONE_G02_END_TO_END_DIRECT_EMITTER_WRITER_PREREG_2026-09-05.md`.

## Exact CI receipt

- source head: `b49db6e13daf85302414bfacea4bb4e0292e193c`
- workflow: `ONE-G0.2 end-to-end direct emitter writer`
- workflow run: `33995269811`
- job: `101384605691` (`end-to-end-direct-emitter-writer`)
- result-bearing falsifier step: **success**
- ONE semantic/hostile test step: **success**
- artifact: `9977859702`
- artifact digest: `sha256:5ed34b429d626f318d72dd6dc4d2f18f9db95fe895d2f74a3dc82650997c0eff`
- frozen result decision: **`advance_end_to_end_direct_emitter_writer`**

## What was compared

This is an adjacent-version relation-to-wire writer A/B after root identities are already available. Both arms charge the same:

- amortization-safe +1 relation admission/proof;
- native one-pass maximal Ref/Surprise segmentation for admitted +1 Laws;
- bounded generic Program construction (`surprise`, ranged `Ref`, `concat`, including bounded hierarchy);
- full `Program.validate_shape()` validation;
- canonical ONE0 semantics and ordinary decoder/reference reconstruction.

Only canonical emission differs:

- baseline: ordinary helper-produced canonical pieces appended by `encode_program()` after the common validation charge;
- candidate: one-pass growable direct emission into the final byte buffer, with no sizing pass and no helper-produced temporary uvarint/ref/node byte strings.

Root SHA construction, broader object discovery/fused observation, container/index placement, durability and product-native integration are outside this A/B and remain explicit debt.

## Frozen matrix result

All semantic/oracle gates passed:

- canonical baseline/candidate wire bytes: **identical on every row**;
- wire stats: **identical on every row**;
- decode + reference reconstruction: **byte-exact on every row**;
- native one-pass segment plan vs independent Python maximal +1 oracle: **exact on every admitted row**;
- reader work/materialization: unchanged because the Program/wire is unchanged;
- no Law operation, fanout/resource cap, root identity or stored-byte semantic changed.

Performance across 21 productive rows:

- median candidate/baseline full charged relation-to-wire writer elapsed: **0.798386x** (~**20.16% lower**);
- productive rows <=0.98x: **21/21**;
- worst individual productive row: **0.899657x**;
- every productive size-class median passed the frozen <=1.00x law.

Productive size-class median ratios:

| Relation size | Candidate / baseline |
|---:|---:|
| 4 KiB | 0.794799x |
| 8 KiB | 0.807167x |
| 16 KiB | 0.775988x |
| 32 KiB | 0.769605x |
| 64 KiB | 0.816232x |
| 128 KiB | 0.798386x |
| 256 KiB | 0.816944x |

Control size-class medians also remained below baseline:

| Relation size | Candidate / baseline |
|---:|---:|
| 4 KiB | 0.772352x |
| 8 KiB | 0.754722x |
| 16 KiB | 0.728586x |
| 32 KiB | 0.643291x |
| 64 KiB | 0.882657x |
| 128 KiB | 0.590083x |
| 256 KiB | 0.566126x |

Worst control size median: **0.882657x**, below the frozen <=1.03x law.

## Important rows

### 256 KiB exact shift

The isolated Python-emitter benchmark had previously shown a non-reproducible context-sensitive red near this row. Under the full charged relation-to-wire writer boundary it did **not** recur:

- baseline: **272,367 ns** median;
- direct-emitter candidate: **245,037 ns** median;
- ratio: **0.899657x**;
- canonical wire: **262,278 B**, identical;
- segment-plan state: **24 B** (2 native segments);
- relation sparse-gate comparison: **160 B**;
- native target segmentation traffic: **262,144 B**.

This falsifies the claim that the earlier 256 KiB red is an unavoidable algorithmic penalty of direct one-pass emission. It does not fully explain the CPython runtime-state anomaly from the isolated harness.

### 256 KiB quarter damage

- baseline: **3,413,556 ns**;
- candidate: **2,788,683 ns**;
- ratio: **0.816944x**;
- wire: **330,777 B**;
- Surprise: **327,425 B**;
- native segments: **516**;
- modeled transient segment plan: **6,192 B**.

### 256 KiB fragmented every 96 B

- baseline: **21,903,438 ns**;
- candidate: **15,652,729 ns**;
- ratio: **0.714624x** (~28.54% lower);
- wire: **297,504 B**;
- Surprise: **264,876 B**;
- Program nodes: **2,736**;
- hierarchy depth: **2**;
- native segments: **5,464**;
- modeled transient segment plan: **65,568 B**.

The gain therefore survives the control-heavy bounded-hierarchy case rather than appearing only on tiny/simple Programs.

## Causal interpretation

The earlier direct-emitter microbenchmark signal survives after relation admission, native one-pass segmentation, bounded Program construction and full shape validation are charged together. The mechanism-level interpretation is straightforward: helper-produced temporary canonical byte strings create avoidable allocation/copy work; directly writing the same canonical fields into the final growable output removes part of that work without changing representation semantics.

The magnitude shrinks from the isolated emission-only experiments to about a **20% median relation-to-wire writer gain**, which is exactly what should happen when unchanged upstream work is honestly charged. That survival is stronger evidence than the earlier isolated ~2–3x emission-only ratios.

The previously observed 256 KiB exact-shift anomaly is now constrained as benchmark/runtime-context debt rather than an inherent direct-emission size cliff: the frozen dense diagnostic did not reproduce a cliff, and this independently structured full-writer gate also passes that row. Do not reopen size-threshold tuning around 256 KiB without new causal evidence.

## Strongest hostile-review objections

This result is **not product writer authority**.

1. Root SHA construction and broader fused observation/object discovery are pre-existing supplied context and are not timed here.
2. Program construction and canonical emission remain Python research code even though segmentation/admission use native kernels.
3. Arbitrary pair discovery is not solved; temporal adjacency supplies pair identity.
4. Authentication/container placement, selective index/framing, recovery/durability and filesystem integration are outside this result.
5. The 256 KiB isolated-harness anomaly is not causally explained, only shown not to survive two differently structured falsifiers.
6. Stored bytes do not improve in this experiment because both arms deliberately emit byte-identical canonical ONE0. This is a compute-efficiency result, not a density result.

## Decision

**ADVANCE the direct canonical-write principle into the preferred research writer path.**

Do not consume a new reader opcode or format revision. Do not treat the Python implementation itself as the future product-native writer. The next decisive question is whether this preferred relation-to-wire path still provides a useful advantage when the broader fused observation/root-hash/authentication costs are charged in a full ingest/writer envelope, and whether the direct-write shape transfers cleanly to the eventual shared native ONE writer.

A high-value next Builder should therefore charge:

`fused observation/root identities -> relation opportunity/admission -> native one-pass segmentation -> bounded generic Program -> validation -> direct canonical emission -> authenticated placement`

while preserving the same wire, decoder semantics, locality/resource accounting and hostile controls. If the direct-write gain becomes negligible under that total envelope, retain it as a local implementation cleanup rather than exaggerating it into a system-level speed claim.
