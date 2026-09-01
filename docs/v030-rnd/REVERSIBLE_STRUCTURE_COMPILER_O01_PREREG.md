# F-01 / O0.1 — General Reversible Structure Compiler composition oracle preregistration

Status: **Foundry O0 Oracle Frontier / research only / no release credit**.

This record is subordinate to `docs/FUNDAMENTAL_RESEARCH_DOCTRINE.md` and `docs/ACTIVE_RESEARCH_THESIS.md`. It freezes the first decisive experiment for F-01 before implementation so the compiler thesis cannot rescue itself after seeing a result by silently changing its grammar, cost boundary, test distribution or success definition.

Canonical CMPCT product/format/release state is unchanged. Existing Forge work on bounded drift, Analytics and other proven/in-flight mechanisms continues independently.

---

## 1. Scientific question

The inherited CMPCT representation tournament is primarily **manually enumerated**. Humans/research campaigns create a new exact transform or relation family and then teach the encoder how to audition it.

O0.1 asks only:

> **Is there material lossless-compression headroom in composing already-trusted exact CMPCT-style representations that the current hand-authored one-stage/tournament policy does not see?**

This is deliberately narrower than “can we build a universal compression language?”

A negative answer at O0.1 is useful. It would show that a seductive universal-compiler direction lacks evidence at its most favorable first boundary and should be retired or reformulated before it consumes major implementation effort.

---

## 2. Prior-art boundary and what O0.1 is not claiming

Programmatic/reversible compression is not an untouched idea.

Relevant prior art includes:

- **Brevis — Lossless Tensor Compression as Program Synthesis (2026):** typed reversible DSL, self-contained bit-exact programs, target-directed bounded A* search and complete serialized-size selection for tensor/checkpoint data.
- **OpenZL (2025–2026):** resolved DAGs of modular reversible codecs with a universal decoder for structured/application-aware compression.
- **Azami & Burtscher, “Identifying Important Data Transformations for Synthesizing Effective Lossless Compressors” (ISPASS 2025):** an LC synthesis framework combining transformation libraries, with evidence that transform importance varies by data/stage and that pruning low-value transformations makes deeper synthesis search more tractable.
- **Verified reversible programming / Flipper (2022):** evidence that reversible compression logic can be represented in a language whose encoder/decoder inverse relationship is structurally/formally constrained.
- grammar/LZ/self-index research: evidence that compact generative descriptions can retain practical random-access/query properties under suitable structures.

CMPCT therefore MUST NOT claim novelty for “compression as program synthesis,” reversible transform graphs, grammar coding, byte transposition, front compression or exact delta programs in isolation.

The CMPCT research question is whether a **general-purpose, content-inferred, archive-aware, eventually cross-object and locality/recovery-aware** reconstruction compiler creates material new leverage beyond those narrower settings and beyond CMPCT's existing hand-authored portfolio.

O0.1 does not attempt to prove that broader claim. It only tests whether compositional headroom exists at all.

---

## 3. Worldview delta under test

### Inherited assumption

A finite manually designed representation tournament is a sufficiently strong way to expose CMPCT's useful reversible structure.

### Candidate worldview

A short composition of simple exact operators can describe useful structure more compactly than any one currently auditioned representation, and recurring winning compositions can serve as an **invention oracle** for future general primitives.

### Capability witness required

A positive O0.1 result must include at least one exact case where:

1. the winning synthesized program uses multiple meaningful operators or a decomposition not equivalent to one existing manual candidate;
2. its **complete charged program representation** is smaller than the best manually nominated control;
3. the same causal motif survives at least one generator-distinct or held-out structural case;
4. the result cannot be explained entirely by a stronger ordinary backend-compressor setting that the baseline omitted.

Without such a witness, O0.1 has not demonstrated a new representational capability.

---

## 4. Oracle Gift Ledger

O0 research may gift **discovery cost**, not representation reality.

Every result MUST state the following gift ledger explicitly.

### Gifted at O0.1

