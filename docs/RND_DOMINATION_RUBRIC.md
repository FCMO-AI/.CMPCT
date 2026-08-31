# CMPCT R&D Domination Rubric

Status: **normative for material CMPCT R&D, performance-frontier selection, and autonomous v0.30 work while the strict external contract is incomplete**.

This document governs **what research to do next and how radical that research must be**. It complements, but never weakens, `docs/AGI_ENGINEERING_STANDARD.md`, `docs/HOURLY_RUN_DURATION_CONTRACT.md`, `docs/PERFORMANCE_RELEASE_GATE.md`, release authority, hostile-input safety, portability, recovery, locality, and the zero-byte no-regression law.

The objective is deliberately stronger than “make CMPCT better on average”:

> **True domination means every frozen workload is strictly smaller AND strictly faster to create than both ordinary ZIP/Deflate and solid Zstd-19, while preserving the accepted v0.29 product floor and every required CMPCT semantic/safety/platform invariant. Ties fail. Aggregate wins never erase a losing row.**

The rubric exists because the route from a partially winning frontier to a true 15/15 frontier is not expected to be uniform. Some rows are boundary problems that deserve careful optimization. Others are architectural or representational dead ends where another local optimization is wasted motion. Future work MUST distinguish those cases explicitly.

---

## 1. Release truth and research truth are separate

This rubric selects and evaluates research. It **does not grant release credit**.

A mechanism may score highly, produce a dramatic experiment, or become the top research priority and still remain research-only until it survives the applicable chain:

`generic mechanism -> canonical semantics -> reader/verification -> recovery/locality -> native -> Android/platform -> selector/product -> exact common-fingerprint external authority -> strict release authority`

Conversely, a low-novelty productization task can outrank new research when a candidate has already demonstrated the required strict win and the remaining blocker is honest integration/evidence debt.

**Research boldness and promotion conservatism are intentionally different control loops.**

---

## 2. Diagnose the red before choosing the solution

Every strict-red workload or release-critical performance red MUST be assigned the strongest currently supported root-cause class before material work begins.

### D0 — Evidence / harness red
The product may already be correct/fast enough, but exact-head custody, benchmark identity, workflow admission, artifact provenance, runner setup, or measurement is broken or missing.

**Default response:** repair evidence. Do not invent a codec to fix CI.

### D1 — Local implementation overhead
The representation and algorithm are adequate; profiling identifies ordinary implementation work whose measured cost is sufficient to close the remaining gap.

Examples: avoidable copies, allocations, Python dispatch, syscalls, hashing duplication, parser overhead, FFI overhead.

**Default response:** R1 optimization is admissible if the cost budget is real.

### D2 — Execution-architecture duplication
The system repeatedly observes, authenticates, scans, materializes, sorts, hashes, decodes, or reconstructs facts that are already available or could have a single semantic owner.

**Default response:** remove a whole pass, fuse ownership, share operation-scoped facts, or convert repeated work into a proof/cache with exact accounting.

### D3 — Search / admission architecture
A large fraction of work is spent constructing or evaluating candidates that later lose, or on heuristics that cannot safely terminate early.

**Default response:** exact lower bounds, impossibility proofs, single-pass admission, branch-and-bound, exact futility filters, better tournament organization, or another algorithmic change that avoids losing work before it is paid.

### D4 — Representation / physical-layout floor
Evidence shows the current representation family cannot satisfy the strict contract even under unrealistically favorable control/metadata assumptions, or repeated cost export makes the present boundary structurally non-Pareto.

**Default response:** invent a new physical/semantic organization, locality grouping, reconstruction model, adaptive portfolio boundary, or other representation family. Further metadata shaving is subordinate support work, not the primary strategy.

### D5 — Productization / platform red
A mechanism already has sufficiently strong candidate evidence, but canonical semantics, recovery, locality, native, Android, portability, selector, or exact common-fingerprint authority is incomplete.

**Default response:** finish productization. Novelty is not rewarded for delaying a proven win.

A workload may carry more than one class. The highest-leverage causal class controls the next hypothesis.

---

## 3. Radicality tiers

Every material performance/research hypothesis MUST declare a radicality tier. “Radical” is not praise; it describes which system boundary changes.

