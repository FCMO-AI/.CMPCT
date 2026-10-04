# CMPCT Assumption & Opportunity Ledger

Status: **living Foundry input; not a release checklist**.

Read with `docs/FUNDAMENTAL_RESEARCH_DOCTRINE.md`, `docs/RESEARCH_LOG.md`, `docs/RND_DOMINATION_RUBRIC.md` and current campaign evidence.

Purpose: preserve the assumptions that current CMPCT architecture makes so future research can attack them deliberately. Benchmarks expose failures; this ledger exposes **possible missing models of information**.

An assumption is not an error merely because it appears here. Most exist for good historical reasons. The Foundry asks whether the reason remains strong enough to justify the representational limitation.

Each inversion should first receive a cheap/generous oracle. Do not convert this file into twenty simultaneous implementation projects.

---

## Priority legend

- **P0** — unusually high conceptual leverage + cheap decisive oracle; strong Foundry candidate now.
- **P1** — high-upside question worth maintaining in the secondary portfolio.
- **P2** — interesting but prerequisites/headroom are unclear.
- **CLOSED/SATURATED** — current evidence constrains the family strongly; reopen only with new causal evidence.

---

# A01 — Useful bases correspond to real source objects

**Priority:** P0

### Inherited assumption

Graph/delta/resemblance mechanisms generally choose existing logical/physical objects as bases or roots.

### Why it exists

Real objects are free to identify, exact, independently reconstructible and naturally compatible with depth/locality/recovery accounting.

### Tension

A family of related objects may have no single member that is the best explanation of the family. Historical accidents determine which versions/files exist; the minimum-description basis need not be one of them.

### Inversion question

> Can CMPCT synthesize a **latent physical basis** that never existed as a user file, then reconstruct each real member as a bounded exact residual from that basis?

### Cheapest oracle

On small deterministic families, optimize or approximate a synthetic byte/record basis offline with discovery cost gifted. Charge:

`stored synthetic basis + every residual + descriptors + integrity`

Compare against:

- best real single base;
- bounded-drift base+edit programs;
- Mosaic/multi-root where applicable;
- direct/solid compression.

### Win condition

Material family-level complete payload headroom, not merely one target; residual/dependency locality remains plausibly bounded.

### Failure interpretation

If an oracle-quality synthetic basis does not beat best-real/multi-root representations after basis charge, do not build production discovery.

### Related territories

Synthetic Basis, FactorGraph, generalized deduplication, grammar induction, consensus/ancestral reconstruction.

---

# A02 — A target should be explained directly by objects, not by latent factors

**Priority:** P1

### Inherited assumption

Relationships are typically target-to-base or target-to-several-roots.

### Tension

Several objects can share orthogonal factors: common skeleton, field plane, header vocabulary, edit motif, numeric lane, container recipe, etc. Direct object references may duplicate the same explanatory information across several edges.

### Inversion question

> Can related objects be decomposed into reusable **factors** plus small object-specific composition programs?

### Cheapest oracle

Take a bounded family and allow a small number of charged shared factors discovered offline. Measure minimum complete description versus direct bases/Mosaic and versus one solid stream.

### Strongest danger

This can degenerate into expensive dictionary learning with huge metadata and poor selective access. Require explicit factor charge and member-level materialization accounting.

---

# A03 — Residuals are terminal payloads

**Priority:** P0/P1

### Inherited assumption

After `target = base + residual/edit program`, the residual is compressed and stored largely independently.

### Tension

Residuals across a family may themselves share:

- repeated positions;
- common edit operations;
- similar literal streams;
- correlated masks;
- numeric/bit-plane geometry;
- recurring reconstruction motifs.

### Inversion question

> Is there a second layer of redundancy in the **space of differences**, and can CMPCT factor it without deep dependency chains?

### Cheapest oracle

Extract exact residual/edit streams from existing version-family mechanisms and compress/factor the residual corpus collectively while charging a direct member-access plan. Compare with independently compressed residuals.

### Product warning

Do not permit recursive arbitrary-depth deltas. Prefer shared residual roots/grammar/factors with bounded depth.

---

# A04 — Logical byte order is the primary geometry

**Priority:** P0, active through Geometry

### Inherited assumption

Most codecs see the object's serialized byte order, optionally with a small set of known transforms.

### Historical evidence against it

Geometry/Lattice experiments show large gains when lanes, records, fields and prefixes are rearranged reversibly before entropy coding.

### Inversion question

> Can CMPCT infer a **better exact information geometry** for arbitrary bytes rather than treating each new layout as a handwritten transform?

### Cheapest oracle

Bounded reversible-program search on <=512 KiB nodes over a small typed transform grammar, exact serialized-cost objective, with direct literal fallback.

### Foundry escalation

Do not automatically implement G5/G6/G7 as manual ladder extensions. Test whether a compiler can discover compositions and whether recurring winning programs imply a smaller general primitive set.

