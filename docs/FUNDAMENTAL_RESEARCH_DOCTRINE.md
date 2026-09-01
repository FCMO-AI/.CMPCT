# CMPCT Fundamental Research Doctrine

Status: **normative for fundamental/invention research on the active CMPCT frontier**.

This document sits *above* `docs/RND_DOMINATION_RUBRIC.md` for research-question generation and *beside* it for execution. It does not weaken any release, benchmark, safety, integrity, locality, recovery, portability or no-regression requirement.

The hierarchy is intentional:

- `AGI_ENGINEERING_STANDARD.md` governs engineering quality, evidence and falsifiability;
- **this document governs what kinds of fundamental questions CMPCT should spend research effort asking**;
- `RND_DOMINATION_RUBRIC.md` governs diagnosis/convergence when a measured product or benchmark red must be closed;
- `BREAKTHROUGH_REHABILITATION.md` governs how a high-upside seed survives temporary regression debt;
- ordinary release/format/performance/platform law governs promotion.

The purpose is to restore and institutionalize the mode of development that produced the largest historical CMPCT advances: EntropyGraph, EntropyGraph II, Mosaic, Geometry and earlier changes that altered the archive's model of information rather than merely optimizing an existing path.

---

## 1. North Star: invent a better model of stored information

CMPCT research is not primarily a campaign to tune a fixed compressor until a fixed benchmark turns green.

The research North Star is:

> **Continuously expand the kinds of exact information relationships, reversible structures and physical organizations that CMPCT can discover and exploit across arbitrary computer data, while keeping the eventual reader bounded, deterministic, secure and practical.**

The strict frozen benchmark matrix remains indispensable, but it is a **court of product truth**, not the sole generator of scientific questions.

A red workload may reveal a missing abstraction. A green workload may still contain a large unexploited abstraction. Fundamental research is allowed and expected to investigate both.

The project should repeatedly ask:

1. What information is present that our current representation cannot see?
2. Which current assumption prevents us from sharing or transforming it?
3. What new exact abstraction would make it representable?
4. How much headroom exists if that abstraction were available perfectly?
5. Can the abstraction be made content-agnostic, bounded and cheap enough to survive into the product?

The intended outcome is not novelty for novelty's sake. It is a **larger achievable Pareto frontier**.

---

## 2. Historical pattern: the best CMPCT milestones changed the worldview

The strongest historical campaigns can be restated as worldview changes:

- native content-aware CMPCT: logical files and physical stored objects do not need to be identical;
- deduplication/hardlinks/sparse semantics: filesystem relationships can be information rather than duplicated bytes;
- nested-container virtualization: an exact container can be content plus an exact reconstruction recipe rather than opaque bytes;
- EntropyGraph: an archive can be an authenticated reconstruction graph rather than isolated compressed files;
- EntropyGraph II: near-equal information is still shared information even when exact chunk equality fails;
- Mosaic: one object may have several independent explanatory ancestors;
- Geometry: logical byte order need not be the physical order most favorable to compression.

These advances did not begin as scalar parameter sweeps. Each made a previously unavailable relationship expressible.

This doctrine tries to make that mode of thinking reproducible rather than accidental.

---

## 3. Two coupled engines: Foundry and Forge

CMPCT development has two different intellectual jobs. They must cooperate without being confused.

### 3.1 Foundry — fundamental invention

The Foundry asks what the archive does **not yet know how to represent**.

Its outputs are:

- fundamental theses;
- oracle experiments;
- new reconstruction/representation primitives;
- new exact search/proof methods;
- decisive negative evidence that closes conceptual territory;
- synthetic/adversarial instruments designed around causal structure;
- new abstractions that may eventually become product capabilities.

The Foundry is thesis-driven, not benchmark-cell-driven.

### 3.2 Forge — convergence and productization

The Forge takes mechanisms that already have evidence and makes the actual product stronger.

Its work includes:

- D0–D5 diagnosis;
- R0–R4 implementation/search/representation repair;
- strict ZIP/Zstd and v0.29 gap closure;
- exact futility and work elimination for known hot paths;
- rehabilitation of regression debt;
- generic admission;
- canonical semantics;
- reader/recovery/locality/native/Android/platform integration;
- final no-regression and release authority.

`RND_DOMINATION_RUBRIC.md` remains excellent Forge law.

### 3.3 Neither may cannibalize the other

Common failure A: the Forge consumes all available effort because its tasks are easier to estimate and finish. Result: a polished local optimum.

