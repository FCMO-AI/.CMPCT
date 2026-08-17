# CMPCT breakthrough rehabilitation policy

Status: normative engineering policy for research and pre-release work.

## Purpose

CMPCT does **not** want a culture where a genuinely transformative idea is discarded the instant one
secondary benchmark moves backward. That behavior protects a scoreboard, not the system.

The project still wants the final released frontier to avoid regression. The change is *where* the
no-regression rule applies:

> **No regression is a promotion boundary, not an exploration boundary.**

A research candidate may temporarily make one measured dimension worse if it produces a large,
reproducible, mechanism-level gain elsewhere. Such a candidate is not release-ready, but neither is it
thrown away. It enters a deliberate **breakthrough rehabilitation** cycle whose job is to retain the
new gain while repairing every inherited strength that the breakthrough damaged.

The intended outcome is stronger than either naive extreme:

- not “reject anything with one red cell”; and
- not “accept a flashy aggregate win and live with the damage.”

The target is: **discover the breakthrough, preserve it, pay its regression debt, then promote only the
combined system that keeps the breakthrough and restores the inherited floor.**

## Two engineering states

CMPCT distinguishes two states that must not be confused.

### 1. Exploration / breakthrough seed

A seed is allowed to be temporarily non-Pareto if all of the following are true:

- the gain is reproducible and clearly outside measurement noise;
- the gain comes from a defensible mechanism rather than benchmark-specific tuning;
- the affected benchmark contract is fair and unchanged;
- every regression is retained and measured, not hidden;
- correctness, byte-exact losslessness, authentication and hostile-input safety are not compromised;
- there is a plausible path to combine, select, isolate or further engineer the mechanism rather than
  merely accepting the regression forever.

There is deliberately no single percentage threshold for “miracle.” A 40% gain in a strategic storage
workload, a 10x latency reduction, elimination of an entire decode pass, or a new representation that
opens a previously impossible design space can all qualify. The evidence and mechanism matter more than
a gamable scalar cutoff.

### 2. Promotion / release candidate

A promotion candidate must close the regression debt before it becomes the new product baseline.
Existing correctness/safety invariants remain hard requirements. For the current release-parity
contract, deterministic archive size must be no worse than the direct base per workload, and confirmed
timing regressions outside the documented noise envelope must be repaired.

A breakthrough can therefore be *accepted as research* before it is *accepted as release state*.

## The breakthrough preservation rule

When a candidate produces a dramatic verified win and also a meaningful regression, agents MUST NOT
immediately delete the mechanism or conclude that the idea failed solely because the normal release
gate is red.

Instead:

1. preserve the exact candidate commit or reproducible patch;
2. preserve the full benchmark matrix, including all losses;
3. identify which cost moved and where it was exported;
4. open an explicit regression-debt ledger;
5. attempt rehabilitation while continuously checking that the original gain survives.

Footnote: preservation does not mean merging damaged product behavior into `main`. It means retaining a
reproducible research state long enough to solve the actual multi-objective engineering problem instead
of destroying useful evidence after the first tradeoff appears.

## Regression-debt ledger

Every breakthrough seed with regressions should record, in its PR/research note or durable benchmark
record:

- **breakthrough metric:** baseline, candidate, absolute delta and relative delta;
- **regressed metric(s):** baseline, candidate, absolute delta and relative delta;
- **scope:** exact workloads, operations, platforms and semantics affected;
- **suspected mechanism:** what resource/cost was moved to buy the gain;
- **hard invariants:** properties that may not be traded even temporarily;
- **rehabilitation hypotheses:** concrete ways to restore the lost metric;
- **gain-retention test:** the measurement that proves the breakthrough itself has not been optimized
  back out of existence;
- **exit condition:** the inherited floor that must be recovered before promotion.

A debt item is not closed by an aggregate average. If a release contract is per-workload, the repaired
candidate must satisfy the per-workload floor.

## Rehabilitation order

Agents should attack breakthrough debt in this order because the earlier strategies often preserve the
largest gain with the least compromise.

