# CMPCT ONE — Engineering Grid / Realization Plan

**Version:** 0.1  
**Date:** 2026-09-04  
**Status:** Binding realization plan for the CMPCT1 research branch  
**Depends on:** `docs/architecture/CMPCT_ONE_CANON_v0.1.md`  
**Primary branch:** `research/cmpct1`  
**Control branch:** `research/cmpct1-cleanroom`  
**Current research seed:** `ONE-G0.1`

---

## Mission

Turn the CMPCT ONE architecture into a real, measurable, independently falsifiable information representation that can eventually supersede the current CMPCT research frontier without weakening CMPCT's established product strengths.

The campaign is not complete when a DSL, VM, benchmark toy, synthetic miracle or elegant design document exists. It is complete only when ONE can repeatedly represent arbitrary real files/filesystems through one reader-visible Law + Surprise representation, provide competitive or superior density and speed, preserve bounded selective access/integrity/recovery, and survive the repository's normal promotion discipline.

The campaign must optimize for **useful information reduction per unit compute**, not maximum search, mechanism count or research spectacle.

---

# 0. Operating constitution

All CMPCT repository laws remain binding unless this branch explicitly supersedes a lower-level experimental assumption with stronger evidence.

Mandatory authority order:

1. measured/fingerprinted evidence;
2. correctness, byte exactness, integrity/authentication, hostile-input safety and data-preservation invariants;
3. `AGENTS.md`;
4. `docs/AGI_ENGINEERING_STANDARD.md`;
5. `docs/FUNDAMENTAL_RESEARCH_DOCTRINE.md`;
6. this Engineering Grid and `docs/architecture/CMPCT_ONE_CANON_v0.1.md` for CMPCT1 design/realization;
7. `docs/BREAKTHROUGH_REHABILITATION.md` for research debt;
8. frozen experiment preregistrations for their exact experiment;
9. mutable current-state/handoff documents;
10. scheduled-task prompts as execution kernels only.

If this plan conflicts with hard product/release law, hard law wins and the conflict must become explicit design debt rather than being silently ignored.

---

# 1. Agent execution model

Material ONE work uses the existing Alice–Ada–Bob cognitive stances.

## Alice — Mission Lock / Referee

Before implementation or a result-bearing experiment, record:

- exact objective;
- observed baseline;
- requested and inferred constraints;
- non-goals;
- authority/safety boundaries;
- falsifiable hypothesis;
- disproof/retirement result;
- evidence required for success;
- dimensions that must not regress silently;
- current experimental version/head/comparators.

Alice owns the definition of success.

## Ada — Builder / Architect

Ada:

- begins from the simplest credible ONE representation;
- reuses repository capabilities before inventing duplicates;
- converts historical mechanisms into ONE discovery/IR rather than preserving reader-visible silos;
- implements the smallest decisive experiment;
- measures complete description bytes and exported runtime cost;
- prefers general laws over benchmark identity or extension-based dispatch.

## Bob — Hostile Reviewer

Bob attempts to reject the result by testing:

- incompressible data;
- already-compressed/media data;
- tiny files;
- giant files;
- false patterns;
- adversarial structure labels;
- malicious programs/resource declarations;
- selective-read amplification;
- memory/CPU bombs;
- corruption locality;
- nondeterminism;
- hidden parser/codec dependencies;
- benchmark leakage;
- uncharged Law/control/model bytes;
- reader-complexity growth;
- search costs hidden behind an oracle.

A material checkpoint does not pass because the implementer is pleased with it.

---

# 2. Completion axes

Every work package is evaluated on two independent axes.

## Axis A — Representation/engineering completeness

As applicable:

- exact semantics specified;
- code implemented rather than mocked;
- deterministic reference behavior;
- unit/property/adversarial tests;
- independent oracle or hand-built vectors;
- malformed-input/resource limits;
- durable evidence and negative results;
- current-state/continuation packet;
- exact-head CI.

## Axis B — Operational effect

As applicable:

- stored-byte effect;
- creation wall/CPU effect;
- extraction/read throughput;
- peak memory;
- selective-read bytes/work;
- corruption blast radius;
- reader code/binary burden;
- representative public/neutral corpus transfer;
- competitor comparison under equivalent semantics.

A beautifully implemented mechanism with no useful effect is not a CMPCT breakthrough. A synthetic size win with no engineering completeness is not a product mechanism.

---

# 3. Required repository structure

The campaign should converge toward this layout unless implementation evidence justifies a better one:

```text
experiments/one/
  README.md                 # zero-history research entrypoint
  VERSION                   # experimental ONE-Gx.y identifier
  ir.py / ir/               # reference semantic objects
  vm.py                     # reference evaluator
  surprise.py               # conceptual/physical Surprise experiments
  observe.py                # fused observation prototype
  discover.py               # Law discovery orchestration
  cost.py                   # full description/resource cost model
  cones.py                  # reconstruction-cone accounting
  crystal.py                # materialization solver
  cache.py                  # discovery cache experiments
  legacy_import.py          # translate historical discovery into ONE IR
  state/                    # machine-readable experiment state/receipts

benchmarks/one/
  one_microbench.py
  one_transfer_corpus.py
  one_hostile_corpus.py
  one_speed_bench.py
  one_access_bench.py

 tests/one/
  conformance/
  property/
  hostile/

native/one-core/            # created only after semantics earn native work

docs/architecture/
  CMPCT_ONE_CANON_v0.1.md

docs/roadmap/
  CMPCT_ONE_ENGINEERING_GRID_v0.1.md

docs/one/
  CURRENT_STATE.md
  ADR-*.md
  NEGATIVE_EVIDENCE.md
```

Do not create all directories merely to satisfy the diagram. Create them when the first real artifact needs them.

---

# 4. Experimental version law

CMPCT1 research identifiers are deliberately cheap and independent of canonical project versions.

Suggested families:

- `ONE-G0.x` — representation semantics / universal derivation proof;
- `ONE-G1.x` — Surprise/statistical prediction;
- `ONE-G2.x` — fused observation and opportunity gating;
- `ONE-G3.x` — automatic Law discovery and composition;
- `ONE-G4.x` — Reconstruction Cones / Crystallization;
- `ONE-G5.x` — native/vectorized execution;
- `ONE-G6.x` — structural lifting / persistent graph / advanced discovery;
- later families only when the architecture genuinely changes.

Research IDs may advance often when useful for evidence. They do not change `pyproject.toml`, canonical format revision or public release identity.

Every result-bearing checkpoint records exact Git SHA in addition to the friendly research ID.

---

# 5. Engineering Grid

## ONE-00 — Authority, baseline and frozen comparators

**Purpose:** Prevent CMPCT1 from manufacturing progress by losing track of what it must supersede.

### Deliverables

- confirm `research/cmpct1` exact head and `CMPCT1_VERSION`;
- preserve frozen v0.29/main pivot authority;
- preserve frozen authoritative v0.30 comparator head/evidence;
- recover the complete 15-workload inherited matrix and exact semantics;
- identify canonical r24 product semantics that ONE must not silently weaken;
- create `docs/one/CURRENT_STATE.md` once code work begins;
- capture F-01 retired-thesis constraints in the ONE negative-evidence ledger.

### Gate

An agent with no chat history can state exactly:

- what ONE is;
- what branches/heads are authorities;
- what v0.29/v0.30 evidence must be beaten or preserved;
- what hard invariants cannot be borrowed;
- the next experiment and its disproof rule.

---

## ONE-01 — Minimal Law IR and deterministic evaluator

**Purpose:** Prove that ONE has a coherent reader ontology before optimizing compression.

### Minimum semantic capabilities

Represent through one generic graph vocabulary:

- literal/Surprise-backed bytes;
- source-range reuse;
- concatenation/slicing;
- repeat/fill/zero regions;
- bounded integer delta/XOR/add relationships;
- multi-source reconstruction;
- exact output length/hash assertions.

