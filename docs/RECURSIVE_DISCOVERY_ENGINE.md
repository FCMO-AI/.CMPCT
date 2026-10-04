# CMPCT Recursive Discovery Engine (RDE)

**Status:** canonical research-method infrastructure for the active CMPCT frontier  
**Scope:** improves how one persistent CMPCT agent chooses, executes, falsifies, and learns from experiments. It does not replace product/release/format law.

## PARETOBONK: what survives

The first RDE sketch was directionally useful but overbuilt. A directory of state, hypothesis, lesson, and policy databases plus several planners would duplicate repository truth, create synchronization debt, and reward record-filling. CMPCT already has durable state, research history, benchmark evidence, release law, and an unusually strong experimental discipline. RDE therefore adds only information that CMPCT does not already preserve reliably: **pre-result predictions, decision alternatives, causal outcomes, counterfactual lessons, and research-policy learning**.

Rejected from the initial sketch:
- no second project-state database;
- no scalar research reward;
- no mandatory ML, embeddings, vector database, swarm, or learned policy;
- no fixed explore/exploit ratio;
- no requirement to log trivial work;
- no replay theatre that merely rephrases history;
- no promotion credit from oracle/simulation/counterfactual evidence.

RDE must earn its own carrying cost. If its ledger does not improve experiment selection or expose reusable scientific mistakes, simplify or remove it.

## Three coupled learning loops

RDE treats each material activation as capable of moving three different frontiers:

1. **L0 Product:** CMPCT itself becomes better.
2. **L1 Science:** the repository gains a more accurate causal model of why CMPCT wins, loses, or saturates.
3. **L2 Discovery:** the campaign becomes better at choosing experiments that create L0/L1 progress.

L2 is the recursive layer. It may change research policy, never product evidence.

## Material experiment contract

Before a non-trivial experiment whose result is not already obvious, record a compact prediction episode. The minimum useful fields are:

- stable episode id and timestamp;
- exact starting commit/branch;
- problem and measured baseline;
- mechanism hypothesis;
- strongest simpler control;
- plausible alternative explanation;
- predicted observations if the mechanism is correct;
- kill/narrow condition;
- expected decision unlocked by the result;
- solution-family / representation class;
- evidence tier being attempted.

After execution append, never rewrite, the outcome:
- exact ending commit/artifact/evidence;
- observation and direct measurements;
- product/science/discovery classification;
- hypothesis disposition: advanced, falsified, narrowed, ambiguous, retired, rehabilitated;
- exported costs and losing cases;
- whether the result was decisive;
- what action actually follows;
- counterfactual: the cheapest earlier discriminator we now know would have produced the same decision;
- reusable discovery lesson, only when supported.

Predictions are immutable after result observation. Corrections are appended.

## Pareto state, not one reward

Never collapse CMPCT research into a single score. Candidate actions and outcomes are judged against the currently relevant Pareto dimensions, including:

**Product:** stored bytes, create/extract/read time, RSS, I/O, selective work/amplification, integrity/recovery, semantics, portability/interoperability, complexity and maintenance.

**Science:** information gain, causal discrimination, generality/held-out transfer, oracle headroom, uncertainty retired, and novelty of solution class.

**Research economics:** time-to-falsification, execution cost, dependency depth, probability of a decisive result, expected upside, future leverage and opportunity cost.

Numbers are used where measured. Do not manufacture pseudo-precise utility weights.

## Experiment market

At each material decision point, generate a small set of genuinely different candidate interventions when uncertainty warrants it. Candidates may include productization, causal diagnosis, cheap oracle, representation change, external-gap investigation, evidence repair, or retirement of a dead family.

Selection asks:

> Which safe actionable experiment is most likely to move the real frontier or decisively change what we do next per unit of scarce activation effort?

Prefer a cheaper discriminator when it can decide the same fork. Prefer productization when a proven mechanism has unclaimed product value. Prefer a worldview-changing experiment when the current family is saturated. Do not generate alternatives ceremonially when one action dominates from direct evidence.

## Oracle ladder