Common failure B: the Foundry continuously invents new ideas and strands mechanisms that already proved strict wins. Result: novelty theater.

Therefore:

- a proven D5 candidate receives convergence priority under S6;
- **at least one live fundamental thesis must exist whenever the project has no explicit reason to suspend Foundry work**;
- when no credible thesis exists, the next research allocation is a Foundry question-generation pass rather than another arbitrary micro-optimization;
- Foundry work may proceed orthogonally while CI/productization waits, but it may not rewrite or destabilize an exact product candidate without evidence.

---

## 4. Three frontiers, not one

Research failure often comes from asking production questions too early. CMPCT therefore distinguishes three frontiers.

### O0 — Oracle Frontier

Question: **What is possible if discovery were much easier than production allows?**

The Oracle Frontier may use deliberately generous conditions:

- exhaustive or expensive search;
- ideal base/anchor knowledge;
- expensive alignment;
- large offline indexes;
- learned or heuristic proposal systems;
- broad transform tournaments;
- idealized lower/upper bounds;
- temporary creation-time debt.

Hard invariants remain hard: reconstruction must be exact; claimed bytes must include the representation actually needed for reconstruction; benchmark identity cannot be baked into the representation; and results must be honest about what costs are gifted by the oracle.

Oracle work exists to estimate **headroom and causal reality**, not to masquerade as product performance.

If an extremely generous oracle cannot create material headroom, kill the idea before production engineering.

If the oracle exposes dramatic headroom, discovery/engineering cost becomes the next research problem instead of a reason to suppress the idea.

### O1 — Research Frontier

Question: **Can the mechanism generalize under bounded realistic semantics?**

The mechanism must now acquire:

- content-agnostic discovery/admission;
- bounded search and decode behavior;
- exact serialized-cost accounting;
- hostile negative controls;
- locality/dependency accounting;
- structural-transfer evidence;
- an explicit survival path.

Some runtime/product debt is still allowed under breakthrough rehabilitation.

### O2 — Product Frontier

Question: **Can canonical CMPCT actually ship the gain?**

All ordinary release law applies. Complete artifact cost, creation/extraction/verification, locality, recovery, integrity, native/platform parity, deterministic semantics, compatibility and exact common-fingerprint benchmark authority matter here.

Do not use O0/O1 evidence as O2 claims.

---

## 5. Radicality model: add R5 information-model invention

`RND_DOMINATION_RUBRIC.md` defines R0–R4. Fundamental research adds one level above that scale.

- **R0** measurement/disproof;
- **R1** local implementation optimization;
- **R2** execution architecture;
- **R3** search/admission algorithm;
- **R4** representation/physical semantics inside a broadly inherited information model;
- **R5 — information-model / reconstruction-ontology invention.** Change what CMPCT considers an object, relationship, explanatory source, reversible view, physical owner or reconstruction program.

Examples of R5 questions:

- must a useful base correspond to a real source object, or may CMPCT create a synthetic shared basis?
- must one target have one parent, or can information be factored across several independent sources?
- are residuals merely payloads, or can residual families themselves share structure?
- is a byte stream the primitive object, or can a short reversible program be the physical representation?
- should compression and indexing be separate, or can one compressed structure also answer useful access queries?
- must update history be a sequence of archives, or can temporal lineage itself be a compression dimension?

R5 is **not inherently better** than R1–R4. It is required only when seeking fundamental frontier expansion. Never call a new header, codec switch or threshold R5.

No R5 quota exists. The Foundry must, however, maintain R5-quality questions in the opportunity portfolio so the project never runs out of genuinely new models to test.

---

## 6. Fundamental Thesis object

Foundry work is organized around persistent **Fundamental Theses**, not isolated hourly tasks.

A thesis MUST be expressible without naming the benchmark that motivated it.

Bad thesis:

> Make `01_shifted_versions` smaller than Zstd-19.

Good thesis:

> Large families with sparse insert/replace/delete drift can be represented more compactly as bounded exact edit relations than as independently owned chunk stores.

A thesis record should contain:

### Worldview delta
- **Inherited assumption:** what CMPCT currently assumes.
- **Proposed model:** what becomes true if the thesis is right.
- **New representational capability:** what can be expressed after the change that could not be expressed efficiently before.

### Scientific case
- causal opportunity;
- strongest prior/adjacent mechanisms;
- plausible upside ceiling;
- strongest reason the idea may fail;
- smallest decisive oracle;
- disproof/retirement condition.

