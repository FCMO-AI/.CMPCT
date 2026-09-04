# CMPCT Fundamental Research Doctrine — Finalized Research Operating System

Status: **normative for fundamental research allocation on the active CMPCT frontier**.

Finalization date: 2026-08-31 (America/Mexico_City).

This version supersedes the first Foundry doctrine previously stored at this path. That earlier text remains preserved in Git history (pre-final blob `cd5e6589f806df10742ca5d1acfbf654c7351ec0`) and is historical rather than normative wherever it conflicts with this document.

This doctrine exists to institutionalize the development mode that produced CMPCT's largest conceptual advances — native content-aware storage, EntropyGraph, EntropyGraph II / the Resemblance Compiler, Mosaic, Geometry and related changes that altered the archive's model of information rather than merely tuning an inherited implementation.

It does **not** weaken any correctness, integrity, recovery, locality, portability, hostile-input, benchmark, evidence, format or release requirement.

---

## 0. Authority and precedence

CMPCT previously accumulated partially overlapping instructions in repository documents and scheduler prompts. That is a control-plane defect. The final authority model is:

1. **Observed evidence is immutable truth.** A policy may interpret evidence; it may not rewrite a measurement, failed experiment, artifact fingerprint or competitor result.
2. **Hard product invariants and release law have veto authority.** Correctness, byte exactness, integrity/authentication, hostile-input/resource bounds, data preservation, declared recovery guarantees, format compatibility and exact release gates cannot be borrowed for research convenience.
3. `docs/AGI_ENGINEERING_STANDARD.md` governs engineering quality, falsifiability, evidence and adversarial review.
4. **This document governs fundamental research allocation and the Foundry/Forge/Custody operating model.**
5. `docs/RND_DOMINATION_RUBRIC.md` governs **Forge convergence only**: diagnosis and closure of known product/performance gaps. Its older whole-R&D role is superseded.
6. `docs/BREAKTHROUGH_REHABILITATION.md` governs preservation and repair of high-upside mechanisms with explicit rehabilitable debt.
7. `docs/ASSUMPTION_LEDGER.md` is an idea source and conditional-constraint ledger. It does not command implementation.
8. `docs/ACTIVE_RESEARCH_THESIS.md` is **mutable current state**, not constitutional law.
9. A frozen experiment/preregistration controls that specific experiment after freeze. It may not override higher-level invariants and may not be edited after result-bearing execution begins; changes require a new superseding preregistration/freeze while preserving the old one.
10. The ChatGPT scheduled task is an **execution kernel only**. It must recover strategy and current truth from the repository and must never become a second strategy authority.

When two lower-level instructions conflict, obey the higher level and preserve the conflict as a repository defect to fix.

---

# 1. North Star

CMPCT fundamental research is not primarily a campaign to make the current compressor slightly better or to turn a fixed benchmark matrix green one cell at a time.

Its research North Star is:

> **Expand the exact information relationships, reversible structures, reconstruction models and physical organizations that CMPCT can discover and exploit across arbitrary computer data, so that the achievable archive Pareto frontier itself becomes larger.**

The product objective remains demanding: actual promoted CMPCT must beat the required competitors under the repository's current strict contracts while preserving its stronger semantics. But those benchmarks are **courts and falsifiers**, not the exclusive source of scientific questions.

A red workload can reveal a missing abstraction. A green workload can contain a larger undiscovered abstraction. The Foundry is expected to investigate both.

The project should repeatedly ask:

1. What information is present that CMPCT's current model cannot express efficiently?
2. Which inherited assumption makes that information invisible or expensive?
3. What exact abstraction would make it representable?
4. Under generous but honest conditions, how much real headroom exists?
5. How much of the general data universe is plausibly addressable by that mechanism?
6. Can the mechanism survive discovery, locality, recovery, integrity, complexity and platform constraints?
7. Can the final product obtain the gain without imposing unacceptable cost on data that does **not** use the mechanism?

The goal is not novelty. The goal is **new capability with material addressable value and a credible route to a stronger product**.

---

# 2. Historical pattern: worldview deltas

