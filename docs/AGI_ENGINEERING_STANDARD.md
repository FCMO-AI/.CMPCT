# CMPCT AGI-grade engineering standard

## Purpose

This document defines the minimum quality bar for substantive CMPCT engineering.

“AGI-grade” is a repository shorthand for an **engineering standard**, not a claim that any contributor,
model or tool is AGI. In this project it means work that combines unusually strong systems reasoning,
scientific discipline, adversarial skepticism, broad technical synthesis and reproducible evidence.

The objective is not to make work sound brilliant. The objective is to make the repository accumulate
results that remain impressive after hostile review, independent reproduction and comparison with mature
alternatives.

A clever patch without evidence is not AGI-grade. A benchmark win bought with weaker semantics is not
AGI-grade. A large diff is not AGI-grade. A small change can be AGI-grade when it identifies the real
constraint, proves the mechanism and removes a meaningful bottleneck without moving risk elsewhere.

## The quality ratchet

Every material milestone MUST leave CMPCT at least as strong as the verified state it inherited.

A change must therefore do one or more of the following while preserving established strengths:

- improve compression ratio on fair workloads;
- improve creation, extraction, list, read or selective-read latency;
- reduce CPU, peak memory, I/O amplification or decode work;
- improve integrity, recovery, crash safety or hostile-input behavior;
- increase filesystem fidelity or deterministic behavior;
- increase portability, interoperability or ordinary-user usability;
- simplify the reader/ABI while retaining capability;
- strengthen conformance, independent evidence or measurement quality;
- remove a known architectural limitation;
- discover and document a reproducible negative result that prevents future wasted effort.

“No regression” is the floor, not the aspiration. When a task is nominally maintenance-only, the agent
should still look for a safe, evidence-backed way to improve the surrounding invariant, test surface,
measurement quality or architecture.

Do not manufacture novelty. If the best engineering result is a narrow surgical fix, make it an
exceptionally well-proven surgical fix.

## Prime directive: solve the real problem

Before editing code, reduce the task to a falsifiable systems problem.

Record or establish:

1. **Observed failure or opportunity.** What is actually wrong, slow, large, fragile, confusing or
   missing? Separate observation from interpretation.
2. **Baseline.** What does current `main` do on the relevant dimensions?
3. **Invariant.** What must remain true after the change?
4. **Constraint map.** Which limits come from format semantics, algorithms, dependencies, operating
   systems, hardware, compatibility, security or measurement?
5. **Hypothesis.** What mechanism is expected to improve the target and why?
6. **Disproof test.** What result would show the hypothesis is wrong?
7. **Acceptance evidence.** What measurements, vectors, adversarial cases or platform tests are needed
   before merge?

Do not begin with “what code can I add?” Begin with “what fact about the system would have to change for
this problem to disappear?”

## Evidence hierarchy

Prefer stronger evidence over more prose. From strongest to weakest for project claims:

1. independent fixed vectors / independent implementation agreement;
2. deterministic controlled experiments with exact provenance;
3. direct base-vs-candidate tests on identical inputs and semantics;
4. repeated measurements with raw observations retained;
5. targeted property/adversarial tests;
6. code inspection and derivation;
7. plausible architectural reasoning;
8. intuition.

Lower levels may generate hypotheses. They do not substitute for higher levels when higher levels are
practical.

When evidence disagrees with intuition, investigate the evidence quality first, then update the model of
the system. Never change a benchmark or test merely because the result is inconvenient.

## The invention protocol

For non-trivial performance, architecture or reliability work, do not stop at the first conventional
solution. Run an explicit invention pass.

### 1. Model the cost

Write down the dominant cost in the correct units: bytes, entropy, syscalls, allocations, copied bytes,
decoded bytes, dependency depth, random seeks, startup time, branch work, metadata, recovery work, or
human friction.

If the cost cannot be named, the optimization target is probably not understood.

### 2. Identify avoidable work

Ask, in order:

- Can the bytes/work be eliminated entirely?
- Can an already-required representation be reused instead of recreated?
- Can the logical object be represented as an exact inverse/view of another object?
- Can global knowledge remove local duplication?
- Can the operation touch less data?
- Can the expensive path be moved to creation time while keeping the reader simple?
- Can a proof, index or recipe replace repeated computation?
- Can the hot path be split from a cold path without lying about semantics?
- Can the representation be made adaptive rather than globally fixed?
- Can the problem be transformed into a graph/selection/packing problem with measurable costs?

### 3. Generate competing hypotheses