Do not add `MOSAIC`, `ZSTD`, `PREFLATE`, `GRAMMAR` or other opaque mechanism opcodes.

### Required tests

- hand-built tiny programs with exact expected bytes;
- malformed node types/fields;
- invalid references;
- integer overflow/underflow policy;
- cycles;
- output-length mismatch;
- bounds/resource declarations;
- deterministic byte-for-byte repeat runs.

### Independent oracle

At least one set of conformance vectors must be constructed independently of the primary encoder. Builder + reader agreement alone is insufficient.

### Gate

A second implementation or independent oracle agrees on semantics, and the same evaluator reconstructs literals, reuse, repetition, sparse regions and multi-parent exact outputs without reader-visible mechanism categories.

### Kill/reform condition

If representing current simple relationships requires excessive control bytes or a reader vocabulary comparable in complexity to the zoo it replaces, revise the IR before moving forward.

---

## ONE-02 — Surprise as the universal residual

**Purpose:** Remove RAW/residual as separate ontologies and unify deterministic/statistical representation.

### Deliverables

- define conceptual `CHOICE` / probability semantics;
- define how uniform/raw information is represented as the limiting case;
- prototype at least two entropy backends behind identical semantics;
- fully charge probability table/model/restart metadata;
- support bounded independent Surprise segments suitable for later seeking/parallelism.

### Benchmarks

- tiny streams;
- highly biased symbols;
- near-uniform bytes;
- mixed distributions;
- many small independent streams;
- large sequential streams;
- decode throughput and table-setup cost.

### Gate

The same ONE semantics encode deterministic reuse, biased residual information and incompressible bytes without switching information models; the physical Surprise backend has a measured credible path to high-throughput native decode.

---

## ONE-03 — Fused Observation Kernel

**Purpose:** Make discovery cheap enough to scale to arbitrary archives.

### Hypothesis

A single cache-friendly observation pass can produce enough reusable evidence to nominate most high-value early Law candidates more cheaply than separate mechanism-specific rescans.

### Signals to prototype

- rolling/content fingerprints;
- exact hash accumulation where required;
- symbol/entropy summaries;
- run/periodicity features;
- lightweight stride/numeric cues;
- similarity sketches;
- candidate boundaries/locality;
- repeated-pattern summaries.

### Performance requirements

Measure:

- bytes scanned per second;
- cycles/byte where available;
- memory bandwidth;
- peak temporary memory;
- cache behavior if practical;
- value of every emitted feature family.

### Gate

The observation pass approaches a practical memory-bandwidth-oriented regime and demonstrably eliminates redundant rescans for later candidate families.

Any expensive feature that rarely affects decisions is removed, sampled or deferred behind an Opportunity Gate.

---

## ONE-04 — Cheap native Law discovery

**Purpose:** Build a credible general compressor using ONE itself before deep synthesis.

### Initial Law families

All compile to generic ONE IR:

- history/range matches;
- cross-object exact reuse;
- repetition/runs;
- simple bounded deltas;
- simple integer/stride predictors;
- lightweight context/statistical prediction;
- basic cross-file/version relationships discovered from content.

### Explicit prohibition

Do not solve ordinary-data losses by embedding opaque Zstd and declaring success.

Existing compressors may be used as baselines/oracles to identify missing predictive structure.

### Gate

ONE can compress broad ordinary data materially below raw storage and has a credible measured trajectory toward mature general compression density/speed without abandoning the unified representation.

### Diagnostic rule

When Zstd/LZMA/ZPAQ wins, record **what relationship/prediction ONE is missing**, not merely the size gap.

---

## ONE-05 — Absorb historical CMPCT mechanisms

**Purpose:** Prove that ONE can preserve CMPCT's strongest existing information relationships without preserving their reader-visible formats.

### Discovery adapters

Use existing algorithms as candidate discoverers, where useful, for:

- exact dedup;
- CDC/resemblance;
- EntropyGraph relationships;
- Mosaic multi-root reconstruction;
- residual-program structure;
- sparse/packed/nested exact relationships;
- v0.30 reversible-structure instruments.

