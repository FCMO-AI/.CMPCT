# CMPCT1 / ONE Genesis gate measurement contract — frozen 2026-09-09

Experimental state: **ONE-G0.2**  
Branch authority: `research/cmpct1`  
Execution boundary: **this contract is preparatory only. It MUST NOT be used to run or score the Genesis decision before the first qualifying activation on 2026-09-11 America/Mexico_City.**

## Mission lock

The September 11 decision is not a compression-ratio contest. CMPCT historically promises a stronger archive/container surface: byte-exact files and filesystem semantics, bounded selective access, integrity, recovery, hostile-input limits, portability and ZIP escape/export behavior. ONE may remain primary only if its storage gains and execution gains survive those obligations rather than exporting cost or dropping semantics.

The gate therefore needs one same-input, same-semantics evidence object that makes **semantic asymmetry visible instead of silently normalizing it away**.

## Frozen comparator authorities

- CMPCT1 candidate: best admissible `research/cmpct1` HEAD at gate start, recorded exactly in the result.
- frozen v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`.
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`, plus the strongest already-developed v0.30 evidence/line that can be reproduced fairly without changing its historical thresholds or semantics.

The v0.30 frozen source is not to be weakened because its broad integration had RED rows, nor strengthened by quoting isolated frontier savings while omitting creation/locality debt. Both its strongest structure and exported costs belong in the adjudication.

## Frozen input authority

The gate consumes the accepted portable 15-workload substrate used by the current v0.29 generalization authority:

- 10 `neutral_hostile_v1` workloads;
- 5 `resemblance_hostile_v1` workloads;
- accepted deterministic neutral repair-v6, including compiler-independent developer ELF fixtures;
- one generated input instance per workload shared by every contender measured in that row.

No system gets its own regenerated corpus tree. File count, logical bytes and `tree_sha256` must be recorded before contender execution.

## Measurement principle

For each metric, the result must state one of four comparability classes:

1. **same_semantics_direct** — the systems perform the same user-visible operation and the measurements can be compared directly;
2. **same_goal_different_mechanism** — user result is equivalent but work/integrity/recovery mechanics differ; compare quantitatively and disclose the difference;
3. **richer_semantics** — one system preserves a property the other does not; bytes/time remain reportable but are not an unqualified head-to-head win;
4. **unavailable** — the exact operation does not exist on that contender; never encode this as zero cost.

A missing metric is evidence debt, not a favorable zero.

## Per-workload required measurements

Every one of the 15 rows must preserve, to the strongest directly measurable extent available on all contenders:

### A. Storage / representation

- complete artifact bytes, including mandatory metadata, integrity and recovery structures;
- logical input bytes and file count;
- candidate saving/regression in bytes and percent against each fair comparator;
- ONE split where available: Law bytes, Surprise bytes, Crystal bytes and required metadata/authentication bytes;
- whether the output is a complete independent archive or depends on external context.

No isolated transform payload may be substituted for complete artifact bytes.

### B. Creation economics

- creation CPU time;
- creation elapsed/wall time;
- peak RSS or strongest available same-process peak-memory measurement;
- optional stage accounting where available: observation/gating, candidate discovery, exact proof, Program construction/validation, hashing/integrity, physical write;
- amount of source/input data read or revisited when instrumentation supports it.

Parallel creation is allowed only when the contender's recorded product/research contract permits it and the same runner/cpu allocation is disclosed. CPU and wall time must both remain visible so parallelism does not masquerade as free work.

### C. Whole-object read/decode

- complete logical extraction/read CPU and wall time;
- effective logical throughput;
- peak memory / temporary materialization where available;
- reconstructed bytes/work when the representation can report it;
- authentication/integrity work required before returning the claimed trusted result.

Hot-kernel replay is supporting causal evidence only; the gate charges required preparation/open/planning work at an appropriate lifecycle boundary.

### D. Selective access

Where a workload contains files large enough for meaningful range testing, use deterministic requests derived from file geometry, not contender output. At minimum record representative small-prefix, interior and end/cross-boundary reads when valid.

Per request record:

- requested logical bytes;
- physical stored/source bytes read/touched;
- decoded/reconstructed bytes;
- planner/preparation work if separately measurable;
- proof/authentication bytes and hash work where applicable;
- CPU and wall time;
- peak temporary bytes;
- amplification = relevant touched or reconstructed bytes / requested bytes;
- whether unrelated archive regions or a whole logical object were materialized.

A solid competitor that must traverse unrelated data may report that cost honestly; CMPCT may not claim selective-access parity for such a system by measuring only the final slice copy.

### E. Integrity, hostile behavior and resource bounds

Record the contender's exact guarantee boundary for the operation being timed:

- CRC/cryptographic identity or equivalent validation performed;
- whether a partial read authenticates only touched physical units, the requested logical range, the whole logical object, or no equivalent boundary;
- malformed metadata/reference rejection;
- decompression/materialization/work limits relevant to the measured path;
- whether failure can return partial unauthenticated bytes.

Correctness, authentication and hostile-input safety are hard invariants. A candidate that violates them is invalid, not a fast result with regression debt.