- **R0 — Measurement / disproof only.** Profiler, lower-bound oracle, exact contribution measurement, impossibility proof, differential harness, causal attribution.
- **R1 — Local optimization.** Same representation and architecture; faster implementation of existing work.
- **R2 — Execution architecture.** Remove/fuse passes, move semantic ownership, operation-scoped caches, single observation pipeline, native hot-path ownership, bounded parallelism changes.
- **R3 — Algorithm / search redesign.** Exact terminals, branch-and-bound, new admission/tournament/search organization, new cost model, proof-directed candidate construction.
- **R4 — Representation / physical semantics.** New on-disk physical organization, reconstruction family, locality grouping, semantic factoring, adaptive representation portfolio, or another change that materially alters the achievable size/time frontier.

The rubric NEVER requires a higher tier merely to appear inventive. It requires the **lowest tier capable of changing the fact that currently makes the row lose**.

---

## 4. Saturation triggers — when optimization is no longer enough

These triggers are mandatory anti-stagnation law.

### S1 — Proven floor trigger
If a valid lower-bound or impossibility analysis shows the current representation family cannot beat the relevant strict competitor while preserving required semantics, the workload becomes **STRUCTURAL_RED / minimum R4**.

R0/R1/R2/R3 work may support or test the new family, but MUST NOT be presented as the main path to victory unless new evidence invalidates the floor proof.

### S2 — Repeated low-yield optimization trigger
If **two consecutive material experiments in the same mechanism family** each fail to close at least 20% of the then-remaining strict gap (or fail their preregistered materiality threshold) and profiling has not exposed a new sufficient local cost owner, the next primary hypothesis MUST move up at least one radicality tier or retire that family.

This prevents endless 10–50 microsecond work against a millisecond deficit.

### S3 — Family retirement trigger
After **three falsified material hypotheses in one mechanism family**, that family is retired as a primary R&D direction. It may be reopened only by new evidence that changes the causal model, lower bound, hardware regime, or representation boundary. A new threshold value is not new evidence.

### S4 — Exported-cost loop trigger
If a family repeatedly improves size while losing creation/runtime/locality/RSS, or improves speed while losing the strict size floor, and two rehabilitation attempts merely move the debt between metrics, the next primary hypothesis MUST change an architectural or representation boundary (R2–R4 as diagnosis warrants) rather than continue scalar tuning.

### S5 — Speculative-work dominance trigger
If exact profiling shows that >=25% of a strict-critical path is spent on candidates/edges/searches that are ultimately rejected, or an exact contribution oracle shows a large search family selects zero useful outputs on the target while preserving a meaningful adversarial opportunity set, prioritize an R3 exact futility/lower-bound/single-pass design before further local acceleration of the speculative work.

### S6 — Proven-win productization trigger
If a mechanism has already demonstrated a reproducible strict size+create win against both external competitors on the target semantics and the remaining blockers are D5, productization gets priority over inventing a replacement. The research queue may continue orthogonally, but it may not strand a proven win.

---

## 5. The strict-gap ledger

Before choosing a material R&D target, establish the current exact evidence for the workload in the dimensions that can block domination:

- CMPCT complete archive bytes;
- ZIP/Deflate complete archive bytes;
- solid Zstd-19 complete archive bytes;
- CMPCT complete creation time;
- ZIP creation time;
- Zstd-19 creation time;
- accepted v0.29 bytes for the identical frozen workload;
- relevant v0.29 runtime/RSS/selective-read floors;
- current locality/decode-unit/recovery/integrity/platform state;
- strongest candidate mechanism and its evidence fingerprint;
- current root-cause class D0–D5;
- minimum radicality tier R0–R4;
- last material hypotheses in this family and measured gap closure;
- next decisive falsification test.

Useful normalized gaps include:

`size_gap_to_X = CMPCT_bytes - X_bytes`

`time_gap_to_X = CMPCT_create - X_create`

and, for a candidate experiment:

`gap_closure_fraction = (old_positive_gap - new_positive_gap) / old_positive_gap`

where positive gap means CMPCT is losing. If the row is already winning that dimension, preserve the margin rather than optimizing it away.

