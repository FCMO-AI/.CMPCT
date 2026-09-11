# ONE-G0.2 root-hash-charged direct-emitter writer — terminal result

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`

Frozen authority: `docs/one/evidence/ONE_G02_ROOT_HASH_CHARGED_DIRECT_EMITTER_PREREG_2026-09-05.md`.

## Exact CI receipt

- exact source head: `fb7708582a158f5fed09f2c8966ac3a048386fc1`
- workflow: `ONE-G0.2 root-hash-charged direct emitter`
- workflow run: `33995465684`
- job: `101385135887` (`root-hash-charged-direct-emitter`)
- conclusion: **success**
- result-bearing falsifier step: **success**
- ONE semantic/hostile tests: **success**
- artifact: `9977915083`
- artifact digest: `sha256:674339cdf92b15c049a5401090075c4f88f548838ec23bbdaef64625c74fdab9`
- frozen decision: **`advance_root_hash_charged_direct_emitter`**

The result-bearing head is the corrected hostile-review version that explicitly rechecks native one-pass segment plans against the independent Python maximal +1 segmentation oracle. Any earlier pre-oracle-fix run is superseded and has no result authority.

## What changed from the preceding writer gate

The preceding end-to-end relation-to-wire gate began after root identities were already supplied. This falsifier adds one unavoidable ingest cost identically to both arms: every timed writer call computes SHA-256 for the complete previous and current version and uses those digests as the actual Program roots.

Everything else remains common between baseline and candidate:

- amortization-safe relation admission/proof;
- native one-pass segmentation;
- bounded generic Program construction;
- full shape validation;
- unchanged ONE0 wire semantics and decoder/reference reconstruction.

Only canonical emission differs: ordinary helper-produced temporary byte strings versus direct writes into the final growable output.

## Frozen matrix result

All semantic/oracle boundaries passed:

- semantic gates: **pass**;
- native segment-plan independent oracle: **pass**;
- baseline/candidate canonical wire: **byte-identical on every row**;
- computed source/current SHA-256 roots: **exact on every row**;
- decode/reconstruction: **byte-exact on every row**;
- stored bytes, Law vocabulary, resource caps and reader work: unchanged between arms.

Performance across the 21 productive rows:

- median candidate/baseline hash-charged writer elapsed: **0.833329x** (~**16.67% lower**);
- productive rows <=1.00x: **21/21**;
- worst individual productive row: **0.954406x**;
- every productive size-class median passed the frozen <=1.03x law.

Productive size medians:

| Relation size | Candidate / baseline |
|---:|---:|
| 4 KiB | 0.808777x |
| 8 KiB | 0.831090x |
| 16 KiB | 0.834126x |
| 32 KiB | 0.834633x |
| 64 KiB | 0.833839x |
| 128 KiB | 0.833329x |
| 256 KiB | 0.833853x |

Control size medians:

| Relation size | Candidate / baseline |
|---:|---:|
| 4 KiB | 0.813066x |
| 8 KiB | 0.849012x |
| 16 KiB | 0.862911x |
| 32 KiB | 0.865656x |
| 64 KiB | 0.845396x |
| 128 KiB | 0.815566x |
| 256 KiB | 0.903495x |

Worst control size median: **0.903495x**, below the frozen <=1.05x law.

## Important hostile rows

### 256 KiB exact shift

This is the row that had produced the earlier isolated Python-emitter anomaly. With two complete SHA-256 root computations additionally charged:

- baseline: **632,404 ns** median;
- direct-emitter candidate: **603,570 ns** median;
- ratio: **0.954406x**;
- wire: **262,278 B**, unchanged;
- transient segment-plan state: **24 B**;
- native segment target traffic: **262,144 B**;
- root hashes: exact;
- independent segment oracle: exact.

The benefit is naturally diluted because hashing now owns a larger fraction of this very simple relation, but the row still improves rather than regressing.

### 256 KiB quarter damage

- baseline: **3,844,519 ns**;
- candidate: **3,205,763 ns**;
- ratio: **0.833853x**;
- wire: **330,777 B**;
- Surprise: **327,425 B**;
- native segments: **516**;
- transient segment plan: **6,192 B**.

### 256 KiB fragmented every 96 B

- baseline: **24,954,949 ns**;
- candidate: **18,143,134 ns**;
- ratio: **0.727036x** (~27.30% lower);
- wire: **297,504 B**;
- Surprise: **264,876 B**;
- nodes: **2,736**;
- hierarchy depth: **2**;
- native segments: **5,464**;
- transient segment plan: **65,568 B**.

The direct-write advantage therefore remains largest when generic control density is high, which is consistent with its causal mechanism: it removes repeated temporary control-byte construction/copy work rather than making hashing or relation proof faster.

## Causal interpretation

Adding two complete SHA-256 root computations reduces the productive median gain from the preceding relation-to-wire result (~20.16%) to **~16.67%**, but does not erase it. All 21 productive rows still improve, every size median remains green, and the formerly unstable 256 KiB exact-shift row remains below baseline.

This strengthens the mechanism-level conclusion that direct final-buffer canonical emission is useful beyond an isolated serializer microbenchmark. It also quantifies dilution honestly: on simple relations, fixed unavoidable ingest work can consume most of the local emitter advantage; on control-heavy Programs the gain remains large.

## Strongest hostile-review objections / remaining debt

This is still **not full ingest or product writer authority**.

1. The promoted/future fused Gear observation path is not charged here.
2. Arbitrary object-pair discovery is not solved; temporal adjacency supplies pair identity.
3. Authenticated index/container placement, durability/recovery and filesystem semantics are not charged.
4. Program construction and canonical emission remain Python research implementations; only relation/segmentation kernels are native.
5. Stored bytes are deliberately unchanged, so this is compute-efficiency evidence, not density evidence.
6. The earlier isolated CPython context anomaly remains unexplained at runtime-mechanism level, although two differently structured broader gates now show it is not an inherent direct-emission size cliff.
7. Authenticated selective access remains separate open debt; the generic range cone result still does not supply wire indexing and selective integrity by itself.

## Decision

**ADVANCE the direct-write principle as the preferred ONE research writer emission shape.**

The next high-value gate should no longer spend time tuning Python emission. It should either:

- integrate/charge the fused observation + identity + relation-to-wire path sufficiently to create an honest broader ingest envelope; or
- transfer direct canonical construction to a shared native ONE writer path and verify byte-identical wire, resource bounds and end-to-end creation throughput.

Do not call the current Python implementation product-native. Do not introduce a format revision or reader-visible opcode: the win is implementation work elimination under unchanged ONE0 semantics.