---

# A05 — Transform vocabulary should be handcrafted

**Priority:** P0

### Inherited assumption

Humans add new exact transforms/mechanisms, and encoder policy auditions a finite manually designed set.

### Tension

The number of plausible exact decompositions grows rapidly, and the best composition may be non-obvious. Handcrafted ladders risk becoming another local optimum.

### Inversion question

> Can compression be formulated as bounded **program synthesis / superoptimization** over reversible operators, with exact serialized size as the objective?

### External evidence

Brevis (2026) demonstrates typed bit-exact tensor compression through self-contained synthesized programs and bounded target-directed search. OpenZL demonstrates graph-composed reversible codecs with a universal decoder. CMPCT's question is broader: arbitrary-data, cross-object, archive-aware and content-inferred synthesis.

### Cheapest oracle

Build a research-only DSL using existing CMPCT primitives first. Search exhaustively/A* on small nodes. Determine whether the synthesizer discovers smaller representations than the current hand-authored tournament and whether those programs transfer.

### Failure modes

- DSL overhead dominates;
- search rediscovers only existing obvious transforms;
- operator interactions explode;
- generality depends on benchmark-specific priors;
- decoder surface becomes too large.

### Success interpretation

Even if the production encoder never performs full synthesis, recurring oracle programs can reveal new primitive families that are later distilled into cheap exact admission.

---

# A06 — Object boundaries supplied by the filesystem are the right reuse boundaries

**Priority:** P1

### Inherited assumption

Files/nodes/chunks define most candidate ownership boundaries.

### Tension

Repeated information can cross file boundaries, align poorly with chunks, or exist as record/field structures that cut across logical object boundaries.

### Inversion question

> Can CMPCT discover **cross-object regions/factors** whose ownership is independent of file/chunk boundaries while preserving exact member access and bounded failure domains?

### Cheapest oracle

On bounded multi-file families, permit a common pool of exact regions/factors independent of original boundaries; price descriptors and read amplification exactly.

### Historical caution

Earlier global/CDC/shared-store experiments can fail badly when their ownership unit is the wrong coordinate system. New work must explain why its unit escapes preserved negative evidence.

---

# A07 — Compression and indexing should be separate structures

**Priority:** P1

### Inherited assumption

Physical compressed data is accompanied by explicit indexes/maps for paths, offsets, chunks, objects and relationships.

### Tension

Grammar/self-index research shows that some compressed representations can support locate/random-access operations directly over the compressed structure.

### Inversion question

> Can a CMPCT representation be both the compressed information and part of its own useful access index, eliminating duplicated navigation/control state?

### Cheapest oracle

Select a highly repetitive bounded family and compare:

`compressed payload + current index`

against a grammar/block-tree/attractor-like representation augmented only with the metadata necessary for CMPCT member/range access.

### Product warning

Text self-index theory does not automatically transfer to arbitrary archive data. This is an abstraction source, not a prescribed algorithm.

---

# A08 — Update history is operational metadata, not a compression dimension

**Priority:** P1

### Inherited assumption

Transactional generations/journals preserve updates, but primary compression usually targets the current logical state and local version relationships.

### Tension

Long-lived archives may contain sequences of states where stable information and mutation patterns dominate total information.

### Inversion question

> Can time/generation lineage become a first-class **Temporal EntropyGraph** in which stable state, mutations and reconstruction checkpoints are optimized together?

### Cheapest oracle

Use deterministic update histories with equivalent final/current-state semantics. Compare full retained-history storage and selective generation recovery against independent snapshots, journal+checkpoint baseline, and version-family graph representations.

### Product warning

Current-state-only archives must not pay temporal machinery they do not need.

---

# A09 — Recovery and locality are taxes applied after compression

**Priority:** P1

### Inherited assumption

Compression candidate is found, then constrained/repaired to satisfy <=8x locality, decode-unit, recovery and corruption requirements.

### Tension

The optimal information organization for compression may be co-designed so that failure domains and access units naturally align with reconstruction factors.

### Inversion question

> Can we choose representation units whose **compression relationships are also the recovery/locality structure**, so resilience/access becomes cheaper by construction?

### Cheapest oracle

For a graph/factor family, optimize a joint objective including stored bytes and exact per-member materialization/failure-domain charge rather than producing a ratio winner and rehabilitating locality afterward.

### External adjacent evidence

Backup delta systems repeatedly show that reference placement/locality can dominate restore economics; locality-aware base selection and inverse delta schemes suggest relationship direction itself can be a systems design variable.

---

# A10 — Candidate construction is necessary to know a candidate loses

**Priority:** P0 in search-heavy lanes

### Inherited assumption

Many representation tournaments construct/compress candidates, then compare final cost.

### Known tension

