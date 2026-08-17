# CMPCT v0.30 child research — Shared-Cost Representation Superoptimizer Extractor

Status: **ACTIVE CHILD RESEARCH / DO NOT MERGE / DO NOT VERSION-BUMP**  
Parent: PR #45 / `agent/lattice-v030-breakthrough` @ `0338527d3a9e4f12df20448c52665d1c93c8b937`  
Branch: `agent/v030-rso-extractor`

## Why this exists

CMPCT now has multiple candidate representation families that may reconstruct identical logical bytes:

- direct / Preflate / accepted v0.29 fallback;
- G1–G4 Geometry and latent-type descendants;
- Mosaic / PrefixGraph references;
- potential synthetic substrate atoms;
- binary/bitplane transforms.

A fixed pipeline order can destroy an option before later shared-cost information is known. Example: one root
costs 120 bytes to materialize and lets two targets store 10-byte recipes. Charging the root separately to each
target makes both references look worse than 100-byte direct targets; globally the shared representation costs
120 + 10 + 10 = 140 instead of 200.

The extractor therefore keeps a bounded **equivalence frontier** per target and prices shared facilities once.

## Relationship to prior art

This is not a claim to have invented equality saturation, facility location, set cover or global extraction.

The `egg` equality-saturation work demonstrates the value of retaining equivalent program forms until a later
cost-based extraction phase: <https://arxiv.org/abs/2004.03082>

CMPCT deliberately implements a smaller problem-specific model rather than a general e-graph. Representation
generators already know their exact inverse and complete local stored cost; the extractor only resolves which
shared roots/atoms/dictionaries should be opened and which equivalent plan should reconstruct each target.

## Model

`Facility`
: one shared stored object with a one-time opening byte cost, e.g. a direct Mosaic root, PrefixGraph root,
  synthetic phrase atom/pack, or shared dictionary.

`Plan`
: one byte-exact way to reconstruct one logical target. It declares private stored bytes, 0–4 required
  facilities, dependency depth, read amplification, peak memory and parser-risk class.

`Policy`
: hard resource boundary. Plans outside it are removed **before** byte optimization.

Total objective during size research:

`sum(opened facility bytes) + sum(selected plan private bytes)`

Future promotion extraction will retain timing/recovery dimensions in the Pareto frontier rather than pretend
one scalar archive-size objective is sufficient.

## Algorithms

### Exact oracle

For <=18 facilities, enumerate all facility subsets and choose the exact cheapest legal closure. This exists as
a research falsifier/reference implementation, not a scalable writer strategy.

### Bounded beam

For larger candidate sets:

1. start from the mandatory facility-free fallbacks;
2. treat each unique plan requirement set as an atomic opening bundle (important for 2–4-root Mosaic plans);
3. expand a bounded beam of opened-facility sets;
4. rank states by an **admissible optimistic lower bound** that treats unopened facilities as free;
5. evaluate each state by exact complete candidate costs;
6. stop at explicit beam/round/expansion budgets.

The optimistic bound lets the beam temporarily carry an opening cost before all downstream targets switch. A
current-cost-only greedy search would reintroduce the same phase-ordering failure the extractor is meant to fix.

## Frozen semantics falsifier

`benchmarks/representation_superoptimizer_v030_probe.py`

Three preregistered synthetic cost cases:

1. shared root amortization;
2. Geometry-vs-shared-reference representation flip;
3. simultaneous two-root Mosaic bundle plus synthetic atom facility.

The bounded beam must exactly match the exhaustive oracle on all three and must strictly beat a deliberately
phase-ordered/local comparator on at least one.

**These are optimizer semantics, not archive benchmark results.** No byte claim about CMPCT v0.30 may be made
from this probe.

## Hard rules

- every target must retain a facility-free fallback;
- no plan may require >4 shared facilities in the current research grammar;
- hard depth/read/memory/parser policy filters happen before optimization;
- candidate generators must charge descriptor/framing bytes before submitting a plan;
- a transform with no independently verified exact inverse never enters the frontier;
- opening a facility does not waive its recovery/locality cost;
- search has an explicit budget;
- the beam must continue to be regression-checked against the exact oracle on small randomized problems.

## Next real integration

Only after the semantics gate is green:

1. instrument an exact public workload to expose complete per-node G0–G4 candidate costs;
2. expose existing Mosaic/PrefixGraph reference candidates and direct-root opening costs without changing their
   current archive grammar;
3. feed both into this extractor as a **diagnostic oracle**;
4. compare its predicted globally-selected closure with the current pipeline's actual complete archive cost;
5. construct a real same-tree archive only if the diagnostic predicts a material win;
6. then add substrate facilities and repeat.

If the real diagnostic finds no phase-ordering loss, do not integrate this machinery merely because the
synthetic tests are elegant.

## Merge lock

**DO NOT MERGE. DO NOT VERSION-BUMP. DO NOT PUBLISH v0.30 CLAIMS.**

The branch exists to establish whether shared-cost extraction is a necessary mechanism. Parent integration is
conditional on real complete-artifact evidence and later explicit user authorization.