### Product survival sketch
- reader complexity;
- stored control/program overhead;
- dependency depth;
- locality/decode unit;
- recovery/integrity implications;
- hostile-resource behavior;
- optional-helper/native/platform burden;
- generic admission path.

### Transfer contract
- discovery cases;
- hostile/negative controls;
- held-out structural variants;
- at least one real or independently generated transfer case before claiming a general mechanism.

### State
One of:

`QUESTION -> ORACLE -> CAUSAL_SEED -> TRANSFER -> REHABILITATION -> CONVERGENCE -> PRODUCT_CANDIDATE`

or terminal:

`FALSIFIED`, `FAMILY_RETIRED`, `SUPERSEDED`.

An hourly activation should normally advance the active thesis rather than recreate project strategy from scratch.

---

## 7. The Assumption Ledger is the primary idea generator

Benchmark reds reveal failures. The **Assumption Ledger** reveals possible worlds.

Maintain `docs/ASSUMPTION_LEDGER.md` as a living map of assumptions currently embedded in CMPCT. Each entry records:

- assumption;
- why it historically existed;
- evidence supporting it;
- known counterexamples/tensions;
- inversion question;
- candidate R4/R5 territories;
- known negative evidence;
- easiest oracle capable of testing the inversion.

The Foundry should search for ideas by attacking assumptions with the largest combination of:

1. plausible hidden information;
2. cross-workload generality;
3. large oracle headroom;
4. cheap falsifiability;
5. bounded product survival path.

The ledger is not a to-do list. Many inversions should be wrong. Its purpose is to keep the project asking questions larger than the current benchmark matrix.

---

## 8. Information Opportunity Map

For important corpora/research instruments, distinguish *where the remaining cost comes from* rather than only recording final archive bytes.

When practical, decompose the opportunity into conceptual components such as:

- exact duplicate information;
- near-equal/resemblance information;
- multi-source composition;
- intra-object layout/field correlation;
- repeated reconstruction programs/grammar;
- residual-family structure;
- entropy-coding residual;
- metadata/index/control tax;
- locality/recovery tax;
- search/audition tax;
- verification/publication tax;
- incompressible floor.

This is not required to be a mathematically unique decomposition. It is a causal research map.

A major research question is attractive when it attacks a large unexplained component that several workloads share.

---

## 9. Headroom-first law

Before building a complicated new production mechanism, ask an unfairly favorable question:

> **If this idea were given ideal discovery and minimal nonessential overhead, could it move the frontier materially?**

Examples:

- perfect base selection;
- perfect clustering;
- framing-free payload floor;
- ideal scheduling floor;
- exhaustive transform search on bounded nodes;
- ideal synthetic basis chosen offline;
- optimal grammar/program for a small exact sample.

Outcomes:

- **oracle cannot win:** retire or reformulate early;
- **oracle wins narrowly:** probably a boundary fix, not a new campaign identity;
- **oracle wins dramatically:** preserve the thesis and attack discovery/product debt;
- **oracle exposes a different bottleneck:** update the worldview before implementation.

This complements exact futility. Exact futility proves a candidate cannot win cheaply; Oracle headroom proves whether a conceptual family is worth making practical at all.

---

## 10. Breakthrough classes

Do not use one overloaded word for every improvement.

### B0 — Boundary fix
Existing model; crosses a near boundary through a local change.

### B1 — Mechanism improvement
Removes or reorganizes a meaningful category of work/bytes inside the current model and transfers beyond one fixture.

### B2 — Frontier breakthrough
Creates a reusable capability that materially expands the achievable Pareto frontier across a structural family.

### B3 — Information-model breakthrough
Changes what information or relationships CMPCT can represent efficiently. Historical EntropyGraph/EntropyGraph II/Mosaic-class work belongs here.

A numeric milestone need not always be B3, but the Foundry's ambition is to keep searching for B2/B3 work.

**Magnitude alone is insufficient.** A 50% synthetic win produced by benchmark identity is invalid. A 5% cross-domain gain from a new universal exact representation may be more important.

---

## 11. Worldview Delta Test / new-noun test

Before calling a campaign fundamental, answer:

> **What can CMPCT represent, discover or prove after this work that it could not do before?**

Then answer:

> **Can the milestone be explained without naming the benchmark that motivated it?**

Strong answers tend to produce durable nouns: EntropyGraph, Resemblance Compiler, Mosaic, Geometry IR.

