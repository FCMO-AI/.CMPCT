# CMPCT next-frontier campaign — bounded multi-root mosaic resemblance

Status: **research only; no v0.29.0 claim has been earned**  
Base: CMPCT v0.28.0 / canonical on-disk revision 24

## Mission lock

### Requested

Continue the Opus-5 CMPCT campaign with milestone-sized work: a future numeric core version must improve
measured compression/indexing performance or another major product property rather than consuming a
version for implementation churn.

### Inferred

v0.28's strongest remaining structural blind spot is a target assembled from **several independent
ancestors**. The current depth-1 delta model chooses one base for one target. A merge/cherry-pick can
therefore contain large exact/resembling regions from roots A, B, C and D while no single root explains
enough of the result.

### Unknown

Whether multi-root COPY references save enough real stored bytes after opcode/root metadata and locality
cost to justify their extra reader complexity, and whether primitive savings survive complete archive
root storage, packing, authentication and recovery overhead. This campaign exists to answer both
questions experimentally.

### Non-goals

- deeper delta-on-delta chains;
- unbounded source indexing or all-pairs similarity search;
- increasing read amplification merely to win a ratio headline;
- calling a target-only primitive benchmark an archive-format win;
- changing canonical revision-24 grammar before independent conformance/native/recovery work exists;
- assigning project version 0.29.0 before material full-artifact evidence exists.

## Hypothesis

A bounded target delta that can COPY from **2–4 independent direct roots** will materially beat the best
single-root/direct representation on branch/merge/cherry-pick workloads, while a measured portfolio
fallback keeps single-parent, false-neighbor and incompressible controls at the inherited floor.

The key information-model change is not “a smarter delta.” It is that one target may have more than one
independent explanatory source. Dependency depth remains exactly 1.

## Disproof conditions

The concept does **not** advance if any of the following survives implementation review:

1. aggregate target-representation bytes improve by less than 5% against the optimistic per-target
   direct/best-single-root floor on the fixed v1 mosaic suite;
2. fewer than three fixed workloads select a genuine >=2-root representation;
3. any fixed workload is forced above its v0.28-style optimistic floor;
4. a selected target exceeds 8x conservative read amplification when every root the reader materializes
   is charged as a complete independently decoded node;
5. decoding can recurse through another delta or dependency depth can exceed 1;
6. aggregate indexed source bytes or checksum-collision fanout is unbounded;
7. malformed root slots/offsets/lengths can read outside declared sources or output limits;
8. the existing v0.28/canonical test suites regress merely because the new research module exists.

A failed gate is useful evidence. Do not reduce these thresholds merely to create v0.29.

## Primitive implementation tranche

`src/cmpct/mosaic.py`
: Separate research primitive with LITERAL and `(root slot, offset, length)` COPY operations. Maximum
  roots, aggregate indexed source bytes, checksum fanout and decoder output are explicit caller-visible
  bounds.

`benchmarks/mosaic_hostile_corpus_v1.py`
: Eight deterministic workloads: two-parent branch merge, four-way cherry-pick, reordered merge,
  code/config-like source merge, single-parent control, false mosaic sources, incompressible control and
  duplicate-root candidate pressure.

`benchmarks/mosaic_v029_bench.py`
: Measures target representation against an **optimistic floor** that auditions every direct root and
  keeps the smallest direct/single-root delta. Root storage is identical and cancels in this primitive
  experiment; the record is forbidden from claiming full-archive improvement.

`tests/test_mosaic.py`
: Exact reconstruction, deterministic multi-root use, flat dependency semantics, source/output bounds,
  malformed references and checksum-collision pressure.

## Primitive measurement contract

For each target:

1. measure direct storage using the same Zstd-vs-RAW rule as EntropyGraph II;
2. encode against every declared independent root with the existing single-base `delta_encode`;
3. choose the smallest direct/single representation as the **v0.28 optimistic floor**;
4. rank at most four candidate roots for mosaic encoding;
5. encode and immediately decode/byte-compare the mosaic payload;
6. charge physical-record overhead plus explicit per-root metadata;
7. conservatively charge every root the primitive representation actually requires;
8. select mosaic only if it uses >=2 roots, remains <=8x, copies >=1/3 of the target, and beats the
   optimistic floor by at least max(128 bytes, 1%);
9. otherwise emit the floor unchanged.

The first gate requires >5% aggregate target-representation improvement, >=3 improved workloads,
0 regressed workloads and <=8x maximum conservative read amplification.

## First result — useful but too easy to stop here

Source commit: `a6e7f29ae09555b652526357b62477897f7713db`  
Durable summary: `benchmarks/history/2026-08-17-mosaic-v029-primitive-v1.json`

The untouched v1 gate passed:

- optimistic v0.28-style target floor: **945,218 B**;
- selected mosaic/fallback target bytes: **518,111 B**;
- improvement: **45.1861%**;
- mosaic-selected workloads: **4/8**;
- regressed workloads: **0**;
- maximum conservative read amplification: **4.0005x**.

The four intended merge workloads individually improved by roughly **77.6–99.9%**, while all four
controls fell back to the optimistic floor.

That result proves the mechanism can represent several independent roots efficiently, but the near-zero
payloads on three synthetic merges expose a benchmark weakness: v1 gives the encoder large pristine
inherited regions. Treating that as sufficient evidence would be benchmark theater.

Footnote: v1 is therefore **preserved, not replaced**. The correct response to an easy benchmark is a
harder additional benchmark, not deleting the evidence that revealed why the first result was easy.

## Stress tranche v2 — pre-registered before measurement

`benchmarks/mosaic_stress_corpus_v2.py` adds ten harder workloads. Positive cases undergo sparse rewrites,
insertions, record-level conflict resolution, reordering, or source-like post-merge edits. Controls add
compressed-stream avalanche, a strong single-parent case, false neighbors, incompressible data, an
8-root diversity case that deliberately exceeds the 4-root candidate cap, and a metadata-dominated
small target.

`benchmarks/mosaic_v029_stress_bench.py` reuses the **same `_measure_target` cost model** as v1. The
harder corpus is not allowed to silently change how the optimistic single-root floor, per-root metadata,
exact decode check or read amplification are calculated.

Before running v2, the additional stress gate was fixed at:

- **>10% aggregate target-representation improvement** versus the optimistic direct/best-single floor;
- **>=3 improved workloads**;
- **>=3 genuine multi-root selections**;
- **0 regressions** under measured fallback;
- **<=8x maximum conservative read amplification**.

The untouched v2 result passed:

- optimistic target floor: **1,156,075 B**;
- selected mosaic/fallback target bytes: **777,886 B**;
- improvement: **32.7132%**;
- mosaic-selected workloads: **6/10**;
- regressed workloads: **0**;
- maximum conservative read amplification: **5.1240x**.

Durable summary: `benchmarks/history/2026-08-17-mosaic-v029-stress-v2.json`.

The v2 result is more informative than v1: a record-store merge with reordering and sparse rewrites still
improves **16.9%**, while compressed-stream avalanche, strong-single-parent, false-neighbor and
incompressible controls all fall back. The 8-root diversity attack also proves the 4-root cap can leave
reuse on the table without forcing candidate fanout wider.

## Full-artifact tranche — pre-registered before first archive run

Primitive wins are not enough. `experiments/entropygraph_v029_mosaic.py` integrates mosaic target nodes
into a complete EntropyGraph research artifact while deliberately preserving v0.28's root centrality and
physical pack decision. It does **not** redesign root placement to flatter the new representation.

