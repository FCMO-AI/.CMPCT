# CMPCT Active Fundamental Research Thesis

Status: **Foundry primary thesis — F-01 / ORACLE DESIGN**  
Canonical product/release state: unchanged.  
Forge work on proven v0.30 mechanisms continues independently.

Read first: `FUNDAMENTAL_RESEARCH_DOCTRINE.md`, `ASSUMPTION_LEDGER.md`, `RND_DOMINATION_RUBRIC.md`, current exact branch/CI/evidence.

---

# F-01 — General Reversible Structure Compiler

## Thesis state

`QUESTION -> ORACLE` **(current)**

No canonical reader/format claim. No release credit. No benchmark-row green credit.

---

## 1. Worldview delta

### Inherited assumption

CMPCT's representation vocabulary is primarily hand-designed. The encoder auditions a growing set of specific exact mechanisms — direct coding, packing, resemblance graphs, Mosaic relationships, Geometry transforms, bounded-drift edit programs, exact views, etc. A human/research campaign invents the next primitive, then writes an admission rule for it.

This worked spectacularly during the project's strongest periods, but it has an eventual failure mode: each successful idea becomes another fixed branch in a manually expanding transform tournament. Geometry can become G5/G6/G7 forever; graph work can become another series of edge types; good local research can converge toward an elaborate but finite vocabulary.

### Proposed model

> **Lossless representation can be treated as bounded synthesis/compilation of a short exact reconstruction program.**

The archive need not choose only among a fixed set of monolithic representations. A research compiler can compose a small typed set of reversible primitives, rank complete candidates by the exact serialized bytes required to reconstruct the target, and store only the resolved program + irreducible literals/streams. Decode executes the resolved program; it does not repeat synthesis.

### New representational capability if true

CMPCT gains a way to discover useful *compositions* and recurring reconstruction motifs that were not individually hand-authored as one new codec path. The research compiler can also act as an **invention oracle**: repeated winning programs reveal new general primitives worth distilling into the production encoder.

This would shift part of future development from:

`human invents transform -> encoder auditions transform`

toward:

`bounded reversible language -> research compiler discovers compact program -> exact evidence reveals reusable mechanism -> production distills mechanism`.

---

## 2. Why this is a fundamental thesis rather than another Geometry optimization

The thesis is not:

> Add more Geometry transforms.

It is:

> Challenge the assumption that the transform ladder itself must be manually enumerated.

Geometry is useful evidence because it proves that reversible layout programs can expose huge hidden regularity. Bounded drift is useful evidence because an exact edit program can outperform chunk-store representations. EntropyGraph/Mosaic are useful evidence because reconstruction relationships already behave like executable descriptions.

The compiler thesis asks whether these ideas belong to a more general reconstruction language.

---

## 3. External prior-art boundary

### Brevis — arXiv:2608.02162 (2026)

Recent independent work demonstrates **bit-exact tensor compression as program synthesis**. Brevis uses a typed reversible DSL, target-directed bounded A* search, a learned production prior for search order, complete serialized-size selection, and self-contained programs that decode without search or the learned prior.

This materially strengthens the plausibility of F-01 but does **not** solve CMPCT's problem. Brevis is tensor/checkpoint-specific; CMPCT targets arbitrary computer data, cross-object relationships, archive semantics, locality, recovery, integrity and generic content-inferred admission.

### OpenZL — arXiv:2510.03203 / arXiv:2605.09928

OpenZL demonstrates compression as a graph of modular reversible codecs with resolved encode-time graphs and a universal decoder. It strongly validates the operational value of a reusable execution vocabulary.

CMPCT must not become a schema-specific clone. The distinctive Foundry question is whether useful structure/relationships can be inferred from arbitrary bytes/objects and compiled into a bounded archive-aware program.

### Prior-art rule

Do not claim program synthesis, reversible transform graphs, byte transposition, front compression or similar primitives as individually novel. Novel CMPCT value, if any, must be in the **general arbitrary-data/cross-object/archive-aware composition, inference, exact-cost selection, bounded semantics and integration model**.

---

## 4. Strongest reasons F-01 may fail

1. **Composition headroom may be mostly fake.** Existing hand-authored transforms may already capture nearly all useful bounded structure; synthesis may merely rediscover them.
2. **Program overhead may eat the gain.** Tags, parameters, substream lengths, literal tables and integrity framing can erase detached-transform improvements.
3. **Search may explode.** A sufficiently expressive DSL creates a combinatorial representation space whose discovery cost is indefensible even as an oracle.
4. **Operators may interact badly.** Individually safe transforms can create pathological intermediate sizes/work or resource bounds when nested.
5. **Generality may be illusory.** A synthesizer can overfit a generator/frozen workload even without explicit benchmark identity if its grammar/priors implicitly encode the fixture.
6. **Decoder complexity may become a new tax.** A universal execution IR that contains every attractive idea can become harder to audit/port/fuzz than bespoke representations.
7. **Current Geometry may already be the right abstraction level.** A small fixed ladder plus exact audition may be more robust and nearly as effective as synthesis.