Analytics/PrefixGraph and other high-effort paths can spend material creation time on ultimately rejected candidates. Unsafe heuristic early terminals have counterexamples.

### Inversion question

> Can exact necessary conditions, optimistic lower bounds and branch-and-bound proofs eliminate losing representation subtrees **before construction**?

### Cheapest oracle

Instrument candidate families with exact lower bounds on unavoidable literals/control/base charge. Measure the fraction of current losing work that becomes provably futile without changing the selected archive.

### Classification

Usually R3 rather than R5, but extremely high leverage because it may make richer Foundry representation search affordable.

---

# A11 — The compressed representation should end in one conventional entropy-coding stage

**Priority:** P2

### Inherited assumption

After structural transformation, streams generally feed conventional general/field compressors.

### Tension

Different residual streams have different statistics. Structure and entropy model may be better co-designed, while a single backend can obscure low-entropy subfields.

### Inversion question

> Should the reversible representation compiler produce several typed residual streams with **locally appropriate bounded entropy models**, rather than one generic terminal stream?

### Caution

Do not turn CMPCT into a zoo of codecs. The gain must survive complete code/metadata/decoder complexity and portability cost.

---

# A12 — Existing exact encodings are separate byte identities even when they expose the same underlying information

**Priority:** P1

### Inherited assumption

Exact Deflate streams, nested containers, plaintext, transformed layouts and other encodings often compete as alternative representations.

### Historical counterexamples

Nested ZIP virtualization, raw-Deflate reuse and reversible precompression demonstrate that multiple exact views can sometimes share one underlying information root.

### Inversion question

> Can CMPCT define a bounded **Exact View Algebra** where authenticated reversible programs connect multiple byte encodings to shared physical information?

### Cheapest oracle

Identify families where the same logical content exists under several deterministic encodings. Measure:

`shared canonical root + exact view programs`

versus preserving each encoding independently and versus existing virtualization/precompression.

### Danger

View composition can create dependency depth and massive implementation surface. Require simple, typed, versioned primitives and shallow composition.

---

# A13 — Similarity/resemblance is primarily a pairwise relation

**Priority:** P1

### Inherited assumption

Candidate discovery often asks whether target A resembles base B, then builds an edge/program.

### Tension

Families may exhibit higher-order structure that no pair captures: common regions split across several members, clusters around no observed medoid, or latent grammar shared across many targets.

### Inversion question

> What information becomes visible only when a **set/family** is modeled jointly rather than as independent pairwise comparisons?

### Related territories

Mosaic already breaks the one-parent assumption for one target. Synthetic bases/factors and residual grammars generalize the question across entire families.

---

# A14 — Format semantics must be known explicitly to exploit structure

**Priority:** P0/P1

### Inherited assumption

Specialized compressors often receive schemas/types; CMPCT intentionally avoids extension/workload identity and uses content-driven mechanisms.

### Tension

OpenZL and domain-specific compressors demonstrate how much ratio/speed is available when structure is known. CMPCT's universal ambition requires discovering enough of that structure from bytes without embedding schema-specific product policy.

### Inversion question

> How much **schema-like structure can be inferred and serialized generically** from arbitrary data, so the decoder receives an exact resolved program rather than requiring prior format knowledge?

### Cheapest oracle

Use content-only structure synthesis on held-out structured byte streams; compare with a schema-informed oracle to quantify the headroom lost by generic discovery.

### Success criterion

The mechanism must transfer across semantically unrelated formats sharing structural properties.

---

# A15 — Reader-visible primitive count may grow with every successful research family

**Priority:** P0 meta-architecture

### Inherited assumption

A sufficiently important representation can earn canonical reader semantics.

### Tension

If every breakthrough becomes a bespoke primitive, the reader eventually becomes the archive equivalent of a compiler backend zoo.

### Inversion question

> Can multiple breakthrough mechanisms compile into a **smaller universal reconstruction IR**, allowing encoder innovation without proportional reader complexity?

### Cheapest oracle

Map current research representations (Geometry, bounded drift, Mosaic-style references, exact views) onto a minimal typed reconstruction instruction set. Measure descriptor inflation and decoder complexity versus bespoke grammars.

### Relationship to A05

A05 asks whether the encoder can synthesize programs. A15 asks whether one compact execution IR can absorb future invention safely.

---

# A16 — Benchmark reds are the natural source of research questions

**Priority:** CLOSED AS PRIMARY POLICY / process assumption explicitly rejected

### Inherited tendency

Autonomous development naturally prioritizes the visible red matrix because it offers precise gaps and immediate reward.

### Why it is dangerous

It converts workloads into customers and makes invention reactive. Historical fundamental advances began from missing information relationships, not merely cell closure.

### Replacement

The strict matrix remains product truth under `RND_DOMINATION_RUBRIC.md`. Fundamental question generation starts from this ledger, active thesis state, unexplained information opportunity and outside-vocabulary research.

