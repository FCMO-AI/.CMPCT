# CMPCT v0.30 research — Representation Superoptimizer

Status: **ACTIVE CHILD RESEARCH — DO NOT MERGE — DO NOT VERSION-BUMP**  
Parent research branch: `agent/lattice-v030-breakthrough` @ `0338527d3a9e4f12df20448c52665d1c93c8b937`  
Parent research PR: #45  
Production floor remains CMPCT **v0.29.0 / canonical r24**.

This child campaign exists so the frozen G3/G4 and CMPNX14 gates on the parent branch can remain untouched while a more radical representation search is explored.

---

## 1. Mission lock

### Requested

Improve the Geometry/GIR direction using both current state-of-the-art lossless-compression ideas and genuinely new mechanisms. The result must be materially better, not merely different.

### Hard invariants

- byte-exact reconstruction;
- authenticated physical records / strong logical identity;
- bounded parser and transform work;
- bounded memory;
- no extension/MIME/private-corpus routing as an admission authority;
- explicit descriptor cost;
- explicit selective-read/dependency consequences;
- no canonical-r24 change during research;
- no release/version/website claim until the ordinary promotion gate is green;
- parent PR #45 remains unmerged.

### Disproof principle

A mechanism is rejected when its complete stored-cost gain is below its preregistered threshold, when its advantage disappears after descriptors/integrity/fallback accounting, when it relies on corpus-specific semantics, or when repairing its resource debt erases the gain.

---

## 2. What current SOTA already teaches us

Do not claim these primitives as CMPCT inventions.

### Columnar adaptive encodings

Apache Parquet already composes dictionary encoding, RLE/bit-packing, delta-binary packing, delta strings/front compression, and BYTE_STREAM_SPLIT. These establish that physical layout and lightweight typed encodings can matter as much as the final entropy codec.

Primary specification:
<https://parquet.apache.org/docs/file-format/data-pages/encodings/>

### ALP / FastLanes

ALP demonstrates that floating-point compression benefits from two-stage sampling/adaptation and vector-friendly representations rather than one fixed transform. Its public reference implementation and paper are maintained by CWI.

Reference implementation:
<https://github.com/cwida/ALP>

### FSST / OptFSST / OnPair

Modern string compressors show that field-local symbol tables remain valuable when random access matters, and that better symbol selection/encoding can still materially improve FSST-like representations.

OptFSST:
<https://arxiv.org/abs/2607.11271>

OnPair:
<https://arxiv.org/abs/2508.02280>

### Bitshuffle

Bitshuffle proves that bit-level transposition can outperform byte-level shuffling for typed binary arrays while remaining reversible and codec-agnostic.

Paper:
<https://arxiv.org/abs/1503.00638>

### Brevis

Brevis (August 2026) independently validates *lossless tensor compression as program synthesis*: a typed reversible DSL, a bounded search, self-contained reconstruction programs, and explicit archive-size accounting. Therefore `compression as program synthesis` is **not** claimed as novel here.

Paper:
<https://arxiv.org/abs/2608.02162>

### Equality saturation / e-graphs

Compiler work on equality saturation shows how many equivalent programs can be retained without destructive phase ordering, then globally costed afterwards.

`egg`:
<https://arxiv.org/abs/2004.03082>

---

## 3. CMPCT-specific synthesis: Representation Superoptimizer (RSO)

The proposed step beyond the parent GIR is to search **one typed reversible representation space spanning both intra-object and inter-object structure**.

Instead of:

`chunk -> choose transform -> choose compressor`

RSO models:

`logical tree -> observations -> reversible representation graph -> exact-cost extraction`

The same optimizer can retain alternatives from:

- Mosaic / direct-base relationships;
- PrefixGraph / version-family relationships;
- Geometry G1-G4;
- binary word/bit-plane transforms;
- latent sequence types and field codelets;
- entropy-codec/fallback choices.

The important distinction from Brevis is scope and objective. Brevis synthesizes tensor reconstruction programs. RSO targets arbitrary file-tree bytes and must price archive bytes together with selective reads, dependency depth, recovery fan-out, parser risk, memory and portability.

---

## 4. Novel hypothesis A — Latent Types as reversible hypotheses

A discovered field is **not declared to be an integer/string/float**. Instead the encoder may propose an executable reversible hypothesis such as:

- canonical integer sequence;
- zero-padded integer template;
- fixed-scale decimal sequence;
- low-cardinality symbol stream;
- periodic sequence;
- affine / sawtooth counter;
- delta or delta-of-delta sequence;
- restricted-alphabet byte string;
- fixed-width binary words;
- generic bytes.

A latent type is admitted only if:

1. the proposed parser accepts every value in the bounded field;
2. its renderer reconstructs every original byte exactly (including lexical form when relevant);
3. its descriptor + residuals + final codec output are smaller than the incumbent;
4. its resource certificate is inside policy.

**Novelty target:** schema becomes a compression *candidate with an inverse proof obligation*, not trusted input metadata.

### Residualized latent types

Near-fits need not be thrown away. A microprogram may model most values and encode explicit exceptions/residuals. This borrows the general learned-compressor idea of model + residual, but uses tiny deterministic models with no external training dependency.

Examples:

- `value[i] = base + step*i` + sparse exceptions;
- `value[i] = offset + ((start + step*i) mod modulus)` + sparse exceptions;
- repeated period + exception bitmap;
- dictionary code + verbatim escape values.