Weak answer:

> It tunes the effort threshold so Analytics is faster.

That may be excellent Forge work; it is simply not the identity of a Foundry campaign.

---

## 12. Structural-transfer gate

A mechanism discovered on one frozen case must prove that it discovered a **relationship**, not a fixture.

The preferred ladder is:

1. **discovery instrument** — the case that exposed the opportunity;
2. **hostile negatives** — data that superficially resembles the opportunity but should not select it;
3. **held-out structural variants** — generated after the mechanism/decision rule is fixed when practical;
4. **independent real or generator-distinct transfer case**;
5. **full frozen product matrix**.

The production encoder must not depend on benchmark identity, workload names, paths or frozen hashes.

A structural transfer test should vary causal dimensions such as edit density, ordering, alignment, sizes, noise, number of sources, false relatives and locality pressure rather than merely changing random seeds.

---

## 13. Decoder simplicity / asymmetric intelligence law

CMPCT should exploit a powerful asymmetry:

> **The encoder/researcher may be intelligent; the decoder must remain bounded and boring.**

Foundry/oracle work may use expensive search, optimization, learned proposal systems or external analysis **only to nominate an exact representation**.

Promotion requires the stored result to reduce to deterministic, independently checkable semantics.

Rules:

- learned systems may propose; they do not prove correctness;
- search may be expensive at O0; decode never repeats the search;
- every selected transform/program is explicitly serialized or otherwise deterministically implied;
- decoder resource bounds are independent of encoder cleverness;
- optional research intelligence must not become an accidental read dependency.

This allows aggressive research without turning archives into opaque model-dependent artifacts.

---

## 14. Reversible Structure Compiler direction

A major generalization opportunity is to stop hand-authoring an endless transform ladder.

Current Geometry-style work can be reinterpreted as fragments of a small reversible language:

`logical bytes -> reversible structure program -> residual streams -> entropy codecs`

A research compiler can search over bounded exact operators such as, where justified:

- literal/direct;
- split/concat;
- repeat/run structure;
- fixed-width lane/bit-plane views;
- delimiter/record geometry;
- prefix/delta/scan relations;
- bounded COPY/LITERAL/edit programs;
- exact multi-source references;
- exact invertible maps (XOR/add/rotation/zigzag/field separation where type is inferred or explicitly represented);
- nested exact views/inverses;
- bounded grammar productions.

The objective is **complete serialized size**, including program tags, parameters, literals, tables and required bases.

The initial compiler may be deliberately expensive and research-only. Its first job is to discover which reusable programs repeatedly win. Those recurring motifs can later be distilled into cheaper nomination/admission paths.

Do not simply grow a DSL because it is elegant. Every operator must earn itself through transfer evidence and reader-complexity accounting.

---

## 15. External prior art is vocabulary, not destination

Fundamental research MUST look beyond the current CMPCT codebase when the local vocabulary is saturated.

Adjacent sources include:

- general lossless compression;
- program synthesis and minimum-description-length search;
- database/columnar encodings;
- grammar compression and compressed self-indexes;
- backup/dedup/delta systems;
- source/version-control representations;
- error-correcting/recovery codes;
- content-addressed and object storage;
- computational biology repetitive collections;
- reversible preprocessing;
- information theory;
- compiler IRs and superoptimization.

Recent relevant examples that should inform, not dictate, CMPCT research include:

- **Brevis / Lossless Tensor Compression as Program Synthesis (2026):** typed reversible DSL, target-directed bounded A* search, bit-exact self-contained programs, exact serialized-size selection. Strong evidence that program-synthesis compression is viable in a specialized domain.
- **OpenZL (2025–2026):** compression as a graph of modular reversible codecs with a universal decoder and resolved encode-time graphs. Strong evidence for transform/graph composition, but largely structured/application-aware rather than CMPCT's desired arbitrary-data/content-inferred archive model.
- **ZipLLM / BitX (NSDI 2026):** evidence that deduplication, family discovery and delta compression can be substantially stronger when designed jointly around the structure of related objects.
- **dynamic/grammar-compressed self-index work:** evidence that compression and indexed access need not always be separate layers.

Do not copy a domain-specific system blindly. Extract the underlying information model, identify what would have to be generalized, and design CMPCT-specific falsifiers.

---

## 16. Candidate R5 research territories

These are **territories, not commitments**. The Foundry should attack them with cheap oracles and retire weak ones aggressively.