`experiments/entropygraph_v029_mosaic_strict.py` is the stable evidence entry point. Every listed mosaic
root is charged exactly as the reader materializes it. `tests/test_mosaic_archive.py` exercises exact
reconstruction, strong verification, authenticated-tail metadata recovery, physical Merkle-leaf
corruption refusal, dependency depth, and the outer v0.28 fallback invariant.

`benchmarks/mosaic_v029_archive_bench.py` builds complete artifacts for every v1 and v2 workload. For
each workload it builds the complete v0.28 portfolio and the complete strict mosaic graph from the same
source tree, then emits the smaller artifact. Exact v0.28 bytes therefore remain a per-workload fallback.

### Full-artifact acceptance gate — fixed before measurement

The first full-artifact run is accepted only if **all** of the following hold:

- v2 complete-artifact bytes are **>2.0% smaller** than complete v0.28 portfolio artifacts;
- v1+v2 combined complete-artifact bytes are **>3.0% smaller** than complete v0.28 artifacts;
- at least **4/10 v2 workloads** improve as complete artifacts;
- at least **5 workloads combined** select a complete mosaic artifact;
- **0 workload size regressions** under exact v0.28 fallback;
- every selected mosaic target remains **<=8x descriptor-actual read amplification**;
- every candidate passes strong logical-tree verification;
- direct grammar tests prove primary-metadata recovery and payload-corruption refusal.

Why the percentage gate is lower than the primitive 32.7% v2 result: the full archive must store the
independent roots themselves, pack them, authenticate physical records, duplicate recovery metadata and
encode the complete file tree. Target-only savings are therefore mathematically diluted. Pretending the
root bytes disappear would be the exact benchmark error this tranche is meant to prevent.

**This threshold was frozen before the first full-artifact result. Every subsequent attempt must clear
these exact same thresholds. A red result changes the mechanism, not the gate.**

## Full-artifact attempt #1 — failed, preserved, and causally useful

Source commit: `24187acd739d62988e01c086078a58bd4c007d65`  
Workflow run: `31983309529`  
Durable summary: `benchmarks/history/2026-08-17-mosaic-v029-full-artifact-attempt1.json`

Attempt #1 completed the benchmark correctly and **failed the pre-registered acceptance gate**:

- v1 complete artifacts: **6,240,113 → 5,911,835 B (-5.2608%)**, 3/8 improved, 0 regressed;
- v2 complete artifacts: **8,589,119 → 8,428,504 B (-1.8700%)**, only 1/10 improved, 0 regressed;
- combined: **14,829,232 → 14,340,339 B (-3.2968%)**, 4/18 improved, 0 regressed;
- maximum descriptor-actual read amplification: **4.0005x**.

So attempt #1 passed the combined >3% size bar and the zero-regression/locality requirements, but it
missed **three independent gates**: v2 was below >2%, only one v2 workload improved instead of four, and
only four workloads combined selected mosaic instead of five.

The failure is not explained by archive root bytes alone. The per-workload record exposed a more specific
mechanism defect:

- v2 `02_shifted_reordered_merge`: **0 mosaic auditions**;
- v2 `03_record_store_conflict_merge`: **0 mosaic auditions** despite one inherited single-delta node;
- v2 `04_source_like_merge`: **0 mosaic auditions**;
- v2 `09_root_diversity_pressure`: **0 mosaic auditions**;
- v1 `03_reordered_two_parent_merge`: **0 mosaic auditions**.

Those are precisely workloads that won at primitive level. Attempt #1 only auditioned mosaic for targets
that v0.28 had already accepted as one-base delta targets. A true multi-parent merge can be too unlike
**any single parent** to cross that inherited gate, which made the integration logically backwards for
the new information model.

Footnote: attempt #1 is retained as executable `experiments/entropygraph_v029_mosaic.py` plus its durable
failed evidence record. Attempt #2 does not rewrite that history.

## Full-artifact attempt #2 — causal eligibility repair, gate unchanged