CMPCT's strongest historical advances can be restated as changes in worldview:

- logical files and physical stored objects need not be identical;
- equal information should not be stored repeatedly;
- filesystem relationships such as sparse holes and hardlinks are information rather than merely bytes;
- a nested container may be content plus an exact reconstruction recipe rather than an opaque blob;
- an archive may be an authenticated reconstruction graph rather than a bag of isolated compressed files;
- near-equal information is still shared information even when exact equality fails;
- one target may have several independent explanatory ancestors;
- logical byte order need not be the physical order that best exposes structure;
- an exact bounded edit/reconstruction program may be a better physical description than chunk ownership.

These are the model for fundamental work.

A strong Foundry campaign should normally be explainable as:

> **Previously CMPCT assumed X. The new thesis says Y. If Y survives, CMPCT can represent Z that it could not efficiently represent before.**

That is the **Worldview Delta Test**.

A second test is the **new-noun test**:

> Can the concept be explained without naming the benchmark that motivated it?

A workload-specific threshold tweak may be excellent engineering. It is simply Forge work rather than the identity of a Foundry campaign.

---

# 3. Two engines and one Custody plane

The prior Foundry/Forge model was directionally correct but incomplete because evidence, safety and canonical truth are not research competitors. The final system therefore has **two engines plus one non-competing plane**.

## 3.1 Foundry — invention

The Foundry generates and falsifies alternative models of information.

Its legitimate outputs include:

- a new exact representational capability;
- an oracle showing large headroom;
- a reusable primitive or reconstruction model;
- a proof/search abstraction that removes an entire class of wasted work;
- structural-transfer evidence;
- a decisive impossibility result;
- a scoped family retirement;
- a smaller/generalized vocabulary that subsumes previous mechanisms.

The Foundry is thesis-driven, not workload-cell-driven.

## 3.2 Forge — convergence

The Forge makes evidenced mechanisms into a superior real product.

Its work includes:

- D0–D5 diagnosis;
- R0–R4 implementation/search/representation work for known product gaps;
- strict external gap closure;
- exact futility and removal of speculative work;
- rehabilitation of regression debt;
- generic content-driven admission;
- canonical semantics;
- reader, recovery, locality, integrity and native/platform implementation;
- no-regression validation and release authority.

`docs/RND_DOMINATION_RUBRIC.md` is normative Forge law.

## 3.3 Custody — truth, invariants and reproducibility

Custody does not compete for “innovation credit.” It protects both engines from self-deception.

Custody owns or enforces:

- evidence fingerprints and immutable negative results;
- benchmark symmetry and provenance;
- frozen preregistration boundaries;
- hard safety/integrity/resource invariants;
- format/version/release locks;
- reproducible zero-history handoff state;
- distinction between measured, inferred, planned and unmeasured claims.

Foundry cannot waive Custody to rescue an exciting thesis. Forge cannot waive Custody to obtain a green release matrix.

Tooling, CI, dashboards and research infrastructure are **Custody/support work** unless they actually produce decision-changing evidence. Building a beautiful oracle framework is not itself a Foundry breakthrough.

---

# 4. Universal substrate, specialized mechanisms

“General-purpose CMPCT” does **not** mean every mechanism must improve every file.

A mechanism may target a narrow structural predicate if:

- the predicate is discovered from content/structure rather than benchmark identity;
- non-applicable data falls back safely;
- admission cost is bounded;
- the mechanism's global carrying cost is justified;
- the final product remains general-purpose.

The desired architecture is a **universal substrate with rigorously admitted specialized exact mechanisms**, not a single universal transform and not a pile of benchmark-specific codecs.

---

# 5. Three evidence frontiers

Research questions fail when production economics are imposed too early or gifted costs are later forgotten. CMPCT uses three evidence frontiers.

## O0 — Oracle Frontier

Question:

> **If discovery/search were generously solved, is the information-model opportunity itself real?**

O0 may gift:

- expensive or exhaustive search;
- ideal candidate ordering;
- perfect anchor/base knowledge;
- offline optimization;
- large temporary analysis structures;
- learned proposal systems;
- unrealistic discovery wall time.

