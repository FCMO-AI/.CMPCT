# CMPCT ONE — Architecture Canon

**Version:** 0.1  
**Date:** 2026-09-04  
**Status:** Foundational research architecture canon  
**Authority:** `research/cmpct1`  
**Experimental lineage:** `CMPCT1-ONE` / current seed `ONE-G0.1`  
**Depends on:** `AGENTS.md`, `docs/AGI_ENGINEERING_STANDARD.md`, `docs/FUNDAMENTAL_RESEARCH_DOCTRINE.md`, `docs/BREAKTHROUGH_REHABILITATION.md`, `docs/PERFORMANCE_RELEASE_GATE.md`

---

## 0. Canonical decision

CMPCT ONE will not be designed as a portfolio of unrelated compressors, transforms, container recipes, delta formats, grammar modes, structure codecs or special-case readers that merely compete and select the smallest output.

CMPCT ONE will be designed around **one underlying information-representation principle**:

> **Law + Surprise, with selective Crystallization.**

Every exact logical object exposed by CMPCT must be reconstructible from one bounded deterministic generative graph plus the irreducible information that graph could not predict.

Conceptually:

```text
D = U(G, S)
```

where:

- `D` is the exact logical information universe to reproduce, including exact file bytes and required filesystem semantics;
- `U` is the stable ONE reconstruction machine;
- `G` is the authenticated **Law graph**: deterministic or probabilistic structure describing what follows from already established information;
- `S` is **Surprise**: the exact remaining choices not implied by the Law;
- selected intermediate results may be **Crystallized** when storing them physically improves access, decode cost, parallelism, recovery, sharing or total system cost.

The encoder may use arbitrarily sophisticated discovery methods. The reader must never have to reproduce that discovery.

The central architectural asymmetry is:

> **Unlimited discovery intelligence on creation; bounded explicit execution on read.**

This document is the design authority for what CMPCT ONE is. `docs/roadmap/CMPCT_ONE_ENGINEERING_GRID_v0.1.md` is the companion realization authority for how to build and falsify it.

---

## 1. Why ONE exists

CMPCT's historical frontier repeatedly improved by changing its model of information:

- logical files and physical stored objects became separable;
- exact duplicate information stopped requiring duplicate storage;
- sparse holes, hardlinks and nested containers became reconstructible semantics rather than opaque bytes;
- EntropyGraph made an archive a reconstruction graph rather than a bag of isolated streams;
- resemblance reuse exploited near-equal information;
- Mosaic allowed one object to be explained from several roots;
- residual program packing recognized structure inside reconstruction programs;
- reversible DEFLATE work demonstrated that apparently entropy-dense historical bytes can sometimes be represented as underlying information plus exact reconstruction evidence.

Those advances exposed a structural problem: the project can keep accumulating increasingly capable mechanisms, but a reader-visible zoo eventually creates its own tax in metadata, dispatch, native parity, fuzz surface, portability, search/admission work and conceptual complexity.

ONE exists to subsume the useful ideas without preserving their accidental representation boundaries.

The desired endpoint is not:

```text
choose(Zstd, Mosaic, grammar, tensor codec, preflate, ...)
```

It is:

```text
observe information
→ construct one Law
→ encode only remaining Surprise
→ materialize Crystals only where useful
```

A future compression discovery should normally improve the ONE compiler's ability to discover Law rather than force a new permanent reader-visible mechanism.

---

## 2. The information model

### 2.1 Law

A **Law** is a bounded generative relation that predicts or deterministically produces output from already available information.

A Law may express relationships that today would be described as:

- repetition;
- copy/reuse;
- delta/prediction from another region;
- multi-source reconstruction;
- arithmetic/numeric progression;
- permutation/interleaving;
- grammar expansion;
- table or dictionary reference;
- statistical symbol prediction;
- reversible format reconstruction;
- any future exact relationship that can be compiled into the stable ONE algebra.

These are not separate archive modes. They are different shapes of Law.

### 2.2 Surprise

**Surprise** is the information needed to select the actual outcome where Law is not sufficient.

The deterministic and statistical cases are one continuum:

- if Law determines the output with probability 1, Surprise cost approaches zero;
- if Law gives a biased distribution, Surprise carries the information needed to select the actual outcome;
- if Law knows essentially nothing, the distribution approaches uniform and Surprise approaches the raw information cost.

Therefore random/incompressible data is not a different storage ontology. It is the limiting case of ONE.

### 2.3 Crystals

A **Crystal** is a physically materialized result that could otherwise be derived.

Crystallization is not a fallback codec. It is a placement decision inside the same information graph.