### Required comparison

For each absorbed family compare:

```text
historical representation complete bytes
vs
ONE representation complete bytes
```

and:

```text
historical read/decode work
vs
ONE read/decode work
```

### Gate

At least the major existing structural wins can be expressed in ONE with acceptable or better complete cost and no new permanent mechanism opcode.

A family whose ONE translation is structurally larger exposes a design defect: either ONE lacks a reusable primitive or the historical mechanism contains a relationship the canon has not modeled correctly.

---

## ONE-06 — Opportunity-Gated Search and branch-and-bound

**Purpose:** Keep ONE from becoming computationally extravagant.

### Core mechanism

Every expensive candidate family must expose:

- cheap observable features;
- expected addressable bytes;
- expected saving range;
- expected compute/memory cost;
- lower bound on complete representation cost where practical;
- a stop/kill condition.

### Candidate ladder

```text
cheap nominate
→ micro-sample
→ bounded sample
→ estimate / lower bound
→ exact full evaluation only if competitive
```

### Required metrics

- candidates nominated per GiB;
- candidates killed at each stage;
- false-positive/false-negative rate against an oracle sample;
- extra CPU seconds;
- bytes saved;
- `bytes_saved / extra_cpu_second`;
- memory traffic/peak memory;
- regret versus deeper oracle search on sampled regions.

### F-01 constraint

Do not use human benchmark labels as the admission predicate. Do not globally prune an operator because it was inactive on one seed. The predictor must be content-derived and tested on generator-distinct positive and negative transfer.

### Gate

ONE obtains most of the available measured gain while evaluating only a bounded sparse fraction of the naive candidate universe.

---

## ONE-07 — Discovery cache and incremental compilation

**Purpose:** Make repeated/versioned use substantially cheaper after the first analysis.

### Deliverables

- content-addressed observation synopsis cache;
- versioned compiler-policy identity so stale decisions do not become authority;
- negative-search evidence where safe/useful;
- changed-cone invalidation;
- bounded neighborhood reconsideration when new information can change sharing.

### Tests

- exact repeat archive;
- one-byte edit;
- shifted insertion;
- mass rename with unchanged content;
- many unchanged files plus one new related file;
- cache corruption/staleness;
- compiler-version change.

### Gate

Repeated creation/update demonstrates major compute savings while preserving the same exact correctness and without making the cache necessary for decoding.

---

## ONE-08 — Reconstruction Cones

**Purpose:** Replace crude dependency proxies with direct accounting of the actual selective-access cost.

### Deliverables

For every independently addressable output range, compute/conservatively certify:

- physical bytes touched;
- bytes decoded;
- Surprise regions touched;
- operation bound;
- scratch-memory bound;
- dependency graph/fan-out;
- failure/corruption exposure.

### Adversarial tests

- deep but cheap derivation;
- shallow but huge-amplification derivation;
- malicious fan-out;
- cyclic references;
- enormous claimed output;
- many tiny dependencies;
- corrupted untouched dependency;
- corrupted touched dependency.

### Gate

The cone model predicts observed selective-read work closely enough to become an admissible solver constraint.

Until this gate passes, do not weaken inherited depth/locality bounds based on theory alone.

---

## ONE-09 — Crystallization solver

**Purpose:** Make compression, speed, locality, parallelism and recovery properties of the same representation rather than independent patches.

### Solver decisions

Materialize a derived node when the added stored bytes are justified by reductions in:

- repeated decode work;
- selective-read amplification;
- remote I/O;
- critical path;
- peak memory;
- corruption blast radius;
- duplicated basis elsewhere.

### Baselines

Compare:

- no Crystals except irreducible input;
- fixed-size checkpoints;
- inherited depth-1 strategy;
- cost-aware ONE crystallization.

### Gate

ONE demonstrates a larger size/access/speed Pareto frontier than simple fixed materialization policies on representative workloads.

---