O0 may **never** gift away representation facts that a decoder/reconstruction actually needs:

- basis/source bytes that must exist;
- program/opcode/control bytes;
- lengths/tables/parameters;
- literals/residual streams;
- exact reconstruction;
- required semantic descriptors.

Every O0 result must maintain an **Oracle Gift Ledger** with:

- gifted discovery costs;
- fully charged representation costs;
- deferred product debts;
- claims the result explicitly does not support.

O0 is headroom evidence, never product-speed or release evidence.

## O1 — Research Frontier

Question:

> **Can the mechanism discover the opportunity generically and survive realistic bounded semantics?**

O1 requires:

- content-agnostic discovery/admission;
- exact cost accounting;
- structural transfer;
- hostile false-positive controls;
- bounded search/decode work;
- dependency/locality accounting;
- an estimate of addressable opportunity;
- global carrying-cost accounting;
- a credible product survival path.

Explicit rehabilitable debt may remain.

## O2 — Product Frontier

Question:

> **Can canonical CMPCT ship the mechanism and remain strictly stronger?**

All current product/release law applies, including complete archive bytes, create/extract/verify costs, locality, decode unit, recovery, integrity, deterministic behavior, native/platform parity, interoperability, no-regression and exact competitor authority.

Do not promote O0/O1 results into O2 language.

---

# 6. Radicality and breakthrough class are separate

Radicality describes **which boundary changes**. Importance describes **what the evidence proves**. Do not conflate them.

The Forge retains R0–R4:

- R0 measurement/disproof;
- R1 local implementation optimization;
- R2 execution architecture;
- R3 search/admission algorithm;
- R4 representation/physical semantics.

Foundry adds:

- **R5 — information-model / reconstruction-ontology invention:** change what CMPCT considers an object, relation, explanatory source, reversible view, physical owner or reconstruction program.

R5 receives no automatic priority. An R1 fix that removes the actual release blocker can be exactly correct. A flashy R5 idea with no headroom or addressable value should die.

Breakthrough evidence is classified separately:

- **B0 boundary fix:** existing model crosses a near boundary;
- **B1 mechanism improvement:** removes/reorganizes a meaningful category of work/bytes and transfers;
- **B2 frontier breakthrough:** reusable capability materially expands the attainable Pareto frontier for a structural family;
- **B3 information-model breakthrough:** changes what information/relationships CMPCT can represent efficiently.

A project version does not need to be B3. The Foundry's purpose is to ensure B2/B3 opportunities continue to be sought rather than accidentally disappearing from the development process.

---

# 7. Thesis initiation gate

The previous doctrine risked forcing an active R5 thesis simply to prove that the Foundry was alive. That is novelty theater. **No active thesis is better than a weak active thesis.**

A question becomes the primary `ACTIVE_RESEARCH_THESIS` only after passing this initiation gate:

1. **Worldview delta:** the challenged assumption and proposed model are explicit.
2. **Capability delta:** state what CMPCT could represent/discover/prove afterward that it cannot efficiently do now.
3. **Non-triviality:** the hypothesis is not merely a renamed threshold, codec switch, benchmark special case or known Forge defect.
4. **Prior-art boundary:** known adjacent work is identified well enough to avoid rediscovering a solved problem while preserving room for independent thinking.
5. **Plausible headroom:** there is a defensible reason the missing capability could matter materially.
6. **Addressable-opportunity hypothesis:** identify where/how often the structural predicate may occur, even if the initial estimate is rough.
7. **Cheap decisive oracle:** there is an experiment capable of changing the decision without first building the final product.
8. **Disproof/retirement rule:** state the result that kills or reformulates the thesis.
9. **Product survival sketch:** reader complexity, control bytes, dependencies, locality, recovery, safety, native/platform burden and generic admission are at least plausibly bounded.
10. **Complexity/carrying-cost hypothesis:** identify what new permanent mechanisms or global costs could be introduced if the idea survives.

If no candidate passes, keep the Foundry idle rather than inventing ceremony.