The compiler may crystallize an intermediate when doing so improves the global objective by reducing one or more of:

- reconstruction work;
- selective-read amplification;
- latency/critical path;
- repeated computation;
- memory pressure;
- corruption/failure blast radius;
- remote I/O;
- duplicate storage elsewhere through wider sharing.

A Crystal may represent information that never existed as a user file. The compiler is allowed to invent a useful latent basis when multiple outputs can be derived from it more cheaply than from the original physical arrangement.

### 2.4 Manifest

The **Manifest** maps user-visible semantics to ONE derivations.

It must preserve the product semantics already valued by CMPCT:

- exact regular-file bytes;
- directories;
- links;
- sparse extents;
- permissions/ownership/timestamps/xattrs/ACLs according to the eventual canonical format contract;
- transactional generations;
- content identity;
- recovery metadata;
- path safety and normalization.

File boundaries remain user semantics. They are not required to be compression-analysis boundaries.

---

## 3. The theoretical objective

ONE approximates a resource-bounded minimum description rather than pretending a generally computable perfect compressor exists.

For data `D`, optional context `C`, and resource contract `R`, the design objective is conceptually:

```text
minimize  encoded_graph_bytes + surprise_bits + crystal_bytes + required_metadata
```

subject to:

```text
U(G, S, C) == D exactly
resource_cost(G, D) <= R
```

`R` may constrain:

- encoder wall/CPU budget;
- decoder work;
- peak memory;
- bytes touched for selective reads;
- startup/open latency;
- parallel critical path;
- failure blast radius;
- remote range behavior;
- implementation/capability burden.

ONE therefore does **not** define compression ratio as the only objective. A 0.1% size saving that makes a 4 KiB range request decode gigabytes is not automatically a win.

The target is the strongest **information-access Pareto frontier** the same representation theory can provide.

---

## 4. One representation, not an opaque codec registry

### 4.1 Hard rule

The permanent ONE reader must not become a disguised registry of historical compressors.

The following is architecturally invalid as an endpoint:

```text
OP_ZSTD(...)
OP_MOSAIC(...)
OP_ATLAS(...)
OP_PREFLATE(...)
OP_TENSOR_CODEC_7(...)
```

Such a design only hides the zoo behind a VM.

### 4.2 What is allowed

The reader may expose a **small stable algebra of generic bulk reconstruction primitives** whose composition can express many families of information relationship.

Candidate primitive classes include, subject to evidence:

- bounded source-range reads;
- concatenation/slicing;
- repeat/fill;
- integer arithmetic under fully specified overflow semantics;
- XOR/add/subtract delta operations;
- fixed-stride and transpose/permutation operations;
- interleave/deinterleave;
- bit pack/unpack;
- bounded table lookup;
- predictor evaluation;
- consumption of Surprise under an explicit probability model;
- bounded checks/length assertions required for safe execution.

The final vocabulary must be smaller than the mechanism inventory it replaces. A primitive is justified because it is a reusable information operation, not because one benchmark needs an opcode.

### 4.3 Compile rich analysis into poor execution

The encoder may contain rich analyzers for ZIP, XML, JSON, SQLite, tensors, images, executable formats or other structures.

Those analyzers are **compiler knowledge**.

They should discover relationships, then compile those relationships into generic ONE Law whenever practical.

Doctrine:

> **Analyze rich. Compile poor.**

A DOCX parser should not automatically become a DOCX decoder requirement. A tensor analyzer should not force a tensor runtime into every reader.

---

## 5. ONE execution semantics

The reconstruction language must be deterministic, bounded and hostile-input-safe.

### 5.1 Prohibited capabilities

The canonical reconstruction machine must not provide:

- arbitrary syscalls;
- network access;
- filesystem access beyond authenticated archive inputs supplied by the reader;
- clocks/randomness;
- unrestricted jumps;
- unbounded loops;
- recursion without a statically enforced finite bound;
- self-modifying code;
- arbitrary dynamic loading;
- platform-dependent floating-point behavior;
- uncontrolled allocation.

ONE is an information dataflow machine, not an application VM.

### 5.2 Static/preflight resource knowledge

Before executing a derivation or serving a range, the reader must be able to establish or conservatively bound:

- expected logical output length;
- admissible input references/ranges;
- maximum scratch memory;
- maximum bounded repetitions/operations;
- required Surprise regions;
- reconstruction dependencies;
- applicable capability/version requirements.

Malformed or impossible declarations fail closed.

### 5.3 Bulk semantics

Primitives should operate on ranges/vectors, not byte-at-a-time instruction streams.

