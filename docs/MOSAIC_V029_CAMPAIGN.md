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
cost to justify their extra reader complexity. This campaign exists to answer that experimentally.

### Non-goals

- deeper delta-on-delta chains;
- unbounded source indexing or all-pairs similarity search;
- increasing read amplification merely to win a ratio headline;
- calling a target-only primitive benchmark an archive-format win;
- changing canonical revision-24 grammar before independent conformance/native/recovery work exists;
- assigning project version 0.29.0 before material evidence exists.

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
4. a selected target exceeds 8x conservative read amplification when every referenced root is charged
   as a complete independently decoded node;
5. decoding can recurse through another delta or dependency depth can exceed 1;
6. aggregate indexed source bytes or checksum-collision fanout is unbounded;
7. malformed root slots/offsets/lengths can read outside declared sources or output limits;
8. the existing v0.28/canonical test suites regress merely because the new research module exists.

A failed gate is useful evidence. Do not reduce these thresholds merely to create v0.29.

## First implementation tranche

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

## Measurement contract

For each target:

1. measure direct storage using the same Zstd-vs-RAW rule as EntropyGraph II;
2. encode against every declared independent root with the existing single-base `delta_encode`;
3. choose the smallest direct/single representation as the **v0.28 optimistic floor**;
4. rank at most four candidate roots for mosaic encoding;
5. encode and immediately decode/byte-compare the mosaic payload;
6. charge physical-record overhead plus explicit per-root metadata;
7. conservatively charge every actually referenced root's full logical bytes to read amplification;
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

Before running v2, the additional stress gate is fixed at:

- **>10% aggregate target-representation improvement** versus the optimistic direct/best-single floor;
- **>=3 improved workloads**;
- **>=3 genuine multi-root selections**;
- **0 regressions** under measured fallback;
- **<=8x maximum conservative read amplification**.

The v2 threshold is deliberately stricter than v1's 5% gate because the first experiment showed that
the mechanism is capable of very large gains on clean composites. If v2 fails, fix or reject the
mechanism; do not lower this threshold after seeing the result.

## If the primitive survives v2

Surviving both primitive gates earns **another experiment**, not immediately v0.29.0. The next tranche
must integrate mosaic targets into an EntropyGraph writer and pay all archive-level costs: root
centrality/packing, metadata/recovery duplication, Merkle leaves, remote selective reads, native-reader
semantics and the existing 15-workload v0.28 suite plus the new mosaic suites.

Only a full-artifact improvement under those constraints can justify a scarce project-version proposal.

## If it loses

Preserve the record and inspect the failure mechanism:

- opcode/root-reference overhead dominates → investigate coalesced root dictionaries or segment maps;
- candidate ranking misses useful roots → improve bounded discovery, not all-pairs search;
- source read amplification dominates → investigate smaller independent root units or target-local root
  slices without weakening integrity;
- best single base already explains merges → multi-root complexity is not warranted;
- false-neighbor work dominates creation CPU → build a conservative rejection model before more codecs.

A negative result that eliminates a seductive architecture is progress, but it does not consume a
numeric CMPCT version.