### 16.1 Synthetic Basis / FactorGraph

Current relationship systems often use real files/nodes as bases. Test whether families are better explained by a synthetic physical basis that never existed as a user file:

`basis + residual_1 + ... + residual_n`

versus best-real-base, Mosaic, direct and solid controls.

The synthetic basis must pay its full stored cost. This is interesting only if it creates material family-level margin.

### 16.2 Residual Graph / residual algebra

After factoring related objects, do not assume residuals are independent noise. Test whether residuals across a family share repeated positions, programs, motifs, bit patterns or geometry that can themselves be factored.

### 16.3 Reconstruction Grammar

Test whether repeated **procedures of reconstruction** are a redundancy class. Shared productions/programs could encode recurring edit/layout operations while parameters carry object-specific differences.

### 16.4 Self-indexed physical representations

Investigate representations where the compressed structure itself supports range/member/search/navigation operations, potentially removing duplicated index/state rather than bolting indexing onto compressed payloads.

### 16.5 Temporal EntropyGraph

Treat update history and generations as first-class relationships. Stable information, mutations and lineage may be more compressible than separately materialized generations.

### 16.6 Exact View Algebra

Generalize nested-container virtualization, precompression and layout transforms into composable authenticated reversible views. Different encodings of the same underlying information may share physical roots while exact view programs reconstruct original bytes.

### 16.7 Recovery/locality co-designed representation

Stop treating recovery and selective access only as taxes applied after compression. Search for organizations whose dependency/failure domains make both compression and recovery/access cheaper by construction.

### 16.8 Proof-directed representation compiler

Attach necessary conditions/lower bounds to transform/search operators so the compiler can prove large subtrees of the representation space futile before constructing them.

---

## 17. Portfolio diversity without novelty theater

The project should avoid both monoculture and random ideation.

At any time:

- one **primary fundamental thesis** should own deep Foundry work;
- up to two **secondary questions** may remain cheap-oracle candidates;
- the Forge may concurrently productize proven mechanisms;
- do not run five major representation campaigns merely to appear creative.

A new primary thesis is chosen because it has stronger headroom/information gain than the incumbent, or because the incumbent is falsified/blocked—not because the hour changed.

---

## 18. Research allocation law for hourly agents

Hourly execution is a scheduling mechanism, not the natural unit of scientific thought.

Therefore:

1. recover the **active fundamental thesis** before selecting work;
2. continue its next decisive experiment across activations until the thesis state changes;
3. do not restart ideation every hour;
4. do not optimize for commit count or number of patches;
5. one deep result that changes the causal model outranks several unrelated small commits;
6. while long CI waits, advance a dependency-safe Foundry or Forge lane without fragmenting the thesis;
7. when no active credible thesis exists, conduct a Foundry pass over the Assumption Ledger and recent external research;
8. when a proven strict candidate is D5, productize it rather than abandoning it for novelty, while maintaining the next Foundry question orthogonally where feasible.

**Time-filling research theater is forbidden.** A thesis document without a decisive experiment is not a breakthrough.

---

## 19. Foundry experiment design

Every material Foundry experiment uses four passes.

### Pass F0 — worldview challenge

State the inherited assumption and why it may be wrong.

### Pass F1 — generous oracle

Give the hypothesis enough advantage to reveal whether meaningful headroom exists. Prefer a small exact experiment over a production implementation.

### Pass F2 — causal adversary

Try to explain the oracle win using a simpler known mechanism. Add hostile controls. Ablate operators/sources. Determine what actually created the gain.

### Pass F3 — transfer and survival

Freeze the mechanism/admission rule, test structural transfer, and sketch product constraints. Then choose:

`ADVANCE_RESEARCH`, `REHABILITATE`, `HAND_TO_FORGE`, `REFORMULATE`, `RETIRE`.

Only after F3 should substantial canonical integration begin.

---

## 20. Negative evidence becomes scientific constraint

A failed experiment is valuable only if its implication is preserved.

Do not record merely:

> CDC residual store lost.

Record:

> Under equality -> bounded packed context -> recent-basis residual progression, CDC-owned decomposition retained a multi-megabyte optimistic payload deficit on the target structural family; further parameter sweeps inside the same ownership model lack a plausible crossing mechanism.

Future hypotheses must explain why they escape known constraints before receiving deep budget.

This turns autonomous failures into a shrinking search space rather than a recurring tax.

---

## 21. Complexity budget / concept compression