This is required for:

- SIMD;
- memory-bandwidth efficiency;
- kernel fusion;
- parallel execution;
- third-party scalar reference implementations that remain simple.

The semantic reference evaluator may be simple and slow. Production execution may lower the same Law into optimized native kernels.

### 5.4 Law fusion

An optimized reader may fuse chains of generic operations into implementation-specific kernels if and only if the fused path is semantically equivalent to the reference evaluator.

Optimization may change execution, never meaning.

---

## 6. Surprise coding

ONE requires one common conceptual Surprise interface rather than separate residual compressors attached to separate mechanisms.

Conceptually the Law exposes a sequence of choices/distributions, and the Surprise engine encodes the realized outcomes.

The first research implementation may evaluate rANS, tANS/FSE-style coding, range coding or another exact entropy backend. The architecture does not canonize one backend before measurement.

Required properties for the eventual physical Surprise representation include:

- exact deterministic decode;
- very high throughput;
- bounded memory;
- efficient small-stream behavior or raw/bypass escape;
- interleaving/parallel lanes where useful;
- restart/checkpoint semantics compatible with selective access;
- complete accounting of model/table/restart metadata.

A candidate entropy backend is an execution/physical-layout choice under ONE, not a second information theory.

---

## 7. Reconstruction Cones

CMPCT historically used bounded dependency depth because depth is a useful proxy for locality and pathological decode chains.

ONE's stronger long-term invariant is the **Reconstruction Cone**.

For every independently addressable logical range `r`, define `Cone(r)` as the authenticated subset of Law, Crystals and Surprise needed to reconstruct it.

The reader/compiler must be able to account for at least:

- bytes physically touched;
- bytes decoded;
- operation/work bound;
- peak memory;
- dependency fan-out/critical path;
- failure/corruption exposure;
- required external context, if any.

A deeper graph is only acceptable when these real costs remain bounded and justified.

### Conservative staging rule

Early Genesis experiments must not weaken existing locality merely because the final theory is broader. Until cone accounting has independent evidence, retain conservative depth/locality caps. Only then may ONE supersede the old depth proxy with the stronger certified cone invariant.

---

## 8. Creation architecture: observe once, think selectively

ONE must win a speed and efficiency contest as well as a density contest.

### 8.1 Fused observation pass

Creation should gather cheap evidence in as few memory passes as practical.

The observation kernel may simultaneously collect:

- rolling/content fingerprints;
- exact hashes where needed;
- entropy and symbol statistics;
- runs/periodicity;
- lightweight integer/stride cues;
- similarity sketches;
- locality and boundary candidates;
- repeated-pattern evidence;
- cheap format/structure hints.

Avoid independent rescans for every hypothesis family.

### 8.2 Marginal Information Yield

The scheduler should reason about expected benefit per resource cost.

A useful research quantity is:

```text
MIY = expected bits eliminated / expected extra compute
```

Additional views may price memory traffic, joules or wall time.

The exact scalar is not sacred. The doctrine is: **deep analysis must earn its compute budget**.

### 8.3 Opportunity-gated search

Expensive search is activated only where cheap evidence predicts meaningful headroom.

Candidate progression should prefer:

```text
cheap evidence
→ tiny sample
→ larger sample
→ lower-bound / benefit estimate
→ exact full proof only if still competitive
```

Most hypotheses should die before full encoding.

### 8.4 Branch and bound

The compiler maintains the best known complete description cost for a region/subgraph.

If a candidate's rigorous lower bound can no longer beat the incumbent after all required program/control/model metadata is charged, terminate it immediately.

### 8.5 Discovery cache

Compiler analysis may be cached by content identity and relevant compiler-version/features.

Useful cache entries may include:

- observation synopsis;
- proven Law fragments;
- rejected candidate families;
- lower bounds;
- known basis relationships;
- performance measurements.

The cache accelerates creation only. It is never required for reading an archive.

### 8.6 Incremental changed-cone compilation

Updates to persistent archives should reuse unchanged graph state and reconsider primarily the affected information region plus a bounded neighborhood where new sharing may change the optimum.

The long-term aim is for update work to tend toward changed information, not total archive size, whenever the graph permits it.

---

## 9. Predictor cooperation, not mechanism competition

A defining ONE goal is to let useful evidence cooperate before Surprise is encoded.

History, parent relationships, numerical structure, local symbol context, cross-file structure and other evidence may contribute to one final prediction.

The architecture should prefer:

```text
P(x | context) = combine(relevant predictors)
```

rather than:

```text
choose one compressor for this file
```