## ONE-10 — Native ONE core and Law fusion

**Purpose:** Prove that generic representation does not imply generic slowness.

### Preconditions

Do not begin native production work until ONE-01/02 semantics have stable vectors and ONE-04/05 demonstrate enough value to justify the implementation surface.

### Native responsibilities

- bounded parser;
- resource preflight;
- authenticated source access;
- Surprise decode;
- generic bulk Law kernels;
- range/cone planner;
- content/hash verification;
- typed errors;
- scalar reference-equivalence tests.

### Optimization

- SIMD for vectorizable primitives;
- lane/interleaved Surprise decode where evidence supports it;
- operation fusion;
- streaming without giant temporaries;
- multithreaded independent cones;
- architecture-specific kernels behind portable semantic fallbacks.

### Gate

Native ONE materially outperforms the reference evaluator and demonstrates credible competitive decode/read throughput without changing semantics or requiring compiler intelligence at read time.

---

## ONE-11 — Rich analyzers, poor reader

**Purpose:** Exploit structure that byte-level heuristics cannot see while keeping the reader ontology unified.

### Candidate analyzer classes

- DEFLATE/ZIP family;
- tabular/numeric;
- tensor/model artifacts;
- selected document/container structures;
- selected media structures where exact reversible lifting has proven headroom.

### Rule

The analyzer may be arbitrarily sophisticated, but accepted output must compile into generic ONE Law + Surprise unless a truly irreducible new generic primitive is justified through architecture change control.

### Required transfer test

A structure-aware win must survive:

- independent real/public data;
- malformed input;
- semantically similar but differently serialized data;
- negative controls where the analyzer should decline;
- complete representation-byte charging;
- parser/discovery carrying cost.

### Gate

At least one real cross-representation or semantic-structure opportunity produces material gain unavailable to ordinary byte reuse while the reader remains generic.

---

## ONE-12 — Persistent graph, transactions and optional shared context

**Purpose:** Make ONE practical for backups, versions and long-lived stores.

### Deliverables

- immutable content-addressed nodes;
- versioned root Manifest;
- append/commit semantics compatible with crash recovery;
- unchanged-node reuse;
- prior-version recovery;
- optional external/shared Information Basis with explicit dependency identity;
- portable-closure/seal operation design.

### Gate

A versioned archive can update incrementally, survive interrupted commit, recover the previous valid state, and be sealed into a self-contained artifact without changing logical identity.

---

## ONE-13 — Hostile generalization campaign

**Purpose:** Prevent ONE from becoming an elegant synthetic compressor.

### Mandatory hostile families

1. incompressible/encrypted-like bytes;
2. already-compressed media;
3. tiny-file forests;
4. giant heterogeneous binaries;
5. sparse and metadata-heavy filesystem cases;
6. repeated/versioned trees;
7. deceptive periodicity/false numerical patterns;
8. structure that fits training/generator assumptions but breaks on transfer;
9. candidate-space explosion inputs;
10. malicious ONE programs/resource declarations;
11. corruption/recovery/locality attacks;
12. public real-world corpora not generated by ONE's fixtures.

### Gate

ONE's discovery policy is content-driven, declines bad opportunities cheaply, and does not depend on benchmark identity to avoid regressions.

Negative evidence is durable.

---

## ONE-14 — Full frontier confrontation

**Purpose:** Answer whether ONE should remain the primary CMPCT research direction.

### Comparators

At minimum:

- frozen v0.29 authority;
- strongest fair/reproducible deferred v0.30 authority;
- canonical r24 where relevant;
- ZIP/Deflate;
- solid tar+Zstd-19;
- ZPAQ method 5;
- 7z/LZMA2;
- other competitor required by current repository benchmark authority.

### Required evidence

- identical corpus tree/fingerprint;
- all 15 inherited workloads;
- archive bytes;
- create wall/CPU;
- extract/read wall/CPU;
- peak memory;
- selective-read amplification/work;
- integrity/recovery semantics qualification;
- deterministic repeatability;
- exact losing rows.