Fundamental invention may increase conceptual power while still making the final implementation unmaintainable. Complexity is a first-class cost.

For every candidate track:

- number of reader-visible primitives;
- grammar/control bytes;
- independent parser states;
- dependency depth/fanout;
- maximum decode work/memory;
- optional-helper dependencies;
- recovery cases;
- native/platform implementation burden;
- fuzz/security surface;
- interaction count with existing representations.

Prefer one orthogonal primitive that subsumes several special cases over many workload-specific codecs.

A useful meta-test is **concept compression**:

> Did this milestone make the architecture's explanation shorter or more general even if its implementation grew?

EntropyGraph-style unification passes this test. A pile of special-case policies does not.

---

## 22. Research-system anti-gaming rules

- Never label ordinary tuning R5.
- Never invent a thesis after seeing a favorable result merely to rationalize it.
- Never use a benchmark name/hash/path/identity as an encoder policy input.
- Never count gifted Oracle costs as product performance.
- Never make a DSL/graph larger solely because additional operators seem sophisticated.
- Never let a speculative Foundry idea strand a reproducible D5 strict win.
- Never let urgent Forge work permanently extinguish fundamental research.
- Never require a research thesis to improve all frozen workloads; require its **selection/admission** to avoid harming the eventual product.
- Never confuse number of green rows with mechanism magnitude.
- Never average away a product red at promotion.
- Never suppress a huge research win merely because its first implementation has explicit rehabilitable debt.
- Never preserve a miracle whose only survival strategy is permanent benchmark cheating or unbounded reader complexity.

---

## 23. Meta-falsification of the doctrine

This process itself can fail.

Revisit the doctrine if:

- six substantive Foundry activations produce no decisive new evidence, family retirement or material headroom;
- active theses repeatedly collapse into benchmark-specific tuning;
- the Assumption Ledger produces only familiar codec ideas;
- three high-priority theses fail for the same hidden reason;
- a major breakthrough arises from a path this system would have rejected;
- process documentation consumes material engineering time;
- the Foundry repeatedly generates mechanisms with no credible bounded reader/product path.

The remedy is to change the question-generation system, not lower benchmark truth.

Documentation overhead should remain small. The minimum durable state is the Assumption Ledger, one active thesis record/campaign note, exact experiments/evidence, and normal repository handoff truth.

---

## 24. Immediate application to the current v0.30 frontier

### Bounded drift

The strict Shifted bounded-drift result has crossed the research size+create boundary. It is now primarily a **Forge/convergence lane**: generic admission, recovery/locality semantics, canonical integration, native/platform parity and full-matrix authority. Do not keep tuning Shifted merely because it produced the discovery.

### Analytics

Existing evidence classifies major remaining creation debt as D2/D3 rather than D4. Continue work-elimination/proof-directed/native execution there under the Domination Rubric. Do not invent a new information model merely to solve a known execution/search problem unless new evidence changes the diagnosis.

### Geometry

Geometry remains both a concrete representation campaign and a possible seed for a larger Foundry thesis:

> **Can arbitrary exact data be compiled into a short reversible structure program instead of selecting from an ever-growing handwritten transform ladder?**

The next fundamental question is therefore not simply G5. It is whether a bounded reversible compiler can *discover* useful compositions and expose new recurring operators while exact serialized cost and hostile controls prevent overfitting.

### Next Foundry requirement

Maintain a primary R5 question while the current strict winner is productized. The first recommended oracle family is the **Reversible Structure Compiler**, with Synthetic Basis/FactorGraph and residual-family factoring as secondary headroom probes.

---

## 25. Final doctrine

**Benchmarks tell CMPCT when it is wrong. They do not get exclusive authority over what CMPCT is allowed to imagine.**

Use the Forge to make proven ideas exact, fast, portable and dominant.

Use the Foundry to ask which assumptions about stored information are unnecessarily primitive.

Start fundamental work from a thesis about information, not a workload name.

Measure oracle headroom before spending heavily on production engineering.

Let expensive encoders discover simple exact representations; keep the reader bounded and deterministic.

Demand structural transfer before calling a fixture win a mechanism.

Preserve negative evidence as constraints on future thought.

Retire exhausted representations instead of lovingly optimizing their floors.

Productize real wins instead of abandoning them for novelty.

And keep searching for the next change that lets us say:

> **Previously CMPCT could not express this relationship. Now it can.**

That is the standard for returning CMPCT to breakthrough-first development.