### F. Recovery / failure blast radius

For each complete artifact representation, record—not fabricate—a directly supported recovery model:

- redundant index/generation/checkpoint structures present;
- ability to select newest valid committed state after an incomplete tail/update where applicable;
- smallest independently authenticated/recoverable physical region where meaningful;
- whether corruption in an unrelated region prevents the measured selective read;
- additional bytes and reader work paid for that recovery property.

If equivalent fault injection cannot be executed across all three contenders, classify the difference and preserve existing exact-source recovery evidence; do not convert a documentation claim into a numeric win.

### G. Portability / reader complexity

Record capability facts required to interpret performance:

- on-disk revision/profile or research identity;
- Python/reference-only versus shared native reader availability;
- independent conformance-vector status;
- supported list/stat/read/range/verify/extract surface;
- filesystem semantics preserved (regular files, dirs, sparse, links, metadata as applicable);
- ZIP export/escape compatibility where implemented;
- platform evidence available for that representation.

Reader source-line counts or binary size may be diagnostic but are not a synthetic score. Complexity is adjudicated by required permanent grammar/capability burden and maintenance/portability obligations, not by gaming LOC.

## Timing topology

To reduce benchmark theater:

- run all contenders for a given comparable operation on the same hosted runner whenever technically possible;
- separate in-process/library timing from fresh-process CLI timing;
- use repeated observations and medians for timing; preserve raw samples;
- do not compare a hot cached candidate call against a cold comparator process start;
- do not hide ONE open/validation/planning in setup if the corresponding comparator work is timed;
- for repeated selective access, report both **first/opened lifecycle** and **steady-state after one legitimate validated open** when both are meaningful;
- cache state and OS page-cache assumptions must be recorded, not guessed.

The existing project release timing noise rule (5% AND 3 ms to call a confirmed regression on hosted CI) remains useful for direct release-style comparisons; the Genesis decision may also preserve mechanism-level ratios that are far outside this envelope.

## Required aggregate views

The final evidence must include all individual rows plus, at minimum:

- total complete artifact bytes for all 15 workloads;
- workload counts smaller/equal/larger versus v0.29 and v0.30;
- aggregate byte delta and largest positive/negative row;
- summed creation CPU and wall where meaningful, plus per-row ratios;
- median and worst direct-comparable read/decode ratios;
- median and worst selective-read amplification on eligible comparable requests;
- peak memory maximum and worst ratio where directly measured;
- explicit semantic/capability matrix for integrity, recovery, locality and portability;
- list of rows where the strongest v0.30 mechanism beats ONE and the Law/predictive structure responsible if known;
- list of ONE wins that disappear when complete creation/read/access cost is charged.

No aggregate may hide a severe losing row. Losses are part of the gate result.

## Decision rubric

`KEEP_CMPCT1_PRIMARY` requires evidence that the best ONE state is a **materially stronger path** and credibly able to supersede both frozen v0.29 and the deferred v0.30 frontier while keeping CMPCT's product obligations.

Evidence favoring that decision includes a combination of:

- meaningful complete-artifact savings on general workloads, not only handpicked Law-positive microcases;
- cheap no-op behavior where useful Law is absent;
- creation economics that make additional discovery earn its cost;
- fast bounded whole-object reconstruction;
- selective access whose work follows requested reconstruction cones rather than unrelated root size;
- unchanged or stronger integrity/resource behavior;
- credible recovery and portability path without exploding permanent reader grammar.

`REACTIVATE_V030_NEAR_TERM` is required if ONE remains primarily a mechanism-level research success whose 15-workload complete-system state fails to outperform or credibly supersede v0.29/v0.30 after all exported costs and product semantics are charged.

The gate may preserve ONE as research in either outcome. It may not manufacture `KEEP_CMPCT1_PRIMARY` by relaxing comparator settings, deleting rows, weakening semantics or scoring unavailable capabilities as zero cost.

## Hostile reviewer checklist

Before accepting the final gate result, try to reject it with these questions:

- Did all contenders see byte-identical trees?
- Did a candidate get credit for a research payload instead of a complete archive?
- Did creation omit discovery/proof/hash/serialization work?
- Did selective access omit planning, authentication, source packing or whole-object decode?
- Did one side include recovery/integrity bytes while another side silently omit the property?
- Did a faster result come from a weaker trust boundary?
- Did parallel wall-time hide much larger CPU consumption?
- Did a missing metric become zero?
- Did an old v0.30 RED integration result erase a genuine frontier mechanism, or did a flashy v0.30 mechanism result erase its known creation debt?
- Did ONE receive tuning information from an early scored preview of this exact gate?

Any yes requires correction before adjudication.

## Before September 11

Allowed work is limited to substrate reproducibility, comparator checkout/authority verification, measurement-schema implementation, test/fault-injection plumbing that does not encode/score the gate, and independent ONE research unrelated to previewing final comparator outcomes.

The first scored same-input comparison remains reserved for the first qualifying activation on 2026-09-11 America/Mexico_City.