### Strategic target

The aspiration is to supersede the B30 15-workload ambition through one underlying ONE representation, not through benchmark-specific file-type switching.

`15/15` is not reportable until the actual gate is green.

### One-week decision checkpoint

At/after 2026-09-11 America/Mexico_City, perform the explicit Genesis decision review already defined by `docs/CMPCT1_GENESIS.md`.

If ONE has not yet beaten every comparator but has produced a materially stronger, causal and credible path, the decision may preserve ONE as primary research only if the remaining debt is explicit and the evidence justifies further runway under the thesis-lease doctrine.

If ONE has failed to outperform or credibly supersede both frozen v0.29 and deferred v0.30 after the agreed evaluation window, reactivate v0.30 as the primary near-term path while preserving ONE as durable research evidence.

---

## ONE-15 — Canonicalization / successor-format gate

**Purpose:** Promote only after ONE is a product, not merely research.

### Promotion requirements

Before ONE changes canonical on-disk CMPCT semantics it must have:

- byte-level normative format specification;
- independent golden vectors;
- at least one independently implemented/verified reader path;
- hostile parser/resource fuzzing;
- native core parity;
- deterministic mode;
- recovery/crash semantics;
- transaction semantics;
- selective-read proof/accounting;
- portability/ABI plan;
- ZIP export/interoperability implications;
- encrypted/authenticated metadata implications where relevant;
- complete direct-base release performance record;
- no open correctness/security/integrity debt;
- all applicable performance regression debt closed or an explicitly approved stronger product contract.

### Gate

Only then may ONE become a canonical format revision and consume a scarce CMPCT core release.

---

# 6. Work-package dependency graph

The intended critical path is:

```text
ONE-00
  ↓
ONE-01 ──────────────┐
  ↓                  │
ONE-02               │
  ↓                  │
ONE-03               │
  ↓                  │
ONE-04               │
  ↓                  │
ONE-05               │
  ↓                  │
ONE-06 ─→ ONE-07     │
  ↓                  │
ONE-08               │
  ↓                  │
ONE-09               │
  ├────────→ ONE-10 ─┤
  ├────────→ ONE-11 ─┤
  └────────→ ONE-12 ─┘
            ↓
          ONE-13
            ↓
          ONE-14
            ↓
          ONE-15
```

Parallel work is allowed when interfaces are stable and evidence remains attributable. Do not create five competing ONE grammars in parallel.

---

# 7. First implementation slice

The first real slice should be intentionally small enough to falsify the architecture quickly.

Implement:

1. ONE node/graph data model;
2. deterministic scalar evaluator;
3. `SOURCE`, `SLICE`, `CONCAT`, `REPEAT/FILL`, generic arithmetic/delta and Surprise-backed literal/choice semantics;
4. output identity and length checks;
5. exact resource preflight for the implemented primitives;
6. one hand-built independent conformance vector set;
7. translator for one existing simple delta/Mosaic-style recipe into ONE;
8. complete-byte cost accounting;
9. a microbenchmark for evaluator throughput/control overhead.

Do **not** begin with:

- LLM synthesis;
- dozens of format parsers;
- GPU kernels;
- global CAS;
- archive-native semantic search;
- hundreds of opcodes;
- a new canonical file extension/revision;
- a marketing benchmark.

First prove one grammar can represent the old relationships cleanly.

---

# 8. Mandatory benchmark families

## A. Ordinary heterogeneous data

Source/config, binaries, documents, mixed media, tiny files.

## B. Version/resemblance data

Insertions, shifts, near-duplicates, reordered blocks, repeated trees.

## C. Generated/structured information

Sequences, tables, numeric series, tensors, structured records with controlled exceptions.

## D. Cross-representation data

Same logical information serialized in materially different physical encodings where ordinary byte dedup has little leverage.

## E. Incompressible/already-compressed controls

Prove cheap decline and low overhead.

## F. Access/recovery

Random member/range reads, remote-like range source, corruption in touched/untouched regions, interrupted versions.