---

# 8. Foundry heartbeat without a novelty quota

An empty Foundry is permissible; a permanently forgotten Foundry is not.

If no primary thesis is active, conduct a bounded **Foundry Review** when any of these triggers occurs:

- a major representation family is retired;
- a major product milestone/release is reached;
- the strict frontier has materially plateaued;
- new external evidence changes the available vocabulary;
- or six consecutive substantive Forge-only activations occur without a Foundry review, unless an exact near-release promotion boundary makes interruption clearly irrational.

A Foundry Review means:

- inspect the Assumption Ledger and scoped negative constraints;
- inspect newly exposed residual/unexplained cost;
- generate a small set of genuinely different worldview hypotheses;
- run or preregister the cheapest decisive oracle for the strongest candidate when justified.

It does **not** require activating a thesis.

This is a heartbeat, not an R5 quota.

---

# 9. Foundry thesis lifecycle and clean handoff

The previous single state chain blurred invention and productization. The final lifecycle separates ownership.

## Foundry-owned states

`QUESTION -> CHARTERED -> ORACLE -> CAUSAL_SEED -> TRANSFER -> HANDOFF_READY`

Terminal Foundry states:

`FALSIFIED`, `FAMILY_RETIRED`, `SUPERSEDED`, `NO_ACTIONABLE_HEADROOM`.

When a mechanism reaches `HANDOFF_READY`, the Foundry records the capability, evidence, transfer scope, debts and generic survival conditions, then hands it to the Forge.

## Forge-owned states

`ADMISSION -> REHABILITATION -> CONVERGENCE -> PRODUCT_CANDIDATE -> PROMOTED`

or terminal:

`PRODUCT_RETIRED`, `RETURN_TO_FOUNDRY`.

Once handed off, the mechanism should not keep monopolizing the primary Foundry thesis merely because productization remains unfinished. This preserves continuous invention without stranding real wins.

---

# 10. Thesis lease and anti-sunk-cost law

Fundamental ambition does not buy indefinite runway.

A thesis lease is measured by **information gain**, not by commit count or wall-clock duration.

A substantive Foundry activation should produce at least one of:

- a new oracle result;
- a changed headroom estimate;
- a falsified causal explanation;
- a new structural-transfer result;
- an operator/hypothesis retirement;
- a scoped negative constraint;
- a thesis state transition;
- a decisive experimental instrument whose result is actually pending externally.

If three substantive Foundry activations produce none of these and no genuine external experiment is pending, the next Foundry action must be a hostile thesis review rather than further implementation.

If six substantive activations produce no decision-changing evidence, state transition or scientifically meaningful constraint, reformulate or retire unless the delay is caused by a documented external blocker to the already-preregistered decisive test.

Do not measure progress by lines of code, DSL size, workflow count, commits or documentation volume.

---

# 11. Addressable Opportunity Mass (AOM)

A large percentage win on a rare synthetic corner is not automatically a large CMPCT breakthrough.

Every thesis advancing beyond O0 should estimate **Addressable Opportunity Mass**:

> the amount/frequency of real arbitrary-data bytes or objects for which the mechanism's content-derived structural predicate is plausibly applicable and materially useful.

AOM is not one universal scalar and need not be precise early. Record at least:

- structural predicate;
- observed prevalence in discovery/transfer corpora;
- fraction of logical bytes/objects potentially addressable;
- oracle saving within addressable data;
- false-positive/admission rate;
- confidence and corpus bias.

A useful rough quantity is:

`addressable_gain = addressable_bytes × conditional_saving_fraction`

but never hide uncertainty behind the product.

A very high conditional saving with tiny AOM may still justify a specialized mechanism if its global carrying cost is negligible. A moderate saving over enormous AOM may be more strategically important than a spectacular niche result.

---

# 12. Global mechanism carrying cost

Portfolio fallback can hide a serious systems tax: every new mechanism may impose costs even when it loses.

Before O1 -> handoff and again before O2 promotion, account for the mechanism's **global carrying cost**:

- nomination/prefilter CPU on non-winning data;
- expensive auditions ultimately rejected;
- metadata/descriptor overhead;
- reader-visible operator count;
- parser/fuzz/security states;
- binary/code size and startup cost;
- recovery/locality interactions;
- native/platform implementation burden;
- maintenance and interoperability burden;
- interactions with other mechanisms;
- opportunity cost of a larger search space.

A new mechanism should normally satisfy at least one:

1. it has a cheap, high-recall necessary-condition/prefilter;
2. its full audition is cheap enough globally;
3. it subsumes/retires older mechanisms;
4. its addressable product gain is large enough to pay the global tax with clear margin.

This creates a **portfolio entropy** discipline: CMPCT must not become better on selected cases while becoming permanently more expensive everywhere else.

---

# 13. Concept-compression ratchet

Major invention should periodically make CMPCT's conceptual vocabulary **smaller or more general**, not only larger.

For each new reader-visible primitive ask:

- can it be expressed through an existing general IR?
- can it subsume an older special case?
- can two existing mechanisms be lowered into one shared primitive?
- can research-only richness be distilled before canonicalization?

Track:

- reader-visible primitives;
- grammar/control bytes;
- parser states;
- dependency/fanout patterns;
- recovery cases;
- native/platform implementations;
- fuzz/security surface.

A successful research compiler may be most valuable when it discovers a recurring motif that should become **one simple new primitive**, rather than when the entire compiler becomes the production format.

The reader should remain bounded and boring even if the encoder/researcher becomes sophisticated.

---

# 14. Frozen-experiment immutability

Preregistration only has value if unfavorable evidence cannot rewrite the experiment.

Once a result-bearing execution begins against a frozen preregistration/instrument:

- do not edit its grammar, thresholds, comparator, corpus contract, cost boundary or positive/negative interpretation;
- deterministic harness defects may be fixed only under a predeclared defect exception;
- any material scientific change creates a **new superseding preregistration/freeze**;
- preserve the previous freeze and failed/inconclusive result;
- later policy documents may reinterpret strategic importance but may not rewrite what the experiment measured.

The active F-01 O0.1 frozen instrument is therefore left untouched by this final doctrine.

---

# 15. Structural-transfer and anti-overfit law

A mechanism discovered on one famous fixture must prove that it discovered a relationship rather than a dataset artifact.

Preferred ladder:

1. discovery instrument;
2. hostile negatives;
3. held-out structural variations generated after the mechanism/admission rule is frozen where practical;
4. generator-distinct or independent real public transfer;
5. broad opportunity/AOM scan;
6. full frozen product matrix.

Vary causal dimensions — edit density, alignment, ordering, widths, noise, false relatives, source count, scale and locality pressure — rather than merely changing seeds.

Production/research policy may not use benchmark names, paths, frozen hashes or equivalent identity.

---

# 16. Asymmetric intelligence law

CMPCT should exploit a powerful asymmetry:

> **The encoder/research process may be intelligent; the decoder must remain deterministic, bounded and independently checkable.**

Research may use:

- exhaustive search;
- dynamic programming;
- optimization;
- theorem-like lower bounds;
- learned proposal/ranking systems;
- external analysis.

Those systems may **nominate** an exact representation. They do not establish correctness.

Promotion requires stored semantics that are explicit/deterministically implied and independently verifiable. Decode does not repeat expensive research search and does not require the learned proposal prior unless a future explicit canonical decision proves such a dependency desirable.

---

# 17. Independent ideation before external anchoring

External literature is mandatory when it can materially change the decision, but it can also anchor the project into somebody else's vocabulary.

For major Foundry question generation, prefer two passes when practical:

1. **local blind pass:** attack CMPCT's assumptions and residual evidence without first searching for a named outside solution;
2. **external adversarial pass:** search primary research/implementations to identify prior art, stronger controls, missed abstractions and reasons the local thesis may already be solved or wrong.

Then synthesize.

Relevant adjacent fields include lossless compression, program synthesis/MDL, compiler superoptimization, databases/columnar encodings, grammar compression/self-indexing, backup/dedup/delta storage, version control, content-addressed storage, repetitive collections/computational biology and recovery/error-correcting systems.