A useful negative result is therefore completely acceptable.

---

# 5. Oracle ladder

Do **not** begin by designing the final canonical DSL or integrating it into `src/cmpct`.

The first job is to measure whether compositional/program-synthesis headroom actually exists.

## O0.1 — Composition-only oracle using trusted existing primitives

### Question

Can compositions of **already-existing exact CMPCT ideas** beat the best current one-transform/manual tournament on bounded nodes, after full program-description charge?

### Deliberate simplification

Start with a tiny research grammar. Prefer wrappers around mechanisms already implemented/tested rather than new algorithms.

Candidate conceptual operators may include only a safe subset such as:

- `LITERAL/DIRECT`;
- `CONCAT/SPLIT` into bounded subranges;
- existing fixed-width lane transforms;
- existing delimiter/hierarchical Geometry views;
- existing prefix-plane/front structure;
- one simple exact scan/map operator only if an existing trusted implementation is available;
- existing backend compression as terminal leaves.

Do **not** add cross-object references yet. O0.1 isolates intra-object program composition.

### Search

Research-only bounded search. Exhaustive/DP/A*/branch-and-bound are all admissible. Search time is reported explicitly and receives **zero product-speed credit**.

Use exact target-directed validity where possible: generated subprograms must reconstruct their assigned target bytes by construction or immediate exact inverse check.

### Cost objective

`total_program_bytes = opcode/control + parameters + lengths/tables + literal/substream payloads + terminal compressed streams + any required padding/framing assumed by the oracle`

Do not rank by transform payload while ignoring the program.

### Baselines

For every node:

1. direct/current incumbent;
2. best existing manually nominated one-stage/known transform under equivalent payload accounting;
3. synthesized composition;
4. literal fallback.

### O0.1 positive signal

Any of the following is enough to advance to O0.2, provided exactness and hostile bounds survive:

- a synthesized composition materially beats the best manual candidate on **at least two structurally distinct cases** and the gain is not equivalent to simply selecting an already-existing single transform;
- a recurring multi-operator motif appears across generator-distinct cases and creates enough aggregate saving to justify distillation as a new primitive;
- the search exposes a previously unseen decomposition whose optimistic complete cost has large enough headroom to warrant a focused causal campaign.

No arbitrary percentage is sacred at O0.1. Report absolute bytes, relative bytes and gap closure. A microscopic one-off improvement is not sufficient to create a campaign identity.

### O0.1 negative signal

If a reasonably broad bounded corpus produces only equivalent rediscoveries of current transforms and no material composition headroom, record that exact result. Do **not** keep enlarging the grammar automatically. Determine whether the failure is:

- genuine lack of compositional opportunity;
- grammar too weak;
- search unable to reach plausible programs;
- control overhead too high;
- current manual transforms already near the useful frontier.

Only the latter three justify O0.2 changes.

---

## O0.2 — Minimal novel-operator probe

Run only if O0.1 evidence says composition/search is plausible but the current vocabulary is the limiter.

Add **at most one or two** generic reversible operator families motivated by observed residual structure, not by a favorite paper.

Candidate examples:

- generic width-preserving reversible `MAP` family (e.g. XOR/add/rotation/zigzag where well-typed);
- exact adjacent `SCAN`/difference family;
- bounded `REPEAT`/period structure;
- bit/field `MERGE/SPLIT` where width can be inferred/encoded generically.

Every added operator must answer:

- what residual regularity demanded it?
- can it be described content-agnostically?
- what decoder/parser/resource surface does it add?
- does it transfer?

If new operators fail, remove/retire them rather than preserving DSL bloat.

---

## O0.3 — Search-pruning / proof-directed compiler

Only after a meaningful synthesis space exists.

Attach cheap lower bounds/necessary conditions to partial programs so large subtrees can be proven unable to beat the incumbent before expensive child construction.

This is the bridge between F-01 and the existing exact-futility research direction.

A rich compiler that must enumerate everything is not a viable long-term Foundry tool.

---

# 6. Structural-transfer contract

A synthesis win on `tokenizer.json`, Shifted or any other famous fixture is insufficient.