Use the cheapest honest rung that can kill or justify further investment:

0. mathematical/information bound;
1. gifted oracle with every gifted fact fully charged to the representation when relevant;
2. offline discoverability;
3. generic detector/admission policy;
4. integrated product mechanism;
5. hostile + held-out/generalization evidence;
6. full current promotion contract.

A lower rung can falsify headroom. It cannot claim a higher-rung product result. If even a generous oracle has immaterial headroom, retire the family unless a materially different objective remains.

## Frontier pressure

RDE actively detects local-optimum signatures:
- repeated tiny gains from one mechanism family;
- threshold gardening;
- repeated exported-cost loops;
- high experiment cost with low information gain;
- repeated ambiguous outcomes from the same evaluator;
- exhausted oracle headroom;
- a predictor repeatedly choosing work that later proves non-decisive.

When these appear, the next candidate set must include at least one genuinely different problem frame: representation, information model, ownership/layout, reconstruction model, cross-object relation, filesystem semantic, execution architecture, proof/evaluator model, or another causally distinct class.

This is a search-space obligation, not an adoption obligation. The incumbent is allowed to win.

## Negative memory and rehabilitation

A failed family is valuable only if its failure boundary is reusable. Record the condition, prediction, observation, likely cause/confidence, and a **reopening condition**. Future agents should not rerun an equivalent dead experiment without changed evidence, changed conditions, or a materially different mechanism.

A negative is never universal merely because one episode failed.

## Counterfactual replay

Replay is decision-focused, not narrative. Periodically, and especially after a decisive result or repeated low-yield work, inspect relevant prior episodes and ask:

1. Given only information available at that historical decision, was the chosen experiment reasonable?
2. With knowledge learned later, what earlier observable discriminator would have shortened the path?
3. Is that discriminator recognizable prospectively in future states?
4. Does the lesson transfer beyond one workload/mechanism?

Only (3)+(4) justify an L2 policy lesson. Hindsight that cannot be recognized prospectively is history, not a policy improvement.

## Prediction calibration

RDE should eventually answer empirical questions about CMPCT's own research process: which hypothesis classes predict correctly, which experiment types are decisive, where oracles over/under-predict product value, which local-optimum signatures precede wasted work, and which controls most often overturn the favored story.

Do not optimize for prediction accuracy alone: trivial predictions can be accurate and useless. Track decision value and frontier movement.

## Minimal durable implementation

The canonical machine-readable append-only ledger is `research/discovery_episodes.jsonl`. It contains only material episodes and L2 lessons; ordinary project state remains in existing canonical documents.

`tools/discovery_ledger.py` validates the ledger, summarizes outcomes, identifies unresolved episodes, reports family saturation signals, and exposes replay candidates. It must remain deterministic and dependency-light.

This document defines semantics. The tool is evidence infrastructure, not an autonomous judge.

## Activation integration

A persistent CMPCT activation should:

**OBSERVE → RECONSTRUCT CAUSAL FRONTIER → GENERATE/SELECT → PREDICT → EXECUTE → ATTACK → MEASURE → LEARN → COUNTERFACTUAL CHECK → LAND**

Not every activation needs a new episode. Continuation of an existing experiment should reuse its episode identity. Infrastructure work should be logged only when it tests a material causal claim or materially changes future research leverage.

At landing, ask two independent questions:
- What did we learn/change about CMPCT?
- Did this episode teach us anything supported about how to investigate CMPCT better next time?

If the second answer is no, do not invent an L2 lesson.

## Success/falsification of RDE itself

RDE is successful only if accumulated evidence shows improvements such as fewer experiments per material decision, shorter anomaly-to-cause time, fewer equivalent dead-family repeats, more cheap falsifications before expensive implementation, better held-out transfer, or greater product/scientific frontier movement per activation.

Periodically compare later policy behavior against frozen earlier episodes through shadow replay. Do not claim recursive improvement merely because the ledger grows.

If RDE becomes documentation overhead, Goodharts against episode metrics, narrows exploration, duplicates canonical state, or fails to produce reusable decision improvements, PARETOBONK it again.