Do not hide a losing dimension inside an aggregate score.

---

## 6. Research Priority Score (RPS)

Score hypotheses for **research allocation**, not promotion. Maximum 100 points.

### A. Domination necessity — 0–15
- 0: unrelated to a strict red or required release floor.
- 5: improves a secondary runtime/reliability concern.
- 10: attacks a material red.
- 15: attacks a row/bottleneck that cannot reach 15/15 without this class of change.

### B. Upside ceiling — 0–20
Estimate from profiling, lower bounds, candidate evidence, or a defensible cost model.
- 0–5: cannot plausibly close a meaningful fraction of the gap.
- 6–12: material partial closure.
- 13–17: can plausibly close the current row.
- 18–20: could close the row and create margin or help multiple rows.

### C. Root-cause fit — 0–15
How directly does the mechanism attack the diagnosed fact that causes the loss?
- 0: cosmetic/uncausal.
- 5: correlated with the bottleneck.
- 10: directly removes/reduces the measured owner.
- 15: changes or eliminates the causal constraint itself.

### D. Generality — 0–10
- 0: benchmark-identity dependent — **automatic rejection**, regardless of total.
- 3: narrow structural case with principled admission.
- 6: reusable family-level mechanism.
- 10: content-agnostic primitive or invariant with cross-workload leverage.

### E. Information gain / falsifiability — 0–15
Reward experiments that teach us something decisive even when they fail.
- 0–4: noisy outcome; weak causal interpretation.
- 5–9: bounded A/B with useful negative evidence.
- 10–12: directly separates competing causal models.
- 13–15: proves a lower bound, impossibility, exact identity, or mechanism-level result that can retire/authorize an entire family.

### F. Decisive-experiment efficiency — 0–10
This is not “cheap is always better”; it asks whether the smallest scientifically valid test can answer the question promptly.
- 0–3: expensive and ambiguous.
- 4–7: moderate cost, clear outcome.
- 8–10: cheap/bounded and decisive.

### G. Composability / survival path — 0–10
Can the gain survive locality, recovery, native, Android, no-regression, and canonical semantics?
- 0–3: likely exports unbounded debt or requires reader complexity.
- 4–7: plausible rehabilitation path.
- 8–10: naturally compatible or byte/grammar neutral.

### H. Simplicity / portability — 0–5
Prefer the mechanism whose final explanation and shared implementation remain bounded and portable.

### Priority bands
- **80–100:** execute/queue now unless a D5 proven-win blocker has higher immediate release leverage.
- **65–79:** strong frontier candidate; advance when prerequisites are ready.
- **50–64:** run only when cheap, needed as a control, or directly unblocking a higher-scoring hypothesis.
- **<50:** do not spend deep CI/research budget without new evidence.

A high score cannot override a saturation minimum tier. An R1 hypothesis on an S1 minimum-R4 workload is inadmissible as the primary strategy even if someone inflates its score.

---

## 7. Micro-optimization admissibility test

R1 work is valuable when it can actually win. Before spending material time on it, answer all three:

1. Is the remaining strict gap small enough that the measured local cost owner could close it with realistic efficiency?
2. Is that cost inside the benchmark timing boundary and not already required by an invariant that cannot be removed?
3. Has this mechanism family avoided S1–S4 saturation?

If any answer is no, R1 may be used only as supporting work; the primary hypothesis must move to the appropriate R2–R4 tier.

This rule explicitly preserves near-boundary work such as removing a known redundant traversal while preventing endless polishing of a representation whose theoretical floor already loses.

---

## 8. Mandatory hypothesis portfolio

For every meaningful strict-red problem, generate at least **three genuinely different solution classes** before committing deep engineering budget, unless a unique correctness fix exists:

1. **simplest strong control** — usually R0/R1/R2;
2. **architecture/algorithm alternative** — R2/R3;
3. **representation/boundary alternative** — R4 when D4/S1 applies, otherwise the highest justified tier.

Do not implement all three. Score them, identify the cheapest decisive disproof for each, and kill weak branches early.

When a workload is STRUCTURAL_RED and no decisive higher-tier experiment is already in flight, the autonomous campaign MUST keep at least one admissible R3/R4 hypothesis active in the frontier queue. It may simultaneously finish D5 productization or near-boundary work on other rows.