- search/optimization wall time may be arbitrarily larger than production limits, subject only to experiment-level resource bounds;
- the search algorithm may enumerate/combine candidates more broadly than a production encoder could afford;
- candidate-order priors may be used to visit promising programs sooner if they are independent of benchmark identity;
- small bounded inputs may be used to make exhaustive/near-exhaustive search feasible.

### Never gifted

- bytes of the resolved reconstruction program;
- opcode/parameter/length/table bytes;
- literal/residual bytes;
- bytes of required terminal compressed streams;
- bytes of any required source/basis if/when such operators are introduced in later stages;
- exact reconstruction correctness;
- output length and resource-safety semantics of the tested operators;
- benchmark identity prohibition;
- any claimed serialized-size comparator.

### Deferred rather than gifted

The following are **explicit debt**, not silently zero-cost:

- canonical archive framing/recovery duplication;
- complete CMPCT file-tree/index integration;
- native/Android/platform implementation;
- full creation-time product budget;
- whole-archive locality and selective-read interaction;
- complete hostile parser/fuzz surface.

O0.1 claims only a bounded-node/family headroom result. Any later O1/O2 stage must remove these debts one at a time.

---

## 5. Grammar v0 — tiny by construction

The first oracle MUST use a deliberately small grammar. Do not design the final reconstruction IR.

The implementation should wrap already-existing exact mechanisms where practical.

### Required universal terminals

- `DIRECT(payload_codec)` / literal/direct storage;
- exact concatenation of bounded child results;
- explicit output length.

### Initial compositional candidates

Subject to concrete code inventory before implementation, grammar v0 may contain only a small safe subset of:

1. `SPLIT(offsets...)` / `CONCAT(children...)` for bounded subranges;
2. existing fixed-width byte-lane transpose variants already implemented in Geometry/Lattice research;
3. existing flat or hierarchical delimiter/record Geometry transforms where their inverse/resource bounds are already available;
4. existing prefix-plane/front transform where already exact and bounded;
5. existing terminal Zstd/direct codec choices already used by the compared research path.

### Explicitly excluded from O0.1

- cross-object references;
- Mosaic multi-root references;
- bounded-drift EDIT relationships;
- synthetic bases/factors;
- learned transform operators;
- arbitrary user-defined code;
- unbounded recursion;
- general loops;
- arbitrary arithmetic expressions;
- schema names, file extensions, benchmark IDs or format-specific production dispatch;
- large collections of newly invented operators.

The exclusion is causal: O0.1 must determine whether **composition itself** creates headroom before cross-object/relation mechanisms are added.

---

## 6. Program semantics and canonical research charge

The research serialization does not need to be a future canonical archive grammar, but its cost model must be deterministic, conservative and fixed before the first result.

Every program pays for:

- one opcode/tag per node;
- encoded output length where not implied safely;
- transform parameters;
- split/child lengths or a deterministic equivalent;
- transform-specific tables/descriptors;
- terminal compressed-stream bytes;
- literal bytes;
- any padding/alignment introduced by the research grammar.

The result record must separate:

`control_bytes`

`terminal_payload_bytes`

`total_program_bytes`

The oracle must NEVER report only detached transformed-payload size as the synthesized result.

If ambiguity exists between two plausible descriptor encodings, use the more conservative one for O0.1 or report both and make promotion depend on the conservative total.

---

## 7. Search correctness and search intelligence

### Validity is independent of search policy

A candidate program is valid only because executing its inverse/reconstruction semantics returns the exact target bytes within declared bounds.

Search order, heuristics or learned priors may not establish validity.

### Priors may rank, not silently delete

A non-proof prior may reorder candidate expansion. It MUST NOT make a semantically valid region of the bounded grammar unreachable if the experiment is described as exhaustive/optimal.

If search uses pruning that can delete candidates, pruning must be one of:

- an exact lower bound;
- a necessary condition;
- a clearly labeled heuristic experiment that makes no optimality claim.

### Search accounting

Record at minimum:

- programs/states generated;
- programs/states fully costed;
- exact-bound prunes;
- heuristic prunes, if any;
- maximum search depth;
- wall time;
- peak RSS when practical;
- whether optimality is proven for each measured target.