Before `CAUSAL_SEED -> TRANSFER`:

1. freeze the grammar/operator semantics and search/admission rule;
2. test hostile negative cases that superficially expose the same separators/strides/repetition but should not profit after control charge;
3. test held-out structural variations created after the rule is fixed where practical;
4. include generator-distinct or real public cases with similar *structure* but unrelated semantic identity;
5. report which program motifs recur and whether their gain survives.

Priors/search ordering may use observable content features. They may never use benchmark names, paths, fixed corpus hashes or equivalent identity.

---

# 7. Decoder / IR constraint

F-01 is strongest if future encoder intelligence can grow without proportional reader growth.

Therefore distinguish:

- **research DSL** — may be richer and unstable;
- **candidate reconstruction IR** — only operators that repeatedly earn transfer evidence;
- **canonical reader IR** — smallest audited set that survives productization.

Never canonicalize an operator merely because the research compiler can use it.

A long-term success would be a compact reconstruction IR capable of absorbing several previously bespoke representations. A long-term failure would be an ever-growing bytecode VM whose only advantage is that it can express every experiment.

---

# 8. Interaction with current Forge work

F-01 does **not** supersede or pause productization of proven mechanisms.

### Bounded drift

The current strict Shifted bounded-drift win is a Forge asset. Continue generic admission, recovery/locality, canonical semantics, native/platform and full-matrix prerequisites. It may later inform an EDIT operator in the research language, but do not delay its convergence merely to wait for F-01.

### Analytics

Current evidence says major debt is D2/D3 execution/search economics. Continue exact work-elimination/native/proof-directed work there. Do not turn Analytics into the F-01 discovery fixture by identity.

### Geometry

Geometry is the nearest existing mechanism family to F-01. Preserve its current evidence. Use its primitives as trusted controls. The purpose of F-01 is to test whether Geometry should evolve into a more general compiler abstraction rather than grow a manual transform ladder forever.

---

# 9. Product survival sketch

Even at ORACLE state, preserve these intended boundaries:

- exact byte reconstruction;
- bounded logical node sizes for synthesis/inversion experiments;
- deterministic stored resolved program;
- no search at decode;
- explicit output lengths and overflow checks;
- per-operator resource validation before allocation/work;
- authenticated physical program/payload representation if advanced to archive form;
- shallow/bounded cross-object dependencies if later introduced;
- locality and decode-unit accounting before O2;
- literal/direct universal fallback;
- optional research intelligence never required to read an archive.

---

# 10. Decision law

At the end of each substantive F-01 experiment record:

```text
thesis: F-01 General Reversible Structure Compiler
state_before: <QUESTION|ORACLE|CAUSAL_SEED|TRANSFER|...>
worldview_tested: <one sentence>
search_space: <operators/bounds>
incumbent: <exact comparator>
headroom_result: <bytes/relative/gap closure>
program_overhead: <bytes>
search_cost: <time/RSS; explicitly O0 debt>
transfer_scope: <cases>
strongest_simpler_explanation: <one sentence>
strongest_surviving_objection: <one sentence>
decision: <ADVANCE_RESEARCH|REFORMULATE|HAND_TO_FORGE|REHABILITATE|RETIRE>
state_after: <...>
next_decisive_test: <one sentence>
```

Do not end a run with merely “promising.”

---

# 11. Secondary questions — do not deep-implement yet

While F-01 is the primary thesis, keep only cheap headroom probes for:

- **F-02 Synthetic Basis / FactorGraph:** can a charged latent basis beat best real-base/Mosaic controls for an entire family?
- **F-03 Residual Graph:** do exact edit/delta residual families contain enough second-order shared structure to merit factoring?
- **F-04 Self-indexed reconstruction structures:** can some compressed structure eliminate part of the separate index/control tax while retaining practical member/range access?

Do not let secondary questions fragment the primary thesis unless an oracle reveals dramatically larger headroom.

---

# 12. Immediate next action

**Build O0.1 as the smallest research-only composition oracle.**

Before implementation:

1. inventory the safest reusable current Geometry/direct transform functions and their exact cost model;
2. define the tiny grammar and canonical research serialization charge;
3. select bounded discovery + hostile + held-out structural cases without giving the compiler workload identity;
4. preregister what result advances, reformulates or retires O0.1;
5. only then implement/search.

The objective of the first run is not to produce v0.30 bytes.

It is to answer one scientific question cleanly:

> **Is there material compression headroom in composing exact representations that the current hand-authored tournament cannot see?**

If yes, CMPCT has evidence for a new research architecture. If no, we have prevented a seductive meta-compressor project from consuming months without proof.