The compiler may still compare alternative Laws internally, but the output abstraction is a single generative graph and Surprise stream.

This is the point at which formerly separate compression ideas can fuse rather than merely coexist.

---

## 10. Information Basis and latent shared structure

ONE may create basis objects not present in the source namespace.

If several outputs are cheaper as transformations of latent `X`, the compiler may materialize or derive `X` and make those outputs depend on it.

Example shape:

```text
        X
      / | \
     A  B  C
```

where `X` is not a supplied file.

This is permitted only when complete cost wins after charging:

- representation of `X`;
- every derivation/program;
- Surprise;
- metadata/indexing;
- access/recovery costs;
- global admission/search carrying cost at the relevant evidence frontier.

This generalizes deduplication from "store equal supplied bytes once" to "store the smallest useful shared explanatory basis we can justify."

---

## 11. Persistence, versions and optional global context

### 11.1 Persistent immutable graph

ONE should naturally support immutable content-addressed graph nodes plus versioned root manifests.

Updates create new nodes/roots while reusing unchanged nodes. This aligns with CMPCT's existing append-generation and recovery direction.

### 11.2 Standalone closure remains the default

A normal `.cmpct` must remain independently reconstructible by default.

Optional cross-archive/global context may later reduce storage further, but the archive must explicitly declare those dependencies and provide a path to materialize a portable closure.

Do not silently turn CMPCT into a thin pointer file whose correctness depends on a disappearing service.

### 11.3 Seal operation

A future context-aware ONE implementation should support a conceptual operation equivalent to:

```text
cmpct seal thin-or-shared.cmpct portable.cmpct
```

which materializes the complete required dependency closure under the same logical identity.

---

## 12. Integrity, authentication and recovery

Identity, reconstruction and verification should converge on the same graph.

Every stored Crystal, Surprise region and relevant Law object should have authenticated identity appropriate to its role.

A Merkle-style graph/root should make it possible to determine:

- whether metadata is authenticated;
- whether touched physical information is authenticated;
- whether a complete logical object matches its declared identity;
- which logical ranges depend on a damaged node;
- which unaffected ranges remain independently recoverable.

Recovery must remain a format property, not prose.

ONE must preserve or improve CMPCT's existing principles of redundant/scannable metadata, committed generations, prior-generation fallback and salvage.

Crystallization may deliberately reduce corruption blast radius when the extra bytes are justified by the product objective.

---

## 13. Remote and selective access

Remote access is not a separate format mode.

A remote-capable reader plans the Reconstruction Cone for the requested range and issues only the authenticated range requests required by that cone.

The system must never silently fetch the whole archive to satisfy an API that claims to be range-local.

ONE physical layout should therefore optimize not only compressed size but also:

- number of remote requests;
- total requested bytes;
- dependency locality;
- restart/checkpoint placement;
- verification granularity.

These are solver inputs for crystallization/layout rather than a separate compressor.

---

## 14. Compiler intelligence and AI

The ONE compiler may use increasingly powerful proposal systems, including learned models or LLMs, to discover candidate Laws.

They receive **proposal authority only**.

Every accepted candidate must be reduced to deterministic ONE semantics, reconstructed exactly, fully costed and measured.

No neural model becomes a mandatory reader dependency merely because it helped discover the encoding.

Doctrine:

```text
AI proposes
→ deterministic ONE program
→ exact reconstruction proof
→ cost/resource measurement
→ accept or reject
```

The trusted evaluator remains the referee.

---

## 15. Lessons inherited from retired F-01

CMPCT ONE must not repeat the failed assumptions of the v0.30 F-01 General Reversible Structure Compiler campaign.

F-01 established useful facts:

- exact composition can create real description-length headroom;
- some multi-stage reversible programs beat one-stage controls after program bytes are charged.

But F-01's transfer review also established binding scoped negatives for the tested regime:

1. human structural labels such as `lane+record` / `lane+lane` were not a trustworthy general admission boundary;
2. operator inactivity on a seed did not justify global grammar pruning;
3. simply expanding the operator/grid space was not justified without a new content-derived causal predictor;
4. exact measured gain after expensive search is an encoder-tournament fact, not by itself a generic discovery policy.

ONE therefore requires **content-derived opportunity prediction and compute-aware search** as part of the architecture. It must not equate a larger synthesis grammar with progress.

The historical F-01 evidence remains reusable as an instrument and negative constraint. It is not silently relabeled as CMPCT1 evidence.

---

## 16. The speed constitution

CMPCT ONE is not allowed to become an overnight research compressor whose only virtue is ratio.

The core speed doctrine is:

> **Observe once. Reuse evidence. Search sparsely. Kill losers early. Fuse winners. Crystallize expensive truths. Vectorize everything.**

Creation optimization priority:

1. eliminate unnecessary search/work;
2. reuse prior analysis;
3. improve cache/memory locality;
4. vectorize bulk work;
5. parallelize independent work;
6. only then spend more compute on deeper discovery.

Eight cores doing useless work eight times faster is not success.

The reader performs no discovery and should have a short critical path dominated by bulk kernels and Surprise decode rather than dispatch or interpretation overhead.

---

## 17. User-facing utility

CMPCT ONE is intended to become the information substrate behind the same practical product promise as CMPCT, but stronger:

- create one archive from arbitrary files/filesystems;
- preserve exact bytes and filesystem semantics;
- extract everything quickly;
- open/list/read individual files quickly;
- serve byte ranges without whole-archive decode;
- survive partial corruption better than fragile solid streams;
- support transactions/versions and incremental updates;
- work locally and remotely;
- export to conventional formats where compatibility requires it;
- eventually support archive-native search/query when the Law exposes reusable structure, without making search indexes mandatory for every archive.

The user should not need to understand Law, Surprise or Crystals to use CMPCT.

The complexity exists to make the default archive better, not to turn compression into a research interface.

---

## 18. Non-goals

ONE is not:

- a collection of benchmark-specific codecs;
- a mandatory AI decoder;
- a general application virtual machine;
- permission to weaken byte exactness;
- permission to weaken integrity, recovery, path safety or resource limits;
- permission to hide creation cost;
- a reason to delete mature r24/v0.29/v0.30 evidence before succession is proven;
- a guarantee that every file can be compressed;
- a claim that minimum description length can be computed exactly;
- an excuse to call any sufficiently complicated graph "unified."

Simplicity at the reader boundary is a product requirement.

---

## 19. Success definition

CMPCT ONE succeeds architecturally when one reader-visible representation can express and efficiently execute the useful information relationships historically represented by separate CMPCT mechanisms **without retaining those mechanism identities as permanent reader modes**.

CMPCT ONE succeeds scientifically when automatic, content-driven Law discovery yields repeatable improvements that survive hostile transfer and complete cost accounting.

CMPCT ONE succeeds as a product only when it clears the repository's normal promotion law and produces a larger Pareto frontier across stored bytes, creation speed, extraction/read speed, selective access, memory, integrity, recovery and portability.

The strategic target is to supersede both v0.29 and the already-developed v0.30 frontier, including the inherited 15-workload contract. "15/15" is an engineering objective, not a claim until identical-input evidence proves it.

---

## 20. Canonical vocabulary

Agents should use this vocabulary consistently:

- **ONE** — the unified CMPCT information representation theory and runtime.
- **Law** — bounded generative relationship/prediction encoded in the ONE graph.
- **Surprise** — irreducible choices/information not implied by the Law.
- **Crystal** — physically materialized derivable information chosen for global system benefit.
- **Manifest** — authenticated mapping from logical filesystem semantics to ONE outputs.
- **Reconstruction Cone** — exact dependency/work/read set required to reconstruct a logical range.
- **Information Basis** — the set of stored/available facts from which outputs are derived; may contain latent compiler-invented objects.
- **Observation Kernel** — fused cheap analysis pass used to generate reusable evidence.
- **Opportunity Gate** — content-derived decision process determining where deeper discovery is worth compute.
- **Law Discovery** — encoder-only search for better explanations.
- **Law Fusion** — execution/compiler optimization that combines generic operations without changing semantics.
- **Portable Closure** — complete self-contained information required to reconstruct an archive without external context.

Historical terms such as Mosaic, EntropyGraph, Atlas, Axiom or individual codec names may be used when discussing lineage, experiments or discovery methods. They are not the desired permanent reader ontology for ONE.

---

## 21. Authority and change control

This canon may evolve during CMPCT1 research, but changes must be deliberate.

A change that alters the definition of Law, Surprise, Crystal, Manifest, deterministic execution, the non-zoo rule, or the core reader/encoder asymmetry is an architecture change and must:

1. state the problem with the current canon;
2. explain the stronger replacement principle;
3. preserve historical rationale rather than silently deleting it;
4. update the companion Engineering Grid where implementation gates change;
5. distinguish proposal from measured evidence;
6. survive Alice/Mission Lock, Ada/Builder and Bob/hostile review.

Do not mutate the canon merely because one experiment is inconvenient.

The architecture should be stable enough that agents can build against it while the compiler's discovery strategies evolve aggressively.