Across any rolling **three substantive R&D activations** while the strict matrix remains below 15/15, at least one activation MUST materially advance the highest-scoring unblocked STRUCTURAL_RED hypothesis (experiment, implementation, oracle, or productization prerequisite), unless repository evidence shows that every such hypothesis is blocked by a prerequisite. The exception and blocker must be recorded rather than silently substituting more micro-tuning.

This is a portfolio floor, not a novelty quota: a proven-win D5 lane may still dominate the other activations.

---

## 9. Preregister the experiment before implementation

Every material frontier experiment MUST make these facts explicit in code comments, durable notes, workflow assertions, or its evidence record:

- exact workload/corpus fingerprint or content-agnostic target family;
- current strict gaps and inherited floor that motivate the work;
- diagnosis D0–D5;
- radicality tier R0–R4 and any active saturation trigger S1–S6;
- RPS with a brief rationale, not just a number;
- mechanism hypothesis;
- strongest simpler control;
- strongest plausible failure explanation;
- invariants that cannot change;
- what work/bytes the mechanism predicts it will eliminate or reorganize;
- disproof condition;
- materiality threshold tied to the actual remaining gap or dominant stage;
- exact identity/equivalence checks;
- hidden-cost accounting: hashing, preprocessing, verification, metadata, recovery, publication, RSS, temporary I/O, locality, decode unit, native/platform burden;
- next productization prerequisite if successful;
- retirement/pivot action if falsified.

A benchmark-name/hash/path-dependent production policy is automatically invalid regardless of score or measured win.

---

## 10. Materiality threshold law

Do not celebrate a statistically real improvement that is strategically irrelevant.

A frontier experiment should normally be designed to do at least one of the following:

- close >=25% of the remaining losing gap on the targeted strict dimension;
- eliminate >=10% of a measured dominant stage when that stage is large enough to matter to the strict gap;
- remove an entire pass/traversal/materialization/authentication/search category;
- establish a reusable mechanism-level candidate strict win;
- establish a lower bound/impossibility result that retires a losing family;
- convert a speculative search into exact proof-directed work;
- materially reduce a release-blocking runtime/RSS/locality debt without changing bytes;
- produce decisive negative evidence that changes the next strategy.

Smaller thresholds are admissible when the row is already extremely near the boundary and the predicted absolute gain is sufficient to cross it. State that explicitly.

---

## 11. Mandatory self-critique loop for every material R&D iteration

Each iteration has three roles. They may be performed by the same agent, but the reasoning and evidence boundaries must be explicit.

### Pass 1 — Referee / pre-mortem
Before implementation, try to reject the idea.

Ask:
- Is the diagnosed cost actually causal and large enough?
- Is there a theoretical floor that makes this tier insufficient?
- Am I accelerating work that should instead be eliminated?
- Could a simpler control capture the same benefit?
- Does the idea accidentally encode benchmark identity?
- What metric will receive the exported cost?
- Does recovery/locality/native/Android destroy the apparent win?
- What exact result would make me retire this family?

If the hypothesis survives, revise it to incorporate the strongest criticism before coding.

### Pass 2 — Builder / decisive instrument
Build the smallest exact experiment capable of changing the decision. Preserve semantics and measure the full required cost boundary.

### Pass 3 — Hostile reviewer / post-mortem
After results, attempt to explain the gain away.

Ask:
- Is this noise, order bias, cache state, harness asymmetry, or stale fingerprint?
- Is final archive/tree identity exact where required?
- Was mandatory work moved outside timing?
- Did locality, recovery, RSS, or reader complexity silently worsen?
- Does an adversarial/unseen structural case break admission?
- Did the experiment test the actual product path or a cheaper research surrogate?
- Does the result close enough of the real strict gap to matter?
- Should the RPS, diagnosis, or minimum radicality tier now change?

Then record one of: `PROMOTE_NEXT_PREREQUISITE`, `REHABILITATE_DEBT`, `ITERATE_SAME_FAMILY`, `ESCALATE_RADICALITY`, or `RETIRE_FAMILY`.

