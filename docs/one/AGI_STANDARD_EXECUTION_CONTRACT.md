# CMPCT ONE — AGI Standard Execution Contract

**Status:** normative for material CMPCT1 / ONE research and engineering work  
**Parent authority:** `docs/AGI_ENGINEERING_STANDARD.md`  
**Scope:** `research/cmpct1` and successor ONE research lines

This file does not replace the FCMO AGI Engineering & Operations Standard. It makes its application to CMPCT1 operational, auditable and difficult to satisfy by prose alone.

## Non-negotiable rule

For every material CMPCT1 experiment, optimization, representation change, writer/reader change, performance claim or promotion decision, the AGI Engineering Standard is **mandatory execution law**, not optional guidance.

A result is not promotable merely because code landed or tests are green. It must leave evidence that an independent reviewer can use to answer the questions below without chat history.

## Required pre-result record

Before result-bearing execution, freeze or otherwise durably record:

1. **Mission Lock** — exact problem/opportunity and why it matters to ONE.
2. **Baseline** — exact inherited implementation/evidence being compared.
3. **Invariant set** — semantics, resource, integrity, locality, portability and reader constraints that may not be weakened.
4. **Falsifiable hypothesis** — the mechanism expected to change a measurable fact.
5. **Disproof test** — the concrete result that retires or constrains the hypothesis.
6. **Cost model** — bytes, CPU/elapsed, memory/state, source traffic, decode/reconstruction work, selective-read amplification and any other exported cost touched by the change.
7. **Independent evidence plan** — oracle, property, fixed vectors or cross-implementation check sufficient to avoid builder/reader shared-bug confidence.
8. **Hostile envelope** — at minimum the relevant incompressible, tiny/boundary, already-compressed/media, false-pattern, structured, temporal/versioned and hostile-resource cases.
9. **Promotion law** — exact thresholds/conditions and terminal decisions, frozen before the result where practical.

If a material experiment cannot state these items, it is not ready to consume research authority.

## Required post-result record

Every material result must durably state:

1. exact source SHA / branch and result provenance;
2. exact measured outputs, including losing and ambiguous rows;
3. semantic/oracle truth and test counts;
4. creation cost and decode/read cost where implicated;
5. state/peak-memory and data-traffic consequences where implicated;
6. selective-access, integrity, recovery and failure-blast-radius consequences where implicated;
7. strongest hostile-review objection that still survives;
8. scoped negative evidence and reopening predicate for rejected families;
9. explicit decision: advance, hold, supersede, retire, or return to Foundry;
10. regression debt, if any, and the next rehabilitation target.

## Evidence hierarchy enforcement

Architectural reasoning and intuition may generate hypotheses, but they cannot promote them when controlled or independent evidence is practical. Prefer, in order:

1. independent fixed vectors / independent implementation agreement;
2. deterministic controlled experiments with exact provenance;
3. direct base-vs-candidate tests on identical inputs and semantics;
4. repeated measurements with raw observations retained;
5. hostile/property tests;
6. source inspection / derivation;
7. architectural inference;
8. intuition.

No lower level may be narrated as if it were a higher level.

## ONE-specific cost honesty

CMPCT1 optimizes **marginal information yield**, not compression ratio in isolation. Every material writer mechanism must account for the costs it creates or removes.

A representation or discovery change is incomplete if it reports only stored bytes while exporting unmeasured CPU, memory traffic, retained state, reconstruction work, selective-read amplification, integrity work, failure blast radius or reader complexity.

The reader performs no discovery. Discovery cost belongs to creation; reconstruction cost belongs to read; neither may be silently moved across the accounting boundary.

## Representation-unification test

Historical CMPCT mechanisms may inform discovery, but a promoted ONE mechanism must compile its useful predictive structure into the same bounded Law + Surprise representation.

Reject any proposal whose practical meaning is merely "old mechanism X behind a new opaque ONE opcode" unless the architecture canon itself is deliberately superseded through a new research decision.

## Hostile Reviewer is a gate, not a paragraph

Before promotion, explicitly try to reject the work.

At minimum ask:

- What workload makes the claimed gain disappear?
- Did we remove work, or merely move it?
- Did a small intermediate representation help CPU even if eliminating it looked cleaner?
- Did we accidentally weaken validation, authentication, locality or recovery?
- Is the apparent owner stable under repeat runs?
- Does a threshold encode the corpus rather than a mechanism?
- Is the result still persuasive if the losing rows are shown first?
- Does the mechanism remain useful after charging global carrying cost?

When hostile review discovers a methodological flaw, repair the experiment **before** consuming result authority whenever possible.

## Promotion and rehabilitation

Exploratory breakthroughs may carry explicit performance debt, but correctness, byte exactness, authentication, hostile-input safety and truthful benchmark semantics are never borrowable debt.

A dramatic gain with ordinary-performance debt remains a research seed governed by `docs/BREAKTHROUGH_REHABILITATION.md`; it is not release or product authority.

## Completion condition

A material CMPCT1 activation is complete only when repository evidence makes clear:

- what fact changed;
- why the mechanism caused it;
- what did not improve;
- what cost was exported or eliminated;
- what evidence level supports the claim;
- what the strongest surviving objection is;
- and what exact next experiment or engineering transition follows.

If those answers exist only in chat, the work is not durably complete.