### A. Portfolio / adaptive selection

Ask whether the old and new mechanisms can coexist and the encoder can select the better representation
per file, chunk, workload, operation or physical region.

This is often the highest-value response: use the breakthrough exactly where it wins and retain the
inherited path where it does not. EntropyGraph II's exact fallback portfolio is an existing example of
this general pattern, not a special exemption.

Selection itself must be measured and bounded. The project must not hide excessive creation CPU,
memory, metadata, reader complexity or dependency depth inside a “best of both” tournament.

### B. Isolate the exported cost

Determine whether the regression comes from one separable stage: startup, metadata, index size,
dictionary load, packing, cache pressure, extra decode work, syscall count, memory allocation, recovery
redundancy or another local cost.

Repair that stage without touching the breakthrough mechanism if possible.

### C. Change the representation boundary

If the tradeoff is structural, change where the system draws the boundary. Examples include splitting
hot/cold paths, adding bounded side information, moving work to creation time, reusing an already-required
representation, or changing physical grouping while keeping logical semantics stable.

### D. Counter-invention

If the breakthrough genuinely damages another important metric, treat that loss as the next invention
mission. Do not merely tune the first mechanism downward until the breakthrough disappears. Search for a
second mechanism that restores the damaged dimension while preserving the original win.

This is the intended “one miracle pays for another” behavior: a large improvement is allowed to expose a
new bottleneck, and that bottleneck becomes the next engineering target.

### E. Only then consider rejecting the seed

A breakthrough seed should be retired when evidence shows that the regression is fundamental under the
required product semantics, rehabilitation attempts erase the original gain, complexity/resource cost
becomes indefensible, or the apparent miracle does not generalize.

Retirement should preserve the negative result so future agents do not repeat the same dead end.

## Hard invariants that do not enter regression debt

Some properties are not ordinary optimization metrics and may not be temporarily “borrowed” to create a
benchmark miracle:

- byte-exact correctness;
- authenticated-data boundaries;
- path traversal and hostile-input safety;
- bounded parser/resource behavior required by the current contract;
- truthful benchmark semantics and provenance;
- preservation of user data;
- required recovery guarantees once claimed as canonical behavior.

A candidate that corrupts bytes or weakens security is a broken candidate, not a breakthrough with debt.

## Release-gate interpretation

A failed release performance gate means **not promotable yet**. For an ordinary small optimization, that
usually means fix or revert it. For a verified breakthrough seed, it means enter rehabilitation.

The gate must continue to report the regression accurately. It must not be weakened, have workloads
removed, or have tolerances widened merely to keep the seed alive.

The correct sequence is:

1. discover;
2. measure;
3. preserve;
4. expose debt;
5. rehabilitate;
6. rerun the full direct-base matrix;
7. promote only after the debt is closed.

This keeps the final no-regression standard while removing the incentive to avoid risky, high-upside
engineering during research.

## Anti-scoreboard rule

The purpose of benchmarking is to model product behavior, not to accumulate green cells.

Agents must not:

- sacrifice a major verified breakthrough solely to make an intermediate matrix uniformly green;
- optimize an aggregate while hiding a severe losing row;
- average away a release-contract regression;
- lower a competitor setting or change semantics after a loss appears;
- declare a debt paid because a different metric improved even more;
- preserve a miracle by permanently accepting unexplained damage to another strategic metric.

The correct target is a **larger Pareto frontier after rehabilitation**.

## Completion test for a rehabilitated breakthrough

Before promotion, a skeptical reviewer should be able to answer yes to all of these:

- Is the original breakthrough still materially present?
- Are all originally regressed release-contract metrics restored to at least their inherited floor?
- Are correctness, integrity, recovery and hostile-input invariants intact?
- Did the repair avoid silently exporting the cost into memory, locality, CPU, metadata or portability?
- Are losing competitor cases still visible?
- Can the result be reproduced from durable repository evidence?
- Is the combined mechanism understandable enough to maintain and port?

If yes, the project has not merely avoided regression. It has converted a risky discovery into a
strictly stronger system.