A run that simply says “promising” without choosing one of these states is incomplete research accounting.

---

## 12. Exact futility is a first-class research target

CMPCT MUST treat **proof that work cannot win** as an optimization primitive.

When possible, prefer:

`cheap exact facts -> optimistic lower bound / necessary condition -> prove candidate cannot beat incumbent -> never construct it`

over:

`construct candidate -> measure candidate -> discover it loses -> discard it`

This applies to graph anchors, splice edges, codec candidates, semantic transforms, nested-container hypotheses, representation families, and verification/materialization paths.

Heuristic early cancellation is not equivalent. If cancellation can change the winning archive, it must remain research until an exact or otherwise release-authorized invariant exists.

---

## 13. Representation invention contract

When D4/S1 applies, future work MUST explicitly search outside the current representation vocabulary.

At least one R4 hypothesis set should consider mechanisms such as, where relevant:

- locality-scoped physical groups rather than one global physical organization;
- self-describing record streams that eliminate duplicated semantic tables;
- authenticated exact views/inverses rather than duplicated bytes;
- adaptive portfolios whose admission is structural and content-agnostic;
- separate physical and semantic ownership where one can be reconstructed exactly from the other;
- entropy/control co-design rather than metadata-after-the-fact compression;
- chunk/group boundaries chosen by recoverability/locality economics rather than codec convenience;
- database/index/dedup/content-addressed-storage/error-correcting-code ideas adapted to archive constraints;
- representations that make selective reads/recovery cheaper by construction instead of repairing amplification later.

These are prompts, not prescribed solutions. The invention pass must still produce competing hypotheses and falsifiable tests.

**Do not preserve a losing representation merely because much code already exists for it. Preserve its reader when compatibility requires it; replace its encoder strategy when evidence requires it.**

---

## 14. Productization survival test

Before declaring a research mechanism “the answer,” sketch how it survives each relevant boundary:

- complete artifact bytes including metadata/control/recovery;
- complete creation timing;
- accepted v0.29 zero-byte floor;
- extraction/verification/runtime floor;
- locality <=8x;
- decode unit <=8 MiB;
- recovery and SHA-256/integrity;
- hostile-input/resource bounds;
- deterministic canonical semantics;
- native shared core;
- Android/platform parity;
- absence/fallback of optional helpers;
- selector/admission generality;
- exact common-fingerprint 15-workload authority.

A mechanism may still be explored when some answers are unknown, but unknowns become explicit regression/productization debt. A research win is strongest when its survival path is short because it removes work without changing bytes or reader grammar.

---

## 15. Autonomous hourly application

At the start of each scheduled/autonomous material activation, after recovering exact repository/CI/matrix truth:

1. identify the strict-red workloads and major v0.29 runtime/RSS reds;
2. classify the highest-value reds D0–D5;
3. apply S1–S6 saturation triggers;
4. inspect in-flight experiments so work is not duplicated;
5. score the best unblocked hypotheses with RPS;
6. choose work from two queues:
   - **Frontier queue:** highest-RPS hypothesis that can change a strict/structural red;
   - **Convergence queue:** highest-leverage D5/productization/evidence prerequisite for an already-proven win;
7. ensure the rolling-three-activation STRUCTURAL_RED portfolio floor remains satisfied;
8. while CI runs, advance the other queue or another dependency-safe high-RPS hypothesis;
9. at handoff, record how diagnosis, RPS, saturation state, and next experiment changed.

The purpose is to stop autonomous work from naturally drifting toward whichever tiny patch is easiest to land.

---

## 16. End-of-run R&D audit

When material R&D occurred, the handoff MUST include, compactly:

```text
strict_target: <workload/lane>
diagnosis: <D0-D5>
radicality: <R0-R4>
saturation_trigger: <none|S1-S6>
RPS: <0-100 + brief reason>
hypothesis_result: <supported|falsified|ambiguous|not_measured>
measured_gap_change: <bytes/time/RSS/etc>
self_critique: <strongest surviving objection>
decision: <PROMOTE_NEXT_PREREQUISITE|REHABILITATE_DEBT|ITERATE_SAME_FAMILY|ESCALATE_RADICALITY|RETIRE_FAMILY>
next_decisive_test: <one sentence>
```