## G. Search-cost attacks

Inputs constructed to nominate many false candidates, defeat seed-local pruning and stress branch-and-bound.

---

# 9. Core quantitative metrics

| Dimension | Metrics |
|---|---|
| Density | total bytes, Law bytes, Surprise bytes, Crystal bytes, metadata |
| Creation speed | wall time, CPU time, cycles/byte where practical |
| Discovery efficiency | candidates/GiB, kill stage, bytes saved / extra CPU-second, oracle regret |
| Memory | peak RSS, temporary bytes, working-set/table sizes |
| Decode | GB/s, CPU time, startup cost, kernel utilization |
| Selective access | requested bytes, physical bytes touched, decoded bytes, operations |
| Parallelism | critical path, scaling 1/2/4/8+ workers, lane utilization |
| Integrity | corruption catch, touched/untouched behavior, whole-object identity |
| Recovery | latest-valid-generation recovery, damage locality, salvage success |
| Portability | reference/native parity, optional capability burden |
| Reader complexity | primitive count, parser/core size, dependency count |
| Generalization | positive transfer, false-positive rate, negative control behavior |
| Update efficiency | changed bytes vs reconsidered/scanned bytes, cache hit rate |

Every material result should state the dimensions it did **not** measure.

---

# 10. The Law Curve

ONE should record an anytime search curve where practical:

```text
compute/search budget → best complete representation bytes
```

A typical durable result may include checkpoints such as:

- observation-only;
- cheap Law discovery;
- medium search;
- deep search;
- oracle/gifted search when explicitly classified O0.

The desired property is monotonic best-known representation under increasing search budget, not monotonic runtime for one fixed heuristic.

This curve lets the project evaluate both ratio and **how efficiently ONE discovers ratio**.

---

# 11. CI and compute discipline

ONE must not worsen the repository's CI saturation problem.

### Fast lane

- semantic/unit/property tests;
- small deterministic conformance vectors;
- static/resource checks;
- short microbench smoke where stable.

### Deep research lane

- transfer corpora;
- heavy synthesis/oracle runs;
- broad competitor comparisons;
- native performance profiling.

### Release lane

Only when canonical promotion is actually in scope.

Use path gating, concurrency cancellation for superseded routing work, and durable exact-source receipts for result-bearing long runs according to existing CI architecture law.

Do not run the complete 15-workload campaign on every tiny ONE commit.

---

# 12. Negative-evidence law

A failed ONE idea is an asset when it narrows the search space honestly.

Record at minimum:

- hypothesis;
- exact tested regime;
- comparator;
- gifted assumptions;
- complete costs charged;
- observed failure;
- causal interpretation if justified;
- scope of the negative constraint;
- exact reopening condition.

Never generalize:

```text
"operator X lost here"
```

into:

```text
"operator X is globally useless"
```

without transfer evidence. F-01 already demonstrated why seed-local inactivity is unsafe as a universal pruning law.

---

# 13. Architecture Decision Records

Create ADRs as the design crosses irreversible or expensive boundaries.

Minimum expected set:

- **ADR-ONE-001:** Law IR primitive set and deterministic integer semantics.
- **ADR-ONE-002:** Surprise conceptual interface and physical entropy backend selection.
- **ADR-ONE-003:** graph/object identity and hashing.
- **ADR-ONE-004:** resource preflight and hostile-program limits.
- **ADR-ONE-005:** Reconstruction Cone model.
- **ADR-ONE-006:** Crystallization cost function.
- **ADR-ONE-007:** Opportunity Gate feature/predictor policy.
- **ADR-ONE-008:** discovery-cache identity/invalidation.
- **ADR-ONE-009:** native Law fusion and SIMD portability boundary.
- **ADR-ONE-010:** persistent graph / transactions / optional external context.
- **ADR-ONE-011:** structural-analyzer compile-away boundary.
- **ADR-ONE-012:** canonical format promotion/compatibility plan.

ADRs describe decisions after evidence, not speculative menus.

---