Attempt #2 is implemented separately in `experiments/entropygraph_v029_mosaic_leaf.py`; the stable
`experiments/entropygraph_v029_mosaic_strict.py` evidence wrapper now points at it. The change targets the
observed failure mechanism rather than the acceptance threshold.

### 1. Preserve the inherited v0.28 central assignment

v0.28's same-band LSH candidate set still exclusively determines the inherited single-delta central-base
assignment. New mosaic discovery **cannot** rewrite that assignment and then count the rewritten baseline
as a mosaic gain.

### 2. Add bounded position-independent discovery

Mosaic supplements same-band LSH with content features that may collide across band positions, because
reordering can move inherited regions from one part of a target to another. Buckets remain bounded.
For graphs with at most **64 nodes**, attempt #2 also uses a hard-bounded exhaustive correctness floor of
at most **16 prior candidates per target**. That is capped O(64×16), not an unbounded all-pairs path.
Larger graphs use only bounded feature buckets.

### 3. Permit direct **leaf** nodes to become mosaic targets

A direct node that v0.28 did not turn into a single delta may now be auditioned for mosaic **only if no
selected v0.28 delta uses it as a base**. Existing selected bases are protected. Candidate roots must
remain direct. Promoted leaf targets are removed from the direct-root set before packing.

This changes eligibility without permitting depth 2: every single or mosaic target still depends only on
independent direct roots.

### 4. Compact descriptors to roots actually used

Attempt #1 could carry a wider candidate-root list than the COPY stream actually referenced. Attempt #2
re-encodes until the descriptor contains only roots that emit COPY bytes. Metadata cost, reader
materialization, and read-amplification accounting therefore refer to exactly the same root set.

### 5. Re-check locality after real physical packing

Tentative leaf mosaics are first screened conservatively, then roots are physically packed. Any leaf
mosaic whose **actual descriptor/root pack** amplification exceeds 8x is rejected, restored as direct,
and packing is recomputed until stable.

### 6. Regression test the exact attempt-1 blind spot

`tests/test_mosaic_archive.py` now requires the v2 shifted/reordered merge—which attempt #1 never even
auditioned—to produce at least one mosaic leaf while every referenced base remains direct and the archive
strong-verifies.

### Attempt #2 acceptance rule

**Unchanged.** Attempt #2 must clear the exact frozen full-artifact gate above. No percentage, workload,
selection, locality, verification, or fallback threshold has been relaxed. If attempt #2 still fails, its
new evidence determines whether candidate discovery, partial-root profitability, chunk boundaries, or
physical packing is the next mechanism to challenge.

## If the full-artifact gate wins

A green full-artifact gate earns a **generalization tranche**, not immediately v0.29.0. The strict mosaic
portfolio must then run against the existing 15-workload v0.28 neutral/resemblance suite, preserve all
existing losses/fallbacks, and compare structural aggregates against archive competitors. Creation CPU,
strong-verification latency, descriptor/root fanout and remote selective-read behavior must remain
visible.

Only after the existing frontier and the new mosaic workloads are reconciled can a scarce v0.29.0
proposal be considered.

## If it loses

Preserve the record and inspect the failure mechanism:

- opcode/root-reference overhead dominates → investigate compact root dictionaries or segment maps;
- candidate ranking misses useful roots → improve bounded discovery, not unbounded all-pairs search;
- a component root is individually unprofitable but jointly useful → consider retaining bounded partial
  candidates based on copied information even when their one-root delta loses;
- source read amplification dominates → investigate smaller independent root units or target-local root
  slices without weakening integrity;
- full root/archive bytes dilute target savings below materiality → mosaic may remain an optional niche
  transform rather than a core-version feature;
- chunk boundaries split multi-parent information into nodes that each see only one root → challenge the
  unit model rather than deepening the dependency graph;
- false-neighbor work dominates creation CPU → build a conservative rejection model before more codecs.

A negative result that eliminates a seductive architecture is progress, but it does not consume a
numeric CMPCT version.