This audit does not replace the normal exact-head/CI/duration handoff.

---

## 17. Rubric anti-gaming rules

The rubric is invalid if used to rationalize a preferred idea after the fact.

- Never inflate RPS to justify work already chosen.
- Never call a threshold tweak R3.
- Never call a new header layout R4 when the physical cost model is unchanged.
- Never lower the strict competitor semantics or frozen workload to increase “gap closure.”
- Never score benchmark-identity dispatch above zero generality; it is rejected.
- Never treat a candidate-only speed number as product creation time.
- Never use aggregate savings to hide a losing row.
- Never convert a missing physical/platform receipt into research credit.
- Never let radicality excuse complexity without a survival path.
- Never let simplicity excuse staying inside a family whose floor is already proven losing.

---

## 18. Rubric evolution / meta-falsification

This rubric itself is subject to evidence.

Revisit it when any of these happen:

- three consecutive highest-RPS experiments produce little decision value;
- the portfolio repeatedly over-selects either micro-optimization or speculative rewrites;
- a major strict win came from a mechanism the score would have suppressed;
- 15/15 progress stalls for >=6 substantive R&D activations without a newly retired blocker or material gap closure;
- a new competitor/constraint changes the domination objective.

A rubric revision MUST preserve prior iteration criticism and explain which selection failure it repairs. Process changes do not weaken release law and do not earn core-version credit.

---

# Design iteration record and adversarial review

The contract above is the result of explicit iteration rather than a first-pass scorecard.

## Iteration 0 — single weighted “best next task” score

**Design:** rank ideas by expected benchmark gain, ease, generality, and productization distance.

**Self-critique:** rejected. It systematically favors safe near-release tweaks because their evidence and implementation cost are easier to estimate. That is precisely how a project can spend hundreds of iterations polishing 10–50 microseconds while a representation has a proven kilobyte or millisecond structural deficit. It also conflates research value with promotion readiness.

**Revision:** separate research priority from release promotion; add explicit diagnosis and radicality tiers.

## Iteration 1 — radicality tiers plus mandatory high-radicality quota

**Design:** require a fixed fraction of activations to perform R3/R4 work.

**Self-critique:** rejected as too blunt. It rewards novelty theater, can force representation churn on a 1% near-boundary implementation deficit, and can strand a mechanism that already achieved a strict candidate win but needs recovery/native/Android productization.

**Revision:** replace unconditional novelty quota with evidence-triggered minimum radicality (S1–S5), plus S6 productization priority and a rolling structural-red portfolio floor only when structural reds actually exist.

## Iteration 2 — final two-queue evidence-triggered rubric

**Design:** diagnosis D0–D5, radicality R0–R4, saturation S1–S6, RPS, strict-gap ledger, two queues, rolling structural-red floor, mandatory pre/post hostile review, and explicit terminal decisions.

**Self-critique:** this is much harder to game, but three residual risks remain:

1. **Score subjectivity.** RPS can still be inflated. Mitigation: raw gap/profiling evidence, automatic rejection rules, explicit rationale, and post-result rescoring.
2. **Research bureaucracy.** A rubric can consume the time intended for engineering. Mitigation: the audit is intentionally compact; deep prose is required only for material frontier hypotheses, not ordinary fixes.
3. **Overconfidence in known solution classes.** Even R4 can become a checklist of familiar ideas. Mitigation: the representation invention contract explicitly requires competing hypotheses and outside-vocabulary search when current framing is saturated.

**Verification conclusion:** Iteration 2 is adopted because it simultaneously (a) forces higher-order invention when current families are demonstrably saturated, (b) preserves conventional optimization where it can genuinely cross a boundary, (c) prevents novel research from stealing productization time from proven wins, (d) rewards decisive negative evidence, and (e) leaves the strict 15/15 release law unchanged.

---

## Final doctrine

**Optimize when the measured remaining cost can win. Redesign execution when duplicated work is the loss. Redesign search when losing candidates consume the budget. Replace the representation when its floor cannot win. Productize immediately when a mechanism already can win. Prove futility as early as possible. Count nothing as domination until the exact product does it on every row.**