A red may trigger a thesis, but it is not required for a thesis to exist.

---

# A17 — More hourly commits imply more useful research progress

**Priority:** CLOSED AS POLICY

### Replacement

Hourly scheduling is a continuity mechanism. The active thesis persists across activations. A decisive oracle, impossibility proof or structural transfer result outranks several unrelated implementation commits.

Do not optimize Foundry work for patch count.

---

# A18 — The best next representation is likely a descendant of the current one

**Priority:** P0 meta-question

### Inherited tendency

Research branches naturally mutate the mechanism already open in the editor.

### Tension

The largest historical jumps often came from changing the coordinate system: TAR -> native objects, bytes -> content roots, equality -> resemblance, one base -> many roots, byte order -> geometry.

### Inversion question

> If all current representation vocabulary were forbidden, how else could the same information be described exactly?

### Foundry use

At thesis saturation, require at least one outside-vocabulary proposal drawn from another field before another descendant tuning pass.

---

# A19 — Stored data and executable description are fundamentally different things

**Priority:** P0/P1

### Inherited assumption

Archive metadata describes where stored payloads are; reconstruction programs are special cases.

### Tension

EntropyGraph edges, container recipes, Geometry transforms and bounded-drift edit programs already blur this boundary. Program-synthesis compression makes the description itself the compressed representation.

### Inversion question

> Should CMPCT increasingly store **small exact programs + irreducible literals** rather than choosing between fixed payload encodings?

### Oracle

Same as A05, but measure program-vs-payload decomposition and identify which data classes benefit from description-centric storage.

---

# A20 — A representation win should be evaluated mainly by bytes and runtime after it is built

**Priority:** P1 meta-research

### Inherited assumption

Final artifact and runtime measurements dominate decisions.

### Tension

For fundamental research, the more important early question can be **how much information the new model explains** and whether the remaining residual becomes qualitatively simpler.

### Inversion question

> Can we track mechanism attribution/headroom—copied/explained bytes, factor coverage, residual entropy/structure, program reuse—in addition to final size so we know whether a thesis is opening a real frontier before its implementation is optimized?

### Rule

These metrics never replace final byte/runtime truth. They are causal instruments for the Foundry.

---

# Current primary Foundry recommendation

## Thesis F-01 — General Reversible Structure Compiler

### Inherited assumption

CMPCT's transform/representation vocabulary is designed manually and auditioned as a fixed ladder/portfolio.

### Proposed model

A bounded typed reconstruction language can express reusable exact structures, and an expensive research compiler can synthesize or compose programs whose complete serialized cost beats the best manually nominated representation. Production can later distill recurrent winners into cheap nomination/admission.

### Why now

- Geometry already demonstrates large gains from reversible layout compilation.
- Bounded-drift demonstrates another exact program-like representation.
- EntropyGraph/Mosaic already provide graph/reconstruction semantics.
- External Brevis evidence shows target-directed exact program-synthesis compression can be practical in a specialized tensor domain.
- OpenZL demonstrates the operational value of universal decode for resolved transform graphs.

### First oracle

Research-only, bounded nodes/families. Start with a **small grammar composed of primitives CMPCT already trusts**, not a giant speculative DSL. Compare:

1. incumbent/direct representation;
2. best manually nominated existing transform;
3. synthesized composition;
4. literal fallback.

Exact serialized bytes decide. Search cost is reported separately as O0 debt.

### Minimum useful outcome

One of:

- new composed program materially beats the hand-authored tournament on held-out structural cases;
- synthesis repeatedly discovers a small recurring operator/motif not currently represented, justifying a new focused primitive;
- strong negative evidence shows current manually designed primitives already span the useful bounded program space, allowing the Foundry to redirect confidently.

### Forbidden shortcut

Do not seed the search with workload identity or file extension. If priors are later used, they may depend only on observable content/structural features and must not alter exact validity.

---

# Secondary Foundry questions

## F-02 — Synthetic Basis / FactorGraph

Test whether a charged latent basis beats every real-base/Mosaic alternative on families with distributed common structure.

## F-03 — Residual Graph

Test whether edit/delta residual collections have enough shared structure to justify a second factoring layer while keeping reconstruction depth bounded.

## F-04 — Self-indexed reconstruction structures

Test whether grammar/block-style structures can remove part of the separate index/control tax while preserving CMPCT-style random member/range access.

---

# Ledger maintenance law

Update this file when evidence changes an assumption, not every time code changes.

For a material Foundry result:

- mark the tested assumption;
- preserve the exact evidence path;
- record whether the inversion gained support, lost support or split into narrower conditions;
- add the strongest new constraint learned;
- update the cheapest next oracle.

Do not delete falsified assumptions/history. A closed direction is part of CMPCT's accumulated scientific memory.