O0.1 may be very slow. It may not be epistemically vague.

---

## 8. Operator-space compression law

The Foundry MUST compress its own search vocabulary.

For each operator or operator family record:

- nomination count;
- participation in winning programs;
- net bytes attributable under ablation where measurable;
- structural families on which it contributes;
- whether its effect is redundant with a simpler composition.

An operator that repeatedly contributes no unique gain is a **search-space liability**, not a prestigious feature.

Before O0.2, remove or demote low-value operators when the evidence supports doing so.

This is informed by prior synthesis work showing that transformation importance is highly uneven and that removing unimportant transforms can make deeper searches more tractable.

A future learned/empirical operator prior may guide expansion order from content-derived features, but exact selection remains based on serialized representation cost.

---

## 9. Discovery, hostile and transfer corpus design

O0.1 MUST NOT be judged only on the current famous v0.30 wins.

The test set has three roles.

### 9.1 Discovery cases

A small bounded set designed to contain structures already known to challenge direct byte order and to verify that the compiler can at least rediscover legitimate transform opportunities.

Potential sources may include bounded public-generator fragments from structured/log/analytics/ML-like data, but the compiler receives only bytes and declared generic resource bounds.

### 9.2 Hostile negatives

Cases that superficially contain attractive syntax/periodicity but should lose once complete control cost is charged, such as:

- random bodies with frequent candidate delimiters;
- irregular/ragged records engineered to make transpose rectangles expensive;
- false repeated prefixes;
- high-entropy lanes;
- tiny structured inputs dominated by program overhead;
- already-compressed/random controls.

Direct fallback MUST win these when the program does not earn itself.

### 9.3 Post-freeze structural transfer

After grammar v0, cost model and search rule are committed, derive additional deterministic challenge seeds from the frozen candidate commit SHA or another post-freeze public value. This prevents hand-tuning the implementation to the exact challenge bytes while preserving reproducibility after the fact.

Transfer cases should vary causal dimensions, not only RNG seeds:

- record widths;
- separator alphabets;
- field counts;
- stride widths;
- prefix similarity;
- raggedness;
- noise density;
- repeated-region placement;
- node sizes;
- combinations of two known structural motifs.

At least one generator-distinct or real public structure should appear before a `CAUSAL_SEED` claim.

---

## 10. Metamorphic structural tests

A real structural mechanism should survive transformations that preserve the underlying opportunity while changing superficial identity.

Where applicable, generate metamorphic pairs such as:

- permuted field/column ordering;
- bijective byte-symbol relabeling where semantics do not require literal values;
- shifted alignment/prefix padding;
- record reordering when field structure remains;
- different separator bytes;
- equivalent structure at multiple node sizes;
- injected irrelevant noisy fields;
- nested composition of two structures.

Do not require identical byte savings under these mutations. Require the causal program family to remain discoverable/profitable when the underlying relation is truly preserved.

This is a stronger anti-overfit test than changing only a benchmark seed.

---

## 11. Exact controls

Each target must report:

1. `DIRECT` / ordinary terminal codec control;
2. best current manually nominated/one-stage Geometry-style candidate available under equivalent node/cost semantics;
3. synthesized grammar-v0 candidate;
4. literal/raw fallback where different from direct terminal coding.

Where a stronger generic compressor is cheap to include for the bounded node, report it as a diagnostic control rather than claiming synthesis headroom that is merely a weak backend setting.

The scientific question is **composition versus current representation vocabulary**, not whether a deliberately weak Zstd level can be beaten.

---

## 12. Foundry explanatory metrics

Final bytes remain decisive, but O0.1 must expose why a program won.

Record where meaningful:

- target logical bytes;
- incumbent bytes;
- synthesized total program bytes;
- absolute/relative saving;
- control/program overhead;
- literal/residual bytes;
- transformed/structured bytes explained by nontrivial operators;
- operator sequence/tree;
- number of children/streams;
- recurrence count of the same normalized program motif across cases;
- search cost;
- exact reconstruction result.