For a meaningful problem, consider at least three distinct classes of solution unless the defect has an
obvious unique correction. Examples: algorithmic, representation-level, layout-level, systems/I/O,
cache/locality, native acceleration, metadata reduction, concurrency or user-workflow solutions.

Do not implement all of them. Use cheap experiments to kill weak ideas early.

### 4. Search outside the local design vocabulary

When the problem is not already well understood, actively inspect relevant primary literature,
standards, mature implementations and adjacent fields. Compression work may borrow from databases,
compilers, deduplication, information retrieval, content-addressed storage, filesystems, networking,
error-correcting codes or program synthesis.

The goal is not to decorate a PR with citations. The goal is to discover mechanisms, lower bounds,
failure modes and experimental methods that change the engineering decision.

### 5. Prefer mechanism-level wins

A threshold tweak that wins one corpus is weak evidence. A representation or algorithm that explains
*why* multiple workloads improve is stronger.

Whenever possible, promote the mechanism into an explicit reusable primitive, invariant or solver input
rather than leaving it as one special-case branch.

## Benchmark ethics and scientific method

CMPCT treats benchmark integrity as part of product integrity.

Every performance claim MUST state the relevant semantics and preserve competitors' legitimate
advantages. In particular:

- identical-input comparisons use the same corpus bytes and filesystem metadata;
- richer CMPCT semantics may not be compared to weaker competitor semantics without qualification;
- library and fresh-process CLI layers remain separate;
- creation time is not hidden inside extraction or vice versa;
- selective access is not credited to a solid stream that must traverse unrelated data;
- archive size includes required metadata;
- integrity/recovery work included on one side must be included or disclosed on the other;
- raw measurements and losing workloads are retained;
- stochastic data generation is seeded or otherwise made reproducible;
- timing conclusions are not drawn from one noisy observation;
- a failed gate is investigated, not negotiated away.

When a mature competitor wins, treat the result as useful information. Determine whether the cause is a
fundamental tradeoff, implementation weakness, benchmark asymmetry or missing representation. If it is
an engineering weakness, turn it into a prioritized defect.

## Adversarial self-review

Before declaring a material task complete, perform a hostile review as if trying to reject the work.

Ask at least:

- What assumption is most likely false?
- What input distribution makes this look bad?
- What happens on incompressible, tiny-file, huge-file, sparse, nested, duplicated and metadata-heavy
  cases?
- Can malformed input trigger excessive allocation, CPU, I/O, recursion or disk materialization?
- Does a partial read accidentally require a full decode?
- Does a failure path return unauthenticated or partially trusted bytes?
- Can recovery select uncommitted state?
- Can path/link behavior escape the destination root?
- Does an optional dependency become mandatory by accident?
- Does the optimization encode a Python/native/platform-specific assumption into the format?
- Can a future reader reconstruct the result without replaying old encoder heuristics?
- Did any comment, test, fallback, note or historical context disappear during refactoring?
- Is the benchmark easier than the real workload?
- Would the result still be persuasive if the losing rows were shown first?

Then add the strongest cheap test that attacks the most dangerous surviving assumption.

## Independent-oracle rule

A builder and reader agreeing with each other proves less than it appears: they can share the same bug.

For format and reconstruction semantics, prefer builder-independent golden vectors, hand/independently
constructed byte oracles, a second implementation, standard-library/mature-tool agreement, or algebraic
properties that do not depend on the implementation under test.

Any new on-disk representation should have an independent oracle before it is considered mature.

## Performance and complexity accounting

Do not optimize one scalar while exporting hidden cost elsewhere.

For substantial representation changes, reason about at least:

- archive bytes;
- creation CPU/time and peak memory;
- extraction CPU/time and peak memory;
- list/open/startup cost;
- selective-read bytes touched and bytes decoded;
- dependency depth / reconstruction fan-out;
- integrity work;
- recovery work;
- temporary disk/materialization requirements;
- implementation complexity in the shared reader;
- portability burden.

A representation that saves 1% size by making a 4 KiB read inflate 2 GiB has not achieved an
unqualified win.

## The engineering-miracle test

The phrase “engineering miracle” has one acceptable meaning in this repository: a result that looked
hard or mutually constrained, but became possible because the contributor found a better model of the
problem.

A miracle-grade result typically has several of these traits:

- removes work instead of merely accelerating it;
- reuses information already present in the system;
- converts a global tradeoff into an adaptive local choice;
- achieves a Pareto improvement across previously conflicting metrics;
- turns an implicit heuristic into an explicit cost model;
- finds a representation that makes a difficult operation trivial for the reader;
- replaces duplicated physical data with an authenticated exact view/reconstruction edge;
- improves both performance and correctness because the new abstraction is cleaner;
- proves a widely assumed limitation was an artifact of the previous design;
- remains understandable, testable and portable after the cleverness is removed from the explanation.