# 14. Non-regression constitution

Every promoted ONE change must preserve or deliberately strengthen:

- byte-exact logical reconstruction;
- filesystem fidelity;
- truthful complete-byte accounting;
- deterministic/reproducible semantics where required;
- hostile-input/resource bounds;
- authenticated-data boundaries;
- recovery of valid committed state;
- bounded/selective access according to declared contract;
- reader simplicity relative to encoder intelligence;
- no benchmark-identity policy;
- no private-data dependence for public claims;
- no hidden mandatory optional dependency;
- no deletion of historical evidence/notes to make ONE appear cleaner;
- ability to decline structure cheaply on incompressible or adversarial data.

Research seeds may incur explicit performance debt under `BREAKTHROUGH_REHABILITATION.md`. Correctness/security/integrity are not debt instruments.

---

# 15. Definition of "ONE has absorbed a mechanism"

A historical mechanism is considered absorbed only when:

1. its useful information relationship is expressible through generic ONE semantics;
2. the historical mechanism name is unnecessary for reading the resulting artifact;
3. complete representation bytes are competitive enough that the translation is not merely theoretical;
4. decode/access cost is bounded and measured;
5. discovery may still reuse historical code temporarily, but no permanent reader/parser island is required;
6. a future alternative discovery algorithm could produce the same kind of ONE graph without changing reader semantics.

Wrapping an old compressed payload in a ONE node is compatibility, not absorption.

---

# 16. Definition of "ONE is fast"

ONE is not fast because one hot kernel benchmarks well.

A defensible speed claim accounts for:

- observation cost;
- candidate nomination;
- rejected-candidate work;
- exact proof/costing;
- graph serialization;
- entropy coding;
- archive finalization;
- reader open/startup;
- selective/full decode;
- integrity work;
- memory traffic/peak memory;
- process-start semantics when comparing CLIs.

The project should prefer removing work to parallelizing waste.

Creation optimization order remains:

> **prune → reuse → locality → vectorize → parallelize → deepen search.**

---

# 17. Agent handoff requirements

Every substantive CMPCT1 activation leaves enough durable state that the next agent does not reconstruct strategy from chat.

At minimum record:

- exact branch/head;
- `CMPCT1_VERSION`;
- current Engineering Grid package/state;
- hypothesis tested;
- code/evidence produced;
- raw/durable benchmark receipt;
- strongest negative result;
- open regression debt;
- exact next decisive action;
- pending external jobs/CI with source fingerprint;
- whether any claimed result is O0, O1 or O2.

`docs/one/CURRENT_STATE.md` should become the compact zero-history handoff once implementation begins; this Engineering Grid remains the stable long-form plan.

---

# 18. Ultimate acceptance test

CMPCT ONE has realized its purpose when a skeptical independent engineer can do the following without chat history:

1. read the canon and this grid;
2. build the reference/native reader;
3. inspect the small generic reconstruction vocabulary;
4. create ONE archives from heterogeneous public corpora;
5. prove exact reconstruction;
6. observe that reuse, statistical coding, multi-parent reconstruction, structured/generative relationships and materialized access anchors all appear as one Law + Surprise graph rather than separate reader modes;
7. obtain competitive or superior size while remaining computationally practical;
8. request small ranges without hidden whole-archive decode;
9. corrupt selected stored regions and observe bounded authenticated failure/recovery behavior;
10. reproduce the benchmark records against v0.29/v0.30 and mature external competitors;
11. improve the encoder's discovery strategy without changing the stable reader semantics;
12. explain remaining losses honestly.

The holy grail is not "ONE has many tricks."

It is:

> **ONE has one theory capable of learning new tricks without becoming a new format every time.**

---

# Immediate next action

**Execute ONE-00 + ONE-01.**

Create the first implementation state packet and the smallest deterministic ONE IR/evaluator that can prove universal derivation semantics for literal, reuse, repetition, sparse/fill and multi-source reconstruction.

Do not optimize the benchmark before the representation itself is independently trustworthy.