A useful derived diagnostic is:

`explanation_fraction = 1 - (irreducible_literal_or_residual_bytes / logical_bytes)`

This is **not** a promotion metric and must not be used to hide poor final size. It helps determine whether a thesis genuinely explains structure or merely wins through a backend codec accident.

---

## 13. O0.1 success states

O0.1 advances only if the result changes our model of the opportunity.

### `ADVANCE_COMPOSITION`

A multi-operator or nontrivial decomposition beats the best manual control materially on at least two structurally distinct cases, survives hostile fallbacks, and transfers to a post-freeze/generator-distinct case.

Next action: causal ablation, operator-space pruning and O0.2 only if observed residual structure demands a missing operator.

### `DISCOVER_PRIMITIVE`

The synthesizer repeatedly finds one normalized composition motif with material net saving across structurally distinct cases. The most valuable output may be to **distill the motif into one new orthogonal primitive** rather than ship a general compiler.

Next action: create a focused mechanism campaign with the compiler retained as an oracle.

### `MANUAL_FRONTIER_CONFIRMED`

The compiler mostly rediscovers the existing manual winners and creates no material net composition headroom despite broad bounded exact search.

Next action: do not grow the DSL automatically. Either retire F-01 or justify one narrowly targeted O0.2 operator from observed unexplained residual structure.

### `SEARCH_INCONCLUSIVE`

The grammar contains plausible headroom, but the search demonstrably fails to explore/optimize the relevant bounded space.

Next action: improve search/proof organization **without adding operators** and rerun the exact same grammar/corpus contract.

### `RETIRE_F01`

No material composition headroom survives complete program charge and structural transfer, and there is no specific evidence that grammar/search rather than the thesis caused the loss.

Preserve the result. Return Foundry priority to the Assumption Ledger.

---

## 14. Thesis lease / anti-sunk-cost law

F-01 does not receive indefinite continuation merely because it is ambitious.

### Lease 1 — O0.1

The initial tiny grammar gets one complete decisive implementation/evidence pass.

A second pass is allowed only if the first result identifies a **specific causal defect in the instrument**, such as an incomplete search or conservative cost bug, without changing the scientific question.

### Lease 2 — O0.2

At most one or two new generic operator families may be introduced, and only when O0.1 residual/ablation evidence specifically motivates them.

Do not add a sequence of operators because each previous result was “almost interesting.”

### Mandatory thesis challenge

If three substantive Foundry activations advance F-01 implementation but produce no new headroom, falsification, operator retirement or decision-changing causal evidence, the next Foundry activation must be a hostile thesis review rather than more implementation.

If six substantive F-01 Foundry activations produce no state transition or decisive scientific constraint, F-01 must be `REFORMULATE` or `RETIRE` unless an exact external blocker prevented the preregistered experiment from executing. The blocker must be explicit.

This is not a speed quota. A single long-running decisive experiment may span activations. The trigger is **lack of information gain**, not elapsed wall time alone.

---

## 15. Outside-vocabulary challenge

The Foundry can become radical-looking while remaining trapped in familiar coordinate systems.

Before reformulating F-01 after a material negative, generate at least one competing explanation from outside the current transform/compiler vocabulary. Sources may include grammar compression, generalized deduplication/basis+deviation, compressed self-indexes, database factorization, version-control histories, backup locality, error-correcting/recovery organization or another relevant field.

The outside proposal does not automatically receive implementation budget. Its purpose is to test whether the framing itself is stale.

If the best outside-vocabulary hypothesis has clearly greater oracle headroom and an equally cheap falsifier, it may supersede F-01.

---

## 16. Idea-generation diversity after F-01

When the Foundry next needs a primary thesis, do not source every idea from the same mechanism family. Generate candidates through at least three of these lenses before selection:

1. **Assumption inversion:** attack a premise in `ASSUMPTION_LEDGER.md`.
2. **Residual/opportunity decomposition:** inspect what bytes/work remain unexplained after current best mechanisms.
3. **Competitor advantage dissection:** identify a generic causal capability a strong competitor exploits that CMPCT currently loses, then abstract away the workload identity.
4. **Cross-domain import:** translate an idea from another storage/compression/indexing/compilers field and state what must change for arbitrary CMPCT semantics.
5. **Forbidden-vocabulary counterfactual:** temporarily forbid the current dominant primitives and ask how the information could otherwise be described exactly.

This is not a quota on implementation. It is a safeguard against idea monoculture.

---

## 17. O1 handoff if O0.1/O0.2 succeeds

A successful Oracle result does NOT immediately become a canonical DSL.

The O1 Research Frontier must remove gifts/debt in a deliberate order:

1. freeze semantics of the smallest winning operator set;
2. prove structural transfer more broadly;
3. replace expensive exhaustive search with content-agnostic bounded nomination/search while preserving the Oracle winner when required by the experiment;
4. use exact lower bounds/proof-directed pruning wherever possible;
5. measure real creation time/RSS;
6. measure program parsing/inverse runtime and resource bounds;
7. integrate node-level complete archive framing and strong verification;
8. measure locality/read amplification and decode units;
9. only then consider a candidate reconstruction IR/canonical representation.

Maintain a **debt vector** for every O1 mechanism:

`discovery_time | encode_time | memory | control_bytes | decoder_ops | locality | recovery | integrity | native/platform | selector/generality`

Do not allow improvement in one debt axis to silently relocate cost to another.

---

## 18. O1 Pareto-compiler principle

O0.1 primarily measures byte headroom. O1 should not collapse the representation decision into one scalar weighted score.

Where multiple programs are meaningfully different, retain a bounded nondominated candidate set over relevant dimensions such as:

- stored bytes;
- encode work after discovery;
- decode work;
- selective-read/materialized bytes;
- decoder memory;
- dependency/failure-domain cost.

The final CMPCT product policy may choose a profile/point according to existing format policy, but the research system should preserve the real Pareto frontier rather than hide one metric inside an arbitrary weight.

---

## 19. Reconstruction IR direction if repeated compositions survive

Do not prematurely design a VM. If repeated compositions survive transfer, the candidate architecture should be evaluated against an immutable/dataflow-style reconstruction IR rather than assuming a stack bytecode.

A promising eventual shape is a typed acyclic dataflow graph / SSA-like model in which:

- values are immutable bounded byte/bit/sequence/table streams;
- operators declare exact input/output size/resource contracts;
- common subexpressions/factors may be physically shared;
- roots identify logical outputs;
- dependency/fanout/locality can be analyzed statically;
- the decoder executes a resolved DAG without search;
- recovery boundaries can align with authenticated subgraphs.

This is a hypothesis, not an O0.1 requirement. Its purpose is to avoid designing a universal reconstruction language whose operational semantics make sharing, resource analysis and recovery harder than necessary.

---

## 20. Decision record required from the first implementation

The durable evidence record must end with:

```text
thesis: F-01 General Reversible Structure Compiler
oracle: O0.1 composition-only
frozen_grammar: <fingerprint/version>
corpus_fingerprint: <discovery + hostile>
postfreeze_transfer_seed: <value derived after freeze>
search_optimality: <proven|bounded-not-proven>
search_states: <generated/costed/pruned>
incumbent_bytes: <aggregate + per case>
synthesized_bytes: <aggregate + per case>
control_bytes: <aggregate + per case>
material_composed_wins: <count>
hostile_false_wins: <count>
transfer_wins: <count>
recurring_program_motifs: <summary>
explanation_fraction: <diagnostic only>
search_time_rss: <explicit O0 debt>
strongest_simpler_explanation: <one sentence>
strongest_surviving_objection: <one sentence>
decision: <ADVANCE_COMPOSITION|DISCOVER_PRIMITIVE|MANUAL_FRONTIER_CONFIRMED|SEARCH_INCONCLUSIVE|RETIRE_F01>
next_decisive_test: <one sentence>
```

Anything less is an implementation result, not a completed Foundry oracle.