Do not chase spectacle. The highest form of cleverness is a design that looks obvious after it is
explained and remains robust under hostile evidence.

## Quality dimensions that must not be traded silently

Every material change must explicitly consider the dimensions it touches:

- correctness and byte-exact losslessness;
- compression ratio;
- create/extract/read/list latency;
- peak and steady-state memory;
- random-access locality;
- integrity and authentication;
- recovery and crash consistency;
- hostile-input resource bounds;
- filesystem semantics;
- deterministic/reproducible behavior;
- backward/forward compatibility;
- portability and ABI simplicity;
- fallback behavior;
- debuggability and observability;
- public reproducibility;
- end-user friction.

If a dimension is intentionally worsened, the tradeoff must be explicit, measured and justified. An
unacknowledged tradeoff is a defect.

## Code standard

Code should be the smallest clear implementation of the proven design, not a transcript of the
exploration that found it.

Mandatory rules:

- preserve existing design comments, footnotes and invariants unless they are demonstrably obsolete;
- when removing a note, preserve the still-valid rationale elsewhere in the same change;
- add concise nearby “why” comments for non-obvious invariants, safety boundaries and benchmark
  semantics;
- avoid copy-pasted parsers, codec logic and policy forks across platforms;
- prefer typed errors and explicit bounds over implicit assumptions;
- make optional accelerators optional;
- keep the reader simpler and more stable than the encoder;
- fail closed on malformed or unauthenticated data;
- add tests for the bug mechanism, not merely the reported example;
- do not leave TODOs as substitutes for required correctness.

## Research-to-production promotion

Research code is allowed to be aggressive. Canonical format code is not allowed to be vague.

Promote a research mechanism only when it has:

1. a precise byte/semantic contract;
2. measurable benefit on non-private reproducible workloads;
3. known losing cases;
4. independent conformance evidence;
5. explicit integrity semantics;
6. bounded create/read/recovery resource accounting;
7. hostile malformed-input tests;
8. recovery/crash behavior where applicable;
9. native/shared-reader support or a deliberate staged compatibility plan;
10. portability and export implications documented.

A promising prototype is not a format revision.

## Completion dossier for every material PR

A material PR should make the following easy to answer from repository/PR evidence:

### Problem
- What exact problem/opportunity was addressed?
- What was the baseline?

### Insight
- What mechanism or invariant made the solution possible?
- What alternatives were rejected and why?

### Evidence
- Which tests/benchmarks/oracles demonstrate correctness and improvement?
- What are the raw or durable result locations?
- What lost, remained unchanged or stayed ambiguous?

### Safety and compatibility
- What hostile/resource/path/recovery cases were considered?
- What reader/format/ABI/platform compatibility changed?

### Performance
- What happened to archive size, create/extract latency, selective access and memory where relevant?
- Did the direct-base release gate pass without weakening its contract?

### Future leverage
- What new capability, abstraction or research direction does this unlock?
- What is the highest-value unresolved defect exposed by this work?

A PR that cannot answer these questions is not ready simply because tests are green.

## Stop conditions

Do not merge when any of the following is true:

- a claimed win is not reproducible;
- the comparison is semantically unfair;
- a deterministic size regression is unexplained;
- a confirmed performance regression exceeds the release contract;
- a parser/resource boundary is knowingly unbounded;
- the change weakens integrity or recovery without explicit redesign approval;
- canonical bytes changed without a format-revision/conformance update;
- a platform integration forks archive semantics;
- private provenance leaked into the public tree;
- required comments/notes/tests were accidentally deleted;
- the work is material but unversioned or lacks a durable benchmark record;
- a major assumption remains untested when a practical disproof test exists.

## Agent behavior under uncertainty

Do not bluff certainty. Label measured fact, source-backed fact, inference, hypothesis and proposal.

If a task exposes a deeper architectural issue, solve the highest-leverage root cause that can be safely
validated in the current milestone rather than polishing symptoms. If the deeper change is too risky for
one milestone, leave a precise executable next mission, not a vague recommendation.

If conventional approaches fail, change the model of the problem before changing the standard of proof.

## Final self-check

Before calling a material task complete, ask:

> If a skeptical expert received only this repository state, the benchmark artifacts and the tests,
> would they independently conclude that CMPCT became better for the claimed reason?

If the answer is not clearly yes, the work is not finished.