Residual bytes are first-class cost. A model is rejected if its residual stream erases the gain.

---

## 5. Novel hypothesis B — Algebraic Bitplane Geometry

Byte lanes are not the end of binary geometry.

For a candidate word width/alignment, first expose bit planes (Bitshuffle prior art), then search a **small invertible algebra** before entropy coding:

- identity;
- XOR with previous word;
- modular subtraction from previous word;
- invertible intra-word XOR-shifts;
- bounded elementary GF(2) basis changes among correlated bit planes.

A primitive such as `plane_i <- plane_i XOR plane_j` is exactly invertible and costs only a tiny descriptor. A bounded beam search can therefore ask whether a different binary basis makes exponent/flag/high-order planes sparser without changing a single source bit.

This is intentionally narrower than an arbitrary learned transform: every operator has a trivial portable inverse and an explicit operation bound.

### Why it may matter

The parent Geometry wins are strongest on text/structured streams. Large `.npy`/tensor-like members still dominate several workloads. Algebraic Bitplane Geometry targets those bytes directly while preserving arbitrary-byte fallback.

---

## 6. Novel hypothesis C — cross-level equality-preserving search

The current pipeline can suffer a phase-ordering problem: an early choice (e.g. make a delta edge) can hide an even better later representation (e.g. structured Geometry on the direct object), or vice versa.

RSO should preserve equivalent reconstruction plans long enough to cost them globally. A practical implementation need not build an unbounded e-graph. Use a bounded typed equivalence set per logical region:

- direct physical view;
- Geometry views;
- latent-type views;
- bitplane/algebraic views;
- reference/delta views;
- pack-placement views.

Then extract the cheapest legal plan under the current research objective.

At promotion time the cost vector is at least:

`(archive_bytes, create_cpu, extract_cpu, peak_memory, read_amp, dependency_depth, recovery_fanout, parser_risk)`.

Research may temporarily expose create-CPU debt; hard safety/integrity constraints are never borrowable.

---

## 7. Search must itself be compressed

A representation superoptimizer can easily become a benchmark-cheating CPU furnace. Therefore search gets a budget.

Proposed hierarchy:

1. **O(n) observation pass** — delimiter statistics, run/cardinality sketches, word-alignment entropy, small period hashes, lane/bit-plane entropy, resemblance hints;
2. **cheap lower-bound screening** — reject candidates that cannot plausibly beat the incumbent after descriptor cost;
3. **bounded finalist synthesis** — only a small typed beam/A* frontier survives;
4. **exact compressor pricing** — run expensive codec work only for finalists;
5. **complete-artifact fallback** — old representation remains available until the entire artifact wins.

Every candidate records how much search work it consumed so future CPU rehabilitation can preserve the exact winning bytes.

---

## 8. Immediate experiments

### Experiment B1 — Schema-blind Bitplane Algebra

Target exact public binary members without trusting their filenames:

- analytics `features.npy`;
- ML `scales.npy`;
- ML `model.q4.bin` as an adversarial high-entropy control;
- analytics `features_compressed.npz` as an already-compressed control.

Audition word widths 2/4/8 and bounded alignments. Compare:

- direct Zstd-19;
- existing byte-lane Geometry;
- plain bitshuffle;
- previous-word XOR + bitshuffle;
- modular delta + bitshuffle;
- a bounded invertible XOR-basis transform + bitshuffle.

Frozen research intent: a candidate must beat the **existing direct/byte-lane incumbent**, not merely raw bytes. Controls may fall back exactly.

### Experiment L1 — Latent sequence microprograms

Target synthetic columns already discovered by G3, but do not use workload/file identity in the transform.

Initial microprogram vocabulary:

- constant;
- exact period;
- FOR/bitpack;
- delta;
- delta-of-delta;
- affine/sawtooth recurrence;
- low-cardinality dictionary;
- restricted-alphabet packing;
- generic raw field sequence.

Every codelet must have an independent inverse vector and bounded exception/residual stream.

### Experiment X1 — phase-ordering counterexample

Construct/publicly preserve at least one corpus where:

- Geometry-first beats reference-first;
- reference-first beats Geometry-first;
- a retained equivalence set finds the correct winner automatically.

If no such case exists, the e-graph/superoptimizer complexity is not justified.

---

## 9. Rejection conditions

Reject or defer this direction if:

- bitplane algebra cannot beat byte-lane Geometry by a material preregistered amount on exact binary workloads;
- latent types win only because the public synthetic generator happens to use perfect counters and fail adversarial perturbation;
- residualized microprograms become equivalent to an expensive generic compressor with worse portability;
- the bounded equivalence search produces no phase-ordering wins;
- repair of create/extract/memory debt erases the stored-byte advantage;
- a native/shared implementation would require unsafe or architecture-specific semantics for ordinary decoding.

---

## 10. Merge lock / parent relationship

This branch is a child research reactor. Do **not** merge it to `main` and do **not** merge it into the parent research branch merely because an isolated oracle is green.

Promotion order:

1. causal child experiment;
2. durable machine evidence;
3. adversarial/resource tests;
4. only then consider integrating the surviving primitive into the parent GIR/RSO design;
5. parent still must pass complete 15-workload and performance-debt rehabilitation;
6. user must explicitly authorize any eventual merge/release.

Footnote: the goal is not to accumulate every SOTA encoding. The goal is to create the smallest reversible language that makes CMPCT discover *why* a representation is compact, then retain only operations that produce measurable Pareto movement.