Examples of useful current vocabulary include Brevis-style reversible program synthesis, OpenZL-style compression graphs, ZipLLM/BitX-style joint deduplication + delta design and grammar/self-index work. These are evidence and vocabulary, not templates that CMPCT must copy. Brevis and OpenZL also mean CMPCT must not claim generic program synthesis or transform graphs themselves as novel.

---

# 18. Negative evidence as scoped conditional law

Preserved failures are essential, but “negative evidence becomes law” can fossilize the project if scope is lost.

Every family retirement/negative constraint should record:

- exact mechanism family;
- tested regime/corpus/scale;
- favorable assumptions already gifted;
- observed floor/failure;
- causal interpretation;
- what remains unproven;
- **reopening predicates**.

Example form:

> Under assumptions A/B/C and regime R, family F retained deficit D even with gifted cost G. Parameter tuning inside F lacks a credible crossing mechanism. Reopen only if assumption A changes, a new representation boundary removes cost C, or evidence shows the tested regime was not representative.

A new threshold value is not a reopening predicate.

Negative evidence is therefore a **conditional theorem**, not dogma.

---

# 19. Foundry candidate selection without a gamable genius score

Do not reduce thesis quality to one scalar. Maintain a **Breakthrough Evidence Vector**:

- **Capability delta** — how new is the representational ability?
- **Oracle headroom** — how large is the best honest opportunity?
- **AOM** — how much data could plausibly benefit?
- **Causal confidence** — do we know what produced the gain?
- **Transfer strength** — how far beyond the discovery fixture does it survive?
- **Survivability** — is there a credible bounded O2 path?
- **Complexity/carrying cost** — what permanent tax does it introduce?
- **Information gain of next test** — how decisively can we learn more?

Prefer hypotheses that Pareto-dominate alternatives on this vector. When tradeoffs are unclear, run the cheapest decisive oracle rather than inventing arbitrary weights.

The Forge may continue to use its RPS for convergence allocation because its objective is narrower and better measured.

---

# 20. Research infrastructure earns no automatic scientific credit

A common failure mode of autonomous R&D is building tools indefinitely because tooling feels productive.

Research tooling counts as a Foundry advance only when it:

- enables a previously impossible decisive experiment; and
- is immediately tied to an actual preregistered decision; or
- produces decision-changing evidence.

Otherwise it is support/Custody work.

A larger compiler, more workflow lanes, more dashboards or a prettier evidence schema are not scientific progress by themselves.

---

# 21. Research-program diversity without fragmentation

Maintain:

- at most **one primary deep Foundry thesis**;
- a small secondary opportunity queue in the Assumption Ledger;
- independent Forge campaigns for mechanisms already handed off.

Secondary ideas should remain cheap oracles until they clearly dominate the incumbent thesis on headroom/information gain or the incumbent is falsified/superseded.

Avoid both monoculture and five-way novelty theater.

When generating replacement theses, use several lenses rather than descendants of one familiar idea:

- assumption inversion;
- residual/unexplained-information analysis;
- competitor causal-advantage analysis;
- cross-domain abstraction import;
- forbidden-vocabulary counterfactual: temporarily forbid the current favorite primitives and ask how else the exact information could be described.

---

# 22. Foundry experiment method

Every material Foundry thesis proceeds through four scientific passes.

## F0 — Worldview challenge / charter

Pass the Thesis Initiation Gate. State the inherited assumption, capability delta, prior-art boundary, AOM hypothesis and kill rule.

## F1 — Generous honest oracle

Give discovery enough advantage to reveal real headroom. Maintain the Oracle Gift Ledger and full representation charge.

## F2 — Causal adversary

Try to explain the result using a simpler known mechanism. Ablate operators/sources. Test hostile negatives. Determine what actually generated the gain.

## F3 — Transfer, opportunity and survival

Freeze the mechanism/admission rule, test structural transfer, estimate AOM, charge global carrying cost and evaluate product survival.

Then choose one explicit Foundry decision:

`ADVANCE_ORACLE`, `DISCOVER_PRIMITIVE`, `REFORMULATE`, `HANDOFF_READY`, `NO_ACTIONABLE_HEADROOM`, `FALSIFIED`, `FAMILY_RETIRED`, `SUPERSEDED`.

“Promising” is not a decision.

---

# 23. Forge handoff contract

A mechanism is `HANDOFF_READY` only when the Foundry can state:

- capability/worldview delta;
- exact evidence and fingerprints;
- causal mechanism;
- transfer scope;
- AOM estimate and uncertainty;
- false-positive/admission evidence;
- complete known debt vector;
- global carrying-cost risks;
- required reader/IR semantics;
- negative constraints;
- next cheapest Forge prerequisite.

The Forge then owns convergence. If Forge discovers that product survival requires changing the information model again rather than ordinary rehabilitation, it may return the problem to Foundry as `RETURN_TO_FOUNDRY` with exact new evidence.

---

# 24. Application to the current v0.30 frontier

This finalization is **process law**, not a retroactive scientific result.

- The current F-01 General Reversible Structure Compiler remains the primary Foundry thesis because it already passed the earlier initiation logic and has a frozen O0.1 instrument. The frozen experiment is not changed by this doctrine.
- Any O0.1 result must still obey its existing frozen comparator, corpus, search and decision contract.
- If F-01 advances beyond O0, it must acquire the newly explicit AOM and global carrying-cost evidence before handoff.
- Existing strict-win mechanisms such as the current bounded-drift research result remain Forge assets and should continue through productization rather than being pulled back into F-01 for elegance.
- Known execution/search reds remain Forge work unless new evidence demonstrates an information-model defect.
- The old requirement that the Domination Rubric allocate all R&D or force a structural-red activation every rolling three runs is superseded. Forge still uses saturation and productization rules; Foundry uses this doctrine and the heartbeat/initiation system.

---

# 25. Final anti-gaming rules

CMPCT agents must not:

- relabel ordinary tuning as R5;
- invent a thesis after seeing a favorable result merely to rationalize it;
- keep a weak thesis alive because it has a grand name;
- treat code/tooling volume as research progress;
- use benchmark identity as policy;
- count gifted O0 discovery costs as O2 performance;
- omit basis/program/control bytes from an oracle representation;
- confuse large conditional saving with large addressable impact;
- hide mechanism tax on data that does not select it;
- let a portfolio accumulate unbounded audition/parser/recovery complexity;
- edit a frozen experiment after seeing result-bearing evidence;
- turn scoped negative evidence into universal dogma;
- use external novelty as a substitute for local causal reasoning;
- strand a proven Forge win for novelty;
- permanently suppress Foundry review because Forge always has another small task;
- average away a required product red;
- weaken hard invariants to preserve a research miracle.

---

# 26. Final doctrine

**Benchmarks tell CMPCT when it is wrong. They do not get exclusive authority over what CMPCT is allowed to imagine.**

Use the **Foundry** to challenge the archive's model of information.

Use the **Forge** to convert evidenced mechanisms into an exact, fast, portable and dominant product.

Use **Custody** to make sure neither side can lie to itself.

Do not manufacture active theses. Admit them through a hard charter gate and revisit the Foundry periodically when no thesis qualifies.

Measure **headroom**, **addressable opportunity**, **structural transfer**, **global carrying cost** and **product survival** separately.

Let expensive research intelligence discover simple exact representations; keep the decoder bounded and independently checkable.

Treat every new mechanism as a permanent tax until it proves otherwise. Prefer concept compression and mechanisms that subsume old complexity.

Freeze experiments before result-bearing execution and preserve unfavorable evidence unchanged.

Treat negative results as scoped conditional constraints with explicit reopening predicates.

Hand successful invention to the Forge instead of confusing productization with continued fundamental research.

And keep seeking changes that allow a durable statement of the form:

> **Previously CMPCT could not express this relationship efficiently. Now it can — and the opportunity is large enough, general enough and bounded enough to matter.**

That is the finalized standard for breakthrough-first CMPCT development.